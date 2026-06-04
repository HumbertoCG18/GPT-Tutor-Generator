"""Índice de referências por âncora (unidade / unidade+tópico) p/ o COURSE_MAP.

Junta references_curation.json (computed_ref_unit/topics, ref_concepts) com os
entries do manifest (title, source_path, file_type). Determinístico, sem I/O.
"""
from src.builder.core import reference_navigation as rn


def _manifest(entries):
    return entries


def _curation(by_id):
    return {"entries": by_id}


def test_ref_with_topic_goes_to_by_topic():
    entries = [{"id": "e1", "title": "Flask", "source_path": "https://github.com/pallets/flask", "file_type": "github-repo"}]
    cur = _curation({"e1": {"computed_ref_unit": "web", "computed_ref_topics": ["Rotas HTTP"], "ref_concepts": ["Flask", "WSGI"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    key = ("web", rn._norm_topic("Rotas HTTP"))
    assert key in idx["by_topic"]
    assert idx["by_topic"][key][0]["entry_id"] == "e1"
    assert idx["by_topic"][key][0]["type"] == "repo"


def test_ref_unit_only_goes_to_by_unit_not_by_topic():
    entries = [{"id": "e2", "title": "Doc", "source_path": "https://docs.python.org/3/library/json.html", "file_type": "link"}]
    cur = _curation({"e2": {"computed_ref_unit": "serializacao", "computed_ref_topics": [], "ref_concepts": ["JSON"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"]["serializacao"][0]["entry_id"] == "e2"
    assert idx["by_unit"]["serializacao"][0]["type"] == "doc"
    assert idx["by_topic"] == {}


def test_ref_without_unit_is_excluded():
    entries = [{"id": "e3", "title": "X", "source_path": "https://x.com", "file_type": "link"}]
    cur = _curation({"e3": {"computed_ref_unit": "", "computed_ref_topics": [], "ref_concepts": ["a"]}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"] == {}
    assert idx["by_topic"] == {}


def test_curation_without_matching_manifest_is_excluded():
    entries = []  # manifest vazio
    cur = _curation({"ghost": {"computed_ref_unit": "web", "computed_ref_topics": [], "ref_concepts": []}})
    idx = rn.build_unit_topic_reference_index(entries, cur)
    assert idx["by_unit"] == {}


def test_type_repo_vs_doc():
    entries = [
        {"id": "r", "title": "R", "source_path": "https://github.com/o/r", "file_type": "github-repo"},
        {"id": "d", "title": "D", "source_path": "https://example.com/p", "file_type": "link"},
    ]
    cur = _curation({
        "r": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": []},
        "d": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": []},
    })
    idx = rn.build_unit_topic_reference_index(entries, cur)
    types = {r["entry_id"]: r["type"] for r in idx["by_unit"]["u"]}
    assert types == {"r": "repo", "d": "doc"}


def test_concepts_capped_to_three_and_stable_order():
    entries = [
        {"id": "b", "title": "B", "source_path": "https://x/b", "file_type": "link"},
        {"id": "a", "title": "A", "source_path": "https://x/a", "file_type": "link"},
    ]
    cur = _curation({
        "b": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": ["c1", "c2", "c3", "c4"]},
        "a": {"computed_ref_unit": "u", "computed_ref_topics": [], "ref_concepts": ["x"]},
    })
    idx = rn.build_unit_topic_reference_index(entries, cur)
    refs = idx["by_unit"]["u"]
    assert [r["entry_id"] for r in refs] == ["a", "b"]  # ordenado por entry_id
    assert refs[1]["concepts"] == ["c1", "c2", "c3"]  # cortado a 3


def test_support_line_format():
    ref = {"entry_id": "e1", "title": "Flask", "source_path": "u", "type": "repo",
           "concepts": ["Flask", "WSGI", "rotas"], "topics": [], "unit_slug": "web"}
    line = rn._ref_support_line(ref)
    assert line == "📖 Apoio: Flask (repo) — Flask, WSGI, rotas → content/BIBLIOGRAPHY.md"
