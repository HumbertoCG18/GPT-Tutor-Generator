"""R-PAGE no gerador do pacote cego v5 (HTML principal = `index.html`, `filepath "/"`, `filesize 0`; exatamente um).
Escritos ANTES das correções. Regra operacional provisória, inferida das respostas locais (inclusive o lote)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gera_pacote_cego as G  # noqa: E402
from test_pacote_cego import carrega, escreve, fixture  # noqa: E402

PAGINA_HTML = b"<html><body>Tutorial</body></html>"


def idx(**k):
    c = {"type": "file", "filename": "index.html", "filepath": "/", "filesize": 0}
    c.update(k)
    return {x: v for x, v in c.items() if v is not None}


def com_pagina(tmp, conteudos, arquivos_pagina=("index.html",), inventario=False):
    """Fixture da API com a página 501 com `conteudos`; grava raw/moodle/pages/501-<nome> para cada nome dado."""
    fonte = fixture(tmp)
    raiz = Path(fonte["moodle_dir"])
    for q in (raiz / "raw/moodle/pages").glob("*"):
        q.unlink()
    for nome in arquivos_pagina:
        escreve(raiz / f"raw/moodle/pages/501-{nome}", PAGINA_HTML if nome == "index.html" else b"<p>anexo</p>")
    api = carrega(raiz / "raw/moodle/contents.json")
    api[1]["modules"][2]["contents"] = conteudos
    escreve(raiz / "raw/moodle/contents.json", json.dumps(api))
    if inventario:
        def reg(mid, modname, arquivo, caminho=None, status="ok", base=None, papel=None):
            r = {"secao": "", "modulo_id": str(mid), "modname": modname, "arquivo": arquivo, "tamanho_api": 0, "status": status}
            if caminho:
                b = (raiz / caminho).read_bytes() if base is None else b"<p>anexo</p>"
                r.update(caminho=caminho, sha256=G.sha_b(b), bytes=len(b))
            return {**r, **({"base": base} if base else {}), **({"papel": papel} if papel else {})}

        regs = [reg(402, "resource", "aula1.pdf", "stash/Geral/aula1.pdf"), reg(403, "url", "Site do livro", status="link_externo"),
                reg(405, "resource", "aula1.pdf", "stash/Unidade 1/aula1.pdf"), reg(406, "resource", "lista1.pdf", "stash/Unidade 1/lista1.pdf"),
                reg(407, "assign", "enunciado.pdf", status="tipo_inesperado")]
        for c in conteudos:
            principal = c.get("filename") == "index.html" and c.get("filepath") == "/" and c.get("filesize") == 0
            regs.append(reg(501, "page", c["filename"], "raw/moodle/pages/501-index.html", papel="html_principal") if principal
                        else reg(501, "page", c["filename"], "501-" + c["filename"], base="anexos_de_pagina", papel="anexo_de_pagina"))
        inv = {"esquema": "inventario-downloads-3", "concluido": True, "cursos": [{"id": "999", "arquivos": regs}]}
        escreve(tmp / "aquisicao/inventario_downloads.json", json.dumps(inv))
        fonte.update(inventario=str(tmp / "aquisicao/inventario_downloads.json"), curso_id="999",
                     inventario_sha256=G.sha_b((tmp / "aquisicao/inventario_downloads.json").read_bytes()))
    return fonte


def mats_pagina(p):
    return sorted((m["tipo"], m["adjudicavel"], m["nome_original"]) for m in carrega(p / "materiais.json")["materiais"]
                  if m["ocorrencias"][0]["modulo"] == "Tutorial")


def test_com_inventario_anexo_html_nao_e_o_html_principal(tmp_path):
    fonte = com_pagina(tmp_path, [{"type": "file", "filename": "notas.html", "filepath": "/", "filesize": 12}, idx()],
                       inventario=True)
    G.monta(fonte, tmp_path / "pacote")
    assert G.audita(fonte, tmp_path / "pacote") == []
    assert mats_pagina(tmp_path / "pacote") == [("anexo_de_pagina", False, "notas.html"), ("pagina", True, "501-index.html")]


def test_com_inventario_colisao_com_index_html_de_anexo(tmp_path):
    fonte = com_pagina(tmp_path, [idx(filesize=26), idx()], inventario=True)
    G.monta(fonte, tmp_path / "pacote")
    assert G.audita(fonte, tmp_path / "pacote") == []
    assert mats_pagina(tmp_path / "pacote") == [("anexo_de_pagina", False, "index.html"), ("pagina", True, "501-index.html")]


@pytest.mark.parametrize("conteudos", [[], [idx(filepath=None)], [idx(filesize=None)], [idx(), idx()]],
                         ids=["sem-conteudos", "sem-filepath", "sem-filesize", "dois-candidatos"])
def test_sem_html_principal_unico_fica_nao_coberto(tmp_path, conteudos):
    fonte = com_pagina(tmp_path, conteudos)
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    tipos = [t for t in mats_pagina(p) if t[0] != "anexo_de_pagina"]
    assert tipos == [("pagina_sem_html_principal", False, "index.html")]
    nao_usados = {x["fonte"]: x["motivo"] for x in carrega(p / "pacote_manifesto.json")["fontes_nao_usadas"]}
    assert "página" in nao_usados["moodle:raw/moodle/pages/501-index.html"]


def test_sem_inventario_candidato_unico_sem_arquivo_local(tmp_path):
    fonte = com_pagina(tmp_path, [idx()], arquivos_pagina=())
    G.monta(fonte, tmp_path / "pacote")
    assert mats_pagina(tmp_path / "pacote") == [("pagina_sem_fonte_local", False, "index.html")]


def test_sem_inventario_arquivo_de_anexo_html_na_pasta_de_paginas_nao_vira_sobra(tmp_path):
    fonte = com_pagina(tmp_path, [{"type": "file", "filename": "notas.html", "filepath": "/", "filesize": 12}, idx()],
                       arquivos_pagina=("index.html", "notas.html"))
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    assert mats_pagina(p) == [("anexo_de_pagina", False, "notas.html"), ("pagina", True, "501-index.html")]
    assert not any(m["nome_original"] == "501-notas.html" for m in carrega(p / "materiais.json")["materiais"])
