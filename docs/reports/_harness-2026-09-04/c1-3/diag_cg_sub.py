"""Diagnostico dos erros de SUBUNIDADE do CG (gold aprovado 06/09) pela rota real do scorer, em memoria, na copia
`.ablacao/Computacao-Grafica-Tutor` (estado = regua automatica). Para cada erro: causa, texto disponivel (tamanho, pagina de
login?), pontuacao do predito e do gold, top-3 do scorer na unidade, e quais aliases do gold aparecem no texto. 0 chamadas."""
import collections
import csv
import functools
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
REPO = "Computacao-Grafica-Tutor"
SIG = sys.argv[1] if len(sys.argv) > 1 else "CG"
REPOS = {"CG": "Computacao-Grafica-Tutor", "MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor",
         "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
REPO = REPOS[SIG]
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

root = COPY / REPO
man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
tax = load_internal_content_taxonomy(root)
code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
topics = list(eng._iter_content_taxonomy_topics(tax))
por_unidade = collections.defaultdict(list)
for t in topics:
    por_unidade[t["unit_slug"]].append(t)
sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)
LOGIN = re.compile(r"\b(login|senha|password|acessar|entrar|username|usuario)\b", re.I)


def texto(entry):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{SIG}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
causas = collections.Counter()
familias = collections.defaultdict(list)
ok = 0
for r in rows:
    e = man.get(r["entry_id"])
    if not e:
        print("?? sumiu", r["entry_id"]); continue
    alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
    t = texto(e)
    unit = str(e.get("computed_unit_slug") or "")
    m = sub_fn(e, tax, t, winning_unit_slug=unit)
    pred = str(m.topic_slug or "")
    gravado = str(e.get("computed_subunit_slug") or "")
    if pred != gravado:
        print(f"  !! harness={pred!r} gravado={gravado!r} {r['entry_id'][:40]} {list(m.reasons)}")
    if pred in alvo:
        ok += 1; continue
    sig = eng._collect_entry_unit_signals(e, t)
    scores = sorted(((eng._score_entry_against_taxonomy_topic(sig, tp), tp["topic_slug"]) for tp in por_unidade.get(unit, [])), reverse=True)
    top = {s: sc for sc, s in scores}
    gold = r["gold_subunit"]
    ntxt = len(t or "")
    login = bool(LOGIN.search(t or "")) and ntxt < 3000
    # aliases do gold que aparecem no texto
    gt = next((tp for tp in por_unidade.get(unit, []) if tp["topic_slug"] == gold), None)
    hits = []
    if gt:
        tn = N(t or "")
        for ph in [gt["topic_label"]] + list(gt.get("aliases") or []):
            if N(ph) and N(ph) in tn:
                hits.append(ph)
    if not gold:
        causa = "gold-vazio-preenchido"
    elif not pred:
        causa = "vazia"
    elif m.ambiguous:
        causa = "ambigua"
    elif top.get(pred, 0) < 1:
        causa = "fraca"
    else:
        causa = "confiante"
    if login:
        causa += "+LOGIN"
    elif ntxt < 200:
        causa += "+SEM-TEXTO"
    causas[causa] += 1
    familias[causa].append(r["entry_id"])
    top3 = " · ".join(f"{s[:22]}={sc:.2f}" for sc, s in scores[:3])
    print(f"[{causa:24}] {r['entry_id'][:38]:38} cat={str(e.get('category'))[:14]:14} txt={ntxt:6} unit={unit[-22:]:22} pred={pred[-24:] or '-':24} ({top.get(pred, 0):.2f}) gold={gold[-24:] or '(vazio)':24} ({top.get(gold, 0):.2f}) | top: {top3} | aliases do gold no texto: {hits[:4]}")
print(f"\n{SIG}: certo {ok}/{len(rows)} · causas: {dict(causas.most_common())}")
for c, ids in familias.items():
    print(f"   {c}: {ids}")
