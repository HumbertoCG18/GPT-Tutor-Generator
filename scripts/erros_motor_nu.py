"""Lista erros de BLOCO por uuid do motor nu (rodar com os 5 repos ablacionados: scratch ablacao.py), com os sinais de cada entry e se algum sinal teria acertado."""
import sys, csv, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GH = Path(r"C:/Users/Humberto/Documents/GitHub"); GEN = GH / "GPT-Tutor-Generator"
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
SEM = re.compile(r"semana\s*(\d+)", re.I)
tot_ok = tot_n = 0; rows = []
for sig, rn in REPO.items():
    repo = GH / rn
    gold = [r for r in csv.DictReader(open(GEN / "docs/reports" / f"ground_truth_{sig}.csv", encoding="utf-8-sig")) if r.get("scorable", "yes").strip().lower() in ("yes", "1", "true", "")]
    es = {e["id"]: e for e in json.load(open(repo / "manifest.json", encoding="utf-8"))["entries"]}
    blocks = json.load(open(repo / "course/.timeline_index.json", encoding="utf-8"))["blocks"]
    by_uuid = {b["block_uuid"]: b for b in blocks}
    classes = sorted([b for b in blocks if b.get("kind") == "class" and b.get("period_start")], key=lambda b: b["period_start"])
    def blk(u): b = by_uuid.get(u); return f"{b['id']} {b.get('period_start','')}..{b.get('period_end','')} [{b.get('kind')}]" if b else "—"
    def by_date(d):
        for b in blocks:
            if b.get("period_start") and b.get("period_end") and b["period_start"] <= d <= b["period_end"]: return b["block_uuid"]
        return None
    ok = n = 0
    for g in gold:
        e = es.get(g["id"]);
        if not e: continue
        n += 1; pred, gu = e.get("temporal_block_id") or "", g["true_block_uuid"]
        if pred == gu: ok += 1; continue
        sec = e.get("source_section") or ""; pd = e.get("posting_date") or ""; lab = e.get("moodle_label") or ""
        m = SEM.search(sec) or SEM.search(lab); sem_hit = ""
        if m:
            k = int(m.group(1)); sem_hit = "sim" if (0 < k <= len(classes) and classes[k-1]["block_uuid"] == gu) else f"nao(k={k})"
        pd_hit = ("sim" if by_date(pd) == gu else "nao") if pd else ""
        rows.append(dict(c=sig, id=g["id"][:34], gold=f"{g['true_block_id']}" + ("" if gu in by_uuid else " SUMIU"), gold_now=blk(gu), pred=blk(pred), met=f"{e.get('temporal_block_method')}/{e.get('temporal_block_provider')}", card=sec[:32], label=lab[:28], pd=pd, pd_hit=pd_hit, sem_hit=sem_hit))
    tot_ok += ok; tot_n += n; print(f"{sig}: {ok}/{n}")
print(f"TOTAL por uuid: {tot_ok}/{tot_n}\n")
print(f"{'c':3} {'entry':34} {'gold':10} {'gold agora':32} {'pred':36} {'metodo':22} {'card':32} {'moodle_label':28} {'post':10} pd? sem?")
for r in rows: print(f"{r['c']:3} {r['id']:34} {r['gold']:10} {r['gold_now']:32} {r['pred']:36} {r['met']:22} {r['card']:32} {r['label']:28} {r['pd']:10} {r['pd_hit']:3} {r['sem_hit']}")
