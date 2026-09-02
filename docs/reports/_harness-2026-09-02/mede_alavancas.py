"""Mede alavancas ESTRUTURAIS para o bloco no motor puro (copias .ablacao), read-only, sobre TODOS os
golds (ganho E perda), e a escada acumulada. Usa as funcoes de producao do motor.

  H1 card generico (Informacoes Gerais/Geral/Avisos) sem janela -> 1o bloco de aula
  H2 prova antiga (ano no id < ano do curso) sem janela -> resolve_exam_prep
  H5 serie numerada no card -> ordem MONOTONICA (DP maximiza soma dos scores do disambiguator)
      (a) sobrescreve todos os membros  (b) so os membros FLAGADOS
  H6 label/titulo com token unico a 1 bloco da janela -> decide, SO nos flagados
  H8 teto de informacao: erros em cards SEM data (provider topic) — o que a data resolveria
"""
import collections, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor.anchor_engine import resolve_exam_prep  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor.disambiguator import (  # noqa: E402
    _block_signature, _moodle_label_text, _score, _toks, entry_tokens,
)
from src.builder.routing.resolver_apply import _is_material  # noqa: E402

COPY = GEN / ".ablacao"
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
GENERIC_CARD = re.compile(r"informa|geral|aviso", re.I)
SERIES_RX = re.compile(r"^([a-z]+?)[-_]?(\d{1,2})(?!\d)")
YEAR_RX = re.compile(r"(20\d\d)")

G = []          # golds: dicts
groups = collections.defaultdict(list)   # (sig, card, radical) -> [gold dicts]


def bid(b):
    return str(b.get("id") or "")


for sig, nome in REPOS.items():
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    cname = str((man.get("course") or {}).get("course_name") or "")
    ctx = build_motor_context(repo, cname)
    order = {bid(b): i for i, b in enumerate(ctx.blocks)}
    # mesma definicao da ref-generica/meta-generica de producao: overview (apresentacao) ou 1a aula
    first_class = next((bid(b) for b in ctx.blocks if str(b.get("kind") or "") in ("overview", "class", "")), "")
    year = max((int(m) for b in ctx.blocks for m in YEAR_RX.findall(str(b.get("period_start") or ""))), default=2026)
    ents = {e["id"]: e for e in man["entries"]}
    preds = load_predictions(repo); labels = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    for eid, gold in labels.items():
        e = ents.get(eid); p = preds.get(eid)
        if not e or not p:
            continue
        win_refs = [str(w) for w in (e.get("temporal_block_window") or [])]
        blocks = [b for b in (ctx.block_by_ref(r) for r in win_refs) if b is not None]
        md = _entry_markdown_text_for_file_map(repo, e) or ""
        g = {"sig": sig, "id": eid, "e": e, "ctx": ctx, "repo": repo, "gold": gold, "pred": p["block_id"],
             "method": str(e.get("temporal_block_method") or "SEM-BLOCO"), "provider": str(e.get("temporal_block_provider") or ""),
             "flag": bool(e.get("temporal_block_flag")), "blocks": blocks, "md": md, "order": order,
             "first_class": first_class, "year": year, "card": str(e.get("source_section") or "")}
        G.append(g)
        m = SERIES_RX.match(eid)
        if m and g["card"] and len(blocks) >= 2:
            groups[(sig, g["card"], m.group(1))].append((int(m.group(2)), g))

n = len(G); base_ok = sum(g["pred"] == g["gold"] for g in G)
print(f"golds={n}  motor puro={base_ok}  erros={n - base_ok}")


def scores_for(g):
    blocks = g["blocks"]; ctx = g["ctx"]
    sigs = [_block_signature(b, ctx) for b in blocks]
    dfw = collections.Counter(t for s in sigs for t in s)
    mat = entry_tokens(g["e"], g["md"])
    return [_score(mat, s, len(blocks), dfw) for s in sigs]


