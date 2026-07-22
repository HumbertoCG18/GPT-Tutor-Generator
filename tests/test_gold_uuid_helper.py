"""Testes do helper true_of (F4 item 6, decisão user 08/07): gold uuid-first
com fallback true_block_id legado. O uuid não muda em reprocess; o display
(bloco-NN) pode driftar posicionalmente — true_of deve devolver o display
ATUAL do bloco quando o uuid resolve, não o rótulo stale gravado no CSV."""
from src.builder.routing.motor.contracts import MotorContext
from scripts.fase0_prova_motor_MF import true_of


def _ctx() -> MotorContext:
    blocks = [
        {"id": "bloco-01", "block_uuid": "u1", "period_start": "2026-03-01"},
        {"id": "bloco-02", "block_uuid": "u2", "period_start": "2026-03-08"},
    ]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})


def test_true_of_uuid_first_resolves_current_display():
    ctx = _ctx()
    row = {"true_block_uuid": "u2", "true_block_id": "bloco-02"}
    assert true_of(ctx, row) == "bloco-02"


def test_true_of_uuid_survives_display_drift():
    # uuid nao muda; display gravado no CSV ficou stale (drift posicional
    # pos-reprocess) -- true_of deve devolver o display ATUAL do bloco.
    ctx = _ctx()
    row = {"true_block_uuid": "u2", "true_block_id": "bloco-99-stale"}
    assert true_of(ctx, row) == "bloco-02"


def test_true_of_falls_back_to_display_when_uuid_empty():
    ctx = _ctx()
    row = {"true_block_uuid": "", "true_block_id": "bloco-01"}
    assert true_of(ctx, row) == "bloco-01"


def test_true_of_falls_back_when_uuid_column_absent():
    ctx = _ctx()
    row = {"true_block_id": "bloco-01"}  # coluna ainda nao migrada (CSV legado)
    assert true_of(ctx, row) == "bloco-01"


def test_true_of_falls_back_when_uuid_does_not_resolve():
    ctx = _ctx()
    row = {"true_block_uuid": "uuid-inexistente", "true_block_id": "bloco-01"}
    assert true_of(ctx, row) == "bloco-01"


def test_true_of_empty_when_no_truth_available():
    ctx = _ctx()
    row = {"true_block_uuid": "", "true_block_id": ""}
    assert true_of(ctx, row) == ""
