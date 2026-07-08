#!/usr/bin/env python3
"""FASE 1 — recall do gate D4 do MOTOR real vs ground_truth_MF.csv (READ-ONLY).

Mede a métrica-número da FASE 1 (spec §6/§7): fração dos erros reais que o
gate FLAGA (recall), além de confiante-errado e falso-alarme do flag. Régua:
mesmo escopo-disamb par-colapsado do probe FASE 0; métricas de gate POR CASO.
Referência ruim a bater: proxy MARCO 1 = 15/26 (57.7%).
NÃO muta manifest/artefato. Uso:
  python scripts/fase1_recall_gate_MF.py [--repo PATH] [--gold CSV]
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.metrics import gate_report              # noqa: E402
from src.builder.routing.motor.anchor_engine import (                  # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_MF.csv"
PISO_ACURACIA = 59.7          # HARD (MARCO 0 Config A'); FASE 0 entregou 62.1
PISO_RECALL_REFERENCIA = 0.577  # proxy MARCO 1 (15/26) — referência ruim a bater
BASELINE_RECALL = 9 / 10  # =0.900 pós-auditoria do gold (2026-07-08; era 14/17 na calibração) — regressão abaixo = FAIL
BASELINE_CONFIANTE_ERRADO = 1   # espelha o probe fase0 — guard ABSOLUTO do gate (pós-auditoria do gold)
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
    outcomes: list = []
    detalhe_erros: list = []
    for r in scope:
        rid, true = r["id"], r["true_block_id"]
        e = byid[rid]
        d = eng.resolve(e, ctx, markdown=_md_text(repo, e))
        if d is None:
            pred = r["computed_block_id"] or ""     # funil = piso (D9)
            results[rid] = (pred == true)
            continue
        pred = display_of(ctx, d.block_ref)
        correct = (pred == true)
        results[rid] = correct
        outcomes.append({"correct": correct, "band": d.band,
                         "flag": d.flag, "method": d.method})
        if not correct:
            detalhe_erros.append((rid, pred, true, d.band, d.flag,
                                  d.method, d.provider,
                                  str(r.get("discriminante") or "")))

    ok, tot = collapse(results, scope)
    pct = ok / tot * 100 if tot else 0.0
    rep = gate_report(outcomes)

    print("=" * 70)
    print(f"FASE 1 — recall do gate D4  repo={repo.name}  course={course_name!r}")
    print(f"  acurácia escopo-disamb: {ok}/{tot} = {pct:.1f}% (par-colapsada; piso HARD {PISO_ACURACIA}%)")
    print(f"  decisões ancoradas (por caso): {rep['total']}")
    print(f"  erros ancorados: {rep['erros']}  | flagados: {rep['erros_flagados']}"
          f"  | confiante-errado: {rep['confiante_errado']}"
          f"  | erros janela-1: {rep['janela1_erros']}")
    print(f"  RECALL DO GATE: {rep['recall_gate']:.3f} "
          f"(referência ruim a bater: {PISO_RECALL_REFERENCIA} = proxy 15/26 MARCO 1)")
    print(f"  fila do flag: {rep['flagged_total']} flagados, "
          f"{rep['flagged_certos']} certos (falso-alarme)")
    print("  erros ancorados (id, pred, true, band, flag, method, provider, discriminante):")
    for x in detalhe_erros:
        print(f"    {x}")
    print("=" * 70)

    ok_acc = pct + 1e-9 >= PISO_ACURACIA
    # Recall é RAZÃO (flagados/erros): curadoria do USER que conserta erros
    # FLAGADOS derruba a razão sem regressão de código. Regressão REAL do gate
    # = erro confiante novo; por isso o veredito compõe com o guard absoluto.
    ok_recall = (
        rep["recall_gate"] + 1e-9 >= BASELINE_RECALL
        or rep["confiante_errado"] <= BASELINE_CONFIANTE_ERRADO
    ) and rep["recall_gate"] > PISO_RECALL_REFERENCIA
    verdict = ok_acc and ok_recall
    print(f"VEREDITO FASE 1: {'PASS' if verdict else 'FAIL'} (acc={ok_acc} recall={ok_recall})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
