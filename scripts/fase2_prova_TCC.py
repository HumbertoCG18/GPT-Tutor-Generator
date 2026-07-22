#!/usr/bin/env python3
"""FASE 2 — prova do provider P4 (TCC topic-bridge) vs ground_truth_TCC.csv (READ-ONLY).

Números do aceite (spec §6): >=4/5 pinos manuais reproduzidos (janela P4 acha o
bloco do pino SEM olhar o manual), cobertura >26%, resíduo cai pro TIER 3 SEM
errar confiante. F-TCC: o N de "Semana N" NUNCA vira janela. NÃO muta manifest/artefato.
A acurácia/matriz é WHOLE-CASCADE por design (padrão dos probes FASE 0/1); a linha
'providers' do output denuncia a mistura manual/topic no headline. Uso:
  python scripts/fase2_prova_TCC.py [--repo PATH] [--gold CSV]
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
from src.builder.routing.motor.anchor_engine import (                  # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)
from src.builder.routing.motor.window_provider import provider_topic   # noqa: E402
from fase0_prova_motor_MF import true_of  # gold uuid-first (F4 item 6)  # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "TCC-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_TCC.csv"
PISO_PINOS = 4             # de 5 (spec §6)
PISO_COBERTURA = 0.26      # deve SUPERAR o só-manual
BASELINE_FUNIL = 0.560     # spec §2: TCC 56.0% (14/25)
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    tl = _load(args.repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(args.repo, "course/.card_block_map.json")
    manifest = _load(args.repo, "manifest.json")
    course_name = str(((manifest.get("course") or {}).get("course_name")) or "")

    # 1) Pinos: P4 SEM o card map (senão P1 responde pelo pino).
    ctx_sem_manual = MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index={}, course_name=course_name)
    manuais = {k: v for k, v in cbm.items() if str(v.get("source") or "") == "manual"}
    reproduzidos, contidos_total = [], []
    for card, info in sorted(manuais.items()):
        win = provider_topic({"source_section": card}, ctx_sem_manual)
        alvo = [str(b) for b in info.get("block_ids") or []]
        inter = sorted(set(win) & set(alvo))
        if inter:
            reproduzidos.append(card)
        if alvo and set(alvo) <= set(win):
            contidos_total.append(card)
        print(f"  pino {'OK ' if inter else 'ERR'} '{card}' manual={alvo} p4={win}")

    # 2) Cobertura + acurácia no gold com a cascata completa.
    ctx = MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index={}, course_name=course_name)
    entries = {str(e.get("id")): e for e in manifest.get("entries") or []}
    with args.gold.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("scorable") or "") == "yes"]

    engine = AnchorEngine()
    com_janela, results, cw = [], {}, []
    prov_count = defaultdict(int)
    results_by_prov = defaultdict(list)
    for r in rows:
        e = entries.get(r["id"])
        if e is None:
            continue
        if provider_topic(e, ctx):
            com_janela.append(r["id"])
        if is_out_of_disamb_scope(e):
            continue
        d = engine.resolve(e, ctx, _md_text(args.repo, e))
        if d is None:
            continue
        pred = str((ctx.block_by_ref(d.block_ref) or {}).get("id") or d.block_ref)
        ok = pred == true_of(ctx, r)
        prov_count[d.provider or "?"] += 1
        results_by_prov[d.provider or "?"].append(ok)
        results[r["id"]] = ok
        if d.band == "alta" and not ok and not d.flag:
            cw.append((r["id"], pred, true_of(ctx, r), d.provider))

    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    acc = sum(int(all(v)) for v in by_pair.values()) / max(total, 1)
    cob = len(com_janela) / max(len(rows), 1)

    print("=" * 70)
    print(f"FASE 2/P4 — TCC  repo={args.repo.name}  escopo={len(rows)} rows gold")
    print(f"  pinos reproduzidos (interseção): {len(reproduzidos)}/{len(manuais)} "
          f"(piso {PISO_PINOS}); contenção total: {len(contidos_total)}/{len(manuais)}")
    print(f"  cobertura P4: {len(com_janela)}/{len(rows)} = {cob:.1%} (piso >{PISO_COBERTURA:.0%})")
    print(f"  acurácia motor (par-colapsada, com-janela): {acc:.1%} de {total} pares "
          f"(baseline funil {BASELINE_FUNIL:.1%})")
    print(f"  providers das decisões: {dict(prov_count)}")
    for prov in sorted(results_by_prov):
        oks = results_by_prov[prov]
        print(f"    acc {prov}: {sum(oks)}/{len(oks)} = {sum(oks)/len(oks):.1%} (por caso, não par-colapsada)")
    print(f"  confiante-e-errado: {len(cw)} {cw}")
    ok_p = len(reproduzidos) >= PISO_PINOS
    ok_c = cob > PISO_COBERTURA
    ok_w = not cw
    verdict = ok_p and ok_c and ok_w
    print("=" * 70)
    print(f"VEREDITO FASE 2/P4: {'PASS' if verdict else 'FAIL'} "
          f"(pinos={ok_p} cobertura={ok_c} confErrado0={ok_w})")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
