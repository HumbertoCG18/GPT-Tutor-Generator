"""Harness do balde B (rodar com os 5 repos ABLACIONADOS via scratch ablacao.py): decisao deterministica atual vs regras candidatas, contra o gold. Argumento opcional: tolerancia de entries por posting_date (default 1)."""
import sys, csv, json, collections, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.path.insert(0, r"C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.window_provider import resolve_window
from src.builder.routing.motor.disambiguator import disambiguate
from src.builder.routing.motor.anchor_engine import resolve_exam_prep, _exam_number, is_out_of_disamb_scope
from src.builder.routing.motor.apply import tier2_due_scope
from src.builder.routing.motor.llm_vote import detect_same_theme_series
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS
from src.utils.helpers import norm_ascii_lower
GH = Path(r"C:/Users/Humberto/Documents/GitHub"); GEN = GH / "GPT-Tutor-Generator"
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
NOT_HOST = set(NEVER_HOSTS_MATERIAL_KINDS) | {"assessment"}
def toks(t): return {w for w in re.findall(r"[a-z0-9]+", norm_ascii_lower(t or "")) if len(w) >= 4}

def posting_window(e, ctx, modal, first_start=""):
    pd = str(e.get("posting_date") or "")
    if not pd or pd == modal or pd < first_start or PDC[pd] > MAXSHARE: return []
    inside = [str(b["id"]) for b in ctx.blocks if b.get("id") and str(b.get("period_start") or "") <= pd <= str(b.get("period_end") or "") and str(b.get("kind")) not in NEVER_HOSTS_MATERIAL_KINDS]
    if inside: return inside
    after = [b for b in ctx.blocks if b.get("id") and str(b.get("period_start") or "") > pd and str(b.get("kind")) not in NEVER_HOSTS_MATERIAL_KINDS]
    after.sort(key=lambda b: str(b.get("period_start")))
    return [str(after[0]["id"])] if after else []

def label_topic(e, ctx, window):
    lab = toks(str(e.get("moodle_label") or "")) | toks(str(e.get("title") or ""))
    hits = []
    for r in window:
        b = ctx.block_by_ref(r)
        if not b: continue
        tt = toks(str(b.get("primary_topic_label") or ""))
        if len(tt) >= 2 and tt <= lab: hits.append(r)
    return hits[0] if len(hits) == 1 else ""

tot = collections.Counter(); PDC = collections.Counter(); MAXSHARE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for sig, rn in REPO.items():
    repo = GH / rn; m = json.load(open(repo / "manifest.json", encoding="utf-8"))
    ctx = build_motor_context(repo, str((m.get("course") or {}).get("name") or ""))
    es = {e["id"]: e for e in m["entries"]}
    pdc = collections.Counter(e.get("posting_date") for e in m["entries"] if e.get("posting_date")); PDC.clear(); PDC.update(pdc)
    series = detect_same_theme_series(m["entries"])
    modal, mc = (pdc.most_common(1)[0] if pdc else ("", 0)); modal = modal if mc >= 0.25 * len(m["entries"]) else ""
    uuid2ref = {str(b.get("block_uuid")): str(b.get("id")) for b in ctx.blocks}
    disp = lambda r: uuid2ref.get(str(r), str(r))
    first_start = min(str(b.get("period_start") or "9") for b in ctx.blocks if b.get("period_start"))
    q = collections.Counter()
    gold = [r for r in csv.DictReader(open(GEN / "docs/reports" / f"ground_truth_{sig}.csv", encoding="utf-8-sig")) if r["scorable"] == "yes"]
    print(f"=== {sig} modal={modal or '-'} ({mc}/{len(m['entries'])})")
    for g in gold:
        e = es.get(g["id"]); gref = uuid2ref.get(g["true_block_uuid"], "?")
        if not e or is_out_of_disamb_scope(e): continue
        pred = uuid2ref.get(str(e.get("temporal_block_id") or ""), "-")
        win, prov = resolve_window(e, ctx)
        lexical = not tier2_due_scope(e)
        base = disambiguate(e, win, ctx, "", provider=prov).block_ref if win else ((resolve_exam_prep(e, ctx).block_ref if (lexical and resolve_exam_prep(e, ctx)) else "funil"))
        # R1 posting: entre data e ordinal
        r1 = base
        pw = posting_window(e, ctx, modal, first_start)
        if pw:
            if not win:
                if not (lexical and resolve_exam_prep(e, ctx)):   # prep primeiro
                    r1 = disambiguate(e, pw, ctx, "", provider="data").block_ref
            elif len(win) > 1 and prov != "manual":
                hit = [r for r in win if disp(r) in {disp(p) for p in pw}]
                if len(hit) == 1: r1 = disp(hit[0])
        # R2 prep antes do voto se provider fraco
        r2 = base
        if lexical and _exam_number(e) > 0 and prov in ("", "ordinal", "topic"):
            p = resolve_exam_prep(e, ctx)
            if p: r2 = p.block_ref
        # R3 label contem topico do bloco (janela > 1)
        r3 = base
        if len(win) > 1:
            lt = label_topic(e, ctx, win)
            if lt: r3 = disp(lt)
        det_dec = disambiguate(e, win, ctx, "", provider=prov) if win else None
        flagged = bool(det_dec and det_dec.flag and len(win) > 1)
        q[("det" + ("✓" if base == gref else "✗"), "nu" + ("✓" if pred == gref else "✗"), "flag" if flagged else "conf")] += 1
        if g["id"] in series and win and len(win) > 1 and not flagged:
            print(f"  SERIE conf: {g['id'][:30]:30} det={base}{'✓' if base==gref else '✗'} nu={pred}{'✓' if pred==gref else '✗'}")
        marks = []
        for name, val in (("R1", r1), ("R2", r2), ("R3", r3)):
            if val != base:
                good = val == gref; tot[f"{name}_{'ganha' if good else ('perde' if base == gref else 'troca')}"] += 1
                marks.append(f"{name}:{base}->{val}{'✓' if good else '✗'}")
        if marks or pred != gref:
            print(f"  {g['id'][:36]:36} gold={gref:8} nu={pred:8} det={base:8}{'F' if flagged else ' '} prov={prov or '-':7} pd={e.get('posting_date') or '-'} {' '.join(marks)}")
    print("  det x nu x flag:", dict(q))
print("\nTOTAL", dict(tot))
