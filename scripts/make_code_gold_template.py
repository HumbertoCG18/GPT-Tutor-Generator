"""Gera template CSV para o gold de código (Fase 3 do resolver).

Uma linha por entry de código/zip de um repo gerado, pré-preenchida com as
predições funil/gemini/resolver + períodos do cronograma. `true_block_id`
sai VAZIO para o humano preencher (Task 3.2.2).

Uso:
    python scripts/make_code_gold_template.py <repo_root> <out.csv>
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_resolver import compare_repo  # noqa: E402
from scripts.eval_ground_truth import load_block_period_map  # noqa: E402

CODE_TYPES = {"code", "zip"}

COLUMNS = [
    "id", "inferred_title", "concepts", "card",
    "funil_band", "funil_block", "funil_period",
    "gemini_primary", "gemini_period",
    "resolver_block", "resolver_period", "resolver_unit",
    "true_block_id",
]


def build_code_gold_rows(
    manifest_entries: list,
    code_curation: dict,
    resolver_rows_by_id: dict,
    period_map: dict,
) -> list[dict]:
    """Monta as linhas do template — pura, sem IO."""
    rows = []
    for entry in manifest_entries:
        if str(entry.get("file_type") or "") not in CODE_TYPES:
            continue
        eid = str(entry.get("id") or "")
        summary = (code_curation.get(eid) or {}).get("summary") or {}
        resolver_row = resolver_rows_by_id.get(eid) or {}

        concepts_raw = summary.get("concepts") or []
        concepts_str = "; ".join(str(c) for c in concepts_raw) if concepts_raw else ""

        funil_block = str(entry.get("computed_block_id") or "")
        gemini_primary = str(summary.get("primary_block_id") or "")
        resolver_block = str(resolver_row.get("resolver_block") or "")

        rows.append({
            "id": eid,
            "inferred_title": str(summary.get("inferred_title") or ""),
            "concepts": concepts_str,
            "card": bool(str(entry.get("source_section") or "").strip()),
            "funil_band": str(entry.get("computed_block_band") or ""),
            "funil_block": funil_block,
            "funil_period": period_map.get(funil_block, ""),
            "gemini_primary": gemini_primary,
            "gemini_period": period_map.get(gemini_primary, ""),
            "resolver_block": resolver_block,
            "resolver_period": period_map.get(resolver_block, ""),
            "resolver_unit": str(resolver_row.get("resolver_unit") or ""),
            "true_block_id": "",
        })
    return rows


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python scripts/make_code_gold_template.py <repo_root> <out.csv>")
        return 2

    repo_root, out_path = Path(pos[0]), Path(pos[1])

    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    manifest_entries = manifest.get("entries") or []

    cur_path = repo_root / "code_curation.json"
    code_curation_raw = json.loads(cur_path.read_text(encoding="utf-8")) if cur_path.exists() else {"entries": {}}
    # Normaliza para {id: record} (sem o wrapper "entries")
    code_curation = code_curation_raw.get("entries") or {}

    compare_result = compare_repo(repo_root) or {}
    resolver_rows = compare_result.get("rows") or []
    resolver_rows_by_id = {r["id"]: r for r in resolver_rows}

    period_map = load_block_period_map(repo_root)

    rows = build_code_gold_rows(manifest_entries, code_curation, resolver_rows_by_id, period_map)

    with Path(out_path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"Template escrito: {out_path}  ({len(rows)} entries de código/zip)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
