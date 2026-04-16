from pathlib import Path

from src.builder.student_state import render_unit_summary_md


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
