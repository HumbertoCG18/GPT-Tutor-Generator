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
    # review F4 C1: _write_temporal grava block_uuid cru; o leitor resolve p/
    # display id quando `blocks` está disponível (senão a cascata dashboard/
    # health/cronograma_health casa contra display ids e vê "unmapped").
    assert resolve_temporal_block(entry, BLOCKS) == "bloco-06"


def test_resolve_temporal_block_uuid_already_display_passes_through():
    """review F4 C1: valor já-display (não-uuid) continua passando intacto."""
    from src.builder.routing.file_map import resolve_temporal_block
    entry = {
        "id": "e",
        "manual_timeline_block_id": "",
        "computed_block_id": "bloco-07",
        "temporal_block_id": "bloco-06",
    }
    assert resolve_temporal_block(entry, BLOCKS) == "bloco-06"


def test_resolve_temporal_block_uuid_unresolvable_returns_raw_no_crash():
    """review F4 C1: uuid que não casa nenhum block_uuid -> comportamento atual
    (valor cru), sem crash — degradação graciosa quando blocks está desatualizado."""
    from src.builder.routing.file_map import resolve_temporal_block
    entry = {
        "id": "e",
        "manual_timeline_block_id": "",
        "computed_block_id": "bloco-07",
        "temporal_block_id": "uuid-que-nao-existe-em-blocks",
    }
    assert resolve_temporal_block(entry, BLOCKS) == "uuid-que-nao-existe-em-blocks"


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
