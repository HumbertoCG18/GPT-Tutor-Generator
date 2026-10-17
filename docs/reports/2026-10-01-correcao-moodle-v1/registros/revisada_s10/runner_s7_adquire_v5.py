"""Runner do S7 (F-01): testes da aquisição v5 executados no lugar contra o moodle.py da worktree, num só processo.

Uso: python -B runner_s7_adquire_v5.py --worktree <raiz> --principal <raiz> --sha-esperado <sha256 do candidato>
                                       --basetemp <dir> --saida <json>

1. worktree em sys.path[0]; importa src.builder.sources.moodle e confere arquivo e sha256;
2. carrega adquire.py do caminho original (ele põe a raiz da principal no sys.path, mas o módulo já está em
   sys.modules e é reaproveitado);
3. confere no processo que adquire.M é o mesmo módulo e que MoodleClient vem do arquivo da worktree;
4. pytest.main na pasta da aquisição, sem cache e com basetemp nos artefatos;
5. repete a conferência; 6. saída ≠ 0 se a identidade divergir, não puder ser determinada ou algum teste falhar.
Fotografa (tamanho, mtime, sha256) a pasta v5, a etapa 2 e a saída .frzero da aquisição antes e depois. Rede vedada.
"""
import argparse
import hashlib
import inspect
import json
import os
import socket
import sys
from pathlib import Path

V5 = "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa3_correcoes_v5_29-09/correcoes/aquisicao"
FOTOGRAFAR = (V5, "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa2_29-09",
              ".frzero/validacao_externa_aquisicao_29-09")


def sha(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def fotografa(principal):
    foto = {}
    for rel in FOTOGRAFAR:
        base = Path(principal) / rel
        for p in sorted(base.rglob("*")) if base.exists() else []:
            if p.is_file():
                st = p.stat()
                foto[str(p.relative_to(principal))] = (st.st_size, st.st_mtime_ns, sha(p))
    return foto


def sem_rede(*a, **k):
    raise AssertionError("rede real vedada no runner do S7")


def identidade(etapa, worktree, esperado):
    alvo = (Path(worktree) / "src/builder/sources/moodle.py").resolve()
    reg = {"etapa": etapa, "alvo": str(alvo), "sha_esperado": esperado}
    try:
        m = sys.modules["src.builder.sources.moodle"]
        reg["modulo_file"] = str(Path(m.__file__).resolve())
        reg["fonte_da_classe"] = str(Path(inspect.getsourcefile(m.MoodleClient)).resolve())
        reg["sha_carregado"] = sha(m.__file__)
        a = sys.modules.get("adquire")
        reg["adquire_M_e_o_mesmo_modulo"] = None if a is None else a.M is m
        reg["adquire_file"] = None if a is None else str(Path(a.__file__).resolve())
        reg["ok"] = (reg["modulo_file"] == str(alvo) and reg["fonte_da_classe"] == str(alvo)
                     and reg["sha_carregado"] == esperado and reg["adquire_M_e_o_mesmo_modulo"] in (None, True))
    except Exception as e:  # identidade indeterminável conta como divergência
        reg["erro"], reg["ok"] = repr(e), False
    return reg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worktree", required=True)
    p.add_argument("--principal", required=True)
    p.add_argument("--sha-esperado", required=True)
    p.add_argument("--basetemp", required=True)
    p.add_argument("--saida", required=True)
    args = p.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede

    aquisicao = Path(args.principal) / V5
    antes = fotografa(args.principal)
    saida = {"python": sys.version, "executavel": sys.executable,
             "runner": {"arquivo": str(Path(__file__).resolve()), "sha256": sha(__file__)},
             "fontes_v5_antes": {k: v[2] for k, v in antes.items() if k.startswith(V5.replace("/", os.sep))},
             "identidades": []}

    sys.path.insert(0, str(Path(args.worktree).resolve()))
    import src.builder.sources.moodle  # noqa: F401  (1)
    saida["identidades"].append(identidade("1: import da worktree", args.worktree, args.sha_esperado))

    sys.path.insert(0, str(aquisicao))
    import adquire  # noqa: F401  (2) do caminho original; põe a raiz da principal no sys.path
    saida["sys_path_inicio_apos_adquire"] = sys.path[:3]
    saida["identidades"].append(identidade("3: depois de carregar adquire.py", args.worktree, args.sha_esperado))

    rc = None
    if all(i["ok"] for i in saida["identidades"]):
        import pytest
        rc = int(pytest.main([str(aquisicao), "-p", "no:cacheprovider", f"--basetemp={args.basetemp}", "-rfEs"]))
    saida["pytest_exit"] = rc
    saida["identidades"].append(identidade("5: depois do pytest", args.worktree, args.sha_esperado))
    saida["outros_modulos_src_carregados"] = sorted(
        f"{n} -> {getattr(m, '__file__', None)}" for n, m in sys.modules.items()
        if n.startswith("src.") and n != "src.builder.sources.moodle" and getattr(m, "__file__", None))

    depois = fotografa(args.principal)
    saida["principal_alterada"] = sorted(k for k in set(antes) | set(depois) if antes.get(k) != depois.get(k))
    ok = all(i["ok"] for i in saida["identidades"]) and rc == 0 and not saida["principal_alterada"]
    saida["resultado"] = "ok" if ok else "falhou"
    Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"identidades {[i['ok'] for i in saida['identidades']]} | pytest {rc} | "
          f"principal alterada {saida['principal_alterada'] or 'nada'} | {saida['resultado']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
