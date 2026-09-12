"""Projeta a regua de subunidade (93 golds) sob scorer-dedupe + limiar variavel.

READ-ONLY. Para cada linha scorable do gold: recomputa pred com o scorer atual
e com o dedupe, aplicando a regra de ambiguidade/gate de auto_map_entry_subtopic.
Entries cuja rota passa por code_curation/markdown externo podem divergir do
manifest no scorer ATUAL — quando divergir, marca SIM-INFIEL (conferir no
reprocess real).
"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))

import json

from sim_dedupe import score_dedupe  # noqa: E402
from src.builder.engine import _iter_content_taxonomy_topics
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
from src.builder.routing.resolver_apply import assemble_resolver_inputs
from src.builder.routing.thresholds import T
from src.builder.timeline.index import _score_entry_against_taxonomy_topic

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
REPORTS = ROOT / "docs" / "reports"
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
LIMIAR_NOVO = float(sys.argv[1]) if len(sys.argv) > 1 else 0.12


def pred_com(scorer, signals, topics, limiar):
    scored = sorted(((t, scorer(signals, t)) for t in topics), key=lambda x: -x[1])
    if not scored:
        return "", 0.0, "sem-topicos"
    winner, ws = scored[0]
    rs = scored[1][1] if len(scored) > 1 else 0.0
    if ws <= 0.0:
        return "", 0.0, "sem-sinal"
    if len(scored) > 1 and ws - rs == 0.0:
        return "", 0.0, "empate"
    rel = (ws - rs) / max(ws, 1e-6)
    if len(scored) == 1:
        conf, amb = 0.72, False
    else:
        conf, amb = max(0.0, min(1.0, rel)), rel < limiar
    if amb or conf < T.SUBUNIT_TAG:
        return "", conf, "ambiguo" if amb else "gate"
    return str(winner["topic_slug"]), conf, ""


tot = {"atual": 0, "novo": 0}
n_tot = 0
infieis = []
flips = []
for sigla, repo_nome in REPOS.items():
    repo = GH / repo_nome
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entries = {str(e.get("id")): e for e in manifest["entries"]}
    cc = repo / "code_curation.json"
    code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}
    taxonomy = load_internal_content_taxonomy(repo) or {}
    todos_topicos = _iter_content_taxonomy_topics(taxonomy)
    with open(REPORTS / f"subunit_gt_{sigla}.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["scorable"] != "yes":
                continue
            n_tot += 1
            e = entries.get(r["entry_id"])
            if e is None:
                continue
            extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
            alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
            manifest_pred = str(e.get("computed_subunit_slug") or "")
            unidade = str(e.get("computed_unit_slug") or "")
            topics = [t for t in todos_topicos if t["unit_slug"] == unidade]
            _, signals, _ = assemble_resolver_inputs(repo, e, code_curation)
            pa, ca, ra = pred_com(_score_entry_against_taxonomy_topic, signals, topics, 0.15)
            pn, cn, rn = pred_com(score_dedupe, signals, topics, LIMIAR_NOVO)
            if pa != manifest_pred:
                infieis.append(f"{sigla} {r['entry_id'][:40]}: sim={pa or '(vazio)'} manifest={manifest_pred or '(vazio)'}")
                # rota infiel: usa manifest como baseline e pula projecao
                tot["atual"] += manifest_pred in alvo
                tot["novo"] += manifest_pred in alvo
                continue
            ok_a = pa in alvo
            ok_n = pn in alvo
            tot["atual"] += ok_a
            tot["novo"] += ok_n
            if ok_a != ok_n or pa != pn:
                flips.append(f"{sigla} {r['entry_id'][:40]}: {pa or '(vazio)'}({'OK' if ok_a else 'ERRO'})"
                             f" -> {pn or '(vazio)'}({'OK' if ok_n else 'ERRO'}) conf {ca:.2f}->{cn:.2f} [{rn}]")

print(f"limiar novo = {LIMIAR_NOVO}")
print(f"ATUAL (sim, limiar 0.15): {tot['atual']}/{n_tot}")
print(f"DEDUPE (limiar {LIMIAR_NOVO}): {tot['novo']}/{n_tot}")
print(f"\nFLIPS ({len(flips)}):")
for f_ in flips:
    print(" ", f_)
print(f"\nSIM-INFIEL ({len(infieis)}) — baseline manifest mantido, conferir no reprocess:")
for f_ in infieis:
    print(" ", f_)
