"""Gera o template de rotulagem MULTI-LABEL para material (nao referencias).

Sai um CSV por curso em `docs/reports/material_gt_<SIGLA>.csv`, no MESMO formato
que `coverage_gt_*.csv` (a regua `eval_coverage.py` ja le `gold_units`
pipe-separated), mais um catalogo de slugs por curso para consulta.

So entram as entries em DISPUTA: aquelas cuja unidade gravada difere da unidade
do bloco temporal verdadeiro. Sao exatamente os casos onde a pergunta e "erro do
scorer ou divergencia de eixo?" — e so o rotulo humano decide.

Ordem: ES2 e SO primeiro (carregam 25 dos 39 erros), depois MF, TCC, IA.

Uso:
    python scripts/make_material_coverage_labels.py
    python scripts/make_material_coverage_labels.py --course ES2
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.engine import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402

GITHUB_DIR = ROOT.parent
# ES2 e SO primeiro: e onde a duvida erro-vs-eixo esta concentrada.
COURSES = [
    ("ES2", "Engenharia-Software-2-Tutor"),
    ("SO", "Sistemas-Operacionais-Tutor"),
    ("MF", "Metodos-Formais-Tutor"),
    ("TCC", "TCC-Tutor"),
    ("IA", "Inteligencia-Artifical-Tutor"),
]
CABECALHO = ["entry_id", "title", "category", "card", "posting_date", "text_chars",
             "evidencia", "pred_unit", "unit_do_bloco_temporal", "gold_units",
             "gold_topics", "scorable", "notas"]


def _evidencia(markdown: str, limite: int = 260) -> str:
    """Headings do markdown quando houver — dizem o assunto melhor que o lead.
    Sem heading, cai no inicio do texto. Vazio => so o Moodle resolve."""
    if not (markdown or "").strip():
        return "(SEM TEXTO — PRECISA MOODLE)"
    titulos = [
        re.sub(r"\s+", " ", m.group(1)).strip()
        for m in re.finditer(r"^#{1,4}\s+(.+?)\s*$", markdown, flags=re.M)
    ]
    titulos = [t for t in titulos if t and not t.lower().startswith(("sumario", "sumário"))]
    if titulos:
        return " · ".join(dict.fromkeys(titulos))[:limite]
    return re.sub(r"\s+", " ", markdown).strip()[:limite]


def _verdade_temporal(sigla: str) -> dict:
    gold_units = ROOT / "tests" / "fixtures" / "eval" / f"gold_units_{sigla}.csv"
    ground_truth = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
    if not (gold_units.exists() and ground_truth.exists()):
        return {}
    por_uuid = {
        (r.get("block_uuid") or "").strip(): (r.get("true_unit") or "").strip()
        for r in csv.DictReader(gold_units.open(encoding="utf-8-sig"))
        if (r.get("true_unit") or "").strip()
    }
    out = {}
    for r in csv.DictReader(ground_truth.open(encoding="utf-8-sig")):
        if (r.get("scorable") or "").strip().lower() != "yes":
            continue
        unidade = por_uuid.get((r.get("true_block_uuid") or "").strip())
        if unidade:
            out[r["id"]] = unidade
    return out


def gerar(sigla: str, repo_name: str) -> dict:
    repo = GITHUB_DIR / repo_name
    manifest_path = repo / "manifest.json"
    verdade = _verdade_temporal(sigla)
    if not manifest_path.exists() or not verdade:
        return {"curso": sigla, "erro": "sem manifest ou sem rotulos"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    taxonomia = load_internal_content_taxonomy(repo) or {}

    catalogo = []
    for unidade in taxonomia.get("units") or []:
        topicos = [str(t.get("slug")) for t in (unidade.get("topics") or [])]
        catalogo.append((str(unidade.get("slug")), str(unidade.get("title") or ""), topicos))

    linhas = []
    for entry in manifest.get("entries") or []:
        eid = str(entry.get("id") or "")
        if not _is_material(entry) or eid not in verdade:
            continue
        gravado = str(entry.get("computed_unit_slug") or entry.get("manual_unit_slug") or "")
        if gravado == verdade[eid]:
            continue  # concorda com a verdade temporal: nao esta em disputa
        markdown = _entry_markdown_text_for_file_map(repo, entry)
        linhas.append({
            "entry_id": eid,
            "title": str(entry.get("title") or ""),
            "category": str(entry.get("category") or ""),
            "card": str(entry.get("source_section") or ""),
            "posting_date": str(entry.get("posting_date") or ""),
            "text_chars": len(markdown or ""),
            "evidencia": _evidencia(markdown),
            "pred_unit": gravado,
            "unit_do_bloco_temporal": verdade[eid],
            "gold_units": "",
            "gold_topics": "",
            "scorable": "yes",
            "notas": "",
        })

    destino = ROOT / "docs" / "reports" / f"material_gt_{sigla}.csv"
    # PRESERVA rotulo humano ja dado: regenerar nao pode apagar trabalho de
    # curadoria (aconteceu em 2026-08-19 e custou os rulings de ES2 e SO).
    ja_rotulado = {}
    if destino.exists():
        for antigo in csv.DictReader(destino.open(encoding="utf-8-sig")):
            if (antigo.get("gold_units") or "").strip() or antigo.get("scorable") == "no":
                ja_rotulado[antigo["entry_id"]] = antigo
    for linha in linhas:
        antigo = ja_rotulado.get(linha["entry_id"])
        if antigo:
            linha["gold_units"] = antigo.get("gold_units", "")
            linha["gold_topics"] = antigo.get("gold_topics", "")
            linha["scorable"] = antigo.get("scorable", "yes")
            linha["notas"] = antigo.get("notas", "")
    with destino.open("w", encoding="utf-8-sig", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=CABECALHO)
        escritor.writeheader()
        escritor.writerows(linhas)

    catalogo_path = ROOT / "docs" / "reports" / f"material_units_{sigla}.md"
    partes = [f"# Catálogo de unidades e tópicos — {sigla}", "",
              "Slugs para preencher `gold_units` (pipe-separated) e `gold_topics`.", ""]
    for slug, titulo, topicos in catalogo:
        partes.append(f"## `{slug}`")
        partes.append(f"{titulo}")
        partes.append("")
        for t in topicos:
            partes.append(f"- `{t}`")
        partes.append("")
    catalogo_path.write_text("\n".join(partes), encoding="utf-8")
    return {"curso": sigla, "casos": len(linhas), "csv": destino.name,
            "catalogo": catalogo_path.name, "unidades": len(catalogo)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", help="sigla; omitido = todos")
    args = parser.parse_args(argv[1:])
    alvos = [(s, r) for s, r in COURSES if not args.course or s == args.course.upper()]
    total = 0
    for sigla, repo in alvos:
        r = gerar(sigla, repo)
        if r.get("erro"):
            print(f"{r['curso']:5} {r['erro']}")
            continue
        total += r["casos"]
        print(f"{r['curso']:5} {r['casos']:3} casos em disputa -> {r['csv']}  "
              f"({r['unidades']} unidades em {r['catalogo']})")
    print(f"\nTOTAL {total} casos para rotular.")
    print("Preencher `gold_units` com os slugs separados por | (ex.: u-01|u-02).")
    print("Medir depois com: python scripts/eval_coverage.py <repo> docs/reports/material_gt_<C>.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
