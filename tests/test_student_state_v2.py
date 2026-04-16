from pathlib import Path

from src.builder.student_state import (
    derive_active_unit_progress,
    parse_battery_frontmatter,
    refresh_active_unit_progress,
    render_student_state_md,
)


def test_yaml_frontmatter_is_minimal_and_well_formed():
    md = render_student_state_md(
        course_name="Cálculo III",
        student_nickname="Humberto",
        today="2026-04-16",
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )
    assert md.startswith("---\n")
    assert "course: Cálculo III" in md
    assert "student: Humberto" in md
    assert "updated: 2026-04-16" in md
    assert md.rstrip().endswith("---")
    assert "## " not in md  # sem headers markdown — YAML puro
    assert len(md.splitlines()) < 40  # teto de tamanho


def test_yaml_has_no_legacy_history_table():
    md = render_student_state_md(
        course_name="X", student_nickname="Y", today="2026-04-16",
        active=None, active_unit_progress=[], recent=[],
        closed_units=[], next_topic="",
    )
    assert "Histórico de sessões" not in md
    assert "Progresso por unidade" not in md


def test_parse_battery_frontmatter_extracts_status():
    content = (
        "---\n"
        "topic: Derivadas parciais\n"
        "topic_slug: derivadas-parciais\n"
        "unit: unidade-02\n"
        "status: em_progresso\n"
        "---\n\n## 2026-04-14 (sessão 1)\n- foo\n"
    )
    fm = parse_battery_frontmatter(content)
    assert fm["topic_slug"] == "derivadas-parciais"
    assert fm["unit"] == "unidade-02"
    assert fm["status"] == "em_progresso"


def test_parse_battery_frontmatter_missing_returns_empty():
    assert parse_battery_frontmatter("sem frontmatter") == {}


def test_derive_active_unit_progress_merges_course_map_with_batteries(tmp_path: Path):
    batteries_dir = tmp_path / "batteries" / "unidade-02"
    batteries_dir.mkdir(parents=True)
    (batteries_dir / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n",
        encoding="utf-8",
    )
    (batteries_dir / "derivadas-parciais.md").write_text(
        "---\ntopic_slug: derivadas-parciais\nunit: unidade-02\nstatus: em_progresso\n---\n",
        encoding="utf-8",
    )

    course_map_topics = [
        ("limites", "Limites"),
        ("continuidade", "Continuidade"),
        ("derivadas-parciais", "Derivadas parciais"),
        ("regra-da-cadeia", "Regra da cadeia"),
    ]

    rows = derive_active_unit_progress(
        unit_slug="unidade-02",
        course_map_topics=course_map_topics,
        batteries_root=tmp_path / "batteries",
    )
    statuses = {r.topic: r.status for r in rows}
    assert statuses == {
        "limites": "compreendido",
        "continuidade": "pendente",
        "derivadas-parciais": "em_progresso",
        "regra-da-cadeia": "pendente",
    }
    assert [r.topic for r in rows] == [slug for slug, _ in course_map_topics]


def test_refresh_rewrites_only_progress_block(tmp_path: Path):
    root = tmp_path
    (root / "student").mkdir()
    state = (
        "---\n"
        "course: X\n"
        "student: Y\n"
        "updated: 2026-04-10\n"
        "\n"
        "active:\n"
        "  unit: unidade-02\n"
        "  topic: limites\n"
        "  status: compreendido\n"
        "  sessions: 1\n"
        "  file: batteries/unidade-02/limites.md\n"
        "\n"
        "active_unit_progress:\n"
        "  - {topic: limites, status: pendente}\n"
        "\n"
        "---\n"
    )
    (root / "student" / "STUDENT_STATE.md").write_text(state, encoding="utf-8")
    (root / "student" / "batteries" / "unidade-02").mkdir(parents=True)
    (root / "student" / "batteries" / "unidade-02" / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n",
        encoding="utf-8",
    )

    refresh_active_unit_progress(
        root_dir=root,
        active_unit_slug="unidade-02",
        course_map_topics=[("limites", "L"), ("continuidade", "C")],
    )

    new_state = (root / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "- {topic: limites, status: compreendido}" in new_state
    assert "- {topic: continuidade, status: pendente}" in new_state
    assert "topic: limites" in new_state
    assert "file: batteries/unidade-02/limites.md" in new_state
