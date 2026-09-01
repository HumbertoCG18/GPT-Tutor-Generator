"""Tests para BlockKind classifier + status derivation."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

import pytest

from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import (
    KIND_DISPLAY,
    KIND_REQUIREMENTS,
    NON_ACADEMIC_KINDS,
    BlockKind,
    requires,
)
from src.builder.timeline.status import derive_block_status


# ---------------------------------------------------------------------------
# kinds.py — invariants
# ---------------------------------------------------------------------------

def test_enum_has_15_values():
    assert len(list(BlockKind)) == 15


def test_requirements_covers_every_kind():
    assert set(KIND_REQUIREMENTS) == set(BlockKind)


def test_display_covers_every_kind():
    assert set(KIND_DISPLAY) == set(BlockKind)
    for kind, meta in KIND_DISPLAY.items():
        assert {"icon", "label", "color"} <= meta.keys()


def test_non_academic_kinds_have_no_requirements():
    for kind in NON_ACADEMIC_KINDS:
        for field in ("unit", "topic", "files"):
            assert requires(kind, field) is False


# ---------------------------------------------------------------------------
# classifier — fixed cases (curated from audit corpus)
# ---------------------------------------------------------------------------

CLASSIFIER_CASES = [
    ({"topic_text": "Feriado de Carnaval"}, BlockKind.HOLIDAY),
    ({"topic_text": "Natal"}, BlockKind.HOLIDAY),
    ({"topic_text": "Corpus Christi"}, BlockKind.HOLIDAY),
    ({"topic_text": "P1 - Prova", "unit_slug": "u1"}, BlockKind.ASSESSMENT),
    ({"topic_text": "PF Avaliação final"}, BlockKind.ASSESSMENT),
    ({"topic_text": "Prova substitutiva"}, BlockKind.ASSESSMENT),
    ({"topic_text": "Recuperação"}, BlockKind.ASSESSMENT),
    ({"topic_text": "Revisão para P2"}, BlockKind.ASSESSMENT),
    ({"topic_text": "Revisão geral"}, BlockKind.REVIEW),
    ({"topic_text": "Apresentação do plano de ensino e avaliação"}, BlockKind.OVERVIEW),
    ({"topic_text": "Ementa da disciplina"}, BlockKind.OVERVIEW),
    ({"topic_text": "Introdução"}, BlockKind.OVERVIEW),
    ({"topic_text": "Disciplina introdução"}, BlockKind.OVERVIEW),
    ({"topic_text": "Introdução à lógica de predicados", "unit_slug": "u1"}, BlockKind.CLASS),
    # P3.4 unit-aware: "trabalho" nu SEM evidencia de unidade = apresentacao/
    # entrega de trabalho -> DELIVERABLE (atravessa unidades). COM unit_slug ou
    # topic_candidates, "trabalho" e tema de aula -> CLASS (mantem unidade).
    ({"topic_text": "Trabalho gerais"}, BlockKind.DELIVERABLE),
    ({"topic_text": "Parte trabalho"}, BlockKind.DELIVERABLE),
    ({"topic_text": "Trabalho sobre escalonamento", "unit_slug": "u1"}, BlockKind.CLASS),
    ({"topic_text": "Trabalho de grafos",
      "topic_candidates": [{"unit_slug": "u1", "score": 0.3}]}, BlockKind.CLASS),
    ({"period_label": "5 dias · 11/03/2026 a 25/03/2026"}, BlockKind.RESERVED),
    ({"topic_text": "Lógica de predicados", "unit_slug": "u1"}, BlockKind.CLASS),
    ({"topic_text": "Atendimento aos alunos"}, BlockKind.OFFICE_HOURS),
    ({"topic_text": "Plantão de dúvidas"}, BlockKind.OFFICE_HOURS),
    ({"topic_text": "Greve"}, BlockKind.SUSPENDED),
    ({"topic_text": "Paralisação"}, BlockKind.SUSPENDED),
    ({"topic_text": "Oficina de Dafny"}, BlockKind.WORKSHOP),
    ({"topic_text": "Kickoff do projeto"}, BlockKind.WORKSHOP),
    ({"topic_text": "Reposição da aula"}, BlockKind.MAKEUP),
    ({"topic_text": "Substituição de aula"}, BlockKind.MAKEUP),
    ({"topic_text": "Divulgação de resultados"}, BlockKind.RESULTS),
    ({"topic_text": "Devolução das provas"}, BlockKind.RESULTS),
    ({"topic_text": "Semana acadêmica"}, BlockKind.ACADEMIC_EVENT),
    ({"topic_text": "Simpósio"}, BlockKind.ACADEMIC_EVENT),
    ({"topic_text": "Planejamento do semestre"}, BlockKind.PLANNING),
    ({"topic_text": "Reunião de conselho"}, BlockKind.PLANNING),
    ({"topic_text": "Reserva técnica"}, BlockKind.RESERVED),
    ({"topic_text": "Entrega trabalho final"}, BlockKind.DELIVERABLE),
    ({"topic_text": "", "unit_slug": ""}, BlockKind.UNKNOWN),
    ({"topic_text": "", "unit_slug": "u1"}, BlockKind.CLASS),
    ({"topic_text": "tema livre", "unit_slug": "u1"}, BlockKind.CLASS),
    # Sinal de prova/revisão só no label da sessão (topic reduzido a stopword).
    # Caso real TCC bloco-24: 01/07 revisão P2 + 03/07 P2 fundidos, topic="para".
    ({"topic_text": "para",
      "sessions": [{"label": "prova p2 prova"}]}, BlockKind.ASSESSMENT),
    ({"topic_text": "para",
      "sessions": [{"label": "revisao para prova p2 aula"},
                   {"label": "prova p2 prova"}]}, BlockKind.ASSESSMENT),
    ({"topic_text": "",
      "sessions": [{"label": "revisao geral"}]}, BlockKind.REVIEW),
    # Caso real Metodos-Formais bloco-07: 15/04 "exercicios de revisao",
    # topic_text vazio MAS unidade foi propagada por inferencia de vizinhos.
    # A sessao de revisao deve vencer a unidade propagada -> REVIEW (nao CLASS).
    ({"topic_text": "", "unit_slug": "unidade-02",
      "sessions": [{"label": "exercicios de revisao aula"}]}, BlockKind.REVIEW),
    # Prova com unidade propagada e topic vazio: sessao P1 vence -> ASSESSMENT.
    ({"topic_text": "", "unit_slug": "unidade-01",
      "sessions": [{"label": "prova p1 prova"}]}, BlockKind.ASSESSMENT),
]


@pytest.mark.parametrize("block, expected", CLASSIFIER_CASES)
def test_classify_block(block, expected):
    assert classify_block(block) == expected


def test_manual_override_wins():
    block = {"topic_text": "Aula normal", "unit_slug": "u1",
             "manual_kind_override": "holiday"}
    assert classify_block(block) == BlockKind.HOLIDAY


def test_invalid_override_falls_back():
    block = {"topic_text": "Feriado", "manual_kind_override": "invalid_xyz"}
    assert classify_block(block) == BlockKind.HOLIDAY


def test_source_kind_wins_over_text_and_unit():
    block = {"source_kind": "assessment", "topic_text": "Lógica",
             "unit_slug": "u1"}
    assert classify_block(block) == BlockKind.ASSESSMENT


def test_manual_override_wins_over_source_kind():
    block = {"source_kind": "assessment", "manual_kind_override": "holiday"}
    assert classify_block(block) == BlockKind.HOLIDAY


def test_invalid_source_kind_falls_back_to_text():
    block = {"source_kind": "garbage", "topic_text": "Feriado de Carnaval"}
    assert classify_block(block) == BlockKind.HOLIDAY


# ---------------------------------------------------------------------------
# status — fixed cases
# ---------------------------------------------------------------------------

STATUS_CASES = [
    ({"kind": "class", "unit_slug": "u1", "primary_topic_label": "t", "sessions": 3}, "ok"),
    ({"kind": "class", "unit_slug": "", "primary_topic_label": "t", "sessions": 3}, "needs_unit"),
    ({"kind": "class", "unit_slug": "u1", "primary_topic_label": "", "topic_text": "", "sessions": 3}, "needs_topic"),
    ({"kind": "class", "unit_slug": "u1", "primary_topic_label": "t", "sessions": 0}, "needs_files"),
    ({"kind": "holiday"}, "non_applicable"),
    ({"kind": "office_hours"}, "non_applicable"),
    ({"kind": "academic_event"}, "non_applicable"),
    ({"kind": "unknown"}, "needs_review"),
    ({"kind": "assessment", "primary_topic_label": "P1"}, "ok"),
    ({"kind": "assessment", "primary_topic_label": "", "topic_text": ""}, "needs_topic"),
    ({"kind": "review"}, "ok"),
    ({"kind": "deliverable", "unit_slug": "u1", "primary_topic_label": "t", "sessions": 1}, "ok"),
    ({"kind": "deliverable", "unit_slug": "u1", "primary_topic_label": "t", "sessions": 0}, "needs_files"),
]


@pytest.mark.parametrize("block, expected", STATUS_CASES)
def test_derive_block_status(block, expected):
    assert derive_block_status(block) == expected


def test_status_unknown_kind_string():
    assert derive_block_status({"kind": "garbage"}) == "needs_review"


# ---------------------------------------------------------------------------
# Regressao: roda nos cursos reais (skip se nao existirem)
# ---------------------------------------------------------------------------

_REAL_COURSES = [
    "Engenharia-Software-2-Tutor",
    "Inteligencia-Artifical-Tutor",
    "Metodos-Formais-Tutor",
    "Sistemas-Operacionais-Tutor",
    "TCC-Tutor",
]

_BASE = Path(os.environ.get("TUTOR_COURSES_DIR",
                            r"C:\Users\Humberto\Documents\GitHub"))


def _load_real_blocks(course: str):
    path = _BASE / course / "course" / ".timeline_index.json"
    if not path.exists():
        pytest.skip(f"course corpus not available: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("blocks", [])


@pytest.mark.parametrize("course", _REAL_COURSES)
def test_real_corpus_unknown_rate(course):
    """Cobertura: <=10% UNKNOWN por curso. Drift = curadoria pendente."""
    blocks = _load_real_blocks(course)
    if not blocks:
        pytest.skip("no blocks")
    kinds = Counter(classify_block(b).value for b in blocks)
    total = sum(kinds.values())
    unknown = kinds.get("unknown", 0)
    rate = unknown / total
    assert rate <= 0.10, f"{course}: {unknown}/{total} unknown ({rate:.0%}) > 10%. Kinds={dict(kinds)}"


# ---------------------------------------------------------------------------
# Topic fallback (Phase 4 fix). Os testes do voto de unidade
# (_vote_unit_from_topic_candidates) morreram com o fallback keyword no
# cutover passo 3 — cadeia topic-labels abaixo segue VIVA.
# ---------------------------------------------------------------------------

from src.builder.timeline.index import (  # noqa: E402
    _TOPIC_FALLBACK_MAX_LEN,
    _humanize_topic_text,
    _resolve_block_topic_label,
)

def test_humanize_strips_border_stopwords():
    assert _humanize_topic_text("de lógica de predicados") == "Lógica de predicados"


def test_humanize_keeps_internal_stopwords():
    assert _humanize_topic_text("teoria da computação") == "Teoria da computação"


def test_humanize_capitalizes_first_char():
    assert _humanize_topic_text("máquinas de turing")[0] == "M"


def test_humanize_preserves_acronym_case():
    assert _humanize_topic_text("API REST e DevOps") == "API REST e DevOps"


def test_humanize_empty_returns_empty():
    assert _humanize_topic_text("") == ""
    assert _humanize_topic_text("   ") == ""


def test_humanize_all_stopwords_keeps_original():
    # se sobrar nada apos stripping, restaura tokens originais
    assert _humanize_topic_text("de da do") == "De da do"


def test_humanize_truncates_at_60():
    out = _humanize_topic_text("a " + "x" * 80)
    assert out.endswith("…")
    assert len(out) <= _TOPIC_FALLBACK_MAX_LEN + 1


def test_resolve_topic_manual_wins():
    block = {"manual_topic_label": "Tópico Curado",
             "primary_topic_label": "outro", "topic_text": "qualquer"}
    label, slug, source = _resolve_block_topic_label(block)
    assert label == "Tópico Curado"
    assert source == "manual"
    assert slug


def test_resolve_topic_taxonomy_layer():
    block = {"primary_topic_label": "Lógica Proposicional",
             "primary_topic_slug": "logica-proposicional",
             "topic_text": "ignorado"}
    label, slug, source = _resolve_block_topic_label(block)
    assert label == "Lógica Proposicional"
    assert slug == "logica-proposicional"
    assert source == "taxonomy"


def test_resolve_topic_text_fallback():
    block = {"primary_topic_label": "", "topic_text": "de problema da parada"}
    label, slug, source = _resolve_block_topic_label(block)
    assert label == "Problema da parada"
    assert source == "topic_text_fallback"
    assert slug


def test_resolve_topic_empty_when_nothing():
    block = {"primary_topic_label": "", "topic_text": ""}
    label, slug, source = _resolve_block_topic_label(block)
    assert label == ""
    assert slug == ""
    assert source == ""


@pytest.mark.parametrize("course", _REAL_COURSES)
def test_real_corpus_every_block_classifies(course):
    """Nenhum bloco deve crashar o classifier."""
    blocks = _load_real_blocks(course)
    for blk in blocks:
        kind = classify_block(blk)
        assert isinstance(kind, BlockKind)
        blk_with_kind = dict(blk, kind=kind.value)
        status = derive_block_status(blk_with_kind)
        assert status in {"ok", "needs_unit", "needs_topic",
                          "needs_files", "non_applicable", "needs_review"}


# ---------------------------------------------------------------------------
# Block grouping splits by authoritative row kind (prova nao funde no vizinho)
# ---------------------------------------------------------------------------

from src.builder.timeline.index import _rows_belong_to_same_thematic_block  # noqa: E402


def _r(content, kind="class", date="01/01/2026"):
    return {"content": content, "kind": kind, "date_text": date}


def test_grouping_splits_when_current_row_is_assessment_kind():
    prev = _r("Feriado Aula", kind="class")
    cur = _r("Prova P1 Prova", kind="assessment")
    assert _rows_belong_to_same_thematic_block(prev, cur, [prev]) is False


def test_grouping_splits_when_previous_row_is_assessment_kind():
    prev = _r("Prova P1 Prova", kind="assessment")
    cur = _r("Arquitetura de software camadas", kind="class")
    assert _rows_belong_to_same_thematic_block(prev, cur, [prev]) is False


def test_grouping_keeps_two_class_rows_with_shared_tokens_together():
    # regressao: duas aulas do mesmo tema continuam no mesmo bloco
    prev = _r("Arquitetura de software em camadas", kind="class")
    cur = _r("Arquitetura de software microservicos", kind="class")
    assert _rows_belong_to_same_thematic_block(prev, cur, [prev]) is True
