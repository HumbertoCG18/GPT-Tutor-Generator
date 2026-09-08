"""A pergunta que decide se da para viver sem gold (08/09, pergunta do user).

O gold nao e insumo do motor — o motor nunca o le. Ele e o instrumento que diz se a decisao foi certa. A pergunta util
nao e "gold ou nao gold", e: **o proprio motor sabe quando esta inseguro?** Se souber, um curso novo dispensa gold: basta
olhar a fila.

Mede a FILA como detector de erro, contra o gold, por eixo:
  confiante & certo    o caso bom
  confiante & ERRADO   o caso perigoso: entrega errado sem avisar  (= `conf-err`)
  na fila  & errado    a fila fez o trabalho dela
  na fila  & certo     alarme falso (custo de revisao humana, nao de qualidade)
E deriva: precisao do "confiante" (se eu confiar no motor sem gold, quanto acerto?) e recall da fila (dos erros, quantos
ela pega?). 0 chamadas. Uso: calibra_fila_como_regua.py
"""
import collections
import csv as _csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
        "FR": "Fundamentos-de-Redes-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402


def golds(sig):
    p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    gb = load_labels_csv(p) if p.exists() else {}
    gu = _load_truth(sig) if sig in UNI else {}
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    gs = {}
    if p.exists():
        for r in _csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes":
                gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


EIXOS = ("bloco", "unidade", "subunidade", "qualquer eixo")
M = {e: collections.Counter() for e in EIXOS}
for sig, repo in GOLD.items():
    root = GH / repo
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]
        ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    for e in man:
        eid = e["id"]
        na_fila = revisar_de(e) in ("duvida", "mudou")
        cert = {}
        if eid in gb:
            cert["bloco"] = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
        if eid in gu:
            cert["unidade"] = str(e.get("computed_unit_slug") or "") == gu[eid]
        if eid in gs:
            cert["subunidade"] = str(e.get("computed_subunit_slug") or "") in gs[eid]
        if cert:
            cert["qualquer eixo"] = all(cert.values())
        for eixo, ok in cert.items():
            c = M[eixo]
            c["n"] += 1
            if na_fila and ok:
                c["fila_certo"] += 1
            elif na_fila and not ok:
                c["fila_errado"] += 1
            elif not na_fila and ok:
                c["conf_certo"] += 1
            else:
                c["conf_ERRADO"] += 1

print("A FILA COMO DETECTOR DE ERRO (o motor sabe quando esta inseguro?)")
print(f"{'eixo':14} {'n':>5} {'confiante&certo':>16} {'confiante&ERRADO':>17} {'fila&errado':>12} {'fila&certo':>11}")
for eixo in EIXOS:
    c = M[eixo]
    print(f"{eixo:14} {c['n']:5} {c['conf_certo']:16} {c['conf_ERRADO']:17} {c['fila_errado']:12} {c['fila_certo']:11}")
print()
print(f"{'eixo':14} {'PRECISAO do confiante':>23} {'RECALL da fila':>16} {'alarme falso':>14}")
for eixo in EIXOS:
    c = M[eixo]
    conf = c["conf_certo"] + c["conf_ERRADO"]
    err = c["conf_ERRADO"] + c["fila_errado"]
    fila = c["fila_certo"] + c["fila_errado"]
    print(f"{eixo:14} {c['conf_certo']:6}/{conf:<6} {100 * c['conf_certo'] / max(1, conf):5.1f}% "
          f"{c['fila_errado']:4}/{err:<4} {100 * c['fila_errado'] / max(1, err):4.0f}% "
          f"{c['fila_certo']:4}/{fila:<4} {100 * c['fila_certo'] / max(1, fila):3.0f}%")
print("\nLEITURA: 'PRECISAO do confiante' e a pergunta do user — num curso NOVO, sem gold, se eu aceitar tudo que o")
print("motor nao poe na fila, quanto disso esta certo? 'RECALL da fila' e quanto dos erros ela consegue avisar.")
