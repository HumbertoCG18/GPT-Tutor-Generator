"""REGUA DE MATERIAIS DE AULA (read-only, copias .ablacao = motor puro): golds separados em AULA / REFERENCIA / BASE.
Linha unica "motor puro hoje" (TODOS / AULA / REF / BASE), o RESTO em AULA por categoria x metodo e quantos seguem
flagados (fila do LLM/humano).

Escada podada em 04/09 (C0 item 9): H1 e H7 refutados no gold (0/0), H9 (card ordenado) e H8 (tokens curtos) ja sao
producao desde a Fase 3 — a escada recalculava alavancas com picks velhos (`moodle_sections/picks_*.json`) e imprimia
170/189 enquanto o motor puro dava 174/189. Vale so o numero do motor puro gravado.
"""
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402

COPY = GEN / ".ablacao"
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
REF = {"bibliografia", "referencias", "references"}
BASE = {"cronograma", "plano-de-ensino", "plano"}


def grupo(e):
    cat = str(e.get("category") or "").strip().lower()
    if cat in REF or str(e.get("file_type") or "") == "url":
        return "REF"
    if cat in BASE or str(e.get("temporal_block_method") or "") == "meta-generica":
        return "BASE"
    return "AULA"


G = []
for sig, nome in REPOS.items():
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    ents = {e["id"]: e for e in man["entries"]}
    preds = load_predictions(repo)
    labels = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    for eid, gold in labels.items():
        e = ents.get(eid); p = preds.get(eid)
        if not e or not p:
            continue
        win = [str(w) for w in (e.get("temporal_block_window") or [])]
        G.append({"sig": sig, "id": eid, "gold": gold, "pred": p["block_id"], "grupo": grupo(e),
                  "cat": str(e.get("category") or ""), "method": str(e.get("temporal_block_method") or "SEM-BLOCO"),
                  "flag": bool(e.get("temporal_block_flag")), "janela": sum(1 for r in win if ctx.block_by_ref(r) is not None),
                  "card": str(e.get("source_section") or "")})

cats = collections.Counter((g["grupo"], g["cat"]) for g in G)
print("CATEGORIAS por grupo:", {gr: {c: n for (gg, c), n in cats.items() if gg == gr} for gr in ("AULA", "REF", "BASE")})
for gr in ("TODOS", "AULA", "REF", "BASE"):
    gs = [g for g in G if gr == "TODOS" or g["grupo"] == gr]
    ok = sum(g["pred"] == g["gold"] for g in gs)
    print(f"  {'motor puro hoje':44} {gr:5} {ok:>3}/{len(gs):<3} {ok / max(len(gs), 1):.1%}", end="")
print()

print("\nRESTO em AULA (o que ainda erra), por categoria x metodo:")
resto = [g for g in G if g["grupo"] == "AULA" and g["pred"] != g["gold"]]
for g in sorted(resto, key=lambda g: (g["cat"], g["sig"])):
    print(f"  {g['sig']:3} {g['id'][:40]:40} cat={g['cat'][:16]:16} metodo={g['method']:10} flag={'S' if g['flag'] else 'n'} janela={g['janela']} card={g['card'][:26]!r}")
flag_aula = [g for g in G if g["grupo"] == "AULA" and (g["flag"] or g["method"] == "SEM-BLOCO")]
err_flag = sum(g["pred"] != g["gold"] for g in flag_aula)
n_aula = sum(1 for g in G if g["grupo"] == "AULA")
print(f"\nAULA: {n_aula} golds | flagados/sem bloco no motor puro: {len(flag_aula)} ({100 * len(flag_aula) / n_aula:.1f}/100), "
      f"dos quais errados {err_flag} | erros CONFIANTES: {len(resto) - err_flag}")
