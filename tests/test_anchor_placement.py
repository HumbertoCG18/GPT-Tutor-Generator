"""TDD tests for src/builder/routing/anchor_placement.py.

5 required paths per the brief:
1. manual_timeline_block_id set -> method="manual" (human truth wins, never overwritten).
2. Valid week-section (dates in timeline, topic matches) -> method="anchor".
3. Admin section (TDE/Trabalho) -> anchor fails -> method="scorer".
4. Week-section with topic mismatch -> anchor fails -> method="scorer".
5. No source_section -> method="scorer".

Determinism: injected resolvers/mint; no raw uuid4 asserted.
"""
from __future__ import annotations

import pytest

from src.builder.routing.anchor_placement import resolve_placement, AnchorResult


# ---------------------------------------------------------------------------
# Synthetic fixtures (no I/O)
# ---------------------------------------------------------------------------

UUID_MANUAL = "aaaa0000-0000-0000-0000-000000000001"
UUID_ANCHOR = "bbbb0000-0000-0000-0000-000000000002"
UUID_SCORER = "cccc0000-0000-0000-0000-000000000003"

# Minimal block fixture — period covers "Semana 4 - 23.03 a 27.03"
BLOCK_SUPERVISIONADO = {
    "id": "bloco-05",
    "block_uuid": UUID_ANCHOR,
    "period_start": "2026-03-18",
    "period_end": "2026-04-15",
    "topic_text": "abordagem supervisionada rede neural",
    "sessions": [
        {"date": "2026-03-23", "label": "ml abordagem supervisionada k nn aula"},
        {"date": "2026-03-25", "label": "ml abordagem supervisionada rede neural aula"},
    ],
    "kind": "class",
}

BLOCK_MANUAL_TARGET = {
    "id": "bloco-01",
    "block_uuid": UUID_MANUAL,
    "period_start": "2026-03-02",
    "period_end": "2026-03-02",
    "topic_text": "plano ensino",
    "sessions": [{"date": "2026-03-02", "label": "plano de ensino aula"}],
    "kind": "class",
}

BLOCK_SCORER_FALLBACK = {
    "id": "bloco-99",
    "block_uuid": UUID_SCORER,
    "period_start": "2026-07-01",
    "period_end": "2026-07-15",
    "topic_text": "fallback",
    "sessions": [],
    "kind": "class",
}

ALL_BLOCKS = [BLOCK_MANUAL_TARGET, BLOCK_SUPERVISIONADO, BLOCK_SCORER_FALLBACK]

YEAR = 2026


def _scorer_resolver(entry: dict, blocks: list) -> str:
    """Stub scorer: always returns UUID_SCORER."""
    return UUID_SCORER


# ---------------------------------------------------------------------------
# Test 1 — manual_timeline_block_id wins always
# ---------------------------------------------------------------------------

def test_manual_wins():
    entry = {
        "id": "entry-manual",
        "manual_timeline_block_id": UUID_MANUAL,
        "source_section": "Semana 4 - 23.03 a 27.03 - Machine Learning Aprendizado Supervisionado",
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.block_uuid == UUID_MANUAL
    assert result.method == "manual"


# ---------------------------------------------------------------------------
# Test 2 — valid semana anchor (dates + topic match)
# ---------------------------------------------------------------------------

def test_anchor_valid_week():
    entry = {
        "id": "entry-anchor",
        "manual_timeline_block_id": "",
        "source_section": "Semana 4 - 23.03 a 27.03 - Machine Learning Aprendizado Supervisionado",
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.block_uuid == UUID_ANCHOR
    assert result.method == "anchor"
    # anchor metadata must be present
    assert result.section is not None
    assert result.window_start is not None
    assert result.window_end is not None


# ---------------------------------------------------------------------------
# Test 3 — admin section (TDE) -> anchor fails -> scorer
# ---------------------------------------------------------------------------

def test_admin_section_falls_through():
    entry = {
        "id": "entry-tde",
        "manual_timeline_block_id": "",
        "source_section": "TDE Trabalho Discente Efetivo",
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.block_uuid == UUID_SCORER
    assert result.method == "scorer"


# ---------------------------------------------------------------------------
# Test 4 — topic mismatch -> anchor fails -> scorer
# ---------------------------------------------------------------------------

def test_topic_mismatch_falls_through():
    # Section says "Algoritmos de Busca" but BLOCK_SUPERVISIONADO is about ML.
    # The only block whose period covers 2026-05-25..2026-05-29 is NONE in our
    # fixture, so this will fall through anyway. But we also test: even if period
    # overlaps, topic must match the block/session topic.
    # We use a section whose dates DO overlap bloco-05 (Mar) but topic is "Busca".
    entry = {
        "id": "entry-mismatch",
        "manual_timeline_block_id": "",
        "source_section": "Semana 4 - 23.03 a 27.03 - Algoritmos de Busca",
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.block_uuid == UUID_SCORER
    assert result.method == "scorer"


# ---------------------------------------------------------------------------
# Test 5 — no source_section -> scorer
# ---------------------------------------------------------------------------

def test_no_source_section_falls_through():
    entry = {
        "id": "entry-no-section",
        "manual_timeline_block_id": "",
        "source_section": None,
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.block_uuid == UUID_SCORER
    assert result.method == "scorer"


# ---------------------------------------------------------------------------
# Test 6 — generic-stem only overlap -> anchor fails -> scorer
# (regressão do canário IA: "Introdução a IA e ML" vs block topic "introducao")
# ---------------------------------------------------------------------------

# Block whose topic_text is only the generic word "introducao" — no distinctive stems.
BLOCK_INTRODUCAO = {
    "id": "bloco-intro",
    "block_uuid": "dddd0000-0000-0000-0000-000000000004",
    "topic_text": "introducao",
    "sessions": [
        {"date": "2026-03-23", "label": "introducao aula"},
    ],
    "kind": "class",
}

ALL_BLOCKS_WITH_INTRO = [BLOCK_MANUAL_TARGET, BLOCK_INTRODUCAO, BLOCK_SCORER_FALLBACK]


def test_generic_stem_only_falls_to_scorer():
    """Overlap only on 'introduc' (generic) must NOT anchor — falls to scorer."""
    entry = {
        "id": "entry-intro-ia",
        "manual_timeline_block_id": "",
        # Section shares ONLY the generic stem "introduc" with the intro block above.
        "source_section": "Semana 4 - 23.03 a 27.03 - Introducao a IA e Introducao a ML",
        "computed_block_id": UUID_SCORER,
    }
    result: AnchorResult = resolve_placement(
        entry,
        ALL_BLOCKS_WITH_INTRO,
        scorer_resolver=_scorer_resolver,
        year=YEAR,
    )
    assert result.method == "scorer", (
        f"Expected scorer (generic-only overlap), got method={result.method!r}"
    )
