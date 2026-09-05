#!/usr/bin/env python3
"""Migra os gold CSVs para block_uuid (decisão user 08/07): adiciona coluna
true_block_uuid resolvendo o display true_block_id no ledger do repo-tutor.

READ-ONLY nos repos-tutor; escreve SÓ nos CSVs de docs/reports/ deste repo.
Display fica (humano lê); uuid vira a referência estável (drift posicional
pós-reprocess não invalida mais o gold).

Uso: python scripts/migrate_gold_uuid.py [--es2 PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.routing.motor.context import build_motor_context  # noqa: E402

GH = Path.home() / "Documents" / "GitHub"
REPOS = {
    "MF": GH / "Metodos-Formais-Tutor",
    "IA": GH / "Inteligencia-Artifical-Tutor",
    "SO": GH / "Sistemas-Operacionais-Tutor",
    "TCC": GH / "TCC-Tutor",
    "ES2": None,  # sem default conhecido: --es2 obrigatório p/ migrar ES2
}


def migrate(course: str, repo: Path, dry: bool) -> tuple:
    gold = ROOT / "docs" / "reports" / f"ground_truth_{course}.csv"
    if not gold.is_file():
        return (0, 0, f"sem CSV: {gold.name}")
    ctx = build_motor_context(repo)
    if not ctx.blocks:
        return (0, 0, f"repo sem timeline: {repo}")
    with open(gold, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "true_block_uuid" not in fields:
        fields.append("true_block_uuid")
    ok = miss = 0
    for r in rows:
        display = str(r.get("true_block_id") or "").strip()
        b = ctx.block_by_ref(display) if display else None
        if b is not None and b.get("block_uuid"):
            r["true_block_uuid"] = str(b["block_uuid"])
            ok += 1
        else:
            r.setdefault("true_block_uuid", "")
            if display:
                miss += 1
    if not dry:
        with open(gold, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return (ok, miss, "ok" if not dry else "dry-run")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--es2", default=None, help="path do repo ES2-Tutor")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.es2:
        REPOS["ES2"] = Path(args.es2)
    failures = 0
    for course, repo in REPOS.items():
        if repo is None or not Path(repo).is_dir():
            print(f"  {course}: PULADO (repo ausente — passe --es2/clone)")
            continue
        ok, miss, status = migrate(course, Path(repo), args.dry_run)
        print(f"  {course}: {ok} uuid resolvidos, {miss} sem match [{status}]")
        if miss:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
