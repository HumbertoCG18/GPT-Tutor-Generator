"""Camada de placement por âncora (estratificada).

Resolve o bloco de destino de cada entry pela cadeia de precedência:
  1. manual_timeline_block_id -> method="manual"    (verdade humana, never overwritten)
  2. source_section semana-validated    -> method="anchor"   (cronograma-validado)
  3. computed_block_id / scorer fallback -> method="scorer"  (último recurso)

API pública:
  resolve_placement(entry, blocks, *, scorer_resolver, year) -> AnchorResult

Design:
- Puro: sem I/O; recebe entries + blocks já carregados.
- PLUGÁVEL por tipo de seção: dispatch em _anchor_resolvers por tipo.
  - "semana" implementado agora.
  - "topico" e "label" retornam None (fall-through; fases seguintes).
- NÃO wired no pipeline de produção — módulo aditivo para o canário IA.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, List, Optional

from src.builder.text.normalize import normalize_match_text

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Regex para "Semana N - DD.MM a DD.MM - Tópico" (com variantes de espaçamento)
# Cobre: "Semana 5 -30.03 a 01.04 ML - Aprendizado Supervisionado" (sem espaço)
_SEMANA_RE = re.compile(
    r"^Semana\s+(\d+)\s*-\s*(\d{1,2})\.(\d{2})\s+a\s+(\d{1,2})\.(\d{2})\s*[-–]?\s*(.*)",
    re.IGNORECASE,
)

# Tokens de seção administrativa — âncora FALHA se o tópico da seção
# é só admin (lição SO: postagem de TDE mislocate entries).
_ADMIN_TOKENS: frozenset = frozenset({
    "tde", "trabalho", "discente", "efetivo",
    "entrega", "recesso", "feriado", "atendimento",
})

# Mínimo de tokens de overlap (normalizado) para o tópico da seção
# bater o tópico do bloco/sessão (cronograma-validation).
# Após o filtro de stems genéricos, "1 overlap" significa "1 stem SIGNIFICATIVO".
_MIN_TOPIC_OVERLAP: int = 1

# Comprimento de prefixo para stemming leve ao comparar tokens de tópico.
# "supervisionado" e "supervisionada" compartilham 13 chars; 8 chars é
# suficiente para distinguir sem falsos positivos em PT.
_STEM_PREFIX: int = 8

# Stems genéricos (prefixo 8 chars) que NÃO distinguem tópicos entre blocos.
# Overlap APENAS nestes stems → conta como 0 → âncora falha → scorer.
# Justificativa: palavras como "Introdução a X" vs "introducao" partilham
# "introduc" mas não identificam o assunto concreto (IA, ML, threads, etc.).
_GENERIC_STEMS: frozenset = frozenset({
    "introduc",  # introdução / introduction
    "continua",  # continuação / continuation
    "exercici",  # exercícios / exercises
    "revisao",   # revisão / revision (sem acento: normalize_match_text remove acentos)
    "conteudo",  # conteúdo / content
    "material",  # material
    "aplicac",   # aplicação / application
    "apresent",  # apresentação / presentation
})


# ---------------------------------------------------------------------------
# Tipos de resultado
# ---------------------------------------------------------------------------

@dataclass
class AnchorResult:
    """Resultado do resolver de placement por entry."""
    block_uuid: str
    method: str              # "manual" | "anchor" | "scorer"
    section: Optional[str] = None          # seção que ancorou (se anchor)
    window_start: Optional[date] = None    # início da janela (se anchor)
    window_end: Optional[date] = None      # fim da janela (se anchor)
    changed: bool = False                  # True se diverge do computed_block_id atual


# ---------------------------------------------------------------------------
# Helpers de normalização/tokenização
# ---------------------------------------------------------------------------

def _norm_tokens(text: str) -> frozenset:
    """Tokens normalizados (>=4 chars)."""
    normalized = normalize_match_text(str(text or ""))
    return frozenset(t for t in normalized.split() if len(t) >= 4)


def _stem_tokens(tokens: frozenset) -> frozenset:
    """Prefixo de 8 chars: stemming leve para PT (supervisionado/supervisionada)."""
    return frozenset(t[:_STEM_PREFIX] for t in tokens)


def _is_admin_section_topic(section_topic: str) -> bool:
    """True se o tópico da seção é puramente administrativo (TDE/entrega/etc)."""
    tokens = _norm_tokens(section_topic)
    if not tokens:
        return True  # sem tópico = admin por omissão
    # Admin quando TODOS os tokens não-triviais são admin tokens
    non_trivial = frozenset(t for t in tokens if len(t) >= 4)
    if not non_trivial:
        return False  # palavras curtas (ex.: "ML") não são admin
    return non_trivial.issubset(_ADMIN_TOKENS)


def _parse_date_ddmm(dd: str, mm: str, year: int) -> Optional[date]:
    try:
        return date(year, int(mm), int(dd))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Parser de tipo de seção
# ---------------------------------------------------------------------------

def _detect_section_type(source_section: str) -> str:
    """Detecta o tipo da seção: 'semana' | 'topico' | 'label' | 'admin' | 'unknown'."""
    if not source_section:
        return "unknown"
    if _SEMANA_RE.match(source_section):
        return "semana"
    # Fases seguintes: topico/label (ex.: "Introdução a IA", labels Moodle)
    return "unknown"


# ---------------------------------------------------------------------------
# Resolver de âncora por tipo: SEMANA (implementado)
# ---------------------------------------------------------------------------

def _topic_overlap(section_topic: str, block: dict) -> int:
    """Conta tokens de overlap entre o tópico da seção e o tópico/sessões do bloco.

    Usa stemming leve (prefixo 8 chars) para absorver flexão PT
    (ex.: "supervisionado" == "supervisionada").
    """
    sec_tokens = _norm_tokens(section_topic)
    if not sec_tokens:
        return 0

    # Coleta tokens do bloco: topic_text + labels de sessão
    block_parts = [str(block.get("topic_text") or "")]
    for session in block.get("sessions") or []:
        block_parts.append(str(session.get("label") or ""))
    block_tokens = _norm_tokens(" ".join(block_parts))

    shared_stems = _stem_tokens(sec_tokens) & _stem_tokens(block_tokens)
    # Remove stems genéricos: só stems SIGNIFICATIVOS contam para âncora.
    meaningful_stems = shared_stems - _GENERIC_STEMS
    return len(meaningful_stems)


def _sessions_in_window(block: dict, win_start: date, win_end: date) -> bool:
    """True se o bloco tem ALGUMA sessão real dentro da janela [win_start, win_end]."""
    for session in block.get("sessions") or []:
        raw_date = str(session.get("date") or "")
        if not raw_date:
            continue
        try:
            session_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if win_start <= session_date <= win_end:
            return True
    return False


def _resolve_semana_with_meta(
    source_section: str,
    blocks: List[dict],
    year: int,
) -> tuple:
    """Igual a _resolve_semana mas também retorna (win_start, win_end, section)."""
    m = _SEMANA_RE.match(source_section)
    if not m:
        return None, None, None, None

    _week_n, dd1, mm1, dd2, mm2, section_topic = m.groups()
    section_topic = section_topic.strip()

    if _is_admin_section_topic(section_topic):
        return None, None, None, None

    win_start = _parse_date_ddmm(dd1, mm1, year)
    win_end = _parse_date_ddmm(dd2, mm2, year)

    if win_start and win_end and win_end < win_start:
        new_month = win_end.month + 1
        new_year = year
        if new_month > 12:
            new_month = 1
            new_year += 1
        last_day = calendar.monthrange(new_year, new_month)[1]
        day = min(win_end.day, last_day)
        win_end = date(new_year, new_month, day)

    if not (win_start and win_end):
        return None, None, None, None

    candidates = [
        b for b in blocks
        if _sessions_in_window(b, win_start, win_end)
    ]

    if not candidates:
        return None, None, None, None

    scored = []
    for b in candidates:
        overlap = _topic_overlap(section_topic, b)
        if overlap >= _MIN_TOPIC_OVERLAP:
            scored.append((overlap, b))

    if not scored:
        return None, None, None, None

    scored.sort(key=lambda x: x[0], reverse=True)
    winner = scored[0][1]
    uuid = str(winner.get("block_uuid") or winner.get("id") or "")
    return uuid, win_start, win_end, source_section


# ---------------------------------------------------------------------------
# Dispatcher de âncora plugável por tipo de seção
# ---------------------------------------------------------------------------

def _anchor_dispatch(
    source_section: str,
    blocks: List[dict],
    year: int,
) -> tuple:
    """Despacha pelo tipo da seção detectada.

    Retorna (block_uuid_or_None, win_start, win_end, section).
    Tipos não implementados (topico/label) retornam (None, None, None, None).
    """
    section_type = _detect_section_type(source_section)

    if section_type == "semana":
        return _resolve_semana_with_meta(source_section, blocks, year)

    # topico e label: fases seguintes — fall-through por agora
    return None, None, None, None


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def resolve_placement(
    entry: dict,
    blocks: List[dict],
    *,
    scorer_resolver: Callable[[dict, List[dict]], str],
    year: int,
) -> AnchorResult:
    """Resolve o bloco de destino de uma entry pela cadeia de precedência.

    Parâmetros:
      entry            — dict da entry (manifest).
      blocks           — lista de blocos do timeline index (com block_uuid).
      scorer_resolver  — callable(entry, blocks) -> block_uuid; fallback scorer.
      year             — ano civil para converter DD.MM em datas absolutas.

    Retorna AnchorResult com block_uuid, method e metadados de âncora.
    """
    current_uuid = str(entry.get("computed_block_id") or "").strip()

    # --- Tier 1: manual ---
    manual = str(entry.get("manual_timeline_block_id") or "").strip()
    if manual:
        # Valida que o uuid existe no ledger de blocos
        valid_uuids = {
            str(b.get("block_uuid") or b.get("id") or "")
            for b in blocks
        }
        if manual in valid_uuids:
            return AnchorResult(
                block_uuid=manual,
                method="manual",
                changed=(manual != current_uuid),
            )
        # uuid não encontrado nos blocos: cai pro scorer (integridade)
        # (este path não ocorre no canário IA com ledger íntegro)

    # --- Tier 2: anchor ---
    source_section = str(entry.get("source_section") or "").strip()
    if source_section:
        anchor_uuid, win_start, win_end, section = _anchor_dispatch(
            source_section, blocks, year
        )
        if anchor_uuid:
            return AnchorResult(
                block_uuid=anchor_uuid,
                method="anchor",
                section=section,
                window_start=win_start,
                window_end=win_end,
                changed=(anchor_uuid != current_uuid),
            )

    # --- Tier 3: scorer ---
    scorer_uuid = scorer_resolver(entry, blocks)
    return AnchorResult(
        block_uuid=scorer_uuid,
        method="scorer",
        changed=(scorer_uuid != current_uuid),
    )


# ---------------------------------------------------------------------------
# Canário IA — computação em memória (persist=False)
# ---------------------------------------------------------------------------

def compute_ia_canary(
    entries: list,
    blocks: list,
    *,
    year: int,
    scorer_resolver: Callable[[dict, List[dict]], str],
) -> list:
    """Computa o placement de cada entry do IA em memória.

    Retorna lista de dicts por entry:
      {entry_id, current_uuid, new_uuid, method, changed, section, window_start, window_end}

    NÃO persiste nada. Read-only sobre entries/blocks.
    """
    results = []
    for entry in entries:
        result = resolve_placement(entry, blocks, scorer_resolver=scorer_resolver, year=year)
        current = str(entry.get("computed_block_id") or "").strip()
        results.append({
            "entry_id": str(entry.get("id") or ""),
            "current_uuid": current,
            "new_uuid": result.block_uuid,
            "method": result.method,
            "changed": result.changed,
            "section": result.section,
            "window_start": result.window_start.isoformat() if result.window_start else None,
            "window_end": result.window_end.isoformat() if result.window_end else None,
        })
    return results
