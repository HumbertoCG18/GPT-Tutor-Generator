"""Disambiguator: escolhe DENTRO da janela (|janela|>1) por IDF len-norm.

Reúso PURO: concept_resolver.concept_token_weights/concept_vector (bounded à
janela) — mas a tokenização/stems desta fase espelha marco0 (prova cacheada
Config A' = 59.7%) para o número bater. session-label é 1ª classe (peso acima
do topic_text agregado).

PROIBIDO importar block_token_weights/score_entry_against_timeline_block/
select_probable_period_for_entry (guard test).
"""
from __future__ import annotations

import math
import re
from typing import Optional, List

from src.builder.text.normalize import normalize_match_text
from src.builder.text.tokens import motor_tokens
from src.builder.routing.motor.contracts import MotorContext, AnchorDecision
from src.builder.routing.thresholds import confidence_band

# Espelha marco0._GEN: stems (prefixo 8) que NÃO discriminam bloco.
# Palavras-função PT: medição 2026-08-05 (docs/reports/2026-08-05-planob-investigacao.md
# §2a) — lista conservadora zera confident-wrong com acurácia intacta (84.2%);
# NÃO estender com demonstrativos/comparativos: a versão larga custou 2 casos (78.9%).
_GENERIC_STEMS = frozenset({
    "introduc", "continua", "exercici", "revisao", "conteudo", "material",
    "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula",
    "para", "resposta", "solucao", "lista",
    # boilerplate de curso (2026-08-21): "apresentacao da DISCIPLINA" e
    # "ESTUDO de CASO" vivem na assinatura do bloco-01 de todo curso e puxavam
    # material generico para la (MF `introducao`, ES2 `azure`).
    "discipli", "estudo", "caso",
    # "trabalho" e o nome da categoria, nao do assunto (ES2 `kubernetes` ia
    # sozinho para "Entrega trabalho final" por esse unico token).
    "trabalho",
    "nao", "sim", "com", "sem", "por", "dos", "das", "nos", "nas", "uma", "que",
})


def _toks(text: str, short_vocab=frozenset()) -> set:
    """Tokens normalizados >=3 chars (ou curtos consagrados em short_vocab), sem dígitos-puros
    nem stems genéricos. Fonte única: text.tokens.motor_tokens (corte 3 do refactor)."""
    return motor_tokens(text, generic_stems=_GENERIC_STEMS, short_vocab=short_vocab)


def course_short_vocab(ctx: MotorContext) -> frozenset:
    """Tokens CURTOS (2-3 chars) consagrados pelo CRONOGRAMA do curso: topic_text +
    primary_topic_label + labels de sessao (Fase 3c). "ag"/"hc"/"sa" valem no IA porque
    uma sessao os consagra; seguem ruido onde nenhuma o faz. Memoizado no ctx."""
    if ctx._short_vocab_cache is not None:
        return ctx._short_vocab_cache
    from src.builder.text.stopwords import short_vocab_from_topic_labels
    texts = []
    for b in ctx.blocks:
        texts.append(normalize_match_text(str(b.get("topic_text") or "") + " " + str(b.get("primary_topic_label") or "")))
        for s in b.get("sessions") or []:
            texts.append(normalize_match_text(str(s.get("label") or "")))
    ctx._short_vocab_cache = frozenset(short_vocab_from_topic_labels(texts))
    return ctx._short_vocab_cache


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def entry_tokens(entry: dict, markdown: str = "", short_vocab=frozenset()) -> set:
    """Sinal LIMPO do material: título + moodle_label + markdown (capado fora)."""
    parts = [str(entry.get("title") or ""), _moodle_label_text(entry), str(markdown or "")]
    return _toks(" ".join(p for p in parts if p), short_vocab)


def block_topic_tokens(block: dict, short_vocab=frozenset()) -> set:
    """Assinatura GROSSA do bloco: topic_text + primary_topic_label."""
    return _toks(
        str(block.get("topic_text") or "") + " " + str(block.get("primary_topic_label") or ""), short_vocab
    )


def block_session_tokens(block: dict, ctx: MotorContext, short_vocab=frozenset()) -> set:
    """Assinatura FINA (1ª classe): sessions[].label + roteiro do dia (lessons_index)."""
    out: set = set()
    for sess in block.get("sessions") or []:
        out |= _toks(str(sess.get("label") or ""), short_vocab)
        # R12: chave do lessons_index e a DATA (YYYY-MM-DD); llm_vote ja trunca
        # [:10] — sem truncar aqui, um date com hora perde o roteiro do dia.
        topic = ctx.lessons_index.get(str(sess.get("date") or "")[:10])
        if topic:
            out |= _toks(str(topic), short_vocab)
    return out


