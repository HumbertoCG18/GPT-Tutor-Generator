from src.builder.artifacts.repo import bibliography_md


class _Entry:
    def __init__(self, **kw):
        d = dict(title="GitHub - a/b", source_path="https://github.com/a/b", tags="",
                 notes="", include_in_bundle=True, category="bibliografia")
        d.update(kw)
        self.__dict__.update(d)

    def id(self):
        return self.__dict__.get("_id", "ref-ab")


def _bib(entries, reference_curation=None):
    return bibliography_md(
        {"course_name": "Eng Soft"}, entries=entries, subject_profile=None,
        reference_curation=reference_curation,
        parse_bibliography_from_teaching_plan_fn=lambda t: {},
        clamp_navigation_artifact=lambda s, **k: s,
    )


def _curation(entry_id="ref-ab", **rec):
    base = dict(ref_summary="", computed_ref_unit="", computed_ref_topics=[])
    base.update(rec)
    return {"entries": {entry_id: base}}


def test_renders_summary_when_present():
    md = _bib([_Entry()], _curation(ref_summary="Framework de autenticacao.",
                                    computed_ref_unit="unidade-01-seguranca",
                                    computed_ref_topics=["autenticacao"]))
    assert "Framework de autenticacao." in md
    assert "unidade-01-seguranca" in md


def test_no_summary_line_when_absent():
    md = _bib([_Entry()], _curation())
    assert "**Resumo:**" not in md
    assert "https://github.com/a/b" in md


def test_relevance_map_lists_mapped_reference():
    md = _bib([_Entry(title="Spring Sec")], _curation(computed_ref_unit="unidade-01-seguranca",
                                                      computed_ref_topics=["autenticacao"]))
    assert "[a preencher]" not in md
    assert "Spring Sec" in md


def test_no_curation_renders_url_only():
    md = _bib([_Entry()], None)
    assert "**Resumo:**" not in md
    # A tabela "[a preencher]" foi removida (Approach C); agora há ponteiro p/ COURSE_MAP.
    assert "course/COURSE_MAP.md" in md
    assert "https://github.com/a/b" in md
