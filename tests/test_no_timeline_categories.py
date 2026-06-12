from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES


def test_references_en_esta_no_filtro():
    assert "references" in _NO_TIMELINE_CATEGORIES
    assert {"cronograma", "bibliografia", "referencias"} <= _NO_TIMELINE_CATEGORIES
