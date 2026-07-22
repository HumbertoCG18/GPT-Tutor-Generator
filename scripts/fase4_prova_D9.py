#!/usr/bin/env python3
"""FASE 4 — prova D9: apply_anchor_engine vs manifest MF (READ-ONLY no repo).

Número do aceite (spec §7 FASE 4): flag-OFF ⇒ byte-idêntico; flag-ON ⇒
computed_* inalterado, só temporal_*; pino manual nunca sobrescrito;
dup-divergence 0; gold MF pair-colapsado sem regressão:
  det (voter=None):        acc >= 82.8% e confiante-errado <= 1  (baseline F0)
  voter all-cache (cap=0): acc >= 87.9% e confiante-errado == 0  (baseline F3)

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.
Uso: python scripts/fase4_prova_D9.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine   # noqa: E402
from src.builder.routing.motor.context import build_motor_context               # noqa: E402
from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope      # noqa: E402
from src.builder.routing.motor.llm_vote import LlmVoter                         # noqa: E402
from fase0_prova_motor_MF import _md_text, collapse, display_of, true_of        # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
CACHE_F3 = ROOT / "docs" / "reports" / "material_curation_MF.json"
ACC_DET_MIN, CW_DET_MAX = 48 / 58, 1   # fração exata baseline F0 (precedente F1: evita FAIL espúrio de float)
ACC_LLM_MIN, CW_LLM_MAX = 51 / 58, 0   # fração exata baseline F3


def _gold_check(entries, ctx, gold_path, repo) -> tuple:
    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    byid = {str(e.get("id")): e for e in entries}
    res, cw = {}, 0
    for r in rows:
        e = byid.get(r["id"])
        if e is None:
            continue
        if is_out_of_disamb_scope(e):
            # universo dos pisos 82.8/87.9 = escopo-disamb de fase0/fase3 (58 rows);
            # TIER-2 (trabalhos/provas/TDE) fica no funil por design — dívida F5.
            continue
        temporal = str(e.get("temporal_block_id") or "").strip()
        block = ctx.block_by_ref(temporal) if temporal else None
        pred = str((block or {}).get("id") or temporal) if temporal else ""
        if not pred:
            # sem temporal: funil-piso responde (computed via display)
            comp = ctx.block_by_ref(str(e.get("computed_block_id") or ""))
            pred = str((comp or {}).get("id") or e.get("computed_block_id") or "")
        truth = true_of(ctx, r)
        res[r["id"]] = (pred == truth)
        if (e.get("temporal_block_band") == "alta"
                and not e.get("temporal_block_flag") and pred != truth):
            cw += 1
    ok, tot = collapse(res, rows)
    return ok, tot, cw


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
    entries0 = man.get("entries") or []
    ctx = build_motor_context(repo, course_name)
    md_fn = lambda e: _md_text(repo, e)  # noqa: E731

    # 1) flag-OFF byte-idêntico
    off = copy.deepcopy(entries0)
    apply_anchor_engine(off, repo, course_name, enabled=False)
    p_off = off == entries0
    print(f"flag-OFF byte-idêntico: {p_off}")

    # 2) flag-ON determinístico (voter=None)
    on = copy.deepcopy(entries0)
    apply_anchor_engine(on, repo, course_name, markdown_fn=md_fn)
    p_computed = all(
        {k: v for k, v in a.items() if not k.startswith("temporal_")}
        == {k: v for k, v in b.items() if not k.startswith("temporal_")}
        for a, b in zip(on, copy.deepcopy(entries0))
    )
    pins = [e for e in on if str(e.get("manual_timeline_block_id") or "").strip()
            and ctx.block_by_ref(str(e.get("manual_timeline_block_id")))]
    p_pins = all(all(k not in e for k in TEMPORAL_KEYS) for e in pins)
    from src.builder.routing.motor.llm_vote import content_key
    groups: dict = {}
    for e in on:
        groups.setdefault(content_key(e, repo), set()).add(
            str(e.get("temporal_block_id") or ""))
    p_dup = all(len(v) == 1 for v in groups.values())
    ok_d, tot_d, cw_d = _gold_check(on, ctx, gold_path, repo)
    acc_d = 100.0 * ok_d / tot_d if tot_d else 0.0
    p_det = (ok_d / tot_d if tot_d else 0.0) >= ACC_DET_MIN and cw_d <= CW_DET_MAX
    print(f"flag-ON det: computed intacto={p_computed} pinos intactos={p_pins} "
          f"({len(pins)} pinos) dup-div0={p_dup}")
    print(f"  gold pair-colapsado: {ok_d}/{tot_d} = {acc_d:.1f}% "
          f"(piso {100 * ACC_DET_MIN:.1f}) conf-errado={cw_d} (max {CW_DET_MAX})")

    # 3) flag-ON com voter ALL-CACHE (cap=0: zero chamadas API; cache copiado)
    p_llm = True
    if CACHE_F3.is_file():
        with tempfile.TemporaryDirectory() as td:
            tmp_cache = Path(td) / "material_curation.json"
            shutil.copy(CACHE_F3, tmp_cache)
            voter = LlmVoter({}, cache_path=tmp_cache, repo_dir=repo, cap=0)
            lv = copy.deepcopy(entries0)
            apply_anchor_engine(lv, repo, course_name, voter=voter, markdown_fn=md_fn)
            ok_l, tot_l, cw_l = _gold_check(lv, ctx, gold_path, repo)
        acc_l = 100.0 * ok_l / tot_l if tot_l else 0.0
        p_llm = (ok_l / tot_l if tot_l else 0.0) >= ACC_LLM_MIN and cw_l <= CW_LLM_MAX
        print(f"flag-ON voter all-cache: {ok_l}/{tot_l} = {acc_l:.1f}% "
              f"(piso {100 * ACC_LLM_MIN:.1f}) conf-errado={cw_l} (max {CW_LLM_MAX}) "
              f"chamadas API={voter.calls} (esperado 0)")
    else:
        print(f"AVISO: cache F3 ausente ({CACHE_F3.name}); passo voter pulado")

    ok = p_off and p_computed and p_pins and p_dup and p_det and p_llm
    print("=" * 70)
    print(f"VEREDITO FASE 4: {'PASS' if ok else 'FAIL'} "
          f"(off={p_off} computed={p_computed} pinos={p_pins} dup={p_dup} "
          f"det={p_det} voter={p_llm})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
