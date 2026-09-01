"""Passo 3 do holdout CG: export do SARC em PDF -> tabela markdown (fixture real da CG 2026/2)."""
from pathlib import Path

from scripts.build_course import sarc_pdf_to_table

FIX = Path(__file__).parent / "fixtures" / "cg" / "Cronograma2026-2.pdf"


def test_sarc_pdf_vira_tabela_com_todas_as_datas():
    md = sarc_pdf_to_table(FIX)
    rows = [l for l in md.splitlines() if l.startswith("|")][2:]
    assert len(rows) == 38
    assert rows[0] == "| 1 | TER | 04/08/2026 | JK | Apresentação da disciplina e Origens da CG | Aula |  |"
    assert rows[1] == "| 2 | QUI | 06/08/2026 | JK | Introdução à OpenGL | Aula | Retirar notebook |"
    assert "| 16 | QUI | 24/09/2026 | JK | Prova P1 | Prova |" in md
    assert "| 22 | TER | 20/10/2026 | JK | Semana Acadêmica | Evento Acadêmico |" in md
    assert "| 32 | TER | 24/11/2026 | JK | Prova PS | Prova de Substituição |" in md


def test_sarc_pdf_celulas_quebradas_nao_vazam_para_colunas_vizinhas():
    md = sarc_pdf_to_table(FIX)
    assert "| 8 | QUI | 27/08/2026 | JK | Processo de Visualização 2D - Recorte e mapeamento | Aula | Retirar notebook |" in md
    assert "Fundamentos JK" not in md and "CG & Aula" not in md


def test_sarc_html_vira_tabela_com_turma():
    """F12: export HTML publico do SARC -> tabela markdown + turma do cabecalho."""
    from scripts.build_course import sarc_html_to_table
    html = (
        "<html><body><span>98710-2 Laboratorio de Redes de Computadores (340) - 32/406</span>"
        "<table><tr><th>#</th><th>Dia</th><th>Data</th><th>Hora</th><th>Descri\u00e7\u00e3o</th>"
        "<th>Atividade</th><th>Recursos</th></tr>"
        "<tr><td>1</td><td>SEG</td><td>03/08/2026</td><td>LM 19:15 - 20:45</td>"
        "<td>Apresenta\u00e7\u00e3o da disciplina</td><td>Aula</td><td>Retirar notebook</td></tr>"
        "<tr><td>2</td><td>SEG</td><td>10/08/2026</td><td>LM 19:15 - 20:45</td>"
        "<td>Wireshark</td><td>Aula</td><td></td></tr></table></body></html>"
    )
    tabela, turma = sarc_html_to_table(html)
    assert turma == "340"
    linhas = tabela.strip().splitlines()
    assert linhas[0].startswith("| # | Dia | Data |")
    assert len(linhas) == 4  # header + separador + 2 datas
    assert "03/08/2026" in linhas[2] and "Wireshark" in linhas[3]
