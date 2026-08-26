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
