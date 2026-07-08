"""AnchorEngine (FASE 0): roteia D6/bibliografia p/ fora, senão janela->disambig.

TIER 0 (dup), TIER 1 (pino manual), janela-de-prazo real (assign_due) e TIER 3
(LLM) = fases seguintes. Aqui: escopo-disambiguator + funil honesto (None).
"""
from __future__ import annotations

from typing import Optional

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor.window_provider import resolve_window
from src.builder.routing.motor.disambiguator import disambiguate

# Categorias que NUNCA entram no disambiguator na FASE 0 (spec §3 TIER 2 + marco0).
# bibliografia/references/cronograma = funil direto (0 chamada LLM depois).
# trabalhos/provas = janela-de-prazo (FASE 4); fora do disambiguator já agora.
_OUT_CATEGORIES = frozenset({
    "bibliografia", "references", "referencias", "cronograma", "apoio",
    "trabalhos", "provas",
})
_TDE_PREFIX = "TDE"


def is_out_of_disamb_scope(entry: dict) -> bool:
    cat = str(entry.get("category") or "").strip().lower()
    if cat in _OUT_CATEGORIES:
        return True
    sec = str(entry.get("source_section") or "").strip()
    return sec.startswith(_TDE_PREFIX)


class AnchorEngine:
    """resolve(entry, ctx) -> AnchorDecision | None (None = funil-piso)."""

    def resolve(self, entry: dict, ctx: MotorContext, markdown: str = "") -> Optional[AnchorDecision]:
        if is_out_of_disamb_scope(entry):
            return None
        window, provider = resolve_window(entry, ctx)
        if not window:
            return None  # sem janela -> funil (invariante ANCHOR-ONLY)
        decision = disambiguate(entry, window, ctx, markdown, provider=provider)
        if not decision.block_ref:
            return None  # nenhum ref da janela resolve -> funil honesto
        decision.provider = provider
        return decision
