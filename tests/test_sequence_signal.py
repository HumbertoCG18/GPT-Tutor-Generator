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
