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


def test_entry_signals_reexports_same_normalize():
    from src.builder.extraction.entry_signals import normalize_match_text as es_norm
    from src.builder.text.normalize import normalize_match_text as canon
    for s in ["Lógica", "P1 - Prova", "Máquina de Turing", "propocional", ""]:
        assert es_norm(s) == canon(s)


import importlib
import pytest


# Modulos cuja normalize e IDENTICA a canonica (inclui o fix de typo
# `propocional`). Apenas estes sao consolidados na Task 0.3. Os demais
# (timeline.signals, vision.card_evidence, extraction.image_markdown) NAO
# aplicam o fix de typo e content_taxonomy mantem `+-./` e dashes -> divergem,
# por isso ficam de fora.
@pytest.mark.parametrize("mod,attr", [
    ("src.builder.artifacts.pedagogy", "_normalize_match_text"),
    ("src.builder.timeline.index", "_normalize_match_text"),
])
def test_modules_match_canonical(mod, attr):
    from src.builder.text.normalize import normalize_match_text as canon
    m = importlib.import_module(mod)
    fn = getattr(m, attr)
    for s in ["Lógica de Predicados", "P1 - Prova!!", "Hierarquia de Chomsky", "propocional", ""]:
        assert fn(s) == canon(s), f"{mod}.{attr} diverge em {s!r}"
