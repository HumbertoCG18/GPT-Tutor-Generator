"""Duas correcoes de RAIZ sem LLM para o mapa bloco->unidade, simuladas em memoria nos 8 tutores:
  H  = higiene do vocab compilado: sinonimo que e nome de SECAO do Moodle (sem numeracao) ou titulo/label de material NAO vira alias
  V  = preenchimento pelo VIZINHO ancorado: ancora (regra do item 10) decide o proprio bloco; bloco sem ancora herda a unidade do
       bloco ancorado mais proximo ANTES (senao, depois); sem DP monotonica
  VX = V com exclusividade relaxada: token exclusivo de 2 unidades nao bloqueia se a unidade argmax tem margem >= 2 sobre a outra
  H+V, H+VX
Mede: pinos manuais (13, verdade humana), regua de UNIDADE (5 golds, entries que seguem o bloco herdam), CG 22 propostos (por bloco), blocos
mudados. Uso: simula_raiz_unidade.py <snapshot_antes> [sec-only]"""
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
SNAP = Path(sys.argv[1])
SEC_ONLY = "sec-only" in sys.argv[2:]  # higiene so por nome de secao (titulos/labels de material ficam)
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_predictions  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.timeline import unit_matcher as um  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}


def strip_num(s):
    return re.sub(r"^\s*\d+(\.\d+)*\s*[-–.:)]?\s*", "", str(s or ""))


def higiene(units, man):
    secs = {N(strip_num(e.get("source_section"))) for e in man if e.get("source_section")}
    titles = set()
    for e in man:
        ml = e.get("moodle_label")
        ml = ml.get("text") if isinstance(ml, dict) else ml
        for x in (e.get("title"), ml):
            if x:
                titles.add(N(str(x)))
    out = json.loads(json.dumps(units))
    n = 0
    for u in out:
        for t in u.get("topics") or []:
            keep = []
            for a in t.get("aliases") or []:
                if N(a) in secs or (not SEC_ONLY and N(a) in titles):
                    n += 1
                    continue
                keep.append(a)
            t["aliases"] = keep
    return out, n


def mapa_vizinho(cands, units, relaxar=False):
    """Ancora do item 10 no proprio bloco; sem ancora, herda do vizinho ancorado mais proximo antes (senao depois)."""
    uslugs = [str(u.get("slug", "") or "") for u in units]
    utoks = [um._unit_tokens(u) for u in units]
    btoks = [um._block_tokens(b) for b in cands]
    m = len(units)
    aff = [[float(len(btoks[i] & utoks[j])) for j in range(m)] for i in range(len(cands))]
    exclusive = [utoks[j] - set().union(*(utoks[k] for k in range(m) if k != j)) for j in range(m)]
    anc = {}
    for i, row in enumerate(aff):
        srt = sorted(row, reverse=True)
        margin = (srt[0] - srt[1]) if m > 1 else srt[0]
        j = row.index(srt[0])
        hits = {k for k in range(m) if btoks[i] & exclusive[k]}
        so_dela = hits == {j} or (relaxar and j in hits and all(row[j] - row[k] >= 2 for k in hits if k != j))
        if srt[0] >= um.ANCHOR_MIN_AFF and margin >= um.ANCHOR_MIN_MARGIN and so_dela:
            anc[i] = j
    assign = [None] * len(cands)
    for i in range(len(cands)):
        if i in anc:
            assign[i] = anc[i]
    last = None
    for i in range(len(cands)):
        if assign[i] is not None:
            last = assign[i]
        elif last is not None:
            assign[i] = last
    nxt = None
    for i in range(len(cands) - 1, -1, -1):
        if assign[i] is not None:
            nxt = assign[i]
        elif nxt is not None:
            assign[i] = nxt
    if all(a is None for a in assign):
        return None
    return [uslugs[a if a is not None else 0] for a in assign], anc