# Pesos da fusão (calibração TDD — spec §12). session-label (fino) > topic (grosso).
W_SESSION_LABEL: float = 1.0
W_TOPIC: float = 0.6
# Calibração FASE 1 (grade com recall, 2026-07-07): grade 4x3x3 na régua
# externa MF mostrou acc par-colapsada invariante a W_TOPIC/W_SESSION_LABEL
# (70.7% em todos os 36 pontos); só MARGIN_TAU move confiante-errado/recall.
# 0.55 é o mínimo de confiante-errado (5->3) com recall máximo (0.706->0.824)
# na grade, com W_TOPIC/W_SESSION_LABEL mantidos (empate de 6 pontos; menor
# diff das constantes vigentes escolhido no desempate).
MARGIN_TAU: float = 0.55
_EPS: float = 1e-9

# Gate de concordância (D4, spec §3) para janela-1 vinda de sinal INDIRETO
# (P3 data, P4 topic): só é confiante se o material carrega token ESPECÍFICO
# do bloco no curso — df global (nº de blocos cuja assinatura tem o token)
# <= DATE_DF_MAX. Data de POSTAGEM != aula do conteúdo (5 misses medidos no
# gold SO); janela topic-1 tem o mesmo shape (Halteproblem TCC, mascarado
# por pino manual — review final F2, finding 3).
# Calibração FASE 2 (grade 1/2/3 na régua externa SO, fase2_prova_SO.py,
# 2026-07-08): confErrado=0 nos 3 pontos; matriz (resto-err, resto-ok,
# alta-ok) = (4,7,8) em 1; (4,2,13) em 2; (4,2,13) em 3 — empate 2x3 no
# máximo de alta-ok. Mantido 2 (vigente desde a calibração D4 da FASE 1
# MF): menor diff da constante e nenhuma regressão nos dois cursos.
DATE_DF_MAX: int = 2


def _block_signature(block: dict, ctx: MotorContext, short_vocab=frozenset()) -> dict:
    """{token: peso} do bloco: session-label (1ª classe) sobrepõe topic (grosso).

    Tokens do NOME DO CURSO (ctx.course_name) saem da assinatura: são
    boilerplate local (2 confiante-errado externos na FASE 0 vinham do
    topic "introducao metodos formais" do bloco-02 — dívida do tracker)."""
    drop = _toks(ctx.course_name, short_vocab)
    sig: dict = {}
    for t in block_topic_tokens(block, short_vocab) - drop:
        sig[t] = W_TOPIC
    for t in block_session_tokens(block, ctx, short_vocab) - drop:
        sig[t] = W_SESSION_LABEL  # 1ª classe: substitui o peso grosso se colidir
    return sig


def _score(mat: set, sig: dict, m: int, df: dict) -> float:
    """IDF local (log(1+m/df)) ponderado pelo peso do token, LEN-NORMalizado."""
    if not sig:
        return 0.0
    # sorted(): mesmo defeito de concept_resolver.py:360 — soma de float sobre
    # set de str, cuja ordem de iteracao muda a cada processo. Sem isto o score
    # difere no ultimo ULP entre rodadas identicas.
    raw = sum(sig[t] * math.log(1.0 + m / df[t]) for t in sorted(mat & set(sig)))
    return raw / math.sqrt(len(sig))


def _global_df(ctx: MotorContext) -> dict:
    """df de cada token sobre as assinaturas de TODOS os blocos do curso."""
    if ctx._global_df_cache is not None:
        return ctx._global_df_cache
    df: dict = {}
    for b in ctx.blocks:
        for t in set(_block_signature(b, ctx)):
            df[t] = df.get(t, 0) + 1
    ctx._global_df_cache = df
    return df


def _gated_window1_decision(entry: dict, block: dict, ctx: MotorContext,
                            markdown: str, win: List[str]) -> AnchorDecision:
    """Janela-1 de P3/P4: alta exige concordância por token discriminante global."""
    ref = str(block.get("id") or block.get("block_uuid") or win[0])
    mat = entry_tokens(entry, markdown)
    sig = set(_block_signature(block, ctx))
    df = _global_df(ctx)
    discriminante = {t for t in (mat & sig) if df.get(t, 0) <= DATE_DF_MAX}
    if discriminante:
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)
    return AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=True,
                          method="janela-1", window=win)


# R3 "titulo-topico" (2026-08-26): o professor nomeia o arquivo pelo TOPICO da aula
# ("Logica de Hoare (parte 2)" <-> bloco "Logica de Hoare"). Se titulo+rotulo contem
# TODOS os tokens do topico de exatamente 1 bloco da janela, e escolha confiante — sem
# voto. Medido nos 5 (nu com markdown + curado): +1 (MF hoare2, que o voto punha no
# bloco vizinho), 0 regressoes, 5 votos de LLM a menos onde o lexico ja acertava.
_TOPIC_FILLER = frozenset({"introducao", "conceitos", "exercicios", "exercicio", "revisao", "aula", "parte"})


def _block_named_in_title(entry: dict, blocks: List[dict]) -> Optional[dict]:
    named = _toks(str(entry.get("title") or "") + " " + _moodle_label_text(entry))
    if not named:
        return None
    hits = []
    for b in blocks:
        topic = _toks(str(b.get("primary_topic_label") or "")) - _TOPIC_FILLER
        if topic and topic <= named:
            hits.append(b)
    return hits[0] if len(hits) == 1 else None


