"""read_only probe (Plano B): rebuild_timeline.py em dry-run (padrao, sem
--write) deve ser leitura de verdade. O script tem seu proprio flag WRITE
que hoje so controla se ELE grava .timeline_index.json — mas o helper
interno (_build_file_map_timeline_context_from_course) grava
ledger/manifest/curation quando persist=True (default), independente do
WRITE do script. rebuild_course deve passar persist=WRITE explicitamente:
dry-run vira read-only de verdade; --write preserva o comportamento atual."""
import types

import scripts.rebuild_timeline as rt


class _FakeSubjectProfile:
    def __init__(self, repo_root):
        self.repo_root = str(repo_root)


def _patch_ctx_builder(monkeypatch, captured):
    def _fake(course_meta, subject_profile, *, content_taxonomy=None, persist=True):
        captured["persist"] = persist
        return {"timeline_index": {"version": 4, "blocks": []}}

    monkeypatch.setattr(rt.engine, "_build_file_map_timeline_context_from_course", _fake)


def test_rebuild_course_dry_run_passes_persist_false(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "WRITE", False)
    captured = {}
    _patch_ctx_builder(monkeypatch, captured)

    sp = _FakeSubjectProfile(tmp_path)
    ok = rt.rebuild_course("X", sp)

    assert ok is True
    assert captured.get("persist") is False


def test_rebuild_course_write_mode_passes_persist_true(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "WRITE", True)
    captured = {}
    _patch_ctx_builder(monkeypatch, captured)

    sp = _FakeSubjectProfile(tmp_path)
    ok = rt.rebuild_course("X", sp)

    assert ok is True
    assert captured.get("persist") is True
