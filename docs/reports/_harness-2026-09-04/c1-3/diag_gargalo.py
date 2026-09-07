"""GARGALO da subunidade + composicao da FILA, no PRODUTO em disco (pos-filtro da descricao), 0 chamadas.

Parte A - subunidade nos 6 cursos com gold: classifica cada erro por CAUSA (vazia/fraca/ambigua/confiante) cruzada com a
EVIDENCIA do gold no texto: o label ou algum alias do subtopico correto aparece no texto que o motor pontua?
  - sem evidencia -> vocabulario: o motor nao TEM como acertar com o texto atual.
  - com evidencia -> decisao: a evidencia esta la e o scorer preferiu outra.
Parte B - fila dos 8: conta `revisar` por motivo.
Uso: diag_gargalo.py
"""
import collections
import csv
import functools
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
TODOS = dict(REPOS, LR="Laboratorio-de-Redes-Tutor", FR="Fundamentos-de-Redes-Tutor")
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)


def texto(root, entry, code_cur):
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


GLOBAL = collections.Counter()
LINHAS = []
print("=" * 120)
print("PARTE A - subunidade: causa x evidencia do gold no texto")
print("=" * 120)
for sig, repo in REPOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade[t["unit_slug"]].append(t)
    csvp = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    rows = [r for r in csv.DictReader(csvp.open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    ok, causas = 0, collections.Counter()
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        t = texto(root, e, code_cur)
        unit = str(e.get("computed_unit_slug") or "")
        m = sub_fn(e, tax, t, winning_unit_slug=unit)
        p1 = str(m.topic_slug or "")
        pred = str(e.get("computed_subunit_slug") or "")
        razoes = " ".join(str(x) for x in (e.get("subunit_match_reasons") or []))
        if pred in alvo:
            ok += 1
            continue
        sig_ = eng._collect_entry_unit_signals(e, t)
        scores = sorted(((eng._score_entry_against_taxonomy_topic(sig_, tp), tp["topic_slug"]) for tp in por_unidade.get(unit, [])), reverse=True)
        top = {s: sc for sc, s in scores}
        gold = r["gold_subunit"]
        gt = next((tp for tp in por_unidade.get(unit, []) if tp["topic_slug"] == gold), None)
        tn = N(t or "")
        hits = [ph for ph in ([gt["topic_label"]] + list(gt.get("aliases") or []) if gt else []) if N(ph) and N(ph) in tn]
        if not gold:
            causa = "gold-vazio"
        elif not gt:
            causa = "gold-fora-da-unidade"
        elif not pred:
            causa = "vazia"
        elif top.get(gold, 0) <= 0:
            causa = "gold-pontua-zero"
        elif top.get(pred, 0) < 1:
            causa = "fraca"
        else:
            causa = "confiante"
        ev = "COM-evidencia" if hits else "SEM-evidencia"
        chave = f"{causa}/{ev}"
        causas[chave] += 1
        GLOBAL[chave] += 1
        LINHAS.append((sig, chave, r["entry_id"][:34], unit[-20:], pred[-22:] or "-", f"{top.get(pred, 0):.2f}",
                       gold[-22:] or "(vazio)", f"{top.get(gold, 0):.2f}", len(t or ""), hits[:2], razoes[:44], p1[-18:]))
    print(f"\n{sig}: {ok}/{len(rows)} · {dict(causas.most_common())}")
print("\n" + "-" * 120)
for l in sorted(LINHAS, key=lambda x: (x[1], x[0])):
    print(f"[{l[1]:26}] {l[0]:3} {l[2]:34} unit={l[3]:20} pred={l[4]:22}({l[5]}) gold={l[6]:22}({l[7]}) txt={l[8]:6} ev={l[9]} why={l[10]} p1={l[11]}")
print("\nTOTAL POR CAUSA x EVIDENCIA:")
tot = sum(GLOBAL.values())
for k, v in GLOBAL.most_common():
    print(f"   {k:30} {v:3}  ({100 * v / tot:.0f}%)")
print(f"   {'soma':30} {tot:3}")

print()
print("=" * 120)
print("PARTE B - fila (revisar) nos 8, por motivo")
print("=" * 120)
FILA = collections.Counter()
POR_CURSO = {}
for sig, repo in TODOS.items():
    man = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    c = collections.Counter()
    for e in man:
        for mot in (e.get("revisar") or []):
            m = mot if isinstance(mot, str) else str(mot.get("motivo") or mot.get("reason") or mot)
            c[m] += 1
            FILA[m] += 1
    POR_CURSO[sig] = (sum(c.values()), len([e for e in man if e.get("revisar")]), len(man))
    print(f"{sig:3} itens={sum(c.values()):3} materiais={POR_CURSO[sig][1]:3}/{len(man):3} · {dict(c.most_common())}")
print("\nFILA TOTAL POR MOTIVO:")
for k, v in FILA.most_common():
    print(f"   {k:34} {v:3}")
print(f"   {'soma':34} {sum(FILA.values()):3}")
