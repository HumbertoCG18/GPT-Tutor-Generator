"""Resolve um card (subpasta do stash) a um ou mais blocos do cronograma.

Fonte autoritativa do gabarito-cards: o card (seção do Moodle) é mapeado por
NOME a uma unidade (→ blocos dela) ou por DATA/semana a um bloco específico.
Puro: sem I/O além do load/save do mapa persistido.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from src.utils.helpers import norm_ascii_lower

_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_WEEK_RE = re.compile(r"\bsemana\s+(\d+)\b", re.IGNORECASE)
_STOP = {"de", "da", "do", "e", "a", "o", "para", "por", "em", "the", "of"}


@dataclass
class CardBlockResolution:
    block_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = "needs-confirmation"


def _tokens(text: str) -> set:
    return {t for t in norm_ascii_lower(text).split() if t and t not in _STOP and len(t) > 2}


def _unit_tokens(unit: dict) -> set:
    parts = [str(unit.get("title") or "")]
    parts += [str(x) for x in (unit.get("topics") or [])]
    parts += [str(x) for x in (unit.get("topic_phrases") or [])]
    parts += [str(x) for x in (unit.get("distinctive_tokens") or [])]
    return _tokens(" ".join(parts))


def _date_in_range(month: int, day: int, start_iso: str, end_iso: str) -> bool:
    def md(iso: str):
        parts = iso.split("-")
        return (int(parts[1]), int(parts[2])) if len(parts) == 3 else None
    s, e = md(start_iso), md(end_iso)
    if not s or not e:
        return False
    return s <= (month, day) <= e


def resolve_card_to_block(card_name, unit_index, blocks) -> CardBlockResolution:
    card_tokens = _tokens(str(card_name or ""))

    # (2) data explícita no nome -> bloco que cobre a data (mês/dia).
    m = _DATE_RE.search(str(card_name or ""))
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        for b in blocks:
            start, end = str(b.get("period_start") or ""), str(b.get("period_end") or "")
            if _date_in_range(month, day, start, end):
                return CardBlockResolution([str(b.get("id"))], 0.9, f"date:{day:02d}/{month:02d}")

    # (1) nome -> unidade por overlap de tokens.
    best_unit, best_overlap = None, 0
    for unit in unit_index or []:
        overlap = len(card_tokens & _unit_tokens(unit))
        if overlap > best_overlap:
            best_unit, best_overlap = unit, overlap
    if best_unit is not None and best_overlap >= 2:
        slug = str(best_unit.get("slug"))
        ids = [str(b.get("id")) for b in blocks if str(b.get("unit_slug") or "") == slug]
        if ids:
            conf = min(0.95, 0.5 + 0.15 * best_overlap)
            return CardBlockResolution(ids, conf, f"unit:{slug}")

    return CardBlockResolution([], 0.0, "needs-confirmation")
