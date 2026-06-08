"""Resolve um card (subpasta do stash) a um ou mais blocos do cronograma.

Fonte autoritativa do gabarito-cards: o card (seção do Moodle) é mapeado por
NOME a uma unidade (→ blocos dela) ou por DATA/semana a um bloco específico.
Puro: sem I/O além do load/save do mapa persistido.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
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

    # (1) nome -> unidade por overlap de tokens (empate -> needs-confirmation).
    scored = sorted(
        ((len(card_tokens & _unit_tokens(u)), u) for u in (unit_index or [])),
        key=lambda x: x[0], reverse=True,
    )
    if scored:
        best_overlap, best_unit = scored[0]
        tie = len(scored) > 1 and scored[1][0] == best_overlap and best_overlap > 0
        need = min(2, len(card_tokens)) if card_tokens else 99
        if best_overlap >= need and not tie:
            slug = str(best_unit.get("slug"))
            ids = [str(b.get("id")) for b in blocks if str(b.get("unit_slug") or "") == slug]
            if ids:
                conf = min(0.95, 0.5 + 0.15 * best_overlap)
                return CardBlockResolution(ids, conf, f"unit:{slug}")

    return CardBlockResolution([], 0.0, "needs-confirmation")


_CARD_MAP_NAME = ".card_block_map.json"


def load_card_block_map(course_dir) -> Dict[str, dict]:
    path = Path(course_dir) / _CARD_MAP_NAME
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_card_block_map(course_dir, mapping) -> None:
    course = Path(course_dir)
    course.mkdir(parents=True, exist_ok=True)
    (course / _CARD_MAP_NAME).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]:
    entry = (card_map or {}).get(str(card_name or ""))
    if entry and "block_ids" in entry:
        return [str(b) for b in (entry.get("block_ids") or [])]
    return list(resolve_card_to_block(card_name, unit_index, blocks).block_ids)
