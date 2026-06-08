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


from src.builder.timeline.card_block import (
    load_card_block_map, save_card_block_map, lookup_card_blocks,
)


def test_card_map_roundtrip(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    mapping = {"Meu Card": {"block_ids": ["bloco-07"], "source": "manual"}}
    save_card_block_map(course, mapping)
    assert load_card_block_map(course) == mapping


def test_load_missing_map_returns_empty(tmp_path):
    assert load_card_block_map(tmp_path / "course") == {}


def test_lookup_prefers_manual_map_over_auto():
    card_map = {"Verificação de Programas": {"block_ids": ["bloco-99"], "source": "manual"}}
    ids = lookup_card_blocks("Verificação de Programas", card_map, UNITS, BLOCKS)
    assert ids == ["bloco-99"]


def test_lookup_falls_back_to_auto_resolution():
    ids = lookup_card_blocks("Verificação de Programas", {}, UNITS, BLOCKS)
    assert set(ids) == {"bloco-10", "bloco-11"}


def test_single_token_card_matches_when_unambiguous():
    units = [
        {"slug": "u-verif", "title": "Verificação de Programas", "topics": ["dafny"], "distinctive_tokens": []},
        {"slug": "u-intro", "title": "Introdução", "topics": ["motivação"], "distinctive_tokens": []},
    ]
    blocks = [{"id": "bloco-10", "unit_slug": "u-verif", "period_start": "2026-04-27", "period_end": "2026-05-04"}]
    r = resolve_card_to_block("Dafny", units, blocks)
    assert r.block_ids == ["bloco-10"]


def test_tie_between_units_needs_confirmation():
    units = [
        {"slug": "u1", "title": "Lógica Proposicional", "topics": [], "distinctive_tokens": []},
        {"slug": "u2", "title": "Lógica Predicados", "topics": [], "distinctive_tokens": []},
    ]
    blocks = [
        {"id": "b1", "unit_slug": "u1", "period_start": "2026-03-02", "period_end": "2026-03-02"},
        {"id": "b2", "unit_slug": "u2", "period_start": "2026-03-09", "period_end": "2026-03-09"},
    ]
    # card "Lógica" casa 1 token com AMBAS -> empate -> needs-confirmation
    r = resolve_card_to_block("Lógica", units, blocks)
    assert r.block_ids == []
    assert r.reason == "needs-confirmation"


def test_date_day_differs_from_month():
    units = []
    blocks = [{"id": "bloco-01", "unit_slug": "u", "period_start": "2026-03-02", "period_end": "2026-03-02"}]
    r = resolve_card_to_block("Aula 02/03", units, blocks)  # DD/MM = 2 de março
    assert r.block_ids == ["bloco-01"]


def test_lookup_manual_empty_blocklist_wins():
    card_map = {"X": {"block_ids": [], "source": "manual"}}
    assert lookup_card_blocks("X", card_map, UNITS, BLOCKS) == []
