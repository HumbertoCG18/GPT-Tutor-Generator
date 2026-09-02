"""REGUA DE MATERIAIS DE AULA (read-only): golds separados em AULA / REFERENCIA / BASE; escada com todas as
alavancas medidas hoje (cada uma so age onde a anterior nao decidiu; estrutura primeiro):
  H1 card generico sem janela -> bloco de apresentacao
  H7 ordem das secoes (picks_h7.json, --chain --only-flagged)
  H9 card como documento ordenado (picks_card.json, --stream --only-flagged)
  H8 tokens curtos consagrados pelo cronograma no desempate (recalcula disambiguate; so flagados)
  H6 label/titulo com token unico a 1 bloco (so flagados)
Mostra o que sobra em AULA, por categoria e por metodo, e quantos ficam flagados (fila do LLM/humano).
"""
import collections, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor import disambiguator as D  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.text.stopwords import short_vocab_from_topic_labels  # noqa: E402

COPY = GEN / ".ablacao"
PULL = Path(__file__).resolve().parent / "moodle_sections"   # picks_h7.json (mede_ordem_secoes) + picks_card.json (mede_card_ordenado)
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
REF = {"bibliografia", "referencias", "references"}
BASE = {"cronograma", "plano-de-ensino", "plano"}
GENERIC_CARD = re.compile(r"informa|geral|aviso", re.I)


def bid(b):
    return str(b.get("id") or "")


def grupo(e):
    cat = str(e.get("category") or "").strip().lower()
    if cat in REF or str(e.get("file_type") or "") == "url":
        return "REF"
    if cat in BASE or str(e.get("temporal_block_method") or "") == "meta-generica":
        return "BASE"
    return "AULA"


G = []
h8 = {}
orig_toks = D._toks
for sig, nome in REPOS.items():
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    first = next((bid(b) for b in ctx.blocks if str(b.get("kind") or "") in ("overview", "class", "")), "")
    ents = {e["id"]: e for e in man["entries"]}
    preds = load_predictions(repo); labels = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    # H8: vocabulario curto do cronograma
    txts = []
    for b in ctx.blocks:
        txts.append(normalize_match_text(str(b.get("topic_text") or "") + " " + str(b.get("primary_topic_label") or "")))
        for s in b.get("sessions") or []:
            txts.append(normalize_match_text(str(s.get("label") or "")))
    short = set(short_vocab_from_topic_labels(txts))

    def toks_short(text, _o=orig_toks, _s=short):
        out = _o(text)
        for t in normalize_match_text(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(text or ""))).split():
            if t in _s:
                out.add(t)
        return out

    for eid, gold in labels.items():
        e = ents.get(eid); p = preds.get(eid)
        if not e or not p:
            continue
        win = [str(w) for w in (e.get("temporal_block_window") or [])]
        blocks = [b for b in (ctx.block_by_ref(r) for r in win) if b is not None]
        g = {"sig": sig, "id": eid, "e": e, "ctx": ctx, "gold": gold, "pred": p["block_id"], "grupo": grupo(e),
             "cat": str(e.get("category") or ""), "method": str(e.get("temporal_block_method") or "SEM-BLOCO"),
             "provider": str(e.get("temporal_block_provider") or ""), "flag": bool(e.get("temporal_block_flag")),
             "blocks": blocks, "card": str(e.get("source_section") or ""), "first": first}
        G.append(g)
        if g["flag"] and g["method"] == "disamb" and len(win) >= 2:
            md = _entry_markdown_text_for_file_map(repo, e) or ""
            D._toks = toks_short
            d = D.disambiguate(e, win, ctx, md, provider=g["provider"])
            D._toks = orig_toks
            new = bid(ctx.block_by_ref(d.block_ref) or {}) or d.block_ref
            if new != g["pred"] or not d.flag:
                h8[(sig, eid)] = (new, bool(d.flag))

h7 = {tuple(k.split("|")): v for k, v in json.loads((PULL / "picks_h7.json").read_text(encoding="utf-8")).items()}
h9 = {tuple(k.split("|")): v for k, v in json.loads((PULL / "picks_card.json").read_text(encoding="utf-8")).items()}


def h1(g):
    return g["first"] if (g["method"] == "SEM-BLOCO" and GENERIC_CARD.search(g["card"])) else None


def h6(g):
    if not (g["flag"] and len(g["blocks"]) >= 2):
        return None
    named = D._toks(str(g["e"].get("title") or "") + " " + D._moodle_label_text(g["e"]))
    sigs = [set(D._block_signature(b, g["ctx"])) for b in g["blocks"]]
    hits = [named & s for s in sigs]
    df = collections.Counter(t for h in hits for t in h)
    cands = [i for i, h in enumerate(hits) if {t for t in h if df[t] == 1}]
    return bid(g["blocks"][cands[0]]) if len(cands) == 1 else None


cats = collections.Counter((g["grupo"], g["cat"]) for g in G)
print("CATEGORIAS por grupo:", {gr: {c: n for (gg, c), n in cats.items() if gg == gr} for gr in ("AULA", "REF", "BASE")})

cur = {(g["sig"], g["id"]): g["pred"] for g in G}
decided = set()
unflag = set()   # decididos por alavanca = deixam de ser flagados


def tally(label):
    for gr in ("TODOS", "AULA", "REF", "BASE"):
        gs = [g for g in G if gr == "TODOS" or g["grupo"] == gr]
        ok = sum(cur[(g["sig"], g["id"])] == g["gold"] for g in gs)
        print(f"  {label:44} {gr:5} {ok:>3}/{len(gs):<3} {ok / max(len(gs), 1):.1%}", end="")
    print()


def apply(label, picks):
    n = 0
    for g in G:
        k = (g["sig"], g["id"])
        if k in decided:
            continue
        pk = picks.get(k) if isinstance(picks, dict) else picks(g)
        if isinstance(pk, tuple):
            pk, still_flag = pk
        else:
            still_flag = False
        if pk:
            cur[k] = pk; decided.add(k); n += 1
            if not still_flag:
                unflag.add(k)
    tally(f"+ {label} (agiu em {n})")


tally("motor puro hoje")
apply("H1 card generico", h1)
apply("H7 ordem das secoes", h7)
apply("H9 card ordenado", h9)
apply("H8 tokens curtos", h8)
apply("H6 label unico", h6)

print("\nRESTO em AULA (o que ainda erra), por categoria x metodo:")
resto = [g for g in G if g["grupo"] == "AULA" and cur[(g["sig"], g["id"])] != g["gold"]]
for g in sorted(resto, key=lambda g: (g["cat"], g["sig"])):
    k = (g["sig"], g["id"])
    print(f"  {g['sig']:3} {g['id'][:40]:40} cat={g['cat'][:16]:16} metodo={g['method']:10} flag={'S' if (g['flag'] and k not in unflag) else 'n'} janela={len(g['blocks'])} card={g['card'][:26]!r}")
flag_aula = [g for g in G if g["grupo"] == "AULA" and ((g["flag"] or g["method"] == "SEM-BLOCO") and (g["sig"], g["id"]) not in unflag)]
err_flag = sum(cur[(g["sig"], g["id"])] != g["gold"] for g in flag_aula)
n_aula = sum(1 for g in G if g["grupo"] == "AULA")
print(f"\nAULA: {n_aula} golds | ainda flagados/sem bloco depois da escada: {len(flag_aula)} ({100 * len(flag_aula) / n_aula:.0f}/100), "
      f"dos quais errados {err_flag} | erros CONFIANTES: {len(resto) - err_flag}")
