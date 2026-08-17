"""Ordem do pipeline de regeneração (re-versionado no cutover passo 3).

Pós-funil: refresh_manifest_auto_tags -> attach_block_summary_fields ->
apply_concept_resolver -> apply_unit_subunit_fields. O attach (caminho de
CÓDIGO, consenso D1) roda ANTES do motor; o motor decide por cima com a
curation como sinal (llm_curation) — invariante da cadeia testado também em
test_routing (passo 2, gap 1.2).
"""
import inspect

from src.builder.ops import pedagogical_regeneration as pr


def test_attach_runs_before_concept_resolver():
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    i_attach = src.find("attach_block_summary_fields(")
    i_apply = src.find("apply_concept_resolver(")
    i_unit = src.find("apply_unit_subunit_fn(")
    assert i_attach != -1 and i_apply != -1 and i_unit != -1
    assert i_attach < i_apply < i_unit, (
        "ordem quebrada: attach deve preceder o motor; unit/subunit fecham a cadeia"
    )


def test_regenerate_pedagogical_files_e2e_locks_call_order(tmp_path, monkeypatch):
    """e2e: trava em RUNTIME a ordem refresh_manifest_auto_tags ->
    attach_block_summary_fields -> apply_concept_resolver ->
    apply_unit_subunit_fields via regenerate_pedagogical_files real
    (fixture minima; flag ausente = motor ON, default do cutover)."""
    from src.models.core import StudentProfile, SubjectProfile
    from src.builder import engine as engine_mod
    from src.builder.routing import resolver_apply as ra

    calls = []

    def _spy(name, fn):
        def _wrapped(*args, **kwargs):
            calls.append(name)
            return fn(*args, **kwargs)
        return _wrapped

    monkeypatch.setattr(
        engine_mod, "_refresh_manifest_auto_tags",
        _spy("refresh_manifest_auto_tags", engine_mod._refresh_manifest_auto_tags),
    )
    monkeypatch.setattr(
        pr, "attach_block_summary_fields",
        _spy("attach_block_summary_fields", pr.attach_block_summary_fields),
    )
    monkeypatch.setattr(
        ra, "apply_concept_resolver",
        _spy("apply_concept_resolver", ra.apply_concept_resolver),
    )
    monkeypatch.setattr(
        engine_mod, "_apply_unit_subunit_fields",
        _spy("apply_unit_subunit_fields", engine_mod._apply_unit_subunit_fields),
    )

    repo = tmp_path / "repo"
    builder = engine_mod.RepoBuilder(
        repo,
        {
            "course_name": "Métodos Formais", "course_slug": "metodos-formais",
            "semester": "2026/1", "professor": "Prof", "institution": "PUCRS",
        },
        [],
        {},
        student_profile=StudentProfile(),
        subject_profile=SubjectProfile(name="Métodos Formais", slug="metodos-formais"),
    )
    builder._create_structure()
    (repo / "content" / "curated" / "item.md").write_text("# Exercicios\n", encoding="utf-8")
    manifest = {
        "entries": [
            {
                "id": "item",
                "title": "item",
                "category": "listas",
                "file_type": "pdf",
                "source_path": "raw/lista.pdf",
                "base_markdown": "content/curated/item.md",
                "tags": "",
            }
        ]
    }

    builder._regenerate_pedagogical_files(manifest)

    assert calls == [
        "refresh_manifest_auto_tags",
        "attach_block_summary_fields",
        "apply_concept_resolver",
        "apply_unit_subunit_fields",
    ], calls
