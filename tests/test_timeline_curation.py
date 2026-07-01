"""Tests para curation store (overrides manuais de bloco) + helpers de UI."""

from __future__ import annotations

import json

import pytest

from src.builder.timeline.curation import (
    CURATION_FILENAME,
    apply_block_curation,
    load_block_curation,
    set_block_override,
)


# ---------------------------------------------------------------------------
# set / load round-trip
# ---------------------------------------------------------------------------

def test_set_then_load_roundtrip(tmp_path):
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", "holiday")
    cur = load_block_curation(tmp_path)
    assert cur == {"bloco-03": {"manual_kind_override": "holiday"}}
    assert (tmp_path / CURATION_FILENAME).exists()


def test_set_multiple_fields_accumulates(tmp_path):
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", "holiday")
    set_block_override(tmp_path, "bloco-03", "manual_topic_label", "Indução")
    cur = load_block_curation(tmp_path)
    assert cur["bloco-03"] == {
        "manual_kind_override": "holiday",
        "manual_topic_label": "Indução",
    }


def test_remove_field_with_empty_value(tmp_path):
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", "holiday")
    set_block_override(tmp_path, "bloco-03", "manual_topic_label", "X")
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", None)
    cur = load_block_curation(tmp_path)
    assert cur["bloco-03"] == {"manual_topic_label": "X"}


def test_remove_last_field_drops_block(tmp_path):
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", "holiday")
    set_block_override(tmp_path, "bloco-03", "manual_kind_override", "")
    assert load_block_curation(tmp_path) == {}


def test_invalid_field_raises(tmp_path):
    with pytest.raises(ValueError):
        set_block_override(tmp_path, "bloco-03", "campo_invalido", "x")


def test_empty_block_id_noop(tmp_path):
    set_block_override(tmp_path, "", "manual_kind_override", "holiday")
    assert load_block_curation(tmp_path) == {}


# ---------------------------------------------------------------------------
# load: ausente / corrompido
# ---------------------------------------------------------------------------

def test_load_missing_returns_empty(tmp_path):
    assert load_block_curation(tmp_path) == {}


def test_load_corrupt_returns_empty(tmp_path):
    (tmp_path / CURATION_FILENAME).write_text("{ not json", encoding="utf-8")
    assert load_block_curation(tmp_path) == {}


def test_load_wrong_shape_returns_empty(tmp_path):
    (tmp_path / CURATION_FILENAME).write_text(
        json.dumps({"version": 1, "blocks": "nope"}), encoding="utf-8"
    )
    assert load_block_curation(tmp_path) == {}


# ---------------------------------------------------------------------------
# apply_block_curation — merge in-place
# ---------------------------------------------------------------------------

