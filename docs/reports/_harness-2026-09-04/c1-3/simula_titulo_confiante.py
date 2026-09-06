"""Alavanca para os 'confiantes errados' da subunidade: parte do rotulo (decomposicao) presente no TITULO do material
(title + label do Moodle) vence a decisao confiante da 1a passada. Simulada em memoria pela rota real nas copias `.ablacao`
(regua automatica), 6 golds (233), 0 chamadas.
  base  1a passada + 2a passada REAL (`propagar_vocabulario_por_headings`, headings + partes) — gate: reproduz o gravado
  T1    entry confiante cujo TITULO contem uma parte de rotulo do topico Y != vencedor, e NENHUMA frase (label/aliases) do
        vencedor esta no titulo -> Y
  T1b   T1 e Y ja pontuava > 0 no corpo na 1a passada (evidencia alem do titulo)
  T2    T1 restrito a vencedor com margem pequena (score do 2o >= 50% do 1o)
Uso: simula_titulo_confiante.py"""
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
from src.builder.routing.resolver_apply import _partes_de_rotulo, propagar_vocabulario_por_headings  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)


def texto(root, entry, code_cur):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


def titulo(entry) -> str:
    ml = entry.get("moodle_label")
    ml = ml.get("text") if isinstance(ml, dict) else ml
    return N(f"{entry.get('title') or ''} {ml or ''}")


def frase_no(texto_norm: str, frase: str) -> bool:
    n = N(frase)
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


VARS = ["base", "T1", "T1b", "T2"]
res = {v: collections.Counter() for v in VARS}
for sig, repo in REPO.items():
    root = COPY / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    units = {str(u.get("slug") or ""): u for u in tax["units"]}
    topics = list(eng._iter_content_taxonomy_topics(tax))
    por_unidade = collections.defaultdict(list)
    for t in topics:
        por_unidade[t["unit_slug"]].append(t)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    rows = {r["entry_id"]: r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}
    # 1a passada real em todos os materiais (a 2a passada precisa do df e das sementes do curso inteiro)
    passe1 = []
    scores1 = {}
    for e in man.values():
        unit = str(e.get("computed_unit_slug") or "")
        if not unit or e.get("manual_subunit_slug"):
            continue
        ent = dict(e)
        t = texto(root, ent, code_cur)
        m = sub_fn(ent, tax, t, winning_unit_slug=unit)
        ent["computed_subunit_slug"] = str(m.topic_slug or "")
        ent["subunit_match_reasons"] = list(m.reasons)
        sig_e = eng._collect_entry_unit_signals(ent, t)
        scores1[e["id"]] = {tp["topic_slug"]: eng._score_entry_against_taxonomy_topic(sig_e, tp) for tp in por_unidade.get(unit, [])}
        passe1.append((ent, t, unit, m))
    propagar_vocabulario_por_headings(passe1, tax, sub_fn, conf_min=T.SUBUNIT_PROPAG_CONF, min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX)
    partes = _partes_de_rotulo(units, passe1, T.SUBUNIT_PROPAG_DF_MAX)
    frases_por_topico = {t["topic_slug"]: [t["topic_label"]] + list(t.get("aliases") or []) for t in topics}
    for ent, t, unit, m in passe1:
        eid = ent["id"]
        r = rows.get(eid)
        if r is None:
            continue
        alvo = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
        base = ent["computed_subunit_slug"]
        gravado = str(man[eid].get("computed_subunit_slug") or "")
        if base != gravado:
            res["base"]["DIVERGE"] += 1
        confiante = bool(m.topic_slug) and not m.ambiguous and m.confidence >= T.SUBUNIT_PROPAG_CONF
        tit = titulo(ent)
        preds = {"base": base, "T1": base, "T1b": base, "T2": base}
        if confiante:
            cand = [y for (u, y), ps in partes.items() if u == unit and y != base and any(frase_no(tit, p) for p in ps)]
            venc_no_titulo = any(frase_no(tit, f) for f in frases_por_topico.get(base, []))
            if len(cand) == 1 and not venc_no_titulo:
                y = cand[0]
                sc = scores1.get(eid, {})
                ordenado = sorted(sc.values(), reverse=True)
                margem_pequena = len(ordenado) > 1 and ordenado[0] > 0 and ordenado[1] >= 0.5 * ordenado[0]
                preds["T1"] = y
                if sc.get(y, 0) > 0:
                    preds["T1b"] = y
                if margem_pequena:
                    preds["T2"] = y
        for v in VARS:
            ok = preds[v] in alvo
            res[v]["ok"] += ok
            res[v]["n"] += 1
            if v != "base":
                a, b = base in alvo, ok
                flip = "+" if (b and not a) else "-" if (a and not b) else ("~" if preds[v] != base else "=")
                res[v][flip] += 1
                if flip != "=":
                    print(f"  {v:3} {flip} {sig:3} {eid[:40]:40} {base[-26:] or '-':26} -> {preds[v][-26:]:26} gold={r['gold_subunit'][-24:] or '(vazio)'} | titulo={tit[:50]!r}")
for v in VARS:
    c = res[v]
    print(f"{v:4} subunidade {c['ok']}/{c['n']}" + (f"  flips + {c['+']} - {c['-']} ~ {c['~']}" if v != "base" else f"  diverge_do_gravado={c['DIVERGE']}"))
