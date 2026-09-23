"""#64: cada regeneração grava em manifest["assignment_run"] o pedido, o efetivo, o executado e o fallback."""
from src.builder.ops import assignment_run as ar
from src.builder.ops import pedagogical_regeneration as pr


def test_new_run_separates_requested_from_effective():
    run = ar.new_run({"use_anchor_engine": True, "use_concept_resolver": False, "image_format": "png"})
    assert run["requested"] == {"use_anchor_engine": True, "use_concept_resolver": False}
    assert run["effective"] == {
        "use_concept_resolver": False, "use_anchor_engine": True, "use_llm_voter": False,
        "compile_vocabulary": False, "enable_material_residual": False,
    }
    assert not any(run["executed"].values()) and run["fallback"] == {}


def test_mark_records_fallback_only_for_enabled_layer():
    run = ar.new_run({"use_anchor_engine": True})
    ar.mark(run, "use_llm_voter", "voter_unavailable")
    ar.mark(run, "use_anchor_engine")
    assert run["fallback"] == {}
    assert run["executed"]["use_anchor_engine"] is True


def test_finish_run_marks_not_run_and_counts_stale_temporal():
    run = ar.new_run({"use_llm_voter": True, "use_concept_resolver": False})
    entries = [{"temporal_block_id": "uuid-1"}, {"computed_block_id": "bloco-02"},
               {"manual_timeline_block_id": "bloco-03"}, {}]
    ar.finish_run(run, entries, blocks=None)
    assert run["fallback"] == {"use_llm_voter": "not_run"}
    assert run["block_source"] == {"temporal_block_id_previous_run": 1, "manual_timeline_block_id": 1,
                                   "computed_block_id": 1, "none": 1}


def _regenerate(tmp_path, options, entries):
    from src.builder import engine as engine_mod
    from src.models.core import StudentProfile, SubjectProfile

    repo = tmp_path / "repo"
    builder = engine_mod.RepoBuilder(
        repo, {"course_name": "Curso", "course_slug": "curso", "semester": "2026/1",
               "professor": "Prof", "institution": "PUCRS"},
        [], options, student_profile=StudentProfile(),
        subject_profile=SubjectProfile(name="Curso", slug="curso"),
    )
    builder._create_structure()
    (repo / "content" / "curated" / "item.md").write_text("# Exercicios\n", encoding="utf-8")
    manifest = {"entries": [{"id": "item", "title": "item", "category": "listas", "file_type": "pdf",
                             "source_path": "raw/lista.pdf", "base_markdown": "content/curated/item.md",
                             "tags": "", **entries}]}
    builder._regenerate_pedagogical_files(manifest)
    return manifest["assignment_run"]


def test_regenerate_records_d9_executed_and_voter_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(pr, "_build_motor_voter", lambda builder: None)
    monkeypatch.setenv("TUTOR_NO_VOCAB_COMPILE", "1")
    run = _regenerate(tmp_path, {"use_anchor_engine": True, "use_llm_voter": True, "compile_vocabulary": True}, {})
    assert run["requested"] == {"use_anchor_engine": True, "use_llm_voter": True, "compile_vocabulary": True}
    assert run["executed"]["use_anchor_engine"] is True
    assert run["executed"]["use_concept_resolver"] is True
    assert run["fallback"] == {"use_llm_voter": "voter_unavailable", "compile_vocabulary": "kill_switch_env"}
    assert "temporal_block_id" in run["block_source"]


def test_regenerate_records_d9_error_as_fallback(tmp_path, monkeypatch):
    import src.builder.routing.motor.apply as motor_apply

    def _boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(pr, "_build_motor_voter", lambda builder: None)
    monkeypatch.setattr(motor_apply, "apply_anchor_engine", _boom)
    run = _regenerate(tmp_path, {"use_anchor_engine": True}, {})
    assert run["executed"]["use_anchor_engine"] is False
    assert run["fallback"] == {"use_anchor_engine": "error:RuntimeError"}


