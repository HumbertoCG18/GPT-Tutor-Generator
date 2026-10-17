"""Harness stdlib do contrato R1–R6 do MoodleClient (correção V1, 01/10/2026).

Uso: python -B harness_r1_r6.py --raiz <worktree> --moodle <moodle.py> --casos <tests/test_moodle.py>
                                --modo delta|candidato --saida <resultado.json>

Carrega a classe real do arquivo indicado e o http.client deste runtime. Casos, instrumentação do fio e oráculos vêm
de tests/test_moodle.py, extraídos por AST (sem pytest). Stub só para dependência ausente do runtime, declarado na
saída. Rede real vedada. Saída 0 só sem divergência inesperada, sem caso não executado e sem falha do harness.
"""
import argparse
import ast
import hashlib
import http.client
import importlib.util
import inspect
import io
import json
import platform
import socket
import sys
import types
from pathlib import Path

DEFINICOES = {"_CASOS_ORCAMENTO", "_R02_ESPERADO", "_FioCorpo", "_monta_fio", "_tipo_em", "_executa_caso",
              "_confere_caso", "_sequencia_r02"}


def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def sem_rede(*a, **k):
    raise AssertionError("rede real vedada no harness")


class Trocas:
    """Equivalente ao monkeypatch.setattr: desfaz tudo ao fim de cada caso."""

    def __init__(self):
        self.feitas = []

    def __call__(self, obj, nome, valor):
        self.feitas.append((obj, nome, getattr(obj, nome)))
        setattr(obj, nome, valor)

    def desfaz(self):
        while self.feitas:
            obj, nome, antigo = self.feitas.pop()
            setattr(obj, nome, antigo)


def carrega_moodle(raiz, arquivo):
    sys.path.insert(0, str(raiz))
    stubs = []
    if importlib.util.find_spec("requests") is None:
        sys.modules["requests"] = types.ModuleType("requests")
        stubs.append("requests: módulo vazio (ausente neste runtime; usado só dentro de função em "
                     "src/utils/helpers.py; não é o cliente nem o transporte)")
    nome = "src.builder.sources.moodle"
    if nome in sys.modules:
        raise SystemExit(f"{nome} já importado antes da carga por caminho")
    spec = importlib.util.spec_from_file_location(nome, arquivo)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod, stubs


def carrega_definicoes(arquivo):
    arvore = ast.parse(Path(arquivo).read_text(encoding="utf-8"))
    nos = [n for n in arvore.body
           if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in DEFINICOES)
           or (isinstance(n, ast.Assign) and any(getattr(t, "id", None) in DEFINICOES for t in n.targets))]
    ns = {"io": io, "__name__": "casos_test_moodle"}
    exec(compile(ast.Module(body=nos, type_ignores=[]), str(arquivo), "exec"), ns)
    faltando = DEFINICOES - set(ns)
    if faltando:
        raise SystemExit(f"definições ausentes em {arquivo}: {sorted(faltando)}")
    return ns


def identidade(args, mod, stubs):
    arquivo = Path(args.moodle).resolve()
    fonte_classe = Path(inspect.getsourcefile(mod.MoodleClient)).resolve()
    ident = {
        "python": sys.version, "executavel": sys.executable, "plataforma": platform.platform(),
        "flags_otimizacao": sys.flags.optimize, "dont_write_bytecode": sys.dont_write_bytecode,
        "http_client": {"arquivo": http.client.__file__, "sha256": sha256(http.client.__file__)},
        "moodle": {"arquivo": str(arquivo), "sha256": sha256(arquivo), "modulo": mod.__name__,
                   "fonte_da_classe": str(fonte_classe)},
        "harness": {"arquivo": str(Path(__file__).resolve()), "sha256": sha256(__file__)},
        "casos": {"arquivo": str(Path(args.casos).resolve()), "sha256": sha256(args.casos)},
        "stubs": stubs, "modo": args.modo,
    }
    problemas = []
    if fonte_classe != arquivo:
        problemas.append(f"MoodleClient vem de {fonte_classe}, não de {arquivo}")
    if mod.http.client is not http.client or http.client.HTTPResponse.__module__ != "http.client":
        problemas.append("http.client do módulo não é o da stdlib deste runtime")
    if not Path(http.client.__file__).resolve().is_relative_to(Path(sys.base_prefix).resolve()):
        problemas.append(f"http.client fora da stdlib do runtime: {http.client.__file__}")
    return ident, problemas


