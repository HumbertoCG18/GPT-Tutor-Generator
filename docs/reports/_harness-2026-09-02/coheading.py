"""Experimento CO-HEADING (Fase 1a): documento cujo titulo/1o heading e suportado pelo topico T
doa seus demais headings como aliases de T (exclusividade: heading que cai em >1 topico nao doa).
Mede subunidade nos 93 golds em 3 variantes, UNIDADE FIXA (curada) para isolar o vocabulario:
  nu        = taxonomia da copia .ablacao (sem sidecar manual)
  coheading = nu + aliases doados (leave-one-out: doacao do proprio doc nao vale para ele)
  manual    = taxonomia do original (controle; deve reproduzir ~93)
READ-ONLY. Sim fiel para entries fora da rota code_curation (as infieis sao listadas).
"""
import collections
import copy
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))

from src.builder.engine import _entry_markdown_text_for_file_map, _iter_content_taxonomy_topics
from src.builder.extraction.content_taxonomy import (
    _extract_markdown_headings, _select_supported_taxonomy_topic, _topic_support_tokens,
)
from src.builder.routing.resolver_apply import _is_material, assemble_resolver_inputs
from src.builder.routing.thresholds import T
from src.builder.text.normalize import normalize_match_text
from src.builder.timeline.index import _score_entry_against_taxonomy_topic

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
COPY = ROOT / ".ablacao"
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
FILLER = {"sumario", "resumo", "exercicios", "exercicio", "introducao", "conclusao", "referencias",
          "bibliografia", "exemplo", "exemplos", "revisao", "aula", "parte", "objetivos", "agenda",
          "conteudo", "definicao", "definicoes", "observacao", "observacoes", "importante", "atividade"}
OUT_CATS = {"cronograma", "provas", "trabalhos", "fotos-de-prova"}


def load_tax(path):
    return json.loads((path / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))


def pred(signals, topics, ambig):
    scored = sorted(((t, _score_entry_against_taxonomy_topic(signals, t)) for t in topics), key=lambda x: -x[1])
    if not scored or scored[0][1] <= 0:
        return ""
    ws = scored[0][1]; rs = scored[1][1] if len(scored) > 1 else 0.0
    if len(scored) > 1 and ws - rs == 0.0:
        return ""
    rel = (ws - rs) / max(ws, 1e-6)
    if len(scored) > 1 and (rel < ambig or rel < T.SUBUNIT_TAG):
        return ""
    return str(scored[0][0]["topic_slug"])


TOT = collections.Counter(); N = 0; infieis = []
for sig, nome in REPOS.items():
    repo = GH / nome
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entries = [e for e in m["entries"] if _is_material(e)]
    by_id = {str(e["id"]): e for e in entries}
    cc = repo / "code_curation.json"
    code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}
    tax_nu = load_tax(COPY / nome)
    tax_manual = load_tax(repo)
    generic = set((_iter_content_taxonomy_topics(tax_nu) or [{}])[0].get("generic_tokens") or [])
    course_toks = set(normalize_match_text(str(tax_nu.get("course_name") or "")).split())
    unit_topics = {u["slug"]: (u.get("topics") or []) for u in tax_nu["units"]}

    # ---- doacoes: heading_norm -> {topic_slug: {doc_ids}}
    doacoes = collections.defaultdict(lambda: collections.defaultdict(set))
    texto_de = {}
    n_docs_com_tese = 0
    for e in entries:
        if str(e.get("category") or "") in OUT_CATS:
            continue
        unit = str(e.get("computed_unit_slug") or "")
        if unit not in unit_topics:
            continue
        md = _entry_markdown_text_for_file_map(repo, e) or ""
        heads = _extract_markdown_headings(md, limit=24)
        ml = e.get("moodle_label"); ml = ml.get("text", "") if isinstance(ml, dict) else str(ml or "")
        candidatos_tese = [str(e.get("title") or ""), ml] + heads[:2]
        tese = None; tese_txt = ""
        for c in candidatos_tese:
            if not c.strip():
                continue
            t = _select_supported_taxonomy_topic(c, unit_topics[unit])
            if t is not None:
                tese, tese_txt = t, normalize_match_text(c); break
        if tese is None:
            continue
        n_docs_com_tese += 1
        for h in heads:
            hn = normalize_match_text(h)
            if not hn or hn == tese_txt:
                continue
            toks = {t for t in _topic_support_tokens(h) if t not in generic and t not in course_toks and t not in FILLER}
            if len(toks) < 2:
                continue
            if any(w in FILLER for w in hn.split()[:1]):
                continue
            doacoes[hn][str(tese["slug"])].add(str(e["id"]))
            texto_de[hn] = h
    exclusivas = {hn: next(iter(d.items())) for hn, d in doacoes.items() if len(d) == 1}
    n_multi = sum(1 for d in doacoes.values() if len(d) > 1)

    # ---- taxonomia co-heading (todas as doacoes) — LOO aplicado por doc na hora de pontuar
    def tax_com(exclude_doc):
        tx = copy.deepcopy(tax_nu)
        for u in tx["units"]:
            for t in u.get("topics") or []:
                al = list(t.get("aliases") or [])
                for hn, (slug, docs) in exclusivas.items():
                    if slug == t.get("slug") and (docs - {exclude_doc}):
                        al.append(texto_de[hn])
                t["aliases"] = list(dict.fromkeys(al))
        return tx

    ok = collections.Counter(); n = 0
    for r in csv.DictReader(open(ROOT / "docs/reports" / f"subunit_gt_{sig}.csv", encoding="utf-8-sig")):
        if r["scorable"] != "yes" or r["entry_id"] not in by_id:
            continue
        e = by_id[r["entry_id"]]
        extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
        alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
        unit = str(e.get("computed_unit_slug") or "")
        _, signals, _ = assemble_resolver_inputs(repo, e, code_curation)
        variantes = {
            "nu": tax_nu, "coheading": tax_com(str(e["id"])), "manual": tax_manual,
        }
        preds = {}
        for nome_v, tx in variantes.items():
            topics = [t for t in _iter_content_taxonomy_topics(tx) if t["unit_slug"] == unit]
            preds[nome_v] = pred(signals, topics, T.SUBUNIT_AMBIG_MARGIN)
        if preds["manual"] != str(e.get("computed_subunit_slug") or ""):
            infieis.append(f"{sig} {r['entry_id'][:40]}")
            continue
        n += 1
        for nome_v, p in preds.items():
            ok[nome_v] += p in alvo
    N += n
    for k in ok: TOT[k] += ok[k]
    print(f"{sig:4} fieis={n:2}  nu={ok['nu']:2}  coheading={ok['coheading']:2}  manual={ok['manual']:2}   "
          f"| docs com tese={n_docs_com_tese}  headings doados exclusivos={len(exclusivas)}  ambiguos(>1 topico)={n_multi}")
    amostra = sorted(exclusivas.items(), key=lambda x: x[0])[:8]
    for hn, (slug, docs) in amostra:
        print(f"      '{texto_de[hn][:45]}' -> {slug[:38]}  ({len(docs)} doc)")
print(f"\nTOTAL fieis {N}: nu={TOT['nu']}  coheading={TOT['coheading']}  manual={TOT['manual']}")
print(f"infieis (rota code_curation, excluidas): {len(infieis)} -> {', '.join(infieis[:12])}")
