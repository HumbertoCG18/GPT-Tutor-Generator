"""MOTOR PURO — regua oficial do produto: sem curadoria manual (pinos/cards/
glossario) E sem voter LLM, nas copias `.ablacao` dos 5 cursos com gold.
READ-ONLY nos originais. Promovido do scratchpad em 02/09 (Fase 0 do plano).

    python scripts/motor_puro.py                # 5 cursos: nu + voter OFF + 3 eixos + subunidade

Mede: bloco/unidade/cobertura (eval_eixos) + subunidade (subunit_gt_*.csv, com-extras
e primario). Regua dupla: nada regride aqui NEM na curada (eval_eixos nos originais).
Baseline 01/09d: bloco 158/200 · unidade 154/191 · cobertura 51/57 · subunidade 26/93.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GEN = Path(__file__).resolve().parents[1]
ORIG = GEN.parent
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
os.environ["TUTOR_REPOS_ORIG"] = str(ORIG)

import ablacao_rapida as ab  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

_orig_merge = ra._merge_profile_flags


def _merge_sem_voter(options, profile):
    _orig_merge(options, profile)
    options["use_llm_voter"] = False


ra._merge_profile_flags = _merge_sem_voter

SIGS = ["MF", "SO", "IA", "ES2", "TCC"]
SUBUNIT_GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
                "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}


def main() -> int:
    t0 = time.time()
    for sig in SIGS:
        src, dst = ORIG / ab.REPO[sig], COPY / ab.REPO[sig]
        ab.sync(src, dst)
        n = ab.ablate(dst)
        print(f"  [nu] {sig}: {n} pinos zerados", flush=True)
    for sig in SIGS:
        ra.reprocess(COPY / ab.REPO[sig], [])
    print(f"reprocess x{len(SIGS)} sem voter: {time.time() - t0:.0f}s", flush=True)

    env = {**os.environ, "TUTOR_REPOS_DIR": str(COPY), "PYTHONIOENCODING": "utf-8"}
    ev = subprocess.run([sys.executable, str(GEN / "scripts/eval_eixos.py")], cwd=str(GEN), env=env,
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n=== EIXOS — motor puro (sem curadoria, sem LLM) ===")
    print(ev.stdout)

    tot_ok = tot_n = prim_ok = 0
    for sigla, repo in SUBUNIT_GOLD.items():
        m = json.loads((COPY / repo / "manifest.json").read_text(encoding="utf-8"))
        pred = {str(e.get("id")): str(e.get("computed_subunit_slug") or "") for e in m["entries"]}
        with open(GEN / "docs" / "reports" / f"subunit_gt_{sigla}.csv", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["scorable"] != "yes":
                    continue
                tot_n += 1
                extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
                alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
                p = pred.get(r["entry_id"], "(SUMIU)")
                tot_ok += p in alvo
                prim_ok += p == r["gold_subunit"]
    print(f"SUBUNIDADE motor puro: {tot_ok}/{tot_n} com-extras · {prim_ok}/{tot_n} primario")
    print(f"total: {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
