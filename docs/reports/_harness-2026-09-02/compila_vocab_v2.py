"""Fase 1c — TESTE REAL do vocabulario compilado por LLM (1 chamada por unidade), no IA.

Desenho: o LLM NAO inventa termos. Recebe os topicos do plano da unidade + titulos/headings dos
materiais da unidade (estrutura: computed_unit_slug da copia nu) e devolve, por topico, os termos
DESSES materiais que pertencem a ele. Pos-filtro: termo == label fora; termo em >1 topico fora
(exclusividade); termo sem token especifico fora.
Mede: (1) precisao dos termos vs sidecar manual (mesmo topico) OU presenca em titulo/heading de
material cujo gold e o topico; (2) cobertura do manual; (3) subunidade nos 93 com os termos do LLM
no lugar do manual (mesma regua do coheading.py). Grava o compilado em scratchpad/vocab_<SIG>.json.

    python compila_vocab.py IA          # gasta ~5 chamadas
"""
import collections
import copy
import csv
import json
import sys
from pathlib import Path
from typing import List

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))

from pydantic import BaseModel, Field

from src.builder.engine import _entry_markdown_text_for_file_map, _iter_content_taxonomy_topics
from src.builder.extraction.content_taxonomy import _extract_markdown_headings, _topic_support_tokens
from src.builder.routing.resolver_apply import _is_material, assemble_resolver_inputs
from src.builder.routing.thresholds import T
from src.builder.runtime.gemini_client import get_gemini_client, has_gemini_api_key
from src.builder.text.normalize import normalize_match_text
from src.builder.timeline.index import _score_entry_against_taxonomy_topic

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
COPY = ROOT / ".ablacao"
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
OUT_CATS = {"cronograma", "provas", "trabalhos", "fotos-de-prova"}
SIG = sys.argv[1] if len(sys.argv) > 1 else "IA"
nome = REPOS[SIG]
repo_o = GH / nome
repo = COPY / nome if (COPY / nome / "manifest.json").exists() else repo_o


class TopicoTermos(BaseModel):
    topico: str = Field(description="label do topico, exatamente como dado")
    termos: List[str] = Field(default_factory=list, description="termos/expressoes DOS MATERIAIS que pertencem a este topico")


class Vocab(BaseModel):
    topicos: List[TopicoTermos] = Field(default_factory=list)


SYSTEM = (
    "Voce recebe os TOPICOS de uma unidade do plano de ensino e os titulos e headings dos MATERIAIS "
    "dessa unidade. Tarefa: para cada topico, liste os termos e expressoes curtas (1-4 palavras) que "
    "APARECEM nos materiais e que pertencem a esse topico (nomes de algoritmos, tecnicas, siglas, "
    "conceitos). Inclua os termos dos TITULOS e as VARIANTES que aparecem no texto (sigla, ingles e "
    "portugues, singular e plural, ex.: 'clustering', 'cluster', 'agrupamento', 'EDA', 'analise "
    "exploratoria'). Regras: (1) so termos presentes no texto dado — nao invente; (2) cada termo em no "
    "maximo um topico; (3) ignore palavras genericas (introducao, exercicio, aula, exemplo, revisao) "
    "e o nome da disciplina; (4) se nenhum material cobre um topico, devolva lista vazia; (5) responda "
    "apenas o JSON do schema."
)

config = json.loads((Path.home() / ".gpt_tutor_config.json").read_text(encoding="utf-8"))
assert has_gemini_api_key(config), "sem chave gemini"
client = get_gemini_client(config)

