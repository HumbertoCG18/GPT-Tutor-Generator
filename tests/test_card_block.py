from src.builder.timeline.card_block import resolve_card_to_block, CardBlockResolution

UNITS = [
    {"slug": "u-intro", "title": "Introdução a Métodos Formais", "topics": ["motivação"], "distinctive_tokens": []},
    {"slug": "u-verif", "title": "Verificação de Programas", "topics": ["hoare", "dafny"], "distinctive_tokens": []},
]
BLOCKS = [
    {"id": "bloco-01", "unit_slug": "u-intro", "period_start": "2026-03-02", "period_end": "2026-03-02"},
    {"id": "bloco-10", "unit_slug": "u-verif", "period_start": "2026-04-27", "period_end": "2026-05-04"},
    {"id": "bloco-11", "unit_slug": "u-verif", "period_start": "2026-05-06", "period_end": "2026-05-06"},
]


def test_card_name_matches_unit_returns_its_blocks():
    r = resolve_card_to_block("Verificação de Programas", UNITS, BLOCKS)
    assert set(r.block_ids) == {"bloco-10", "bloco-11"}
    assert r.confidence > 0.0
    assert r.reason.startswith("unit:")


def test_card_partial_name_still_matches_unit():
    r = resolve_card_to_block("Verificacao de Programas (Hoare/Dafny)", UNITS, BLOCKS)
    assert set(r.block_ids) == {"bloco-10", "bloco-11"}


def test_card_with_date_maps_to_covering_block():
    r = resolve_card_to_block("Aula 06/05", UNITS, BLOCKS)
    assert r.block_ids == ["bloco-11"]
    assert r.reason.startswith("date:")


def test_unmatched_card_needs_confirmation():
    r = resolve_card_to_block("Bibliografia-Livros", UNITS, BLOCKS)
    assert r.block_ids == []
    assert r.confidence == 0.0
    assert r.reason == "needs-confirmation"
