"""Para as decisoes disamb ALTA com gold: o `unit_block_conflict` (unidade do texto != unidade do bloco) separa erradas de certas?
Tambem: a unidade do bloco VERDADEIRO (gold) coincide com a unidade que o texto escolheu? Read-only."""
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_predictions  # noqa: E402

S = Path(__file__).parent
CASES = [
    ("MF", GEN / ".ablacao/Metodos-Formais-Tutor", GEN / "docs/reports/ground_truth_MF.csv"),
    ("IA", GEN / ".ablacao/Inteligencia-Artifical-Tutor", GEN / "docs/reports/ground_truth_IA.csv"),
    ("ES2", GEN / ".ablacao/Engenharia-Software-2-Tutor", GEN / "docs/reports/ground_truth_ES2.csv"),
    ("CG-export", GEN / ".ablacao/Computacao-Grafica-Tutor", GEN / "docs/reports/ground_truth_CG.csv"),
    ("CG-rebuild", GEN / ".ablacao/CG-rebuild-holdout/Computacao-Grafica-Tutor", S / "ground_truth_CG.rebuild.csv"),
]
agg = {"wrong_conf": 0, "wrong_noconf": 0, "right_conf": 0, "right_noconf": 0, "wrong_gold_unit_eq_text": 0}
for name, repo, gold_path in CASES:
    gold = {}
    with gold_path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("scorable", "yes") == "yes" and r.get("true_block_id"):
                gold[r["id"].strip()] = r["true_block_id"].strip()
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    tl = json.loads((repo / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    unit_of_block = {str(b.get("id")): str(b.get("unit_slug") or "") for b in blocks}
    preds = load_predictions(repo)
    flagged = sum(1 for e in man["entries"] if e.get("temporal_block_flag"))
    print(f"== {name} (entries {len(man['entries'])}, flagadas hoje {flagged})")
    for e in man["entries"]:
        if str(e.get("temporal_block_method") or "") not in ("disamb", "disamb-curto") or e.get("temporal_block_flag"):
            continue
        g = gold.get(e["id"])
        if g is None:
            continue
        pred = preds.get(e["id"], {}).get("block_id", "")
        ok = pred == g
        conf = e.get("unit_block_conflict")
        uconf = float(e.get("unit_match_confidence") or 0)
        text_unit = str(e.get("computed_unit_slug") or "")
        gold_unit = unit_of_block.get(g, "")
        key = ("right" if ok else "wrong") + ("_conf" if conf else "_noconf")
        agg[key] += 1
        if not ok and conf and str(conf.get("unit")) == gold_unit:
            agg["wrong_gold_unit_eq_text"] += 1
        mark = "OK " if ok else "ERR"
        print(f"  {mark} {e['id'][:40]:40} pred={pred:8} gold={g:8} conflito={'sim' if conf else 'nao'} "
              f"u_texto={(conf or {}).get('unit', text_unit)[:34]:34} u_bloco_gold={gold_unit[:30]:30} uconf={uconf:.2f}")
print("AGREGADO:", agg)
