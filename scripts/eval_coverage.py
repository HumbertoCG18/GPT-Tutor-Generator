"""Regua de COBERTURA: mede material transversal -> N unidades contra rotulo humano.

Multi-label por natureza (uma prova/referencia cobre varias unidades), entao a
metrica e precision/recall/F1 por item + macro, mais exact-set-match. Le a
predicao da curation do repo, aceitando o campo atual (`computed_ref_unit`,
single) e o futuro (`coverage_units`, lista).

Uso:
    python scripts/eval_coverage.py <repo_root> docs/reports/coverage_gt_<SIGLA>.csv
    python scripts/eval_coverage.py <repo_root> <labels.csv> --json
    python scripts/eval_coverage.py --selftest
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def _split(value: str) -> set[str]:
    return {p.strip() for p in str(value or "").split("|") if p.strip()}


def _load_predictions(repo_root: Path) -> dict[str, set[str]]:
    for name in ("coverage_curation.json", "references_curation.json"):
        path = Path(repo_root) / "course" / name
        if not path.exists():
            continue
        entries = json.loads(path.read_text(encoding="utf-8")).get("entries", {}) or {}
        out = {}
        for eid, rec in entries.items():
            units = rec.get("coverage_units")
            if isinstance(units, list):
                slugs = {str(u.get("unit_slug") if isinstance(u, dict) else u or "").strip() for u in units}
            else:
                slugs = {str(rec.get("computed_ref_unit") or "").strip()}
            out[eid] = {s for s in slugs if s}
        return out
    return {}


def score(gold: dict[str, set[str]], pred: dict[str, set[str]]) -> dict:
    rows, exact = [], 0
    for eid, gold_units in gold.items():
        pred_units = pred.get(eid, set())
        hit = len(gold_units & pred_units)
        precision = hit / len(pred_units) if pred_units else 0.0
        recall = hit / len(gold_units) if gold_units else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        exact += int(gold_units == pred_units)
        rows.append({
            "entry_id": eid, "gold": sorted(gold_units), "pred": sorted(pred_units),
            "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "missing": sorted(gold_units - pred_units), "spurious": sorted(pred_units - gold_units),
        })
    n = len(rows) or 1
    return {
        "n": len(rows),
        "exact_set_match": exact,
        "macro_precision": round(sum(r["precision"] for r in rows) / n, 3),
        "macro_recall": round(sum(r["recall"] for r in rows) / n, 3),
        "macro_f1": round(sum(r["f1"] for r in rows) / n, 3),
        "sem_predicao": sum(1 for r in rows if not r["pred"]),
        "rows": rows,
    }


def _selftest() -> int:
    gold = {"a": {"u1", "u2"}, "b": {"u3"}, "c": {"u4"}}
    pred = {"a": {"u1", "u2"}, "b": {"u3", "u9"}, "c": set()}
    result = score(gold, pred)
    assert result["exact_set_match"] == 1, result["exact_set_match"]
    assert result["macro_recall"] == round((1.0 + 1.0 + 0.0) / 3, 3), result["macro_recall"]
    assert result["macro_precision"] == round((1.0 + 0.5 + 0.0) / 3, 3), result["macro_precision"]
    assert result["sem_predicao"] == 1
    assert result["rows"][1]["spurious"] == ["u9"]
    print("selftest ok")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    if len(argv) < 3:
        print(__doc__)
        return 2
    repo_root, labels_path = Path(argv[1]).resolve(), Path(argv[2])
    gold, pendentes = {}, []
    with labels_path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("scorable", "yes")).strip().lower() != "yes":
                continue
            units = _split(row.get("gold_units", ""))
            if not units:
                pendentes.append(row["entry_id"])
                continue
            gold[row["entry_id"]] = units

    result = score(gold, _load_predictions(repo_root))
    result["nao_rotuladas"] = len(pendentes)
    if "--json" in argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"itens rotulados: {result['n']} | nao rotulados: {len(pendentes)}")
    if not result["n"]:
        print("nada a medir: preencha gold_units no CSV")
        return 0
    print(f"exact-set-match: {result['exact_set_match']}/{result['n']} | "
          f"macro P/R/F1: {result['macro_precision']}/{result['macro_recall']}/{result['macro_f1']} | "
          f"sem predicao: {result['sem_predicao']}")
    print()
    for row in result["rows"]:
        status = "OK " if row["f1"] == 1.0 else "ERR"
        print(f"{status} {row['entry_id'][:40]:42} F1={row['f1']:<5} "
              f"falta={','.join(row['missing']) or '-'} sobra={','.join(row['spurious']) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
