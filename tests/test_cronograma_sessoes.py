from src.builder.artifacts import repo


def _blocks_with_sessions():
    return [
        {
            "id": "bloco-04",
            "period_label": "Semana 11/03",
            "primary_topic_label": "Especificações Indutivas",
            "topics": ["conjuntos indutivos"],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s1", "date": "2026-03-11", "kind": "class",
                 "label": "conjuntos indutivos e equacoes recursivas", "signals": []},
                {"id": "s2", "date": "2026-03-18", "kind": "class",
                 "label": "estudo de caso listas", "signals": []},
            ],
        },
        {
            "id": "bloco-09",
            "period_label": "Semana 22/04",
            "primary_topic_label": "",
            "topics": [],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s3", "date": "2026-04-22", "kind": "assessment",
                 "label": "prova p1", "signals": []},
            ],
        },
    ]


def test_render_lists_sessions_by_date_with_weekday():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "### Sessões" in md
    assert "qua 11/03" in md          # 2026-03-11 é quarta
    assert "estudo de caso listas" in md
    assert "qua 18/03" in md


def test_render_marks_assessment_session():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "⏱" in md
    assert "prova p1" in md


def test_render_block_without_sessions_omits_section():
    blocks = [{"id": "b1", "period_label": "Aula 1", "topics": [], "sessions": []}]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "### Sessões" not in md


def test_render_session_with_empty_date_does_not_crash():
    blocks = [{
        "id": "b1", "period_label": "Aula 1", "topics": [],
        "sessions": [{"id": "s", "date": "", "kind": "async", "label": "atividade ead", "signals": []}],
    }]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "atividade ead" in md
    assert "(sem data)" in md
