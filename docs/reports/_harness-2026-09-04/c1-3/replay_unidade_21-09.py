"""W-B1: replay em memoria da fase real de unidade; gold somente na avaliacao."""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
from functools import partial
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
EVIDENCE = DATA / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(ROOT))

from src.builder.artifacts import repo
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
from src.builder.core.code_summarization import load_code_curation
from src.builder.core.markdown_utils import strip_frontmatter_block
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy, _parse_glossary_terms
from src.builder.extraction.entry_signals import collect_entry_unit_signals, normalize_match_text
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _normalize_unit_slug, _topic_text
from src.builder.facade.glossary import build_glossary_aliases
from src.builder.routing import file_map as FM, resolver_apply as RA
from src.builder.text.stopwords import UNIT_GENERIC_TOKENS, TIMELINE_UNIT_NEUTRAL_TOKENS
from src.builder.timeline.index import (
    _iter_content_taxonomy_topics, _score_entry_against_taxonomy_topic,
    _score_timeline_unit_phrase, TopicMatchResult,
)
from src.utils.helpers import collapse_ws


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_index = partial(
    FM.build_file_map_unit_index, normalize_match_text=normalize_match_text,
    normalize_unit_slug=_normalize_unit_slug, strip_outline_prefix=FM.strip_outline_prefix,
    topic_text=_topic_text, unit_generic_tokens=UNIT_GENERIC_TOKENS,
)
score_unit = partial(FM.score_entry_against_unit,
                     score_timeline_unit_phrase=_score_timeline_unit_phrase,
                     timeline_unit_neutral_tokens=TIMELINE_UNIT_NEUTRAL_TOKENS)
auto_unit = partial(
    FM.auto_map_entry_unit, build_file_map_unit_index=build_index,
    collect_entry_unit_signals=collect_entry_unit_signals, score_entry_against_unit=score_unit,
    normalize_unit_slug=_normalize_unit_slug,
    score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
)
auto_sub = partial(
    FM.auto_map_entry_subtopic, collect_entry_unit_signals=collect_entry_unit_signals,
    iter_content_taxonomy_topics=_iter_content_taxonomy_topics,
    score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
    topic_match_result_factory=TopicMatchResult,
)
glossary = build_glossary_aliases(
    repo_artifacts_module=repo, course_meta_clamp_navigation_artifact=repo.clamp_navigation_artifact,
    collapse_ws=collapse_ws, strip_frontmatter_block=strip_frontmatter_block,
    parse_units_from_teaching_plan=_parse_units_from_teaching_plan, topic_text=_topic_text,
)
course_index = partial(
    FM.build_file_map_unit_index_from_course, build_file_map_unit_index_fn=build_index,
    parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
    glossary_md_fn=glossary["glossary_md"], parse_glossary_terms_fn=_parse_glossary_terms,
    normalize_match_text_fn=normalize_match_text, collapse_ws_fn=collapse_ws,
    unit_generic_tokens=UNIT_GENERIC_TOKENS, timeline_unit_neutral_tokens=TIMELINE_UNIT_NEUTRAL_TOKENS,
    course_terms_fn=glossary["course_terms"],
)


def replay(root):
    original = read(root / "manifest.json")["entries"]
    entries = copy.deepcopy(original)
    # Nao alimentar a decisao com a unidade final gravada, nem com seu conflito.
    for entry in entries:
        for field in ("computed_unit_slug", "unit_match_reasons", "unit_match_confidence", "unit_block_conflict"):
            entry.pop(field, None)
    profile = SimpleNamespace(**read(root / "_inputs_15-09.json")["profile_input"])
    taxonomy = load_internal_content_taxonomy(root)
    blocks = read(root / "course/.timeline_index.json")["blocks"]
    raw = {}

    def trace_unit(entry, units, text, topic_index=None, **kwargs):
        match = auto_unit(entry, units, text, topic_index=topic_index, **kwargs)
        raw[str(entry["id"])] = {"slug": match.slug, "confidence": match.confidence,
                                 "ambiguous": match.ambiguous, "reasons": list(match.reasons)}
        return match

    RA.apply_unit_subunit_fields(
        entries, blocks, {"_repo_root": root, "course_name": profile.name, "_content_taxonomy": taxonomy},
        profile, root, load_code_curation(root), auto_map_entry_unit_fn=trace_unit,
        auto_map_entry_subtopic_fn=auto_sub, build_file_map_unit_index_from_course_fn=course_index,
        iter_content_taxonomy_topics_fn=_iter_content_taxonomy_topics,
        entry_markdown_text_for_file_map_fn=_entry_markdown_text_for_file_map,
    )
    return {str(e["id"]): e for e in original}, {str(e["id"]): e for e in entries}, raw


