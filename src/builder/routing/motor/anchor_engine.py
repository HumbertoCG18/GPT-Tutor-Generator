"""AnchorEngine (FASE 0): roteia D6/bibliografia p/ fora, senão janela->disambig.

TIER 0 (dup), TIER 1 (pino manual), janela-de-prazo real (assign_due) e TIER 3
(LLM) = fases seguintes. Aqui: escopo-disambiguator + funil honesto (None).
"""
from __future__ import annotations

import re
from typing import Optional, Set

from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext, LlmVoterProtocol
from src.builder.routing.motor.window_provider import resolve_window, drop_never_hosts, provider_card
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
# Meta-material da disciplina (plano de ensino, cronograma): o card nao importa.
_META_CATEGORIES = frozenset({"cronograma"})


def resolve_generic_reference(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]:
    """B-6 (2026-08-21): referencia SEM card -> primeiro bloco de aula.

    Convencao que o user aplicava a mao (4 pinos identicos em MF/IA para
    `aws`, `archive`, `o-que-e-IA`, `ia-responsavel`): bibliografia geral, sem
    secao no Moodle e sem data, mora na apresentacao da disciplina. Medido
    contra o gold: 4/5 — a excecao e `eth2` (referencia ESPECIFICA de Dafny,
    gold no bloco do topico), preco aceito para nao pinar. Com card, a entry
    segue a cascata normal (o card datado do IA resolve `artigo` sozinho).

    Meta-material (2026-09-01, dissecacao dos 117 votos de LLM): plano de
    ensino/cronograma dos 8 cursos iam ao llm-funil e o LLM escolhia o
    bloco-01 em 8/8 (gold 4/4). Mesma convencao, card ignorado (o plano mora
    em "Plano de Ensino"/"Informacoes Gerais"). method "meta-generica" para a
    regua vigiar em separado.
    """
    cat = str(entry.get("category") or "").strip().lower()
    meta = cat in _META_CATEGORIES
    if not meta and cat not in _REFERENCE_CATEGORIES:
        return None
    if not meta and str(entry.get("source_section") or "").strip():
        return None
    method = "meta-generica" if meta else "ref-generica"
    # "overview" = apresentacao da disciplina/plano (IA e SO usam esse kind no
    # bloco-01); onde nao existe, o primeiro bloco de aula.
    first = next((b for b in ctx.blocks
                  if str(b.get("kind") or "") in ("overview", "class", "") and b.get("id")), None)
    if first is None:
        return None
    ref = str(first.get("id"))
    return AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=False,
                          provider=method, method=method, window=[ref])


# "p1" / "prova 2" / "revisao p1" / "revisão para P1" -> N
_EXAM_CUE = re.compile(r"(?:^|[^a-z])(?:p\s?-?(\d)|prova\s?-?(\d)|revis[aã]o[- ]?(?:para[- ]?)?(?:a[- ]?)?p(\d))", re.I)
# Nao hospedam preparacao de prova: kinds que nunca hospedam material (inclui a
# aula suspensa — MF bloco-08 "suspensao" fica ENTRE a revisao e a P1) + a prova.
_NOT_PREP_HOSTS = frozenset(NEVER_HOSTS_MATERIAL_KINDS) | {"assessment"}

# D1 (ruling 28/08, implementado 01/09): prova PRINCIPAL = rotulo P<n>/"Prova N"
# no bloco (topic_text + labels de sessao — topic_text de bloco de prova e VAZIO
# na maioria dos cursos reais); PS/G2/PF/substitutiva/recuperacao NUNCA contam
# (cobrem o semestre inteiro — R7 da cobertura). A lista negativa antiga
# (_NOT_MAIN_EXAM sobre topic_text) errava nos DOIS sentidos, medido nos 6
# cursos em 01/09: G2 contava como principal em TODOS (topic vazio passa) e a
# P2 de MF/ES2 ("entrega do t2" no topic) ficava DE FORA — a prep-P2 do MF
# ancorava na G2. Bloco assessment SEM rotulo (SO-27/IA-24, resquicio
# LightGrey com label "aula") tambem nao e principal.
_MAIN_EXAM_LABEL_RE = re.compile(r"\bprova\s*-?\s*p?(\d)\b|\bp(\d)\b", re.I)
_NEVER_MAIN_RE = re.compile(r"\bps\b|\bg2\b|\bsubstitui|\brecupera|\bprova\s+final\b|\bpf\b", re.I)


def _block_exam_hay(block: dict) -> str:
    labels = " ".join(str(s.get("label") or "") for s in (block.get("sessions") or []))
    return f"{block.get('topic_text') or ''} {labels}".lower()


def is_main_exam_block(block: dict) -> bool:
    """Fonte unica da 'prova principal' (prep-prova aqui; R6 da cobertura)."""
    if str(block.get("kind") or "") != "assessment":
        return False
    hay = _block_exam_hay(block)
    if _NEVER_MAIN_RE.search(hay):
        return False
    return bool(_MAIN_EXAM_LABEL_RE.search(hay))


def _exam_number(entry: dict) -> int:
    for text in (entry.get("id"), entry.get("title"), entry.get("source_section")):
        m = _EXAM_CUE.search(str(text or ""))
        if m:
            return int(next(g for g in m.groups() if g))
    return 0


