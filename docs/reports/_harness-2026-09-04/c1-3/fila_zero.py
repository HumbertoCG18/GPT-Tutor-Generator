"""Fila de revisao do regime ZERO LLM (snapshot `snap_placar/<regime>/`): por motivo e por curso; rendimento contra o gold (duvida que e erro x
duvida que e acerto) e ERROS CONFIANTES (fora da fila) por eixo. Uso: fila_zero.py [zero|auto]"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
SNAP = GEN / "docs/reports/_harness-2026-09-04/c1-3/snap_placar"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_labels_csv  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402

REGIME = (sys.argv + ["zero"])[1]
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}


def golds(sig):
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {}
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


TOT = Counter(); MOT = Counter(); MOT_SIG = defaultdict(Counter); CONF = Counter(); CONF_EX = defaultdict(list); DUV_ERR = Counter()
for sig, repo in REPO.items():
    mp = SNAP / REGIME / f"{repo}.manifest.json"
    if not mp.exists():
        continue
    man = json.loads(mp.read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((SNAP / REGIME / f"{repo}.timeline.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]; ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    c = Counter()
    for e in man:
        r = revisar_de(e)
        c["materiais"] += 1
        eid = e["id"]
        erros = []
        if eid in gb and ti.get(str(e.get("temporal_block_id") or ""), "") != gb[eid]:
            erros.append("bloco")
        if eid in gu and str(e.get("computed_unit_slug") or "") != gu[eid]:
            erros.append("unidade")
        if eid in gs and str(e.get("computed_subunit_slug") or "") not in gs[eid]:
            erros.append("sub")
        if r in ("duvida", "mudou"):
            c["fila"] += 1
            ms = motivos_de(e) or ["?"]
            for m in ms:
                MOT[m] += 1; MOT_SIG[sig][m] += 1
            if erros:
                c["fila & erra"] += 1
                for ax in erros:
                    DUV_ERR[f"duvida acerta erro de {ax}"] += 1
            elif eid in gb or eid in gu or eid in gs:
                c["fila & certo (aviso vazio)"] += 1
            else:
                c["fila sem gold"] += 1
        else:
            for ax in erros:
                CONF[f"{sig} {ax}"] += 1; CONF[f"TOTAL {ax}"] += 1
                if len(CONF_EX[ax]) < 6:
                    CONF_EX[ax].append(f"{sig}:{eid[:26]}")
            if erros:
                c["confiante & erra"] += 1
    TOT.update(c)
    print(f"[{sig}] materiais {c['materiais']:3} · fila {c['fila']:3} ({100*c['fila']/c['materiais']:.0f}/100) · fila&erra {c['fila & erra']:2} · fila&certo {c['fila & certo (aviso vazio)']:2} · fila sem gold {c['fila sem gold']:2} · CONFIANTE&erra {c['confiante & erra']:2} · motivos {dict(MOT_SIG[sig].most_common(6))}")
c = TOT
print(f"\n[TOTAL {REGIME}] materiais {c['materiais']} · fila {c['fila']} ({100*c['fila']/c['materiais']:.1f}/100) · fila&erra {c['fila & erra']} · fila&certo {c['fila & certo (aviso vazio)']} · fila sem gold {c['fila sem gold']} · CONFIANTE&erra {c['confiante & erra']}")
print("motivos:", dict(MOT.most_common(12)))
print("duvida que acerta erro:", dict(DUV_ERR))
print("erros confiantes por eixo:", {k: v for k, v in CONF.items() if k.startswith("TOTAL")}, "| por curso:", {k: v for k, v in CONF.items() if not k.startswith("TOTAL")})
print("exemplos confiantes:", dict(CONF_EX))
