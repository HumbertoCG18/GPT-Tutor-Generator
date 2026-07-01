"""TDD — Stage B: wire anchor_placement via campo aditivo temporal_block_id.

Invariantes do gate:
- computed_block_id NUNCA é tocado pelo anchor pass (KB byte-idêntico).
- temporal_block_id escrito só para method ∈ {anchor, manual}; ausente p/ scorer.
- helper resolve_temporal_block: temporal vence; fallback = resolve_effective_block
  (honra manual → flag-OFF byte-idêntico).
- gate enabled=False → resolve_placement nunca chamado (isolamento dos outros repos).
"""
from __future__ import annotations

import copy
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures sintéticas — espelham o caso real IA (Semana 9 agrupamento)
# ---------------------------------------------------------------------------

UUID_06 = "0606aaaa-0000-0000-0000-000000000006"
UUID_07 = "0707bbbb-0000-0000-0000-000000000007"
UUID_01 = "0101cccc-0000-0000-0000-000000000001"

# bloco-06 = agrupamento (k-means 20/04 + hierárquico 27/04) — abrange S8 e início S9
BLOCK_06 = {
    "id": "bloco-06",
    "block_uuid": UUID_06,
    "topic_text": "abordagem nao supervisionada agrupamento k means hierarquico",
    "sessions": [
        {"date": "2026-04-20", "label": "ml abordagem nao supervisionada k means exercicios aula"},
        {"date": "2026-04-27", "label": "ml abordagem nao supervisionada hierarquico exercicios aula"},
    ],
    "kind": "class",
}

# bloco-07 = só "dúvidas para t1" (29/04) — tópico-lixo; o scorer errou pra cá
BLOCK_07 = {
    "id": "bloco-07",
    "block_uuid": UUID_07,
    "topic_text": "duvidas para",
    "sessions": [
        {"date": "2026-04-29", "label": "duvidas para t1 aula"},
    ],
    "kind": "class",
}

BLOCK_01 = {
    "id": "bloco-01",
    "block_uuid": UUID_01,
    "topic_text": "plano ensino introducao",
    "sessions": [{"date": "2026-03-02", "label": "plano de ensino aula"}],
    "kind": "class",
}

BLOCKS = [BLOCK_01, BLOCK_06, BLOCK_07]


def _passthrough_scorer(entry, blocks):
    return str(entry.get("computed_block_id") or "")


# ---------------------------------------------------------------------------
# year determinístico
# ---------------------------------------------------------------------------

def test_course_year_from_blocks_modal():
    from src.builder.routing.anchor_placement import _course_year_from_blocks
    assert _course_year_from_blocks(BLOCKS) == 2026


def test_course_year_from_blocks_empty_is_zero():
    from src.builder.routing.anchor_placement import _course_year_from_blocks
    assert _course_year_from_blocks([{"id": "b", "sessions": []}]) == 0


# ---------------------------------------------------------------------------
# Produtor: os 2 movers (Semana 9 hierárquico) → bloco-06
# ---------------------------------------------------------------------------

def test_apply_anchor_placement_mover_goes_to_06():
    from src.builder.routing.anchor_placement import apply_anchor_placement
    entry = {
        "id": "aula-sobre-agrupamento-parte-2-hierarquico",
        "manual_timeline_block_id": "",
        "source_section": "Semana 9 - 27.04 a 01.05 - Agrupamento Hierarquico",
        "computed_block_id": "bloco-07",  # scorer errou pra cá
    }
    entries = [entry]
    apply_anchor_placement(entries, BLOCKS, scorer_resolver=_passthrough_scorer)
    assert entry["temporal_block_id"] == UUID_06
    assert entry["temporal_block_method"] == "anchor"
    # KB intocado
    assert entry["computed_block_id"] == "bloco-07"


# ---------------------------------------------------------------------------
# Produtor: não-mover (anchor concorda com scorer) → temporal setado, computed igual
# ---------------------------------------------------------------------------

def test_apply_anchor_placement_non_mover_sets_temporal_keeps_computed():
    from src.builder.routing.anchor_placement import apply_anchor_placement
    entry = {
        "id": "agrupamento-usando-k-means",
        "manual_timeline_block_id": "",
        "source_section": "Semana 8 - 20.04 a 24.04 - Agrupamento K Means",
        "computed_block_id": "bloco-06",  # scorer já acertou
    }
    entries = [entry]
    apply_anchor_placement(entries, BLOCKS, scorer_resolver=_passthrough_scorer)
    assert entry["temporal_block_id"] == UUID_06
    assert entry["temporal_block_method"] == "anchor"
    assert entry["computed_block_id"] == "bloco-06"  # KB intocado


# ---------------------------------------------------------------------------
# Produtor: scorer → temporal_block_id NÃO é setado (cai no fallback do helper)
# ---------------------------------------------------------------------------

def test_apply_anchor_placement_manual_leaves_temporal_unset():
    """Anchor-only: method=manual NÃO grava temporal_block_id. Manual flui pelo
    fallback resolve_effective_block inalterado (não re-roteia em volta dele)."""
    from src.builder.routing.anchor_placement import apply_anchor_placement
    entry = {
        "id": "artigo-manual",
        "manual_timeline_block_id": UUID_01,  # verdade humana, bloco válido
        # tem âncora válida também, mas manual vence no resolve_placement (Tier 1)
        "source_section": "Semana 8 - 20.04 a 24.04 - Agrupamento K Means",
        "computed_block_id": "",
    }
    entries = [entry]
    apply_anchor_placement(entries, BLOCKS, scorer_resolver=_passthrough_scorer)
    assert not entry.get("temporal_block_id")
    assert not entry.get("temporal_block_method")


