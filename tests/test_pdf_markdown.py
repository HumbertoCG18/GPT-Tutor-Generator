"""pdf_markdown: ActualText respeitado e OCR so sem texto nativo (2026-08-28)."""
from pathlib import Path

import pytest

from src.utils.pdf_markdown import (pdf_has_native_text, pdf_to_markdown, respect_actualtext,
                                    splice_fractions, stacked_fractions)

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("pymupdf4llm")

TCC_PLAN = Path("C:/Users/Humberto/Desktop/Moodle/teoria-da-computabilidade-e-complexidade/sem-secao/Plano de Ensino.pdf")
CG_SARC = Path(__file__).parent / "fixtures" / "cg" / "Cronograma2026-2.pdf"


def _pua(text: str) -> int:
    return sum(1 for c in text if 0xE000 <= ord(c) <= 0xF8FF)


def test_respect_actualtext_tira_a_flag_e_restaura():
    import pymupdf4llm.helpers.document_layout as layout
    antes = layout.FLAGS
    assert antes & pymupdf.TEXT_IGNORE_ACTUALTEXT, "premissa: a versao instalada ignora ActualText por default"
    with respect_actualtext():
        assert not (layout.FLAGS & pymupdf.TEXT_IGNORE_ACTUALTEXT)
    assert layout.FLAGS == antes


def test_fixture_cg_tem_texto_nativo_e_zero_pua():
    if not CG_SARC.exists():
        pytest.skip("fixture ausente")
    assert pdf_has_native_text(CG_SARC)
    assert _pua(pdf_to_markdown(CG_SARC)) == 0


def test_plano_tcc_formula_com_parenteses_e_mais():
    """Google Docs + Inter codifica `( + )` via /ActualText: G1 = (P1+P2+T)/3."""
    if not TCC_PLAN.exists():
        pytest.skip("PDF real do TCC ausente nesta maquina")
    md = pdf_to_markdown(TCC_PLAN)
    assert _pua(md) == 0
    assert "G1 = (P1+P2+T)/3" in md


SO_PLAN = Path("C:/Users/Humberto/Desktop/Moodle/sistemas-operacionais/Informações Gerais/Plano de Ensino.pdf")
MF_PLAN = Path("C:/Users/Humberto/Desktop/Moodle/metodos-formais-para-computacao/Plano de Ensino/plano.pdf")


def _pdf_sintetico(tmp_path, tabela=False):
    """Fracao desenhada como o Word/LaTeX: numerador, barra vetorial, denominador centrado.
    Com `tabela=True`, a mesma barra vira borda de tabela (bordas verticais + regua vizinha)."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Avaliacao:", fontsize=11)
    page.insert_text((72, 130), "G1 = P1 + P2 + TP", fontsize=11)      # numerador (com lhs no mesmo span)
    page.draw_line((100, 134), (170, 134), width=0.7)                     # barra
    page.insert_text((131, 146), "3", fontsize=11)                        # denominador centrado
    if tabela:
        page.draw_line((100, 110), (100, 160), width=0.7)
        page.draw_line((170, 110), (170, 160), width=0.7)
        page.draw_line((100, 160), (170, 160), width=0.7)
    page.insert_text((72, 180), "Onde: P1 - prova 1", fontsize=11)
    out = tmp_path / ("tabela.pdf" if tabela else "fracao.pdf")
    doc.save(str(out))
    return out


def test_fracao_empilhada_vira_divisao(tmp_path):
    pdf = _pdf_sintetico(tmp_path)
    fr = stacked_fractions(pdf)
    assert [(f["lhs"], f["numerator"], f["denominator"]) for f in fr] == [("G1 =", "P1 + P2 + TP", "3")]
    md = pdf_to_markdown(pdf)
    assert "G1 = (P1 + P2 + TP) / 3" in md
    assert not any(l.strip() == "3" for l in md.splitlines())


def test_borda_de_tabela_nao_e_fracao(tmp_path):
    assert stacked_fractions(_pdf_sintetico(tmp_path, tabela=True)) == []


def test_splice_denominador_na_mesma_linha_e_markdown_preservado():
    md = "## **G1 = P1 + P2 + TP**\n3\n\nOnde:\n"
    out = splice_fractions(md, [{"page": 0, "lhs": "G1 =", "numerator": "P1 + P2 + TP", "denominator": "3"}])
    assert out == "## **G1 = (P1 + P2 + TP) / 3**\n\nOnde:\n"
    md2 = "𝐺1 =[𝑃1 + 𝑃2 + 𝑀𝑇] 3 \nOnde: \n"
    out2 = splice_fractions(md2, [{"page": 0, "lhs": "𝐺1 =", "numerator": "𝑃1 + 𝑃2 + 𝑀𝑇", "denominator": "3"}])
    assert out2.splitlines()[0] == "G1 = (P1 + P2 + MT) / 3"


@pytest.mark.parametrize("pdf,esperado", [(SO_PLAN, "G1 = (P1 + P2 + TP) / 3"), (MF_PLAN, "G1 = (P1 + P2 + MT) / 3")])
def test_planos_reais_com_fracao(pdf, esperado):
    if not pdf.exists():
        pytest.skip("PDF real ausente nesta maquina")
    assert esperado in pdf_to_markdown(pdf)
