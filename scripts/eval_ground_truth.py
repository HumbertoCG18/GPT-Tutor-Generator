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
