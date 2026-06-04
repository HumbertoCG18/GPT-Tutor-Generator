from src.models.core import FileEntry


def _minimal():
    return FileEntry(source_path="raw/x.pdf", file_type="pdf", category="material", title="X")


def test_required_fields_always_present():
    d = _minimal().to_dict()
    for k in ("source_path", "file_type", "category", "title"):
        assert k in d


def test_default_valued_fields_omitted():
    d = _minimal().to_dict()
    assert "ocr_language" not in d
    assert "force_ocr" not in d
    assert "auto_tags" not in d
    assert "notes" not in d


def test_non_default_fields_kept():
    e = _minimal()
    e.notes = "revisar"
    e.force_ocr = True
    d = e.to_dict()
    assert d["notes"] == "revisar"
    assert d["force_ocr"] is True


def test_round_trip_through_from_dict():
    e = _minimal()
    e.notes = "n"
    e.manual_tags = ["a"]
    again = FileEntry.from_dict(e.to_dict())
    assert again.notes == "n"
    assert again.manual_tags == ["a"]
    assert again.ocr_language == _minimal().ocr_language
