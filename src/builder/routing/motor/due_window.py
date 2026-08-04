"""TIER 2 janela-de-prazo: due-date por-assignment -> bloco da entrega.

Spec: 2026-07-22-janela-de-prazo-tier2-design.md + adendo F5b 2026-08-03.
Matching: posicional (file_dues por filename, D-G) com fallback stem (D-C).
Janela (D-H/D-I): só bloco DE CONTEÚDO (topics não-vazio) ancora — containment
-> band pela fonte; senão último bloco de conteúdo anterior -> media+FLAG.
Nunca chuta: sem due casado -> None -> funil. NUNCA disambiguator, NUNCA voto LLM.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.utils.helpers import norm_ascii_lower

_TDE_PREFIX = "TDE"
_STEM_RE = re.compile(r"\bt(\d+)\b")
_CONF_ALTA, _CONF_MEDIA = 0.95, 0.75


def tier2_due_scope(entry: dict) -> bool:
    """Categorias que TENTAM o provider (gated em casar due; senão funil)."""
    cat = str(entry.get("category") or "").strip().lower()
    if cat in ("trabalhos", "provas"):
        return True
    sec = str(entry.get("source_section") or "").strip()
    return cat.startswith("codigo") and sec.startswith(_TDE_PREFIX)


def _card_entry(entry: dict, ctx: MotorContext) -> Optional[dict]:
    sec = str(entry.get("source_section") or "").strip()
    if not sec:
        return None
    cm = ctx.card_block_map or {}
    hit = cm.get(sec)
    if isinstance(hit, dict):
        return hit
    want = norm_ascii_lower(sec)
    for k, v in cm.items():
        if isinstance(v, dict) and norm_ascii_lower(str(k)) == want:
            return v
    return None


def _stems(text: str) -> set:
    return set(_STEM_RE.findall(norm_ascii_lower(text)))


def _match_due(entry: dict, ctx: MotorContext) -> Optional[dict]:
    """UM {name, due, source}: posicional (file_dues, D-G) > stem (D-C) > None."""
    card = _card_entry(entry, ctx)
    if card is None:
        return None
    base = Path(str(entry.get("source_path") or "")).name.casefold()
    hit = (card.get("file_dues") or {}).get(base) if base else None
    if isinstance(hit, dict) and str(hit.get("due") or ""):
        return {"name": base, "due": str(hit.get("due")),
                "source": str(hit.get("source") or "")}
    dues = [d for d in (card.get("assign_dues") or [])
            if isinstance(d, dict) and str(d.get("due") or "")]
    if not dues:
        return None
    if len(dues) == 1:
        mine = _stems(f"{entry.get('title') or ''} {entry.get('id') or ''}")
        theirs = _stems(str(dues[0].get("name") or ""))
        if mine and theirs and not (mine & theirs):
            return None  # stem-conflito: extracao parcial nao pode virar chute
        return dues[0]
    mine = _stems(f"{entry.get('title') or ''} {entry.get('id') or ''}")
    if not mine:
        return None
    hits = [d for d in dues if _stems(str(d.get("name") or "")) & mine]
    return hits[0] if len(hits) == 1 else None


def resolve_due_window(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]:
    m = _match_due(entry, ctx)
    if not m:
        return None
    due = str(m.get("due") or "")
    contain = prev = None
    for b in ctx.blocks:  # ordenados por period_start (contrato do MotorContext)
        if not (b.get("topics") or []):
            continue  # D-H: só bloco DE CONTEÚDO ancora entrega (admin/prova fora)
        start = str(b.get("period_start") or "")
        end = str(b.get("period_end") or "") or start
        if not start:
            continue
        if start <= due <= end:
            contain = b
            break
        if end < due:
            prev = b  # último bloco inteiramente antes do due
    if contain is not None:
        band = "alta" if str(m.get("source") or "") == "structured" else "media"
        return AnchorDecision(
            block_ref=str(contain.get("id") or ""), conf=_CONF_ALTA if band == "alta" else _CONF_MEDIA,
            band=band, flag=False, provider="due-window", method="due-contain",
            window=[str(contain.get("id") or "")])
    if prev is None:
        return None  # due antes do primeiro bloco: sem âncora honesta -> funil
    return AnchorDecision(
        block_ref=str(prev.get("id") or ""), conf=_CONF_MEDIA, band="media",
        flag=True, provider="due-window", method="due-straddle",
        window=[str(prev.get("id") or "")])
