"""Testes das linhas de apoio (📖 Apoio) emitidas no COURSE_MAP a partir do
índice course_meta["_reference_nav_index"]. RED→GREEN da Task 2."""
from __future__ import annotations

from src.builder.engine import course_map_md
from src.builder.extraction.teaching_plan import _normalize_unit_slug
from src.builder.core.reference_navigation import _norm_topic
from src.models.core import SubjectProfile


# Plano no formato markdown reconhecido por parse_units_from_teaching_plan:
# heading "### Unidade N - Título" + bullets "- Tópico".
TEACHING_PLAN = """
### Unidade 1 - Desenvolvimento Web
- Rotas HTTP
- Templates
"""

UNIT_SLUG = _normalize_unit_slug("Unidade 1 - Desenvolvimento Web")


def _make_profile():
    return SubjectProfile(
        name="Desenvolvimento Web",
        slug="desenvolvimento-web",
        syllabus="",
        teaching_plan=TEACHING_PLAN,
    )


def _ref(entry_id, title, type_, concepts, topics):
    return {
        "entry_id": entry_id,
        "title": title,
        "source_path": "",
        "type": type_,
        "concepts": list(concepts),
        "topics": list(topics),
        "unit_slug": UNIT_SLUG,
    }


def _render(by_unit=None, by_topic=None, with_index=True):
    course_meta = {"course_name": "Desenvolvimento Web"}
    if with_index:
        course_meta["_reference_nav_index"] = {
            "by_unit": by_unit or {},
            "by_topic": by_topic or {},
        }
    return course_map_md(course_meta, _make_profile())


def test_support_line_appears_under_topic():
    ref = _ref("e1", "Flask", "repo", ["roteamento"], ["Rotas HTTP"])
    tkey = (UNIT_SLUG, _norm_topic("Rotas HTTP"))
    out = _render(by_unit={UNIT_SLUG: [ref]}, by_topic={tkey: [ref]})

    assert "📖 Apoio: Flask (repo)" in out

    lines = out.splitlines()
    # A linha de apoio deve aparecer logo após o bullet "Rotas HTTP".
    topic_idx = next(i for i, ln in enumerate(lines) if "Rotas HTTP" in ln and "[ ]" in ln)
    assert "📖 Apoio: Flask (repo)" in lines[topic_idx + 1]


def test_unit_only_ref_appears_under_unit_header():
    ref = _ref("e1", "Geral", "doc", [], [])
    out = _render(by_unit={UNIT_SLUG: [ref]}, by_topic={})
    assert "📖 Apoio: Geral (doc)" in out


def test_degraded_mode_no_index_is_unchanged():
    empty = _render(by_unit={}, by_topic={}, with_index=True)
    base = _render(with_index=False)
    assert "📖 Apoio" not in base
    # Índice vazio deve produzir saída byte-idêntica ao modo sem índice.
    assert base == empty


def test_cap_two_lines_plus_overflow():
    refs = [
        _ref("e1", "Ref A", "repo", [], ["Rotas HTTP"]),
        _ref("e2", "Ref B", "repo", [], ["Rotas HTTP"]),
        _ref("e3", "Ref C", "repo", [], ["Rotas HTTP"]),
    ]
    tkey = (UNIT_SLUG, _norm_topic("Rotas HTTP"))
    out = _render(by_unit={UNIT_SLUG: refs}, by_topic={tkey: refs})

    assert out.count("📖 Apoio:") == 2
    assert "(+1 referência(s) em content/BIBLIOGRAPHY.md)" in out
