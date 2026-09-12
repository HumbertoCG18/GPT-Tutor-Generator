"""Montador unico de taxonomia rica: sonda == producao por construcao.
Fixture minima com contrato real de manifest (id/category/review_status;
ver institutional.md §Contratos)."""
import json
from pathlib import Path

from src.builder.ops.taxonomy_inputs import build_rich_content_taxonomy


def test_montador_passa_entries_vivas_para_taxonomy_fn(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "course": {"name": "X"},
        "entries": [
            {"id": "a", "category": "material-de-aula", "review_status": "approved"},
            {"id": "b", "category": "material-de-aula", "review_status": "approved"},
        ],
    }), encoding="utf-8")
    seen = {}

    def fake_filter(root_dir, entries):
        seen["filter_args"] = (Path(root_dir), [e["id"] for e in entries])
        return entries[:1]  # simula filtro de vivas

    def fake_taxonomy(course_meta, subject_profile, manifest_entries=None):
        seen["entries_recebidas"] = [e["id"] for e in (manifest_entries or [])]
        return {"units": ["u"], "topics": []}

    out = build_rich_content_taxonomy(
        tmp_path, {"name": "X", "_repo_root": tmp_path}, None,
        taxonomy_fn=fake_taxonomy, filter_live_fn=fake_filter,
    )
    assert out == {"units": ["u"], "topics": []}
    assert seen["filter_args"][1] == ["a", "b"]      # leu o manifest real
    assert seen["entries_recebidas"] == ["a"]        # passou as VIVAS filtradas


def test_montador_sem_manifest_devolve_taxonomia_sem_entries(tmp_path):
    def fake_taxonomy(course_meta, subject_profile, manifest_entries=None):
        return {"units": [], "topics": [], "got": manifest_entries}
    out = build_rich_content_taxonomy(
        tmp_path, {}, None,
        taxonomy_fn=fake_taxonomy, filter_live_fn=lambda r, e: e,
    )
    assert out["got"] == []
