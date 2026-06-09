"""BIBLIOGRAPHY sem a tabela de relevância redundante; com ponteiro p/ COURSE_MAP."""
from src.builder.artifacts import repo


class _Entry:
    def __init__(self, eid, title, source_path):
        self._id = eid
        self.title = title
        self.source_path = source_path
        self.tags = ""
        self.notes = ""
        self.professor_signal = ""
        self.include_in_bundle = True

    def id(self):
        return self._id


def _bib(entries, curation):
    return repo.bibliography_md(
        {"course_name": "Curso"},
        entries,
        None,
        reference_curation=curation,
        parse_bibliography_from_teaching_plan_fn=lambda _t: {},
        clamp_navigation_artifact=lambda text, **_k: text,
    )


def test_no_relevance_table_headers():
    entries = [_Entry("e1", "Flask", "https://github.com/pallets/flask")]
    cur = {"entries": {"e1": {"ref_summary": "resumo", "computed_ref_unit": "web",
                              "computed_ref_topics": ["Rotas HTTP"]}}}
    out = _bib(entries, cur)
    assert "Mapa de relevância por tópico" not in out
    assert "Acessível" not in out
    assert "Incidência em prova" not in out


def test_pointer_to_course_map_present():
    out = _bib([_Entry("e1", "Flask", "u")], {"entries": {}})
    assert "course/COURSE_MAP.md" in out
    assert "📖 Apoio" in out


def test_relevante_para_still_present_per_entry():
    entries = [_Entry("e1", "Flask", "u")]
    cur = {"entries": {"e1": {"ref_summary": "r", "computed_ref_unit": "web",
                             "computed_ref_topics": ["Rotas HTTP"]}}}
    out = _bib(entries, cur)
    assert "Relevante para" in out


def test_clamp_label_is_bibliography():
    captured = {}

    def _clamp(text, **kwargs):
        captured["label"] = kwargs.get("label")
        return text

    repo.bibliography_md(
        {"course_name": "Curso"}, [_Entry("e1", "F", "u")], None,
        reference_curation={"entries": {}},
        parse_bibliography_from_teaching_plan_fn=lambda _t: {},
        clamp_navigation_artifact=_clamp,
    )
    assert captured["label"] == "course/BIBLIOGRAPHY.md"
