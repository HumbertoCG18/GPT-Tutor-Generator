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
