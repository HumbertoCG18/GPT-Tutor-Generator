#!/usr/bin/env python3
"""FASE 5 — prova TIER-2 (janela-de-prazo): 8 rows out-of-scope do gold MF.

Universo DECLARADO: rows scorable==yes com is_out_of_disamb_scope(entry)==True
(8 rows: t1/t2/t1-thy/revisao-p1-gabarito/plano/eth2/aws/archive). Campo medido =
atribuicao EFETIVA pos-motor flag-ON: temporal_block_id se existir, senao
computed_block_id (ambos resolvidos a display via ctx.block_by_ref).

Modos (auto-detectados):
  baseline-only  nenhum card do card map tem assign_dues -> exige acc == BASELINE (1/8)
  target         algum card tem assign_dues             -> exige acc >= TARGET (4/8) e cw == 0

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.
"""
from __future__ import annotations

import argparse
import copy
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.apply import apply_anchor_engine        # noqa: E402
from src.builder.routing.motor.context import build_motor_context      # noqa: E402
from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope  # noqa: E402
from fase0_prova_motor_MF import _md_text, true_of                     # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
BASELINE = (1, 8)   # fracao exata: funil hoje (so revisao-p1-gabarito)
TARGET = (4, 8)     # fracao exata: + t1, t2, t1-thy via due-window


def _load_manifest_entries(repo: Path) -> list:
    import json
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return m.get("files") or m.get("entries") or []


def _effective_display(e: dict, ctx) -> str:
    # Espelha a producao (resolve_temporal_block -> resolve_effective_block):
    # temporal vence; sem temporal, PINO MANUAL vence computed. O motor limpa
    # temporal_* em entry pinada (apply.py:73-75) exatamente para o leitor
    # cair no manual - a regua tem que cair igual.
    ref = str(e.get("temporal_block_id") or "").strip()
    if not ref:
        ref = str(e.get("manual_timeline_block_id") or "").strip()
    if not ref:
        ref = str(e.get("computed_block_id") or "").strip()
    if not ref:
        return ""
    block = ctx.block_by_ref(ref)
    return str((block or {}).get("id") or ref)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    ctx = build_motor_context(args.repo, "Metodos Formais")
    if not ctx.blocks:
        print("FAIL: contexto sem blocos"); return 1
    entries = copy.deepcopy(_load_manifest_entries(args.repo))
    apply_anchor_engine(entries, args.repo, "Metodos Formais",
                        enabled=True, voter=None, markdown_fn=lambda e: _md_text(args.repo, e))

    rows = [r for r in csv.DictReader(open(args.gold, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    byid = {str(e.get("id")): e for e in entries}
    universe, ok, cw = [], 0, 0
    for r in rows:
        e = byid.get(r["id"])
        if e is None or not is_out_of_disamb_scope(e):
            continue
        universe.append(r["id"])
        pred = _effective_display(e, ctx)
        truth = true_of(ctx, r)
        hit = (pred == truth)
        ok += int(hit)
        if (str(e.get("temporal_block_band") or "") == "alta"
                and not e.get("temporal_block_flag") and not hit):
            cw += 1
        print(f"  {r['id']:38s} pred={pred or '-':10s} true={truth:10s} {'OK' if hit else 'X'}")

    n = len(universe)
    has_dues = any((v or {}).get("assign_dues")
                   for v in (ctx.card_block_map or {}).values() if isinstance(v, dict))
    mode = "target" if has_dues else "baseline-only"
    print(f"\nuniverso={n} rows out-of-scope · modo={mode} · acc={ok}/{n} · confident-wrong={cw}")

    if n != BASELINE[1]:
        print(f"FAIL: universo {n} != {BASELINE[1]} declarado (gold mudou? re-declarar)"); return 1
    if mode == "baseline-only":
        want = BASELINE[0]
        verdict = (ok == want)
        print("assign_dues AUSENTE -> baseline-only (nao conta como PASS do alvo)")
        print(f"{'PASS' if verdict else 'FAIL'}: acc {ok}/{n} vs baseline exigido {want}/{n}")
        return 0 if verdict else 1
    verdict = (ok >= TARGET[0]) and (cw == 0)
    print(f"{'PASS' if verdict else 'FAIL'}: acc {ok}/{n} vs piso {TARGET[0]}/{TARGET[1]} · cw={cw} (exigido 0)")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
