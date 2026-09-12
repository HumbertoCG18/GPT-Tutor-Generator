"""TETO DA ARQUITETURA PROPOSTA PELO USER (08/09): extrair palavras-chave dos arquivos, agrupar, e so entao casar com
as subunidades do plano.

A 2a passada que ja existe (`resolver_apply.propagar_vocabulario_por_headings`) e essa ideia, mas SEMEADA: so propaga a
partir de materiais que a 1a passada ja decidiu com confianca. Onde o vocabulario e fraco, nao ha semente — ovo e galinha.
O que a proposta do user acrescenta e dispensar a semente: se os arquivos se AGRUPAREM sozinhos por palavra-chave, uma
evidencia fraca por grupo decide o grupo inteiro.

Isso so funciona se o agrupamento respeitar a fronteira de subunidade. Este script mede exatamente isso, com a taxonomia
LIMPA (sem vocabulario de LLM e sem sidecar curado) — o regime "sem LLM" de verdade:

  A) PUREZA   dos grupos: dos pares de arquivos que caem no mesmo grupo, quantos tem a mesma subunidade no gold?
  B) TETO     com oraculo no grupo (cada grupo recebe a subunidade majoritaria do gold): o maximo que a arquitetura da.
  C) REAL     cada grupo recebe o topico de maior score SOMADO sobre os membros (deterministico, sem gold).
  BASE        o motor por arquivo, mesma taxonomia limpa.

Agrupamento: dentro da UNIDADE (a subunidade so compete la), arestas entre arquivos que compartilham >= K tokens
distintivos (df <= DF_MAX no curso), componentes conexas.
0 chamadas. Uso: mede_cluster_keywords.py
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
DF_MAX = 0.20     # token em mais de 20% dos materiais do curso nao e distintivo
KS = [2, 3, 4]    # tokens distintivos em comum para ligar dois arquivos
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


def limpa(tax: dict, curados: set) -> dict:
    """Taxonomia sem alias vindo de LLM ou de sidecar curado."""
    import copy
    t = copy.deepcopy(tax)
    units = t.get("units")
    it = list(units.values()) if isinstance(units, dict) else list(units or [])
    for u in it:
        for tp in (u.get("topics") or []):
            tp["aliases"] = [a for a in (tp.get("aliases") or []) if N(a) not in curados]
    return t


TOT = collections.Counter()
DET = []
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    # vocabulario a REMOVER: sidecar curado (arquivado) + compilado por LLM
    curados = set()
    for nome in (".glossary_curation.json", ".glossary_curation.gold.json", ".glossary_curation.llm.json"):
        p = root / "course" / nome
        if p.exists():
            for k, v in json.loads(p.read_text(encoding="utf-8")).items():
                if not k.startswith("_"):
                    curados |= {N(s) for s in (v.get("synonyms") or [])}
    tax = limpa(load_internal_content_taxonomy(root), curados)
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade[t["unit_slug"]].append(t)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    gs = {r["entry_id"]: ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
          for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}
    # texto e tokens distintivos
    txt, toks = {}, {}
    df = collections.Counter()
    for eid, e in man.items():
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(eid) or "") or {}
        t = f"{md}\n{code_curation_signal_text(rec) if rec else ''}"
        txt[eid] = t
        toks[eid] = _tokens(t)
        df.update(toks[eid])
    teto = DF_MAX * max(1, len(man))
    distintivo = {eid: {x for x in v if df[x] <= teto} for eid, v in toks.items()}
    # base: motor por arquivo, taxonomia limpa
    base = 0
    score_cache = {}
    for eid in gs:
        e = man.get(eid)
        if not e:
            continue
        u = str(e.get("computed_unit_slug") or "")
        m = sub_fn(e, tax, txt[eid], winning_unit_slug=u)
        base += str(m.topic_slug or "") in gs[eid]
        sinais = eng._collect_entry_unit_signals(e, txt[eid])
        score_cache[eid] = {tp["topic_slug"]: eng._score_entry_against_taxonomy_topic(sinais, tp)
                            for tp in por_unidade.get(u, [])}
    for K in KS:
        # componentes conexas dentro da unidade
        por_u = collections.defaultdict(list)
        for eid in gs:
            e = man.get(eid)
            if e:
                por_u[str(e.get("computed_unit_slug") or "")].append(eid)
        pai = {eid: eid for eid in gs}

        def acha(x):
            while pai[x] != x:
                pai[x] = pai[pai[x]]
                x = pai[x]
            return x

        for u, ids in por_u.items():
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    if len(distintivo[ids[i]] & distintivo[ids[j]]) >= K:
                        a, b = acha(ids[i]), acha(ids[j])
                        if a != b:
                            pai[a] = b
        grupos = collections.defaultdict(list)
        for eid in gs:
            grupos[acha(eid)].append(eid)
        # A) pureza dos pares
        par_ok = par_tot = 0
        for g in grupos.values():
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    par_tot += 1
                    par_ok += bool(gs[g[i]] & gs[g[j]])
        # B) teto com oraculo no grupo
        oraculo = 0
        for g in grupos.values():
            cnt = collections.Counter()
            for eid in g:
                for s in gs[eid]:
                    cnt[s] += 1
            melhor = cnt.most_common(1)[0][0] if cnt else ""
            oraculo += sum(1 for eid in g if melhor in gs[eid])
        # C) real: soma dos scores no grupo
        real = 0
        for g in grupos.values():
            soma = collections.Counter()
            for eid in g:
                for s, v in (score_cache.get(eid) or {}).items():
                    soma[s] += v
            melhor = soma.most_common(1)[0][0] if soma and soma.most_common(1)[0][1] > 0 else ""
            real += sum(1 for eid in g if melhor in gs[eid])
        ngrup = len([g for g in grupos.values() if len(g) > 1])
        DET.append((sig, K, len(gs), base, len(grupos), ngrup, par_ok, par_tot, oraculo, real))
        TOT[f"base"] = TOT.get("base", 0)
    TOT["n"] += len(gs)
    TOT["base"] += base

print(f"taxonomia LIMPA (sem vocabulario de LLM e sem sidecar curado) — o regime 'sem LLM' de verdade")
print(f"{'':4} {'K':>2} {'n':>4} {'base':>5} {'grupos':>7} {'>1':>4} {'pureza dos pares':>18} {'TETO oraculo':>13} {'REAL soma':>10}")
for d in DET:
    sig, K, n, base, ng, ng1, po, pt, ora, real = d
    pur = f"{po}/{pt} {100 * po / pt:.0f}%" if pt else "-"
    print(f"{sig:4} {K:2} {n:4} {base:5} {ng:7} {ng1:4} {pur:>18} {ora:6} {100 * ora / n:4.0f}% {real:5} {100 * real / n:4.0f}%")
print()
for K in KS:
    sub = [d for d in DET if d[1] == K]
    n = sum(d[2] for d in sub)
    print(f"K={K}: base {sum(d[3] for d in sub)}/{n} · TETO com oraculo no grupo {sum(d[8] for d in sub)}/{n} · "
          f"REAL {sum(d[9] for d in sub)}/{n} · pureza {sum(d[6] for d in sub)}/{sum(d[7] for d in sub)}")
