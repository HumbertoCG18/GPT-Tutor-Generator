"""IDF intra-unidade no scorer de SUBTOPICO, simulado em memoria pela rota real (engine._auto_map_entry_subtopic),
sobre as copias .ablacao (motor puro +vocab) e o snapshot 'antes' dos manifests. Sem reprocess, sem tocar src/.
Uso: simula_idf_sub.py <dir_snapshot_antes>
Variantes: base (reproduz o baseline; gate do harness) · V1 tokens: tokens do titulo da unidade + tokens presentes em >= 2
subtopicos irmaos viram genericos (so no bonus de overlap) · V2 = V1 + frases: alias repetido em >= 2 irmaos ou cujos tokens
sao todos genericos sai da lista (phrase-IDF) · V2s = V1 + so alias repetido VERBATIM em >= 2 irmaos sai."""
import collections
import csv
import functools
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
SNAP = Path(sys.argv[1])
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
iter_orig = eng._iter_content_taxonomy_topics


def _toks(t):
    return {x for x in normalize_match_text(str(t or "")).split() if len(x) >= 4}


def make_iter(variante: str):
    def _iter(taxonomy):
        topics = [dict(t) for t in iter_orig(taxonomy)]
        if variante == "base":
            return topics
        por_unidade = collections.defaultdict(list)
        for t in topics:
            por_unidade[t["unit_slug"]].append(t)
        for unit_slug, irmaos in por_unidade.items():
            generic = set(irmaos[0].get("generic_tokens") or [])
            titulo = _toks(irmaos[0].get("unit_title")) - generic
            df_tok = collections.Counter()
            df_frase = collections.Counter()
            for t in irmaos:
                vocab = set()
                frases = set()
                for ph in [t["topic_label"]] + list(t.get("aliases") or []):
                    vocab |= _toks(ph) - generic
                    frases.add(normalize_match_text(ph))
                df_tok.update(vocab)
                df_frase.update(frases)
            shared = {tok for tok, n in df_tok.items() if n >= 2}
            intra = titulo | shared
            for t in irmaos:
                t["generic_tokens"] = sorted(generic | intra)
                if variante in ("V2", "V2s"):
                    keep = []
                    for al in t.get("aliases") or []:
                        n = normalize_match_text(al)
                        if df_frase[n] >= 2 or (variante == "V2" and not (_toks(al) - generic - intra)):
                            continue
                        keep.append(al)
                    t["aliases"] = keep
        return topics
    return _iter


def subtopic_fn(variante):
    return functools.partial(
        fm.auto_map_entry_subtopic,
        collect_entry_unit_signals=eng._collect_entry_unit_signals,
        iter_content_taxonomy_topics=make_iter(variante),
        score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
        topic_match_result_factory=TopicMatchResult,
    )


def texto(root: Path, entry: dict, code_cur: dict) -> str:
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    if resumo:
        return f"{md}\n\n{resumo}" if md else resumo
    return md


VARIANTES = ["base", "V1", "V2", "V2s"]
resultado = {v: collections.Counter() for v in VARIANTES}
for sig, repo in REPO.items():
    root = COPY / repo
    man = {e["id"]: e for e in json.loads((SNAP / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    with (GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("scorable") == "yes"]
    fns = {v: subtopic_fn(v) for v in VARIANTES}
    for r in rows:
        e = man.get(r["entry_id"])
        if e is None:
            print(f"  ?? {sig} {r['entry_id']} nao esta no manifest"); continue
        alvo = {r["gold_subunit"]} | set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
        t = texto(root, e, code_cur)
        unit = str(e.get("computed_unit_slug") or "")
        preds = {}
        for v in VARIANTES:
            m = fns[v](e, tax, t, winning_unit_slug=unit)
            preds[v] = (str(m.topic_slug or ""), m.confidence, m.ambiguous, list(m.reasons))
        # gate do harness: base tem que reproduzir o campo gravado no snapshot
        gravado = str(e.get("computed_subunit_slug") or "")
        if preds["base"][0] != gravado:
            resultado["base"]["DIVERGE_DO_SNAPSHOT"] += 1
            print(f"  !! {sig} {r['entry_id'][:40]} harness={preds['base'][0]!r} snapshot={gravado!r} {preds['base'][3]}")
        for v in VARIANTES:
            ok = preds[v][0] in alvo
            resultado[v]["ok"] += ok
            resultado[v]["n"] += 1
            if v != "base":
                a, b = preds["base"][0] in alvo, ok
                flip = "+" if (b and not a) else "-" if (a and not b) else ("~" if preds[v][0] != preds["base"][0] else "=")
                resultado[v][flip] += 1
                if flip != "=":
                    print(f"  {v} {flip} {sig:3} {r['entry_id'][:38]:38} base={preds['base'][0][:26] or '-':26} -> {preds[v][0][:26] or '-':26} gold={r['gold_subunit'][:24]:24} conf {preds['base'][1]:.2f}->{preds[v][1]:.2f}")
for v in VARIANTES:
    c = resultado[v]
    print(f"{v:4} subunidade {c['ok']}/{c['n']}" + (f"  flips: + {c['+']}  - {c['-']}  ~ {c['~']}" if v != "base" else f"  diverge_do_snapshot={c['DIVERGE_DO_SNAPSHOT']}"))
