"""Matcher posicional bloco->unidade.

Afinidade = overlap de tokens entre o conteudo do bloco (labels de sessao +
topic_text) e a unidade (titulo + labels/aliases dos topicos), com stopwords PT
e tokens curtos filtrados. Mais forte/especifico que o scorer-keyword antigo, que
casava contra o NOME da unidade (confundia "computavel"~"computabilidade").

`assign_units_positional` alinha blocos-aula (ordem cronologica) a unidades
(ordem do plano) por DP monotonico GLOBAL: maximiza a soma de afinidade sob a
restricao de indice de unidade nao-decrescente. Robusto a ancora espuria
isolada (o otimo global mantem blocos fortes na unidade certa).
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

ANCHOR_MIN_MARGIN = 1.0   # margem minima (winner - runnerup) p/ confianca ANCHOR no bloco
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


def assign_units_positional(
    class_blocks: Sequence[Mapping], units: Sequence[Mapping]
) -> List[Tuple[str, float]]:
    """(unit_slug, confidence) por bloco-aula, em ordem. [] se inaplicavel.

    Alinhamento monotonico GLOBAL (DP): atribui cada bloco-aula (ordem
    cronologica) a uma unidade (ordem do plano) de indice nao-decrescente,
    maximizando a soma de afinidade token-overlap. Robusto a ancora espuria
    isolada (o otimo global mantem blocos fortes na unidade certa). Retorna []
    se <2 unidades, sem blocos, ou nenhum sinal de afinidade em lugar nenhum
    (sinaliza fallback).
    """
    n = len(class_blocks)
    m = len(units)
    if m < 2 or n == 0:
        return []
    uslugs = [str(u.get("slug", "") or "") for u in units]
    utoks = [_unit_tokens(u) for u in units]
    aff = [[float(len(_block_tokens(b) & utoks[j])) for j in range(m)] for b in class_blocks]

    if not any(aff[i][j] > 0 for i in range(n) for j in range(m)):
        return []  # nenhum sinal -> fallback

    NEG = float("-inf")
    dp = [[NEG] * m for _ in range(n)]
    par = [[-1] * m for _ in range(n)]
    for u in range(m):
        dp[0][u] = aff[0][u]
    for i in range(1, n):
        for u in range(m):
            best = NEG
            bu = -1
            # melhor unidade anterior pu <= u; empate -> menor pu (nao avancar atoa)
            for pu in range(u + 1):
                if dp[i - 1][pu] > best:
                    best = dp[i - 1][pu]
                    bu = pu
            dp[i][u] = aff[i][u] + best
            par[i][u] = bu

    # unidade final: maior dp; empate -> menor indice (nao super-avancar)
    last = 0
    best = NEG
    for u in range(m):
        if dp[n - 1][u] > best:
            best = dp[n - 1][u]
            last = u
    assign = [0] * n
    assign[n - 1] = last
    for i in range(n - 1, 0, -1):
        assign[i - 1] = par[i][assign[i]]

    out: List[Tuple[str, float]] = []
    for i in range(n):
        u = assign[i]
        row = aff[i]
        srt = sorted(row, reverse=True)
        margin = (srt[0] - srt[1]) if len(srt) > 1 else srt[0]
        is_argmax = row[u] > 0 and row[u] >= max(row)
        if is_argmax and margin >= STRONG_MARGIN:
            conf = CONF_STRONG
        elif is_argmax and margin >= ANCHOR_MIN_MARGIN:
            conf = CONF_ANCHOR
        else:
            conf = CONF_FILL
        out.append((uslugs[u], conf))
    return out
