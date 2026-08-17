"""WindowProvider: cascata de providers por CONFIABILIDADE (P1 manual > P2 labels).

FASE 0: só P1/P2 (card_block_map). P3 (data-no-nome) e P4 (tópico) = FASE 2.
Retorna janela como lista de refs DISPLAY (bloco-NN). [] = sem janela = funil.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from src.utils.helpers import norm_ascii_lower
from src.builder.timeline.card_block import normalized_card_map
from src.builder.text.normalize import normalize_match_text
from src.builder.routing.motor.disambiguator import block_topic_tokens, block_session_tokens, _GENERIC_STEMS
from src.builder.timeline.classifier import STRONG_EXAM_RE as _STRONG_EXAM_RE
from src.builder.timeline.classifier import WEAK_EXAM_TOKENS as _TOPIC_EXAM_STEMS

from src.builder.routing.motor.contracts import MotorContext


def _card_entry(entry: dict, ctx: MotorContext) -> dict:
    """Entrada do card_block_map para a source_section da entry (match sem
    acento/caixa via card_block.normalized_card_map — helper ÚNICO; em
    colisão, o último vence)."""
    key = norm_ascii_lower(str(entry.get("source_section") or ""))
    if not key:
        return {}
    # Card malformado (não-dict) degrada para janela vazia, não crashes.
    if ctx._ncm_cache is None:
        ctx._ncm_cache = normalized_card_map(ctx.card_block_map)
    info = ctx._ncm_cache.get(key)
    return info if isinstance(info, dict) else {}


def _window_for_source(entry: dict, ctx: MotorContext, source: str) -> List[str]:
    info = _card_entry(entry, ctx)
    if str(info.get("source") or "") != source:
        return []
    return [str(b) for b in (info.get("block_ids") or []) if str(b)]


def provider_manual(entry: dict, ctx: MotorContext) -> List[str]:
    """P1 — card-window MANUAL (verdade humana)."""
    return _window_for_source(entry, ctx, "manual")


def provider_labels(entry: dict, ctx: MotorContext) -> List[str]:
    """P2 — card_block_map LABELS datado (parse_card_dates A-D)."""
    return _window_for_source(entry, ctx, "labels")


def _modal_years(ctx: MotorContext) -> List[str]:
    """Anos das sessions, mais frequente primeiro (curso pode virar o ano)."""
    if ctx._modal_years_cache is not None:
        return ctx._modal_years_cache
    counts: dict = {}
    for b in ctx.blocks:
        for s in b.get("sessions") or []:
            y = str(s.get("date") or "")[:4]
            if y.isdigit():
                counts[y] = counts.get(y, 0) + 1
    years = sorted(counts, key=lambda y: counts[y], reverse=True)
    ctx._modal_years_cache = years
    return years


def provider_date(entry: dict, ctx: MotorContext) -> List[str]:
    """P3 — DATA-no-nome (DD.MM) -> sessão do cronograma -> bloco (janela ~1).

    0 colisão medida no corpus SO; se uma data cair em 2 blocos a janela
    carrega ambos (honesto — o disambiguator decide)."""
    dm = extract_date_in_name(entry)
    if not dm:
        return []
    dd, mm = dm
    for year in _modal_years(ctx):
        iso = f"{year}-{mm:02d}-{dd:02d}"
        refs = [
            str(b.get("id") or "")
            for b in ctx.blocks
            if any(str(s.get("date") or "") == iso for s in b.get("sessions") or [])
        ]
        refs = [r for r in refs if r]
        if refs:
            return refs
    return []


# P4 — topic-bridge (spec §3 [Δ item 9]; F-TCC: o N ordinal NUNCA vira janela).
_SEMANA_TOPIC_RE = re.compile(r"^\s*semana\s*\d+\s*-\s*(.+)$", re.IGNORECASE)
TOPIC_STEM_LEN: int = 6
TOPIC_MIN_TOKEN: int = 3


def _topic_tokens(topic: str) -> set:
    """Tokens do TÓPICO curado do card: >=3 chars, sem genéricos.

    Piso 2 seria no-op: a assinatura do bloco (_toks) tem piso 3 — token
    curto do tópico nunca casa. Se a calibração TCC pedir np/t2, o piso-2
    exige assinatura própria do P4 nos DOIS lados (decisão por número)."""
    out = set()
    for t in normalize_match_text(str(topic or "")).split():
        if len(t) >= TOPIC_MIN_TOKEN and not t.isdigit() and t[:8] not in _GENERIC_STEMS:
            out.add(t)
    return out


def _stems(tokens: set) -> set:
    return {t[:TOPIC_STEM_LEN] for t in tokens}


# Exam-vocab fraco (par do ruling C1): sozinho não indica EXAME, só quando o
# bloco tem sinal FORTE (STRONG_EXAM_RE) em algum outro lugar do próprio bloco.
# Item 8b (cutover passo 3): vocabulario UNIFICADO no classifier (nomes
# publicos STRONG_EXAM_RE/WEAK_EXAM_TOKENS, importados no topo) — os aliases
# locais _STRONG_EXAM_RE/_TOPIC_EXAM_STEMS preservam o vocabulario deste modulo.


def _block_session_hay(b: dict, ctx: MotorContext) -> str:
    """Texto CRU das sessões do bloco (labels + lessons_index) — a MESMA
    fonte de block_session_tokens (disambiguator.py:63-71), só que não
    tokenizado: _STRONG_EXAM_RE precisa ver "p1"/"p2" etc. inteiros, que o
    piso de 3 chars de _toks descartaria."""
    parts = []
    for sess in b.get("sessions") or []:
        parts.append(str(sess.get("label") or ""))
        topic = ctx.lessons_index.get(str(sess.get("date") or ""))
        if topic:
            parts.append(str(topic))
    return " ".join(parts)


def _block_topic_stems(ctx: MotorContext) -> dict:
    """id(block) -> _stems(assinatura) de TODOS os blocos, memoizado por ctx (item 16).

    Assinatura por bloco e invariante por indice; mesmo padrao de
    ctx._global_df_cache (disambiguator.py:123-132).

    Guard C6 (diagnóstico 2026-08-06, re-flip TCC tentativa 4): rótulo de
    taxonomia rica do bloco (primary_topic_label, ex. "Prova da
    Indecidibilidade...") vaza "prova"/"teste" pro stem-matching do P4 via
    block_topic_tokens mesmo quando o bloco é uma AULA, não um exame. O
    ruling C1 (mesmo par prova/teste) só libera esses tokens do lado TOPIC
    quando o bloco tem sinal FORTE de exame (_STRONG_EXAM_RE) no seu próprio
    texto de sessões; o lado SESSION (block_session_tokens) nunca é
    filtrado — é dele que vêm os 8 membros legítimos da janela real."""
    if ctx._stems_cache is not None:
        return ctx._stems_cache
    cache: dict = {}
    for b in ctx.blocks:
        topic_toks = block_topic_tokens(b)
        if topic_toks & _TOPIC_EXAM_STEMS and not _STRONG_EXAM_RE.search(_block_session_hay(b, ctx)):
            topic_toks = topic_toks - _TOPIC_EXAM_STEMS
        sig = topic_toks | block_session_tokens(b, ctx)
        cache[id(b)] = _stems(sig)
    ctx._stems_cache = cache
    return cache


def provider_topic(entry: dict, ctx: MotorContext) -> List[str]:
    """P4 — TÓPICO do card "Semana N - Tópico" ↔ topic_text/sessions[].label."""
    m = _SEMANA_TOPIC_RE.match(str(entry.get("source_section") or ""))
    if not m:
        return []
    tstems = _stems(_topic_tokens(m.group(1)))
    if not tstems:
        return []  # card só-ordinal: week-math PROIBIDO -> sem janela
    stems_by_block = _block_topic_stems(ctx)
    refs = []
    for b in ctx.blocks:
        if tstems & stems_by_block.get(id(b), set()):
            ref = str(b.get("id") or "")
            if ref:
                refs.append(ref)
    return refs


# Cascata em ordem de CONFIABILIDADE. Cada par (fn, nome).
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
    (provider_date, "data"),
    (provider_topic, "topic"),
)


def resolve_window(entry: dict, ctx: MotorContext) -> Tuple[List[str], str]:
    """1º provider com janela não-vazia -> (janela, nome_provider). ([], "") = funil."""
    for fn, name in _CASCADE:
        win = fn(entry, ctx)
        if win:
            return win, name
    return [], ""


# P3 — data-no-nome (spec §8: extrator DD.MM de title/moodle_label/source_path).
# Reimplementado PURO: o sinal DD.MM legado vive em símbolo condenado do cutover.
_DATE_PREFIX_RE = re.compile(r"^\s*(\d{1,2})[. ](\d{1,2})\b")


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def extract_date_in_name(entry: dict):
    """(dd, mm) do PREFIXO de title/moodle_label/basename(source_path); None se ausente."""
    basename = re.split(r"[\\/]", str(entry.get("source_path") or ""))[-1]
    for text in (str(entry.get("title") or ""), _moodle_label_text(entry), basename):
        m = _DATE_PREFIX_RE.match(text)
        if not m:
            continue
        dd, mm = int(m.group(1)), int(m.group(2))
        if 1 <= dd <= 31 and 1 <= mm <= 12:
            return dd, mm
    return None
