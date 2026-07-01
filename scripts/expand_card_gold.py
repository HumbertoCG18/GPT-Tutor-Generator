"""Expande a planilha por-card (rotulada) para um gold file->bloco auto-contido.

Le o gold_by_card_<curso>.csv DEPOIS de voce confirmar `true_block_id` por card,
e o manifest do repo (p/ a predicao atual), e emite uma linha por ARQUIVO:
id, title, predicted_block_id, predicted_band, true_block_id. Esse formato e
consumido por scripts/eval_ground_truth.py (load_predictions_from_gold +
load_labels_csv + check_baseline) — gate cross-curso auto-contido.

Uso:
    python -m scripts.expand_card_gold <repo_root> <gold_by_card.csv> <out_gold.csv>
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT_COLUMNS = ["id", "title", "predicted_block_id", "predicted_band", "true_block_id"]


def expand_rows(repo_root: Path, by_card_csv: Path) -> list[dict]:
    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    pred = {}
    for e in manifest.get("entries") or []:
        eid = str(e.get("id") or "")
        if eid:
            pred[eid] = {"block": str(e.get("computed_block_id") or ""),
                         "band": str(e.get("computed_block_band") or ""),
                         "title": str(e.get("title") or "")}
    out = []
    with by_card_csv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            true_block = str(row.get("true_block_id") or "").strip()
            fids = [x for x in str(row.get("file_ids") or "").split(";") if x]
            for fid in fids:
                p = pred.get(fid, {})
                out.append({"id": fid, "title": p.get("title", ""),
                            "predicted_block_id": p.get("block", ""),
                            "predicted_band": p.get("band", ""),
                            "true_block_id": true_block})
    return out


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 3:
        print("uso: python -m scripts.expand_card_gold <repo_root> <gold_by_card.csv> <out_gold.csv>")
        return 2
    repo_root, by_card_csv, out = Path(pos[0]), Path(pos[1]), Path(pos[2])
    rows = expand_rows(repo_root, by_card_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    labeled = sum(1 for r in rows if r["true_block_id"])
    print(f"{out}  ({len(rows)} arquivos, {labeled} com true_block_id)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
