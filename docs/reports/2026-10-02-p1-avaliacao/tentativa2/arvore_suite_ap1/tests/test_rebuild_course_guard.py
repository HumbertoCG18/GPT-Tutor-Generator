"""W2 (rebuild_course --write) ganha o mesmo guard de encolhimento do W1."""
import json
import pytest
from pathlib import Path

import scripts.rebuild_timeline as rt
from src.builder.ops.pedagogical_regeneration import UnitsShrinkError


class _Profile:
    teaching_plan = "**UNIDADE 1** A\n**UNIDADE 2** B\n**UNIDADE 3** C"
    syllabus = ""
    def __init__(self, root): self.repo_root = str(root)


def test_rebuild_write_aborta_em_encolhimento(tmp_path, monkeypatch):
    (tmp_path / "course").mkdir()
    (tmp_path / "manifest.json").write_text(json.dumps({"course": {"name": "X"}}), encoding="utf-8")
    # indice ANTIGO em disco: 3 unidades
    (tmp_path / "course" / ".timeline_index.json").write_text(json.dumps({
        "version": 3, "blocks": [
            {"id": "bloco-01", "kind": "class", "unit_slug": "u1"},
            {"id": "bloco-02", "kind": "class", "unit_slug": "u2"},
            {"id": "bloco-03", "kind": "class", "unit_slug": "u3"},
        ]}), encoding="utf-8")
    # build devolve indice ENCOLHIDO (1 unidade)
    shrunk = {"timeline_index": {"version": 3, "blocks": [
        {"id": "bloco-01", "kind": "class", "unit_slug": "u1"}]}}
    monkeypatch.setattr(rt.engine, "_build_file_map_timeline_context_from_course",
                        lambda *a, **k: shrunk)
    monkeypatch.setattr(rt, "WRITE", True, raising=False)
    before = (tmp_path / "course" / ".timeline_index.json").read_text(encoding="utf-8")
    ok = rt.rebuild_course("X", _Profile(tmp_path))
    after = (tmp_path / "course" / ".timeline_index.json").read_text(encoding="utf-8")
    assert after == before, "indice foi sobrescrito apesar do encolhimento"
    assert ok is False
