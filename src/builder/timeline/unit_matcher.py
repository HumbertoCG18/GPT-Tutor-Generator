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
from src.builder.text.stopwords import UNIT_MATCHER_STOPWORDS as _STOPWORDS
_UNIT_GENERIC = {"unidade", "aprendizagem", "visao", "geral"}

ANCHOR_MIN_MARGIN = 1.0   # margem minima (winner - runnerup) p/ confianca ANCHOR no bloco
STRONG_MARGIN = 3.0       # margem p/ ancora forte

CONF_STRONG = 0.8   # ancora com margem forte
CONF_ANCHOR = 0.6   # ancora normal
CONF_FILL = 0.4     # preenchido por posicao (sem sinal proprio)

# "E/S" normaliza a montante (normalize_match_text troca "/" por espaco) pra
# "e s" -- bigrama de 2 tokens de 1 char, descartado pelo filtro len>=3 abaixo.
# Sessoes de E/S ficavam com sinal zero pra unidade-07-gerencia-de-entrada-e-saida
# (caso real SO bloco-16/17: label "gerencia de e s"). Expande ANTES de tokenizar.
_ABBR_ES_RE = re.compile(r"\be\s+s\b")


def _tokens(text: str) -> set:
    """Tokens alfabeticos >=3 chars, sem acento/stopword."""
    norm = norm_ascii_lower(text or "")
    norm = _ABBR_ES_RE.sub("entrada saida", norm)
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

    # Tie-break secundario por sinal concentrado (campanha 2 U1b): empate na
    # soma -> vence o caminho com maior soma de quadrados (sinal forte num
    # bloco > migalhas espalhadas; caso real bloco-16 MF). Empate duplo
    # mantem menor indice (nao avancar atoa).
    NEG = (float("-inf"), float("-inf"))
    dp = [[NEG] * m for _ in range(n)]
    par = [[-1] * m for _ in range(n)]
    for u in range(m):
        dp[0][u] = (aff[0][u], aff[0][u] ** 2)
    for i in range(1, n):
        for u in range(m):
            best = NEG
            bu = -1
            # melhor unidade anterior pu <= u; empate (soma E soma^2) -> menor pu
            for pu in range(u + 1):
                if dp[i - 1][pu] > best:
                    best = dp[i - 1][pu]
                    bu = pu
            dp[i][u] = (aff[i][u] + best[0], aff[i][u] ** 2 + best[1])
            par[i][u] = bu

    # unidade final: maior (soma, soma^2); empate -> menor indice
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


# F5 (censo Lab SO 2026-08-28): cadeira SEM prova marca o fim de cada unidade com uma
# ENTREGA numerada ("Fechamento da parte N", Atividade=Trabalho). O digito sobrevive
# nos labels das sessoes (topic_text normalizado o perde).
_PARTE_RE = re.compile(r"\bparte\s*0*(\d{1,2})\b")


def _milestone_number(block: Mapping):
    for sess in block.get("sessions") or []:
        m = _PARTE_RE.search(norm_ascii_lower(str(sess.get("label") or "")))
        if m:
            return int(m.group(1))
    m = _PARTE_RE.search(norm_ascii_lower(str(block.get("topic_text") or "")))
    return int(m.group(1)) if m else None


def assign_units_by_work_milestones(
    runtime_blocks: Sequence[dict], class_candidates: Sequence[dict], units: Sequence[Mapping]
) -> bool:
    """F5: entregas numeradas segmentam as unidades — "parte N" fecha a unidade N.

    So se aplica quando os marcos (blocos deliverable com "parte <n>") formam
    exatamente 1..K na ordem do calendario E K == numero de unidades do plano
    (Lab SO: 4 "Fechamento da parte N" <-> 4 unidades). A numeracao explicita e
    autoridade (mesmo principio do U<n> no card, D3): bloco-aula entre o marco
    N-1 e o N pertence a unidade N. Fora dessas condicoes retorna False e o DP
    posicional decide como sempre ("parte" sem numero, SO 2026/1 com 4 partes e
    7 unidades, "Parte 1" dentro de titulo de aula do MF — nada muda)."""
    if len(units) < 2:
        return False
    marcos = []
    for i, b in enumerate(runtime_blocks):
        if str(b.get("source_kind") or "") != "deliverable" and str(b.get("kind") or "") != "deliverable":
            continue
        n = _milestone_number(b)
        if n is not None:
            marcos.append((i, n))
    if [n for _, n in marcos] != list(range(1, len(units) + 1)):
        return False
    pos_marco = [i for i, _ in marcos]
    idx_de = {id(b): i for i, b in enumerate(runtime_blocks)}
    for b in class_candidates:
        pos = idx_de.get(id(b))
        if pos is None:
            continue
        u = sum(1 for pm in pos_marco if pm < pos)  # quantos marcos ja passaram
        u = min(u, len(units) - 1)
        b["unit_slug"] = str(units[u].get("slug", "") or "")
        b["unit_confidence"] = CONF_STRONG
        if b["unit_slug"]:
            b["auto_unit_slug"] = b["unit_slug"]
    return True


def assign_units_around_pins(blocks: Sequence[dict], units: Sequence[Mapping], *, is_pinned) -> int:
    """Re-roda o DP monotonico SO nos blocos-aula sem pino de unidade. In-place.

    2026-08-25: um pino de unidade (curadoria, `block_manual_unit_slug`) e uma
    inversao LOCAL calendario-vs-plano (IA ensina ML/u05 em marco-abril, antes
    de busca/u02; ruling T9c). O DP original nao sabe dos pinos: com afinidade
    forte nos blocos pinados (aliases do glossario), a monotonicidade empurrava
    TODOS os blocos seguintes para u05 (16 entries do IA, sem gold, trocaram de
    unidade). Excluindo os pinados da cadeia, a excecao nao propaga. Sem pino
    e no-op (mesma lista, mesmo DP). Retorna quantos blocos foram re-atribuidos."""
    free = [b for b in blocks if not b.get("source_kind") and not is_pinned(b)]
    if len(free) == len([b for b in blocks if not b.get("source_kind")]):
        return 0  # sem pino: o DP ja rodou sobre esta mesma lista
    result = assign_units_positional(free, units)
    if not result:
        return 0
    n = 0
    for b, (slug, conf) in zip(free, result):
        if (b.get("unit_slug"), b.get("unit_confidence")) != (slug, conf):
            n += 1
        b["unit_slug"] = slug
        b["unit_confidence"] = conf
        if slug:
            b["auto_unit_slug"] = slug
    return n
