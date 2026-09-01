"""Regua OFICIAL de subunidade: computed_subunit_slug vs subunit_gt_{SO,IA,ES2,TCC}.csv.

    python scripts/eval_subunit_gt.py

Convencao (confirmada 31/08): conta o gold PRIMARIO; gold_subunits_extra e
aceito como acerto SO na variante com-extras (este script aceita extras —
para primario-apenas, ver o bloco PRIMARIO do handoff). Promovido do
scratchpad em 01/09 (virou rotina de gate)."""
import csv
import json
from pathlib import Path

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
REPORTS = GH / "GPT-Tutor-Generator" / "docs" / "reports"
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}

tot_ok = tot_n = 0
for sigla, repo in REPOS.items():
    m = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))
    pred = {str(e.get("id")): str(e.get("computed_subunit_slug") or "") for e in m["entries"]}
    ok = n = 0
    with open(REPORTS / f"subunit_gt_{sigla}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["scorable"] != "yes":
                continue
            n += 1
            extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
            alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
            p = pred.get(r["entry_id"], "(ENTRY-SUMIU)")
            if p in alvo:
                ok += 1
            else:
                print(f"  ERRO {sigla} {r['entry_id'][:55]}: pred={p or '(vazio)'} gold={r['gold_subunit'] or '(vazio)'}")
    print(f"{sigla}: {ok}/{n}")
    tot_ok += ok
    tot_n += n
print(f"TOTAL subunidade: {tot_ok}/{tot_n}")
