"""Passo 2 do holdout CG: classificacao de links e paginas internas do Moodle (casos reais da CG 2026/2)."""
from scripts.moodle_pull import classify_page, classify_url

HOSTS = {"inf.pucrs.br"}


def test_url_pagina_do_site_do_professor_e_material():
    assert classify_url("Página sobre Geometria Computacional", "5 - Geometria Computacional",
                        "https://www.inf.pucrs.br/pinho/CG/Aulas/GeomComp/GeomComp.htm", HOSTS)[:2] == ("material-pagina", "snapshot")
    assert classify_url("Exercício sobre Remoção de Ruído", "8 - Manipulação de Imagens",
                        "https://www.inf.pucrs.br/pinho/CGII/Exercicios/RemocaoDeRuido/", HOSTS)[:2] == ("material-pagina", "snapshot")


def test_url_pdf_no_site_do_professor_baixa_direto():
    assert classify_url("Slides", "3 - Fundamentos", "http://www.inf.pucrs.br/pinho/CG/SlidesEmPDF/FundamentosMatematicos.pdf", HOSTS)[:2] == ("material-pdf", "download")


def test_url_youtube_e_video_referencia():
    assert classify_url("Aula gravada", "11 - Morfologia", "https://youtu.be/Wlorjfqy7Uw", HOSTS)[:2] == ("video", "referencia")


def test_url_card_de_bibliografia_vence_dominio():
    assert classify_url("Livro texto", "Bibliografia", "https://www.inf.pucrs.br/pinho/CG/Aulas/X.htm", HOSTS)[0] == "referencia"


def test_url_repositorio_e_referencia_e_desconhecido_vai_para_review():
    assert classify_url("Código", "2 - OpenGL", "https://github.com/x/y", HOSTS)[:2] == ("referencia", "referencia")
    assert classify_url("Ferramenta", "2 - OpenGL", "https://exemplo.org/app", HOSTS)[1] == "review"


def test_pagina_interna_nome_primeiro():
    lista = "<p>Exercícios</p>" + "".join(f'<a href="https://youtu.be/abcdef{i}">v</a>' for i in range(4))
    assert classify_page(lista, "Exercícios sobre Curvas")[0] == "material-pagina-moodle"
    assert classify_page('<a href="https://youtu.be/abcdef1">a</a><a href="https://youtu.be/abcdef2">b</a>', "Página com Vídeos sobre Mapeamento")[0] == "indice-videos"
    codigo = "<pre>" + "int main() { return 0; } " * 300 + "</pre>"
    assert classify_page(codigo, "Página com vídeos sobre INSTANCIAMENTO")[0] == "material-pagina-moodle"


def test_pagina_interna_sem_nome_decide_pelo_conteudo():
    videos = "".join(f'<a href="https://www.youtube.com/watch?v=abcdef{i}">v</a>' for i in range(5))
    assert classify_page(videos, "Sem pista")[0] == "indice-videos"
    assert classify_page("<p>" + "texto " * 400 + "</p>", "Sem pista")[0] == "material-pagina-moodle"


def test_url_do_sarc_e_cronograma_mesmo_em_card_de_plano():
    """F12: o export do SARC postado no Moodle e o cronograma da disciplina."""
    from scripts.moodle_pull import classify_url
    tipo, acao, sinal = classify_url(
        "Cronograma", "Plano de Ensino",
        "https://sarc.pucrs.br/Default/Export.aspx?id=abc&ano=2026&sem=2", set())
    assert (tipo, acao, sinal) == ("cronograma", "cronograma", "sarc")


def test_turma_do_shortname_e_do_export():
    """F12/F14: turma do shortname ("4646I-04310262" -> 310) x turma do cabecalho ("(330)")."""
    from scripts.moodle_pull import turma_do_export, turma_do_shortname
    assert turma_do_shortname("4646I-04310262") == "310"
    assert turma_do_shortname("98710-02340262") == "340"
    assert turma_do_shortname("4646M-04031261") == "031"
    assert turma_do_shortname("sem-padrao") == ""
    assert turma_do_export("<div>4646I-4 Laborat\u00f3rio de Sistemas Operacionais (330) - 32/410</div>") == "330"
    assert turma_do_export("<div>sem turma</div>") == ""