def main():
    out = HERE / "replay_unidade_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    # Importar a regua local nao executa build nem main; paths de gold sao do worktree.
    compare = load("compare_wb1", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    total, courses, divergences, records = collections.Counter(), {}, [], []
    for sig, name in mede.NOMES.items():
        ref = DATA / ".frzero/pacote_fontes_15-09" / name
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, replayed, raw = replay(root)
        c = collections.Counter()
        for eid, entry in saved.items():
            pred = replayed[eid]
            same = str(entry.get("computed_unit_slug") or "") == str(pred.get("computed_unit_slug") or "")
            c["manifest_n"] += 1
            c["manifest_fiel"] += same
            c["scorer_reexecutado"] += eid in raw
            c["confianca_diverge"] += entry.get("unit_match_confidence") != pred.get("unit_match_confidence")
            record = {"curso": sig, "id": eid, "source_path": entry.get("source_path"),
                      "gravado": entry.get("computed_unit_slug", ""), "replay": pred.get("computed_unit_slug", ""),
                      "scorer": raw.get(eid), "reasons_gravado": entry.get("unit_match_reasons"),
                      "reasons_replay": pred.get("unit_match_reasons"),
                      "conflict_gravado": entry.get("unit_block_conflict"),
                      "conflict_replay": pred.get("unit_block_conflict")}
            records.append(record)
            if not same:
                divergences.append({**record, "local": "src/builder/routing/resolver_apply.py:461-525" if eid in raw
                                    else "src/builder/routing/resolver_apply.py:420-437"})
        ref_entries = {str(e["id"]): e for e in read(ref / "manifest.json")["entries"]}
        source_index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(EVIDENCE / f"herancas_{sig}_15-09.json")["entries"]}
        golds = mede.golds(sig)
        with (EVIDENCE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            eid = row["entry_id"]
            old = ref_entries.get(mapping.get(eid) or "")
            hits = source_index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, eid, "origem nao unica")
            entry = hits[0] if hits else None
            for axis, gold in zip(("bloco", "unidade"), golds[:2]):
                if row[axis] == "":
                    continue
                c[f"{axis}_n"] += 1
                if entry is None:
                    c[f"{axis}_ausente"] += 1
                    continue
                ix = 0 if axis == "bloco" else 1
                saved_pred = compare.predictions(root, entry)[ix]
                pred = compare.predictions(root, replayed[str(entry["id"])])[ix]
                truth = gold[eid]
                c[f"{axis}_gravado"] += saved_pred == truth if ix == 0 else saved_pred in truth
                c[f"{axis}_replay"] += pred == truth if ix == 0 else pred in truth
        courses[sig] = dict(c)
        total.update(c)
        print(sig, dict(c), flush=True)
    checks = {
        "bloco_213_237": total["bloco_replay"] == 213 and total["bloco_n"] == 237,
        "unidade_gravada_239_284": total["unidade_gravado"] == 239 and total["unidade_n"] == 284,
        "unidade_replay_239_284": total["unidade_replay"] == 239 and total["unidade_n"] == 284,
        "fidelidade_100_porcento": total["manifest_fiel"] == total["manifest_n"],
    }
    report = {"head": "ce02a8f47285c30c16f12b131bdf86c46dcba64e", "checks": checks,
              "total": dict(total), "courses": courses, "divergences": divergences, "entries": records,
              "scope": "Fase real apply_unit_subunit_fields importada. Blocos congelados; nao e replay do motor de bloco.",
              "inputs": ["manifest (identidade, categoria, sinais, tags, pinos, computed_block_id, temporal_block_id)",
                         "_inputs_15-09.json:profile_input.teaching_plan", "course/.content_taxonomy.json",
                         "course/.timeline_index.json:blocks (id, block_uuid, unit_slug, period_start, kind)",
                         "Markdown referenciado, code_curation.json, tag_profile e curadoria de glossario quando presentes"],
              "missing_in_manifest": "slug bruto pre-gate e ranking completo do scorer nao sao persistidos; conflito so preserva o vencedor nos casos discordantes. Snapshot do indice de unidade pre-decisao tambem nao e persistido.",
              "limitations": ["Nao mede regra candidata; nenhum build/rebuild ou LLM.",
                              "Vocabulário integral reconstruido por funcoes atuais de src; nao supor identidade de confiancas sem medir.",
                              "Fidelidade compara todas as entries, inclusive vazias e nao processadas; ausentes permanecem nos denominadores."]}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOTAL", dict(total))
    print("ASSERTS", checks)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())
    assert all(checks.values()), "Infidelidade localizada no JSON; nao usar para medir regra candidata."


if __name__ == "__main__":
    main()
