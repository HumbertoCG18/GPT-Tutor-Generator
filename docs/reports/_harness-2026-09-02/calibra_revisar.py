"""Fase 0 (02/09). Calibra os gatilhos de `revisar` contra o gold: precisao (gatilho -> erro real?) e
recall (erro real -> algum gatilho?) por eixo. READ-ONLY.

    python calibra_revisar.py [repos_dir]     # default: originais (curado); passe .ablacao p/ motor puro
"""
import collections
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402

GH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
SUB = {"SO", "IA", "ES2", "TCC"}


def gatilhos(e):
    g = motivos_de(e)
    if str(e.get("temporal_block_method") or "") == "llm":
        g.append("llm")
    return g


rows = []  # (curso, id, gatilhos, erros)
for sig, nome in REPOS.items():
    repo = GH / nome
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ents = {str(e["id"]): e for e in m["entries"] if _is_material(e)}
    preds = load_predictions(repo)
    labels = load_labels_csv(ROOT / "docs/reports" / f"ground_truth_{sig}.csv")
    truth_u = _load_truth(sig)
    gold_sub = {}
    if sig in SUB:
        with open(ROOT / "docs/reports" / f"subunit_gt_{sig}.csv", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["scorable"] == "yes":
                    extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
                    gold_sub[r["entry_id"]] = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
    for eid, e in ents.items():
        erros = []
        if eid in labels and preds.get(eid, {}).get("block_id") != labels[eid]:
            erros.append("bloco")
        if eid in truth_u and str(e.get("computed_unit_slug") or "") != truth_u[eid]:
            erros.append("unidade")
        if eid in gold_sub and str(e.get("computed_subunit_slug") or "") not in gold_sub[eid]:
            erros.append("subunidade")
        tem_gold = (eid in labels) or (eid in truth_u) or (eid in gold_sub)
        rows.append((sig, eid, gatilhos(e), erros, tem_gold, revisar_de(e)))

print(f"repos: {GH}")
print(f"\n{'GATILHO':16}{'n':>5}{'c/gold':>8}{'erro-qualquer':>15}{'prec':>7} | erro bloco / unid / sub")
por_g = collections.defaultdict(list)
for sig, eid, gs, errs, tg, rv in rows:
    for g in gs:
        por_g[g].append((errs, tg))
for g, lst in sorted(por_g.items(), key=lambda x: -len(x[1])):
    cg = [errs for errs, tg in lst if tg]
    err = sum(1 for errs in cg if errs)
    b = sum(1 for errs in cg if "bloco" in errs); u = sum(1 for errs in cg if "unidade" in errs)
    s = sum(1 for errs in cg if "subunidade" in errs)
    print(f"{g:16}{len(lst):>5}{len(cg):>8}{err:>15}{err / max(len(cg), 1):>7.0%} | {b:>4} / {u:>4} / {s:>3}")

print("\nRECALL por eixo (erro real -> em qual camada cai):")
for eixo in ("bloco", "unidade", "subunidade"):
    errs = [(sig, eid, gs, rv) for sig, eid, gs, e2, tg, rv in rows if eixo in e2]
    cam = collections.Counter(rv for _, _, _, rv in errs)
    print(f"  {eixo:11} erros={len(errs):>3}  duvida={cam.get('duvida', 0):>3}  llm={cam.get('llm', 0):>3}  ok={cam.get('ok', 0):>3}")
    escapes = [(sig, eid, gs) for sig, eid, gs, rv in errs if rv == "ok"]
    if escapes:
        print(f"    escapam (ok): {', '.join(f'{s}:{i}' for s, i, _ in escapes[:14])}{' ...' if len(escapes) > 14 else ''}")

tot = collections.Counter(rv for *_, rv in rows)
n = len(rows)
print(f"\nrevisar nos 5 c/ gold ({n} materiais): duvida {tot['duvida']} · llm {tot['llm']} · ok {tot['ok']} "
      f"-> {100 * (tot['duvida'] + tot['llm']) / n:.1f}/100")