def test_regenerate_without_d9_flags_stale_temporal_from_previous_run(tmp_path):
    run = _regenerate(tmp_path, {}, {"temporal_block_id": "uuid-antigo"})
    assert run["requested"] == {}
    assert run["effective"]["use_anchor_engine"] is False
    assert run["executed"]["use_anchor_engine"] is False and run["fallback"] == {}
    assert run["block_source"]["temporal_block_id_previous_run"] == 1


def test_regenerate_voter_counts_as_executed_only_with_d9_and_flags_partial(tmp_path, monkeypatch):
    class _Voter:
        def prune(self, keys):
            return 0

        def round_summary(self):
            return {"calls": 2, "errors": 1, "skipped_cap": 0, "no_key": 0, "cache_hits": 3}

    monkeypatch.setattr(pr, "_build_motor_voter", lambda builder: _Voter())
    run = _regenerate(tmp_path, {"use_anchor_engine": True, "use_llm_voter": True}, {})
    assert run["executed"]["use_llm_voter"] is True
    assert run["fallback"] == {"use_llm_voter": "partial"}
    assert run["detail"]["use_llm_voter"]["errors"] == 1


def _vocab_run(tmp_path, monkeypatch, compiled):
    from types import SimpleNamespace
    from src.builder.core import vocabulary_compile
    from src.builder.extraction import content_taxonomy

    monkeypatch.delenv("TUTOR_NO_VOCAB_COMPILE", raising=False)
    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda builder: object())
    monkeypatch.setattr(content_taxonomy, "load_internal_content_taxonomy", lambda root: {})
    monkeypatch.setattr(vocabulary_compile, "compile_course_vocabulary", lambda *a, **k: compiled)
    run = ar.new_run({"compile_vocabulary": True})
    pr._run_vocabulary_compile_layer(SimpleNamespace(options={"compile_vocabulary": True}, root_dir=tmp_path), [], run)
    return run


def test_vocabulary_not_compiled_is_fallback_not_execution(tmp_path, monkeypatch):
    run = _vocab_run(tmp_path, monkeypatch, None)
    assert run["executed"]["compile_vocabulary"] is False
    assert run["fallback"] == {"compile_vocabulary": "not_compiled"}


def test_vocabulary_units_with_error_flag_partial(tmp_path, monkeypatch):
    run = _vocab_run(tmp_path, monkeypatch, {"_unidades_com_erro": ["u01"]})
    assert run["executed"]["compile_vocabulary"] is True
    assert run["fallback"] == {"compile_vocabulary": "partial"}
    assert run["detail"]["compile_vocabulary"] == {"units_with_error": 1}


def _residual_run(tmp_path, monkeypatch, blocks):
    from types import SimpleNamespace
    from src.builder.core import summary_core

    class _Client:
        def summarize_bundle(self, **kwargs):
            raise RuntimeError("api")

    def _summarize(root, orphans, blocks_, extract, cap):
        for o in orphans:
            extract(o["_text"])
        return {}

    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda builder: _Client())
    monkeypatch.setattr(summary_core, "summarize_residual_materials", _summarize)
    builder = SimpleNamespace(options={"enable_material_residual": True}, root_dir=tmp_path,
                              _load_timeline_blocks=lambda: blocks)
    run = ar.new_run(builder.options)
    pr.run_material_residual(builder, [{"id": "a", "title": "Aula"}], run)
    return run


def test_residual_without_blocks_is_fallback(tmp_path, monkeypatch):
    run = _residual_run(tmp_path, monkeypatch, [])
    assert run["executed"]["enable_material_residual"] is False
    assert run["fallback"] == {"enable_material_residual": "no_timeline_blocks"}


def test_residual_absorbed_errors_flag_partial(tmp_path, monkeypatch):
    run = _residual_run(tmp_path, monkeypatch, [{"id": "bloco-01", "block_uuid": "u1"}])
    assert run["executed"]["enable_material_residual"] is True
    assert run["fallback"] == {"enable_material_residual": "partial"}
    assert run["detail"]["enable_material_residual"] == {"orphans": 1, "errors": 1}
