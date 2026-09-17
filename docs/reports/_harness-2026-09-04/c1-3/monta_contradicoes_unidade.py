"""C5 item 1 (12/09): os materiais em que o gold de unidade POR MATERIAL (`docs/reports/material_gt_<sig>.csv`, rulings do user de
19/08) contradiz o gold de unidade POR BLOCO (`tests/fixtures/eval/gold_units_<sig>.csv` |><| `ground_truth_<sig>.csv`, o que a
regua le). Medido em 12/09: 16 (MF 4, SO 8, ES2 4) + 1 do MF so no material_gt. Gera a planilha de adjudicacao com os dois lados e
as fontes; o user preenche `decisao` (bloco | material | outra unidade | scorable=no) e `fonte`. 0 chamadas.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/monta_contradicoes_unidade.py"""
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN / "scripts"))
from eval_entry_unit import _load_truth  # noqa: E402

TUTORES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
           "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
COLS = ["curso", "entry_id", "title", "category", "secao_moodle", "gold_bloco", "unidade_do_bloco_gold", "unidade_material_gt",
        "notas_material_gt", "pred_unit_produto", "revisar", "decisao", "fonte"]
rows = []
for sig, repo in TUTORES.items():
    bloco = _load_truth(sig)
    gt = {r["id"]: r for r in csv.DictReader((GEN / "docs/reports" / f"ground_truth_{sig}.csv").open(encoding="utf-8-sig", newline=""))}
    man = {e["id"]: e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    p = GEN / "docs/reports" / f"material_gt_{sig}.csv"
    if not p.exists():
        continue
    for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes":
            continue
        us = [u for u in r["gold_units"].split("|") if u]
        if len(us) != 1:
            continue
        eid = r["entry_id"]
        if eid in bloco and bloco[eid] == us[0]:
            continue
        e = man.get(eid, {})
        rows.append({"curso": sig, "entry_id": eid, "title": e.get("title") or r.get("title", ""), "category": e.get("category", ""),
                     "secao_moodle": e.get("source_section", ""), "gold_bloco": gt.get(eid, {}).get("true_block_id", ""),
                     "unidade_do_bloco_gold": bloco.get(eid, "(sem gold por bloco)"), "unidade_material_gt": us[0],
                     "notas_material_gt": r.get("notas", ""), "pred_unit_produto": e.get("computed_unit_slug", ""),
                     "revisar": e.get("revisar", ""), "decisao": "", "fonte": ""})
out = GEN / "docs/reports/contradicoes_unidade_material_gt_vs_bloco.csv"
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(out.name, len(rows), "linhas:", {s: sum(r["curso"] == s for r in rows) for s in TUTORES})
for r in rows:
    print(f"  {r['curso']:3} {r['entry_id'][:40]:40} bloco={r['gold_bloco']:8} u_bloco={r['unidade_do_bloco_gold'][:22]:22} u_material={r['unidade_material_gt'][:22]:22} produto={r['pred_unit_produto'][:22]:22} | {r['notas_material_gt'][:70]}")
