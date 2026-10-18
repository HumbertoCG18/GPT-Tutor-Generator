"""Quantos "disamb" ALTA (sem flag) repousam em 1 so token de contato (regra `exclusivo`, s2=0) e quantos deles erram o gold?
Copias .ablacao (motor puro) dos 5 cursos + CG export (puro) + CG rebuild (holdout puro). Read-only."""
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_predictions  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor import disambiguator as D  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402

S = Path(__file__).parent
CASES = [
    ("MF", GEN / ".ablacao/Metodos-Formais-Tutor", GEN / "docs/reports/ground_truth_MF.csv"),
    ("SO", GEN / ".ablacao/Sistemas-Operacionais-Tutor", GEN / "docs/reports/ground_truth_SO.csv"),
    ("IA", GEN / ".ablacao/Inteligencia-Artifical-Tutor", GEN / "docs/reports/ground_truth_IA.csv"),
    ("ES2", GEN / ".ablacao/Engenharia-Software-2-Tutor", GEN / "docs/reports/ground_truth_ES2.csv"),
    ("TCC", GEN / ".ablacao/TCC-Tutor", GEN / "docs/reports/ground_truth_TCC.csv"),
    ("CG-export", GEN / ".ablacao/Computacao-Grafica-Tutor", GEN / "docs/reports/ground_truth_CG.csv"),
    ("CG-rebuild", GEN / ".ablacao/CG-rebuild-holdout/Computacao-Grafica-Tutor", S / "ground_truth_CG.rebuild.csv"),
]

tot = {"alta": 0, "excl1": 0, "excl1_wrong": 0, "excl2+": 0, "excl2+_wrong": 0, "margem": 0, "margem_wrong": 0, "sem_gold": 0}
for name, repo, gold_path in CASES:
    if not (repo / "manifest.json").exists():
        print(f"{name}: sem copia em {repo}")
        continue
    gold = {}
    with gold_path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("scorable", "yes") == "yes" and r.get("true_block_id"):
                gold[r["id"].strip()] = r["true_block_id"].strip()
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    preds = load_predictions(repo)
    rows = []
    for e in man["entries"]:
        if str(e.get("temporal_block_method") or "") not in ("disamb", "disamb-curto") or e.get("temporal_block_flag"):
            continue
        win = list(e.get("temporal_block_window") or [])
        blocks = [b for b in (ctx.block_by_ref(r) for r in win) if b is not None]
        if len(blocks) < 2:
            continue
        md = _entry_markdown_text_for_file_map(repo, e) or ""
        short = D.course_short_vocab(ctx) if e.get("temporal_block_method") == "disamb-curto" else frozenset()
        mat = D.entry_tokens(e, md, short)
        sigs = [D._block_signature(b, ctx, short) for b in blocks]
        m = len(blocks)
        df = {}
        for sig in sigs:
            for t in sig:
                df[t] = df.get(t, 0) + 1
        scores = [D._score(mat, sig, m, df) for sig in sigs]
        order = sorted(range(m), key=lambda i: scores[i], reverse=True)
        s2 = scores[order[1]]
        hits = sorted(mat & set(sigs[order[0]]))
        pred = preds.get(e["id"], {}).get("block_id", "")
        g = gold.get(e["id"])
        ok = None if g is None else (pred == g)
        excl = s2 <= 0
        bucket = ("excl1" if len(hits) == 1 else "excl2+") if excl else "margem"
        tot["alta"] += 1
        if g is None:
            tot["sem_gold"] += 1
        else:
            tot[bucket] += 1
            if not ok:
                tot[bucket + "_wrong"] += 1
        rows.append((e["id"], bucket, hits, pred, g, ok))
    n = len(rows)
    wg = [r for r in rows if r[5] is not None]
    print(f"== {name}: disamb alta {n} (com gold {len(wg)}) | excl1 {sum(1 for r in wg if r[1] == 'excl1')} "
          f"(erradas {sum(1 for r in wg if r[1] == 'excl1' and not r[5])}) | excl2+ {sum(1 for r in wg if r[1] == 'excl2+')} "
          f"(erradas {sum(1 for r in wg if r[1] == 'excl2+' and not r[5])}) | margem {sum(1 for r in wg if r[1] == 'margem')} "
          f"(erradas {sum(1 for r in wg if r[1] == 'margem' and not r[5])})")
    for r in rows:
        if r[5] is False:
            print(f"     ERRADA {r[0][:44]:44} {r[1]:7} hits={r[2]} pred={r[3]} gold={r[4]}")
    for r in rows:
        if r[1] == "excl1" and r[5]:
            print(f"     certa  {r[0][:44]:44} excl1   hits={r[2]} pred={r[3]}")
print("TOTAL:", tot)
