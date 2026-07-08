#!/usr/bin/env python3
"""FASE 0 — prova READ-ONLY do MOTOR real vs ground_truth_MF.csv.

Reproduz a régua do MARCO 0 (colapso de par, escopo-disamb) chamando o motor de
produção (src/builder/routing/motor). Verifica:
  - escopo-disamb par-colapsado >= 59.7% (piso MARCO 0 Config A' — HARD)
  - contenção fora da janela <= BASELINE_CONTENCAO_FORA (baseline consciente)
  - confiante-e-errado (band alta + errado) <= BASELINE_CONFIANTE_ERRADO
    (baseline consciente — dívida FASE 1; regressão acima = FAIL)
NÃO muta manifest/artefato. Uso:
  python scripts/fase0_prova_motor_MF.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# permite rodar de qualquer cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.anchor_engine import (                 # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_MF.csv"
PISO = 59.7
# Baselines renegociados na FASE 1 (calibração com recall, 2026-07-07):
# confiante-errado 3 (era 7 na FASE 0: -2 poluição nome-do-curso via desconto
# course_name Task 3; -2 via calibração MARGIN_TAU 0.45->0.55 na grade FASE 1
# Task 5 — a redução veio do desconto + da calibração, NÃO do gate
# discriminante Task 4, que não converteu erro nenhum neste corpus e só
# custou 2 falso-alarme). Resíduo final (3): exerciciosdafny2,
# formalizacaoalgoritmos-invarianteslaco, hoare — todos gold discriminante=yes
# same-theme (Dafny/verificação/indução) que o token discriminante não
# resolve; candidatos a TIER 3 (LLM).
BASELINE_CONFIANTE_ERRADO = 3
# contenção-fora = 2: lacuna do card_block_map REAL do repo MF — seção
# "Verificação de Programas" sem bloco-09. Pendência de curadoria USER.
BASELINE_CONTENCAO_FORA = 2
MD_CAP = 6000


def _load(repo: Path, rel: str):
    p = repo / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _md_text(repo: Path, e: dict) -> str:
    for k in ("approved_markdown", "curated_markdown", "base_markdown"):
        rel = str(e.get(k) or "")
        p = repo / rel
        if rel and p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:MD_CAP]
            except OSError:
                pass
    return ""


def build_context(repo: Path, course_name: str = "") -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    lessons = (_load(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index=lessons,
        course_name=course_name,
    )


def display_of(ctx: MotorContext, ref: str) -> str:
    b = ctx.block_by_ref(ref)
    return str((b or {}).get("id") or ref)


def collapse(results: dict, rows: list) -> tuple:
    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    ok = sum(int(all(by_pair[k])) for k in by_pair)
    return ok, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    args = ap.parse_args()
    repo, gold_path = Path(args.repo), Path(args.gold)

    if not repo.is_dir():
        print(f"ERRO: repo MF nao encontrado: {repo}", file=sys.stderr)
        return 2

    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    course_name = str((man.get("course") or {}).get("course_name") or "")
    byid = {}
    for e in man.get("entries") or []:
        byid.setdefault(str(e.get("id")), e)

    ctx = build_context(repo, course_name)
    eng = AnchorEngine()

    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    scope = [r for r in rows
             if byid.get(r["id"]) and not is_out_of_disamb_scope(byid[r["id"]])]

    results: dict = {}
    contencao_fora = []
    confiante_errado = []
    for r in scope:
        rid, true = r["id"], r["true_block_id"]
        e = byid[rid]
        d = eng.resolve(e, ctx, markdown=_md_text(repo, e))
        if d is None:
            pred = r["computed_block_id"] or ""     # funil = piso (D9)
            results[rid] = (pred == true)
            continue
        pred = display_of(ctx, d.block_ref)
        results[rid] = (pred == true)
        if true and true not in [display_of(ctx, w) for w in d.window]:
            contencao_fora.append((rid, true, d.window))
        if d.band == "alta" and pred != true:
            confiante_errado.append((rid, pred, true))

    ok, tot = collapse(results, scope)
    pct = ok / tot * 100 if tot else 0.0
    print("=" * 70)
    print(f"FASE 0 — motor real  repo={repo.name}  escopo-disamb={tot} (par-colapsado)")
    print(f"  escopo-disamb: {ok}/{tot} = {pct:.1f}%   (piso MARCO 0 A' = {PISO}%)")
    print(f"  contenção fora da janela: {len(contencao_fora)} "
          f"(baseline consciente FASE 0 = {BASELINE_CONTENCAO_FORA})")
    for x in contencao_fora:
        print(f"    {x}")
    print(f"  confiante-e-errado (band alta): {len(confiante_errado)} "
          f"(baseline consciente FASE 0 = {BASELINE_CONFIANTE_ERRADO}, dívida FASE 1)")
    for x in confiante_errado:
        print(f"    {x}")
    print("=" * 70)

    ok_number = pct + 1e-9 >= PISO
    ok_conten = len(contencao_fora) <= BASELINE_CONTENCAO_FORA
    ok_conf = len(confiante_errado) <= BASELINE_CONFIANTE_ERRADO
    verdict = ok_number and ok_conten and ok_conf
    print(f"VEREDITO FASE 0: {'PASS' if verdict else 'FAIL'} "
          f"(num={ok_number} conten={ok_conten} conf={ok_conf})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
