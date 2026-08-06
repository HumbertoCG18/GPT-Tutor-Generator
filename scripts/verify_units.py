"""verify_units — guard de regua: unidade nunca encolhe em silencio (fio subject_profile, Task 4).

Compara, por repo, unidades do PLANO DE ENSINO (parser: SubjectStore.find_by_repo_root ->
_parse_units_from_teaching_plan; fallback content/curated/plano.md se o perfil nao tem
teaching_plan) vs unidades presentes no INDICE persistido
(course/.timeline_index.json, distinct unit_slug/auto_unit_slug). Promocao do script de
sonda da Task 2 (verify_units_5cursos.py).

Uma PERDA (slug no parser que nao esta no indice) ja registrada em
tests/fixtures/eval/units_baseline.json = WARN, exit 0 (fato conhecido; a cura,
fio Task 3, atualiza o baseline quando resolve). Uma perda NOVA (fora do baseline)
= FAIL, exit != 0 -- e exatamente o bug que motivou este guard
(docs/reports/2026-08-05-unit-sources-investigacao.md): reprocess sem subject_profile
derruba unidades do indice sem nenhum log.

READ-ONLY: json.load puro, nao escreve nada em repo nenhum.

Uso:
    python scripts/verify_units.py <repo_root> [<repo_root> ...] [--baseline PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore  # noqa: E402
from src.builder.extraction.teaching_plan import (  # noqa: E402
    _parse_units_from_teaching_plan,
    _normalize_unit_slug,
)

DEFAULT_BASELINE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "units_baseline.json"


def parser_units(repo_root: Path, store: SubjectStore) -> tuple[str, list[str]]:
    """-> (fonte, slugs) parseados do teaching_plan vivo (SubjectStore) ou fallback plano.md."""
    profile = store.find_by_repo_root(repo_root)
    plan_text = ""
    source = "nenhum (perfil ausente/plano vazio, sem plano.md)"
    if profile is not None and (profile.teaching_plan or "").strip():
        plan_text = profile.teaching_plan
        source = f"subjects.json ({profile.name})"
    else:
        plano_md = repo_root / "content" / "curated" / "plano.md"
        if plano_md.is_file():
            plan_text = plano_md.read_text(encoding="utf-8")
            source = "content/curated/plano.md (fallback)"
    if not plan_text:
        return source, []
    units = _parse_units_from_teaching_plan(plan_text)
    return source, [_normalize_unit_slug(title) for title, _topics in units]


def index_units(repo_root: Path) -> list[str]:
    """-> unit-slugs distintos persistidos em course/.timeline_index.json (json.load puro)."""
    idx_path = repo_root / "course" / ".timeline_index.json"
    if not idx_path.is_file():
        return []
    try:
        data = json.loads(idx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    slugs: set[str] = set()
    for block in data.get("blocks") or []:
        for key in ("unit_slug", "auto_unit_slug"):
            slug = str(block.get(key) or "").strip()
            if slug:
                slugs.add(slug)
    return sorted(slugs)


def check_repo(repo_root: Path, store: SubjectStore, baseline: dict) -> dict:
    """Verdict puro para um repo. `baseline` ja carregado (sem I/O aqui)."""
    course_key = repo_root.name
    source, parser_slugs = parser_units(repo_root, store)
    idx_slugs = index_units(repo_root)
    missing = sorted(set(parser_slugs) - set(idx_slugs))

    known = (baseline.get("courses") or {}).get(course_key) or {}
    known_missing = set(known.get("missing_slugs") or [])
    new_losses = sorted(set(missing) - known_missing)

    if not missing:
        status = "OK"
    elif new_losses:
        status = "FAIL"
    else:
        status = "WARN"

    return {
        "course": course_key,
        "source": source,
        "parser_n": len(parser_slugs),
        "index_n": len(idx_slugs),
        "missing_slugs": missing,
        "new_losses": new_losses,
        "status": status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repos", nargs="+", help="repo_root(s) do(s) curso(s) a verificar")
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="path do units_baseline.json")
    args = parser.parse_args(argv)

    baseline_path = Path(args.baseline)
    baseline: dict = {}
    if baseline_path.is_file():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    store = SubjectStore()
    exit_code = 0
    for raw_repo in args.repos:
        repo_root = Path(raw_repo)
        if not repo_root.is_dir():
            print(f"ERRO: repo nao encontrado: {repo_root}", file=sys.stderr)
            exit_code = 2
            continue
        result = check_repo(repo_root, store, baseline)
        print(
            f"{result['course']:36} parser={result['parser_n']:<3} indice={result['index_n']:<3} "
            f"{result['status']}  (fonte parser: {result['source']})"
        )
        if result["status"] == "FAIL":
            print(f"  FAIL perda NOVA (fora do baseline): {result['new_losses']}", file=sys.stderr)
            exit_code = 2
        elif result["status"] == "WARN":
            print(f"  WARN perda ja conhecida (baseline): {result['missing_slugs']}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
