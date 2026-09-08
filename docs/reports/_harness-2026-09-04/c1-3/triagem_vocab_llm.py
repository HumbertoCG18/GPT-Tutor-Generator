"""TRIAGEM DA CHAMADA: quais unidades REALMENTE precisam do vocabulario por LLM?

O compilador da Fase 1b gasta 1 chamada por unidade COM MATERIAL, sem perguntar se aquela unidade precisa. O user
(08/09) quer o maximo deterministico e LLM so onde o arquivo nao permite concluir. A granularidade certa da pergunta
nao e o arquivo, e a UNIDADE: o vocabulario e um ativo do curso, e uma chamada serve todos os materiais da unidade.

Este experimento ABLA o `.glossary_curation.llm.json` UMA UNIDADE POR VEZ nos 2 cursos com gold de subunidade que ja
tem o arquivo (MF, CG). Para cada unidade mede:
  - delta      quanto a subunidade PIORA sem o vocabulario daquela unidade = valor real da chamada
  - sinal      indicador DETERMINISTICO, disponivel ANTES de chamar: fracao dos materiais da unidade que a 1a passada
               deixa sem decisao forte (vazio, ambiguo ou score < 1)
Se `sinal` prediz `delta`, existe regra de triagem: chamar so as unidades acima do corte.
0 chamadas de LLM. Uso: triagem_vocab_llm.py
"""
import collections
import csv as _csv
import functools
import json
import os
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/triagem"
CURSOS = {"MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (triagem_vocab_llm)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from src.builder import engine as eng  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402

IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")
sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)


def gold_de(sig):
    return {r["entry_id"]: ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
            for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}


def sub_por_unidade(root: Path, gs: dict):
    """{unit_slug: (certos, n)} da subunidade, no estado atual do repo."""
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    out = collections.defaultdict(lambda: [0, 0])
    for e in man:
        if e["id"] not in gs:
            continue
        u = str(e.get("computed_unit_slug") or "")
        out[u][1] += 1
        out[u][0] += str(e.get("computed_subunit_slug") or "") in gs[e["id"]]
    return out


print("VALOR REAL DE CADA CHAMADA (ablacao do vocabulario LLM, uma unidade por vez)")
print(f"{'':4} {'unidade':30} {'mat':>4} {'termos':>7} {'com':>5} {'sem':>5} {'delta':>6} {'sinal-fraco':>12}")
LINHAS = []
t0 = time.time()
DST.mkdir(parents=True, exist_ok=True)
for sig, repo in CURSOS.items():
    root = GH / repo
    gs = gold_de(sig)
    llm = json.loads((root / "course/.glossary_curation.llm.json").read_text(encoding="utf-8"))
    tax = load_internal_content_taxonomy(root)
    # chave do sidecar ("<code> <label>") -> unit_slug
    key2unit = {}
    por_unidade_tops = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade_tops[t["unit_slug"]].append(t)
        code = str(t.get("topic_code") or "").strip()   # o campo do iterador e topic_code, nao code
        for k in {f"{code} {t['topic_label']}".strip(), t["topic_label"]}:
            key2unit[N(k)] = t["unit_slug"]
    unidades = collections.defaultdict(list)
    for k in llm:
        if k.startswith("_"):
            continue
        u = key2unit.get(N(k))
        if u:
            unidades[u].append(k)
    base = sub_por_unidade(root, gs)
    # sinal deterministico: fracao de materiais da unidade sem decisao forte na 1a passada
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    fraco = collections.defaultdict(lambda: [0, 0])
    for eid in gs:
        e = man.get(eid)
        if not e:
            continue
        u = str(e.get("computed_unit_slug") or "")
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(e.get("id") or "")) or {}
        txt = f"{md}\n{code_curation_signal_text(rec) if rec else ''}"
        m = sub_fn(e, tax, txt, winning_unit_slug=u)
        sinais = eng._collect_entry_unit_signals(e, txt)
        sc = max([eng._score_entry_against_taxonomy_topic(sinais, tp) for tp in por_unidade_tops.get(u, [])] or [0])
        fraco[u][1] += 1
        fraco[u][0] += (not m.topic_slug) or bool(m.ambiguous) or sc < 1.0
    for u, keys in sorted(unidades.items(), key=lambda x: -len(x[1])):
        dst = DST / repo
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(root, dst, ignore=IGN)
        p = dst / "course/.glossary_curation.llm.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        ntermos = sum(len(d[k].get("synonyms") or []) for k in keys)
        for k in keys:
            d.pop(k, None)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        ra.reprocess(dst, [])
        dep = sub_por_unidade(dst, gs)
        shutil.rmtree(dst, ignore_errors=True)
        com = sum(v[0] for v in base.values())
        sem = sum(v[0] for v in dep.values())
        nm, nf = fraco[u][1], fraco[u][0]
        pct = (100 * nf / nm) if nm else 0
        LINHAS.append((sig, u, nm, ntermos, com, sem, sem - com, pct))
        print(f"{sig:4} {u[8:38]:30} {nm:4} {ntermos:7} {com:5} {sem:5} {sem - com:+6} {nf}/{nm} {pct:4.0f}%", flush=True)

print("\nRESUMO — se so chamassemos as unidades que rendem:")
uteis = [l for l in LINHAS if l[6] < 0]
inuteis = [l for l in LINHAS if l[6] == 0]
print(f"  unidades com vocabulario LLM: {len(LINHAS)}  ->  rendem {len(uteis)} · nao mudam nada {len(inuteis)}")
print(f"  chamadas economizaveis: {len(inuteis)}/{len(LINHAS)} ({100 * len(inuteis) / max(1, len(LINHAS)):.0f}%)")
print(f"  pontos que as uteis carregam: {-sum(l[6] for l in uteis)}")
print("\n  as INUTEIS (chamada desperdicada) e seu sinal deterministico:")
for l in sorted(inuteis, key=lambda x: x[7]):
    print(f"     {l[0]:4} {l[1][8:40]:32} mat={l[2]:3} sinal-fraco={l[7]:4.0f}%")
print("\n  as UTEIS:")
for l in sorted(uteis, key=lambda x: x[6]):
    print(f"     {l[0]:4} {l[1][8:40]:32} mat={l[2]:3} delta={l[6]:+3} sinal-fraco={l[7]:4.0f}%")
print(f"\n[fim] {time.time() - t0:.0f}s")
