"""Regua entry->unidade. Roda o scorer de unidade pelo caminho de producao.

A verdade nao precisa de rotulo novo: e a composicao de dois golds JA APROVADOS.

    docs/reports/ground_truth_<C>.csv   entry  -> true_block_uuid
    tests/fixtures/eval/gold_units_<C>.csv    block_uuid -> true_unit
    =>                                   entry  -> true_unit

CAVEAT: a verdade e a unidade do bloco TEMPORAL. Material transversal (uma serie
de laboratorio entregue ao longo do semestre) tem unidade de COBERTURA diferente
da temporal por design — nesses cursos a regua SUPERESTIMA o erro. Ver
`docs/reports/2026-08-18-achados-eixo-unidade.md`, achado A-3.

Uso:
    python scripts/eval_entry_unit.py                 # os 5 cursos
    python scripts/eval_entry_unit.py --course SO
    python scripts/eval_entry_unit.py --json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.engine import (  # noqa: E402
    _auto_map_entry_unit,
    _build_file_map_unit_index_from_course,
    _entry_markdown_text_for_file_map,
    _iter_content_taxonomy_topics,
)
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile  # noqa: E402

GITHUB_DIR = ROOT.parent
COURSES = {
    "MF": "Metodos-Formais-Tutor",
    "SO": "Sistemas-Operacionais-Tutor",
    "IA": "Inteligencia-Artifical-Tutor",
    "ES2": "Engenharia-Software-2-Tutor",
    "TCC": "TCC-Tutor",
}


def _load_truth(sigla: str) -> dict:
    """entry_id -> true_unit, via ground_truth |><| gold_units."""
    gold_units = ROOT / "tests" / "fixtures" / "eval" / f"gold_units_{sigla}.csv"
    ground_truth = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
    if not (gold_units.exists() and ground_truth.exists()):
        return {}
    unit_by_uuid = {
        (row.get("block_uuid") or "").strip(): (row.get("true_unit") or "").strip()
        for row in csv.DictReader(gold_units.open(encoding="utf-8-sig"))
        if (row.get("true_unit") or "").strip()
    }
    truth = {}
    for row in csv.DictReader(ground_truth.open(encoding="utf-8-sig")):
        if (row.get("scorable") or "").strip().lower() != "yes":
            continue
        unit = unit_by_uuid.get((row.get("true_block_uuid") or "").strip())
        if unit:
            truth[row["id"]] = unit
    return truth


def score_course(sigla: str, repo_name: str, store: SubjectStore) -> dict:
    repo = GITHUB_DIR / repo_name
    manifest_path = repo / "manifest.json"
    truth = _load_truth(sigla)
    if not manifest_path.exists() or not truth:
        return {"curso": sigla, "erro": "sem manifest ou sem rotulos"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Perfil resolvido OU aborta: sem ele o unit_index cai no fallback repo-derived
    # e a medicao fica invalida (licao da sessao 2026-08-18).
    profile = store.find_by_repo_root(repo)
    if profile is None:
        return {"curso": sigla, "erro": "perfil nao resolvido — medicao seria invalida"}

    course_meta = {**(manifest.get("course") or {}), "_repo_root": repo}
    unit_index = _build_file_map_unit_index_from_course(course_meta, profile)
    if not unit_index:
        return {"curso": sigla, "erro": "unit_index vazio"}
    topic_index = _iter_content_taxonomy_topics(load_internal_content_taxonomy(repo) or {})
    # learned_unit_boosts: producao passa (resolver_apply.py:225). Omitir
    # inflava a medicao em ~5 pontos e produziu um sweep de gate invalido
    # (2026-08-19) — reproduzir pelo caminho REAL, nao pelo aproximado.
    try:
        tag_profile = load_tag_profile(repo / "course")
    except Exception:
        tag_profile = None

    n = certo = sem_resposta = confiante_errado = bruto = 0
    erros = []
    for entry in manifest.get("entries") or []:
        entry_id = str(entry.get("id") or "")
        if not _is_material(entry) or entry_id not in truth:
            continue
        n += 1
        want = truth[entry_id]
        markdown = _entry_markdown_text_for_file_map(repo, entry)
        learned = build_learned_unit_boosts(tag_profile, entry) if tag_profile else {}
        match = _auto_map_entry_unit(entry, unit_index, markdown, topic_index,
                                     learned_unit_boosts=learned)
        bruto += match.slug == want
        if match.ambiguous or match.confidence < T.UNIT_TAG:
            sem_resposta += 1
            if match.slug == want:
                erros.append({"id": entry_id, "kind": "perdido-no-gate",
                              "conf": round(float(match.confidence), 2), "unit": want})
        elif match.slug == want:
            certo += 1
        else:
            confiante_errado += 1
            erros.append({"id": entry_id, "kind": "confiante-e-errado",
                          "conf": round(float(match.confidence), 2),
                          "got": match.slug, "want": want})
    return {"curso": sigla, "n": n, "bruto": bruto, "certo": certo,
            "sem_resposta": sem_resposta, "confiante_errado": confiante_errado,
            "erros": erros}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", help="sigla (MF/SO/IA/ES2/TCC); omitido = todos")
    parser.add_argument("--json", action="store_true", help="saida JSON")
    args = parser.parse_args(argv[1:])

    alvos = {args.course.upper(): COURSES[args.course.upper()]} if args.course else COURSES
    store = SubjectStore()
    resultados = [score_course(s, r, store) for s, r in alvos.items()]

    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
        return 0

    tot = {k: 0 for k in ("n", "bruto", "certo", "sem_resposta", "confiante_errado")}
    print(f"{'curso':6}{'n':>5}{'bruto':>7}{'certo':>7}{'sem_resp':>10}{'conf-ERRADO':>13}")
    for r in resultados:
        if r.get("erro"):
            print(f"{r['curso']:6}  {r['erro']}")
            continue
        for k in tot:
            tot[k] += r[k]
        print(f"{r['curso']:6}{r['n']:>5}{r['bruto']:>7}{r['certo']:>7}"
              f"{r['sem_resposta']:>10}{r['confiante_errado']:>13}")
    if tot["n"]:
        print(f"{'TOTAL':6}{tot['n']:>5}{tot['bruto']:>7}{tot['certo']:>7}"
              f"{tot['sem_resposta']:>10}{tot['confiante_errado']:>13}")
        print(f"\ncerto {tot['certo']/tot['n']:.0%} · sem resposta {tot['sem_resposta']/tot['n']:.0%}"
              f" · confiante-e-errado {tot['confiante_errado']/tot['n']:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
