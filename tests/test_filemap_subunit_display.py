from src.builder.artifacts.navigation import _display_subunit_slug


def test_manual_subunit_wins():
    entry = {
        "manual_subunit_slug": "sub-manual",
        "auto_tags": ["subunit:sub-auto"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == "sub-manual"


def test_gated_tag_used_when_no_manual():
    entry = {
        "auto_tags": ["unit:u1", "subunit:sub-auto", "bloco:bloco-01"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == "sub-auto"


def test_ungated_computed_is_not_surfaced():
    # Sem tag subunit: (nao passou no gate) -> FILE_MAP NAO mostra o best-effort.
    entry = {
        "auto_tags": ["unit:u1"],
        "computed_subunit_slug": "sub-computed",
    }
    assert _display_subunit_slug(entry) == ""


def test_empty_when_nothing():
    assert _display_subunit_slug({}) == ""
