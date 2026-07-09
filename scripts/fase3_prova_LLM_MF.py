#!/usr/bin/env python3
"""FASE 3 — prova do TIER 3 (voto LLM) vs ground_truth_MF.csv (READ-ONLY no repo-tutor).

Numero do aceite (spec §7 FASE 3): lift >= +4 acertos no escopo do voto
(flagged ∪ same-theme, com janela e decisao) SEM novo confiante-errado
(band alta + errado, medido GLOBAL) — era +5 no MARCO 1 cru; regras finais:
sem-janela NAO vota. Autoconfianca do LLM ignorada (nunca lida por gate).

Cache: docs/reports/material_curation_MF.json (identidade de conteudo md5;
seed = docs/reports/marco1_votes_MF.json re-chaveado na primeira rodada).
O repo-tutor NAO recebe escrita (disciplina READ-ONLY; sidecar = FASE 4).
Cap=20 chamadas/rodada: escopo maior que o cap -> INCOMPLETO exit 1;
re-rodar acumula cache ate completar.

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.

Uso: python scripts/fase3_prova_LLM_MF.py [--repo PATH] [--gold CSV] [--cap N] [--dry-run]
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
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.anchor_engine import (                   # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)
from src.builder.routing.motor.llm_vote import (                        # noqa: E402
    LlmVoter, build_vote_prompt, detect_same_theme_series,
    import_marco1_seed, save_material_curation,
)
from fase0_prova_motor_MF import (                                      # noqa: E402
    _md_text, build_context, collapse, display_of,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
CACHE = ROOT / "docs" / "reports" / "material_curation_MF.json"
SEED = ROOT / "docs" / "reports" / "marco1_votes_MF.json"
# Piso renegociado com SIGN-OFF do user (2026-07-09), pos-experimento gemini-3.5-flash:
# +4 era derivado do MARCO 1 (modelo 2.5, escopo cru). Medido com 3.5 pinado, 44 votos
# frescos: lift +3, global 82.8%->87.9%, conf-errado 0; variante flagged-only PIOR
# (+2, conf-errado 1) — escopo flagged∪serie confirmado otimo. Regressao futura <+3 = FAIL.
LIFT_MIN = 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--cap", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true", help="monta prompts, nao chama API")
    args = ap.parse_args()
    repo, gold_path = Path(args.repo), Path(args.gold)

    if not repo.is_dir():
        print(f"ERRO: repo MF nao encontrado: {repo}", file=sys.stderr)
        return 2

    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    course_name = str((man.get("course") or {}).get("course_name") or "")
    entries = man.get("entries") or []
    byid = {str(e.get("id")): e for e in entries}
    ctx = build_context(repo, course_name)

    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    scope_rows = [r for r in rows
                  if byid.get(r["id"]) and not is_out_of_disamb_scope(byid[r["id"]])]

    # 1) baseline deterministico + escopo do voto
    eng0 = AnchorEngine()
    series = detect_same_theme_series(entries)
    base = {}                    # rid -> (decision, markdown)
    vote_rows = []
    for r in scope_rows:
        e = byid[r["id"]]
        md = _md_text(repo, e)
        d = eng0.resolve(e, ctx, markdown=md)
        if d is None:
            continue             # sem janela/decisao -> funil; NAO vota (spec §12)
        base[r["id"]] = (d, md)
        if d.flag or r["id"] in series:
            vote_rows.append(r)

    n_flag = sum(1 for r in vote_rows if base[r["id"]][0].flag)
    print(f"FASE 3 — escopo do voto: {len(vote_rows)} rows "
          f"({n_flag} flagged; serie same-theme total={len(series)})")

    if args.dry_run:
        for r in vote_rows[:5]:
            d, md = base[r["id"]]
            print(f"\n===== {r['id']} =====")
            print(build_vote_prompt(byid[r["id"]], d.window, ctx, md)[:900])
        print(f"\n(dry-run: {len(vote_rows)} prompts montaveis; nada chamado)")
        return 0

    # 2) seed do MARCO 1 (so na primeira rodada, cache ainda nao existe)
    if not CACHE.is_file() and SEED.is_file():
        seed = import_marco1_seed(
            json.loads(SEED.read_text(encoding="utf-8")), byid, repo)
        save_material_curation(CACHE, {"version": 1, "votes": seed})
        print(f"  seed MARCO 1 importado: {len(seed)} votos -> {CACHE.name}")

    # 3) rodada com voto (cache acumula entre rodadas)
    cfg_path = Path.home() / ".gpt_tutor_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    voter = LlmVoter(cfg, cache_path=CACHE, repo_dir=repo, cap=args.cap)
    eng1 = AnchorEngine(voter=voter, series_ids=series)

    d_ok = l_ok = 0
    res_det, res_llm = {}, {}
    cw = []
    for r in scope_rows:
        got = base.get(r["id"])
        if got is None:
            continue
        d0, md = got
        e = byid[r["id"]]
        d1 = eng1.resolve(e, ctx, markdown=md)
        pred0 = display_of(ctx, d0.block_ref)
        pred1 = display_of(ctx, d1.block_ref) if d1 else pred0
        ok0, ok1 = pred0 == r["true_block_id"], pred1 == r["true_block_id"]
        res_det[r["id"]], res_llm[r["id"]] = ok0, ok1
        if d1 and d1.band == "alta" and not d1.flag and not ok1:
            cw.append((r["id"], pred1, r["true_block_id"]))
        if r in vote_rows:
            d_ok += ok0
            l_ok += ok1
            mark0, mark1 = ("ok" if ok0 else "X "), ("ok" if ok1 else "X ")
            print(f"  {r['id'][:46]:46} det={pred0:9}{mark0} "
                  f"llm={pred1:9}{mark1} true={r['true_block_id']:9} "
                  f"[{d1.method if d1 else '-'}]")

    pend = [r["id"] for r in vote_rows if not voter.has_vote(byid[r["id"]])]
    lift = l_ok - d_ok
    ok_g, tot_g = collapse(res_llm, scope_rows)

    print("=" * 70)
    print(f"FASE 3/TIER 3 — MF  chamadas API nesta rodada: {voter.calls}  "
          f"erros: {voter.errors}  sem-voto (cap): {voter.skipped_cap}")
    print(f"  escopo do voto: deterministico {d_ok}/{len(vote_rows)} -> "
          f"LLM {l_ok}/{len(vote_rows)}  lift={lift:+d} (piso +{LIFT_MIN})")
    print(f"  global escopo-disamb par-colapsado c/ voto: {ok_g}/{tot_g}")
    print(f"  confiante-e-errado (band alta, global): {len(cw)} {cw}")
    if pend:
        print(f"  INCOMPLETO: {len(pend)} sem voto (cap/erro) — re-rode p/ acumular: {pend}")
    print("=" * 70)

    ok_lift = lift >= LIFT_MIN
    ok_cw = not cw
    ok_full = not pend
    verdict = ok_lift and ok_cw and ok_full
    print(f"VEREDITO FASE 3: {'PASS' if verdict else 'FAIL'} "
          f"(lift={ok_lift} confErrado0={ok_cw} completo={ok_full})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
