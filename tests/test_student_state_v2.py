from src.builder.student_state import render_student_state_md


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
