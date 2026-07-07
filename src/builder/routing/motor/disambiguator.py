"""Disambiguator: escolhe DENTRO da janela (|janela|>1) por IDF len-norm.

Reúso PURO: concept_resolver.concept_token_weights/concept_vector (bounded à
janela) — mas a tokenização/stems desta fase espelha marco0 (prova cacheada
Config A' = 59.7%) para o número bater. session-label é 1ª classe (peso acima
do topic_text agregado).

PROIBIDO importar block_token_weights/score_entry_against_timeline_block/
select_probable_period_for_entry (guard test).
"""
from __future__ import annotations

import re
from typing import List

from src.builder.text.normalize import normalize_match_text
from src.builder.routing.motor.contracts import MotorContext

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
