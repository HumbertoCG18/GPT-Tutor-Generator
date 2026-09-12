"""Versao JUSTA do teste da arquitetura do user: sem fecho transitivo.

`mede_cluster_keywords.py` usou componentes conexas e degenerou (IA virou 1 grupo de 39). Aqui a pergunta e direta e
sem encadeamento: **dois arquivos parecidos por palavra-chave tem a mesma subunidade?**

  VIZINHO   para cada material, o mais similar (Jaccard dos tokens distintivos, dentro da unidade): ele tem a mesma
            subunidade no gold? Essa e a taxa que qualquer propagacao por similaridade herda como teto.
  kNN-3     entre os 3 mais similares, a subunidade majoritaria bate com o gold?
  ANCORA    so entre pares onde UM dos dois o motor ja decide certo (o caso real da propagacao): o vizinho herda certo?
Taxonomia LIMPA (sem LLM, sem sidecar). Compara com a similaridade contra o ROTULO do topico, que e o que o scorer ja faz.
0 chamadas. Uso: mede_vizinho_keywords.py
"""
import collections
import csv as _csv
import functools
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
DF_MAX = 0.20
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.timeline.unit_matcher import _tokens  # noqa: E402

sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)


def limpa(tax, curados):
    import copy
    t = copy.deepcopy(tax)
    units = t.get("units")
    for u in (list(units.values()) if isinstance(units, dict) else list(units or [])):
        for tp in (u.get("topics") or []):
            tp["aliases"] = [a for a in (tp.get("aliases") or []) if N(a) not in curados]
    return t


T = collections.Counter()
print(f"{'':4} {'n':>4} {'base':>5} {'VIZINHO igual':>15} {'kNN-3':>12} {'ANCORA certa':>14}")
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    curados = set()
    for nome in (".glossary_curation.json", ".glossary_curation.gold.json", ".glossary_curation.llm.json"):
        p = root / "course" / nome
        if p.exists():
            for k, v in json.loads(p.read_text(encoding="utf-8")).items():
                if not k.startswith("_"):
                    curados |= {N(s) for s in (v.get("synonyms") or [])}
    tax = limpa(load_internal_content_taxonomy(root), curados)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    gs = {r["entry_id"]: ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
          for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}
    txt, toks, df = {}, {}, collections.Counter()
    for eid, e in man.items():
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(eid) or "") or {}
        txt[eid] = f"{md}\n{code_curation_signal_text(rec) if rec else ''}"
        toks[eid] = _tokens(txt[eid])
        df.update(toks[eid])
    teto = DF_MAX * max(1, len(man))
    dist = {eid: {x for x in v if df[x] <= teto} for eid, v in toks.items()}
    certo = {}
    for eid in gs:
        e = man.get(eid)
        if not e:
            continue
        m = sub_fn(e, tax, txt[eid], winning_unit_slug=str(e.get("computed_unit_slug") or ""))
        certo[eid] = str(m.topic_slug or "") in gs[eid]
    por_u = collections.defaultdict(list)
    for eid in gs:
        e = man.get(eid)
        if e:
            por_u[str(e.get("computed_unit_slug") or "")].append(eid)
    c = collections.Counter()
    for u, ids in por_u.items():
        for a in ids:
            sims = sorted(((len(dist[a] & dist[b]) / max(1, len(dist[a] | dist[b])), b) for b in ids if b != a), reverse=True)
            if not sims or sims[0][0] <= 0:
                continue
            c["n"] += 1
            viz = sims[0][1]
            c["viz"] += bool(gs[a] & gs[viz])
            top3 = [b for _, b in sims[:3]]
            cnt = collections.Counter()
            for b in top3:
                for s in gs[b]:
                    cnt[s] += 1
            c["knn"] += bool(cnt and cnt.most_common(1)[0][0] in gs[a])
            if certo.get(viz):
                c["anc_n"] += 1
                c["anc_ok"] += bool(gs[a] & gs[viz])
    base = sum(1 for v in certo.values() if v)
    T.update(c)
    T["base"] += base
    T["ngold"] += len(gs)
    print(f"{sig:4} {len(gs):4} {base:5} {c['viz']:6}/{c['n']:<4} {100 * c['viz'] / max(1, c['n']):4.0f}% "
          f"{c['knn']:5}/{c['n']:<4} {100 * c['knn'] / max(1, c['n']):4.0f}% {c['anc_ok']:5}/{c['anc_n']:<4} {100 * c['anc_ok'] / max(1, c['anc_n']):4.0f}%")
print(f"{'TOT':4} {T['ngold']:4} {T['base']:5} {T['viz']:6}/{T['n']:<4} {100 * T['viz'] / max(1, T['n']):4.0f}% "
      f"{T['knn']:5}/{T['n']:<4} {100 * T['knn'] / max(1, T['n']):4.0f}% {T['anc_ok']:5}/{T['anc_n']:<4} {100 * T['anc_ok'] / max(1, T['anc_n']):4.0f}%")
print("\nLEITURA: 'VIZINHO igual' e o teto de QUALQUER propagacao por similaridade de palavras-chave.")
print("Se estiver perto de 50%, arquivos parecidos NAO compartilham subunidade e a arquitetura nao fecha.")
