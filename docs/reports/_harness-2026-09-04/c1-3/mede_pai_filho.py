"""Alcance da regra PAI x FILHO: dos erros de subunidade nos 6 golds, quantos sao entre topicos da MESMA arvore do plano
(pai X.Y e filho X.Y.Z), e em que direcao. Sem parentesco = a regra nao alcanca. Read-only, 0 chamadas.
Uso: mede_pai_filho.py [zero|auto|produto]"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
SNAP = GEN / "docs/reports/_harness-2026-09-04/c1-3/snap_placar"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REGIME = (sys.argv + ["produto"])[1]
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}


def code_de(tax: dict) -> dict:
    """slug -> code normalizado ("4.1.1"); "" quando o plano nao numera."""
    return {t["slug"]: str(t.get("code") or "").strip().rstrip(".")
            for u in tax.get("units") or [] for t in u.get("topics") or []}


def parentesco(a: str, b: str) -> str:
    """Relacao entre dois codes: 'filho->pai', 'pai->filho', 'irmaos', 'mesma raiz', 'sem parentesco', 'sem code'."""
    if not a or not b:
        return "sem code"
    pa, pb = a.split("."), b.split(".")
    if len(pa) > len(pb) and pa[:len(pb)] == pb:
        return "escolheu FILHO, gold quer PAI"
    if len(pb) > len(pa) and pb[:len(pa)] == pa:
        return "escolheu PAI, gold quer FILHO"
    if len(pa) == len(pb) and len(pa) > 1 and pa[:-1] == pb[:-1]:
        return "irmaos (mesmo pai)"
    if pa[0] == pb[0]:
        return "mesma unidade, ramos diferentes"
    return "sem parentesco"


TOT = Counter()
EX = []
for sig, repo in REPO.items():
    if REGIME == "produto":
        mp = GH / repo / "manifest.json"
    else:
        mp = SNAP / REGIME / f"{repo}.manifest.json"
    if not Path(mp).exists():
        continue
    man = {e["id"]: e for e in json.loads(Path(mp).read_text(encoding="utf-8"))["entries"]}
    tax = json.loads((GH / repo / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    codes = code_de(tax)
    labels = {t["slug"]: t.get("label") for u in tax.get("units") or [] for t in u.get("topics") or []}
    c = Counter()
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes" or r["entry_id"] not in man:
            continue
        e = man[r["entry_id"]]
        got = str(e.get("computed_subunit_slug") or "")
        aceitos = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        if got in aceitos:
            continue
        c["erros"] += 1
        alvo = r["gold_subunit"]
        rel = "motor vazio" if not got else ("gold vazio" if not alvo else parentesco(codes.get(got, ""), codes.get(alvo, "")))
        c[rel] += 1
        if rel.startswith("escolheu") or rel == "irmaos (mesmo pai)":
            EX.append(f"{sig} {r['entry_id'][:30]:30} {rel:30} {codes.get(got,'?'):8} {str(labels.get(got))[:22]:24} -> {codes.get(alvo,'?'):8} {str(labels.get(alvo))[:26]}")
    TOT.update(c)
    print(f"  [{sig}] erros {c['erros']:2} · " + " · ".join(f"{k}={v}" for k, v in c.items() if k != "erros"))
print(f"\n[TOTAL {REGIME}] erros de subunidade {TOT['erros']}")
for k, v in sorted(TOT.items(), key=lambda kv: -kv[1]):
    if k != "erros":
        print(f"   {v:3}  {k}")
print("\ncasos que a regra pai x filho alcanca:")
for x in EX:
    print("   ", x)