# ---- H1: card generico sem janela -> 1o bloco de aula
def h1(g):
    if g["method"] == "SEM-BLOCO" and GENERIC_CARD.search(g["card"]):
        return g["first_class"]
    return None


# ---- H2: prova antiga sem janela -> prep
def h2(g):
    e = g["e"]
    if g["method"] != "SEM-BLOCO" or str(e.get("category") or "") != "provas":
        return None
    anos = [int(y) for y in YEAR_RX.findall(str(e.get("id") or "") + " " + str(e.get("title") or ""))]
    if not anos or min(anos) >= g["year"]:
        return None
    d = resolve_exam_prep(e, g["ctx"])
    return d.block_ref if d else None


# ---- H6: label unico a 1 bloco, so flagados
def h6(g):
    if not (g["flag"] and len(g["blocks"]) >= 2):
        return None
    named = _toks(str(g["e"].get("title") or "") + " " + _moodle_label_text(g["e"]))
    sigs = [set(_block_signature(b, g["ctx"])) for b in g["blocks"]]
    hits = [named & s for s in sigs]
    df = collections.Counter(t for h in hits for t in h)
    cands = [i for i, h in enumerate(hits) if {t for t in h if df[t] == 1}]
    return bid(g["blocks"][cands[0]]) if len(cands) == 1 else None


# ---- H5: serie monotonica (DP) por grupo; devolve {id: bloco}
def h5(only_flagged):
    out = {}
    for key, members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda x: x[0])
        g0 = members[0][1]
        classes = [b for b in g0["blocks"] if str(b.get("kind") or "") == "class"]
        classes.sort(key=lambda b: g0["order"][bid(b)])
        if len(classes) < 2:
            continue
        idx = {bid(b): i for i, b in enumerate(classes)}
        S = []
        for k, g in members:
            sc = scores_for(g); by = {bid(b): s for b, s in zip(g["blocks"], sc)}
            S.append([by.get(bid(b), 0.0) for b in classes])
        M, B = len(members), len(classes)
        NEG = float("-inf")
        dp = [[NEG] * B for _ in range(M)]; back = [[-1] * B for _ in range(M)]
        for j in range(B):
            dp[0][j] = S[0][j]
        for i in range(1, M):
            best, bj = NEG, -1
            for j in range(B):
                if dp[i - 1][j] > best:
                    best, bj = dp[i - 1][j], j
                if best > NEG:
                    dp[i][j] = best + S[i][j]; back[i][j] = bj
        j = max(range(B), key=lambda j: dp[M - 1][j])
        assign = [0] * M
        for i in range(M - 1, -1, -1):
            assign[i] = j; j = back[i][j] if i > 0 else j
        for (k, g), j in zip(members, assign):
            if only_flagged and not g["flag"]:
                continue
            out[(g["sig"], g["id"])] = bid(classes[j])
    return out


def report(nome, picks):
    fix = brk = same_ok = same_err = 0
    det = []
    for g in G:
        pk = picks.get((g["sig"], g["id"])) if isinstance(picks, dict) else picks(g)
        if not pk:
            continue
        ok0, ok1 = g["pred"] == g["gold"], pk == g["gold"]
        if ok1 and not ok0: fix += 1; det.append(f"+{g['sig']}:{g['id']}")
        elif ok0 and not ok1: brk += 1; det.append(f"-{g['sig']}:{g['id']}")
        elif ok0: same_ok += 1
        else: same_err += 1
    print(f"{nome:44} conserta {fix:>2}  quebra {brk:>2}  (ja certo {same_ok}, erra→erra {same_err})  {' '.join(det)[:200]}")
    return fix, brk


