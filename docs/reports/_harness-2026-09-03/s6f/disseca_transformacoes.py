"""Disseca a decisao `disamb` do transformacoesgl (rebuild) x transformacoes-geometricas-em-opengl (export):
mesmo caminho do apply (build_motor_context + _entry_markdown_text_for_file_map + _lexical_decision), por bloco da janela.
Read-only."""
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor import disambiguator as D  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402

CASES = (("EXPORT puro", GEN / ".ablacao/Computacao-Grafica-Tutor", "transformacoes-geometricas-em-opengl"),
         ("REBUILD puro", GEN / ".ablacao/CG-rebuild-holdout/Computacao-Grafica-Tutor", "transformacoesgl"))

for label, repo, eid in CASES:
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    e = next(x for x in man["entries"] if x["id"] == eid)
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    md = _entry_markdown_text_for_file_map(repo, e) or ""
    win = list(e.get("temporal_block_window") or [])
    blocks = [b for b in (ctx.block_by_ref(r) for r in win) if b is not None]
    mat = D.entry_tokens(e, md)
    sigs = [D._block_signature(b, ctx) for b in blocks]
    m = len(blocks)
    df = {}
    for sig in sigs:
        for t in sig:
            df[t] = df.get(t, 0) + 1
    scores = [D._score(mat, sig, m, df) for sig in sigs]
    print(f"=== {label} {eid} | md {len(md)} chars | tokens do material {len(mat)} | janela {win}")
    for b, sig, sc in sorted(zip(blocks, sigs, scores), key=lambda x: -x[2]):
        hits = sorted(mat & set(sig))
        print(f"  {b['id']:9} score={sc:.4f} hits={[(h, sig[h], df[h]) for h in hits]}")
    order = sorted(range(m), key=lambda i: scores[i], reverse=True)
    s1, s2 = scores[order[0]], scores[order[1]] if m > 1 else 0.0
    rel = (s1 - s2) / max(s1, D._EPS)
    hb = mat & set(sigs[order[0]])
    hr = mat & set(sigs[order[1]]) if m > 1 else set()
    print(f"  s1={s1:.4f} s2={s2:.4f} rel_margin={rel:.3f} discriminante={sorted(hb - hr)} exclusivo={s2 <= 0 and m >= 2} MARGIN_TAU={D.MARGIN_TAU}")
    dec = D._lexical_decision(e, blocks, ctx, md, win)
    print(f"  decisao: {dec.block_ref} band={dec.band} flag={dec.flag} conf={dec.conf:.3f}")
    # onde o material toca QUALQUER assinatura do curso (fora da janela tambem)
    alls = {b["id"]: D._block_signature(b, ctx) for b in ctx.blocks}
    touched = {bid: sorted(mat & set(sig)) for bid, sig in alls.items() if mat & set(sig)}
    print(f"  toca assinaturas (curso inteiro): {touched}")
    print(f"  '2d' no material? {'2d' in mat} | tokens com 'geometr': {sorted(t for t in mat if 'geometr' in t)} | 'instanciamento' in md: {'instanciamento' in md.lower()}")
