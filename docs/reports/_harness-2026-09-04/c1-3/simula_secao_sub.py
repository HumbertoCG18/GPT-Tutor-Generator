"""Regra da SECAO do Moodle para a subunidade (06/09; oraculo: a secao "Curvas Parametricas" nomeia o subtopico). Simulada em memoria
pela rota real (1a passada + 2a passada REAL + regra por cima) nas copias `.ablacao`, 6 golds (233), 0 chamadas.
  base  reproduz o gravado
  S1    1a passada NAO confiante (vazio/ambiguo/conf < 0,7): secao nomeia exatamente UM subtopico da unidade -> ele (sobrepoe a 2a passada)
  S1b   como S1, mas so se DEPOIS da 2a passada a subunidade ainda esta vazia ou ambigua
  S2    S1 + decisao confiante tambem cai quando a secao nomeia exatamente um subtopico Y != vencedor e nao nomeia o vencedor
'Nomeia' = frase (label/alias) contida na secao ou secao contida na frase, ou tokens especificos de um contem os do outro; tokens genericos fora.
Uso: simula_secao_sub.py"""
import collections
import csv
import functools
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
GEN_T = {"exercicios", "exercicio", "processamento", "imagens", "computacao", "grafica", "sobre", "para", "geometrica", "introducao",
         "algoritmos", "algoritmo", "conceito", "conceitos", "tecnicas", "representacao", "unidade", "semana", "aula", "aulas", "parte"}
_NUM = re.compile(r"^\s*\d+(\.\d+)*\s*[-.]?\s*")
sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)


def toks(s):
    return {x for x in N(s).split() if len(x) >= 4} - GEN_T


def texto(root, entry, code_cur):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


def secao_nomeia(secao, unit_topics):
    """slugs dos subtopicos da unidade que a secao nomeia."""
    s = N(_NUM.sub("", secao or ""))
    st = toks(s)
    if not s:
        return set()
    hits = set()
    for t in unit_topics:
        frases = [N(x) for x in [t["topic_label"]] + list(t.get("aliases") or []) if N(x)]
        if any(re.search(r"(^|\s)" + re.escape(f) + r"(\s|$)", s) or re.search(r"(^|\s)" + re.escape(s) + r"(\s|$)", f) for f in frases):
            hits.add(t["topic_slug"])
            continue
        lt = toks(t["topic_label"])
        if st and lt and (st <= lt or lt <= st):
            hits.add(t["topic_slug"])
    return hits


VARS = ["base", "S1", "S1b", "S2"]
res = {v: collections.Counter() for v in VARS}
for sig, repo in REPO.items():
    root = COPY / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    topics = list(eng._iter_content_taxonomy_topics(tax))
    por_unidade = collections.defaultdict(list)
    for t in topics:
        por_unidade[t["unit_slug"]].append(t)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    rows = {r["entry_id"]: r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}
    passe1 = []
    for e in man.values():
        unit = str(e.get("computed_unit_slug") or "")
        if not unit or e.get("manual_subunit_slug"):
            continue
        ent = dict(e)
        t = texto(root, ent, code_cur)
        m = sub_fn(ent, tax, t, winning_unit_slug=unit)
        ent["computed_subunit_slug"] = str(m.topic_slug or "")
        ent["subunit_match_reasons"] = list(m.reasons)
        passe1.append((ent, t, unit, m))
    propagar_vocabulario_por_headings(passe1, tax, sub_fn, conf_min=T.SUBUNIT_PROPAG_CONF, min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX)
    frases_topico = {t["topic_slug"]: [t["topic_label"]] + list(t.get("aliases") or []) for t in topics}
    for ent, t, unit, m in passe1:
        eid = ent["id"]
        r = rows.get(eid)
        if r is None:
            continue
        alvo = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
        base = ent["computed_subunit_slug"]
        if base != str(man[eid].get("computed_subunit_slug") or ""):
            res["base"]["DIVERGE"] += 1
        confiante = bool(m.topic_slug) and not m.ambiguous and m.confidence >= T.SUBUNIT_PROPAG_CONF
        hits = secao_nomeia(str(ent.get("source_section") or ""), por_unidade.get(unit, []))
        y = next(iter(hits)) if len(hits) == 1 else ""
        preds = {v: base for v in VARS}
        if y:
            if not confiante:
                preds["S1"] = y
                preds["S2"] = y
                ainda_indecisa = (not base) or ("ambiguous" in " ".join(ent.get("subunit_match_reasons") or [])) or any(str(x).startswith("empate") for x in (ent.get("subunit_match_reasons") or []))
                if ainda_indecisa:
                    preds["S1b"] = y
            elif y != base:
                sec_norm = N(_NUM.sub("", str(ent.get("source_section") or "")))
                venc_na_secao = any(N(f) and re.search(r"(^|\s)" + re.escape(N(f)) + r"(\s|$)", sec_norm) for f in frases_topico.get(base, []))
                if not venc_na_secao:
                    preds["S2"] = y
        for v in VARS:
            ok = preds[v] in alvo
            res[v]["ok"] += ok
            res[v]["n"] += 1
            if v != "base":
                a, b = base in alvo, ok
                flip = "+" if (b and not a) else "-" if (a and not b) else ("~" if preds[v] != base else "=")
                res[v][flip] += 1
                if flip != "=":
                    print(f"  {v:3} {flip} {sig:3} {eid[:36]:36} [{str(ent.get('source_section') or '')[:26]:26}] {base[-24:] or '-':24} -> {preds[v][-24:]:24} gold={r['gold_subunit'][-22:] or '(vazio)'}")
for v in VARS:
    c = res[v]
    print(f"{v:4} subunidade {c['ok']}/{c['n']}" + (f"  flips + {c['+']} - {c['-']} ~ {c['~']}" if v != "base" else f"  diverge_do_gravado={c['DIVERGE']}"))
