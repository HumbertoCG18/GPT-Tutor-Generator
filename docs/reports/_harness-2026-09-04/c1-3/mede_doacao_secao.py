"""DOACAO PELA SECAO DO MOODLE — a regra que a curadoria manual imitava, sem o gold.

O professor agrupa os materiais em secoes ("7 - Curvas Parametricas", "Microsservicos", "Threads"). Se a secao nomeia
um topico do plano, entao o vocabulario dos materiais daquela secao (titulo, label do Moodle, headings) e o lexico
concreto daquele topico: `bezier`, `hermite`, `casteljau` sao "Tipos de Curvas Parametricas". Isso e exatamente o que
o sidecar curado faz hoje, mas derivado do MOODLE em vez do gold.

Mede, com a taxonomia LIMPA (sem os aliases curados):
  A) quantas secoes nomeiam exatamente um topico, e quantos materiais moram nelas
  B) TETO da atribuicao direta: todo material da secao recebe o topico que a secao nomeia
  C) o vocabulario que seria doado
Uso: mede_doacao_secao.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _secao_nomeia_subtopico  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.builder.timeline.unit_matcher import _tokens  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

H_RE = re.compile(r"^#{1,3}\s+(.+)$", re.M)
TOT = collections.Counter()
print("A) SECOES QUE NOMEIAM UM TOPICO (taxonomia limpa) e B) TETO da atribuicao direta")
print(f"{'':5} {'secoes':>7} {'nomeiam':>8} {'mat.cobertos':>13} {'acerta':>12} {'motor hoje':>12}")
DOA = {}
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    curp = root / "course/.glossary_curation.json"
    curados = set()
    if curp.exists():
        for k, v in json.loads(curp.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                curados |= {N(s) for s in (v.get("synonyms") or [])}
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        c2 = dict(t)
        c2["aliases"] = [a for a in (t.get("aliases") or []) if N(a) not in curados]
        por_unidade[t["unit_slug"]].append(c2)
    # materiais por secao
    porsec = collections.defaultdict(list)
    for e in man.values():
        s = str(e.get("source_section") or "").strip()
        if s:
            porsec[s].append(e)
    gold = {r["entry_id"]: ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";"))))
            for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline=""))
            if r["scorable"] == "yes" and r["gold_subunit"]}
    c = collections.Counter()
    doa = collections.defaultdict(set)
    for sec, ents in porsec.items():
        c["sec"] += 1
        # unidade dominante da secao
        u = collections.Counter(str(x.get("computed_unit_slug") or "") for x in ents).most_common(1)[0][0]
        tops = por_unidade.get(u, [])
        alvo = _secao_nomeia_subtopico({"source_section": sec}, tops, MOTOR_GENERIC_STEMS)
        if not alvo:
            continue
        c["nomeia"] += 1
        for e in ents:
            if e["id"] in gold:
                c["cob"] += 1
                c["ok"] += alvo in gold[e["id"]]
            md = eng._entry_markdown_text_for_file_map(root, e) or ""
            txt = f"{e.get('title') or ''} {moodle_label_text(e) or ''} {' '.join(H_RE.findall(md)[:8])}"
            doa[(u, alvo)] |= _tokens(txt)
    # o que ja esta no topico sai da doacao
    for (u, alvo), v in list(doa.items()):
        tp = next((t for t in por_unidade.get(u, []) if t["topic_slug"] == alvo), None)
        base = _tokens(" ".join([tp.get("topic_label") or ""] + list(tp.get("aliases") or []))) if tp else set()
        outros = set()
        for t in por_unidade.get(u, []):
            if t["topic_slug"] != alvo:
                outros |= _tokens(" ".join([t.get("topic_label") or ""] + list(t.get("aliases") or [])))
        doa[(u, alvo)] = v - base - outros
    DOA[sig] = doa
    for eid, a in gold.items():
        c["mot"] += str(man[eid].get("computed_subunit_slug") or "") in a
    c["ngold"] = len(gold)
    TOT.update(c)
    print(f"{sig:5} {c['sec']:7} {c['nomeia']:8} {c['cob']:5}/{c['ngold']:<7} {c['ok']:5} {100 * c['ok'] / max(1, c['cob']):4.0f}% "
          f"{c['mot']:6} {100 * c['mot'] / max(1, c['ngold']):4.0f}%")
print(f"{'TOT':5} {TOT['sec']:7} {TOT['nomeia']:8} {TOT['cob']:5}/{TOT['ngold']:<7} {TOT['ok']:5} "
      f"{100 * TOT['ok'] / max(1, TOT['cob']):4.0f}% {TOT['mot']:6} {100 * TOT['mot'] / max(1, TOT['ngold']):4.0f}%")

print("\nC) VOCABULARIO DOADO (o que viraria sinonimo, por topico):")
for sig, doa in DOA.items():
    itens = [(t, sorted(v)[:8]) for (u, t), v in doa.items() if v]
    print(f"\n  {sig} ({len(itens)} topicos recebem doacao):")
    for t, v in itens[:5]:
        print(f"     {t[:38]:38} <- {v}")
