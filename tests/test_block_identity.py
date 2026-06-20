"""TDD — Task 1: identity ledger + block_uuid + re-attach + refuse-guard.

Testes:
  T2  re-sync muda data → uuid re-anexa, NÃO re-cunha
  T3  empate/sem-data → desempate por topic_tokens; sem desempate → cunha + flag
  T4  refuse-guard: ledger vazio + refs existentes → raise; sem refs → cunha ok
  ledger round-trip  load/save atômico
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.builder.timeline.block_identity import (
    BlockIdentityError,
    load_identity_ledger,
    reattach_block_uuids,
    save_identity_ledger,
    scan_existing_block_refs,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_SEQ = iter(range(1000))


def _mint():
    return f"uuid-{next(_SEQ):04d}"


def _block(period_start="", period_end="", topic_text="", display_id="bloco-01"):
    return {
        "id": display_id,
        "period_start": period_start,
        "period_end": period_end,
        "topic_text": topic_text,
        "topics": [],
        "aliases": [],
    }


def _record(uuid, start, end, tokens=None, display_id="bloco-01"):
    return {
        "uuid": uuid,
        "anchor": {
            "period_start": start,
            "period_end": end,
            "topic_tokens": tokens or [],
        },
        "display_id_last": display_id,
        "first_seen": "2026-01-01",
        "last_seen": "2026-01-01",
    }


# ---------------------------------------------------------------------------
# ledger round-trip
# ---------------------------------------------------------------------------


def test_load_returns_empty_list_when_absent(tmp_path):
    assert load_identity_ledger(tmp_path) == []


def test_save_and_load_round_trip(tmp_path):
    records = [_record("uuid-abc", "2026-01-01", "2026-01-15")]
    save_identity_ledger(tmp_path, records)
    loaded = load_identity_ledger(tmp_path)
    assert loaded == records


def test_save_is_atomic_no_tmp_residue(tmp_path):
    save_identity_ledger(tmp_path, [_record("uuid-x", "2026-01-01", "2026-01-10")])
    names = [p.name for p in tmp_path.iterdir()]
    assert ".block_identity.json" in names
    assert not any(n.endswith(".tmp") for n in names)


# ---------------------------------------------------------------------------
# T2 — re-sync muda data: best-overlap herda uuid
# ---------------------------------------------------------------------------


def test_t2_resync_date_shift_inherits_uuid():
    """Ledger: anchor D1..D4 (2026-01-01..2026-01-20).
    Rebuild: bloco deslocado p/ D2..D5 (2026-01-05..2026-01-25).
    Overlap original D1..D4 ∩ D2..D5 = D2..D4 (15d).
    Must inherit same uuid, NOT mint.
    """
    ledger = [_record("uuid-A", "2026-01-01", "2026-01-20")]
    blocks = [_block("2026-01-05", "2026-01-25", display_id="bloco-01")]

    blocks_out, ledger_out, flags = reattach_block_uuids(
        blocks, ledger, has_existing_refs=False, mint=_mint
    )

    assert blocks_out[0]["block_uuid"] == "uuid-A"
    assert not flags
    # ledger still has exactly 1 record (append-only, no dup)
    uuids = [r["uuid"] for r in ledger_out]
    assert uuids.count("uuid-A") == 1


def test_t2_last_seen_refreshed_on_match():
    from src.builder.timeline.block_identity import _today

    ledger = [_record("uuid-B", "2026-01-01", "2026-01-20")]
    blocks = [_block("2026-01-05", "2026-01-25", display_id="bloco-01")]

    _, ledger_out, _ = reattach_block_uuids(
        blocks, ledger, has_existing_refs=False, mint=_mint
    )
    matched = next(r for r in ledger_out if r["uuid"] == "uuid-B")
    assert matched["last_seen"] == _today()


# ---------------------------------------------------------------------------
# T3 — empate de datas / sem data
# ---------------------------------------------------------------------------


def test_t3_tiebreak_by_topic_tokens():
    """2 blocos com MESMA janela de datas → desempate por topic_tokens."""
    ledger = [
        _record("uuid-X", "2026-02-01", "2026-02-28", tokens=["python", "lista"]),
        _record("uuid-Y", "2026-02-01", "2026-02-28", tokens=["java", "heranca"]),
    ]
    block_x = _block("2026-02-01", "2026-02-28", topic_text="python lista", display_id="bloco-01")
    block_y = _block("2026-02-01", "2026-02-28", topic_text="java heranca", display_id="bloco-02")

    blocks_out, _, flags = reattach_block_uuids(
        [block_x, block_y], ledger, has_existing_refs=False, mint=_mint
    )

    assert blocks_out[0]["block_uuid"] == "uuid-X"
    assert blocks_out[1]["block_uuid"] == "uuid-Y"
    assert not flags


def test_t3_no_date_mints_new_uuid_and_flags():
    """Bloco sem data (period_start='') → cunha novo uuid + loga flag."""
    ledger = [_record("uuid-C", "2026-01-01", "2026-01-15")]
    blocks = [_block("", "", topic_text="algo", display_id="bloco-01")]

    blocks_out, ledger_out, flags = reattach_block_uuids(
        blocks, ledger, has_existing_refs=False, mint=_mint
    )

    minted = blocks_out[0]["block_uuid"]
    assert minted != "uuid-C"
    assert any(minted in f for f in flags)
    # minted record appended
    assert any(r["uuid"] == minted for r in ledger_out)


def test_t3_exact_date_tie_no_token_overlap_mints_and_flags():
    """Empate exato de overlap sem desempate por token → cunha + flag."""
    ledger = [
        _record("uuid-P", "2026-03-01", "2026-03-31", tokens=["algebra"]),
        _record("uuid-Q", "2026-03-01", "2026-03-31", tokens=["calculo"]),
    ]
    # block with NO topic tokens → cannot tiebreak
    block = _block("2026-03-01", "2026-03-31", topic_text="", display_id="bloco-01")

    blocks_out, ledger_out, flags = reattach_block_uuids(
        [block], ledger, has_existing_refs=False, mint=_mint
    )

    minted = blocks_out[0]["block_uuid"]
    assert minted not in ("uuid-P", "uuid-Q")
    assert any(minted in f for f in flags)


# ---------------------------------------------------------------------------
# T4 — refuse-guard
# ---------------------------------------------------------------------------


def test_t4_empty_ledger_with_refs_raises():
    """ledger=[] + has_existing_refs=True → BlockIdentityError."""
    blocks = [_block("2026-01-01", "2026-01-15")]
    with pytest.raises(BlockIdentityError):
        reattach_block_uuids(blocks, [], has_existing_refs=True, mint=_mint)


def test_t4_empty_ledger_no_refs_mints_ok():
    """ledger=[] + has_existing_refs=False → cunha à vontade."""
    blocks = [_block("2026-01-01", "2026-01-15")]
    blocks_out, ledger_out, flags = reattach_block_uuids(
        blocks, [], has_existing_refs=False, mint=_mint
    )
    assert "block_uuid" in blocks_out[0]
    assert len(ledger_out) == 1


# ---------------------------------------------------------------------------
# T — zero overlap mints new uuid (append)
# ---------------------------------------------------------------------------


def test_zero_overlap_mints_and_appends():
    """Bloco sem sobreposição com nenhum registro → cunha + append."""
    ledger = [_record("uuid-OLD", "2025-01-01", "2025-01-31")]
    blocks = [_block("2026-06-01", "2026-06-30", display_id="bloco-01")]

    blocks_out, ledger_out, flags = reattach_block_uuids(
        blocks, ledger, has_existing_refs=False, mint=_mint
    )

    minted = blocks_out[0]["block_uuid"]
    assert minted != "uuid-OLD"
    assert len(ledger_out) == 2  # old + new


# ---------------------------------------------------------------------------
# scan_existing_block_refs
# ---------------------------------------------------------------------------


def test_scan_returns_false_when_no_files(tmp_path):
    assert scan_existing_block_refs(tmp_path, {}) is False


_SAMPLE_UUID = "550e8400-e29b-41d4-a716-446655440000"


def test_scan_returns_true_when_card_block_map_has_uuid_block_ids(tmp_path):
    cbm = {"Semana 1": {"block_ids": [_SAMPLE_UUID], "confidence": 0.9, "reason": "ok"}}
    (tmp_path / ".card_block_map.json").write_text(
        json.dumps(cbm), encoding="utf-8"
    )
    assert scan_existing_block_refs(tmp_path, {}) is True


def test_scan_returns_false_when_card_block_map_has_only_positional_ids(tmp_path):
    cbm = {"Semana 1": {"block_ids": ["bloco-01"], "confidence": 0.9, "reason": "ok"}}
    (tmp_path / ".card_block_map.json").write_text(
        json.dumps(cbm), encoding="utf-8"
    )
    assert scan_existing_block_refs(tmp_path, {}) is False


def test_scan_returns_true_when_manifest_has_uuid_manual_block_id(tmp_path):
    manifest = {"manual_timeline_block_id": _SAMPLE_UUID}
    assert scan_existing_block_refs(tmp_path, manifest) is True


def test_scan_returns_false_when_manifest_has_positional_manual_block_id(tmp_path):
    manifest = {"manual_timeline_block_id": "bloco-02"}
    assert scan_existing_block_refs(tmp_path, manifest) is False


def test_scan_returns_true_when_curation_has_uuid_keys(tmp_path):
    curation = {"version": 1, "blocks": {_SAMPLE_UUID: {"manual_kind_override": "holiday"}}}
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation), encoding="utf-8"
    )
    assert scan_existing_block_refs(tmp_path, {}) is True


def test_scan_returns_false_when_curation_has_positional_keys(tmp_path):
    curation = {"version": 1, "blocks": {"bloco-03": {"manual_kind_override": "holiday"}}}
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation), encoding="utf-8"
    )
    assert scan_existing_block_refs(tmp_path, {}) is False


def test_scan_returns_false_when_curation_has_empty_blocks(tmp_path):
    curation = {"version": 1, "blocks": {}}
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation), encoding="utf-8"
    )
    assert scan_existing_block_refs(tmp_path, {}) is False