def serializa(v):
    if isinstance(v, bytes):
        return {"hex": v.hex()} if len(v) <= 64 else {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()}
    if isinstance(v, (list, tuple)):
        return [serializa(x) for x in v]
    if isinstance(v, dict):
        return {k: serializa(x) for k, x in v.items()}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return repr(v)


def classifica(modo, caso, falhas, erro):
    if erro:
        return "nao_executado", True
    if modo == "candidato":
        return ("contrato_ok", False) if not falhas else ("contrato_falhou", True)
    estado = caso["delta"]
    if estado == "controle":
        hist = [f for f in falhas if f[0] == "historico"]
        if hist:
            return "controle_falhou", True
        return ("controle_verde_com_assercao_nova_vermelha" if falhas else "controle_verde"), False
    if estado == "defeito":
        return ("defeito_reproduzido", False) if falhas else ("defeito_nao_reproduzido", True)
    if estado == "regra_nova":
        tipo = any(f[1] == "tipo" for f in falhas)
        return ("regra_nova_ausente_no_delta", False) if tipo else ("regra_nova_ja_atendida", True)
    return "novo_registrado", False


def main():
    if not __debug__:
        raise SystemExit("rode sem -O: o harness exige asserções ativas")
    p = argparse.ArgumentParser()
    p.add_argument("--raiz", required=True)
    p.add_argument("--moodle", required=True)
    p.add_argument("--casos", required=True)
    p.add_argument("--modo", choices=("delta", "candidato"), required=True)
    p.add_argument("--saida", required=True)
    args = p.parse_args()

    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    mod, stubs = carrega_moodle(args.raiz, args.moodle)
    ident, problemas = identidade(args, mod, stubs)
    ns = carrega_definicoes(args.casos)
    casos = ns["_CASOS_ORCAMENTO"]
    ids = [c["id"] for c in casos]
    if len(ids) != len(set(ids)):
        problemas.append("ids de caso repetidos")

    resultados, inesperados = [], []
    for caso in casos:
        troca = Trocas()
        res, falhas, erro = None, [], None
        try:
            res = ns["_executa_caso"](caso, mod, troca)
            falhas = ns["_confere_caso"](caso, res)
        except Exception as e:  # caso não executado: conta como divergência
            erro = repr(e)
        finally:
            troca.desfaz()
        situacao, ruim = classifica(args.modo, caso, falhas, erro)
        if ruim:
            inesperados.append(caso["id"])
        obtido = None if res is None else {
            "tipo": res["tipo"], "retorno": res["retorno"], "bytes": res["bytes"], "corpo": res["corpo"],
            "partial": getattr(res["exc"], "partial", None), "causa": None if res["exc"] is None or
            res["exc"].__cause__ is None else type(res["exc"].__cause__).__name__,
            "mensagem": None if res["exc"] is None else str(res["exc"]), "aberturas": res["aberturas"],
            "ops": [(o["op"], o["pedido"], o["pos"], len(o["dado"]), o["erro"]) for o in res["ops"]]}
        resultados.append(serializa({"id": caso["id"], "grupo": caso["grupo"], "estado_no_delta": caso["delta"],
                                     "situacao": situacao, "falhas": falhas, "erro": erro,
                                     "esperado": caso["esp"], "obtido": obtido}))

    troca = Trocas()
    try:
        obs = ns["_sequencia_r02"](mod, troca)
        erro = None
    except Exception as e:  # sequência não executada
        obs, erro = None, repr(e)
    finally:
        troca.desfaz()
    r02_ok = erro is None and obs == ns["_R02_ESPERADO"]
    if not r02_ok:
        inesperados.append("R02")
    resultados.append(serializa({"id": "R02", "grupo": "retencao", "estado_no_delta": "controle",
                                 "situacao": ("contrato_ok" if args.modo == "candidato" else "controle_verde")
                                 if r02_ok else "divergiu", "erro": erro,
                                 "esperado": ns["_R02_ESPERADO"], "obtido": obs}))

    contagem = {}
    for r in resultados:
        contagem[r["situacao"]] = contagem.get(r["situacao"], 0) + 1
    saida = {"identidade": ident, "problemas_de_identidade": problemas, "inesperados": inesperados,
             "situacoes": contagem, "casos": resultados,
             "nao_cobertos": ["R01 (reentrância, M-03): só documentação, fora do código"]}
    Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sys.version.split()[0]} | {args.modo} | moodle {ident['moodle']['sha256'][:16]} | "
          f"casos {len(resultados)} | {contagem} | inesperados {inesperados} | identidade {problemas or 'ok'}")
    return 1 if inesperados or problemas else 0


if __name__ == "__main__":
    sys.exit(main())