def test_resource_html_vai_para_o_stash_como_html_material():
    """Roteiro .html de resource entra no stash como .html (material, S6d) — antes era impresso em PDF
    (S6b fez .html virar tipo `html`; cru ele caia como codigo-professor, labs 2026/2)."""
    import scripts.moodle_pull as mp
    import types
    pull = object.__new__(mp.Pull)
    pull.stash = __import__("pathlib").Path("/tmp/stash"); pull.rawm = __import__("pathlib").Path("/tmp/raw")
    pull.root = __import__("pathlib").Path("/tmp"); pull.links = []; pull.labels = []
    pull.sections = []; pull.nomes = {}; pull.turma_moodle = ""; pull.dry = True; pull.browser = None
    sec = {"name": "[10/08] - Wireshark", "section": 4, "summary": "", "modules": [
        {"modname": "resource", "id": 1, "name": "Laboratório 1 - Wireshark",
         "contents": [{"filename": "Lab 1 - Wireshark.html", "fileurl": "http://x/f"}]}]}
    pull.c = types.SimpleNamespace(get_course_contents=lambda c: [sec],
                                   _call=lambda *a, **k: {"courses": [{"shortname": "98710-02340262"}]})
    import json as _json
    pull.snap = types.SimpleNamespace(write_links=lambda: None, pages={}, print_all=lambda: None)
    try:
        pull.run(340)
    except Exception:
        pass  # escrita de arquivos fora do escopo do teste (dry escreve jsons)
    rec = next(r for r in pull.links if r["nome"].startswith("Laborat"))
    assert rec["tipo"] == "material-pagina-arquivo" and rec["acao"] == "html"
    assert "Lab 1 - Wireshark.html" in "".join(pull.nomes.keys())


# --- S6d: paginas entram no stash como .html (nao impressas); regra (a): PDF ja impresso do mesmo stem vence ---

def _pull(tmp_path, contents, get_bytes):
    import types
    import scripts.moodle_pull as mp
    pull = object.__new__(mp.Pull)
    pull.root = tmp_path; pull.stash = tmp_path / "stash"; pull.rawm = tmp_path / "raw" / "moodle"
    pull.links = []; pull.labels = []; pull.sections = []; pull.nomes = {}; pull.turma_moodle = ""
    pull.dry = False; pull.pdf = True; pull.browser = None; pull.tok = "t"
    pull.c = types.SimpleNamespace(get_course_contents=lambda c: contents,
                                   _call=lambda *a, **k: {"courses": [{"shortname": "98710-02340262"}]})
    pull.get = lambda fileurl: get_bytes
    pull.get_plain = lambda url: get_bytes
    pull.snap = types.SimpleNamespace(write_links=lambda: None, pages={}, print_all=lambda: None, stash=None,
                                      saved=[], save_page=None, save_material=None)
    return pull


def _resource_html(name="Laboratório 1 - Wireshark", fname="Lab 1 - Wireshark.html"):
    return [{"name": "[10/08] - Wireshark", "section": 4, "summary": "", "modules": [
        {"modname": "resource", "id": 1, "name": name, "contents": [{"type": "file", "filename": fname, "fileurl": "http://x/f"}]}]}]


def test_resource_html_e_gravado_normalizado_no_stash(tmp_path):
    raw = '<html><head><meta charset="iso-8859-1"></head><body><p>Roteiro</p></body></html>'.encode("cp1252")
    pull = _pull(tmp_path, _resource_html(), raw)
    pull.run(340)
    dest = tmp_path / "stash" / "[10.08] - Wireshark" / "Lab 1 - Wireshark.html"
    assert dest.is_file()
    text = dest.read_text(encoding="utf-8")
    assert '<meta charset="utf-8">' in text and "iso-8859-1" not in text and "Roteiro" in text
    rec = next(r for r in pull.links if r["nome"].startswith("Laborat"))
    assert rec["acao"] == "html" and rec["destino"].endswith("Lab 1 - Wireshark.html")
    assert pull.nomes["[10.08] - Wireshark/Lab 1 - Wireshark.html"] == "Laboratório 1 - Wireshark"
    assert not list((tmp_path / "stash").rglob("*.pdf"))


