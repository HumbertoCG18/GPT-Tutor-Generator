"""REGUA SEM GOLD (06/09): coerencia do bloco com a POSICAO DO PROFESSOR no Moodle (label datado, data no nome do modulo,
secao-semana, faixa dos irmaos datados — mesma logica de `_harness-2026-09-02/audita_gold.py`), nos 8 tutores, todos os
materiais, no PRODUTO (originais). Onde ha gold, calibra a regua: coerente-mas-errado e incoerente-mas-certo.
Read-only, 0 chamadas. Uso: coerencia_moodle.py [--lista]"""
import collections
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
LISTA = "--lista" in sys.argv
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.sources.moodle import sanitize_folder_name  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS  # noqa: E402

PULL = GEN / "docs/reports/_harness-2026-09-02/moodle_contents"
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
DATE_FULL = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
DATE_NAME = re.compile(r"^\s*\[?\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b")
SEC_RANGE = re.compile(r"(\d{1,2})[./](\d{1,2})\s*a\s*(\d{1,2})[./](\d{1,2})")


def norm(t):
    return " ".join(normalize_match_text(str(t or "")).split())


def bid(b):
    return str(b.get("id") or "")


def hosts(b):
    k = str(b.get("kind") or "")
    return k not in NEVER_HOSTS_MATERIAL_KINDS and k != "assessment"


def blocks_in_range(ctx, d1, d2):
    a, b_ = d1.isoformat(), d2.isoformat()
    return [bid(blk) for blk in ctx.blocks if hosts(blk) and any(a <= str(s.get("date") or "")[:10] <= b_ for s in (blk.get("sessions") or []))]


def placement_of(sig, repo, man, ctx):
    """{entry_id: (blocos, fonte)} pela posicao do professor no Moodle."""
    contents = json.loads((PULL / f"{sig}.json").read_text(encoding="utf-8"))
    year = int(str(ctx.blocks[0].get("period_start") or "2026")[:4]) if ctx.blocks else 2026
    order = {bid(b): i for i, b in enumerate(ctx.blocks)}
    ents = man["entries"]
    by_id = {e["id"]: e for e in ents}
    placement = {}
    for s in contents:
        sec_name = str(s.get("name") or "")
        sec_folder = sanitize_folder_name(sec_name)
        in_sec = [e for e in ents if str(e.get("source_section") or "") == sec_folder]
        sec_blocks = []
        m = SEC_RANGE.search(sec_name)
        mw = re.search(r"semana\s*(\d{1,2})", sec_name, re.I)
        if not m and mw and ctx.blocks:
            first_date = min((str(s_.get("date") or "")[:10] for b in ctx.blocks for s_ in (b.get("sessions") or []) if s_.get("date")), default="")
            if first_date:
                d0 = date.fromisoformat(first_date)
                d0 = d0 - timedelta(days=d0.weekday())
                d1 = d0 + timedelta(days=7 * (int(mw.group(1)) - 1))
                sec_blocks = blocks_in_range(ctx, d1, d1 + timedelta(days=6))
        if m:
            try:
                d1 = date(year, int(m.group(2)), int(m.group(1)))
                d2 = date(year, int(m.group(4)), int(m.group(3)))
                sec_blocks = blocks_in_range(ctx, min(d1, d2), max(d1, d2))
            except ValueError:
                sec_blocks = []
        run, run_txt, pending = [], "", []
        for mod in s.get("modules") or []:
            mn = mod.get("modname")
            name = str(mod.get("name") or "")
            if mn == "label":
                ds = DATE_FULL.findall(name)
                if ds:
                    d1 = date(int(ds[0][2]), int(ds[0][1]), int(ds[0][0]))
                    d2 = date(int(ds[1][2]), int(ds[1][1]), int(ds[1][0])) if len(ds) > 1 and re.search(r"\d{4}\s*a\s*\d", name) else d1
                    bl = blocks_in_range(ctx, min(d1, d2), max(d1, d2))
                    if bl:
                        pending.append((bl, name[:70]))
                continue
            if mn in ("url", "forum", "assign", "quiz", "page", "label"):
                continue
            if pending:
                run = list(dict.fromkeys(b for bl, _ in pending for b in bl))
                run_txt = " || ".join(t for _, t in pending)
                pending = []
            fns = {str(c.get("filename") or "").lower() for c in (mod.get("contents") or [])}
            ids = [e["id"] for e in in_sec if Path(str(e.get("source_path") or "")).name.lower() in fns]
            if not ids:
                stems = {norm(Path(f).stem) for f in fns}
                ids = [e["id"] for e in in_sec if norm(Path(str(e.get("source_path") or "")).stem) in stems]
            if not ids:
                same = [e["id"] for e in in_sec if norm(e.get("moodle_label") if not isinstance(e.get("moodle_label"), dict) else e["moodle_label"].get("text")) == norm(name)]
                n_mod = sum(1 for m2 in (s.get("modules") or []) if norm(m2.get("name")) == norm(name))
                ids = same if (len(same) == 1 or n_mod == 1) else []
            if not ids:
                ids = [e["id"] for e in in_sec if norm(Path(str(e.get("source_path") or "")).stem) == norm(name)]
            dm = DATE_NAME.match(name)
            src, bl = "", []
            if dm:
                try:
                    d = date(year, int(dm.group(2)), int(dm.group(1)))
                    b = blocks_in_range(ctx, d, d)
                    if b:
                        bl, src = b, "data no nome"
                except ValueError:
                    pass
            if not bl and run:
                bl, src = run, "label datado"
            if not bl and sec_blocks:
                bl, src = sec_blocks, "secao-semana"
            for eid in ids:
                if eid not in placement:
                    placement[eid] = (bl, src)
    card_rng = collections.defaultdict(set)
    for eid, (bl, src) in placement.items():
        if bl and src != "secao-semana":
            card_rng[str(by_id.get(eid, {}).get("source_section") or "")].update(bl)
    for e in ents:
        if e["id"] in placement and placement[e["id"]][0]:
            continue
        rng = card_rng.get(str(e.get("source_section") or ""))
        if rng:
            lo, hi = min(order[b] for b in rng), max(order[b] for b in rng)
            placement[e["id"]] = ([bid(b) for b in ctx.blocks[lo:hi + 1] if hosts(b)], "faixa dos irmaos")
    return placement


