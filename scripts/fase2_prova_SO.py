#!/usr/bin/env python3
"""FASE 2 — prova do provider P3 (SO data-no-nome) vs ground_truth_SO.csv (READ-ONLY).

Números do aceite (spec §6): cobertura ~45%, data->exatamente 1 bloco (0 colisão),
confiante-errado 0 no escopo P3. Reporta tb acurácia par-colapsada vs baseline
do funil (47.4%). NÃO muta manifest/artefato. A acurácia/matriz é WHOLE-CASCADE
por design (padrão dos probes FASE 0/1); a linha 'providers' do output denuncia
contaminação de outro provider. Uso:
  python scripts/fase2_prova_SO.py [--repo PATH] [--gold CSV]
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
from src.builder.routing.motor.window_provider import (                # noqa: E402
    provider_date, resolve_window,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Sistemas-Operacionais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_SO.csv"
PISO_COBERTURA = 0.40      # spec ~45%; medido 20/42=48% bruto
BASELINE_FUNIL = 0.474     # spec §2: SO 47.4% (18/38) — motor deve >=
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


def build_context(repo: Path) -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    m = _load(repo, "manifest.json")
    course_name = str(((m.get("course") or {}).get("course_name")) or "")
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index={}, course_name=course_name,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    ctx = build_context(args.repo)
    manifest = _load(args.repo, "manifest.json")
    entries = {str(e.get("id")): e for e in manifest.get("entries") or []}
    with args.gold.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("scorable") or "") == "yes"]

    engine = AnchorEngine()
    cobertos, colisoes, contidos, fora = [], [], [], []
    results, cw, matriz = {}, [], defaultdict(int)
    prov_count = defaultdict(int)
    for r in rows:
        e = entries.get(r["id"])
        if e is None:
            continue
        win = provider_date(e, ctx)
        if win:
            cobertos.append(r["id"])
            if len(win) > 1:
                colisoes.append((r["id"], win))
            (contidos if r["true_block_id"] in win else fora).append(r["id"])
        if is_out_of_disamb_scope(e):
            continue
        d = engine.resolve(e, ctx, _md_text(args.repo, e))
        if d is None:
            continue
        pred = str((ctx.block_by_ref(d.block_ref) or {}).get("id") or d.block_ref)
        prov_count[d.provider or "?"] += 1
        ok = pred == r["true_block_id"]
        results[r["id"]] = ok
        matriz[("alta" if d.band == "alta" else "resto", "ok" if ok else "err")] += 1
        if d.band == "alta" and not ok and not d.flag:
            cw.append((r["id"], pred, r["true_block_id"], d.provider))

    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    acc = sum(int(all(v)) for v in by_pair.values()) / max(total, 1)
    cob = len(cobertos) / max(len(rows), 1)

    print("=" * 70)
    print(f"FASE 2/P3 — SO  repo={args.repo.name}  escopo={len(rows)} rows gold")
    print(f"  cobertura P3: {len(cobertos)}/{len(rows)} = {cob:.1%} (piso {PISO_COBERTURA:.0%})")
    print(f"  colisões (data em >1 bloco): {len(colisoes)} {colisoes}")
    print(f"  contenção da janela P3: {len(contidos)} in / {len(fora)} out; out={fora}")
    print(f"  acurácia motor (par-colapsada, com-janela): {acc:.1%} de {total} pares "
          f"(baseline funil {BASELINE_FUNIL:.1%})")
    print(f"  matriz gate: {dict(matriz)}")
    print(f"  providers das decisões: {dict(prov_count)}")
    print(f"  confiante-e-errado (band alta, sem flag): {len(cw)} {cw}")
    ok_cob = cob >= PISO_COBERTURA
    ok_col = not colisoes
    ok_cw = not cw
    verdict = ok_cob and ok_col and ok_cw
    print("=" * 70)
    print(f"VEREDITO FASE 2/P3: {'PASS' if verdict else 'FAIL'} "
          f"(cobertura={ok_cob} colisao0={ok_col} confErrado0={ok_cw})")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
