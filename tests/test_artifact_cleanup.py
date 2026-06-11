def test_progress_schema_generator_removed():
    """O gerador morto progress_schema_md não deve mais existir."""
    import src.builder.artifacts.repo as repo
    assert not hasattr(repo, "progress_schema_md")


def test_build_progress_schema_in_stale_delete(tmp_path):
    """build/PROGRESS_SCHEMA.md deve ser limpo em repos existentes:
    o path precisa estar na lista de stale-delete da regeneração."""
    import inspect
    import src.builder.ops.pedagogical_regeneration as pr
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    assert '"build"' in src and 'PROGRESS_SCHEMA.md' in src
