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
