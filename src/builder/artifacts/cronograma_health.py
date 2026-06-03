# src/builder/artifacts/cronograma_health.py
from __future__ import annotations

from collections import defaultdict
from typing import Iterable


_NON_MATERIAL_CATEGORIES = {"cronograma", "bibliografia", "referencias"}


def _entry_block_id(entry: dict) -> str:
    manual = str(entry.get("manual_timeline_block_id") or "").strip()
    if manual:
        return manual
    for tag in entry.get("auto_tags") or []:
        t = str(tag)
        if t.startswith("bloco:"):
            return t[len("bloco:"):]
    return ""


def material_coverage(entries: Iterable[dict]) -> dict:
    """% de materiais com bloco, orfaos, por tipo. Read-only."""
    entries = [
        e for e in (entries or [])
        if str(e.get("category") or "").lower() not in _NON_MATERIAL_CATEGORIES
    ]
    total = len(entries)
    with_block = 0
    by_type: dict = defaultdict(lambda: {"total": 0, "with_block": 0})
    for e in entries:
        ftype = str(e.get("file_type") or "pdf").lower()
        by_type[ftype]["total"] += 1
        if _entry_block_id(e):
            with_block += 1
            by_type[ftype]["with_block"] += 1
    return {
        "total": total,
        "with_block": with_block,
        "orphans": total - with_block,
        "coverage": (with_block / total) if total else 0.0,
        "by_type": {k: dict(v) for k, v in by_type.items()},
    }


def _blocks_by_material_count(entries, blocks) -> dict:
    counts = {b.get("id"): 0 for b in (blocks or []) if b.get("id")}
    for e in entries or []:
        bid = _entry_block_id(e)
        if bid in counts:
            counts[bid] += 1
    return counts


def cronograma_health_md(course_meta: dict, entries: list, blocks: list) -> str:
    rep = material_coverage(entries)
    name = str((course_meta or {}).get("name") or "Curso")
    lines = [
        f"# CRONOGRAMA_HEALTH — {name}",
        "",
        f"- **Cobertura de material**: {rep['coverage']:.0%} "
        f"({rep['with_block']}/{rep['total']} com bloco)",
        f"- **Órfãos** (sem bloco): {rep['orphans']}",
        "",
        "## Por tipo",
        "",
        "| Tipo | Com bloco | Total |",
        "|---|---|---|",
    ]
    for ftype, v in sorted(rep["by_type"].items()):
        lines.append(f"| {ftype} | {v['with_block']} | {v['total']} |")

    counts = _blocks_by_material_count(entries, blocks)
    poor = [bid for bid, n in counts.items() if n == 0]
    rich = sorted(((n, bid) for bid, n in counts.items()), reverse=True)[:5]
    lines += [
        "",
        "## Blocos pobres (0 materiais)",
        "",
        (", ".join(poor) if poor else "_nenhum_"),
        "",
        "## Blocos mais ricos",
        "",
    ]
    for n, bid in rich:
        lines.append(f"- {bid}: {n} material(is)")
    return "\n".join(lines) + "\n"
