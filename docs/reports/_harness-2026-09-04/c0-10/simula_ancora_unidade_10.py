"""C0 item 10 (read-only): a DP posicional bloco->unidade erra onde o professor sai da ordem do plano (SO bloco-06, bloco-20).
Simula duas variantes de ANCORA LEXICAL FORTE (bloco cuja afinidade argmax tem margem >= STRONG_MARGIN):
  A) "ancora vence": o bloco-ancora recebe o argmax; os outros ficam como na DP.
  B) "DP segmentada": ancoras fixas; a DP monotonica roda em cada trecho entre ancoras, com as unidades limitadas ao intervalo
     [ancora anterior, ancora seguinte] quando esse intervalo e crescente; trecho com ancoras fora de ordem roda livre.
Mede: (1) reproducao da DP atual vs auto_unit_slug gravado (validacao); (2) acerto contra os pinos manuais de unidade (14 blocos);
(3) blocos que mudam; (4) efeito na regua de UNIDADE (5 golds): entries que seguem a unidade do bloco herdam a unidade nova."""
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_predictions  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.timeline import unit_matcher as um  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
COPY = GEN / ".ablacao"


def load(root):
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    tax = json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    return blocks, list(tax.get("units") or [])


def aff_matrix(cands, units):
    utoks = [um._unit_tokens(u) for u in units]
    return [[float(len(um._block_tokens(b) & utoks[j])) for j in range(len(units))] for b in cands]


def anchors_of(aff):
    out = {}
    for i, row in enumerate(aff):
        srt = sorted(row, reverse=True)
        margin = (srt[0] - srt[1]) if len(srt) > 1 else srt[0]
        if srt[0] > 0 and margin >= um.STRONG_MARGIN:
            out[i] = row.index(srt[0])
    return out


def variant_A(base_idx, aff):
    out = list(base_idx)
    for i, u in anchors_of(aff).items():
        out[i] = u
    return out


from src.builder.routing.motor.disambiguator import _GENERIC_STEMS


def _generic(tok):
    return any(tok.startswith(s) for s in _GENERIC_STEMS)


def anchors_C(aff, cands, units, drop_generic=False, why=None):
    utoks = [um._unit_tokens(u) for u in units]
    uniq = [utoks[j] - set().union(*[utoks[k] for k in range(len(units)) if k != j]) for j in range(len(units))]
    out = {}
    for i, row in enumerate(aff):
        srt = sorted(row, reverse=True); margin = (srt[0] - srt[1]) if len(srt) > 1 else srt[0]
        j = row.index(srt[0])
        ex = um._block_tokens(cands[i]) & uniq[j]
        if drop_generic:
            ex = {x for x in ex if not _generic(x)}
        if srt[0] > 0 and margin >= um.ANCHOR_MIN_MARGIN and ex:
            out[i] = j
            if why is not None: why[i] = sorted(ex)
    return out


def variant_B(aff, m, anc=None):
    n = len(aff)
    anc = anchors_of(aff) if anc is None else anc
    if not anc:
        return um._dp_monotonic(aff, m)[1]
    out = [None] * n
    for i, u in anc.items():
        out[i] = u
    idx = sorted(anc)
    bounds = [(-1, 0), *[(i, anc[i]) for i in idx], (n, m - 1)]
    for (i0, u0), (i1, u1) in zip(bounds, bounds[1:]):
        seg = list(range(i0 + 1, i1))
        if not seg:
            continue
        lo, hi = (u0 if i0 >= 0 else 0), (u1 if i1 < n else m - 1)
        if lo <= hi:
            sub = [[aff[i][u] for u in range(lo, hi + 1)] for i in seg]
            _, a = um._dp_monotonic(sub, hi - lo + 1)
            for k, i in enumerate(seg):
                out[i] = a[k] + lo
        else:  # ancoras fora da ordem do plano: trecho livre
            _, a = um._dp_monotonic([aff[i] for i in seg], m)
            for k, i in enumerate(seg):
                out[i] = a[k]
    return out


def pins_of(cands):
    return [(i, str(b.get('block_manual_unit_slug') or '')) for i, b in enumerate(cands) if str(b.get('block_manual_unit_slug') or '')]


