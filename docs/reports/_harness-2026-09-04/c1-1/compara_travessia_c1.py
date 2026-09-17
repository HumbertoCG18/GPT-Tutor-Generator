"""C0 item 12: travessia ANTES = item 12 da C0 (05/09, JSONs no HEAD) x DEPOIS = C1 item 1 (FILE_MAP completo) x DEPOIS (JSONs novos).
Por curso x modo: hit@1, hit@3, bloco, por estilo; flips por pergunta quando o JSON do HEAD corresponde a tabela."""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# tabela "antes" do tracker (hit1, hit3, bloco_ok/bloco_n, estruturada, ambigua, malformada)
ANTES = {
    ("FR", "sem-llm"): (9, 11, "5/6", 4, 2, 3), ("FR", "llm"): (15, 15, "6/6", 5, 5, 5), ("FR", "llm-completo"): (15, 15, "5/6", 5, 5, 5),
    ("IA", "sem-llm"): (10, 12, "6/8", 4, 1, 5), ("IA", "llm"): (9, 10, "8/8", 3, 2, 4), ("IA", "llm-completo"): (10, 10, "8/8", 3, 2, 5),
    ("CG", "sem-llm"): (5, 6, "10/11", 4, 0, 1), ("CG", "llm"): (7, 7, "8/11", 2, 3, 2), ("CG", "llm-completo"): (7, 8, "7/11", 2, 3, 2),
}


def load_head(sig, modo):
    r = subprocess.run(["git", "-C", str(GEN), "show", f"HEAD:docs/reports/travessia_result_{sig}_{modo}.json"], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def estilo(d):
    c = Counter(); n = Counter()
    for l in d.get("linhas", []):
        n[l.get("estilo")] += 1; c[l.get("estilo")] += int(bool(l.get("hit1")))
    return c, n


print(f"{'curso':5} {'modo':13} | {'hit@1 antes->depois':22} {'hit@3':14} {'bloco':12} | estrut  ambig  malf   | chamadas")
for (sig, modo), (h1, h3, bl, es, am, ma) in ANTES.items():
    p = GEN / "docs/reports" / f"travessia_result_{sig}_{modo}.json"
    if not p.exists():
        print(f"{sig:5} {modo:13} | (sem resultado novo)"); continue
    d = json.loads(p.read_text(encoding="utf-8"))
    c, n = estilo(d)
    print(f"{sig:5} {modo:13} | {h1:>2}/15 -> {d['hit1']:>2}/15 {'':8} {h3:>2} -> {d['hit3']:>2}     {bl:>5} -> {d['bloco_ok']}/{d['bloco_n']:<3} | "
          f"{es}->{c['estruturada']}   {am}->{c['ambigua']}   {ma}->{c['malformada']}   | {d.get('chamadas')}")
    head = load_head(sig, modo)
    if head and (head.get("hit1"), head.get("hit3")) == (h1, h3):
        hb = {l["pergunta"]: l for l in head.get("linhas", [])}
        for l in d.get("linhas", []):
            a = hb.get(l["pergunta"])
            if a and bool(a.get("hit1")) != bool(l.get("hit1")):
                print(f"      flip {'+' if l.get('hit1') else '-'} [{l.get('estilo')}] {l['pergunta'][:58]!r} esperado={l.get('esperado')} antes={a.get('escolhido', [])[:2]} depois={l.get('escolhido', [])[:2]}")
    else:
        print(f"      (JSON do HEAD nao bate com a tabela 'antes' — hit1 {head.get('hit1') if head else '?'}; sem flips por pergunta)")
