"""AnchorEngine (FASE 0): roteia D6/bibliografia p/ fora, senão janela->disambig.

TIER 0 (dup), TIER 1 (pino manual), janela-de-prazo real (assign_due) e TIER 3
(LLM) = fases seguintes. Aqui: escopo-disambiguator + funil honesto (None).
"""
from __future__ import annotations

from typing import Optional, Set

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext, LlmVoterProtocol
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
    """resolve(entry, ctx) -> AnchorDecision | None (None = funil-piso).

    TIER 3 (FASE 3): voter opcional — voter=None => saida byte-identica as
    FASES 0-2. Escopo do voto = decisao FLAGADA ∪ membro de serie same-theme
    (spec §3 TIER 3); aceitacao cega: band "media", flag=False, provider="llm"
    (spec §12 regra 3). Sem-janela nunca chega ao voto (funil antes).
    Janela-1 NUNCA vota (D4×janela-1, decisão 10/07): 1 candidato = voto sem informação.
    """

    def __init__(self, voter: Optional["LlmVoterProtocol"] = None,
                 series_ids: Optional[Set[str]] = None):
        self._voter = voter
        self._series_ids = frozenset(series_ids or ())

    def resolve_funnel(self, entry: dict, ctx: MotorContext, markdown: str = "") -> Optional[AnchorDecision]:
        """B-4 (2026-08-21): sem janela, o LLM vota com janela = TODOS os blocos.

        Revoga o "sem-janela nunca vota" da spec §12 por medicao: no funil o
        scorer concept-fused acertava 6/26 (23%); o LLM com a janela inteira,
        13/26 (50%), mantendo as 6 e sem voto fora da janela. band "media" +
        flag=True de proposito: 50% e honesto, a entry fica na fila humana e o
        method "llm-funil" deixa a regua vigiar esse degrau em separado.
        voter=None => None (funil de antes, byte-identico).
        """
        if self._voter is None:
            return None
        window = [str(b.get("id") or "") for b in ctx.blocks if b.get("id")]
        if not window:
            return None
        voted = self._voter.vote(entry, window, ctx, markdown)
        if not voted:
            return None
        return AnchorDecision(block_ref=voted, conf=0.0, band="media", flag=True,
                              provider="llm-funil", method="llm-funil", window=window)

    def resolve(self, entry: dict, ctx: MotorContext, markdown: str = "") -> Optional[AnchorDecision]:
        if is_out_of_disamb_scope(entry):
            return None
        window, provider = resolve_window(entry, ctx)
        if not window:
            return self.resolve_funnel(entry, ctx, markdown)  # sem janela -> llm-funil ou None
        decision = disambiguate(entry, window, ctx, markdown, provider=provider)
        if not decision.block_ref:
            return None  # nenhum ref da janela resolve -> funil honesto
        decision.provider = provider
        if self._voter is not None and len(window) > 1 and (
                decision.flag or str(entry.get("id") or "") in self._series_ids):
            voted = self._voter.vote(entry, window, ctx, markdown)
            if voted:
                decision.block_ref = voted
                decision.band = "media"
                decision.flag = False
                decision.provider = "llm"
                decision.method = "llm"
        return decision
