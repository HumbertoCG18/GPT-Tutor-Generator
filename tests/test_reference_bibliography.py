from types import SimpleNamespace
from src.builder.artifacts.repo import bibliography_md


def _entry(**kw):
    base = dict(title="GitHub - a/b", source_path="https://github.com/a/b", tags="",
                notes="", professor_signal="", include_in_bundle=True,
                ref_summary="", computed_ref_unit="", computed_ref_topics=[])
    base.update(kw)
    return SimpleNamespace(**base)


def _bib(entries):
    return bibliography_md(
        {"course_name": "Eng Soft"}, entries=entries, subject_profile=None,
        parse_bibliography_from_teaching_plan_fn=lambda t: {},
        clamp_navigation_artifact=lambda s, **k: s,
    )


def test_renders_summary_when_present():
    md = _bib([_entry(ref_summary="Framework de autenticacao.", computed_ref_unit="unidade-01-seguranca",
                      computed_ref_topics=["autenticacao"])])
    assert "Framework de autenticacao." in md
    assert "unidade-01-seguranca" in md


def test_no_summary_line_when_absent():
    md = _bib([_entry()])
    assert "**Resumo:**" not in md
    assert "https://github.com/a/b" in md  # ainda surfacea URL


def test_relevance_map_lists_mapped_reference():
    md = _bib([_entry(title="Spring Sec", computed_ref_unit="unidade-01-seguranca",
                      computed_ref_topics=["autenticacao"])])
    assert "[a preencher]" not in md
    assert "Spring Sec" in md
