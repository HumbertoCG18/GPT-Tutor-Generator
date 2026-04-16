from pathlib import Path

import pytest

from src.builder.student_state import (
    UnitNotReadyError,
    consolidate_unit,
    render_unit_summary_md,
)


def _seed_repo(root: Path) -> None:
    (root / "student" / "batteries" / "unidade-02").mkdir(parents=True)
    (root / "student" / "batteries" / "unidade-02" / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## 2026-04-05 (sessão 1)\n- Resolveu: def formal\n",
        encoding="utf-8",
    )
    (root / "student" / "batteries" / "unidade-02" / "continuidade.md").write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## 2026-04-10 (sessão 1)\n- Resolveu: teorema\n",
        encoding="utf-8",
    )
    (root / "student" / "STUDENT_STATE.md").write_text(
        "---\ncourse: X\nstudent: Y\nupdated: 2026-04-20\n"
        "active:\n  unit: unidade-02\n  topic: continuidade\n"
        "  status: compreendido\n  sessions: 1\n"
        "  file: batteries/unidade-02/continuidade.md\n\n"
        "active_unit_progress:\n"
        "  - {topic: limites, status: compreendido}\n"
        "  - {topic: continuidade, status: compreendido}\n\n"
        "---\n",
        encoding="utf-8",
    )


def test_render_unit_summary_aggregates_bullets(tmp_path: Path):
    batteries = [
        (
            "limites.md",
            "---\ntopic: Limites\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
            "## 2026-04-05 (sessão 1)\n- Compreendeu: def formal\n- Dúvidas: ε-δ\n- Ação tutor: exemplo gráfico\n\n"
            "## 2026-04-08 (sessão 2)\n- Resolveu: ε-δ\n- Dúvidas: [nenhuma]\n",
        ),
        (
            "continuidade.md",
            "---\ntopic: Continuidade\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
            "## 2026-04-10 (sessão 1)\n- Compreendeu: teorema intermediário\n- Dúvidas: [nenhuma]\n",
        ),
    ]

    summary = render_unit_summary_md(
        unit_slug="unidade-02",
        closed_date="2026-04-20",
        topic_order=["limites", "continuidade"],
        batteries=batteries,
    )
    assert "unit: unidade-02" in summary
    assert "status: consolidado" in summary
    assert "sessions_total: 3" in summary
    assert "topics: [limites, continuidade]" in summary
    assert "**Tópicos cobertos:**" in summary
    assert "limites" in summary and "continuidade" in summary
    assert "**Dúvidas resolvidas:**" in summary
    assert "ε-δ" in summary


def test_consolidate_unit_happy_path(tmp_path: Path):
    _seed_repo(tmp_path)
    result = consolidate_unit(
        root_dir=tmp_path,
        unit_slug="unidade-02",
        today="2026-04-20",
        topic_order=["limites", "continuidade"],
    )
    assert result.summary_path == tmp_path / "student" / "batteries" / "unidade-02.summary.md"
    assert result.summary_path.exists()
    assert not (tmp_path / "student" / "batteries" / "unidade-02").exists()
    state = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "closed_units: [unidade-02]" in state
