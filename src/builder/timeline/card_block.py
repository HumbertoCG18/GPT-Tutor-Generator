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
from src.builder.text.stopwords import CARD_BLOCK_STOP as _STOP
from src.builder.timeline.block_identity import _POSITIONAL_RE, _is_uuid_ref

_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_WEEK_RE = re.compile(r"\bsemana\s+(\d+)\b", re.IGNORECASE)


@dataclass
class CardBlockResolution:
    block_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = "needs-confirmation"


def _tokens(text: str) -> set:
    return {t for t in norm_ascii_lower(text).split() if t and t not in _STOP and len(t) > 2}


def _block_topic_tokens(block: dict) -> set:
    parts = [str(block.get("primary_topic_label") or "")]
    for t in (block.get("topics") or []):
        if isinstance(t, dict):
            parts.append(str(t.get("label") or t.get("slug") or ""))
        else:
            parts.append(str(t))
    parts += [str(a) for a in (block.get("aliases") or [])]
    return _tokens(" ".join(parts))


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
    need = min(2, len(card_tokens)) if card_tokens else 99

    # (1) data explícita no nome -> bloco que cobre a data (mês/dia).
    m = _DATE_RE.search(str(card_name or ""))
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        for b in blocks:
            if _date_in_range(month, day, str(b.get("period_start") or ""), str(b.get("period_end") or "")):
                return CardBlockResolution([str(b.get("id"))], 0.9, f"date:{day:02d}/{month:02d}")

    # (2) nome casa o TÍTULO de uma unidade -> unidade inteira (card largo intencional).
    title_scored = sorted(
        ((len(card_tokens & _tokens(str(u.get("title") or ""))), u) for u in (unit_index or [])),
        key=lambda x: x[0], reverse=True,
    )
    if title_scored:
        best_t, best_u = title_scored[0]
        tie = len(title_scored) > 1 and title_scored[1][0] == best_t and best_t > 0
        if best_t >= need and not tie:
            slug = str(best_u.get("slug"))
            ids = [str(b.get("id")) for b in blocks if str(b.get("unit_slug") or "") == slug]
            if ids:
                return CardBlockResolution(ids, min(0.95, 0.5 + 0.15 * best_t), f"unit:{slug}")

    # (3) nome casa o TÓPICO de um bloco -> bloco específico (mais fino).
    best_blocks, best_ov = [], 0
    for b in blocks:
        ov = len(card_tokens & _block_topic_tokens(b))
        if ov > best_ov:
            best_blocks, best_ov = [b], ov
        elif ov == best_ov and ov > 0:
            best_blocks.append(b)
    if best_ov >= need and best_blocks:
        ids = [str(b.get("id")) for b in best_blocks]
        return CardBlockResolution(ids, min(0.9, 0.45 + 0.15 * best_ov), "topic")

    # (4) overlap de TÓPICOS da unidade (coarse) -> unidade inteira (fallback).
    total_scored = sorted(
        ((len(card_tokens & _unit_tokens(u)), u) for u in (unit_index or [])),
        key=lambda x: x[0], reverse=True,
    )
    if total_scored:
        best_tot, best_u = total_scored[0]
        tie = len(total_scored) > 1 and total_scored[1][0] == best_tot and best_tot > 0
        if best_tot >= need and not tie:
            slug = str(best_u.get("slug"))
            ids = [str(b.get("id")) for b in blocks if str(b.get("unit_slug") or "") == slug]
            if ids:
                return CardBlockResolution(ids, min(0.9, 0.5 + 0.12 * best_tot), f"unit:{slug}")

    return CardBlockResolution([], 0.0, "needs-confirmation")


def resolve_block_ref(raw: str, index_blocks: list) -> str:
    """Recebe raw (bloco-NN, índice N, ou já-uuid) e retorna block_uuid correspondente ("" se não resolve).

    uuid passthrough: se raw já é uuid-format (não casa _POSITIONAL_RE), devolve raw.
    bloco-NN: procura em index_blocks por b["id"] == raw, retorna b["block_uuid"].
    índice nu N: idem com b["id"] == f"bloco-{int(N):02d}".
    """
    raw = str(raw or "").strip()
    if not raw:
        return ""
    # UUID passthrough: não casa positional → é uuid-format
    if _is_uuid_ref(raw):
        return raw
    # bloco-NN explícito
    if re.match(r"^bloco-\d+$", raw):
        for b in index_blocks:
            if str(b.get("id") or "") == raw:
                return str(b.get("block_uuid") or "")
        return ""
    # Índice nu (bare integer)
    if re.match(r"^\d+$", raw):
        target = f"bloco-{int(raw):02d}"
        for b in index_blocks:
            if str(b.get("id") or "") == target:
                return str(b.get("block_uuid") or "")
        return ""
    return ""


_CARD_MAP_NAME = ".card_block_map.json"


def load_card_block_map(course_dir) -> Dict[str, dict]:
    path = Path(course_dir) / _CARD_MAP_NAME
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalized_card_map(card_map) -> Dict[str, dict]:
    """Índice do card_map por chave normalizada (NFKD + sem acento + lower).

    Resolve divergência de caixa/acento entre o source_section da entry e a
    chave (nome de pasta) do .card_block_map.json — relevante para cards
    M365/legados com acentuação inconsistente. Em colisão, o último vence.
    """
    out: Dict[str, dict] = {}
    for key, value in (card_map or {}).items():
        out[norm_ascii_lower(str(key))] = value
    return out


def lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]:
    entry = _normalized_card_map(card_map).get(norm_ascii_lower(str(card_name or "")))
    if entry and "block_ids" in entry:
        raw_ids = [str(b) for b in (entry.get("block_ids") or [])]
        if not blocks:
            # fallback seguro: sem índice, retorna o raw
            return raw_ids
        # Lazy compat: resolve bloco-NN / índice-nu para uuid; uuid passthrough
        resolved = []
        for bid in raw_ids:
            r = resolve_block_ref(bid, blocks)
            if r:
                resolved.append(r)
        return resolved
    return list(resolve_card_to_block(card_name, unit_index, blocks).block_ids)


def lookup_card_assign_due(card_name, card_map) -> str:
    """Deadline ISO de entrega do card no card map ("" quando ausente).

    Gravado em import_moodle_courses via extract_assign_deadlines (S5)."""
    entry = _normalized_card_map(card_map).get(norm_ascii_lower(str(card_name or ""))) or {}
    return str(entry.get("assign_due") or "")
