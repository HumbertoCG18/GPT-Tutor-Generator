"""Gera o template de gold de unidade (U3) a partir do indice EM DISCO
(course/.timeline_index.json) — NAO da sonda (course_probe): o gold rotula o
estado ATUAL de producao, nao um recompute experimental. So LEITURA nos
repos-tutor; escreve so em docs/reports/gold_templates/ deste repo.
Uso: python scripts/gold_units_template.py"""
from __future__ import annotations

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
from scripts.eval_units import sigla_for_repo  # noqa: E402

OUT_DIR = ROOT / "docs" / "reports" / "gold_templates"
FIELDS = ["block_uuid", "block_id", "date_start", "date_end", "kind",
          "topic_text", "unit_slug_atual", "true_unit", "notes"]


def build_rows(index: dict) -> list[dict]:
    """Um bloco = 1 linha; pula blocos com source_kind (provas/eventos gerados
    fora da timeline instrucional, ver task-6-brief)."""
    rows = []
    for b in index.get("blocks", []):
        if b.get("source_kind"):
            continue
        rows.append({
            "block_uuid": b.get("block_uuid") or "",
            "block_id": b.get("id") or "",
            "date_start": b.get("period_start") or "",
            "date_end": b.get("period_end") or "",
            "kind": b.get("kind") or "",
            "topic_text": b.get("topic_text") or "",
            "unit_slug_atual": b.get("unit_slug") or "",
            "true_unit": "",
            "notes": "",
        })
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    store = SubjectStore()
    for name in store.names():
        sp = store.get(name)
        repo = Path(getattr(sp, "repo_root", "") or "")
        sigla = sigla_for_repo(repo)
        if not sigla:
            continue
        idx_path = repo / "course" / ".timeline_index.json"
        if not idx_path.is_file():
            print(f"[skip] {sigla}: sem indice ({idx_path})")
            continue

        index = json.loads(idx_path.read_text(encoding="utf-8"))
        rows = build_rows(index)
        out_path = OUT_DIR / f"gold_units_{sigla}.csv"
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"{sigla}: {len(rows)} blocos -> {out_path}")
        total += len(rows)

    print(f"TOTAL: {total} blocos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
