"""Motor de atribuição material->bloco (ANCHOR-ONLY, plugável mode-aware).

Pacote ISOLADO: proibido importar os símbolos condenados do cutover
(block_token_weights, score_entry_against_timeline_block,
select_probable_period_for_entry) — ver tests/test_motor_import_guard.py.
Reúso permitido: concept_resolver (scoring PURO), card_block, thresholds,
entry_signals, text/*.
"""
from src.builder.routing.motor.contracts import (
    AnchorDecision,
    MotorContext,
)
from src.builder.routing.motor.window_provider import resolve_window
from src.builder.routing.motor.disambiguator import disambiguate

__all__ = ["AnchorDecision", "MotorContext", "resolve_window", "disambiguate"]
