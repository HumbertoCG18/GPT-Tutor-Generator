"""Gera o golden set real do Metodos-Formais (P0 da reforma da atribuicao).

Cruza o manifest real com a secao FISICA de cada arquivo no stash e o gabarito
card_block_map. Ground truth ancorado no cronograma: secao com 1 bloco no
gabarito vira expected automatico; 2+ ou sem gabarito fica null para decisao
humana (preservada em re-runs via merge_manual_decisions).

Utilitario de dados (caminhos da maquina do Humberto como constantes) — nao e
codigo de producao. Spec: docs/superpowers/specs/2026-06-12-atribuicao-p0-*.md

Uso:
    python scripts/build_golden_metodos_formais.py            # grava a fixture
    python scripts/build_golden_metodos_formais.py --dry-run  # so imprime
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_TUTOR = Path("C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor")
STASH = Path("C:/Users/Humberto/Desktop/Moodle/metodos-formais-para-computacao")
OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "metodos_formais_golden.json"

_EXCLUDED_CATEGORIES = {"bibliografia", "referencias", "references", "cronograma"}
_MARKDOWN_CHARS = 1500


def stash_section_index(stash_dir: Path) -> dict:
    """{basename.casefold(): secao fisica} so para basenames de secao unica."""
    secs: dict = defaultdict(set)
    for f in stash_dir.rglob("*"):
        if f.is_file() and f.name != "_ARQUIVOS_DO_CARD.txt":
            secs[f.name.casefold()].add(f.relative_to(stash_dir).parts[0])
    return {k: next(iter(v)) for k, v in secs.items() if len(v) == 1}


def case_for_entry(entry: dict, sec_index: dict, card_map: dict) -> dict:
    """Um caso do golden a partir de uma entry do manifest real."""
    base = Path(str(entry.get("source_path") or "")).name.casefold()
    section = sec_index.get(base, "")
    case = {
        "id": str(entry.get("id") or ""),
        "title": str(entry.get("title") or ""),
        "category": str(entry.get("category") or ""),
        # S4: SO as auto_tags `ferramenta:` do manifest real (alimentam o sinal
        # de ferramenta do scorer via _entry_from_case do harness). As demais
        # auto_tags computadas (unit:/bloco:/tipo:) sao PREDICOES de runs
        # anteriores — carrega-las contamina o eval (vazamento pelo canal
        # legado de auto_tags: 40/48 -> 37/48 medido em 12/06) e nao representa
        # a primeira atribuicao em producao.
        "auto_tags": [
            str(t) for t in (entry.get("auto_tags") or [])
            if str(t).strip().startswith("ferramenta:")
        ],
        # S4b: basename do arquivo fonte real — o harness deriva a ferramenta
        # da EXTENSÃO (.thy -> isabelle, .dfy -> dafny) via raw_target.
        "raw_target": Path(str(entry.get("source_path") or "")).name,
        "source_section_real": section,
        "unit_guess": {
            "slug": str(entry.get("computed_unit_slug") or ""),
            "confidence": float(entry.get("unit_match_confidence") or 0.0),
            "ambiguous": False,
        },
        "markdown": "",
        "expected_block_id": None,
        "expected_origin": "",
        "candidates": [],
        "note": "",
    }
    if entry.get("manual_timeline_block_id"):
        case["expected_origin"] = "excluido"
        case["note"] = "bloco manual — nao mede o scorer"
        return case
    category = case["category"].strip().lower()
    if category in _EXCLUDED_CATEGORIES:
        case["expected_origin"] = "excluido"
        case["note"] = f"categoria fora da timeline: {category}"
        return case
    if not section:
        case["expected_origin"] = "excluido"
        case["note"] = "sem secao fisica derivavel (fora do stash ou basename ambiguo)"
        return case
    block_ids = list((card_map.get(section) or {}).get("block_ids") or [])
    if len(block_ids) == 1:
        case["expected_block_id"] = block_ids[0]
        case["expected_origin"] = "gabarito_1bloco"
    elif len(block_ids) >= 2:
        case["expected_origin"] = "precisa_decisao"
        case["candidates"] = block_ids
    else:
        case["expected_origin"] = "sem_gabarito"
    return case


def attach_markdown(case: dict, entry: dict, repo: Path) -> None:
    """Primeiros _MARKDOWN_CHARS do markdown base da entry (sinal pro scorer)."""
    rel = str(entry.get("base_markdown") or "")
    if not rel:
        return
    p = repo / rel
    if p.is_file():
        try:
            case["markdown"] = p.read_text(encoding="utf-8", errors="replace")[:_MARKDOWN_CHARS]
        except OSError:
            pass


def merge_manual_decisions(old_cases: list, new_cases: list) -> None:
    """Preserva expected_block_id preenchido a mao em re-runs (muta new_cases).

    Chave (id, category): o manifest real tem ids duplicados entre categorias
    (ex. 'introducao' em material-de-aula E codigo-professor)."""
    decided = {
        (str(c.get("id")), str(c.get("category") or "")): c
        for c in old_cases or []
        if c.get("expected_block_id")
        and c.get("expected_origin") in ("precisa_decisao", "sem_gabarito")
    }
    for case in new_cases:
        old = decided.get((str(case.get("id")), str(case.get("category") or "")))
        if old and case.get("expected_origin") in ("precisa_decisao", "sem_gabarito"):
            case["expected_block_id"] = old["expected_block_id"]
            case["note"] = str(old.get("note") or "decisao humana preservada")


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dry = "--dry-run" in argv
    manifest = json.loads((REPO_TUTOR / "manifest.json").read_text(encoding="utf-8"))
    ti = json.loads((REPO_TUTOR / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    card_map = json.loads((REPO_TUTOR / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    sec_index = stash_section_index(STASH)

    cases = []
    for entry in manifest.get("entries") or []:
        case = case_for_entry(entry, sec_index, card_map)
        if case["expected_origin"] != "excluido":
            attach_markdown(case, entry, REPO_TUTOR)
        cases.append(case)
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        merge_manual_decisions(old.get("cases") or [], cases)

    gold = {
        "subject": "Metodos-Formais",
        "generated_from": {
            "manifest": str(REPO_TUTOR / "manifest.json"),
            "timeline_index": str(REPO_TUTOR / "course" / ".timeline_index.json"),
            "card_block_map": str(REPO_TUTOR / "course" / ".card_block_map.json"),
        },
        "card_block_map": card_map,
        "timeline": {"blocks": ti.get("blocks") or []},
        "cases": cases,
    }
    pend = [c for c in cases
            if c["expected_origin"] in ("precisa_decisao", "sem_gabarito")
            and not c["expected_block_id"]]
    excl = sum(1 for c in cases if c["expected_origin"] == "excluido")
    print(f"casos: {len(cases)}  pendentes (decisao humana): {len(pend)}  excluidos: {excl}")
    for c in pend:
        cands = f"  candidatos: {', '.join(c['candidates'])}" if c["candidates"] else ""
        print(f"  - {c['id']:40} secao={c['source_section_real']}{cands}")
    if not dry:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(gold, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"gravado: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
