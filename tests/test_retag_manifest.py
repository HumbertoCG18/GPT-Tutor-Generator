from scripts.retag_manifest import retag, summarize_changes


def test_summarize_counts_block_id_changes():
    before = [
        {"id": "a", "computed_block_id": "bloco-01"},
        {"id": "b", "computed_block_id": "bloco-05"},
        {"id": "c", "computed_block_id": "bloco-03"},
    ]
    after = [
        {"id": "a", "computed_block_id": "bloco-01"},   # igual
        {"id": "b", "computed_block_id": "bloco-04"},   # mudou
        {"id": "c", "computed_block_id": ""},           # virou orfao
    ]
    rep = summarize_changes(before, after)
    assert rep["total"] == 3
    assert rep["changed"] == 2
    assert {"id": "b", "from": "bloco-05", "to": "bloco-04"} in rep["changes"]
    assert {"id": "c", "from": "bloco-03", "to": ""} in rep["changes"]


def test_retag_passes_persist_false_to_timeline_context_builder(tmp_path, monkeypatch):
    """read_only probe (Plano B): retag() e leitura (mesmo com --write, quem
    grava o manifest.json e o proprio main(), depois de retag() retornar) —
    mas o helper interno (_build_file_map_timeline_context_from_course) grava
    ledger/manifest/curation quando persist=True (default). Sem persist=False
    explicito, "so ler" suja o repo-tutor mesmo sem --write (Task 4 §0)."""
    import src.builder.engine as engine_mod

    (tmp_path / "manifest.json").write_text('{"entries": []}', encoding="utf-8")

    captured = {}

    def _fake_ctx_builder(course_meta, subject_profile, *, persist=True, content_taxonomy=None):
        captured["persist"] = persist
        return {"blocks_by_unit": {}, "unassigned_blocks": [], "timeline_index": {"blocks": []}}

    monkeypatch.setattr(engine_mod, "_build_file_map_timeline_context_from_course", _fake_ctx_builder)

    retag(tmp_path, None)

    assert captured.get("persist") is False