TOT = collections.Counter()
print(f"{'curso':5} {'mat':>4} {'c/posicao':>9} {'coerente':>8} {'incoer.':>7} {'s/posicao':>9} | {'gold: coer&certo':>16} {'coer&errado':>11} {'incoer&certo':>12} {'incoer&errado':>13}")
for sig, nome in REPOS.items():
    repo = GH / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    placement = placement_of(sig, repo, man, ctx)
    preds = load_predictions(repo)
    gp = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    gold = load_labels_csv(gp) if gp.exists() else {}
    c = collections.Counter()
    incoer = []
    for e in man["entries"]:
        if not _is_material(e):
            continue
        eid = e["id"]
        c["mat"] += 1
        bl, src = placement.get(eid, ([], ""))
        pred = preds.get(eid, {}).get("block_id", "")
        if not bl:
            c["sem"] += 1
            continue
        c["pos"] += 1
        coer = pred in bl
        c["coer" if coer else "incoer"] += 1
        if not coer:
            incoer.append(f"{eid[:34]}:{pred or '-'}∉{'/'.join(b[-2:] for b in bl[:6])}[{src[:6]}]")
        g = gold.get(eid)
        if g:
            certo = pred == g
            c[("coer" if coer else "incoer") + ("_certo" if certo else "_errado")] += 1
    TOT.update(c)
    print(f"{sig:5} {c['mat']:4} {c['pos']:9} {c['coer']:8} {c['incoer']:7} {c['sem']:9} | {c['coer_certo']:16} {c['coer_errado']:11} {c['incoer_certo']:12} {c['incoer_errado']:13}")
    if LISTA and incoer:
        print("      incoerentes:", incoer[:12])
c = TOT
print(f"{'TOTAL':5} {c['mat']:4} {c['pos']:9} {c['coer']:8} {c['incoer']:7} {c['sem']:9} | {c['coer_certo']:16} {c['coer_errado']:11} {c['incoer_certo']:12} {c['incoer_errado']:13}")
print(f"coerencia (onde ha posicao): {c['coer']}/{c['pos']} = {c['coer'] / max(1, c['pos']):.1%} · cobertura da regua: {c['pos']}/{c['mat']} = {c['pos'] / max(1, c['mat']):.0%}")
