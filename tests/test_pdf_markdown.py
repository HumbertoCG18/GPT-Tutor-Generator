"""pdf_markdown: ActualText respeitado e OCR so sem texto nativo (2026-08-28)."""
from pathlib import Path

import pytest

from src.utils.pdf_markdown import pdf_has_native_text, pdf_to_markdown, respect_actualtext

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
