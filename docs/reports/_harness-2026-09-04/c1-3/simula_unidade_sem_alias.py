"""Mapa bloco->unidade (DP + ancora) nos 8 tutores, em memoria, com variantes de `_unit_tokens`/`_tokens` do unit_matcher:
  base  = oficial (deve reproduzir o unit_slug gravado)
  NA    = unidade tokenizada so pelo PLANO (titulo + labels dos topicos), SEM aliases compilados por LLM
  ST    = radicais (6 chars) dos dois lados (bloco e unidade)
  NA+ST = as duas
Mede: reproducao; blocos mudados; pinos manuais de unidade (verdade humana, 7 tutores); regua de UNIDADE (5 golds, entries que
seguem o bloco herdam); CG: os 22 do gold de subunidade proposto (UNIDADE ERRADA) por bloco. Uso: simula_unidade_sem_alias.py <snapshot_antes>"""
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
SNAP = Path(sys.argv[1])
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_predictions  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.timeline import unit_matcher as um  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
_tokens_orig, _unit_tokens_orig = um._tokens, um._unit_tokens


def _unit_tokens_plano(unit):
    parts = [str(unit.get("title", "") or "")] + [str(t.get("label", "") or "") for t in (unit.get("topics") or []) if isinstance(t, dict)]
    return um._tokens(" ".join(parts)) - um._UNIT_GENERIC


def _tokens_stem(text):
    return {t[:6] for t in _tokens_orig(text)}


VARS = {"base": (_tokens_orig, _unit_tokens_orig), "NA": (_tokens_orig, _unit_tokens_plano),
        "ST": (_tokens_stem, _unit_tokens_orig), "NA+ST": (_tokens_stem, _unit_tokens_plano)}


def run(cands, units, var):
    um._tokens, um._unit_tokens = VARS[var]
    try:
        out = um.assign_units_positional(cands, units)
    finally:
        um._tokens, um._unit_tokens = _tokens_orig, _unit_tokens_orig
    return [s for s, _ in out] if out else None


cg_truth = {}
for r in csv.DictReader((GEN / "docs/reports/subunit_gt_CG.csv").open(encoding="utf-8-sig", newline="")):
    m = re.search(r"= u0(\d)|\(u0(\d)\)|u0(\d)/", r["notas"])
    if "UNIDADE ERRADA" in r["notas"] and m:
        cg_truth[r["entry_id"]] = "unidade-0" + next(g for g in m.groups() if g)

TOT = {v: {"pins_ok": 0, "mud": 0, "uni_ok": 0, "cg_ok": 0} for v in VARS}
pins_n = uni_n = cg_n = 0
for sig, name in REPOS.items():
    root = GH / name
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    units = list(json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8")).get("units") or [])
    cands = [b for b in blocks if not b.get("source_kind")]
    if len(units) < 2 or not cands:
        print(f"== {sig}: fora"); continue
    res = {v: run(cands, units, v) for v in VARS}
    if res["base"] is None:
        print(f"== {sig}: sem afinidade"); continue
    gravado = [str(b.get("auto_unit_slug") or b.get("unit_slug") or "") for b in cands]
    rep = sum(1 for k in range(len(cands)) if res["base"][k] == gravado[k])
    pins = [(k, str(b.get("block_manual_unit_slug") or "")) for k, b in enumerate(cands) if str(b.get("block_manual_unit_slug") or "")]
    pins_n += len(pins)
    line = f"== {sig}: blocos-aula {len(cands)} | reproduz gravado {rep}/{len(cands)} | pinos {len(pins)}:"
    for v in VARS:
        r = res[v] or res["base"]
        ok = sum(1 for k, p in pins if r[k] == p)
        mud = sum(1 for k in range(len(cands)) if r[k] != res["base"][k])
        TOT[v]["pins_ok"] += ok
        TOT[v]["mud"] += mud
        line += f" {v} {ok}/{len(pins)} mud {mud} ·"
    print(line)
    for k, b in enumerate(cands):
        if any((res[v] or res["base"])[k] != res["base"][k] for v in VARS) or k in dict(pins):
            pin = dict(pins).get(k, "")
            print(f"     {str(b.get('id')):8} '{str(b.get('primary_topic_label'))[:26]:26}' " + " ".join(f"{v}={(res[v] or res['base'])[k][8:24]:16}" for v in VARS) + f" pino={pin[8:24] if pin else '-'}")
    # regua de unidade (5 golds): entries que seguem o bloco herdam a unidade nova
    truth = _load_truth(sig) if sig in ("MF", "SO", "IA", "ES2", "TCC") else {}
    if sig == "CG":
        truth = {}
        man_cg = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        for eid, e in man_cg.items():
            if _is_material(e) and e.get("computed_unit_slug"):
                truth[eid] = cg_truth.get(eid, e["computed_unit_slug"])
    mp = SNAP / name / "manifest.json"
    src_root = SNAP / name if mp.exists() else root
    if truth and (src_root / "manifest.json").exists():
        ents = {e["id"]: e for e in json.loads((src_root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        preds = load_predictions(src_root)
        uob = {}
        for k, b in enumerate(cands):
            for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
                uob[key] = {v: (res[v] or res["base"])[k] for v in VARS}
        flips = {v: [] for v in VARS}
        for eid, want in truth.items():
            e = ents.get(eid)
            if not e or not _is_material(e):
                continue
            got = str(e.get("computed_unit_slug") or "")
            trio = uob.get(preds.get(eid, {}).get("block_id", ""))
            for v in VARS:
                val = trio[v] if (trio and got == trio["base"]) else got
                okv = val.startswith(want) if sig == "CG" else (val == want)
                if sig == "CG":
                    TOT[v]["cg_ok"] += okv
                else:
                    TOT[v]["uni_ok"] += okv
                if v != "base" and okv != (got.startswith(want) if sig == "CG" else got == want):
                    flips[v].append(f"{eid[:26]}:{'+' if okv else '-'}")
            if sig == "CG":
                cg_n += 1
            else:
                uni_n += 1
        for v in VARS:
            if v != "base" and flips[v]:
                print(f"     flips {v}: {flips[v][:14]}")
print("\nTOTAL:", " | ".join(f"{v}: pinos {TOT[v]['pins_ok']}/{pins_n} · blocos mudados {TOT[v]['mud']} · unidade(5 golds) {TOT[v]['uni_ok']}/{uni_n} · CG(93, 22 propostos) {TOT[v]['cg_ok']}/{cg_n}" for v in VARS))
