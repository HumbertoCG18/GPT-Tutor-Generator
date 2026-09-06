"""CG unidade sem LLM e sem pino — regras GENERICAS medidas nos 8 (mapa bloco->unidade, em memoria):
  RF  = radical (6) so como fallback (aff exata < 2)                                    [ja medido: +1 bloco, 0 colateral]
  SG  = token generico por RADICAL entre unidades: token cujo radical aparece no vocab de >= 2 unidades sai de _unit_tokens
  Z0  = bloco com afinidade zero em todas as unidades herda do bloco-aula anterior com evidencia
  DF  = alias cujo(s) token(s) aparecem em > 25% dos materiais do curso (boilerplate: 'OpenGL') nao entra em _unit_tokens
Variantes: base, RF, RF+SG, RF+SG+Z0, RF+DF, RF+SG+Z0+DF. Verdade: pinos (16, com os 3 do CG), unidade (5 golds), blocos mudados.
Uso: simula_cg_unidade_generico.py <snapshot_antes>"""
import json
import sys
from collections import Counter
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
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.timeline import unit_matcher as um  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
DF_MAX = 0.25


def stem(toks):
    return {t[:6] for t in toks}


def unit_tokens_variant(units, man, sg, df):
    """_unit_tokens por unidade com SG (radical generico entre unidades) e DF (alias boilerplate) aplicados."""
    base = [um._unit_tokens(u) for u in units]
    if df:
        # tokens dos materiais (titulo + label + secao): alias cujos tokens todos aparecem em > DF_MAX dos materiais e boilerplate
        mats = []
        for e in man:
            ml = e.get("moodle_label")
            ml = ml.get("text") if isinstance(ml, dict) else ml
            mats.append(um._tokens(" ".join(str(x) for x in (e.get("title"), ml, e.get("source_section")) if x)))
        dfc = Counter(t for m in mats for t in m)
        boiler = {t for t, c in dfc.items() if c > DF_MAX * len(mats)}
        out = []
        for u, toks in zip(units, base):
            drop = set()
            for t in u.get("topics") or []:
                for a in t.get("aliases") or []:
                    at = um._tokens(a)
                    if at and at <= boiler:
                        drop |= at
            # so remove o token se ele NAO vem do titulo/label do plano (que ficam)
            plano = um._tokens(" ".join([str(u.get("title", "") or "")] + [str(t.get("label", "") or "") for t in (u.get("topics") or [])]))
            out.append(toks - (drop - plano))
        base = out
    if sg:
        cnt = Counter()
        for toks in base:
            for s in stem(toks):
                cnt[s] += 1
        shared = {s for s, c in cnt.items() if c >= 2}
        base = [{t for t in toks if t[:6] not in shared} for toks in base]
    return base


def mapa(cands, units, man, rf, sg, z0, df):
    utoks = unit_tokens_variant(units, man, sg, df)
    orig = um._unit_tokens
    um._unit_tokens = lambda u, _cache={id(u): t for u, t in zip(units, utoks)}: _cache.get(id(u), orig(u))
    try:
        off = um.assign_units_positional(cands, units)
    finally:
        um._unit_tokens = orig
    if not off:
        return None
    uslugs = [str(u.get("slug") or "") for u in units]
    m = len(units)
    btoks = [um._block_tokens(b) for b in cands]
    aff = [[len(btoks[i] & utoks[j]) for j in range(m)] for i in range(len(cands))]
    out = [s for s, _ in off]
    base = list(out)
    if rf:
        us = [stem(t) for t in utoks]
        bs = [stem(t) for t in btoks]
        ex = [us[j] - set().union(*(us[k] for k in range(m) if k != j)) for j in range(m)]
        for i in range(len(cands)):
            if max(aff[i]) >= um.ANCHOR_MIN_AFF:
                continue
            sa = [len(bs[i] & us[j]) for j in range(m)]
            srt = sorted(sa, reverse=True)
            j = sa.index(srt[0])
            margin = srt[0] - (srt[1] if m > 1 else 0)
            hits = {k for k in range(m) if bs[i] & ex[k]}
            if srt[0] >= um.ANCHOR_MIN_AFF and margin >= um.ANCHOR_MIN_MARGIN and hits == {j}:
                out[i] = uslugs[j]
    if z0:
        last = None
        for i in range(len(cands)):
            if max(aff[i]) > 0 or out[i] != base[i]:
                last = out[i]
            elif last is not None:
                out[i] = last
    return out


VARS = {"base": (0, 0, 0, 0), "RF": (1, 0, 0, 0), "RF+SG": (1, 1, 0, 0), "RF+SG+Z0": (1, 1, 1, 0), "RF+DF": (1, 0, 0, 1), "RF+SG+Z0+DF": (1, 1, 1, 1)}
T = {v: {"pins": 0, "mud": 0, "uni": 0} for v in VARS}
pn = un = 0
for sig, name in REPOS.items():
    root = GH / name
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    units = list(json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8")).get("units") or [])
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    cands = [b for b in blocks if not b.get("source_kind")]
    if len(units) < 2 or not cands:
        continue
    res = {v: mapa(cands, units, man, *f) for v, f in VARS.items()}
    if res["base"] is None:
        continue
    for v in VARS:
        res[v] = res[v] or res["base"]
    pins = [(k, str(b.get("block_manual_unit_slug") or "")) for k, b in enumerate(cands) if str(b.get("block_manual_unit_slug") or "")]
    pn += len(pins)
    truth = _load_truth(sig) if sig in ("MF", "SO", "IA", "ES2", "TCC") else {}
    man_root = SNAP / name if (SNAP / name / "manifest.json").exists() else root
    ents = {e["id"]: e for e in json.loads((man_root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    preds = load_predictions(man_root)
    uob = {}
    for k, b in enumerate(cands):
        for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            uob[key] = {v: res[v][k] for v in VARS}
    line = f"== {sig}:"
    for v in VARS:
        ok = sum(1 for k, p in pins if res[v][k] == p)
        mud = sum(1 for k in range(len(cands)) if res[v][k] != res["base"][k])
        T[v]["pins"] += ok
        T[v]["mud"] += mud
        okg = 0
        for eid, want in truth.items():
            e = ents.get(eid)
            if not e or not _is_material(e):
                continue
            got = str(e.get("computed_unit_slug") or "")
            trio = uob.get(preds.get(eid, {}).get("block_id", ""))
            val = trio[v] if (trio and got == trio["base"]) else got
            okg += (val == want)
            if v == "base":
                un += 1
        T[v]["uni"] += okg
        line += f" {v}: pinos {ok}/{len(pins)} mud {mud} gold {okg} ·"
    print(line)
    for k, b in enumerate(cands):
        if any(res[v][k] != res["base"][k] for v in VARS):
            print(f"     {str(b.get('id')):8} '{str(b.get('primary_topic_label'))[:22]:22}' " + " ".join(f"{v}={res[v][k][8:22]:14}" for v in VARS) + f" pino={dict(pins).get(k, '-')[8:22]}")
print("TOTAL:", " | ".join(f"{v}: pinos {T[v]['pins']}/{pn} mud {T[v]['mud']} unidade {T[v]['uni']}/{un}" for v in VARS))
