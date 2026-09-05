"""Esqueleto da regua de COBERTURA (material transversal -> N unidades).

Cobertura nao e o eixo temporal: prova, lista, gabarito e bibliografia nao
pertencem a um bloco, cobrem N unidades. Este script so monta o CSV a rotular
(rotulo e humano) e o catalogo de unidades do curso para consulta.

Preserva as colunas gold_*/scorable/notas de um CSV ja existente: reexecutar
atualiza evidencia e predicao sem apagar rotulo manual.

Uso:
    python scripts/make_coverage_labels.py <repo_root> <SIGLA>
    python scripts/make_coverage_labels.py <repo_root> <SIGLA> --categories provas,listas
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[1] / "docs" / "reports"
DEFAULT_CATEGORIES = ("referencias", "references", "bibliografia")
FIELDS = [
    "entry_id", "title", "category", "card", "text_source", "text_chars", "evidencia",
    "pred_unit", "gold_units", "gold_topics", "scorable", "notas",
]
_GOLD_FIELDS = ("gold_units", "gold_topics", "scorable", "notas")
_NOISE_RE = re.compile(r"^(!\[|\||>|<!--|-->|\{\d+\}|-{3,}|\s*$)")


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _evidence(repo_root: Path, entry: dict, limit: int = 220) -> tuple[str, int, str]:
    """(caminho_do_md, tamanho, primeiras linhas de prosa). Vazio quando nao ha texto local."""
    rel = ""
    for field in ("approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"):
        rel = str(entry.get(field) or "")
        if rel:
            break
    if not rel:
        return "", 0, ""
    path = repo_root / rel
    if not path.exists():
        return rel, 0, ""
    text = path.read_text(encoding="utf-8", errors="replace")
    # O sumario executivo injetado no topo do curated e boilerplate: a evidencia
    # util comeca depois do marcador de fim.
    body = text.split("EXEC_SUMMARY_END", 1)[-1]
    prose = []
    for raw in body.splitlines():
        line = raw.strip()
        if _NOISE_RE.match(line):
            continue
        prose.append(line.lstrip("#").strip())
    snippet = re.sub(r"\s+", " ", " ".join(prose))[:limit]
    return rel, len(text), snippet


def _write_unit_catalog(sigla: str, taxonomy: dict) -> Path:
    lines = [f"# Catalogo de unidades e topicos — {sigla}", "",
             "Consulta para preencher `gold_units` / `gold_topics` (pipe-separated).", ""]
    for unit in taxonomy.get("units", []) or []:
        lines.append(f"## `{unit.get('slug', '')}`")
        lines.append(f"{unit.get('title', '')}")
        for topic in unit.get("topics", []) or []:
            label = re.sub(r"\*+", "", str(topic.get("label") or "")).strip()
            lines.append(f"- `{topic.get('slug', '')}` — {label}")
        lines.append("")
    out = REPORTS / f"coverage_units_{sigla}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    repo_root = Path(argv[1]).resolve()
    sigla = argv[2].upper()
    categories = set(DEFAULT_CATEGORIES)
    if "--categories" in argv:
        categories = {c.strip().lower() for c in argv[argv.index("--categories") + 1].split(",") if c.strip()}

    manifest = _read_json(repo_root / "manifest.json", {})
    taxonomy = _read_json(repo_root / "course" / ".content_taxonomy.json", {})
    curation = _read_json(repo_root / "course" / "references_curation.json", {}).get("entries", {})

    out_csv = REPORTS / f"coverage_gt_{sigla}.csv"
    previous = {}
    if out_csv.exists():
        with out_csv.open(encoding="utf-8-sig", newline="") as fh:
            previous = {row["entry_id"]: row for row in csv.DictReader(fh)}

    rows = []
    for entry in manifest.get("entries", []) or []:
        if str(entry.get("category") or "").lower() not in categories:
            continue
        eid = str(entry.get("id") or "")
        source, size, snippet = _evidence(repo_root, entry)
        keep = previous.get(eid, {})
        rows.append({
            "entry_id": eid,
            "title": str(entry.get("title") or ""),
            "category": str(entry.get("category") or ""),
            "card": str(entry.get("source_section") or ""),
            "text_source": source,
            "text_chars": size,
            "evidencia": snippet,
            "pred_unit": str((curation.get(eid) or {}).get("computed_ref_unit") or ""),
            "gold_units": keep.get("gold_units", ""),
            "gold_topics": keep.get("gold_topics", ""),
            "scorable": keep.get("scorable", "yes"),
            "notas": keep.get("notas", ""),
        })

    REPORTS.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    catalog = _write_unit_catalog(sigla, taxonomy)

    rotulados = sum(1 for r in rows if r["gold_units"].strip())
    sem_texto = sum(1 for r in rows if not r["text_chars"])
    print(f"{sigla}: {len(rows)} entries | rotuladas={rotulados} | sem texto local={sem_texto}")
    print(f"  {out_csv}")
    print(f"  {catalog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