m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
entries = [e for e in m["entries"] if _is_material(e) and str(e.get("category") or "") not in OUT_CATS]
tax = json.loads((repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
course_name = str(tax.get("course_name") or "")
generic = set((_iter_content_taxonomy_topics(tax) or [{}])[0].get("generic_tokens") or [])

compilado = {}   # label -> [termos]
chamadas = 0
for u in tax["units"]:
    labels = [str(t.get("label") or "") for t in (u.get("topics") or []) if t.get("label")]
    mats = [e for e in entries if str(e.get("computed_unit_slug") or "") == u["slug"]]
    if not labels or not mats:
        continue
    linhas = []
    for e in mats:
        md = _entry_markdown_text_for_file_map(repo_o, e) or ""
        heads = _extract_markdown_headings(md, limit=24)
        ml = e.get("moodle_label"); ml = ml.get("text", "") if isinstance(ml, dict) else str(ml or "")
        linhas.append(f"- TITULO: {e.get('title')} | LABEL MOODLE: {ml}\n  HEADINGS: " + " | ".join(h[:60] for h in heads[:24]))
    bundle = (f"DISCIPLINA: {course_name}\nUNIDADE: {u.get('title')}\nTOPICOS DO PLANO:\n" +
              "\n".join(f"  * {l}" for l in labels) + "\n\nMATERIAIS:\n" + "\n".join(linhas))
    try:
        res = client.summarize_bundle(bundle_text=bundle[:24000], schema=Vocab, system_instruction=SYSTEM)
        chamadas += 1
    except Exception as ex:
        print(f"[erro] {u['slug']}: {type(ex).__name__}: {str(ex)[:120]}")
        continue
    for tt in res.topicos:
        if tt.topico in labels:
            compilado.setdefault(tt.topico, []).extend([t.strip() for t in tt.termos if t.strip()])
print(f"chamadas: {chamadas} · topicos com termos: {sum(1 for v in compilado.values() if v)}/{len(compilado)}")

# ---- pos-filtro: exclusividade + termo != label + token especifico
label_norm = {l: normalize_match_text(l) for l in compilado}
onde = collections.defaultdict(set)
for l, ts in compilado.items():
    for t in ts:
        onde[normalize_match_text(t)].add(l)
filtrado = {}
for l, ts in compilado.items():
    keep = []
    for t in dict.fromkeys(ts):
        tn = normalize_match_text(t)
        if not tn or tn == label_norm[l] or len(onde[tn]) > 1:
            continue
        toks = {x for x in _topic_support_tokens(t) if x not in generic}
        if not toks:
            continue
        keep.append(t)
    filtrado[l] = keep
Path(f"vocab_{SIG}_v2.json").write_text(json.dumps(filtrado, ensure_ascii=False, indent=2), encoding="utf-8")
n_termos = sum(len(v) for v in filtrado.values())
print(f"termos apos filtro: {n_termos} (descartados por exclusividade/label/generico: {sum(len(v) for v in compilado.values()) - n_termos})")

# ---- precisao vs manual + presenca em material do gold
manual_path = repo_o / "course" / ".glossary_curation.json"
manual = {}
if manual_path.exists():
    raw = json.loads(manual_path.read_text(encoding="utf-8"))
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        syn = v.get("synonyms") if isinstance(v, dict) else v
        manual[normalize_match_text(k)] = {normalize_match_text(s) for s in (syn or [])}
gold_rows = [r for r in csv.DictReader(open(ROOT / "docs/reports" / f"subunit_gt_{SIG}.csv", encoding="utf-8-sig")) if r["scorable"] == "yes"] if (ROOT / "docs/reports" / f"subunit_gt_{SIG}.csv").exists() else []
by_id = {str(e["id"]): e for e in m["entries"]}
slug_of_label = {str(t.get("label")): str(t.get("slug")) for u in tax["units"] for t in (u.get("topics") or [])}
heads_por_topico = collections.defaultdict(str)
for r in gold_rows:
    e = by_id.get(r["entry_id"])
    if not e:
        continue
    md = _entry_markdown_text_for_file_map(repo_o, e) or ""
    heads_por_topico[r["gold_subunit"]] += " " + normalize_match_text(str(e.get("title") or "") + " " + " ".join(_extract_markdown_headings(md, limit=24)))
certos = total = 0; no_manual = 0; cobertura_hit = cobertura_n = 0
print("\nTERMOS (✓ = no manual do mesmo topico ou em titulo/heading de material com gold = topico):")
for l, ts in filtrado.items():
    ln = label_norm[l]; slug = slug_of_label.get(l, "")
    marks = []
    for t in ts:
        tn = normalize_match_text(t); total += 1
        ok_manual = tn in manual.get(ln, set())
        ok_mat = (" " + tn + " ") in (" " + heads_por_topico.get(slug, "") + " ")
        certos += (ok_manual or ok_mat); no_manual += ok_manual
        marks.append(("✓" if (ok_manual or ok_mat) else "✗") + t)
    print(f"  {l[:40]:40} {' · '.join(marks)[:150]}")
for ln, syns in manual.items():
    for s in syns:
        cobertura_n += 1
        cobertura_hit += any(normalize_match_text(t) == s for l, ts in filtrado.items() if label_norm[l] == ln for t in ts)
print(f"\nPRECISAO: {certos}/{total} = {certos / max(total, 1):.0%} (no manual: {no_manual}) · COBERTURA do manual: {cobertura_hit}/{cobertura_n}")

# ---- subunidade nos golds com os termos do LLM como aliases (taxonomia da copia nu)
if gold_rows:
    tx = copy.deepcopy(tax)
    for u in tx["units"]:
        for t in u.get("topics") or []:
            t["aliases"] = list(dict.fromkeys(list(t.get("aliases") or []) + filtrado.get(str(t.get("label")), [])))
    topics_llm = _iter_content_taxonomy_topics(tx); topics_nu = _iter_content_taxonomy_topics(tax)
    cc = repo_o / "code_curation.json"
    code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}

    def pred(signals, topics):
        sc = sorted(((t, _score_entry_against_taxonomy_topic(signals, t)) for t in topics), key=lambda x: -x[1])
        if not sc or sc[0][1] <= 0:
            return ""
        ws = sc[0][1]; rs = sc[1][1] if len(sc) > 1 else 0.0
        if len(sc) > 1 and (ws - rs == 0.0 or (ws - rs) / max(ws, 1e-6) < T.SUBUNIT_AMBIG_MARGIN):
            return ""
        return str(sc[0][0]["topic_slug"])
    ok_nu = ok_llm = n = 0
    for r in gold_rows:
        e = by_id.get(r["entry_id"])
        if not e:
            continue
        extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
        alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
        unit = str(e.get("computed_unit_slug") or "")
        _, sig, _ = assemble_resolver_inputs(repo_o, e, code_curation)
        n += 1
        ok_nu += pred(sig, [t for t in topics_nu if t["unit_slug"] == unit]) in alvo
        ok_llm += pred(sig, [t for t in topics_llm if t["unit_slug"] == unit]) in alvo
    print(f"SUBUNIDADE {SIG}: nu={ok_nu}/{n} · com vocab LLM={ok_llm}/{n} · manual (referencia)={'39/39' if SIG == 'IA' else '?'}")
