"""S6f (c): re-chaveia ground_truth_CG.csv para o CG REBUILD (ids novos vem do nome do arquivo/modulo do stash da API).

Casamento por stem normalizado (minusculas, so [a-z0-9]) da coluna `material` contra o basename do source_path de cada entry
do manifest novo; extensao ignorada (pagina impressa .pdf -> .html). Bloco: confere que a numeracao bloco-NN do rebuild e a
mesma do original (mesmo cronograma) — se for, `true_block_id` vale como esta; senao usa `true_block_uuid` via ledger.
Escreve ground_truth_CG.rebuild.csv NO SCRATCHPAD (o gold versionado so muda com o ok do user). Read-only nos originais."""
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG = GEN.parent / "Computacao-Grafica-Tutor"
REPO = GEN / ".ablacao" / "CG-rebuild" / "Computacao-Grafica-Tutor"
GOLD = GEN / "docs/reports/ground_truth_CG.csv"
OUT = Path(__file__).parent / "ground_truth_CG.rebuild.csv"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", Path(str(s)).stem.lower())


def blocks(repo):
    d = json.loads((repo / "course/.timeline_index.json").read_text(encoding="utf-8"))
    bl = d if isinstance(d, list) else d.get("blocks", [])
    return [(str(b.get("id")), str(b.get("period_start") or b.get("start") or ""), str(b.get("period_end") or b.get("end") or ""),
             str(b.get("title") or b.get("label") or "")[:40]) for b in bl]


bo, bn = blocks(ORIG), blocks(REPO)
same = [x[:3] for x in bo] == [x[:3] for x in bn]
print(f"blocos original {len(bo)} x rebuild {len(bn)} | mesma numeracao/datas: {same}")
if not same:
    for a, b in zip(bo, bn):
        if a[:3] != b[:3]:
            print("   difere:", a, "x", b)

man = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))["entries"]
orig_sec = {e["id"]: str(e.get("source_section") or "") for e in json.loads((ORIG / "manifest.json").read_text(encoding="utf-8"))["entries"]}
sec_of = {e["id"]: str(e.get("source_section") or "") for e in man}
by_norm = {}
for e in man:
    by_norm.setdefault(norm(Path(str(e.get("source_path") or "")).name), []).append(e["id"])
by_id = {e["id"] for e in man}
# Paginas do site impressas em PDF no export tinham o TITULO como nome; no rebuild o bundle leva o stem da URL.
ALIAS = {"origens-da-computacao-grafica": "intro",
         "transformacoes-geometricas-em-opengl": "transformacoesgl",
         "computacao-grafica-curvas-parametricas": "curvas",
         "computacao-grafica-modelagem-de-solidos": "modelagem3d"}

rows = list(csv.DictReader(GOLD.open(encoding="utf-8-sig", newline="")))
out, unmatched, ambiguous = [], [], []
for r in rows:
    key = norm(r["material"])
    cands = by_norm.get(key) or ([r["id"]] if r["id"] in by_id else [])
    if r["id"] in ALIAS and ALIAS[r["id"]] in by_id:
        cands = [ALIAS[r["id"]]]
    if not cands:
        unmatched.append((r["id"], r["material"], r["scorable"]))
        continue
    if len(cands) > 1:
        same_sec = [c for c in cands if sec_of.get(c) == orig_sec.get(r["id"])]
        ambiguous.append((r["id"], cands, same_sec))
        cands = same_sec or cands
    new = dict(r)
    new["id_export"] = r["id"]
    new["id"] = cands[0]
    if r["id"] in ALIAS:
        new["nota"] = (new.get("nota") or "") + " | re-chaveado S6f: pagina do site impressa no export -> bundle html"
    out.append(new)

seen = set()
dedup = []
for r in out:
    if r["id"] in seen:
        continue
    seen.add(r["id"])
    dedup.append(r)
fields = list(rows[0].keys()) + ["id_export"]
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(dedup)
print(f"gold: {len(rows)} linhas -> {len(dedup)} re-chaveadas ({len(out) - len(dedup)} duplicadas por id novo) | "
      f"scorable=yes re-chaveadas: {sum(1 for r in dedup if r['scorable'] == 'yes')}")
print("sem par no rebuild:", unmatched)
print("ambiguos:", ambiguous)
print("entries do rebuild sem linha no gold:", sorted(by_id - {r['id'] for r in dedup})[:40])
print("->", OUT)
