"""Regua de unidade: gold block_uuid->true_unit vs indice EM DISCO (producao).
Uso: python scripts/eval_units.py [--course MF] [--baseline caminho.json]
Gold: tests/fixtures/eval/gold_units_<CURSO>.csv (keyed block_uuid — NUNCA
bloco-NN posicional; licao do drift do gold MF, tracker 2026-07-08)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.core import SubjectStore  # noqa: E402

GOLD_DIR = ROOT / "tests" / "fixtures" / "eval"

# curso = sigla derivada do nome do repo-tutor (basename sem sufixo "-Tutor").
REPO_SIGLA = {
    "Metodos-Formais": "MF",
    "Sistemas-Operacionais": "SO",
    "Engenharia-Software-2": "ES2",
    "Inteligencia-Artifical": "IA",  # typo do repo real, mantido de proposito
    "TCC": "TCC",
}


def score_course(gold_csv, index) -> dict:
    by_uuid = {b.get("block_uuid"): b for b in index.get("blocks", [])}
    ok, total, mismatches = 0, 0, []
    with open(gold_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            true = (row.get("true_unit") or "").strip()
            if not true:
                continue
            total += 1
            blk = by_uuid.get((row.get("block_uuid") or "").strip()) or {}
            got = str(blk.get("unit_slug") or "")
            if got == true:
                ok += 1
            else:
                mismatches.append({"block_uuid": row.get("block_uuid"),
                                   "block_id": row.get("block_id"),
                                   "true": true, "got": got})
    return {"ok": ok, "total": total, "mismatches": mismatches}


def sigla_for_repo(repo_root: Path) -> str | None:
    base = repo_root.name
    if base.endswith("-Tutor"):
        base = base[: -len("-Tutor")]
    return REPO_SIGLA.get(base)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", default=None, metavar="CURSO",
                    help="restringe a 1 curso (sigla, ex. MF)")
    ap.add_argument("--baseline", default=None, help="json anterior; exit 1 se regressao")
    ap.add_argument("--out", default=None, help="grava o resultado em json")
    args = ap.parse_args()

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8")) if args.baseline else {}

    results: dict = {}
    regressed = False
    store = SubjectStore()
    for name in store.names():
        sp = store.get(name)
        repo = Path(getattr(sp, "repo_root", "") or "")
        sigla = sigla_for_repo(repo)
        if not sigla or (args.course and sigla != args.course):
            continue

        gold_csv = GOLD_DIR / f"gold_units_{sigla}.csv"
        idx_path = repo / "course" / ".timeline_index.json"
        if not gold_csv.is_file():
            print(f"[skip] {sigla}: sem gold ({gold_csv})")
            continue
        if not idx_path.is_file():
            print(f"[skip] {sigla}: sem indice ({idx_path})")
            continue

        index = json.loads(idx_path.read_text(encoding="utf-8"))
        r = score_course(gold_csv, index)
        results[sigla] = r
        pct = (100.0 * r["ok"] / r["total"]) if r["total"] else 0.0
        print(f"{sigla} {r['ok']}/{r['total']} ({pct:.1f}%)")
        for m in r["mismatches"]:
            print(f"  MISMATCH {m['block_id']} ({m['block_uuid']}) true={m['true']} got={m['got']}")

        base_ok = (baseline.get(sigla) or {}).get("ok")
        if base_ok is not None and r["ok"] < base_ok:
            regressed = True
            print(f"  REGRESSAO: ok={r['ok']} < baseline={base_ok}")

    if args.out:
        Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
