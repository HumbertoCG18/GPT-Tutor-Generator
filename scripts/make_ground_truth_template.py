"""Gera um CSV esqueleto de rotulos ground-truth a partir de um repo gerado.

Uma linha por material do manifest, com a predicao atual; a coluna
`true_block_id` ja vem pre-preenchida com o bloco predito (o usuario so
confirma/corrige). Imprime no stdout a referencia de blocos validos.

Uso:
    python scripts/make_ground_truth_template.py <repo_root> <out.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.eval_ground_truth import load_predictions, load_block_period_map

COLUMNS = ["id", "title", "category", "markdown_path",
           "predicted_block_id", "predicted_period", "predicted_band", "true_block_id"]


def build_template_rows(repo_root: Path) -> list:
    preds = load_predictions(repo_root)
    block_map = load_block_period_map(repo_root)
    rows = []
    for eid, p in preds.items():
        block_id = p.get("block_id", "")
        rows.append({
            "id": eid,
            "title": p.get("title", ""),
            "category": p.get("category", ""),
            "markdown_path": p.get("markdown_path", ""),
            "predicted_block_id": block_id,
            "predicted_period": block_map.get(block_id, ""),
            "predicted_band": p.get("band", ""),
            "true_block_id": block_id,
        })
    return rows


def write_template_csv(rows: list, out_path: Path) -> None:
    with Path(out_path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python scripts/make_ground_truth_template.py <repo_root> <out.csv>")
        return 2
    repo_root, out_path = Path(pos[0]), Path(pos[1])
    rows = build_template_rows(repo_root)
    write_template_csv(rows, out_path)
    block_map = load_block_period_map(repo_root)
    print(f"Esqueleto escrito: {out_path}  ({len(rows)} materiais)")
    print("Blocos validos (id -> periodo):")
    for bid, period in block_map.items():
        print(f"  {bid:<16} {period}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
