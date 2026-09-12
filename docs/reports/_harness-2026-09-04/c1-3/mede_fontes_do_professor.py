"""TETO DAS FONTES DO PROFESSOR: o vocabulario que identifica o subtopico certo existe no plano, no SARC ou no Moodle?

Pergunta do user (07/09): "o ideal e pegar as taxonomias a partir do plano de ensino, SARC e talvez do titulo dos
arquivos (ou label do Moodle), para que o motor puro tivesse mais precisao".

Para cada material com gold de subunidade, mede se o subtopico CERTO e nomeavel por cada fonte, usando o mesmo criterio
de nomeacao do motor (`resolver_apply._secao_nomeia_subtopico`: frase contida ou tokens especificos contidos, sem
genericos), e sempre restrito aos topicos da unidade do material:

  PLANO    o rotulo do topico (ou um alias que ja veio do plano) aparece no TEXTO do material
  SARC     o label da sessao do bloco do material nomeia o topico
  SECAO    a secao do Moodle nomeia o topico
  TITULO   titulo do material + label do Moodle nomeiam o topico
  HEADINGS os headings do markdown nomeiam o topico

Sem gold nenhum na conta: o gold so diz qual e o certo, para medir se a fonte o alcanca.
Uso: mede_fontes_do_professor.py
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
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _secao_nomeia_subtopico  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

H_RE = re.compile(r"^#{1,3}\s+(.+)$", re.M)
LIMPO = "--limpo" in sys.argv  # avalia SARC/SECAO/TITULO/HEADINGS contra a taxonomia SEM os aliases curados
# 12/09 tarde (astra, brief v2): `--limpo` so tira o sidecar MANUAL (`course/.glossary_curation.json`). Os sinonimos do
# sidecar do LLM (`course/.glossary_curation.llm.json`) ja estao FUNDIDOS na taxonomia e sobrevivem: medido, 501 dos 841
# aliases dos 6 cursos (60%) sao de origem LLM. Ou seja, o "teto das fontes cruas do professor" era medido com
# vocabulario de LLM dentro. `--cru` tira os dois sidecares, igual ao regime `sem_llm` do replay.
CRU = "--cru" in sys.argv
# `--sem-gemini` tira do TEXTO o que veio do Gemini: os blocos IMAGE_DESCRIPTION (74/227) e o resumo de codigo (33/227).
SEM_GEMINI = "--sem-gemini" in sys.argv


def nomeia(texto: str, tops: list) -> str:
    return _secao_nomeia_subtopico({"source_section": texto}, tops, MOTOR_GENERIC_STEMS)


def frase_no(texto_norm: str, frase: str) -> bool:
    n = N(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


FONTES = ["PLANO", "AL-CURADO", "AL-HEADING", "SARC", "SECAO", "TITULO", "HEADINGS"]
_COD = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+")


def _sem_cod(s: str) -> str:
    return _COD.sub("", str(s or ""))
TOT = collections.Counter()
POR_CURSO = {}
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade[t["unit_slug"]].append(t)
    curp = root / "course/.glossary_curation.json"
    curados = set()
    if curp.exists():
        for k, v in json.loads(curp.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                curados |= {N(s) for s in (v.get("synonyms") or [])}
    if CRU:  # o sidecar do LLM tambem sai (ver nota do CRU la em cima)
        llmp = root / "course/.glossary_curation.llm.json"
        if llmp.exists():
            for k, v in json.loads(llmp.read_text(encoding="utf-8")).items():
                if not k.startswith("_"):
                    curados |= {N(s) for s in (v.get("synonyms") or [])}
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    ses = {}
    for b in tl["blocks"]:
        lab = " ".join(str(s.get("label") or "") for s in (b.get("sessions") or []))
        ses[b["id"]] = lab
        ses[str(b.get("block_uuid") or "")] = lab
    lim = collections.defaultdict(list)
    for u, ts in por_unidade.items():
        for tp in ts:
            c2 = dict(tp)
            c2["aliases"] = [a for a in (tp.get("aliases") or []) if N(a) not in curados]
            lim[u].append(c2)
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    c = collections.Counter()
    for r in rows:
        e = man.get(r["entry_id"])
        gold = r["gold_subunit"]
        if not e or not gold:
            continue
        c["n"] += 1
        unit = str(e.get("computed_unit_slug") or "")
        tops = por_unidade.get(unit, [])
        tops_limpos = lim.get(unit, [])
        gt = next((t for t in tops if t["topic_slug"] == gold), None)
        if not gt:
            c["gold-fora-da-unidade"] += 1
            continue
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(e.get("id") or "")) or {}
        if SEM_GEMINI:
            from src.builder.extraction.entry_signals import texto_para_score
            md = texto_para_score(md)
            rec = {}
        txt = md + "\n" + (code_curation_signal_text(rec) if rec else "")
        label = gt.get("topic_label") or ""
        todos_al = list(gt.get("aliases") or [])
        # alias do PLANO = o proprio rotulo e o rotulo com o codigo ("1.3.4 Orientada a Microsservicos")
        plano_al = [label] + [a for a in todos_al if N(_sem_cod(a)) == N(label)]
        cur_al = [a for a in todos_al if N(a) in curados]
        outros_al = [a for a in todos_al if a not in plano_al and a not in cur_al]
        tn = N(txt)
        hit = {}
        hit["PLANO"] = any(f and frase_no(tn, f) for f in plano_al)
        hit["AL-CURADO"] = any(f and frase_no(tn, f) for f in cur_al)
        hit["AL-HEADING"] = any(f and frase_no(tn, f) for f in outros_al)
        bid = str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "")
        tops_ev = tops_limpos if LIMPO else tops
        hit["SARC"] = nomeia(ses.get(bid, ""), tops_ev) == gold
        hit["SECAO"] = nomeia(str(e.get("source_section") or ""), tops_ev) == gold
        hit["TITULO"] = nomeia(f"{e.get('title') or ''} {moodle_label_text(e) or ''}", tops_ev) == gold
        hit["HEADINGS"] = nomeia(" ".join(H_RE.findall(md)[:12]), tops_ev) == gold
        for f in FONTES:
            c[f] += hit[f]
        c["QUALQUER"] += any(hit.values())
        c["NENHUMA"] += not any(hit.values())
        c["SO-PLANO"] += hit["PLANO"]
        c["SEM-CURADO"] += hit["PLANO"] or hit["AL-HEADING"] or hit["SARC"] or hit["SECAO"] or hit["TITULO"] or hit["HEADINGS"]
        # 12/09 (astra): so as 5 fontes CRUAS do professor, sem coluna de alias (AL-HEADING hoje carrega o vocab LLM fundido no glossario)
        c["PROFESSOR"] += hit["PLANO"] or hit["SARC"] or hit["SECAO"] or hit["TITULO"] or hit["HEADINGS"]
        c["PLANO+SARC+MOODLE"] += hit["PLANO"] or hit["SARC"] or hit["SECAO"] or hit["TITULO"]
    POR_CURSO[sig] = c
    TOT.update(c)

MODO = ("[CRU: taxonomia sem os aliases dos sidecares manual E LLM]" if CRU
        else "[TAXONOMIA LIMPA: sem aliases curados do sidecar MANUAL; os do LLM sobrevivem]" if LIMPO
        else "[taxonomia como esta]")
if SEM_GEMINI:
    MODO += " [SEM GEMINI no texto: sem IMAGE_DESCRIPTION e sem code_curation]"
print(f"O SUBTOPICO CERTO E ALCANCAVEL POR CADA FONTE DO PROFESSOR? {MODO}")
cols = FONTES + ["PLANO+SARC+MOODLE", "SEM-CURADO", "PROFESSOR", "QUALQUER", "NENHUMA"]
print(f"{'':5} {'n':>4} " + " ".join(f"{f[:9]:>10}" for f in cols))
for sig, c in POR_CURSO.items():
    print(f"{sig:5} {c['n']:4} " + " ".join(f"{c[f]:>4} {100 * c[f] / max(1, c['n']):>4.0f}%" for f in cols))
print(f"{'TOT':5} {TOT['n']:4} " + " ".join(f"{TOT[f]:>4} {100 * TOT[f] / max(1, TOT['n']):>4.0f}%" for f in cols))
print(f"\ngold fora da unidade computada (nao contam acima): {TOT['gold-fora-da-unidade']}")
print("\nLEITURA: 'PLANO' e o que o motor ja tem hoje pelo texto. As colunas SARC/SECAO/TITULO/HEADINGS sao o que as")
print("fontes do professor acrescentariam. 'NENHUMA' e o piso: nenhuma fonte do professor nomeia o subtopico certo.")
