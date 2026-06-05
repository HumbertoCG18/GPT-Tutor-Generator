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
