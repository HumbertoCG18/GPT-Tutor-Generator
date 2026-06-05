"""Harness de medicao de correcao file->bloco contra um repo gerado real.

Le predicoes do manifest.json + bloco->periodo do course/.timeline_index.json
e compara com rotulos de verdade (CSV). Reporta acuracia, confusao,
confiante-e-errado e calibracao por band. Nao re-roda o scorer.

Uso:
    python scripts/eval_ground_truth.py <repo_root> <labels.csv>
    python scripts/eval_ground_truth.py <repo_root> <labels.csv> --json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def load_predictions(repo_root: Path) -> dict:
    manifest = json.loads((Path(repo_root) / "manifest.json").read_text(encoding="utf-8"))
    preds = {}
    for e in manifest.get("entries", []):
        eid = str(e.get("id", ""))
        if not eid:
            continue
        preds[eid] = {
            "block_id": str(e.get("computed_block_id", "")),
            "band": str(e.get("computed_block_band", "")),
            "confidence": float(e.get("computed_block_confidence", 0.0) or 0.0),
            "title": str(e.get("title", "")),
            "category": str(e.get("category", "")),
            "markdown_path": str(e.get("markdown_path", "") or e.get("base_markdown", "")),
        }
    return preds


def load_block_period_map(repo_root: Path) -> dict:
    path = Path(repo_root) / "course" / ".timeline_index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(b.get("id", "")): str(b.get("period_label", "")) for b in data.get("blocks", [])}


def load_labels_csv(path: Path) -> dict:
    labels = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            eid = str(row.get("id", "")).strip()
            true_block = str(row.get("true_block_id", "")).strip()
            if eid and true_block:
                labels[eid] = true_block
    return labels


def evaluate_ground_truth(predictions: dict, labels: dict, block_map: dict) -> dict:
    bands = {"alta": {"correct": 0, "wrong": 0}, "media": {"correct": 0, "wrong": 0},
             "baixa": {"correct": 0, "wrong": 0}, "": {"correct": 0, "wrong": 0}}
    confusion: dict = {}
    rows = []
    correct = orphans = missed = confident_wrong = 0

    for eid, true_block in labels.items():
        pred = predictions.get(eid, {})
        predicted = str(pred.get("block_id", ""))
        band = str(pred.get("band", ""))
        is_correct = predicted == true_block
        if is_correct:
            correct += 1
        if predicted == "":
            orphans += 1
            if true_block:
                missed += 1
        if band == "alta" and not is_correct:
            confident_wrong += 1
        bands.setdefault(band, {"correct": 0, "wrong": 0})
        bands[band]["correct" if is_correct else "wrong"] += 1
        key = f"{true_block}->{predicted or '(orfao)'}"
        confusion[key] = confusion.get(key, 0) + 1
        rows.append({"id": eid, "true": true_block, "predicted": predicted,
                     "band": band, "correct": is_correct,
                     "title": str(pred.get("title", ""))})

    total = len(labels)
    return {
        "total": total, "correct": correct, "wrong": total - correct,
        "block_accuracy": (correct / total) if total else 0.0,
        "orphans": orphans, "missed": missed, "confident_wrong": confident_wrong,
        "bands": bands, "confusion": confusion, "cases": rows,
    }


def format_report(report: dict, block_map: dict) -> str:
    lines = ["=== Eval ground-truth: atribuicao file -> bloco ==="]
    acc = report["block_accuracy"]
    lines.append(f"Acuracia: {report['correct']}/{report['total']} ({acc * 100:.1f}%)")
    lines.append(f"Orfaos (previu vazio): {report['orphans']}   Missed (verdade tinha bloco): {report['missed']}")
    lines.append(f"Confiante e ERRADO (band alta, bloco errado): {report['confident_wrong']}")
    lines.append("")
    lines.append("Calibracao por band (correto / errado):")
    for band in ("alta", "media", "baixa", ""):
        b = report["bands"].get(band, {"correct": 0, "wrong": 0})
        lines.append(f"  {(band or '(vazio)'):<8} {b['correct']:>3} ok / {b['wrong']:>3} erro")
    wrong = [c for c in report["cases"] if not c["correct"]]
    lines.append("")
    if wrong:
        lines.append("Erros:")
        for c in wrong:
            tp = block_map.get(c["true"], c["true"])
            pp = block_map.get(c["predicted"], c["predicted"] or "(orfao)")
            lines.append(f"  - {c['id']:<24} verdade={c['true'] or '-'} ({tp}) "
                         f"previu={c['predicted'] or '(orfao)'} ({pp}) band={c['band'] or '-'}")
    else:
        lines.append("Sem erros.")
    return "\n".join(lines)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    as_json = "--json" in argv
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python scripts/eval_ground_truth.py <repo_root> <labels.csv> [--json]")
        return 2
    repo_root, labels_path = Path(pos[0]), Path(pos[1])
    preds = load_predictions(repo_root)
    block_map = load_block_period_map(repo_root)
    labels = load_labels_csv(labels_path)
    report = evaluate_ground_truth(preds, labels, block_map)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report, block_map))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
