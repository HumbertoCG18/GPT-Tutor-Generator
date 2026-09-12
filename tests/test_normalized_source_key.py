"""normalized_source_key: chave canônica de source_path (dedup de UI)."""

from src.utils.helpers import normalized_source_key


def test_url_passthrough_casefolded():
    assert normalized_source_key("HTTPS://Ex.com/A") == "https://ex.com/a"


def test_empty():
    assert normalized_source_key("") == ""
    assert normalized_source_key(None) == ""


def test_path_normalized_forward_slashes_casefold():
    out = normalized_source_key("C:\\Foo\\..\\Foo\\Bar.PDF")
    assert "\\" not in out
    assert out == out.casefold()
    assert out.endswith("foo/bar.pdf")
