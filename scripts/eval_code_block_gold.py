"""Harness read-only: mede funil e resolver contra o gold de blocos de codigo.

Uso:
    python scripts/eval_code_block_gold.py <repo_root> [gold.json]
    (default gold = tests/fixtures/eval/code_block_gold.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_resolver import compare_repo  # noqa: E402

_DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "tests/fixtures/eval/code_block_gold.json"


def score_against_gold(gold_entries: dict, rows_by_id: dict) -> dict:
    """Computa acuracia funil e resolver contra o gold; sem IO."""
    funil = {"total": 0, "correct": 0, "confident_wrong": 0}
    resolver = {"total": 0, "correct": 0, "confident_wrong": 0}
    by_conf: Dict[str, dict] = {}
    missing: List[str] = []
    per_entry: List[dict] = []

    for eid, gold in gold_entries.items():
        true_block = gold.get("true_block_id") or ""
        if not true_block:
            continue
        row = rows_by_id.get(eid)
        if row is None:
            missing.append(eid)
            continue

        conf = gold.get("confidence", "media")

        ok_f = row["funil_block"] == true_block
        ok_r = row["resolver_block"] == true_block
        cw_f = row["funil_band"] == "alta" and not ok_f
        cw_r = row["resolver_band"] == "alta" and not ok_r

        funil["total"] += 1
        funil["correct"] += int(ok_f)
        funil["confident_wrong"] += int(cw_f)
        resolver["total"] += 1
        resolver["correct"] += int(ok_r)
        resolver["confident_wrong"] += int(cw_r)

        if conf not in by_conf:
            by_conf[conf] = {"funil": {"total": 0, "correct": 0}, "resolver": {"total": 0, "correct": 0}}
        by_conf[conf]["funil"]["total"] += 1
        by_conf[conf]["funil"]["correct"] += int(ok_f)
        by_conf[conf]["resolver"]["total"] += 1
        by_conf[conf]["resolver"]["correct"] += int(ok_r)

        per_entry.append({
            "id": eid,
            "true": true_block,
            "funil_block": row["funil_block"],
            "resolver_block": row["resolver_block"],
            "funil_ok": ok_f,
            "resolver_ok": ok_r,
            "confidence": conf,
        })

    total = funil["total"]
    funil["block_accuracy"] = funil["correct"] / total if total else 0.0
    resolver["block_accuracy"] = resolver["correct"] / total if total else 0.0

    for tier in by_conf.values():
        t_f = tier["funil"]["total"]
        t_r = tier["resolver"]["total"]
        tier["funil"]["accuracy"] = tier["funil"]["correct"] / t_f if t_f else 0.0
        tier["resolver"]["accuracy"] = tier["resolver"]["correct"] / t_r if t_r else 0.0

    return {
        "funil": funil,
        "resolver": resolver,
        "by_confidence": by_conf,
        "missing": missing,
        "per_entry": per_entry,
    }


def _pct(n: int, total: int) -> str:
    return f"{n}/{total} ({100 * n // total if total else 0}%)"


def _render(result: dict) -> str:
    f = result["funil"]
    r = result["resolver"]
    total = f["total"]
    lines: List[str] = []

    lines.append("=== PLACAR: funil vs resolver vs gold ===")
    lines.append(
        f"funil:    acc {_pct(f['correct'], total)}, confiante-errado {f['confident_wrong']}"
    )
    lines.append(
        f"resolver: acc {_pct(r['correct'], total)}, confiante-errado {r['confident_wrong']}"
    )
    lines.append("")

    by_conf = result["by_confidence"]
    for tier in ("alta", "media"):
        if tier not in by_conf:
            continue
        tf = by_conf[tier]["funil"]
        tr = by_conf[tier]["resolver"]
        lines.append(
            f"subset confidence={tier}:  funil {_pct(tf['correct'], tf['total'])}  "
            f"resolver {_pct(tr['correct'], tr['total'])}"
        )
    lines.append("")

    lines.append(f"{'id':<30} {'true':<12} {'funil':>6} {'res':>5} {'conf':<6}")
    lines.append("-" * 62)
    for e in sorted(result["per_entry"], key=lambda x: x["id"]):
        lines.append(
            f"{e['id']:<30} {e['true']:<12} "
            f"{'OK' if e['funil_ok'] else e['funil_block']:>6} "
            f"{'OK' if e['resolver_ok'] else e['resolver_block']:>5} "
            f"{e['confidence']:<6}"
        )

    missing = result["missing"]
    if missing:
        lines.append("")
        lines.append(f"missing (no gold, sem row): {', '.join(missing)}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    repo_root = Path(argv[1]) if len(argv) > 1 else None
    if repo_root is None:
        print("Uso: python scripts/eval_code_block_gold.py <repo_root> [gold.json]")
        return 1
    gold_path = Path(argv[2]) if len(argv) > 2 else _DEFAULT_GOLD
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    result = compare_repo(repo_root)
    if result is None or result.get("error"):
        print(f"ERRO ao carregar repo: {result}")
        return 1
    rows_by_id = {r["id"]: r for r in result["rows"]}
    scored = score_against_gold(gold["entries"], rows_by_id)
    print(_render(scored))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
