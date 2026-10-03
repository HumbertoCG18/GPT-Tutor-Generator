"""Reprodutor dos casos da revisão da etapa 2 contra a v2 (executada em 29/09) e a v3 (esta etapa). Sem rede.

Fixtures sintéticas em diretório temporário; `urlopen` e cliente Moodle falsos. Grava `reprodutores_v2_v3.json`.
Uso: python reproduz_casos_revisao.py
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
E2 = AQUI.parents[1] / "validacao_externa_etapa2_29-09"
sys.path.insert(0, str(AQUI / "pacote_cego"))
sys.path.insert(0, str(AQUI / "aquisicao"))
import test_adquire_v3 as TA  # noqa: E402
import test_pacote_cego as TP  # noqa: E402
import test_pacote_cego_v3 as T3  # noqa: E402


def carrega(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VERSOES = {"v2": {"G": carrega("pacote_v2", E2 / "correcoes/pacote_cego/gera_pacote_cego.py"),
                  "A": carrega("adquire_v2", E2 / "aquisicao/adquire.py")},
           "v3": {"G": carrega("pacote_v3", AQUI / "pacote_cego/gera_pacote_cego.py"),
                  "A": carrega("adquire_v3", AQUI / "aquisicao/adquire.py")}}


def tenta(f):
    try:
        return f()
    except BaseException as exc:   # noqa: BLE001
        return {"excecao": type(exc).__name__, "mensagem": str(exc)[:600]}


def plano_com_predicao(G, tmp):
    fonte = TP.fixture(tmp)
    TP.escreve(Path(fonte["plano_texto"]), TP.PLANO + "\ncomputed_unit_slug: unidade-01\n")
    G.monta(fonte, tmp / "pacote")
    copiado = b"computed_unit_slug" in b"".join(q.read_bytes() for q in (tmp / "pacote/plano").iterdir())
    return {"auditoria": G.audita(fonte, tmp / "pacote"), "conteudo_copiado": copiado}


def zip_com_conteudo_proibido(G, tmp):
    fonte = TP.fixture(tmp, formato="pastas")
    z = T3.zip_bytes({"aula.txt": "Conteúdo", "anotacoes.txt": json.dumps({"computed_subunit_slug": "t1"})})
    TP.escreve(Path(fonte["moodle_dir"]) / "Unidade 1/material.zip", z)
    G.monta(fonte, tmp / "pacote")
    m = next(x for x in TP.carrega(tmp / "pacote/materiais.json")["materiais"] if x["nome_original"] == "material.zip")
    copiado = z in b"".join(q.read_bytes() for q in (tmp / "pacote").rglob("*") if q.is_file())
    return {"auditoria": G.audita(fonte, tmp / "pacote"), "tipo": m["tipo"], "adjudicavel": m["adjudicavel"],
            "bytes_copiados": copiado}


def origem_unico_candidato_outra_secao(G, tmp):
    a = {"rel": "stash/Secao A/slides.pdf", "sha": "x" * 64, "nome": "slides.pdf", "tamanho": 15}
    return {"pasta_pedida": "Secao B",
            "retornado": G.resolve_origem({"filename": "slides.pdf", "filesize": 15}, "Secao B", {("slides.pdf", 15): [a]})}


class _Rede:
    """urlopen falso instalado só durante o caso."""

    def __init__(self, A, respostas, orc):
        self.A, self.respostas, self.orc = A, respostas, orc

    def __enter__(self):
        self.antes = (self.A.urllib.request.urlopen, self.A.ORC)
        self.A.urllib.request.urlopen = lambda url, timeout=None: TA.Resposta(self.respostas[url])
        self.A.ORC = self.orc
        return self

    def __exit__(self, *a):
        self.A.urllib.request.urlopen, self.A.ORC = self.antes
        return False


def chama_baixa_curso(A, versao, cli, raiz, orc):
    if versao == "v2":
        return A.baixa_curso(cli, "curso", raiz, orc)
    arquivos = []
    A.baixa_curso(cli, "curso", raiz, orc, arquivos)
    return arquivos


def anexo_page_fora_da_raiz(A, versao, tmp):
    cli = TA.Cliente({"curso": [TA.secao("Geral", TA.modulo(1, "resource", TA.conteudo("a.txt", "u/a")),
                                         TA.modulo(2, "page", TA.conteudo("imagem.png", "u/img")))]})
    with _Rede(A, {"u/a": b"texto a", "u/img": TA.PNG}, {"bytes_por_arquivo_max": 100, "bytes_totais_max": 1000}):
        r = tenta(lambda: chama_baixa_curso(A, versao, cli, tmp / "downloads/curso", {"bytes": 0}))
    escritos = sorted(p.relative_to(tmp).as_posix() for p in tmp.rglob("*") if p.is_file())
    if isinstance(r, dict):
        r["mensagem"] = r["mensagem"].replace(str(tmp).replace("\\", "\\\\"), "<tmp>").replace(str(tmp), "<tmp>")[:200]
        return {"erro": r, "retornou_inventario": False, "arquivos_escritos": escritos}
    return {"retornou_inventario": True, "registros": [{k: a.get(k) for k in ("arquivo", "status", "base", "caminho")} for a in r],
            "arquivos_escritos": escritos}


def limite_confiado_ao_filesize(A, versao, tmp):
    cli = TA.Cliente({"curso": [TA.secao("S", TA.modulo(1, "resource", TA.conteudo("x.txt", "u/x", 1)))]})
    orc = {"bytes": 0}
    with _Rede(A, {"u/x": b"1234567"}, {"bytes_por_arquivo_max": 5, "bytes_totais_max": 5}):
        r = chama_baixa_curso(A, versao, cli, tmp / "c", orc)
    return {"limite_arquivo": 5, "limite_total": 5, "bytes_enviados": 7, "status": r[0]["status"], "bytes_contados": orc["bytes"]}


def main():
    out = {"metodo": "fixtures sintéticas, cliente e urlopen falsos; nenhuma rede, gold, build ou motor", "casos": {}}
    for versao, m in VERSOES.items():
        for nome, f in (("plano_com_predicao", plano_com_predicao), ("zip_real_conteudo_nao_examinado", zip_com_conteudo_proibido),
                        ("origem_unico_candidato_outra_secao", origem_unico_candidato_outra_secao)):
            with tempfile.TemporaryDirectory() as tmp:
                out["casos"].setdefault(nome, {})[versao] = tenta(lambda: f(m["G"], Path(tmp)))
        for nome, f in (("anexo_page_fora_da_raiz", anexo_page_fora_da_raiz), ("limite_confiado_ao_filesize", limite_confiado_ao_filesize)):
            with tempfile.TemporaryDirectory() as tmp:
                out["casos"].setdefault(nome, {})[versao] = tenta(lambda: f(m["A"], versao, Path(tmp)))
    texto = json.dumps(out, ensure_ascii=False, indent=1, default=str)
    (AQUI / "reprodutores_v2_v3.json").write_text(texto + "\n", encoding="utf-8", newline="\n")
    print(texto)


if __name__ == "__main__":
    main()
