"""[6 GOLDS, CG/MF PROPOSTOS; WEAK-ONLY: 2a passada so onde a 1a nao decidiu com confianca] Propagacao de vocabulario SEM LLM para a subunidade: tokens EXCLUSIVOS dos headings/titulo dos materiais que o
proprio motor ja atribuiu com confianca a um subtopico viram aliases desse subtopico (2 passadas). Simulado em memoria
pela rota real sobre as copias .ablacao (motor puro +vocab) e o snapshot 'antes'. Sem reprocess, sem Gemini.
Uso: simula_propaga_headings.py <dir_snapshot_antes> [conf_min=0.5] [min_entries=1] [df_max=1.0] [orig]  (orig = originais/curada)"""
import collections
import csv
import functools
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
SNAP = Path(sys.argv[1])
CONF_MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
MIN_ENTRIES = int(sys.argv[3]) if len(sys.argv) > 3 else 1
DF_MAX = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != "orig" else 1.0  # token em > DF_MAX dos materiais do curso = generico
if "orig" in sys.argv[4:]:  # curada: originais (glossario manual presente), manifests dos originais
    COPY = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor", "MF": "Metodos-Formais-Tutor"}
iter_orig = eng._iter_content_taxonomy_topics


from src.builder.routing.motor.disambiguator import _GENERIC_STEMS  # noqa: E402


def _toks(t):
    # tokens >= 4 chars SEM os stems genericos do motor ('exemplo', 'exercici', 'resposta', 'aula'...): a propagacao
    # espalhava 'exemplo'/'respostas' como alias e derrubava CG slab e MF respostas (medido 05/09).
    return {x for x in normalize_match_text(str(t or "")).split() if len(x) >= 4 and not any(x.startswith(s) for s in _GENERIC_STEMS)}


def subtopic_fn(extra_aliases):
    def _iter(taxonomy):
        topics = [dict(t) for t in iter_orig(taxonomy)]
        for t in topics:
            add = extra_aliases.get((t["unit_slug"], t["topic_slug"]))
            if add:
                t["aliases"] = list(t.get("aliases") or []) + sorted(add)
        return topics
    return functools.partial(
        fm.auto_map_entry_subtopic,
        collect_entry_unit_signals=eng._collect_entry_unit_signals,
        iter_content_taxonomy_topics=_iter,
        score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
        topic_match_result_factory=TopicMatchResult,
    )


def texto(root, entry, code_cur):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


tot = collections.Counter()
for sig, repo in REPO.items():
    root = COPY / repo
    ents = json.loads((SNAP / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    man = {e["id"]: e for e in ents}
    tax = load_internal_content_taxonomy(root)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    base_fn = subtopic_fn({})
    # passada 1: todos os materiais com unidade
    p1 = {}
    for e in ents:
        if not _is_material(e) or not e.get("computed_unit_slug"):
            continue
        t = texto(root, e, code_cur)
        m = base_fn(e, tax, t, winning_unit_slug=e["computed_unit_slug"])
        sigs = eng._collect_entry_unit_signals(e, t)
        p1[e["id"]] = (m, t, _toks(sigs.get("markdown_headings_text", "")) | _toks(sigs.get("title_text", "")))
    # vocabulario ja existente por unidade (labels + aliases de todos os subtopicos) e genericos
    topics = iter_orig(tax)
    vocab_unit = collections.defaultdict(set)
    generic_unit = {}
    for tp in topics:
        generic_unit[tp["unit_slug"]] = set(tp.get("generic_tokens") or []) | _toks(tp.get("unit_title"))
        for ph in [tp["topic_label"]] + list(tp.get("aliases") or []):
            vocab_unit[tp["unit_slug"]] |= _toks(ph)
    # tokens de headings/titulo dos confiantes, por (unidade, subtopico)
    tok_sub = collections.defaultdict(lambda: collections.defaultdict(int))  # unit -> token -> entries por sub
    tok_owner = collections.defaultdict(lambda: collections.defaultdict(set))  # unit -> token -> {subs}
    for eid, (m, t, toks) in p1.items():
        if not m.topic_slug or m.ambiguous or m.confidence < CONF_MIN:
            continue
        unit = man[eid]["computed_unit_slug"]
        for tok in toks - generic_unit.get(unit, set()) - vocab_unit.get(unit, set()):
            tok_owner[unit][tok].add(m.topic_slug)
            tok_sub[unit][(tok, m.topic_slug)] += 1
    df_mat = collections.Counter()
    for _m, _t, toks in p1.values():
        df_mat.update(toks)
    extra = collections.defaultdict(set)
    for unit, owners in tok_owner.items():
        for tok, subs in owners.items():
            if df_mat[tok] > DF_MAX * len(p1):
                continue
            if len(subs) == 1 and tok_sub[unit][(tok, next(iter(subs)))] >= MIN_ENTRIES:
                extra[(unit, next(iter(subs)))].add(tok)
    n_alias = sum(len(v) for v in extra.values())
    prop_fn = subtopic_fn(extra)
    # passada 2 contra o gold
    with (GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("scorable") == "yes"]
    c = collections.Counter()
    for r in rows:
        e = man.get(r["entry_id"])
        if e is None or e["id"] not in p1:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
        m1, t, _ = p1[e["id"]]
        if m1.topic_slug and not m1.ambiguous and m1.confidence >= CONF_MIN:
            m2 = m1  # WEAK-ONLY: decisao confiante da 1a passada nunca e sobreposta
        else:
            m2 = prop_fn(e, tax, t, winning_unit_slug=e["computed_unit_slug"])
        a, b = (m1.topic_slug or "") in alvo, (m2.topic_slug or "") in alvo
        flip = "+" if (b and not a) else "-" if (a and not b) else ("~" if m2.topic_slug != m1.topic_slug else "=")
        c[flip] += 1
        c["ok1"] += a
        c["ok2"] += b
        c["n"] += 1
        if flip != "=":
            ganhos = sorted(extra.get((e["computed_unit_slug"], m2.topic_slug or ""), set()))[:6]
            print(f"  {flip} {sig:3} {r['entry_id'][:38]:38} {m1.topic_slug[:24] or '-':24} -> {m2.topic_slug[:24] or '-':24} gold={r['gold_subunit'][:22]:22} conf {m1.confidence:.2f}->{m2.confidence:.2f} aliases_novos_do_alvo={ganhos}")
    print(f"{sig:3} confiantes={sum(1 for m, _, _ in p1.values() if m.topic_slug and not m.ambiguous and m.confidence >= CONF_MIN)}/{len(p1)} aliases novos={n_alias} | sub {c['ok1']}/{c['n']} -> {c['ok2']}/{c['n']}  + {c['+']}  - {c['-']}  ~ {c['~']}")
    tot.update({k: c[k] for k in ("ok1", "ok2", "n", "+", "-", "~")})
print(f"TOTAL[weak-only] conf_min={CONF_MIN} min_entries={MIN_ENTRIES} df_max={DF_MAX}: sub {tot['ok1']}/{tot['n']} -> {tot['ok2']}/{tot['n']}  + {tot['+']}  - {tot['-']}  ~ {tot['~']}")
