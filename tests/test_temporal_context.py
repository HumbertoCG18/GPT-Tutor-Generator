"""Gerador do artefato setup/CONTEXTO_TEMPORAL.md."""

from src.builder.artifacts.temporal_context import build_temporal_context_rows


def _class_block():
    return {
        "id": "bloco-01",
        "period_start": "2026-03-03",
        "period_end": "2026-03-10",
        "kind": "class",
        "unit_slug": "unidade-01-limites",
        "topics": ["Definição de limite", "Limites laterais"],
        "primary_topic_label": "Definição de limite",
    }


def _assessment_block():
    return {
        "id": "bloco-09",
        "period_start": "2026-04-28",
        "period_end": "2026-04-28",
        "kind": "assessment",
        "sessions": [{"label": "prova p1 prova"}],
        "scope_unit_slugs": ["unidade-01-limites", "unidade-02-derivadas"],
    }


def test_class_row_uses_full_topics_list_and_short_unit():
    rows = build_temporal_context_rows([_class_block()])
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == "bloco-01"
    assert r["inicio"] == "2026-03-03"
    assert r["fim"] == "2026-03-10"
    assert r["tipo"] == "aula"
    assert r["unidade"] == "U1"
    assert r["unidade_slug"] == "unidade-01-limites"
    assert r["topico"] == "Definição de limite; Limites laterais"
    assert r["escopo"] == []


def test_class_row_falls_back_to_primary_topic_when_no_topics():
    blk = _class_block()
    blk["topics"] = []
    rows = build_temporal_context_rows([blk])
    assert rows[0]["topico"] == "Definição de limite"


def test_assessment_row_has_exam_code_and_short_scope():
    rows = build_temporal_context_rows([_assessment_block()])
    r = rows[0]
    assert r["tipo"] == "prova P1"
    assert r["escopo"] == ["U1", "U2"]
    assert r["escopo_slugs"] == ["unidade-01-limites", "unidade-02-derivadas"]


def test_review_and_holiday_tipo_labels():
    review = {"id": "b7", "period_start": "2026-04-21", "kind": "review",
              "scope_unit_slugs": ["unidade-01-limites"]}
    holiday = {"id": "b8", "period_start": "2026-04-22", "kind": "holiday"}
    rows = build_temporal_context_rows([review, holiday])
    assert rows[0]["tipo"] == "revisão"
    assert rows[0]["escopo"] == ["U1"]
    assert rows[1]["tipo"] == "feriado"


def test_block_without_start_date_is_omitted():
    blk = {"id": "x", "kind": "class", "topics": ["t"]}  # sem period_start
    assert build_temporal_context_rows([blk]) == []


def test_end_falls_back_to_start_when_missing():
    blk = {"id": "b", "period_start": "2026-03-03", "kind": "class"}
    assert build_temporal_context_rows([blk])[0]["fim"] == "2026-03-03"
