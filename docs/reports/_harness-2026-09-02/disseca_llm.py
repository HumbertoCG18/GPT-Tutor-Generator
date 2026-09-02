"""Disseca os materiais decididos por LLM (llm / llm-funil) nos 8 repos.

READ-ONLY. Para cada um, re-roda resolve_window + disambiguate SEM voter e
classifica POR QUE o motor se flagou. Compara palpite do motor vs voto do LLM
vs gold (quando ha).
"""
import collections
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.engine import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor.anchor_engine import resolve_window, is_out_of_disamb_scope, resolve_exam_prep  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor.disambiguator import (  # noqa: E402
    MARGIN_TAU, _block_signature, _score, disambiguate, entry_tokens, _EPS,
)
from src.builder.routing.motor.due_window import tier2_due_scope  # noqa: E402
from src.builder.routing.motor.llm_vote import detect_same_theme_series  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}

linhas = []
for sigla, nome in REPOS.items():
    repo = GH / nome
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entries = m["entries"]
    course = str((m.get("course") or {}).get("course_name") or "")
    ctx = build_motor_context(repo, course)
    series = detect_same_theme_series(entries)
    gt = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
    gold = load_labels_csv(gt) if gt.exists() else {}

    def uuid_of(ref):
        b = ctx.block_by_ref(str(ref or ""))
        return str((b or {}).get("block_uuid") or ref or "")

    for e in entries:
        mt = str(e.get("temporal_block_method") or "")
        if mt not in ("llm", "llm-funil"):
            continue
        eid = str(e.get("id"))
        md = _entry_markdown_text_for_file_map(repo, e) or ""
        llm_pick = uuid_of(e.get("temporal_block_id"))
        gold_uuid = uuid_of(gold.get(eid)) if eid in gold else ""
        prova = tier2_due_scope(e)
        window, provider = resolve_window(e, ctx)
        row = {"curso": sigla, "id": eid, "cat": str(e.get("category") or ""), "metodo": mt,
               "provider": provider or "", "janela": len(window or []), "serie": eid in series,
               "prova": prova, "llm_pick": llm_pick, "gold": gold_uuid, "motor_pick": "", "causa": "",
               "s1": 0.0, "s2": 0.0, "margem": 0.0, "secao": str(e.get("source_section") or "")[:40],
               "titulo": str(e.get("title") or "")[:50], "md_chars": len(md)}
        if not window:
            prep = resolve_exam_prep(e, ctx)
            row["causa"] = "sem-janela (funil)"
            if prep is not None:
                row["causa"] = "sem-janela mas prep-prova?"  # nao deveria ocorrer
            linhas.append(row)
            continue
        if prova and len(window) > 1:
            row["causa"] = "prova/trabalho sem due: vota sempre"
            d = disambiguate(e, window, ctx, md, provider=provider)
            row["motor_pick"] = uuid_of(d.block_ref)
            linhas.append(row)
            continue
        d = disambiguate(e, window, ctx, md, provider=provider)
        row["motor_pick"] = uuid_of(d.block_ref)
        blocks = [ctx.block_by_ref(r) for r in window]
        blocks = [b for b in blocks if b]
        mat = entry_tokens(e, md)
        sigs = [_block_signature(b, ctx) for b in blocks]
        df = {}
        for sig in sigs:
            for t in sig:
                df[t] = df.get(t, 0) + 1
        scores = [_score(mat, sig, len(blocks), df) for sig in sigs]
        order = sorted(range(len(blocks)), key=lambda i: scores[i], reverse=True)
        s1 = scores[order[0]] if order else 0.0
        s2 = scores[order[1]] if len(order) > 1 else 0.0
        rel = (s1 - s2) / max(s1, _EPS)
        hits_best = mat & set(sigs[order[0]]) if order else set()
        hits_runner = mat & set(sigs[order[1]]) if len(order) > 1 else set()
        disc = hits_best - hits_runner
        row.update({"s1": round(s1, 2), "s2": round(s2, 2), "margem": round(rel, 2)})
        if d.method == "titulo-topico" or (d.method == "janela-1"):
            row["causa"] = f"serie ({d.method} confiante)" if eid in series else f"?? {d.method}"
        elif not d.flag:
            row["causa"] = "serie (lexico confiante, vota mesmo assim)"
        elif s1 <= 0:
            row["causa"] = "sem-token (material nao casa nenhum bloco)"
        elif not disc:
            row["causa"] = "sem-discriminante (mesmos tokens no 1o e 2o)"
        elif s2 > 0 and rel < MARGIN_TAU:
            row["causa"] = f"margem baixa (<{MARGIN_TAU})"
        else:
            row["causa"] = "outro"
        linhas.append(row)

# ---------- relatorio
print(f"{len(linhas)} materiais decididos por LLM\n")
por_causa = collections.Counter(r["causa"] for r in linhas)
print("CAUSA                                              n   motor=LLM  gold: motor / LLM")
for causa, n in por_causa.most_common():
    rs = [r for r in linhas if r["causa"] == causa]
    igual = sum(1 for r in rs if r["motor_pick"] and r["motor_pick"] == r["llm_pick"])
    com_gold = [r for r in rs if r["gold"]]
    m_ok = sum(1 for r in com_gold if r["motor_pick"] == r["gold"])
    l_ok = sum(1 for r in com_gold if r["llm_pick"] == r["gold"])
    print(f"  {causa:48} {n:>3}   {igual:>3}/{n:<3}    {m_ok:>2}/{len(com_gold):<2} / {l_ok:>2}/{len(com_gold):<2}")

print("\nPROVIDER da janela (onde ha janela):")
for (prov, tam), n in sorted(collections.Counter((r["provider"], min(r["janela"], 6)) for r in linhas if r["janela"]).items()):
    print(f"  {prov:10} janela={tam}{'+' if tam == 6 else ' '}  {n}")

print("\nSEM JANELA (funil) por curso/categoria:")
for k, n in collections.Counter(f"{r['curso']}/{r['cat']}" for r in linhas if not r["janela"]).most_common():
    print(f"  {k:32} {n}")

print("\nDETALHE (uma linha por material):")
print(f"{'curso':4} {'id':40} {'cat':16} {'prov':7} {'jan':>3} {'s1':>5} {'s2':>5} {'mrg':>5} {'m=L':>3} {'gold':>5} causa")
for r in sorted(linhas, key=lambda r: (r["causa"], r["curso"], r["id"])):
    ml = "=" if r["motor_pick"] and r["motor_pick"] == r["llm_pick"] else ("-" if r["motor_pick"] else " ")
    g = ""
    if r["gold"]:
        g = ("M" if r["motor_pick"] == r["gold"] else "m") + ("L" if r["llm_pick"] == r["gold"] else "l")
    print(f"{r['curso']:4} {r['id'][:40]:40} {r['cat'][:16]:16} {r['provider'][:7]:7} {r['janela']:>3} "
          f"{r['s1']:>5} {r['s2']:>5} {r['margem']:>5} {ml:>3} {g:>5} {r['causa'][:34]}")

out = Path(__file__).with_name("disseca_llm.csv")
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
    w.writeheader()
    w.writerows(linhas)
print(f"\ncsv: {out}")