def disambiguate(entry: dict, window: List[str], ctx: MotorContext,
                 markdown: str = "", provider: str = "") -> AnchorDecision:
    win = list(window or [])
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if not blocks:
        return AnchorDecision(block_ref="", method="funil", window=win)
    # Fast-path janela-1 exige que a JANELA ORIGINAL tenha 1 ref, não apenas
    # os resolvíveis (comentário FASE 1 mantido). Janela-1 vinda de sinal
    # INDIRETO (data/topic) passa pelo gate de concordância D4; manual/labels
    # (verdade humana / datado) mantêm o fast-path incondicional.
    if len(win) == 1 and len(blocks) == 1:
        # "card" (Fase 3b): semana do label + ORDEM dos materiais e sinal inferido como
        # data/topic — sem token discriminante fica flagado (medido 03/09: janela-1
        # incondicional levou conf-err de 3 a 15 no motor puro; SO exemplo-criacao x4).
        if provider in ("data", "topic", "card"):
            return _gated_window1_decision(entry, blocks[0], ctx, markdown, win)
        ref = str(blocks[0].get("id") or blocks[0].get("block_uuid") or win[0])
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)

    named = _block_named_in_title(entry, blocks)
    if named is not None:
        ref = str(named.get("id") or named.get("block_uuid") or "")
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="titulo-topico", window=win)

    decision = _lexical_decision(entry, blocks, ctx, markdown, win)
    if decision.flag:
        # Fase 3c (item 5): tokens CURTOS consagrados pelo cronograma entram nos DOIS
        # lados (material e assinatura) so onde o lexico padrao ficou em duvida; adota
        # se muda o bloco ou tira a flag. Medido 02/09 (H8, so flagados): +4/-2, IA k-NN x4.
        short = course_short_vocab(ctx)
        if short:
            alt = _lexical_decision(entry, blocks, ctx, markdown, win, short)
            if alt.block_ref and (alt.block_ref != decision.block_ref or not alt.flag):
                alt.method = "disamb-curto"
                return alt
    return decision


def _lexical_decision(entry: dict, blocks: List[dict], ctx: MotorContext, markdown: str,
                      win: List[str], short_vocab=frozenset()) -> AnchorDecision:
    """Desempate lexical D4 dentro da janela (>= 2 blocos resolviveis)."""
    mat = entry_tokens(entry, markdown, short_vocab)
    sigs = [_block_signature(b, ctx, short_vocab) for b in blocks]
    m = len(blocks)
    df: dict = {}
    for sig in sigs:
        for t in sig:
            df[t] = df.get(t, 0) + 1
    scores = [_score(mat, sig, m, df) for sig in sigs]

    order = sorted(range(len(blocks)), key=lambda i: scores[i], reverse=True)
    i1 = order[0]
    s1 = scores[i1]
    s2 = scores[order[1]] if len(order) > 1 else 0.0
    rel_margin = (s1 - s2) / max(s1, _EPS)
    # D4 (spec §3), relido 2026-08-21: confiança exige >=1 token DISCRIMINANTE
    # — token do material que casa a assinatura do best e NÃO a do runner-up —
    # e, HAVENDO competição (s2>0), margem >= MARGIN_TAU. Vitória só-por-peso/
    # IDF (mesmos tokens) nunca é confiante. O `s2 > 0` obrigatório de antes
    # confundia SEM COMPETIÇÃO com SEM EVIDÊNCIA: s1>0 com s2=0 (só o best casa
    # algum token) é a evidência lexical mais exclusiva possível. Medido nos 5
    # cursos (87 janelas >= 2): nesse balde o léxico acerta 21/23 e o LLM
    # 22/23 — acurácia total igual (73/87) com 22 votos de LLM a menos.
    hits_best = mat & set(sigs[i1])
    hits_runner = mat & set(sigs[order[1]]) if len(order) > 1 else set()
    discriminante = hits_best - hits_runner
    # Janela degradada (ref fantasma: so 1 bloco resolve) nao tem runner-up —
    # s2=0 ali nao e exclusividade, e ausencia de comparacao: segue flagada.
    exclusivo = s2 <= 0 and len(blocks) >= 2
    confident = s1 > 0 and bool(discriminante) and (
        exclusivo or (s2 > 0 and rel_margin >= MARGIN_TAU))

    ref = str(blocks[i1].get("id") or blocks[i1].get("block_uuid") or win[i1])
    if confident:
        band = "alta"
    else:
        # Decisão flagada NUNCA carrega band "alta" (fecha o vazamento
        # BAND_HIGH=0.50 de confidence_band — decisão controller 2026-07-07).
        band = confidence_band(rel_margin)
        if band == "alta":
            band = "media"
    return AnchorDecision(
        block_ref=ref, conf=float(rel_margin),
        band=band, flag=not confident, method="disamb", window=win,
    )
