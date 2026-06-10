"""Regra léxica: lista de revisão para prova (revisão + Pk) -> bloco de revisão
que precede a prova Pk."""

from src.builder.extraction.content_taxonomy import (
    review_list_block_for_entry,
    _exam_code_from_text,
    _exam_code_from_block,
)

BLOCKS = [
    {"id": "bloco-06", "kind": "class"},
    {"id": "bloco-07", "kind": "review"},
    {"id": "bloco-09", "kind": "assessment", "sessions": [{"label": "prova p1 prova"}]},
    {"id": "bloco-16", "kind": "class"},
    {"id": "bloco-17", "kind": "review"},
    {"id": "bloco-18", "kind": "assessment", "sessions": [{"label": "prova p2 prova"}]},
    {"id": "bloco-19", "kind": "assessment", "sessions": [{"label": "prova ps prova de substituicao"}]},
]


def test_review_list_routes_to_review_before_exam():
    assert review_list_block_for_entry({"title": "revisao_p1"}, BLOCKS) == "bloco-07"
    assert review_list_block_for_entry({"title": "revisao_p1_gabarito"}, BLOCKS) == "bloco-07"
    assert review_list_block_for_entry({"title": "revisao_p2"}, BLOCKS) == "bloco-17"
    assert review_list_block_for_entry({"title": "lista de revisao p2"}, BLOCKS) == "bloco-17"


def test_review_list_ignores_non_matching():
    assert review_list_block_for_entry({"title": "revisao"}, BLOCKS) == ""        # sem código de prova
    assert review_list_block_for_entry({"title": "CorrecaoTerminacao"}, BLOCKS) == ""  # sem 'revis'
    assert review_list_block_for_entry({"title": "prova_p1"}, BLOCKS) == ""       # é a prova, não revisão


def test_review_list_uses_source_path_when_no_title():
    e = {"title": "", "source_path": "C:/x/revisao_p1.pdf"}
    assert review_list_block_for_entry(e, BLOCKS) == "bloco-07"


def test_review_list_no_review_block_before_exam_returns_empty():
    blocks = [{"id": "b1", "kind": "assessment", "sessions": [{"label": "prova p1 prova"}]}]
    assert review_list_block_for_entry({"title": "revisao_p1"}, blocks) == ""


def test_exam_code_from_text():
    assert _exam_code_from_text("revisao p1") == "P1"
    assert _exam_code_from_text("prova ps") == "PS"
    assert _exam_code_from_text("g2 prova") == "G2"
    assert _exam_code_from_text("prova final") == "PF"
    assert _exam_code_from_text("nada aqui") == ""


def test_exam_code_from_block():
    assert _exam_code_from_block({"sessions": [{"label": "prova p2 prova"}]}) == "P2"
    assert _exam_code_from_block({"period_label": "exame"}) == "EXAME"