_PREP_WORD = re.compile(r"revis[aã]o|lista|exerc[ií]cio", re.I)


def is_exam_prep_material(entry: dict) -> bool:
    """"lista/revisao pN" e o seu gabarito sao PREPARACAO, nao a prova em si —
    mesmo quando a categoria e `provas` (MF `revisao-p1-gabarito`, "Respostas"
    da lista de revisao). A prova propriamente dita ("prova-1-2024-02") nao
    tem a palavra de preparacao e segue lexical=False."""
    if _exam_number(entry) <= 0:
        return False
    return any(_PREP_WORD.search(str(entry.get(k) or "")) for k in ("id", "title", "source_section"))


def resolve_exam_prep(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]:
    """Preparacao de prova (2026-08-25): "lista/revisao pN" SEM janela -> ultimo
    bloco hospedavel antes da N-esima prova PRINCIPAL.

    Convencao do user ("essas listas preparam o aluno para a prova, e sempre
    uma aula antes"), aplicada ao gold e medida nos 5 cursos: 7/7 (MF revisao-p1,
    SO lista-p1/p2 + gabarito + exercicios-p2, ES2 revisao-p1, TCC aula-16).
    Substituicao/entrega nao contam como prova principal. So entra onde a
    cascata nao tem janela (card generico "Informacoes Gerais" -> era llm-funil);
    card datado continua decidindo antes."""
    n = _exam_number(entry)
    if n <= 0:
        return None
    mains = [b for b in ctx.blocks if is_main_exam_block(b)]
    if n > len(mains):
        return None
    target = mains[n - 1]
    prev = None
    for b in ctx.blocks:
        if b is target:
            break
        if str(b.get("kind") or "") in _NOT_PREP_HOSTS or not b.get("id"):
            continue
        prev = b
    if prev is None:
        return None
    ref = str(prev.get("id"))
    return AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=False,
                          provider="prep-prova", method="prep-prova", window=[ref])


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
        window = drop_never_hosts([str(b.get("id") or "") for b in ctx.blocks if b.get("id")], ctx)
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
        prep_ok = lexical or is_exam_prep_material(entry)
        if not window:
            # sem janela -> preparacao de prova (deterministico; nunca para a
            # PROPRIA prova/trabalho, lexical=False) -> card como documento
            # ordenado (Fase 3b) -> llm-funil ou None
            prep = resolve_exam_prep(entry, ctx) if prep_ok else None
            if prep is not None:
                return prep
            window, provider = provider_card(entry, ctx), "card"
            if not window:
                return self.resolve_funnel(entry, ctx, markdown)
        if prep_ok and provider in ("ordinal", "topic"):
            # Balde B (2026-08-26): janela INDIRETA (card por topico "Exercicios de
            # Revisao para Prova" -> [05, 06]; "Aula 16" -> 16o encontro) nao vence a
            # convencao de preparacao de prova: o LLM votava 05 para MF revisao-p1
            # (gold 07 = ultimo bloco antes da P1) e o ordinal dava 19 para TCC
            # aula-16 (gold 16). Card manual/datado e data-no-nome continuam
            # decidindo antes. Medido no motor nu dos 5: +2, 0 regressoes.
            prep = resolve_exam_prep(entry, ctx)
            if prep is not None:
                return prep
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
            # nenhum ref da janela resolve (card_block_map com uuid obsoleto):
            # "funil honesto" hoje e o llm-funil, nao None. IA `ag-feito`: janela
            # [fantasma, evento]; sem o evento (kind proibido) sobrava so o
            # fantasma e a entry perdia o temporal inteiro (2026-08-21).
            return self.resolve_funnel(entry, ctx, markdown)
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
        if decision.flag and provider != "card":
            # Fase 3b (item 3): decisao ainda FLAGADA (sem voter, ou voto sem resposta) ->
            # o card lido como documento ordenado (semana do label / modulo datado + ordem
            # dos materiais, card_stream) estreita a janela e o texto decide dentro dela.
            # Nunca sobrepoe decisao confiante (medido 02/09: a tudo +13/-10, so flagados
            # +12/-5) e NUNCA preempta o voto: com o card antes do voter a janela-1 do card
            # calava o LLM e a curada caiu 199 -> 187 (03/09).
            card = provider_card(entry, ctx)
            if card:
                alt = disambiguate(entry, card, ctx, markdown, provider="card")
                # Mesmo bloco e mesma duvida = nada novo: o provider original (mais direto,
                # ex. data/janela-1 no SO) fica; so adota quando muda o bloco ou tira a flag.
                if alt.block_ref and (alt.block_ref != decision.block_ref or not alt.flag):
                    decision, provider = alt, "card"
                    decision.provider = "card"
        if provider == "card" and not decision.flag and decision.band == "alta":
            # Calibracao medida (motor puro dos 5, 03/09): das decisoes do card sem flag,
            # 8/11 certas (73%) — banda "alta" e ~98% no resto do motor. "media" e o
            # numero honesto; a decisao fica e nao entra na fila de duvida.
            decision.band = "media"
        return decision
