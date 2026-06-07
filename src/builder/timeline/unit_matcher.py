"""Matcher posicional bloco->unidade.

Afinidade = overlap de tokens entre o conteudo do bloco (labels de sessao +
topic_text) e a unidade (titulo + labels/aliases dos topicos), com stopwords PT
e tokens curtos filtrados. Mais forte/especifico que o scorer-keyword antigo, que
casava contra o NOME da unidade (confundia "computavel"~"computabilidade").

`assign_units_positional` alinha blocos-aula (ordem cronologica) a unidades
(ordem do plano) por anchor-fill monotonico: ancoras (vencedor com margem)
progridem nao-decrescente; ancora fraca fora de ordem e rebaixada; blocos sem
sinal herdam a unidade da ancora anterior.
"""

from __future__ import annotations

import re
from typing import List, Mapping, Sequence, Tuple

from src.utils.helpers import norm_ascii_lower

# Stopwords PT + tokens genericos que nao discriminam unidade/topico.
_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "para", "com",
    "em", "no", "na", "nos", "nas", "ao", "aos", "um", "uma", "sobre", "que",
    "introducao", "aula", "parte", "modulo",
}
_UNIT_GENERIC = {"unidade", "aprendizagem", "visao", "geral"}

ANCHOR_MIN_MARGIN = 1.0   # margem minima (winner - runnerup) p/ virar ancora
STRONG_MARGIN = 3.0       # margem p/ ancora forte

CONF_STRONG = 0.8   # ancora com margem forte
CONF_ANCHOR = 0.6   # ancora normal
CONF_FILL = 0.4     # preenchido por posicao (sem sinal proprio)


def _tokens(text: str) -> set:
    """Tokens alfabeticos >=3 chars, sem acento/stopword."""
    norm = norm_ascii_lower(text or "")
    return {t for t in re.findall(r"[a-z]+", norm) if len(t) >= 3 and t not in _STOPWORDS}


def _block_tokens(block: Mapping) -> set:
    parts = [str(s.get("label", "")) for s in (block.get("sessions") or []) if isinstance(s, Mapping)]
    parts.append(str(block.get("topic_text", "") or ""))
    return _tokens(" ".join(parts))


def _unit_tokens(unit: Mapping) -> set:
    parts = [str(unit.get("title", "") or "")]
    for t in unit.get("topics", []) or []:
        if isinstance(t, Mapping):
            parts.append(str(t.get("label", "") or ""))
            parts.extend(str(a) for a in (t.get("aliases") or []))
    return _tokens(" ".join(parts)) - _UNIT_GENERIC


def score_block_unit_affinity(block: Mapping, unit: Mapping) -> float:
    """Overlap de tokens entre bloco e unidade (0.0 se nenhum)."""
    return float(len(_block_tokens(block) & _unit_tokens(unit)))


def assign_units_positional(
    class_blocks: Sequence[Mapping], units: Sequence[Mapping]
) -> List[Tuple[str, float]]:
    """(unit_slug, confidence) por bloco-aula, em ordem. [] se inaplicavel.

    Inaplicavel: <2 unidades, sem blocos, ou nenhuma ancora (sinaliza fallback).
    """
    if len(units) < 2 or not class_blocks:
        return []
    uslugs = [str(u.get("slug", "") or "") for u in units]
    utoks = [_unit_tokens(u) for u in units]

    anchors: List[Tuple[int, int, float]] = []  # (block_idx, unit_idx, margin)
    for i, b in enumerate(class_blocks):
        bt = _block_tokens(b)
        aff = [float(len(bt & ut)) for ut in utoks]
        order = sorted(range(len(units)), key=lambda j: aff[j], reverse=True)
        win = order[0]
        ws = aff[win]
        rs = aff[order[1]] if len(order) > 1 else 0.0
        if ws > 0 and (ws - rs) >= ANCHOR_MIN_MARGIN:
            anchors.append((i, win, ws - rs))

    if not anchors:
        return []

    kept: List[Tuple[int, int]] = []
    strong: set = set()
    cur = -1
    for (i, u, m) in anchors:
        if u >= cur:
            kept.append((i, u)); cur = u
            if m >= STRONG_MARGIN:
                strong.add(i)
        # fora de ordem -> rebaixa (segue a sequencia; correcao via override manual)
    if not kept:
        return []

    anchor_idx = {i for (i, _) in kept}
    assign: List[int] = [-1] * len(class_blocks)
    for (i, u) in kept:
        assign[i] = u
    cur_u = 0
    for i in range(len(class_blocks)):
        if assign[i] >= 0:
            cur_u = assign[i]
        else:
            assign[i] = cur_u

    out: List[Tuple[str, float]] = []
    for i in range(len(class_blocks)):
        if i in strong:
            conf = CONF_STRONG
        elif i in anchor_idx:
            conf = CONF_ANCHOR
        else:
            conf = CONF_FILL
        out.append((uslugs[assign[i]], conf))
    return out
