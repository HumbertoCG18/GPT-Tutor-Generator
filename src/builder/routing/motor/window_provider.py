"""WindowProvider: cascata de providers por CONFIABILIDADE (P1 manual > P2 labels).

FASE 0: só P1/P2 (card_block_map). P3 (data-no-nome) e P4 (tópico) = FASE 2.
Retorna janela como lista de refs DISPLAY (bloco-NN). [] = sem janela = funil.
"""
from __future__ import annotations

from typing import List, Tuple

from src.utils.helpers import norm_ascii_lower
from src.builder.timeline.card_block import normalized_card_map

from src.builder.routing.motor.contracts import MotorContext


def _card_entry(entry: dict, ctx: MotorContext) -> dict:
    """Entrada do card_block_map para a source_section da entry (match sem
    acento/caixa via card_block.normalized_card_map — helper ÚNICO; em
    colisão, o último vence)."""
    key = norm_ascii_lower(str(entry.get("source_section") or ""))
    if not key:
        return {}
    # Card malformado (não-dict) degrada para janela vazia, não crashes.
    info = normalized_card_map(ctx.card_block_map).get(key)
    return info if isinstance(info, dict) else {}


def _window_for_source(entry: dict, ctx: MotorContext, source: str) -> List[str]:
    info = _card_entry(entry, ctx)
    if str(info.get("source") or "") != source:
        return []
    return [str(b) for b in (info.get("block_ids") or []) if str(b)]


def provider_manual(entry: dict, ctx: MotorContext) -> List[str]:
    """P1 — card-window MANUAL (verdade humana)."""
    return _window_for_source(entry, ctx, "manual")


def provider_labels(entry: dict, ctx: MotorContext) -> List[str]:
    """P2 — card_block_map LABELS datado (parse_card_dates A-D)."""
    return _window_for_source(entry, ctx, "labels")


# Cascata em ordem de CONFIABILIDADE. Cada par (fn, nome).
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
)


def resolve_window(entry: dict, ctx: MotorContext) -> Tuple[List[str], str]:
    """1º provider com janela não-vazia -> (janela, nome_provider). ([], "") = funil."""
    for fn, name in _CASCADE:
        win = fn(entry, ctx)
        if win:
            return win, name
    return [], ""
