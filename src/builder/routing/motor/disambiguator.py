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
from typing import List

from src.builder.text.normalize import normalize_match_text
from src.builder.routing.motor.contracts import MotorContext, AnchorDecision
from src.builder.routing.thresholds import confidence_band

# Espelha marco0._GEN: stems (prefixo 8) que NÃO discriminam bloco.
_GENERIC_STEMS = frozenset({
    "introduc", "continua", "exercici", "revisao", "conteudo", "material",
    "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula",
    "para", "resposta", "solucao", "lista",
})


def _toks(text: str) -> set:
    """Tokens normalizados >=3 chars, sem dígitos-puros nem stems genéricos.

    Quebra camelCase ANTES do fold (LogicaDeHoare -> logica de hoare)."""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(text or ""))
    out: set = set()
    for t in normalize_match_text(text).split():
        if len(t) >= 3 and not t.isdigit() and t[:8] not in _GENERIC_STEMS:
            out.add(t)
    return out


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def entry_tokens(entry: dict, markdown: str = "") -> set:
    """Sinal LIMPO do material: título + moodle_label + markdown (capado fora)."""
    parts = [str(entry.get("title") or ""), _moodle_label_text(entry), str(markdown or "")]
    return _toks(" ".join(p for p in parts if p))


def block_topic_tokens(block: dict) -> set:
    """Assinatura GROSSA do bloco: topic_text + primary_topic_label."""
    return _toks(
        str(block.get("topic_text") or "") + " " + str(block.get("primary_topic_label") or "")
    )


def block_session_tokens(block: dict, ctx: MotorContext) -> set:
    """Assinatura FINA (1ª classe): sessions[].label + roteiro do dia (lessons_index)."""
    out: set = set()
    for sess in block.get("sessions") or []:
        out |= _toks(str(sess.get("label") or ""))
        topic = ctx.lessons_index.get(str(sess.get("date") or ""))
        if topic:
            out |= _toks(str(topic))
    return out


# Pesos da fusão (calibração TDD — spec §12). session-label (fino) > topic (grosso).
W_SESSION_LABEL: float = 1.0
W_TOPIC: float = 0.6
# Gate D4 proxy (MARCO 0): margem relativa mínima p/ band "alta". Calibrado no
# gold MF embutido (decisão controller 2026-07-07): 0.45 supera o 0.441 do case
# 'intro' -> confiante-errado=0. Calibração fina COM RECALL = FASE 1.
MARGIN_TAU: float = 0.45
_EPS: float = 1e-9


def _block_signature(block: dict, ctx: MotorContext) -> dict:
    """{token: peso} do bloco: session-label (1ª classe) sobrepõe topic (grosso).

    Tokens do NOME DO CURSO (ctx.course_name) saem da assinatura: são
    boilerplate local (2 confiante-errado externos na FASE 0 vinham do
    topic "introducao metodos formais" do bloco-02 — dívida do tracker)."""
    drop = _toks(ctx.course_name)
    sig: dict = {}
    for t in block_topic_tokens(block) - drop:
        sig[t] = W_TOPIC
    for t in block_session_tokens(block, ctx) - drop:
        sig[t] = W_SESSION_LABEL  # 1ª classe: substitui o peso grosso se colidir
    return sig


def _score(mat: set, sig: dict, m: int, df: dict) -> float:
    """IDF local (log(1+m/df)) ponderado pelo peso do token, LEN-NORMalizado."""
    if not sig:
        return 0.0
    raw = sum(sig[t] * math.log(1.0 + m / df[t]) for t in (mat & set(sig)))
    return raw / math.sqrt(len(sig))


def disambiguate(entry: dict, window: List[str], ctx: MotorContext, markdown: str = "") -> AnchorDecision:
    win = list(window or [])
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if not blocks:
        return AnchorDecision(block_ref="", method="funil", window=win)
    # Fast-path janela-1 exige que a JANELA ORIGINAL tenha 1 ref, não apenas
    # os resolvíveis: ref obsoleto no card_block_map (drift) não pode virar
    # confiança "alta"/1.0 sem evidência de token — cai no scoring normal,
    # onde 1 bloco resolvível => s2=0 => flagado/media (honesto).
    if len(win) == 1 and len(blocks) == 1:
        ref = str(blocks[0].get("id") or blocks[0].get("block_uuid") or win[0])
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)

    mat = entry_tokens(entry, markdown)
    sigs = [_block_signature(b, ctx) for b in blocks]
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
    # Confiança exige COMPETIÇÃO real (s2>0): runner-up zerado = sem evidência
    # de disputa, nunca confiante (mata rel_margin=1.0 degenerado no gold MF —
    # decisão controller 2026-07-07).
    confident = s1 > 0 and s2 > 0 and rel_margin >= MARGIN_TAU

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
