"""A proposta do user como ALAVANCA, nao como arquitetura de substituicao (08/09).

Medido antes: o vizinho mais similar por palavras-chave tem a mesma subunidade em 76% dos casos
(`mede_vizinho_keywords.log`). A 2a passada que ja existe propaga por HEADINGS a partir de materiais confiantes; esta
simulacao acrescenta uma 3a via: **material que continua indeciso herda a subunidade do vizinho mais similar que o motor
decidiu com confianca**. Similaridade = Jaccard dos tokens distintivos (df <= 20% do curso), dentro da unidade.

Rota real em memoria: 1a passada + 2a passada REAL (`propagar_vocabulario_por_headings`) + a regra por cima, nos 6 golds.
Variantes por piso de similaridade. Regime honesto: taxonomia LIMPA (sem sidecar curado, sem vocabulario de LLM) e
tambem no estado ATUAL do produto, para ver se a alavanca sobrevive quando ja ha vocabulario.
0 chamadas. Uso: simula_propaga_similaridade.py
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
PISOS = [0.05, 0.10, 0.20, 0.30]
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings  # noqa: E402
from src.builder.routing.thresholds import T as TH  # noqa: E402
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


def roda(regime: str):
    TOT = collections.Counter()
    for sig, repo in GOLD.items():
        root = GH / repo
        man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        curados = set()
        if regime == "LIMPO":
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
        # 1a passada + 2a passada REAL, como o motor faz
        passe1 = []
        for eid, e in man.items():
            u = str(e.get("computed_unit_slug") or "")
            m = sub_fn(e, tax, txt[eid], winning_unit_slug=u)
            passe1.append((e, txt[eid], u, m))
        propagar_vocabulario_por_headings(passe1, tax, sub_fn, conf_min=TH.SUBUNIT_PROPAG_CONF,
                                          min_entries=TH.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=TH.SUBUNIT_PROPAG_DF_MAX)
        dec, conf = {}, {}
        for e, t, u, m in passe1:
            dec[e["id"]] = str(m.topic_slug or "")
            conf[e["id"]] = float(getattr(m, "confidence", 0) or 0)
        por_u = collections.defaultdict(list)
        for eid, e in man.items():
            por_u[str(e.get("computed_unit_slug") or "")].append(eid)
        base = sum(1 for eid in gs if dec.get(eid, "") in gs[eid])
        TOT["base"] += base
        TOT["n"] += len(gs)
        for piso in PISOS:
            novo = dict(dec)
            for u, ids in por_u.items():
                ancoras = [b for b in ids if dec.get(b) and conf.get(b, 0) >= TH.SUBUNIT_PROPAG_CONF]
                for a in ids:
                    if dec.get(a):
                        continue          # so onde o motor NAO decidiu
                    sims = sorted(((len(dist[a] & dist[b]) / max(1, len(dist[a] | dist[b])), b) for b in ancoras), reverse=True)
                    if sims and sims[0][0] >= piso:
                        novo[a] = dec[sims[0][1]]
            ok = sum(1 for eid in gs if novo.get(eid, "") in gs[eid])
            mud = sum(1 for eid in gs if novo.get(eid, "") != dec.get(eid, ""))
            g = sum(1 for eid in gs if novo.get(eid, "") in gs[eid] and dec.get(eid, "") not in gs[eid])
            p = sum(1 for eid in gs if dec.get(eid, "") in gs[eid] and novo.get(eid, "") not in gs[eid])
            TOT[f"ok{piso}"] += ok
            TOT[f"mud{piso}"] += mud
            TOT[f"g{piso}"] += g
            TOT[f"p{piso}"] += p
    return TOT


for regime in ("LIMPO", "ATUAL"):
    T = roda(regime)
    print(f"\n=== regime {regime} ({'sem vocabulario nenhum' if regime == 'LIMPO' else 'produto como esta hoje'}) ===")
    print(f"  base (1a + 2a passada real): {T['base']}/{T['n']}")
    print(f"  {'piso':>6} {'certos':>7} {'delta':>6} {'ganha':>6} {'perde':>6} {'muda':>5}")
    for piso in PISOS:
        print(f"  {piso:6.2f} {T[f'ok{piso}']:7} {T[f'ok{piso}'] - T['base']:+6} {T[f'g{piso}']:6} {T[f'p{piso}']:6} {T[f'mud{piso}']:5}")
