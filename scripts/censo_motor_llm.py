"""Censo motor x LLM por eixo + fila `revisar`, nos 8 repos. READ-ONLY (le manifests + gold).
Promovido do scratchpad em 02/09 (Fase 0 do plano).

    python scripts/censo_motor_llm.py                       # originais (regua curada)
    TUTOR_REPOS_DIR=.ablacao python scripts/censo_motor_llm.py   # copias (motor puro)

Metrica de PRODUTO (decisao B, 02/09): `revisar` por 100 materiais = camadas duvida + llm.
Calculado pela funcao pura `routing.revisar.revisar_de` sobre o entry gravado (mesma
que o reprocess persiste no campo `revisar`), entao vale mesmo em manifest antigo.
"""
from __future__ import annotations

import collections
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_ground_truth import (  # noqa: E402
    evaluate_ground_truth, load_block_period_map, load_labels_csv, load_pair_keys, load_predictions,
)
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.routing.revisar import DUVIDA, LLM, motivos_de, revisar_de  # noqa: E402

GH = Path(os.environ.get("TUTOR_REPOS_DIR") or ROOT.parent)
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
MOTOR = {"janela-1", "disamb", "prep-prova", "irmao-card", "titulo-topico", "ref-generica",
         "due-contain", "due-straddle", "d6", "funil", "meta-generica"}


def main() -> int:
    tot_m = collections.Counter()
    tot_src = collections.defaultdict(lambda: {"correct": 0, "wrong": 0})
    tot = collections.Counter()
    motivos = collections.Counter()
    print(f"{'curso':5} {'mat':>4} | {'BLOCO motor':>11} {'llm-jan':>8} {'llm-funil':>9} {'pino':>5} {'vazio':>5} | "
          f"{'UNID manual':>11} {'auto':>5} {'vazio':>5} | {'SUB tag':>7} {'vazio':>5} | {'gemini':>6} | "
          f"{'REVISAR duvida':>14} {'llm':>4} {'/100':>5}")
    for sigla, nome in REPOS.items():
        repo = GH / nome
        if not (repo / "manifest.json").exists():
            print(f"{sigla:5} (sem manifest em {repo})")
            continue
        m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        ents = [e for e in m["entries"] if _is_material(e)]
        cc = repo / "code_curation.json"
        gemini = 0
        if cc.exists():
            recs = (json.loads(cc.read_text(encoding="utf-8")).get("entries") or {})
            gemini = sum(1 for e in ents if str(e.get("id")) in recs)
        meth = collections.Counter(str(e.get("temporal_block_method") or "") for e in ents)
        pinos = sum(1 for e in ents if str(e.get("manual_timeline_block_id") or "").strip())
        b_motor = sum(v for k, v in meth.items() if k in MOTOR)
        b_llm = meth.get("llm", 0)
        b_funil = meth.get("llm-funil", 0)
        b_vazio = sum(1 for e in ents if not str(e.get("temporal_block_id") or e.get("manual_timeline_block_id") or "").strip())
        u_manual = sum(1 for e in ents if str(e.get("manual_unit_slug") or "").strip())
        u_vazio = sum(1 for e in ents if not str(e.get("computed_unit_slug") or "").strip())
        u_auto = len(ents) - u_manual - u_vazio
        s_tag = sum(1 for e in ents if str(e.get("computed_subunit_slug") or "").strip())
        s_vazio = len(ents) - s_tag
        rev = collections.Counter(revisar_de(e) for e in ents)
        for e in ents:
            motivos.update(motivos_de(e))
        r_duv, r_llm = rev.get(DUVIDA, 0), rev.get(LLM, 0)
        r100 = 100.0 * (r_duv + r_llm) / max(len(ents), 1)
        tot_m.update(meth)
        tot.update({"mat": len(ents), "b_motor": b_motor, "b_llm": b_llm, "b_funil": b_funil, "pinos": pinos,
                    "b_vazio": b_vazio, "u_manual": u_manual, "u_auto": u_auto, "u_vazio": u_vazio,
                    "s_tag": s_tag, "s_vazio": s_vazio, "gemini": gemini, "r_duv": r_duv, "r_llm": r_llm})
        print(f"{sigla:5} {len(ents):>4} | {b_motor:>11} {b_llm:>8} {b_funil:>9} {pinos:>5} {b_vazio:>5} | "
              f"{u_manual:>11} {u_auto:>5} {u_vazio:>5} | {s_tag:>7} {s_vazio:>5} | {gemini:>6} | "
              f"{r_duv:>14} {r_llm:>4} {r100:>5.0f}")
        gt = ROOT / "docs" / "reports" / f"ground_truth_{sigla}.csv"
        if gt.exists():
            rep = evaluate_ground_truth(load_predictions(repo), load_labels_csv(gt), load_block_period_map(repo),
                                        pair_keys=load_pair_keys(gt))
            for src, v in (rep.get("sources") or {}).items():
                tot_src[src]["correct"] += v["correct"]
                tot_src[src]["wrong"] += v["wrong"]
    T = tot
    n = max(T["mat"], 1)
    r100 = 100.0 * (T["r_duv"] + T["r_llm"]) / n
    print(f"{'TOTAL':5} {T['mat']:>4} | {T['b_motor']:>11} {T['b_llm']:>8} {T['b_funil']:>9} {T['pinos']:>5} {T['b_vazio']:>5} | "
          f"{T['u_manual']:>11} {T['u_auto']:>5} {T['u_vazio']:>5} | {T['s_tag']:>7} {T['s_vazio']:>5} | {T['gemini']:>6} | "
          f"{T['r_duv']:>14} {T['r_llm']:>4} {r100:>5.0f}")
    print(f"\nBLOCO nos 8 ({n} materiais): motor {T['b_motor']} ({T['b_motor']/n:.0%}) · llm-na-janela {T['b_llm']} "
          f"({T['b_llm']/n:.0%}) · llm-funil {T['b_funil']} ({T['b_funil']/n:.0%}) · pinos {T['pinos']} · sem bloco {T['b_vazio']}")
    print(f"REVISAR por 100 materiais: {r100:.1f}  (duvida {T['r_duv']} + llm {T['r_llm']} de {n}) · "
          f"votos por 100: {100.0 * (T['b_llm'] + T['b_funil']) / n:.1f}")
    print(f"anatomia da duvida (gatilhos, um material pode ter >1): {dict(motivos.most_common())}")
    print(f"metodos: {dict(tot_m.most_common())}")
    if tot_src:
        print("\nACERTO POR FONTE no gold de bloco:")
        for src, v in sorted(tot_src.items(), key=lambda x: -(x[1]['correct'] + x[1]['wrong'])):
            n_ = v["correct"] + v["wrong"]
            print(f"  {src:16} {v['correct']:>3}/{n_:<3} {v['correct']/max(n_,1):.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
