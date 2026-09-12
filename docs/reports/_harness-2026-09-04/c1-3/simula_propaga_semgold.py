"""Mesma propagacao de vocabulario (headings exclusivos dos confiantes -> aliases do subtopico, 2 passadas) nos cursos SEM
gold de subunidade (MF, CG, FR, LR): lista o que MUDARIA, para revisao humana. Em memoria, sem reprocess, sem Gemini.
Uso: simula_propaga_semgold.py <dir_snapshot_antes> conf_min min_entries df_max [weak]"""
import collections
import functools
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
SNAP = Path(sys.argv[1])
CONF_MIN, MIN_ENTRIES, DF_MAX = float(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
WEAK_ONLY = "weak" in sys.argv[5:]  # passada 2 so onde a 1a nao decidiu com confianca (nunca sobrepoe decisao confiante)
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
        "FR": "Fundamentos-de-Redes-Tutor", "LR": "Laboratorio-de-Redes-Tutor"}
iter_orig = eng._iter_content_taxonomy_topics


def _toks(t):
    return {x for x in normalize_match_text(str(t or "")).split() if len(x) >= 4}


def subtopic_fn(extra_aliases):
    def _iter(taxonomy):
        topics = [dict(t) for t in iter_orig(taxonomy)]
        for t in topics:
            add = extra_aliases.get((t["unit_slug"], t["topic_slug"]))
            if add:
                t["aliases"] = list(t.get("aliases") or []) + sorted(add)
        return topics
    return functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                             iter_content_taxonomy_topics=_iter, score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                             topic_match_result_factory=TopicMatchResult)


def texto(root, entry, code_cur):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


for sig, repo in REPO.items():
    root = COPY / repo
    mp = (SNAP / repo / "manifest.json") if (SNAP / repo / "manifest.json").exists() else (root / "manifest.json")
    ents = json.loads(mp.read_text(encoding="utf-8"))["entries"]
    man = {e["id"]: e for e in ents}
    tax = load_internal_content_taxonomy(root)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    base_fn = subtopic_fn({})
    p1 = {}
    for e in ents:
        if not _is_material(e) or not e.get("computed_unit_slug"):
            continue
        t = texto(root, e, code_cur)
        m = base_fn(e, tax, t, winning_unit_slug=e["computed_unit_slug"])
        sigs = eng._collect_entry_unit_signals(e, t)
        p1[e["id"]] = (m, t, _toks(sigs.get("markdown_headings_text", "")) | _toks(sigs.get("title_text", "")))
    topics = iter_orig(tax)
    vocab_unit = collections.defaultdict(set)
    generic_unit = {}
    for tp in topics:
        generic_unit[tp["unit_slug"]] = set(tp.get("generic_tokens") or []) | _toks(tp.get("unit_title"))
        for ph in [tp["topic_label"]] + list(tp.get("aliases") or []):
            vocab_unit[tp["unit_slug"]] |= _toks(ph)
    tok_sub = collections.defaultdict(lambda: collections.defaultdict(int))
    tok_owner = collections.defaultdict(lambda: collections.defaultdict(set))
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
    prop_fn = subtopic_fn(extra)
    mud = 0
    for eid, (m1, t, _) in p1.items():
        if WEAK_ONLY and m1.topic_slug and not m1.ambiguous and m1.confidence >= CONF_MIN:
            continue
        m2 = prop_fn(man[eid], tax, t, winning_unit_slug=man[eid]["computed_unit_slug"])
        if (m2.topic_slug or "") != (m1.topic_slug or ""):
            mud += 1
            print(f"  ~ {sig:3} {eid[:40]:40} {m1.topic_slug[:28] or '-':28} -> {m2.topic_slug[:28] or '-':28} conf {m1.confidence:.2f}->{m2.confidence:.2f} card={str(man[eid].get('source_section'))[:28]!r}")
    print(f"{sig:3} materiais={len(p1)} confiantes={sum(1 for m, _, _ in p1.values() if m.topic_slug and not m.ambiguous and m.confidence >= CONF_MIN)} aliases novos={sum(len(v) for v in extra.values())} MUDAM={mud}")
