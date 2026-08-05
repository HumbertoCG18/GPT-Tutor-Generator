import inspect
from src.builder.ops import pedagogical_regeneration as pr


def test_resolve_unit_block_tags_runs_before_attach_block_summary():
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    i_resolve = src.find("resolve_unit_block_tags_fn(")
    i_attach = src.find("attach_block_summary_fields(")
    assert i_resolve != -1 and i_attach != -1
    assert i_resolve < i_attach, "funil deve rodar antes do attach (consenso D1 depende disso)"


def test_regenerate_pedagogical_files_e2e_locks_call_order(tmp_path, monkeypatch):
    """e2e (T7b): trava em RUNTIME a ordem refresh_manifest_auto_tags ->
    resolve_unit_block_tags -> attach_block_summary_fields via
    regenerate_pedagogical_files real (fixture minima, nao so grep de fonte
    como o teste irmao acima). A precedencia de computed_block_method depende
    dela: attach_block_summary_fields roda DEPOIS e o caminho de codigo
    (consensus/llm_only) sobrescreve o method do funil por cima
    (content_taxonomy.py:1322-1330)."""
    from src.models.core import StudentProfile, SubjectProfile
    from src.builder import engine as engine_mod

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
        engine_mod, "_resolve_unit_block_tags",
        _spy("resolve_unit_block_tags", engine_mod._resolve_unit_block_tags),
    )
    monkeypatch.setattr(
        pr, "attach_block_summary_fields",
        _spy("attach_block_summary_fields", pr.attach_block_summary_fields),
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
        "resolve_unit_block_tags",
        "attach_block_summary_fields",
    ], calls
