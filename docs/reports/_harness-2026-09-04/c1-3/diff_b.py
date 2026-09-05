"""diff_b.py <antes> <depois>: flips por entry (bloco com veredito do gold; unidade/sub listados) entre 2 snapshots."""
import sys, json, csv
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"); SP = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts")); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_predictions
SIG = {"Metodos-Formais-Tutor": "MF", "Sistemas-Operacionais-Tutor": "SO", "Inteligencia-Artifical-Tutor": "IA",
       "Engenharia-Software-2-Tutor": "ES2", "TCC-Tutor": "TCC", "Computacao-Grafica-Tutor": "CG"}
A, B = SP / sys.argv[1], SP / sys.argv[2]
FIELDS = ("temporal_block_band", "temporal_block_flag", "temporal_block_method", "computed_unit_slug", "computed_subunit_slug")
for repo, sig in SIG.items():
    if not (A / repo / "manifest.json").exists() or not (B / repo / "manifest.json").exists():
        continue
    gold = {}
    p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("scorable") == "yes": gold[r["id"].strip()] = r["true_block_id"].strip()
    sub = {}
    ps = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    if ps.exists():
        with ps.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("scorable") == "yes":
                    sub[r["entry_id"]] = {r["gold_subunit"]} | set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
    pa, pb = load_predictions(A / repo), load_predictions(B / repo)
    ma = {e["id"]: e for e in json.loads((A / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    mb = {e["id"]: e for e in json.loads((B / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    def score(preds, man):
        ok = ce = 0
        for eid, g in gold.items():
            pb_ = preds.get(eid, {}).get("block_id", ""); e = man.get(eid, {})
            ok += pb_ == g
            if pb_ != g and e.get("temporal_block_band") == "alta" and not e.get("temporal_block_flag"): ce += 1
        sok = sum(str(man.get(k, {}).get("computed_subunit_slug") or "") in v for k, v in sub.items())
        return ok, ce, sok
    sa, sb = score(pa, ma), score(pb, mb)
    print(f"{sig}: bloco {sa[0]}/{len(gold)} conf-err {sa[1]} -> {sb[0]}/{len(gold)} conf-err {sb[1]}" + (f" | sub {sa[2]}/{len(sub)} -> {sb[2]}/{len(sub)}" if sub else ""))
    for eid in ma:
        ba, bb = pa.get(eid, {}).get("block_id", ""), pb.get(eid, {}).get("block_id", "")
        ch = [(f, ma[eid].get(f), mb.get(eid, {}).get(f)) for f in FIELDS if ma[eid].get(f) != mb.get(eid, {}).get(f)]
        if ba != bb or ch:
            g = gold.get(eid)
            ver = "" if g is None else ("+" if (bb == g and ba != g) else "-" if (ba == g and bb != g) else "=")
            print(f"   {ver:1} {eid[:40]:40} bloco {ba or '-'}->{bb or '-'} gold={g or '-'} " + "; ".join(f"{f}:{x}->{y}" for f, x, y in ch)[:150])
