from src.builder.routing.sequence import extract_lecture_ordinal


def test_extracts_ordinal_after_aula_marker():
    assert extract_lecture_ordinal("aula 03 slides") == 3


def test_extracts_ordinal_with_single_digit():
    assert extract_lecture_ordinal("aula 3") == 3


def test_extracts_ordinal_after_encontro_marker():
    assert extract_lecture_ordinal("encontro 2 logica") == 2


def test_extracts_ordinal_when_glued_to_marker():
    # "Aula03.pdf" normaliza para "aula03 pdf" (sem espaco)
    assert extract_lecture_ordinal("aula03 pdf") == 3


def test_picks_digit_adjacent_to_marker_not_trailing_year():
    assert extract_lecture_ordinal("aula 03 2024") == 3


def test_returns_none_for_lista_marker():
    assert extract_lecture_ordinal("lista 2 inducao") is None


def test_returns_none_for_prova_marker():
    assert extract_lecture_ordinal("prova 1") is None


def test_returns_none_for_subchapter_pair():
    # "Capitulo 5.12" normaliza para "capitulo 5 12" -> sem marcador de aula
    assert extract_lecture_ordinal("capitulo 5 12 introducao") is None


def test_returns_none_for_bare_year():
    assert extract_lecture_ordinal("slides 2024 revisao") is None


def test_returns_none_for_roman_numeral():
    assert extract_lecture_ordinal("aula iii predicados") is None


def test_returns_none_when_no_ordinal():
    assert extract_lecture_ordinal("slides de logica") is None


def test_returns_none_for_year_glued_to_marker():
    # "aula2024" nao deve casar (mais de 3 digitos colados, sem fronteira)
    assert extract_lecture_ordinal("aula2024 revisao") is None


from src.builder.routing.sequence import annotate_class_ordinals


def _blocks():
    return [
        {"id": "b1", "kind": "class"},
        {"id": "b2", "kind": "class"},
        {"id": "b3", "kind": "holiday"},
        {"id": "b4", "kind": "review"},
        {"id": "b5", "kind": "class"},
    ]


def test_numbers_only_class_blocks_in_order():
    blocks = annotate_class_ordinals(_blocks())
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_block_without_kind_gets_none():
    blocks = annotate_class_ordinals([{"id": "x"}])
    assert blocks[0]["class_ordinal"] is None


def test_is_idempotent():
    blocks = _blocks()
    annotate_class_ordinals(blocks)
    annotate_class_ordinals(blocks)
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_no_class_blocks_all_none():
    blocks = annotate_class_ordinals([{"id": "h", "kind": "holiday"}])
    assert blocks[0]["class_ordinal"] is None


from src.builder.routing.thresholds import T


def test_sequence_boost_is_moderate_tiebreaker():
    # Menor que data (0.30) e topico-compativel (0.48): desempata sem sobrepor.
    assert T.SEQUENCE_BOOST == 0.20
    assert T.SEQUENCE_BOOST < 0.30
