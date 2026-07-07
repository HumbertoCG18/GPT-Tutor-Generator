from dataclasses import fields

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext


def test_anchor_decision_fields_and_defaults():
    d = AnchorDecision(block_ref="bloco-05")
    assert d.block_ref == "bloco-05"
    assert d.conf == 0.0
    assert d.band == ""
    assert d.flag is False
    assert d.provider == ""
    assert d.method == ""
    assert d.window == []
    names = {f.name for f in fields(AnchorDecision)}
    assert names == {"block_ref", "conf", "band", "flag", "provider", "method", "window"}


def test_anchor_decision_window_is_not_shared():
    a = AnchorDecision(block_ref="bloco-01")
    b = AnchorDecision(block_ref="bloco-02")
    a.window.append("bloco-01")
    assert b.window == []  # default_factory, não lista compartilhada


def test_motor_context_indexes_blocks_by_ref():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u1", "period_start": "2026-03-04"},
        {"id": "bloco-02", "block_uuid": "u2", "period_start": "2026-03-02"},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    # ordena por period_start
    assert [b["id"] for b in ctx.blocks] == ["bloco-02", "bloco-01"]
    # índice por id E por uuid
    assert ctx.block_by_ref("bloco-01")["block_uuid"] == "u1"
    assert ctx.block_by_ref("u2")["id"] == "bloco-02"
    assert ctx.block_by_ref("inexistente") is None
