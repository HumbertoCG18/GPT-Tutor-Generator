"""Harness OFFLINE do eixo COBERTURA: recomputa `derive_coverage_units` por entry do gold
(`docs/reports/material_gt_<SIGLA>.csv`) lendo os repos como estao, SEM reprocessar (~15 s).

    python scripts/harness_cobertura.py            # regua de cobertura = a do eval_eixos (52/57 em 2026-08-27)
    python scripts/harness_cobertura.py base --detalhe   # por erro: topicos de cada unidade no texto e no card
    python scripts/harness_cobertura.py final      # experimento: fallback = computed_unit_slug FINAL (temporal)

Para testar uma REGRA: importe `rodar(modo, derive=minha_funcao)` — a funcao recebe os mesmos
argumentos de `derive_coverage_units` (entry, unit_index, texto, normalize, fallback_unit_slug,
topic_index, blocks). Foi assim que R2/R4/R5/R6/R7 foram medidas antes de tocar producao
(41 -> 52, 0 quebras); o modo `final` mediu 34/57 e matou a ideia "fallback = unidade temporal":
gold de UNIDADE = unidade do bloco temporal (onde mora), gold de COBERTURA = o que o conteudo cobre.
"""
import csv, json, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
from eval_entry_unit import COURSES, GITHUB_DIR
from src.builder.engine import (_build_file_map_unit_index_from_course, _iter_content_taxonomy_topics,
                                _entry_markdown_text_for_file_map, _auto_map_entry_unit)
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
from src.builder.routing.thresholds import T
from src.builder.routing import coverage_rules as CR
from src.builder.text.normalize import normalize_match_text
from src.models.core import SubjectStore
from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile
from src.builder.core.code_summarization import code_curation_signal_text

NORM = lambda t: normalize_match_text(t, keep="+-./")

def carregar(sigla, repo_name, store):
    repo = GITHUB_DIR / repo_name
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    profile = store.find_by_repo_root(repo); assert profile, sigla
    unit_index = _build_file_map_unit_index_from_course({**(man.get("course") or {}), "_repo_root": repo}, profile)
    topic_index = _iter_content_taxonomy_topics(load_internal_content_taxonomy(repo) or {})
    try: tag_profile = load_tag_profile(repo / "course")
    except Exception: tag_profile = None
    cc = json.loads((repo / "code_curation.json").read_text(encoding="utf-8")) if (repo / "code_curation.json").exists() else {}
    tl = repo / "course" / ".timeline_index.json"
    blocks = (json.loads(tl.read_text(encoding="utf-8")).get("blocks") or []) if tl.exists() else []
    return repo, man, unit_index, topic_index, tag_profile, (cc.get("entries") or {}), blocks

def texto_de(repo, entry, code_entries):
    md = _entry_markdown_text_for_file_map(repo, entry)
    rec = code_entries.get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md

def rodar(modo="base", detalhe=False, derive=None):
    derive = derive or CR.derive_coverage_units
    store = SubjectStore(); tot = ok = 0; erros = []
    for sigla, repo_name in COURSES.items():
        csvp = ROOT / "docs/reports" / f"material_gt_{sigla}.csv"
        if not csvp.exists(): continue
        repo, man, unit_index, topic_index, tag_profile, code_entries, blocks = carregar(sigla, repo_name, store)
        by_id = {str(e["id"]): e for e in man["entries"]}
        for row in csv.DictReader(csvp.open(encoding="utf-8-sig")):
            if row.get("scorable", "yes").strip().lower() != "yes": continue
            e = by_id.get(row["entry_id"]);
            if e is None: continue
            gold = {p.strip() for p in row["gold_units"].split("|") if p.strip()}
            texto = texto_de(repo, e, code_entries)
            if modo == "base":
                learned = build_learned_unit_boosts(tag_profile, e) if tag_profile else {}
                m = _auto_map_entry_unit(e, unit_index, texto, topic_index, learned_unit_boosts=learned)
                fb = m.slug if (not m.ambiguous and m.confidence >= T.UNIT_TAG) else ""
            else:
                fb = str(e.get("computed_unit_slug") or "")
            cov = derive(e, unit_index, texto, normalize=NORM, fallback_unit_slug=fb, topic_index=topic_index, blocks=blocks)
            pred = {c["unit_slug"] for c in cov} or ({fb} if fb else set()) or ({str(e.get("computed_unit_slug") or "")} - {""})
            tot += 1
            if pred == gold: ok += 1; continue
            erros.append((sigla, row["entry_id"], gold, pred, cov, e, texto, unit_index, topic_index))
    print(f"[{modo}] cobertura {ok}/{tot}")
    for sigla, eid, gold, pred, cov, e, texto, unit_index, topic_index in erros:
        sh = lambda s: "|".join(x.split("-")[1] for x in sorted(s))
        print(f"  [{sigla}] {eid[:44]:44} gold={sh(gold):14} pred={sh(pred):14} regras={[(c['unit_slug'].split('-')[1], c['rule']) for c in cov]}")
        if detalhe:
            tn = NORM(texto); cn = NORM(str(e.get("source_section") or ""))
            por = CR._topicos_por_unidade(topic_index, NORM)
            for u in unit_index:
                slug = u["slug"]; tops = por.get(slug, [])
                no_texto = [t for t in tops if t in tn]; no_card = [t for t in tops if CR._casa(t, cn)]
                tit = str(u.get("normalized_title") or "")
                print(f"        u{slug.split('-')[1]} titulo_no_texto={tit in tn!s:5} texto={len(no_texto):2}/{len(tops):2} {[t[:24] for t in no_texto][:4]} card={[t[:20] for t in no_card]}")
    return ok, tot, erros

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "base"
    rodar(modo, detalhe="--detalhe" in sys.argv)
