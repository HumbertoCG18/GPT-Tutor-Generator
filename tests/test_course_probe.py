import scripts.course_probe as cp


class _FakeSP:
    def __init__(self, root):
        self.repo_root = str(root)
        self.teaching_plan = ""


def test_probe_chama_pipeline_completo_na_ordem(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text('{"course": {}, "entries": []}', encoding="utf-8")
    calls = []
    monkeypatch.setattr(cp.engine, "_build_rich_content_taxonomy",
                        lambda *a, **k: calls.append("tax") or {"units": []})

    def _ctx(cm, sp, content_taxonomy=None, persist=True):
        calls.append(("ctx", persist))
        return {"timeline_index": {"version": 4, "blocks": []}}

    monkeypatch.setattr(cp.engine, "_build_file_map_timeline_context_from_course", _ctx)
    monkeypatch.setattr(cp.engine, "_persist_enriched_timeline_index",
                        lambda idx: calls.append("persist") or {"version": 4, "blocks": []})
    out = cp.compute_production_index(_FakeSP(tmp_path))
    assert calls == ["tax", ("ctx", False), "persist"]
    assert out["blocks"] == []
