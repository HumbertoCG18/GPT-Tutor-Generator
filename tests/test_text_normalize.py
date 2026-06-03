from src.builder.text.normalize import normalize_match_text


def test_strips_accents_and_lowercases():
    assert normalize_match_text("Lógica de Predicados") == "logica de predicados"


def test_collapses_whitespace_and_symbols():
    assert normalize_match_text("P1 - Prova!!  final") == "p1 prova final"


def test_typo_fix_propocional():
    assert normalize_match_text("propocional") == "proposicional"


def test_empty_and_none():
    assert normalize_match_text("") == ""
    assert normalize_match_text(None) == ""
