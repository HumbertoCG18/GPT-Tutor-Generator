"""Mede o motor cru consumindo termos estruturados, sem depender de GLOSSARY.md."""
import importlib.util
import json
import os
import re
import sys
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MOTOR = ROOT / "docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py"
DEST = Path(os.environ.get("FLUXO_DEST") or ROOT / ".frzero").resolve()


def main() -> int:
    assert DEST.is_relative_to((ROOT / ".frzero").resolve())
    assert not DEST.exists(), f"destino experimental deve nascer vazio: {DEST}"
    sys.path.insert(0, str(ROOT))
    import src.builder.engine as engine
    from src.builder.facade.glossary import build_glossary_aliases

    def sem_teto(text: str, *, max_chars: int, label: str) -> str:
        assert label == "course/GLOSSARY.md"
        return (text or "").strip()

    glossary_integral = build_glossary_aliases(
        repo_artifacts_module=engine._repo_artifacts,
        course_meta_clamp_navigation_artifact=sem_teto,
        collapse_ws=engine._collapse_ws,
        strip_frontmatter_block=engine._strip_frontmatter_block,
        parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
        topic_text=engine._topic_text,
    )["glossary_md"]

    cache = {}
    stats = {}

    def termos_estruturados(course_meta, subject_profile, *, root_dir, manifest_entries):
        signature = None if manifest_entries is None else tuple(
            str(e.get("id") or e.get("entry_id") or e.get("base_markdown") or "")
            for e in manifest_entries
        )
        cache_key = (str(root_dir), signature)
        if cache_key in cache:
            return cache[cache_key]

        plan = getattr(subject_profile, "teaching_plan", "") or ""
        units = engine._parse_units_from_teaching_plan(plan)
        evidence = engine._glossary_aliases["_collect_glossary_evidence"](
            root_dir,
            manifest_entries=manifest_entries,
            unit_titles=[title for title, _topics in units],
        )
        curated = engine._repo_artifacts.load_glossary_curation(root_dir)
        entries = []
        for unit_title, topics in units:
            for topic in topics:
                term = engine._topic_text(topic)
                found = engine._find_glossary_evidence(term, unit_title, evidence)
                definition, seeded, not_confuse = engine._seed_glossary_fields(
                    term, unit_title, evidence=found,
                )
                merged = engine._repo_artifacts.merge_glossary_synonyms(
                    seeded,
                    curated.get(engine._repo_artifacts._glossary_curation_key(term), []),
                )
                synonyms = sorted(dict.fromkeys(
                    item.strip()
                    for item in re.split(r"[,;/|]", merged)
                    if item.strip() not in engine._content_taxonomy._GLOSSARY_EMPTY_MARKERS
                ))
                entries.append({
                    "term": engine._collapse_ws(term),
                    "unit_hint": engine._collapse_ws(unit_title),
                    "synonyms": synonyms,
                    "definition": engine._collapse_ws(definition),
                    "not_confuse": engine._collapse_ws(not_confuse),
                })

        full = glossary_integral(
            course_meta,
            subject_profile,
            root_dir=root_dir,
            manifest_entries=manifest_entries,
        )
        parsed = [
            {
                "term": item["term"],
                "unit_hint": item["unit_hint"],
                "synonyms": item["synonyms"],
                "definition": item["definition"],
            }
            for item in engine._parse_glossary_terms(full)
            if item.get("unit_hint") and item.get("term") != "[Termo]"
        ]
        direct = [
            {key: item[key] for key in ("term", "unit_hint", "synonyms", "definition")}
            for item in entries
        ]
        if direct != parsed:
            first = next(
                (
                    (index, left, right)
                    for index, (left, right) in enumerate(zip(direct, parsed), 1)
                    if left != right
                ),
                (None, None, None),
            )
            raise AssertionError(
                f"termos diretos divergem do glossario integral: {root_dir}; "
                f"quantidades={len(direct)}/{len(parsed)}; primeiro={first}"
            )

        compact = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
        if manifest_entries is not None:
            stats[str(root_dir)] = {
                "topics": len(entries),
                "glossary_chars": len(full),
                "structured_chars": len(compact),
            }
        cache[cache_key] = (entries, compact)
        return entries, compact

    def texto_direto(course_meta, subject_profile, *, root_dir=None, manifest_entries=None):
        return termos_estruturados(
            course_meta,
            subject_profile,
            root_dir=Path(root_dir),
            manifest_entries=manifest_entries,
        )[1]

    def taxonomia_direta(course_meta, subject_profile=None, manifest_entries=None):
        root_dir = Path(course_meta.get("_repo_root"))
        terms, compact = termos_estruturados(
            course_meta,
            subject_profile,
            root_dir=root_dir,
            manifest_entries=manifest_entries,
        )
        original_parser = engine._content_taxonomy._parse_glossary_terms
        engine._content_taxonomy._parse_glossary_terms = lambda _text: terms
        try:
            return engine._file_map_build_file_map_content_taxonomy_from_course(
                course_meta,
                subject_profile,
                manifest_entries,
                parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
                topic_text=engine._topic_text,
                glossary_md_fn=lambda *_args, **_kwargs: compact,
                collect_strong_heading_candidates=engine._collect_strong_heading_candidates,
                resolve_semantic_profile_fn=engine.resolve_semantic_profile,
                build_content_taxonomy_fn=engine._build_content_taxonomy,
            )
        finally:
            engine._content_taxonomy._parse_glossary_terms = original_parser

    def indice_unidades_direto(course_meta, subject_profile=None):
        root_dir = Path(course_meta.get("_repo_root"))
        terms, compact = termos_estruturados(
            course_meta,
            subject_profile,
            root_dir=root_dir,
            manifest_entries=None,
        )
        return engine._file_map_build_file_map_unit_index_from_course(
            course_meta,
            subject_profile,
            build_file_map_unit_index_fn=engine._build_file_map_unit_index,
            parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
            glossary_md_fn=lambda *_args, **_kwargs: compact,
            parse_glossary_terms_fn=lambda _text: terms,
            normalize_match_text_fn=engine._normalize_match_text,
            collapse_ws_fn=engine._collapse_ws,
            unit_generic_tokens=engine._FILE_MAP_UNIT_GENERIC_TOKENS,
            timeline_unit_neutral_tokens=engine._TIMELINE_UNIT_NEUTRAL_TOKENS,
        )

    original_write_tag_catalog = engine._write_tag_catalog

    def catalogo_direto(root_dir, subject_profile, manifest_entries, *, course_map_text, glossary_text):
        course_meta = {
            "course_name": getattr(subject_profile, "name", "") or Path(root_dir).name,
            "_repo_root": Path(root_dir),
        }
        compact = texto_direto(
            course_meta,
            subject_profile,
            root_dir=root_dir,
            manifest_entries=manifest_entries,
        )
        return original_write_tag_catalog(
            root_dir,
            subject_profile,
            manifest_entries,
            course_map_text=course_map_text,
            glossary_text=compact,
        )

    engine._build_file_map_content_taxonomy_from_course = taxonomia_direta
    engine._build_file_map_unit_index_from_course = indice_unidades_direto
    engine._write_tag_catalog = catalogo_direto

    spec = importlib.util.spec_from_file_location("motor_taxonomia_direta", MOTOR)
    motor = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(motor)
    motor.DEST = DEST
    selected = sys.argv[1].split(",") if len(sys.argv) > 1 else list(motor.NOMES)

    rc = motor.main([
        "--config", "regua",
        "--sem-curadoria-benchmark", "puro",
        "--cursos", ",".join(selected),
    ])
    (DEST / "_CONFIG_ATUAL.txt").write_text(
        "regua (veto=texto, SEM curadoria do benchmark=puro, braco=taxonomia-direta)\n"
        f"cursos: {','.join(selected)}\n",
        encoding="utf-8",
    )

    print("\n=== EQUIVALENCIA E TAMANHO ===")
    for sig in selected:
        name = motor.NOMES[sig]
        root = str(DEST / name)
        stat = stats[root]
        tax = json.loads((Path(root) / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
        topics = [topic for unit in tax.get("units", []) for topic in unit.get("topics", [])]
        zero = sum(not (topic.get("aliases") or []) for topic in topics)
        reduction = 100 * (1 - stat["structured_chars"] / stat["glossary_chars"])
        print(
            f"{sig}: equivalencia=OK topics={stat['topics']} aliases={len(topics) - zero}/{len(topics)} "
            f"glossary={stat['glossary_chars']} structured={stat['structured_chars']} reducao={reduction:.1f}%"
        )
    print(f"TENTATIVAS DE REDE BLOQUEADAS: {len(motor.TENTATIVAS)}")
    assert not motor.TENTATIVAS
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
