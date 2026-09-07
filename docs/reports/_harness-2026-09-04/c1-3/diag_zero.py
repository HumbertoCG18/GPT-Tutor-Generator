"""Diagnostico do regime ZERO LLM (snapshot `snap_placar/zero/`): dos materiais com gold que NAO estao 100% certos, que eixo falha e por que,
e quanto sinal deterministico nao usado existe (topico do bloco do SARC = subtopico da taxonomia; secao; unidade do bloco). Read-only.
Uso: diag_zero.py [zero|vocab|auto]"""
import csv
import json
import re
import sys
import unicodedata
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

REGIME = (sys.argv + ["zero"])[1]
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def golds(sig):
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {}
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


TOT = Counter()
TOT_SIG = defaultdict(Counter)
for sig, repo in REPO.items():
    mp = SNAP / REGIME / f"{repo}.manifest.json"
    if not mp.exists():
        continue
    man = {e["id"]: e for e in json.loads(mp.read_text(encoding="utf-8"))["entries"]}
    blocks = json.loads((SNAP / REGIME / f"{repo}.timeline.json").read_text(encoding="utf-8"))["blocks"]
    B = {}
    for b in blocks:
        B[b["block_uuid"]] = b
        B[b["id"]] = b
    tax = json.loads((GH / repo / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    topics = {}   # slug -> (unit_slug, label)
    unit_title = {}
    for u in tax["units"]:
        unit_title[u["slug"]] = u["title"]
        for t in u.get("topics") or []:
            topics[t["slug"]] = (u["slug"], t["label"])
    gb, gu, gs = golds(sig)
    c = TOT_SIG[sig]
    for eid, e in man.items():
        axes = {}
        ref = str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "")
        blk = B.get(ref)
        pred_b = blk["id"] if blk else ""
        if eid in gb:
            axes["bloco"] = pred_b == gb[eid]
        if eid in gu:
            axes["unidade"] = str(e.get("computed_unit_slug") or "") == gu[eid]
        if eid in gs:
            axes["sub"] = str(e.get("computed_subunit_slug") or "") in gs[eid]
        if not axes:
            continue
        c["com_gold"] += 1
        if all(axes.values()):
            c["100%"] += 1
            continue
        falha = "+".join(k for k, ok in axes.items() if not ok)
        c[f"falha {falha}"] += 1
        # --- subunidade
        if "sub" in axes and not axes["sub"]:
            got = str(e.get("computed_subunit_slug") or "")
            gold = gs[eid]
            if gold == {""}:
                c["sub: gold-vazio, motor pos"] += 1
            elif not got:
                c["sub: vazia"] += 1
            else:
                c["sub: errada"] += 1
            reasons = " ".join(e.get("subunit_match_reasons") or [])
            if "empate" in reasons:
                c["sub: empate"] += 1
            # sinal do bloco do SARC
            if blk and gold != {""}:
                pts = blk.get("primary_topic_slug") or ""
                bts = set(blk.get("topics") or []) if isinstance(blk.get("topics"), list) else set()
                bts = {t if isinstance(t, str) else (t.get("slug") or "") for t in bts}
                if pts in gold:
                    c["sub: topico primario do BLOCO = gold"] += 1
                    c[f"sub: topico do bloco = gold e sub {'vazia' if not got else 'errada'}"] += 1
                elif bts & gold:
                    c["sub: gold entre os topicos do bloco"] += 1
                elif pts and pts in topics:
                    c["sub: bloco nomeia OUTRO subtopico"] += 1
                else:
                    c["sub: bloco sem topico da taxonomia"] += 1
            # secao nomeia o gold?
            sec = norm(e.get("source_section"))
            if gold != {""} and any(g in topics and norm(topics[g][1]) and norm(topics[g][1]) in sec for g in gold):
                c["sub: secao nomeia o gold"] += 1
            # titulo nomeia o gold?
            tit = norm(e.get("title"))
            if gold != {""} and any(g in topics and norm(topics[g][1]) and norm(topics[g][1]) in tit for g in gold):
                c["sub: titulo nomeia o gold"] += 1
        # --- unidade
        if "unidade" in axes and not axes["unidade"]:
            bu = (blk or {}).get("unit_slug") or ""
            if bu == gu[eid]:
                c["unidade: bloco tem a unidade certa"] += 1
            elif not blk:
                c["unidade: sem bloco"] += 1
            else:
                c["unidade: bloco tambem errado"] += 1
            if norm(unit_title.get(gu[eid], "")) and norm(unit_title[gu[eid]]) in norm(e.get("source_section")):
                c["unidade: secao nomeia a unidade"] += 1
            if not e.get("computed_unit_slug"):
                c["unidade: vazia"] += 1
        # --- bloco
        if "bloco" in axes and not axes["bloco"]:
            c[f"bloco: {'flagado' if e.get('temporal_block_flag') else 'CONFIANTE'}"] += 1
            c[f"bloco: provider {e.get('temporal_block_provider') or '-'}"] += 1
            win = e.get("temporal_block_window") or []
            win_ids = {B[w]["id"] for w in win if w in B}
            if not pred_b:
                c["bloco: sem bloco"] += 1
            elif gb[eid] in win_ids:
                c["bloco: gold na janela"] += 1
            else:
                c["bloco: gold FORA da janela"] += 1
    TOT.update(c)

print(f"REGIME {REGIME}")
for sig, c in TOT_SIG.items():
    print(f"\n[{sig}] com gold {c['com_gold']} · 100% {c['100%']} · falham {c['com_gold'] - c['100%']}")
    for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])):
        if k not in ("com_gold", "100%"):
            print(f"   {v:3}  {k}")
c = TOT
print(f"\n[TOTAL] com gold {c['com_gold']} · 100% {c['100%']} · falham {c['com_gold'] - c['100%']}")
for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])):
    if k not in ("com_gold", "100%"):
        print(f"   {v:3}  {k}")
