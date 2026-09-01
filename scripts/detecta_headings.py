"""Auditoria: headings internos vs subunidade atribuida (fila 2026-08-31, item b).

    python scripts/detecta_headings.py                    # 6 cursos
    python scripts/detecta_headings.py --repos ES2,SO     # subconjunto
    python scripts/detecta_headings.py --min-chars 6      # calibrar contencao

Regra (a mesma investigacao manual que achou SO plano/programa e ES2 devops
em 31/08, agora sem LLM e repetivel):
  SUSPEITO = algum heading do markdown nomeia uma subunit IRMA (mesma unidade,
  diferente da atribuida) E a subunit atribuida nao aparece em NENHUM heading.

Matching label<->heading nos DOIS sentidos (contencao apos normalize): o
heading "DevOps" e MAIS CURTO que o label "Conceito de DevOps" e tem que
casar — contencao so do label no heading perdia esse caso. Labels PUROS da
taxonomia (sem aliases): aliases incluem os enriquecidos por heading, que
mascarariam exatamente o padrao que se procura (caso ES2 `web`/serverless).

Read-only: nao muda manifest nem motor. Rodar POS-reprocess, como o
detecta_duplicatas. Saida = relatorio por curso para triagem humana — flag
NAO significa erro (doc multi-secao legitimo tambem aparece; ES2 `devops`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from eval_entry_unit import COURSES as _COURSES, GITHUB_DIR  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402

COURSES = dict(_COURSES)
COURSES.setdefault("CG", "Computacao-Grafica-Tutor")

_MD_KEYS = ("approved_markdown", "curated_markdown", "base_markdown")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def _headings(md_text: str) -> list[str]:
    return [normalize_match_text(h) for h in _HEADING_RE.findall(md_text)]


def _casa(label_norm: str, heading_norm: str, min_chars: int) -> bool:
    """Contencao nos DOIS sentidos; o lado contido precisa de min_chars para
    nao casar por token estrutural curto."""
    if not label_norm or not heading_norm:
        return False
    if label_norm == heading_norm:
        return True
    menor, maior = sorted((label_norm, heading_norm), key=len)
    return len(menor) >= min_chars and menor in maior


def _topics_por_unidade(taxonomy: dict) -> dict[str, list[tuple[str, str]]]:
    """{unit_slug: [(topic_slug, label_normalizado)]} — labels puros."""
    por_unidade: dict[str, list[tuple[str, str]]] = {}
    for unit in (taxonomy or {}).get("units", []) or []:
        slug = str(unit.get("slug") or "")
        for topic in unit.get("topics", []) or []:
            t_slug = str(topic.get("slug") or "")
            label = normalize_match_text(str(topic.get("label") or ""))
            if slug and t_slug and label:
                por_unidade.setdefault(slug, []).append((t_slug, label))
    return por_unidade


def audita_curso(repo: Path, min_chars: int) -> list[dict]:
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    try:
        taxonomy = json.loads((repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    topics = _topics_por_unidade(taxonomy)
    suspeitos = []
    for entry in manifest.get("entries") or []:
        atribuida = str(entry.get("computed_subunit_slug") or "")
        unidade = str(entry.get("computed_unit_slug") or "")
        if not atribuida or not unidade or entry.get("duplicate_of"):
            continue
        irmaos = topics.get(unidade) or []
        label_atribuida = next((lb for sl, lb in irmaos if sl == atribuida), "")
        if not label_atribuida:
            continue
        md_rel = next((entry.get(k) for k in _MD_KEYS if entry.get(k)), None)
        if not md_rel or not (repo / str(md_rel)).is_file():
            continue
        hs = _headings((repo / str(md_rel)).read_text(encoding="utf-8", errors="replace"))
        if not hs:
            continue
        atribuida_em_heading = any(_casa(label_atribuida, h, min_chars) for h in hs)
        if atribuida_em_heading:
            continue
        irmas_citadas = sorted({
            sl for sl, lb in irmaos
            if sl != atribuida and any(_casa(lb, h, min_chars) for h in hs)
        })
        if irmas_citadas:
            suspeitos.append({
                "id": str(entry.get("id") or ""),
                "atribuida": atribuida,
                "irmas_em_heading": irmas_citadas,
            })
    return suspeitos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repos", default=",".join(COURSES), help="siglas separadas por virgula")
    ap.add_argument("--min-chars", type=int, default=5,
                    help="tamanho minimo do lado contido na contencao (default 5; 'devops' tem 6)")
    args = ap.parse_args()

    total = 0
    for sigla in [s.strip().upper() for s in args.repos.split(",") if s.strip()]:
        nome = COURSES.get(sigla)
        if not nome:
            print(f"[skip] sigla desconhecida: {sigla}")
            continue
        repo = Path(GITHUB_DIR) / nome
        suspeitos = audita_curso(repo, args.min_chars)
        print(f"\n== {sigla} ({nome}): {len(suspeitos)} suspeito(s)")
        for s in suspeitos:
            print(f"   {s['id']}: atribuida={s['atribuida']} (fora dos headings); "
                  f"headings citam irma(s): {', '.join(s['irmas_em_heading'])}")
        total += len(suspeitos)
    print(f"\nTOTAL: {total} suspeito(s) — triagem humana; flag nao significa erro.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
