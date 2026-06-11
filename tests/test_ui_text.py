from src.ui.ui_text import default_source_label


def test_default_source_label_with_subject():
    assert default_source_label("Cálculo I") == "Padrões da matéria «Cálculo I»"


def test_default_source_label_no_subject_sentinel():
    assert default_source_label("(nenhuma)") == "Padrões globais (Configurações)"


def test_default_source_label_empty_and_none():
    assert default_source_label("") == "Padrões globais (Configurações)"
    assert default_source_label(None) == "Padrões globais (Configurações)"


def test_default_source_label_strips_whitespace():
    assert default_source_label("  Física  ") == "Padrões da matéria «Física»"