def test_apply_merges_matching_ids(tmp_path):
    set_block_override(tmp_path, "bloco-02", "manual_kind_override", "holiday")
    blocks = [{"id": "bloco-01"}, {"id": "bloco-02"}, {"id": "bloco-03"}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[1]["manual_kind_override"] == "holiday"
    assert "manual_kind_override" not in blocks[0]


def test_apply_no_curation_returns_zero(tmp_path):
    blocks = [{"id": "bloco-01"}]
    assert apply_block_curation(blocks, tmp_path) == 0
    assert "manual_kind_override" not in blocks[0]


def test_apply_idempotent(tmp_path):
    set_block_override(tmp_path, "bloco-01", "manual_topic_label", "T")
    blocks = [{"id": "bloco-01"}]
    apply_block_curation(blocks, tmp_path)
    apply_block_curation(blocks, tmp_path)
    assert blocks[0]["manual_topic_label"] == "T"


def test_apply_skips_non_dict_blocks(tmp_path):
    set_block_override(tmp_path, "bloco-01", "manual_kind_override", "holiday")
    blocks = [None, "x", {"id": "bloco-01"}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1


# ---------------------------------------------------------------------------
# UI helpers (timeline_dashboard)
# ---------------------------------------------------------------------------

def test_block_kind_honors_override():
    from src.ui.timeline_dashboard import block_kind
    block = {"topic_text": "Aula normal", "unit_slug": "u1",
             "manual_kind_override": "holiday"}
    assert block_kind(block) == "holiday"


def test_save_block_kind_override_wrapper(tmp_path):
    from src.ui.timeline_dashboard import save_block_kind_override
    save_block_kind_override(tmp_path, "bloco-05", "assessment")
    assert load_block_curation(tmp_path)["bloco-05"]["manual_kind_override"] == "assessment"
    save_block_kind_override(tmp_path, "bloco-05", None)
    assert load_block_curation(tmp_path) == {}


def test_save_block_unit_override_wrapper(tmp_path):
    from src.ui.timeline_dashboard import save_block_unit_override
    save_block_unit_override(tmp_path, "bloco-12", "unidade-03-indecidibilidade")
    assert load_block_curation(tmp_path)["bloco-12"]["manual_unit_slug"] == "unidade-03-indecidibilidade"
    save_block_unit_override(tmp_path, "bloco-12", None)
    assert load_block_curation(tmp_path) == {}


def test_apply_curation_overrides_sets_unit(tmp_path):
    from src.builder.timeline.index import _apply_curation_overrides
    set_block_override(tmp_path, "bloco-12", "manual_unit_slug", "unidade-03")
    ti = {"version": 4, "blocks": [
        {"id": "bloco-12", "kind": "class", "unit_slug": "", "unit_confidence": 0.0,
         "topic_text": "halting problem", "sessions": [{"d": 1}]}
    ]}
    touched = _apply_curation_overrides(ti, tmp_path)
    assert touched == 1
    blk = ti["blocks"][0]
    assert blk["unit_slug"] == "unidade-03"
    assert blk["unit_confidence"] == 1.0


def test_kind_display_safe_lookup():
    from src.ui.timeline_dashboard import _kind_display
    assert _kind_display("class")["label"] == "Aula"
    fallback = _kind_display("garbage")
    assert fallback["icon"] == "❓"


def test_status_color_map_covers_all_statuses():
    from src.ui.timeline_dashboard import _STATUS_COLOR, _STATUS_LABEL
    statuses = {"ok", "needs_unit", "needs_topic", "needs_files",
                "non_applicable", "needs_review"}
    assert statuses <= set(_STATUS_COLOR)
    assert statuses <= set(_STATUS_LABEL)


# ---------------------------------------------------------------------------
# manual_scope_unit_slugs override
# ---------------------------------------------------------------------------

def test_scope_override_roundtrip(tmp_path):
    from src.builder.timeline.curation import set_block_override, load_block_curation
    set_block_override(tmp_path, "blk-01", "manual_scope_unit_slugs", ["u1", "u2"])
    cur = load_block_curation(tmp_path)
    assert cur["blk-01"]["manual_scope_unit_slugs"] == ["u1", "u2"]


def test_scope_override_empty_list_removes(tmp_path):
    from src.builder.timeline.curation import set_block_override, load_block_curation
    set_block_override(tmp_path, "blk-01", "manual_scope_unit_slugs", ["u1"])
    set_block_override(tmp_path, "blk-01", "manual_scope_unit_slugs", [])
    assert load_block_curation(tmp_path) == {}


def test_save_block_scope_override_wrapper(tmp_path):
    from src.ui.timeline_dashboard import save_block_scope_override
    from src.builder.timeline.curation import load_block_curation
    save_block_scope_override(tmp_path, "blk-01", ["u1", "u2"])
    assert load_block_curation(tmp_path)["blk-01"]["manual_scope_unit_slugs"] == ["u1", "u2"]
    save_block_scope_override(tmp_path, "blk-01", [])
    assert load_block_curation(tmp_path) == {}


def test_scope_override_applies_renamed(tmp_path):
    from src.builder.timeline.curation import set_block_override, apply_block_curation
    set_block_override(tmp_path, "blk-01", "manual_scope_unit_slugs", ["u1", "u2"])
    blocks = [{"id": "blk-01"}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[0]["block_manual_scope_slugs"] == ["u1", "u2"]
    assert "manual_scope_unit_slugs" not in blocks[0]


# ---------------------------------------------------------------------------
# apply_block_curation — uuid-keyed curation (migrated files, Task 3)
# ---------------------------------------------------------------------------

def test_apply_uuid_keyed_curation_applies_override(tmp_path):
    """Curation migrada (chave = block_uuid) deve ser aplicada ao bloco."""
    import json
    uuid = "a1b2c3d4-0001-0000-0000-000000000000"
    curation_data = {
        "version": 1,
        "blocks": {uuid: {"manual_kind_override": "holiday"}},
    }
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation_data), encoding="utf-8"
    )
    blocks = [{"id": "bloco-03", "block_uuid": uuid}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[0]["manual_kind_override"] == "holiday"


def test_apply_uuid_keyed_all_fields(tmp_path):
    """Todos os campos override funcionam via chave uuid."""
    import json
    uuid = "a1b2c3d4-0002-0000-0000-000000000000"
    curation_data = {
        "version": 1,
        "blocks": {uuid: {
            "manual_kind_override": "assessment",
            "manual_topic_label": "Prova Final",
            "manual_unit_slug": "unidade-10",
        }},
    }
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation_data), encoding="utf-8"
    )
    blocks = [{"id": "bloco-07", "block_uuid": uuid}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[0]["manual_kind_override"] == "assessment"
    assert blocks[0]["manual_topic_label"] == "Prova Final"
    assert blocks[0]["block_manual_unit_slug"] == "unidade-10"


def test_apply_legacy_key_still_works_after_uuid_support(tmp_path):
    """Backwards-compat: curation keyed por bloco-NN (não migrada) ainda aplica."""
    set_block_override(tmp_path, "bloco-05", "manual_kind_override", "holiday")
    blocks = [{"id": "bloco-05"}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[0]["manual_kind_override"] == "holiday"


def test_apply_uuid_takes_priority_over_legacy_key(tmp_path):
    """Se existirem entradas uuid E bloco-NN, uuid vence."""
    import json
    uuid = "a1b2c3d4-0003-0000-0000-000000000000"
    curation_data = {
        "version": 1,
        "blocks": {
            uuid: {"manual_kind_override": "holiday"},
            "bloco-01": {"manual_kind_override": "assessment"},
        },
    }
    (tmp_path / ".timeline_curation.json").write_text(
        json.dumps(curation_data), encoding="utf-8"
    )
    blocks = [{"id": "bloco-01", "block_uuid": uuid}]
    touched = apply_block_curation(blocks, tmp_path)
    assert touched == 1
    assert blocks[0]["manual_kind_override"] == "holiday"