print("\n== ALAVANCAS isoladas (sobre os 203 golds) ==")
h5a, h5b = h5(False), h5(True)
res = {}
res["H1 card generico -> 1o bloco de aula"] = report("H1 card generico -> 1o bloco de aula", h1)
res["H2 prova antiga -> prep"] = report("H2 prova antiga -> prep", h2)
res["H5a serie monotonica (todos os membros)"] = report("H5a serie monotonica (todos os membros)", h5a)
res["H5b serie monotonica (so flagados)"] = report("H5b serie monotonica (so flagados)", h5b)
res["H6 label unico (so flagados)"] = report("H6 label unico (so flagados)", h6)

# ---- H8: teto de informacao (cards sem data)
topic_err = [g for g in G if g["provider"] == "topic" and g["pred"] != g["gold"]]
topic_all = [g for g in G if g["provider"] == "topic"]
print(f"\nH8 cards SEM data (provider topic): {len(topic_all)} golds, {len(topic_err)} erros -> "
      f"com data/ordem no card virariam janela pequena (janela-1 acerta 96%)")
print("   erros:", " ".join(f"{g['sig']}:{g['id']}" for g in topic_err))

# ---- ESCADA acumulada: H1 -> H2 -> H5b -> H6 ; residual flagado -> LLM (69/70 = 98.6%)
print("\n== ESCADA acumulada (estrutura primeiro; cada degrau so age onde o anterior nao agiu) ==")
cur = {(g["sig"], g["id"]): g["pred"] for g in G}
decided = set()
def apply(nome, picks):
    global cur
    n_changed = 0
    for g in G:
        k = (g["sig"], g["id"])
        if k in decided:
            continue
        pk = picks.get(k) if isinstance(picks, dict) else picks(g)
        if pk:
            cur[k] = pk; decided.add(k); n_changed += 1
    ok = sum(cur[(g["sig"], g["id"])] == g["gold"] for g in G)
    print(f"  + {nome:40} agiu em {n_changed:>2} -> {ok}/{n}")
    return ok
ok = base_ok
print(f"  motor puro hoje{'':29} -> {base_ok}/{n}")
ok = apply("H1 card generico", h1)
_h7 = json.load(open(Path(__file__).resolve().parent / "moodle_sections" / "picks_h7.json", encoding="utf-8"))  # rode antes: mede_ordem_secoes.py --chain --only-flagged
h7 = {tuple(k.split("|")): v for k, v in _h7.items()}
report("H7 ordem das secoes (chain, so flagados)", h7)
ok = apply("H7 ordem das secoes (chain, flagados)", h7)
ok = apply("H6 label unico (flagados)", h6)
# residual: flagados ou sem bloco que a escada nao decidiu -> LLM
resid = [g for g in G if (g["sig"], g["id"]) not in decided and (g["flag"] or g["method"] == "SEM-BLOCO")]
resid_err = sum(cur[(g["sig"], g["id"])] != g["gold"] for g in resid)
conf_err = sum(cur[(g["sig"], g["id"])] != g["gold"] for g in G if (g["sig"], g["id"]) not in decided and not (g["flag"] or g["method"] == "SEM-BLOCO"))
print(f"  residual para o LLM: {len(resid)} materiais ({100*len(resid)/n:.0f}/100), dos quais {resid_err} errados hoje; "
      f"erros CONFIANTES fora do alcance do LLM: {conf_err}")
esperado = ok - resid_err + round(len(resid) * 0 + resid_err * (69/70))  # LLM conserta ~98.6% do que decide
print(f"  esperado com LLM nos {len(resid)} residuais (acerto 69/70): ~{ok + round(resid_err * 69/70)}/{n}  "
      f"(teto se o LLM acertasse tudo: {ok + resid_err}/{n}; os {conf_err} confiantes-errados ficam)")
print("\n  confiantes-errados:", " ".join(f"{g['sig']}:{g['id']}({g['method']})" for g in G if (g['sig'], g['id']) not in decided and not (g['flag'] or g['method'] == 'SEM-BLOCO') and cur[(g['sig'], g['id'])] != g['gold']))
