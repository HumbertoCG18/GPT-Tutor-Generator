"""T5 tests — Task 3: HUMAN-TRUTH surfaces migrated to uuid with FLAG trava."""
import pytest
from src.builder.timeline.block_identity import (
    migrate_human_truth_block_refs,
    migrate_primary_block_ids,
)

BLOCKS = [
    {"id": "bloco-01", "block_uuid": "uuid-01"},
    {"id": "bloco-02", "block_uuid": "uuid-02"},
    {"id": "bloco-03", "block_uuid": "uuid-03"},
]


def test_t5_manual_timeline_resolves_to_uuid():
    entries = [{"id": "e1", "manual_timeline_block_id": "bloco-03"}]
    updated, _, flags = migrate_human_truth_block_refs(entries, {}, BLOCKS)
    assert updated[0]["manual_timeline_block_id"] == "uuid-03"
    assert flags == []


def test_t5_manual_timeline_unresolvable_flags_not_dropped():
    entries = [{"id": "e1", "manual_timeline_block_id": "bloco-99"}]
    updated, _, flags = migrate_human_truth_block_refs(entries, {}, BLOCKS)
    assert updated[0]["manual_timeline_block_id"] == "bloco-99"
    assert len(flags) == 1
    assert flags[0]["surface"] == "manual_timeline_block_id"
    assert flags[0]["raw_value"] == "bloco-99"


def test_t5_curation_key_resolves_to_uuid():
    curation = {"bloco-03": {"note": "override"}}
    _, updated_cur, flags = migrate_human_truth_block_refs([], curation, BLOCKS)
    assert "uuid-03" in updated_cur
    assert "bloco-03" not in updated_cur
    assert flags == []


def test_t5_curation_key_unresolvable_flags_not_dropped():
    curation = {"bloco-99": {"note": "override"}}
    _, updated_cur, flags = migrate_human_truth_block_refs([], curation, BLOCKS)
    assert "bloco-99" in updated_cur
    assert len(flags) == 1
    assert flags[0]["surface"] == "timeline_curation_key"
    assert flags[0]["raw_value"] == "bloco-99"


def test_t5_primary_block_id_resolves_to_uuid():
    entries = [{"id": "e1", "summary": {"primary_block_id": "bloco-03"}}]
    updated, flags = migrate_primary_block_ids(entries, BLOCKS)
    assert updated[0]["summary"]["primary_block_id"] == "uuid-03"
    assert flags == []


def test_t5_primary_block_id_unresolvable_flags_not_dropped():
    entries = [{"id": "e1", "summary": {"primary_block_id": "bloco-99"}}]
    updated, flags = migrate_primary_block_ids(entries, BLOCKS)
    assert updated[0]["summary"]["primary_block_id"] == "bloco-99"
    assert len(flags) == 1
    assert flags[0]["surface"] == "primary_block_id"
    assert flags[0]["raw_value"] == "bloco-99"


def test_t5_bare_int_resolves():
    entries = [{"id": "e1", "manual_timeline_block_id": "3"}]
    updated, _, flags = migrate_human_truth_block_refs(entries, {}, BLOCKS)
    assert updated[0]["manual_timeline_block_id"] == "uuid-03"
    assert flags == []


def test_t5_uuid_passthrough():
    entries = [{"id": "e1", "manual_timeline_block_id": "uuid-03"}]
    updated, _, flags = migrate_human_truth_block_refs(entries, {}, BLOCKS)
    assert updated[0]["manual_timeline_block_id"] == "uuid-03"
    assert flags == []
