"""AnchorEngine (FASE 0): roteia D6/bibliografia p/ fora, senão janela->disambig.

TIER 0 (dup), TIER 1 (pino manual), janela-de-prazo real (assign_due) e TIER 3
(LLM) = fases seguintes. Aqui: escopo-disambiguator + funil honesto (None).
"""
from __future__ import annotations

from typing import Optional, Set

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext, LlmVoterProtocol
from src.builder.routing.motor.window_provider import resolve_window
from src.builder.routing.motor.disambiguator import disambiguate

# Categorias que NUNCA entram no disambiguator (spec §3 TIER 2 + marco0).
# trabalhos/provas = janela-de-prazo (tier2 no apply.py, antes do engine).
# bibliografia/references/cronograma/apoio SAIRAM da lista em 2026-08-21 (B-5):
# o gold da a elas um bloco (plano -> bloco-01; artigo com card datado -> bloco
# da semana) e 12 das 14 em producao ja tinham pino manual, que vence antes.
# Liberadas, as 2 sem pino acertam (janela-1 pelo card datado; llm-funil).
# O card TDE continua fora: e agrupamento administrativo, nao tema.
_OUT_CATEGORIES = frozenset({"trabalhos", "provas"})
_TDE_PREFIX = "TDE"


def is_out_of_disamb_scope(entry: dict) -> bool:
    cat = str(entry.get("category") or "").strip().lower()
    if cat in _OUT_CATEGORIES:
        return True
    sec = str(entry.get("source_section") or "").strip()
    return sec.startswith(_TDE_PREFIX)


_REFERENCE_CATEGORIES = frozenset({"bibliografia", "references", "referencias"})


def resolve_generic_reference(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]:
    """B-6 (2026-08-21): referencia SEM card -> primeiro bloco de aula.

    Convencao que o user aplicava a mao (4 pinos identicos em MF/IA para
    `aws`, `archive`, `o-que-e-IA`, `ia-responsavel`): bibliografia geral, sem
    secao no Moodle e sem data, mora na apresentacao da disciplina. Medido
    contra o gold: 4/5 — a excecao e `eth2` (referencia ESPECIFICA de Dafny,
    gold no bloco do topico), preco aceito para nao pinar. Com card, a entry
    segue a cascata normal (o card datado do IA resolve `artigo` sozinho).
    """
    cat = str(entry.get("category") or "").strip().lower()
    if cat not in _REFERENCE_CATEGORIES:
        return None
    if str(entry.get("source_section") or "").strip():
        return None
    # "overview" = apresentacao da disciplina/plano (IA e SO usam esse kind no
    # bloco-01); onde nao existe, o primeiro bloco de aula.
    first = next((b for b in ctx.blocks
                  if str(b.get("kind") or "") in ("overview", "class", "") and b.get("id")), None)
    if first is None:
        return None
    ref = str(first.get("id"))
    return AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=False,
                          provider="ref-generica", method="ref-generica", window=[ref])


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
        return self.resolve_unscoped(entry, ctx, markdown)

    def resolve_unscoped(self, entry: dict, ctx: MotorContext, markdown: str = "",
                         *, lexical: bool = True) -> Optional[AnchorDecision]:
        """Cascata de janela + desempate + voto + llm-funil, SEM a checagem de
        escopo. apply.py chama daqui para provas/trabalhos sem due casado (B-6,
        2026-08-21): um card MANUAL "Semana 14 - Apresentacoes T2" -> bloco-25
        cobre as 5 entries do cluster de uma vez, em vez de 5 pinos.

        lexical=False (trabalhos/provas): o texto de um enunciado descreve o
        CONTEUDO cobrado, nao a entrega — o desempate por token aponta a aula
        do assunto (TCC `t1-enunciado` -> aula 03, entrega = 04). Com janela
        de 1 bloco a estrutura (card/data) decide; com mais, so o voto sobre a
        janela, nunca o token."""
        window, provider = resolve_window(entry, ctx)
        if not window:
            return self.resolve_funnel(entry, ctx, markdown)  # sem janela -> llm-funil ou None
        if not lexical and len(window) > 1:
            if self._voter is None:
                return None
            voted = self._voter.vote(entry, window, ctx, markdown)
            if not voted:
                return None
            return AnchorDecision(block_ref=voted, conf=0.0, band="media", flag=False,
                                  provider="llm", method="llm", window=list(window))
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
