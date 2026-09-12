from src.ui.codes_panel import _code_row_label, _entry_filename


def test_label_prefers_inferred_title():
    assert _code_row_label({"inferred_title": "Tripla de Hoare"}, {"title": "hoare"}, "hoare") == "Tripla de Hoare"


def test_label_falls_back_to_entry_title():
    assert _code_row_label({}, {"title": "exemplos.zip"}, "exemplos-zip") == "exemplos.zip"


def test_label_falls_back_to_id():
    assert _code_row_label({}, {}, "exemplos-zip") == "exemplos-zip"


def test_entry_filename_basename_com_extensao():
    assert _entry_filename({"source_path": "C:/x/Modelos/exemplos.zip"}) == "exemplos.zip"


def test_entry_filename_lida_com_backslash():
    assert _entry_filename({"source_path": r"C:\x\Provas\exemplos.thy"}) == "exemplos.thy"


def test_entry_filename_vazio_quando_sem_source():
    assert _entry_filename({}) == ""
