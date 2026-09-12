"""Radicais so como FALLBACK no mapa bloco->unidade: DP oficial (tokens exatos) decide; bloco cuja afinidade exata maxima < 2 (sem ancora
possivel) ganha ancora por RADICAL (>= 2 radicais, margem >= 1, radical exclusivo de UMA unidade). Medido nos 8 (05/09 tarde): 1 bloco muda
(CG bloco-15 Modelagem -> u07 = pino), 0 colateral, unidade 183 = 183/191. Uso: simula_radical_fallback.py <snapshot_antes>"""
import json
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


def stem(toks):
    return {t[:6] for t in toks}


T = {"pins": [0, 0, 0], "uni": [0, 0, 0], "mud": 0}
for sig, name in REPOS.items():
    root = GH / name
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    units = list(json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8")).get("units") or [])
    cands = [b for b in blocks if not b.get("source_kind")]
    if len(units) < 2 or not cands:
        continue
    off = um.assign_units_positional(cands, units)
    if not off:
        continue
    base = [s for s, _ in off]
    uslugs = [str(u.get("slug") or "") for u in units]
    m = len(units)
    utoks = [um._unit_tokens(u) for u in units]
    btoks = [um._block_tokens(b) for b in cands]
    ustem = [stem(t) for t in utoks]
    bstem = [stem(t) for t in btoks]
    excl = [ustem[j] - set().union(*(ustem[k] for k in range(m) if k != j)) for j in range(m)]
    new = list(base)
    mud = []
    for i, b in enumerate(cands):
        aff = [len(btoks[i] & utoks[j]) for j in range(m)]
        if max(aff) >= um.ANCHOR_MIN_AFF:
            continue
        saff = [len(bstem[i] & ustem[j]) for j in range(m)]
        srt = sorted(saff, reverse=True)
        j = saff.index(srt[0])
        margin = srt[0] - (srt[1] if m > 1 else 0)
        hits = {k for k in range(m) if bstem[i] & excl[k]}
        if srt[0] >= um.ANCHOR_MIN_AFF and margin >= um.ANCHOR_MIN_MARGIN and hits == {j} and uslugs[j] != base[i]:
            new[i] = uslugs[j]
            mud.append((b.get("id"), base[i][8:22], uslugs[j][8:22], str(b.get("primary_topic_label"))[:22]))
    pins = [(k, str(b.get("block_manual_unit_slug") or "")) for k, b in enumerate(cands) if str(b.get("block_manual_unit_slug") or "")]
    pb = sum(1 for k, p in pins if base[k] == p)
    pn = sum(1 for k, p in pins if new[k] == p)
    T["pins"][0] += pb
    T["pins"][1] += pn
    T["pins"][2] += len(pins)
    T["mud"] += len(mud)
    truth = _load_truth(sig) if sig in ("MF", "SO", "IA", "ES2", "TCC") else {}
    man_root = SNAP / name if (SNAP / name / "manifest.json").exists() else root
    ents = {e["id"]: e for e in json.loads((man_root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    preds = load_predictions(man_root)
    uob = {}
    for k, b in enumerate(cands):
        for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            uob[key] = (base[k], new[k])
    ok_b = ok_n = n = 0
    for eid, want in truth.items():
        e = ents.get(eid)
        if not e or not _is_material(e):
            continue
        got = str(e.get("computed_unit_slug") or "")
        pair = uob.get(preds.get(eid, {}).get("block_id", ""))
        val = pair[1] if (pair and got == pair[0]) else got
        ok_b += got == want
        ok_n += val == want
        n += 1
    T["uni"][0] += ok_b
    T["uni"][1] += ok_n
    T["uni"][2] += n
    print(f"== {sig}: pinos {pb}->{pn}/{len(pins)} | blocos mudados {len(mud)} {mud} | gold {ok_b}->{ok_n}/{n}")
print(f"TOTAL radical-fallback: pinos {T['pins'][0]}->{T['pins'][1]}/{T['pins'][2]} | blocos mudados {T['mud']} | unidade(5 golds) {T['uni'][0]}->{T['uni'][1]}/{T['uni'][2]}")
