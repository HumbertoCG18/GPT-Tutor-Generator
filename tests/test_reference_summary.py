from unittest.mock import MagicMock
from src.builder.core.reference_summary import summarize_reference, ReferenceSummary


def test_returns_none_without_client():
    assert summarize_reference("algum texto", None) is None


def test_returns_none_on_empty_text():
    assert summarize_reference("   ", MagicMock()) is None


def test_returns_dict_with_summary_and_concepts():
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(
        inferred_title="Spring Security", summary="Framework de autenticacao.",
        concepts=["autenticacao", "oauth"],
    )
    out = summarize_reference("readme do spring security", client)
    assert out["summary"] == "Framework de autenticacao."
    assert out["concepts"] == ["autenticacao", "oauth"]


def test_returns_none_on_client_exception():
    client = MagicMock()
    client.summarize_bundle.side_effect = Exception("api down")
    assert summarize_reference("texto", client) is None


def test_batch_writes_only_curation(tmp_path):
    import json as _json
    from src.builder.core import reference_summary as rs
    root = tmp_path
    (root / "course").mkdir()
    manifest_blob = _json.dumps({"entries": [
        {"id": "r1", "category": "referencias", "file_type": "github-repo",
         "source_path": "https://github.com/a/b"}]})
    (root / "manifest.json").write_text(manifest_blob, encoding="utf-8")
    builder = type("B", (), {"root_dir": root})()
    units = [{"slug": "u1", "normalized_title": "x", "topic_phrases": [], "topic_tokens": [], "distinctive_tokens": []}]
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(inferred_title="t", summary="s", concepts=["c"])
    orig = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto fixo"
        rs.summarize_all_reference_entries(builder, units, client)
        rs.summarize_all_reference_entries(builder, units, client)  # 2a vez: cache
    finally:
        rs.fetch_reference_text = orig
    assert client.summarize_bundle.call_count == 1
    assert (root / "manifest.json").read_text(encoding="utf-8") == manifest_blob
    cur = _json.loads((root / "course" / "references_curation.json").read_text(encoding="utf-8"))
    assert cur["entries"]["r1"]["ref_summary"] == "s"


# --- escopo e higiene da curation (2026-08-18) ------------------------------

def test_categoria_references_entra_na_camada():
    """3 entries vivas com `category='references'` (MF 1, IA 2) nunca entravam:
    o vocabulario da UI diz `referencias`, mas o dado real tem 3 grafias."""
    from src.builder.core.reference_summary import _REFERENCE_CATEGORIES

    assert {"referencias", "references", "bibliografia"} <= _REFERENCE_CATEGORIES


def test_curation_poda_entries_que_sumiram_do_manifest(tmp_path):
    """ES2 tinha 6/6 orfas e TCC 2/2 (as-of 2026-08-18). code_curation ja poda."""
    import json as _json
    from src.builder.core import reference_summary as rs

    root = tmp_path
    (root / "course").mkdir()
    (root / "manifest.json").write_text(_json.dumps({"entries": [
        {"id": "viva", "category": "bibliografia", "source_path": "x.pdf"}]}), encoding="utf-8")
    (root / "course" / "references_curation.json").write_text(_json.dumps({"entries": {
        "viva": {"ref_summary": "", "ref_concepts": [], "computed_ref_unit": "u1"},
        "orfa": {"ref_summary": "sumiu do manifest", "ref_concepts": []},
    }}), encoding="utf-8")
    builder = type("B", (), {"root_dir": root})()

    orig = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto"
        out = rs.summarize_all_reference_entries(builder, [], None)
    finally:
        rs.fetch_reference_text = orig

    assert "viva" in out["entries"]
    assert "orfa" not in out["entries"]


def test_curation_grava_coverage_units_multi(tmp_path):
    import json as _json
    from src.builder.core import reference_summary as rs

    root = tmp_path
    (root / "course").mkdir()
    (root / "manifest.json").write_text(_json.dumps({"entries": [
        {"id": "r1", "category": "references", "source_path": "x.pdf"}]}), encoding="utf-8")
    units = [
        {"slug": "u-seg", "normalized_title": "seguranca",
         "topic_phrases": ["autenticacao e autorizacao"],
         "topic_tokens": ["autenticacao"], "distinctive_tokens": []},
        {"slug": "u-micro", "normalized_title": "microservicos",
         "topic_phrases": ["service discovery distribuido"],
         "topic_tokens": ["discovery"], "distinctive_tokens": []},
    ]
    builder = type("B", (), {"root_dir": root})()

    orig = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: (
            "autenticacao e autorizacao com service discovery distribuido")
        out = rs.summarize_all_reference_entries(builder, units, None)
    finally:
        rs.fetch_reference_text = orig

    rec = out["entries"]["r1"]
    assert isinstance(rec["coverage_units"], list) and len(rec["coverage_units"]) == 2
    assert {u["unit_slug"] for u in rec["coverage_units"]} == {"u-seg", "u-micro"}
    assert rec["computed_ref_unit"] in {"u-seg", "u-micro"}   # compat com o COURSE_MAP