def test_apply_anchor_placement_scorer_leaves_temporal_unset():
    from src.builder.routing.anchor_placement import apply_anchor_placement
    entry = {
        "id": "artigo-externo",
        "manual_timeline_block_id": "",
        "source_section": "",  # sem seção → scorer
        "computed_block_id": "bloco-99",
    }
    entries = [entry]
    apply_anchor_placement(entries, BLOCKS, scorer_resolver=_passthrough_scorer)
    assert not entry.get("temporal_block_id")
    assert entry["computed_block_id"] == "bloco-99"


# ---------------------------------------------------------------------------
# Produtor: NUNCA muta computed_block_id (prova da desconflação KB)
# ---------------------------------------------------------------------------

def test_apply_anchor_placement_never_mutates_computed_block_id():
    from src.builder.routing.anchor_placement import apply_anchor_placement
    entries = [
        {"id": "a", "source_section": "Semana 9 - 27.04 a 01.05 - Agrupamento Hierarquico",
         "computed_block_id": "bloco-07", "manual_timeline_block_id": ""},
        {"id": "b", "source_section": "", "computed_block_id": "bloco-99",
         "manual_timeline_block_id": ""},
        {"id": "c", "source_section": "Semana 8 - 20.04 a 24.04 - Agrupamento K Means",
         "computed_block_id": "bloco-06", "manual_timeline_block_id": ""},
    ]
    before = {e["id"]: e["computed_block_id"] for e in entries}
    apply_anchor_placement(entries, BLOCKS, scorer_resolver=_passthrough_scorer)
    after = {e["id"]: e["computed_block_id"] for e in entries}
    assert before == after


# ---------------------------------------------------------------------------
# Gate de isolamento: enabled=False → resolve_placement NUNCA chamado
# ---------------------------------------------------------------------------

def test_apply_anchor_placement_disabled_never_calls_resolver():
    from src.builder.routing import anchor_placement
    entry = {
        "id": "x",
        "source_section": "Semana 9 - 27.04 a 01.05 - Agrupamento Hierarquico",
        "computed_block_id": "bloco-07",
        "manual_timeline_block_id": "",
    }

    def _boom(*a, **k):
        raise AssertionError("resolve_placement não devia ser chamado com enabled=False")

    with patch.object(anchor_placement, "resolve_placement", _boom):
        anchor_placement.apply_anchor_placement([entry], BLOCKS, enabled=False,
                                                scorer_resolver=_passthrough_scorer)
    assert "temporal_block_id" not in entry


# ---------------------------------------------------------------------------
# Helper resolve_temporal_block — flag OFF ≡ resolve_effective_block (honra manual)
# ---------------------------------------------------------------------------

def test_resolve_temporal_block_no_temporal_honors_manual():
    from src.builder.routing.file_map import resolve_temporal_block, resolve_effective_block
    entry = {
        "id": "e",
        "manual_timeline_block_id": "bloco-01",
        "computed_block_id": "bloco-06",
        # sem temporal_block_id
    }
    got = resolve_temporal_block(entry, BLOCKS)
    assert got == resolve_effective_block(entry, BLOCKS).block_id
    assert got == "bloco-01"  # manual vence no fallback


def test_resolve_temporal_block_no_temporal_falls_to_computed():
    from src.builder.routing.file_map import resolve_temporal_block
    entry = {"id": "e", "manual_timeline_block_id": "", "computed_block_id": "bloco-06"}
    assert resolve_temporal_block(entry, BLOCKS) == "bloco-06"


# ---------------------------------------------------------------------------
# Helper — temporal_block_id vence quando presente
# ---------------------------------------------------------------------------

def test_resolve_temporal_block_temporal_wins():
    from src.builder.routing.file_map import resolve_temporal_block
    entry = {
        "id": "e",
        "manual_timeline_block_id": "",
        "computed_block_id": "bloco-07",
        "temporal_block_id": UUID_06,
    }
    assert resolve_temporal_block(entry, BLOCKS) == UUID_06


# ---------------------------------------------------------------------------
# Schema — temporal_block_id round-trip; default "" omitido do to_dict
# ---------------------------------------------------------------------------

def test_temporal_block_id_round_trips():
    from src.models.core import FileEntry
    e = FileEntry.from_dict({
        "source_path": "x.pdf",
        "file_type": "pdf", "category": "", "title": "X",
        "temporal_block_id": UUID_06,
        "temporal_block_method": "anchor",
    })
    d = e.to_dict()
    assert d.get("temporal_block_id") == UUID_06
    assert d.get("temporal_block_method") == "anchor"
    e2 = FileEntry.from_dict(d)
    assert e2.temporal_block_id == UUID_06
    assert e2.temporal_block_method == "anchor"


def test_temporal_block_id_default_omitted_from_to_dict():
    from src.models.core import FileEntry
    e = FileEntry.from_dict({"source_path": "y.pdf", "file_type": "pdf", "category": "", "title": "Y"})
    d = e.to_dict()
    assert "temporal_block_id" not in d
    assert "temporal_block_method" not in d
