"""Pos-check: nenhum resumo de codigo com generated_at de HOJE nas copias (tripwire funcionou)."""
import json, glob, os, sys, datetime
GEN = r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"; hoje = datetime.date.today().isoformat(); tot = 0
for p in glob.glob(f"{GEN}/.ablacao/*-Tutor/code_curation.json"):
    ents = json.load(open(p, encoding="utf-8")).get("entries") or {}
    n = sum(1 for v in ents.values() if str(v.get("generated_at")).startswith(hoje)); tot += n
    print(f"  {os.path.basename(os.path.dirname(p)):32} resumos de hoje={n}/{len(ents)}")
print("TOTAL resumos de codigo gerados hoje nas copias:", tot); sys.exit(1 if tot else 0)
