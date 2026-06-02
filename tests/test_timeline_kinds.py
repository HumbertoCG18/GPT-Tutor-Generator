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

def test_enum_has_14_values():
    assert len(list(BlockKind)) == 14


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
    ({"topic_text": "Apresentação do plano de ensino e avaliação"}, BlockKind.CLASS),
    ({"topic_text": "Ementa da disciplina"}, BlockKind.CLASS),
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
# Vote unit from topic_candidates (Phase 3 fix)
# ---------------------------------------------------------------------------

from src.builder.timeline.index import (  # noqa: E402
    _humanize_topic_text,
    _resolve_block_topic_label,
    _vote_unit_from_topic_candidates,
)


def _idx(*slugs):
    return [{"slug": s, "title": s} for s in slugs]


def test_vote_unit_unanimous_candidates_assigns_unit():
    block = {"topic_candidates": [
        {"unit_slug": "unidade-01-arquitetura", "score": 0.20},
        {"unit_slug": "unidade-01-arquitetura", "score": 0.20},
        {"unit_slug": "unidade-01-arquitetura", "score": 0.20},
    ]}
    slug, conf = _vote_unit_from_topic_candidates(
        block, _idx("unidade-01-arquitetura", "unidade-02-devops"))
    assert slug == "unidade-01-arquitetura"
    assert 0.30 <= conf <= 0.55


def test_vote_unit_divided_candidates_abstains():
    block = {"topic_candidates": [
        {"unit_slug": "unidade-01-arquitetura", "score": 0.30},
        {"unit_slug": "unidade-02-devops", "score": 0.28},
    ]}
    slug, conf = _vote_unit_from_topic_candidates(
        block, _idx("unidade-01-arquitetura", "unidade-02-devops"))
    assert slug == ""
    assert conf == 0.0


def test_vote_unit_no_candidates_abstains():
    slug, conf = _vote_unit_from_topic_candidates(
        {"topic_candidates": []}, _idx("u1", "u2"))
    assert slug == ""


def test_vote_unit_skips_unknown_slug():
    block = {"topic_candidates": [
        {"unit_slug": "ghost-unit", "score": 0.50},
        {"unit_slug": "ghost-unit", "score": 0.50},
    ]}
    slug, _ = _vote_unit_from_topic_candidates(block, _idx("real-unit"))
    assert slug == ""


def test_vote_unit_below_min_score_filtered():
    block = {"topic_candidates": [
        {"unit_slug": "u1", "score": 0.05},
        {"unit_slug": "u1", "score": 0.05},
    ]}
    slug, _ = _vote_unit_from_topic_candidates(block, _idx("u1"))
    assert slug == ""


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