cg_truth = {}
for r in csv.DictReader((GEN / "docs/reports/subunit_gt_CG.csv").open(encoding="utf-8-sig", newline="")):
    mm = re.search(r"= u0(\d)|\(u0(\d)\)|u0(\d)/", r["notas"])
    if "UNIDADE ERRADA" in r["notas"] and mm:
        cg_truth[r["entry_id"]] = "unidade-0" + next(g for g in mm.groups() if g)

VARS = ["base", "H", "V", "VX", "H+V", "H+VX"]
TOT = {v: {"pins_ok": 0, "mud": 0, "uni_ok": 0, "cg_ok": 0} for v in VARS}
pins_n = uni_n = cg_n = 0
for sig, name in REPOS.items():
    root = GH / name
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    units = list(json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8")).get("units") or [])
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    cands = [b for b in blocks if not b.get("source_kind")]
    if len(units) < 2 or not cands:
        print(f"== {sig}: fora"); continue
    units_h, n_drop = higiene(units, man)
    res = {}
    off = um.assign_units_positional(cands, units)
    res["base"] = [s for s, _ in off] if off else None
    if res["base"] is None:
        print(f"== {sig}: sem afinidade"); continue
    offh = um.assign_units_positional(cands, units_h)
    res["H"] = [s for s, _ in offh] if offh else res["base"]
    for key, uu, rel in (("V", units, False), ("VX", units, True), ("H+V", units_h, False), ("H+VX", units_h, True)):
        r = mapa_vizinho(cands, uu, rel)
        res[key] = r[0] if r else res["base"]
    pins = [(k, str(b.get("block_manual_unit_slug") or "")) for k, b in enumerate(cands) if str(b.get("block_manual_unit_slug") or "")]
    pins_n += len(pins)
    line = f"== {sig}: blocos-aula {len(cands)} | aliases removidos pela higiene {n_drop} | pinos {len(pins)}:"
    for v in VARS:
        ok = sum(1 for k, p in pins if res[v][k] == p)
        mud = sum(1 for k in range(len(cands)) if res[v][k] != res["base"][k])
        TOT[v]["pins_ok"] += ok
        TOT[v]["mud"] += mud
        line += f" {v} {ok}/{len(pins)} mud {mud} ·"
    print(line)
    for k, b in enumerate(cands):
        if any(res[v][k] != res["base"][k] for v in VARS) or k in dict(pins):
            pin = dict(pins).get(k, "")
            print(f"     {str(b.get('id')):8} '{str(b.get('primary_topic_label'))[:24]:24}' " + " ".join(f"{v}={res[v][k][8:22]:14}" for v in VARS) + f" pino={pin[8:22] if pin else '-'}")
    truth = _load_truth(sig) if sig in ("MF", "SO", "IA", "ES2", "TCC") else {}
    src_root = SNAP / name if (SNAP / name / "manifest.json").exists() else root
    if sig == "CG":
        src_root = root
        truth = {e["id"]: cg_truth.get(e["id"], e["computed_unit_slug"]) for e in man if _is_material(e) and e.get("computed_unit_slug")}
    if truth:
        ents = {e["id"]: e for e in json.loads((src_root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        preds = load_predictions(src_root)
        uob = {}
        for k, b in enumerate(cands):
            for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
                uob[key] = {v: res[v][k] for v in VARS}
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
                TOT[v]["cg_ok" if sig == "CG" else "uni_ok"] += okv
                if v != "base" and okv != ((got.startswith(want)) if sig == "CG" else (got == want)):
                    flips[v].append(f"{eid[:22]}:{'+' if okv else '-'}")
            if sig == "CG":
                cg_n += 1
            else:
                uni_n += 1
        for v in VARS:
            if v != "base" and flips[v]:
                print(f"     flips {v}: +{sum(f.endswith('+') for f in flips[v])} -{sum(f.endswith('-') for f in flips[v])} {flips[v][:10]}")
print("\nTOTAL:")
for v in VARS:
    print(f"  {v:5} pinos {TOT[v]['pins_ok']}/{pins_n} · blocos mudados {TOT[v]['mud']} · unidade(5 golds) {TOT[v]['uni_ok']}/{uni_n} · CG(93; 22 propostos) {TOT[v]['cg_ok']}/{cg_n}")
