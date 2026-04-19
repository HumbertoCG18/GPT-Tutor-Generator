from pathlib import Path
from datetime import datetime

from src.builder.artifacts.student_state import (
    ActiveTopic,
    ProgressRow,
    consolidate_unit,
    detect_state_version,
    refresh_active_unit_progress,
    render_student_state_md,
)


def test_end_to_end_build_refresh_consolidate(tmp_path: Path):
    today = datetime.now().strftime("%Y-%m-%d")
    (tmp_path / "student").mkdir()
    state = render_student_state_md(
        course_name="Cálculo",
        student_nickname="Humberto",
        today=today,
        active=ActiveTopic(
            unit="unidade-02",
            topic="limites",
            status="em_progresso",
            sessions=0,
            file="batteries/unidade-02/limites.md",
        ),
        active_unit_progress=[
            ProgressRow("limites", "pendente"),
            ProgressRow("continuidade", "pendente"),
        ],
        recent=[],
        closed_units=[],
        next_topic="continuidade",
    )
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(state, encoding="utf-8")
    batteries = tmp_path / "student" / "batteries" / "unidade-02"
    batteries.mkdir(parents=True)
    (batteries / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## X (sessão 1)\n- Resolveu: tudo\n",
        encoding="utf-8",
    )
    (batteries / "continuidade.md").write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## Y (sessão 1)\n- Resolveu: tudo\n",
        encoding="utf-8",
    )

    refresh_active_unit_progress(
        root_dir=tmp_path,
        active_unit_slug="unidade-02",
        course_map_topics=[("limites", "L"), ("continuidade", "C")],
    )
    assert detect_state_version(tmp_path) == "v2"
    text = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "status: compreendido" in text

    result = consolidate_unit(
        root_dir=tmp_path,
        unit_slug="unidade-02",
        today=today,
        topic_order=["limites", "continuidade"],
    )
    assert result.summary_path.exists()
    assert not batteries.exists()
    final = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "closed_units: [unidade-02]" in final