TOT = {"pinos": 0, "base_ok": 0, "A_ok": 0, "B_ok": 0, "A_mud": 0, "B_mud": 0, "repro": 0, "repro_n": 0}
UNI = {"base": [0, 0], "A": [0, 0], "B": [0, 0], "C": [0, 0], "D": [0, 0], "E": [0, 0]}
PER = {}
for sig, name in REPOS.items():
    orig = GH / name
    blocks, units = load(orig)
    if len(units) < 2:
        print(f"== {sig}: <2 unidades na taxonomia; fora"); continue
    cands = [b for b in blocks if not b.get("source_kind")]
    aff = aff_matrix(cands, units)
    if not any(v > 0 for row in aff for v in row):
        print(f"== {sig}: sem afinidade; fora"); continue
    uslugs = [str(u.get("slug") or "") for u in units]
    base_idx = um._dp_monotonic(aff, len(units))[1]
    # tentativa de reproduzir o desvio de janela: usa a funcao oficial
    official = um.assign_units_positional(cands, units)
    base = [s for s, _ in official] if official else [uslugs[i] for i in base_idx]
    base_idx = [uslugs.index(s) if s in uslugs else 0 for s in base]
    A = [uslugs[i] for i in variant_A(base_idx, aff)]
    B = [uslugs[i] for i in variant_B(aff, len(units))]
    whyC = {}; ancC = anchors_C(aff, cands, units, why=whyC)
    C = [uslugs[i] for i in variant_B(aff, len(units), ancC)]
    whyD = {}; ancD = anchors_C(aff, cands, units, drop_generic=True, why=whyD)
    D = [uslugs[i] for i in variant_B(aff, len(units), ancD)]
    E = list(base)
    for i, u in ancD.items():
        E[i] = uslugs[u]
    eo = sum(1 for i, pp in pins_of(cands) if E[i] == pp); em = sum(1 for i in range(len(cands)) if E[i] != base[i])
    TOT['E_ok'] = TOT.get('E_ok', 0) + eo; TOT['E_mud'] = TOT.get('E_mud', 0) + em
    print(f'   [{sig}] E (ancora D so no proprio bloco): pinos ok {eo}/{len(pins_of(cands))} | blocos mudados {em} -> ' + str([(str(cands[i].get('id')), base[i][8:22], E[i][8:22], whyD.get(i)) for i in range(len(cands)) if E[i] != base[i]]))
    if sig == 'IA':
        print('   [IA] D detalhe: ' + str([(str(cands[i].get('id')), base[i][8:26], D[i][8:26], dict(pins_of(cands)).get(i, '')[8:26]) for i in range(len(cands)) if D[i] != base[i]]))
    do = sum(1 for i, pp in pins_of(cands) if D[i] == pp); dm = sum(1 for i in range(len(cands)) if D[i] != base[i])
    TOT['D_ok'] = TOT.get('D_ok', 0) + do; TOT['D_mud'] = TOT.get('D_mud', 0) + dm
    print(f'   D (C sem token generico): ancoras {len(ancD)} | pinos ok {do} | blocos mudados {dm} -> ' + str([(str(cands[i].get('id')), base[i][8:22], D[i][8:22]) for i in range(len(cands)) if D[i] != base[i]]))
    anc_tokens = {str(cands[i].get('id')): whyC.get(i) for i in range(len(cands)) if C[i] != base[i] and i in whyC}
    print(f'   tokens das ancoras C nos blocos mudados: {anc_tokens}')
    co = sum(1 for i, p in pins_of(cands) if C[i] == p); cm = sum(1 for i in range(len(cands)) if C[i] != base[i])
    TOT['C_ok'] = TOT.get('C_ok', 0) + co; TOT['C_mud'] = TOT.get('C_mud', 0) + cm
    print(f'   C (ancora margem>=1 + token exclusivo): ancoras {len(ancC)} | pinos ok {co} | blocos mudados {cm} -> ' + str([(str(cands[i].get('id')), base[i][8:22], C[i][8:22]) for i in range(len(cands)) if C[i] != base[i]]))
    if sig == 'SO':
        utoks = [um._unit_tokens(u) for u in units]
        for i, b in enumerate(cands):
            if str(b.get('id')) in ('bloco-06', 'bloco-20'):
                bt = um._block_tokens(b)
                print(f'   {b.get("id")} tokens={sorted(bt)[:12]}')
                for j, u in enumerate(units):
                    inter = bt & utoks[j]
                    if inter: print(f'      aff {uslugs[j][:30]:30} = {len(inter)} {sorted(inter)}')
    # (1) reproducao vs auto_unit_slug gravado na COPIA (sem pinos) quando existe, senao no original
    src = COPY / name if (COPY / name / "course/.timeline_index.json").exists() else orig
    stored = {str(b.get("id")): str(b.get("auto_unit_slug") or "") for b in load(src)[0]}
    rep = sum(1 for b, s in zip(cands, base) if stored.get(str(b.get("id")), "") == s)
    TOT["repro"] += rep; TOT["repro_n"] += len(cands)
    # (2) pinos manuais
    pins = [(i, str(b.get("block_manual_unit_slug") or "")) for i, b in enumerate(cands) if str(b.get("block_manual_unit_slug") or "")]
    bo = sum(1 for i, p in pins if base[i] == p); ao = sum(1 for i, p in pins if A[i] == p); bbo = sum(1 for i, p in pins if B[i] == p)
    TOT["pinos"] += len(pins); TOT["base_ok"] += bo; TOT["A_ok"] += ao; TOT["B_ok"] += bbo
    am = sum(1 for i in range(len(cands)) if A[i] != base[i]); bm = sum(1 for i in range(len(cands)) if B[i] != base[i])
    TOT["A_mud"] += am; TOT["B_mud"] += bm
    anc = anchors_of(aff)
    print(f"== {sig}: blocos-aula {len(cands)} | reproduz DP gravada {rep}/{len(cands)} | ancoras fortes {len(anc)} | pinos {len(pins)}: DP {bo} · A {ao} · B {bbo} | blocos mudados A {am} · B {bm}")
    for i in sorted(set(list(anc) + [i for i, _ in pins]) | {i for i in range(len(cands)) if A[i] != base[i] or B[i] != base[i]}):
        b = cands[i]
        pin = dict(pins).get(i, "")
        print(f"     {str(b.get('id')):8} {'ANC' if i in anc else '   '} DP={base[i][8:24]:16} A={A[i][8:24]:16} B={B[i][8:24]:16} pino={pin[8:24] if pin else '-':16} '{str(b.get('primary_topic_label'))[:34]}'")
    # (4) regua de unidade: entries do gold que seguem a unidade do bloco
    truth = _load_truth(sig)
    if truth and (COPY / name / "manifest.json").exists():
        ents = {e["id"]: e for e in json.loads((COPY / name / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        preds = load_predictions(COPY / name)
        unit_of_block = {}
        for k, b in enumerate(cands):
            for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
                unit_of_block[key] = (base[k], A[k], B[k], C[k], D[k], E[k])
        for eid, want in truth.items():
            e = ents.get(eid)
            if not e or not _is_material(e):
                continue
            got = str(e.get("computed_unit_slug") or "")
            pred = preds.get(eid, {}).get("block_id", "")
            trio = unit_of_block.get(pred)
            for key, nu in (("base", got), ("A", None), ("B", None), ("C", None), ("D", None), ("E", None)):
                if key == "base":
                    val = got
                else:
                    # segue o bloco se a unidade gravada e a unidade DP do bloco previsto
                    val = {"A": trio[1], "B": trio[2], "C": trio[3], "D": trio[4], "E": trio[5]}[key] if (trio and got == trio[0]) else got
                PER.setdefault(sig, {}).setdefault(key, [0, 0]); PER[sig][key][1] += 1; PER[sig][key][0] += int(val == want)
                if key in ('C', 'D', 'E') and (val == want) != (got == want): PER[sig].setdefault('flips_' + key, []).append(f"{eid[:28]}:{'+' if val == want else '-'}")
                UNI[key][1] += 1; UNI[key][0] += int(val == want)
print("\nTOTAL: reproducao da DP gravada", f"{TOT['repro']}/{TOT['repro_n']}", "| pinos manuais", TOT["pinos"], f"-> DP acerta {TOT['base_ok']} · A {TOT['A_ok']} · B {TOT['B_ok']}",
      f"| blocos mudados A {TOT['A_mud']} · B {TOT['B_mud']} · C {TOT.get('C_mud')} | pinos C {TOT.get('C_ok')}")
print("REGUA UNIDADE (5 golds, entries que seguem o bloco herdam):", {k: f"{v[0]}/{v[1]}" for k, v in UNI.items()}, "| pinos D", TOT.get('D_ok'), "E", TOT.get('E_ok'), "| blocos mudados D", TOT.get('D_mud'), "E", TOT.get('E_mud'))
for s, d in PER.items(): print(f"   {s}: " + " ".join(f"{k}={v[0]}/{v[1]}" for k, v in d.items() if not k.startswith('flips')) + " | flips C: " + str(d.get('flips_C', [])) + " | flips D: " + str(d.get('flips_D', [])) + " | flips E: " + str(d.get('flips_E', [])))
