"""Propagação do match_rationale (Gemini) pro manifest + FileEntry."""

from src.models.core import FileEntry


def _entry(**kw):
    base = dict(source_path="C:/x/a.py", file_type="code", category="codigo-professor", title="test")
    base.update(kw)
    return FileEntry(**base)


def test_fileentry_roundtrip_preserves_rationale():
    e = _entry(computed_block_rationale="Usa listas e loops do bloco 5")
    d = e.to_dict()
    assert d["computed_block_rationale"] == "Usa listas e loops do bloco 5"
    assert FileEntry.from_dict(d).computed_block_rationale == "Usa listas e loops do bloco 5"


def test_fileentry_default_rationale_not_emitted():
    d = _entry().to_dict()
    assert "computed_block_rationale" not in d  # default "" não incha o manifest
    assert FileEntry.from_dict(d).computed_block_rationale == ""


from src.builder.ops.pedagogical_regeneration import attach_block_rationale


CURATION = {
    "entries": {
        "id-1": {"summary": {"match_rationale": "Demonstra recursão do bloco 3"}},
        "id-2": {"summary": {"match_rationale": "   "}},  # whitespace -> ignora
        "id-3": {},  # sem summary
    }
}


def test_attach_copies_rationale_for_matching_entry():
    entries = [{"id": "id-1", "title": "a"}]
    out = attach_block_rationale(entries, CURATION)
    assert out[0]["computed_block_rationale"] == "Demonstra recursão do bloco 3"


def test_attach_skips_blank_rationale_and_missing_summary():
    entries = [{"id": "id-2"}, {"id": "id-3"}, {"id": "id-9"}, {"title": "sem id"}]
    out = attach_block_rationale(entries, CURATION)
    for e in out:
        assert "computed_block_rationale" not in e


def test_attach_tolerates_empty_curation():
    entries = [{"id": "id-1"}]
    assert attach_block_rationale(entries, {}) == [{"id": "id-1"}]
    assert attach_block_rationale(entries, None) == [{"id": "id-1"}]
