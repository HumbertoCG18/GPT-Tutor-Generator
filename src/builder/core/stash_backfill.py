"""Backfill de source_section em entries já processados (manifest existente).

Casa por basename: o source_path do stash difere do original no manifest, então
o nome do arquivo é a ponte. Basename que aparece em >1 card é ambíguo (não
atribui — vai pra confirmação manual).
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from src.builder.core.stash_import import StashScanResult


def match_entries_to_cards(manifest_entries, scan: StashScanResult) -> Tuple[Dict[str, str], List[str], List[str]]:
    by_basename: Dict[str, set] = {}
    for item in scan.items:
        by_basename.setdefault(Path(item.source_path).name, set()).add(item.card_name)
    counts = Counter({name: len(cards) for name, cards in by_basename.items()})

    assignments: Dict[str, str] = {}
    unmatched: List[str] = []
    ambiguous: List[str] = []
    for entry in manifest_entries or []:
        eid = str(entry.get("id") or "")
        base = Path(str(entry.get("source_path") or "")).name
        if base not in by_basename:
            unmatched.append(eid or base)
            continue
        if counts[base] > 1:
            ambiguous.append(eid or base)
            continue
        assignments[eid or base] = next(iter(by_basename[base]))
    return assignments, unmatched, ambiguous
