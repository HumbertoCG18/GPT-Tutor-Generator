"""TDD — WO2: leitor de manual_timeline_block_id casa uuid migrado (Fase 1).

Bug da classe: resolve_entry_manual_timeline_block casava só block.id (bloco-NN),
nunca block_uuid → pins uuid (Fase 1) viravam None → verdade-humana invisível
(período em branco nos 4 pins do IA). Fix: uuid-first + fallback bloco-NN/ordinal.

Independe da flag da âncora (o resolver não lê flag nenhuma).
"""
from __future__ import annotations

from src.builder.routing.file_map import (
    resolve_entry_manual_timeline_block,
    resolve_effective_block,
    resolve_temporal_block,
)

UUID_01 = "0101cccc-0000-0000-0000-000000000001"
UUID_05 = "0505dddd-0000-0000-0000-000000000005"

BLOCK_01 = {"id": "bloco-01", "block_uuid": UUID_01, "unit_slug": "unit-01",
            "period_label": "S1", "sessions": [{"date": "2026-03-02"}], "kind": "class"}
BLOCK_05 = {"id": "bloco-05", "block_uuid": UUID_05, "unit_slug": "unit-02",
            "period_label": "S5", "sessions": [{"date": "2026-03-30"}], "kind": "class"}
BLOCKS = [BLOCK_01, BLOCK_05]
CTX = {"timeline_index": {"blocks": BLOCKS}}


def test_uuid_pin_resolves_to_block():
    """Pin uuid (Fase 1) → casa block_uuid → retorna o bloco pinado (hoje: None)."""
    entry = {"id": "pin", "manual_timeline_block_id": UUID_01}
    block = resolve_entry_manual_timeline_block(entry, CTX)
    assert block is not None
    assert str(block.get("id")) == "bloco-01"


def test_legacy_bloco_nn_still_resolves():
    """Fallback não quebra a forma antiga: bloco-NN exato continua resolvendo."""
    entry = {"id": "legacy", "manual_timeline_block_id": "bloco-05"}
    block = resolve_entry_manual_timeline_block(entry, CTX)
    assert block is not None
    assert str(block.get("id")) == "bloco-05"


def test_empty_manual_returns_none():
    assert resolve_entry_manual_timeline_block({"id": "x"}, CTX) is None


def test_uuid_pin_surfaces_in_effective_block():
    """O fix faz o pin aparecer nas superfícies: resolve_effective_block = manual."""
    entry = {"id": "pin", "manual_timeline_block_id": UUID_01, "computed_block_id": "bloco-05"}
    eb = resolve_effective_block(entry, BLOCKS)
    assert eb.block_id == "bloco-01"
    assert eb.source == "manual"


def test_uuid_pin_surfaces_in_temporal_block():
    """resolve_temporal_block (flag OFF, sem temporal) cai no fallback que agora honra o pin."""
    entry = {"id": "pin", "manual_timeline_block_id": UUID_01, "computed_block_id": "bloco-05"}
    assert resolve_temporal_block(entry, BLOCKS) == "bloco-01"


def test_resolver_is_flag_independent():
    """O resolver não lê flag de âncora: resolve igual sem qualquer contexto de flag."""
    entry = {"id": "pin", "manual_timeline_block_id": UUID_01}
    # nenhuma options/flag passada — resolve mesmo assim
    assert resolve_entry_manual_timeline_block(entry, CTX).get("id") == "bloco-01"
