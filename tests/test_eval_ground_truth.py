import csv
import json
from pathlib import Path

from scripts.eval_ground_truth import (
    load_predictions, load_block_period_map, load_labels_csv,
)


def _make_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    manifest = {
        "entries": [
            {"id": "m-ok", "title": "Aula 1", "category": "material-de-aula",
             "computed_block_id": "bloco-01", "computed_block_band": "alta",
             "computed_block_confidence": 0.9, "markdown_path": "content/curated/m-ok.md"},
            {"id": "m-confwrong", "title": "Aula 2", "category": "material-de-aula",
             "computed_block_id": "bloco-02", "computed_block_band": "alta",
             "computed_block_confidence": 0.88, "markdown_path": "content/curated/m2.md"},
            {"id": "m-orfao", "title": "Aula 3", "category": "material-de-aula",
             "markdown_path": "content/curated/m3.md"},
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    timeline = {"version": 4, "blocks": [
        {"id": "bloco-01", "period_label": "Semana 1"},
        {"id": "bloco-02", "period_label": "Semana 2"},
        {"id": "bloco-03", "period_label": "Semana 3"},
    ]}
    (repo / "course" / ".timeline_index.json").write_text(json.dumps(timeline), encoding="utf-8")
    return repo


def test_load_predictions_reads_fields_with_defaults(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    assert preds["m-ok"]["block_id"] == "bloco-01"
    assert preds["m-ok"]["band"] == "alta"
    assert preds["m-orfao"]["block_id"] == ""
    assert preds["m-orfao"]["band"] == ""
    assert preds["m-ok"]["markdown_path"] == "content/curated/m-ok.md"


def test_load_block_period_map(tmp_path):
    repo = _make_repo(tmp_path)
    m = load_block_period_map(repo)
    assert m["bloco-01"] == "Semana 1"
    assert m["bloco-03"] == "Semana 3"


def test_load_labels_csv_skips_empty_true(tmp_path):
    p = tmp_path / "labels.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "true_block_id"])
        w.writerow(["m-ok", "bloco-01"])
        w.writerow(["m-skip", ""])
    labels = load_labels_csv(p)
    assert labels == {"m-ok": "bloco-01"}


from scripts.eval_ground_truth import evaluate_ground_truth


def test_evaluate_metrics(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    block_map = load_block_period_map(repo)
    labels = {"m-ok": "bloco-01", "m-confwrong": "bloco-03", "m-orfao": "bloco-03"}
    r = evaluate_ground_truth(preds, labels, block_map)
    assert r["total"] == 3
    assert r["correct"] == 1
    assert r["wrong"] == 2
    assert abs(r["block_accuracy"] - 1/3) < 1e-9
    assert r["confident_wrong"] == 1
    assert r["orphans"] == 1
    assert r["missed"] == 1
    band_total = sum(b["correct"] + b["wrong"] for b in r["bands"].values())
    assert band_total == r["total"]
    assert r["confusion"]["bloco-03->(orfao)"] == 1


def test_evaluate_only_labeled_entries(tmp_path):
    repo = _make_repo(tmp_path)
    preds = load_predictions(repo)
    block_map = load_block_period_map(repo)
    labels = {"m-ok": "bloco-01"}
    r = evaluate_ground_truth(preds, labels, block_map)
    assert r["total"] == 1
    assert r["correct"] == 1
