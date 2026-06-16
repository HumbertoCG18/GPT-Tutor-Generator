from src.ui.codes_panel import _code_row_label


def test_label_prefers_inferred_title():
    assert _code_row_label({"inferred_title": "Tripla de Hoare"}, {"title": "hoare"}, "hoare") == "Tripla de Hoare"


def test_label_falls_back_to_entry_title():
    assert _code_row_label({}, {"title": "exemplos.zip"}, "exemplos-zip") == "exemplos.zip"


def test_label_falls_back_to_id():
    assert _code_row_label({}, {}, "exemplos-zip") == "exemplos-zip"