def test_resource_html_nao_sobrescreve_pdf_ja_impresso(tmp_path):
    # regra (a), user 03/09: LR tem 4 labs .htm impressos em PDF; o .html so entra onde nao existe <stem>.pdf
    card = tmp_path / "stash" / "[10.08] - Wireshark"
    card.mkdir(parents=True)
    (card / "Lab 1 - Wireshark.pdf").write_bytes(b"%PDF")
    pull = _pull(tmp_path, _resource_html(), b"<html><body>x</body></html>")
    pull.run(340)
    assert not (card / "Lab 1 - Wireshark.html").exists()
    rec = next(r for r in pull.links if r["nome"].startswith("Laborat"))
    assert rec["acao"] == "pdf-existente" and rec["destino"].endswith("Lab 1 - Wireshark.pdf")
    assert "Lab 1 - Wireshark.html" not in "".join(pull.nomes.keys())


def test_mod_page_material_e_gravada_como_html_no_stash(tmp_path):
    contents = [{"name": "2 - Biblioteca OpenGL", "section": 2, "summary": "", "modules": [
        {"modname": "page", "id": 3770138, "name": "Exercícios", "url": "https://moodle.pucrs.br/mod/page/view.php?id=3770138",
         "contents": [{"type": "file", "filename": "index.html", "fileurl": "http://x/p"}]}]}]
    frag = '<div class="no-overflow"><p>Exercício 1: desenhe um polígono.</p></div>'.encode("utf-8")
    pull = _pull(tmp_path, contents, frag)
    pull.run(95106)
    dest = tmp_path / "stash" / "2 - Biblioteca OpenGL" / "exercicios.html"
    assert dest.is_file() and "desenhe um pol" in dest.read_text(encoding="utf-8")
    rec = next(r for r in pull.links if r["nome"] == "Exercícios")
    assert rec["tipo"] == "material-pagina-moodle" and rec["acao"] == "html"
    assert pull.nomes["2 - Biblioteca OpenGL/exercicios.html"] == "Exercícios"
    assert (tmp_path / "raw" / "moodle" / "pages" / "3770138-exercicios.html").is_file()


def test_snapshot_de_pagina_do_professor_vira_bundle_no_stash(tmp_path):
    contents = [{"name": "7 - Curvas Paramétricas", "section": 7, "summary": "", "modules": [
        {"modname": "url", "id": 1, "name": "Página sobre Curvas Paramétricas",
         "contents": [{"type": "url", "fileurl": "http://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm"}]},
        {"modname": "url", "id": 2, "name": "Outra página", "contents": [{"type": "url", "fileurl": "http://www.inf.pucrs.br/pinho/CG/Aulas/Intro/intro.htm"}]}]}]
    pull = _pull(tmp_path, contents, b"")
    calls = []
    def fake_save_page(url, card, kind, level, follow=True):
        calls.append(("page", url, card))
        stem = url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return {"url": url, "local": f"raw/site/x/{stem}.htm", "card": card, "title": stem, "images": []}

    def fake_save_material(rec, stash):
        calls.append(("material", rec["url"], str(stash)))
        stem = rec["local"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return stash / rec["card"] / stem / f"{stem}.htm"

    pull.snap.save_page = fake_save_page
    pull.snap.save_material = fake_save_material
    pull.run(95106)
    assert ("page", "http://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm", "7 - Curvas Paramétricas") in calls
    assert any(c[0] == "material" and c[1].endswith("Curvas.htm") for c in calls)
    rec = next(r for r in pull.links if r["nome"] == "Página sobre Curvas Paramétricas")
    assert rec["acao"] == "snapshot" and rec["destino"].endswith("Curvas.htm")
    assert pull.nomes["7 - Curvas Paramétricas/Curvas.htm"] == "Página sobre Curvas Paramétricas"
