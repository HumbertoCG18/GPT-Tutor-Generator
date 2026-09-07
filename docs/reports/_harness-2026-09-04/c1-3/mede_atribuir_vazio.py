"""O motor SEMPRE escolhe um subtopico. Duas medicoes no produto em disco (0 chamadas):

  A) CURVA DO PISO: se a decisao final tem winner_score < p, o motor deixa VAZIO. Acerto = predito no conjunto do gold
     (vazio acerta quando o gold e vazio). Mostra saldo por piso e o piso que maximiza.
  B) ATRATORES: por subtopico, quantas vezes venceu e a taxa de acerto — subtopico generico que puxa tudo.
Uso: mede_atribuir_vazio.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCORE_RE = re.compile(r"(?:winner_)?score=([0-9.]+)")

CASOS = []  # (sig, id, score, pred, alvo, reasons)
for sig, repo in REPOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        razoes = [str(x) for x in (e.get("subunit_match_reasons") or [])]
        m = SCORE_RE.search(" ".join(razoes))
        CASOS.append((sig, r["entry_id"], float(m.group(1)) if m else 0.0,
                      str(e.get("computed_subunit_slug") or ""), alvo, " ".join(razoes)))

base = sum(1 for c in CASOS if c[3] in c[4])
print(f"base: {base}/{len(CASOS)}\n")
print("A) CURVA DO PISO (score < p -> vazio)")
print(f"{'piso':>6} {'certos':>7} {'delta':>6} {'ganha':>6} {'perde':>6} {'afetados':>9}")
melhor = (base, 0.0)
for p in [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0]:
    ok = ganha = perde = afet = 0
    for sig, eid, sc, pred, alvo, _ in CASOS:
        novo = "" if (pred and sc < p) else pred
        if novo != pred:
            afet += 1
            if novo in alvo and pred not in alvo:
                ganha += 1
            elif pred in alvo and novo not in alvo:
                perde += 1
        ok += novo in alvo
    print(f"{p:6.2f} {ok:7} {ok - base:+6} {ganha:6} {perde:6} {afet:9}")
    if ok > melhor[0]:
        melhor = (ok, p)
print(f"melhor piso: {melhor[1]} -> {melhor[0]}/{len(CASOS)} ({melhor[0] - base:+d})\n")

print("distribuicao do score do vencedor:")
faixas = [(0, 0.15), (0.15, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 10.0), (10.0, 1e9)]
print(f"{'faixa':>14} {'n':>5} {'certos':>7} {'%':>5}")
for lo, hi in faixas:
    g = [c for c in CASOS if c[3] and lo <= c[2] < hi]
    if g:
        ok = sum(1 for c in g if c[3] in c[4])
        print(f"{lo:6.2f}-{hi if hi < 1e8 else 999:6.1f} {len(g):5} {ok:7} {100 * ok / len(g):4.0f}%")
vaz = [c for c in CASOS if not c[3]]
print(f"{'(sem subunid)':>14} {len(vaz):5} {sum(1 for c in vaz if c[3] in c[4]):7}")

print("\nB) ATRATORES (subtopico que mais vence, ordenado por erros)")
vit = collections.Counter()
err = collections.Counter()
for sig, eid, sc, pred, alvo, _ in CASOS:
    if not pred:
        continue
    vit[(sig, pred)] += 1
    if pred not in alvo:
        err[(sig, pred)] += 1
print(f"{'curso':4} {'subtopico':40} {'vence':>6} {'erra':>5} {'prec':>5}")
for k, n in err.most_common(14):
    print(f"{k[0]:4} {k[1][:40]:40} {vit[k]:6} {n:5} {100 * (vit[k] - n) / vit[k]:4.0f}%")
