"""Placar consistente (06/09): por material com os TRES golds (bloco, unidade, subunidade), quantos estao 100% certos e quantos
erram em cada eixo, por regime do motor: zero LLM / vocab / auto / produto (curadoria). Snapshots de `placar_100_runs.py`
(zero, vocab) e `motor_auto.py` (auto = copias apos auto5 + holdout); produto = originais. Uso: placar_100.py"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
SNAP = C13 / "snap_placar"
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_labels_csv  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402

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


def bloco_pred(entry, ti):
    """id do bloco (pino manual vence), resolvendo uuid -> id pelo timeline do proprio regime."""
    ref = str(entry.get("manual_timeline_block_id") or entry.get("temporal_block_id") or "")
    return ti.get(ref, ref)


def medir(regime, man_path, ti_path, sig):
    man = {e["id"]: e for e in json.loads(man_path.read_text(encoding="utf-8"))["entries"]}
    ti = {}
    for b in json.loads(ti_path.read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]
        ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    c = Counter()
    for eid, e in man.items():
        axes = {}
        if eid in gb:
            axes["bloco"] = bloco_pred(e, ti) == gb[eid]
        if eid in gu:
            axes["unidade"] = str(e.get("computed_unit_slug") or "") == gu[eid]
        if eid in gs:
            axes["sub"] = str(e.get("computed_subunit_slug") or "") in gs[eid]
        if not axes:
            continue
        c["com_gold"] += 1
        for k, ok in axes.items():
            c[f"n_{k}"] += 1
            c[f"ok_{k}"] += ok
        if len(axes) == 3:
            c["tres_golds"] += 1
            c["tres_certos"] += all(axes.values())
        c["tudo_certo"] += all(axes.values())
    return c


REGIMES = {
    "zero LLM": lambda sig, repo: (SNAP / "zero" / f"{repo}.manifest.json", SNAP / "zero" / f"{repo}.timeline.json"),
    "vocab (1 LLM)": lambda sig, repo: (SNAP / "vocab" / f"{repo}.manifest.json", SNAP / "vocab" / f"{repo}.timeline.json") if sig != "CG" else (None, None),
    "auto (vocab+voter)": lambda sig, repo: (SNAP / "auto" / f"{repo}.manifest.json", SNAP / "auto" / f"{repo}.timeline.json"),
    "produto (curadoria)": lambda sig, repo: (GH / repo / "manifest.json", GH / repo / "course/.timeline_index.json"),
}
print(f"{'regime':22} {'curso':5} {'c/gold':>6} {'100% certo':>10} {'3 golds':>7} {'3 certos':>8} | {'bloco':>9} {'unidade':>9} {'subunid.':>9}")
for regime, fn in REGIMES.items():
    tot = Counter()
    for sig, repo in REPO.items():
        mp, tp = fn(sig, repo)
        if mp is None or not mp.exists():
            continue
        c = medir(regime, mp, tp, sig)
        tot.update(c)
        print(f"{regime:22} {sig:5} {c['com_gold']:6} {c['tudo_certo']:10} {c['tres_golds']:7} {c['tres_certos']:8} | {str(c['ok_bloco']) + '/' + str(c['n_bloco']):>9} {str(c['ok_unidade']) + '/' + str(c['n_unidade']):>9} {str(c['ok_sub']) + '/' + str(c['n_sub']):>9}")
    c = tot
    print(f"{regime:22} {'TOTAL':5} {c['com_gold']:6} {c['tudo_certo']:10} {c['tres_golds']:7} {c['tres_certos']:8} | {str(c['ok_bloco']) + '/' + str(c['n_bloco']):>9} {str(c['ok_unidade']) + '/' + str(c['n_unidade']):>9} {str(c['ok_sub']) + '/' + str(c['n_sub']):>9}\n")
