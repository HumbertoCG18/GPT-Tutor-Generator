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


def test_fileentry_roundtrip_preserves_match_fields():
    e = _entry(computed_block_method="consensus", computed_block_match_confidence=0.87)
    d = e.to_dict()
    assert d["computed_block_method"] == "consensus"
    assert d["computed_block_match_confidence"] == 0.87
    back = FileEntry.from_dict(d)
    assert back.computed_block_method == "consensus"
    assert back.computed_block_match_confidence == 0.87


def test_fileentry_default_match_fields_not_emitted():
    d = _entry().to_dict()
    assert "computed_block_method" not in d  # default "" não incha o manifest
    assert "computed_block_match_confidence" not in d  # default 0.0 idem
    back = FileEntry.from_dict(d)
    assert back.computed_block_method == ""
    assert back.computed_block_match_confidence == 0.0


from src.builder.ops.pedagogical_regeneration import attach_block_summary_fields


CURATION = {
    "entries": {
        "id-1": {"summary": {
            "match_rationale": "Demonstra recursão do bloco 3",
            "block_match_method": "consensus",
            "block_match_confidence": 0.91,
        }},
        "id-2": {"summary": {"match_rationale": "   "}},  # whitespace -> ignora
        "id-3": {},  # sem summary
    }
}


def test_attach_copies_rationale_for_matching_entry():
    entries = [{"id": "id-1", "title": "a"}]
    out = attach_block_summary_fields(entries, CURATION)
    assert out[0]["computed_block_rationale"] == "Demonstra recursão do bloco 3"


def test_attach_skips_blank_rationale_and_missing_summary():
    entries = [{"id": "id-2"}, {"id": "id-3"}, {"id": "id-9"}, {"title": "sem id"}]
    out = attach_block_summary_fields(entries, CURATION)
    for e in out:
        assert "computed_block_rationale" not in e


def test_attach_tolerates_empty_curation():
    entries = [{"id": "id-1"}]
    assert attach_block_summary_fields(entries, {}) == [{"id": "id-1"}]
    assert attach_block_summary_fields(entries, None) == [{"id": "id-1"}]


def test_attach_removes_stale_rationale():
    # curation foi pruned/reatribuída: justificativa antiga não pode sobreviver
    entries = [{"id": "id-9", "computed_block_rationale": "stale"}]
    out = attach_block_summary_fields(entries, CURATION)
    assert "computed_block_rationale" not in out[0]


def test_attach_copies_match_fields_for_matching_entry():
    entries = [{"id": "id-1", "title": "a"}]
    out = attach_block_summary_fields(entries, CURATION)
    assert out[0]["computed_block_method"] == "consensus"
    assert out[0]["computed_block_match_confidence"] == 0.91


def test_attach_skips_match_fields_when_missing_summary():
    entries = [{"id": "id-2"}, {"id": "id-3"}, {"id": "id-9"}]
    out = attach_block_summary_fields(entries, CURATION)
    for e in out:
        assert "computed_block_method" not in e
        assert "computed_block_match_confidence" not in e


def test_attach_removes_stale_match_fields():
    entries = [{"id": "id-9", "computed_block_method": "orphan",
                "computed_block_match_confidence": 0.4}]
    out = attach_block_summary_fields(entries, CURATION)
    assert "computed_block_method" not in out[0]
    assert "computed_block_match_confidence" not in out[0]


def test_attach_drops_nonnumeric_match_confidence():
    curation = {"entries": {"id-1": {"summary": {"block_match_confidence": "abc"}}}}
    entries = [{"id": "id-1", "computed_block_match_confidence": 0.5}]
    out = attach_block_summary_fields(entries, curation)
    assert "computed_block_match_confidence" not in out[0]
