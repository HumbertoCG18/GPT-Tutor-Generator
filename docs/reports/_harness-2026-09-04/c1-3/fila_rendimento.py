"""Fila de revisao (`routing.revisar`) x golds, no PRODUTO (8 tutores, read-only, 0 chamadas): rendimento por camada
(duvida / mudou / llm) e por gatilho, e contrafactual de politicas (tamanho da fila, erros pegos/perdidos).
Gatilhos NOVOS simulados: `sub-vazia` (subunidade vazia com unidade) e `sub-fraca` (winner_score < 1)."""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from eval_ground_truth import load_predictions  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
        "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
SUB = {"SO", "IA", "ES2", "TCC", "MF", "CG"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}

rows = []   # (sig, id, gatilhos (+ novos), mudou, llm, errado|None, camada atual)
for sig, repo in REPO.items():
    r = GH / repo
    ents = [e for e in json.loads((r / "manifest.json").read_text(encoding="utf-8"))["entries"] if _is_material(e)]
    gold_b = {}
    p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    if p.exists():
        for row in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            if row.get("scorable") == "yes":
                gold_b[row["id"].strip()] = row["true_block_id"].strip()
    preds = load_predictions(r) if gold_b else {}
    gold_u = _load_truth(sig) if sig in UNI else {}
    gold_s = {}
    if sig in SUB:
        for row in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
            if row["scorable"] == "yes":
                gold_s[row["entry_id"]] = {row["gold_subunit"]} | set(filter(None, row["gold_subunits_extra"].split(";")))
    for e in ents:
        eid = str(e["id"])
        w = []
        if eid in gold_b:
            w.append(preds.get(eid, {}).get("block_id", "") != gold_b[eid])
        if eid in gold_u:
            w.append(str(e.get("computed_unit_slug") or "") != gold_u[eid])
        sub = str(e.get("computed_subunit_slug") or "")
        if eid in gold_s:
            w.append(sub not in gold_s[eid])
        m = set(motivos_de(e) or [])
        rs = " ".join(e.get("subunit_match_reasons") or [])
        sc = re.search(r"winner_score=([\d.]+)", rs)
        if not sub and e.get("computed_unit_slug"):
            m.add("sub-vazia")
        if sc and float(sc.group(1)) < 1:
            m.add("sub-fraca")
        rows.append((sig, eid, m, bool(str(e.get("sync_changed") or "").strip()), e.get("temporal_block_method") == "llm",
                     (any(w) if w else None), revisar_de(e)))

n = len(rows)
errados = sum(1 for r in rows if r[5])
gat = defaultdict(Counter)
for sig, eid, m, mu, ll, wrong, cam in rows:
    for g in m:
        gat[g]["fila"] += 1
        gat[g]["com_gold"] += wrong is not None
        gat[g]["errado"] += bool(wrong)
print(f"materiais {n} · errados em algum eixo (com gold) {errados}")
print("=== gatilho: na fila · com gold · errados · rendimento ===")
for g, c in sorted(gat.items(), key=lambda kv: -kv[1]["fila"]):
    print(f"   {g:16} {c['fila']:3} · {c['com_gold']:3} · {c['errado']:3} · {c['errado'] / max(1, c['com_gold']):.0%}")


def base(m):
    return {x for x in m if x not in ("sub-vazia", "sub-fraca")}


POL = {
    "P0 atual: duvida + mudou + llm": lambda m, mu, ll: bool(base(m)) or mu or ll,
    "P1 sem a camada llm": lambda m, mu, ll: bool(base(m)) or mu,
    "P2 P1 e sem 'conflito'": lambda m, mu, ll: bool(base(m) - {"conflito"}) or mu,
    "P1 + sub-vazia": lambda m, mu, ll: bool(base(m) | (m & {"sub-vazia"})) or mu,
    "P1 + sub-vazia + sub-fraca": lambda m, mu, ll: bool(m) or mu,
    "P2 + sub-vazia + sub-fraca": lambda m, mu, ll: bool(m - {"conflito"}) or mu,
    "P3 P1 sem sub-ambigua e due-straddle": lambda m, mu, ll: bool(base(m) - {"sub-ambigua", "flag:due-straddle"}) or mu,
    "P4 P2 sem sub-ambigua (so flags+empate+sem-bloco+mudou)": lambda m, mu, ll: bool(base(m) - {"conflito", "sub-ambigua", "flag:due-straddle"}) or mu,
    "P5 P4 + sub-empate->tambem sub-vazia": lambda m, mu, ll: bool((base(m) - {"conflito", "sub-ambigua", "flag:due-straddle"}) | (m & {"sub-vazia"})) or mu,
}
print("=== politica: na fila · /100 · erros pegos · perdidos · CG/100 · MF/100 ===")
tot = Counter(r[0] for r in rows)
for name, f in POL.items():
    fila = [r for r in rows if f(r[2], r[3], r[4])]
    pegos = sum(1 for r in fila if r[5])
    pc = Counter(r[0] for r in fila)
    print(f"   {name:34} {len(fila):3} · {100 * len(fila) / n:4.1f} · {pegos:2} · {errados - pegos:2} · {100 * pc['CG'] / tot['CG']:3.0f} · {100 * pc['MF'] / tot['MF']:3.0f}")
print("=== errados FORA da fila atual (camada ok) ===")
for r in rows:
    if r[5] and r[6] == "ok":
        print(f"   {r[0]:3} {r[1][:44]:44} sinais novos={sorted(r[2])}")
