from src.builder.extraction.content_taxonomy import _card_scoped_block

UNITS = [{"slug": "u-verif", "title": "Verificação de Programas", "topics": ["hoare"], "distinctive_tokens": []}]
BLOCKS = [
    {"id": "bloco-10", "unit_slug": "u-verif", "period_start": "2026-04-27", "period_end": "2026-05-04"},
    {"id": "bloco-11", "unit_slug": "u-verif", "period_start": "2026-05-06", "period_end": "2026-05-06"},
    {"id": "bloco-01", "unit_slug": "u-intro", "period_start": "2026-03-02", "period_end": "2026-03-02"},
]


def _score_stub(entry, md, scoped, unit_slug, topic_slug):
    return scoped[-1], 0.7


def test_card_single_block_is_chosen_with_high_conf():
    entry = {"source_section": "Introdução"}
    units = [{"slug": "u-intro", "title": "Introdução", "topics": [], "distinctive_tokens": []}]
    bid, conf, method = _card_scoped_block(entry, "", units, BLOCKS, {}, _score_stub)
    assert bid == "bloco-01"
    assert conf >= 0.8
    assert method == "card"


def test_card_wide_uses_scorer_restricted_to_card_blocks():
    entry = {"source_section": "Verificação de Programas"}
    bid, conf, method = _card_scoped_block(entry, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "bloco-11"
    assert conf == 0.7
    assert method == "card+scorer"


def test_no_card_returns_none():
    bid, conf, method = _card_scoped_block({"source_section": ""}, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "" and conf == 0.0


def test_card_with_no_matching_blocks_returns_none():
    bid, conf, method = _card_scoped_block({"source_section": "Card Fantasma"}, "", UNITS, BLOCKS, {}, _score_stub)
    assert bid == "" and conf == 0.0
