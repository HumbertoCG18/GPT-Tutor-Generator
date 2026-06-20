from __future__ import annotations

import json
import logging

from src.builder.artifacts import student_state as student_state_v2
from src.builder.ops.state_ops import (
    derive_active_unit_slug_from_state,
    ensure_unit_battery_directories,
)
from src.builder.core.reference_navigation import build_unit_topic_reference_index
from src.builder.core.reference_summary import load_reference_curation
from src.builder.routing.thresholds import METHOD_CAPS, confidence_band
from src.models.core import FileEntry
from src.utils.helpers import slugify, write_text

logger = logging.getLogger(__name__)


def _resolve_gemini_client(builder):
    """Resolve o client Gemini real (mesmo factory de summarize_all_code_entries).

    Le a config persistida (~/.gpt_tutor_config.json, igual ao AppConfig) e usa
    `get_gemini_client(config)`, que retorna None se nao houver gemini_api_key.
    Qualquer falha (sem extra google-genai, sem chave, IO) -> None: o caminho
    residual degrada para no-op e a build segue normal.
    """
    try:
        import json as _json
        from pathlib import Path as _Path
        from src.builder.runtime.gemini_client import get_gemini_client

        cfg_path = _Path.home() / ".gpt_tutor_config.json"
        if not cfg_path.exists():
            return None
        config = _json.loads(cfg_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            return None
        return get_gemini_client(config)
    except Exception:
        return None


def run_material_residual(builder, live_manifest_entries):
    """Camada 2: residuo Gemini p/ materiais sem bloco. OPT-IN EXPLICITO.

    So roda quando `builder.options['enable_material_residual']` for True E houver
    client Gemini. DEFAULT OFF: operacoes leves (unprocess/reject) chamam
    regenerate_pedagogical_files na UI thread; resolver/chamar o client aqui
    faria ate 20 chamadas de rede sincronas (summarize_bundle, max_retries=5),
    travando o app. A opcao deve ser habilitada apenas em contexto com background
    thread (mesmo padrao do code summarization em ui/codes_panel.py).

    Retorna `live_manifest_entries` (mutado in-place quando roda).
    """
    options = getattr(builder, "options", {}) or {}
    if not bool(options.get("enable_material_residual", False)):
        return live_manifest_entries

    gemini_client = _resolve_gemini_client(builder)
    if gemini_client is None:
        return live_manifest_entries

    from src.builder.artifacts.cronograma_health import _entry_block_id
    from src.builder.core.summary_core import summarize_residual_materials
    from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map

    from pydantic import BaseModel as _BaseModel, Field as _Field

    class _KeywordsSchema(_BaseModel):
        keywords: list[str] = _Field(
            default_factory=list,
            description="3-8 palavras-chave tecnicas do material.",
        )

    def _extract_concepts(text: str) -> list:
        # Adapter sobre GeminiClient.summarize_bundle. summarize_bundle exige
        # um schema pydantic e retorna a instancia parseada (resp.parsed),
        # NAO um objeto com .text. Em caso de erro, retorna [] (degrada).
        try:
            res = gemini_client.summarize_bundle(
                bundle_text=text[:6000],
                schema=_KeywordsSchema,
                system_instruction=(
                    "Liste 3-8 palavras-chave tecnicas do material academico. "
                    "Responda apenas o JSON conforme schema."
                ),
            )
            kws = getattr(res, "keywords", None) or []
            return [str(w).strip() for w in kws if str(w).strip()]
        except Exception:
            return []

    _blocks = builder._load_timeline_blocks()
    orphans = []
    for e in live_manifest_entries:
        # passa _blocks p/ validar id manual stale igual a health/dashboard (fonte unica)
        if _entry_block_id(e, _blocks):
            continue
        txt = _entry_markdown_text_for_file_map(builder.root_dir, e) or str(e.get("title") or "")
        orphans.append({"id": e.get("id"), "_text": txt})
    if orphans and _blocks:
        resolved = summarize_residual_materials(
            builder.root_dir, orphans, _blocks, _extract_concepts, cap=20,
        )
        by_id = {e.get("id"): e for e in live_manifest_entries}
        for eid, rec in resolved.items():
            bid = rec.get("primary_block_id")
            if bid and by_id.get(eid) is not None:
                tags = [t for t in (by_id[eid].get("auto_tags") or []) if not str(t).startswith("bloco:")]
                tags.append(f"bloco:{bid}")
                by_id[eid]["auto_tags"] = tags
    return live_manifest_entries


def attach_block_summary_fields(entries: list, code_curation: dict, blocks: list = None) -> list:
    """Sincroniza campos do code_curation (summary.*) com o entry dict:
    match_rationale -> computed_block_rationale,
    block_match_method -> computed_block_method,
    block_match_confidence -> computed_block_match_confidence.
    Sem valor na curation, remove o campo — evita dado stale após
    prune/reatribuição."""
    curation_entries = (code_curation or {}).get("entries", {})
    for e in entries:
        rec = curation_entries.get(str(e.get("id") or "")) or {}
        summary = rec.get("summary") or {}

        rationale = str(summary.get("match_rationale") or "").strip()
        if rationale:
            e["computed_block_rationale"] = rationale
        else:
            e.pop("computed_block_rationale", None)

        method = str(summary.get("block_match_method") or "").strip()
        if method:
            # Caminho de CÓDIGO vence: roda DEPOIS de resolve_unit_block_tags
            # no regenerate_pedagogical_files, então consensus/llm_only
            # sobrescreve o method do funil (P2.3) — comportamento intencional.
            e["computed_block_method"] = method
        elif str(e.get("computed_block_method") or "") not in METHOD_CAPS:
            # Sem method na curation: só remove se o valor existente NÃO é do
            # funil (METHOD_CAPS = manual/review_rule/card/card+scorer/
            # scorer_only, recém-gravado por resolve_unit_block_tags nesta
            # mesma regeneração). Pop incondicional apagaria o method do funil
            # de toda entry não-código; o pop continua valendo para dado de
            # código stale (prune/reatribuição), que era o propósito original.
            e.pop("computed_block_method", None)

        conf = summary.get("block_match_confidence")
        if conf is not None:
            try:
                e["computed_block_match_confidence"] = float(conf)
            except (TypeError, ValueError):
                e.pop("computed_block_match_confidence", None)
        else:
            e.pop("computed_block_match_confidence", None)

        # D1: consenso band-gated para CÓDIGO. computed_block_id é a fonte única
        # do bloco. O funil decide (card-aware); o Gemini só desempata onde o
        # funil é honestamente fraco — SEM card E band "baixa". Card e funil-forte
        # nunca são sobrescritos (preserva o gabarito autoritativo, erro 0/22).
        if str(e.get("file_type") or "") in ("code", "zip"):
            gemini_primary = str(summary.get("primary_block_id") or "")
            if gemini_primary and blocks:
                from src.builder.timeline.block_identity import _POSITIONAL_RE as _POS_RE
                from src.builder.timeline.card_block import resolve_block_ref as _rbr
                if _POS_RE.match(gemini_primary):
                    _r = _rbr(gemini_primary, blocks)
                    if _r:
                        gemini_primary = _r
            if (
                gemini_primary
                and not str(e.get("source_section") or "").strip()
                and str(e.get("computed_block_band") or "") == "baixa"
            ):
                e["computed_block_id"] = gemini_primary
                e["computed_block_method"] = method or "llm_only"
                _gem_conf = summary.get("block_match_confidence")
                if _gem_conf is not None:
                    try:
                        e["computed_block_confidence"] = float(_gem_conf)
                        e["computed_block_band"] = confidence_band(float(_gem_conf))
                    except (TypeError, ValueError):
                        pass

    return entries


def regenerate_pedagogical_files(
    builder,
    manifest: dict,
    *,
    filter_live_manifest_entries_fn,
    build_file_map_content_taxonomy_from_course_fn,
    write_internal_content_taxonomy_fn,
    build_file_map_timeline_context_from_course_fn,
    persist_enriched_timeline_index_fn,
    empty_timeline_index_fn,
    build_assessment_context_from_course_fn,
    write_internal_assessment_context_fn,
    generate_claude_project_instructions_fn,
    generate_gpt_instructions_fn,
    generate_gemini_instructions_fn,
    tutor_policy_md_fn,
    pedagogy_md_fn,
    modes_md_fn,
    output_templates_md_fn,
    root_readme_fn,
    generated_repo_gitignore_text_fn,
    course_map_md_fn,
    glossary_md_fn,
    write_tag_catalog_fn,
    refresh_manifest_auto_tags_fn,
    resolve_unit_block_tags_fn,
    syllabus_md_fn,
    exam_index_md_fn,
    exercise_index_md_fn,
    bibliography_md_fn,
    assignment_index_md_fn,
    code_index_md_fn,
    whiteboard_index_md_fn,
    file_map_md_fn,
    student_profile_md_fn,
    student_state_md_fn,
    parse_units_from_teaching_plan_fn,
    topic_text_fn,
    inject_executive_summary_fn,
    exam_categories,
    exercise_categories,
    assignment_categories,
    code_categories,
    whiteboard_categories,
) -> None:
    stale_files = [
        builder.root_dir / "system" / "PDF_CURATION_GUIDE.md",
        builder.root_dir / "system" / "BACKEND_ARCHITECTURE.md",
        builder.root_dir / "system" / "BACKEND_POLICY.yaml",
        builder.root_dir / "student" / "PROGRESS_SCHEMA.md",
        builder.root_dir / "build" / "PROGRESS_SCHEMA.md",
    ]
    for stale in stale_files:
        if stale.exists():
            try:
                stale.unlink()
                logger.info("Removido arquivo obsoleto: %s", stale)
            except Exception as exc:
                logger.warning("Falha ao remover %s: %s", stale, exc)

    live_manifest_entries = filter_live_manifest_entries_fn(builder.root_dir, manifest.get("entries", []))
    manifest["entries"] = live_manifest_entries
    runtime_course_meta = {**builder.course_meta, "_repo_root": builder.root_dir}

    content_taxonomy = build_file_map_content_taxonomy_from_course_fn(
        runtime_course_meta,
        builder.subject_profile,
        live_manifest_entries,
    )
    runtime_course_meta["_content_taxonomy"] = content_taxonomy
    write_internal_content_taxonomy_fn(builder.root_dir, content_taxonomy)

    timeline_context = build_file_map_timeline_context_from_course_fn(
        runtime_course_meta,
        builder.subject_profile,
        content_taxonomy=content_taxonomy,
    )
    runtime_course_meta["_timeline_context"] = timeline_context
    enriched_timeline_index = persist_enriched_timeline_index_fn(
        timeline_context.get("timeline_index", empty_timeline_index_fn()),
    )
    write_text(
        builder.root_dir / "course" / ".timeline_index.json",
        json.dumps(enriched_timeline_index, indent=2, ensure_ascii=False),
    )

    assessment_context = build_assessment_context_from_course_fn(
        runtime_course_meta,
        builder.subject_profile,
        timeline_context=timeline_context,
    )
    runtime_course_meta["_assessment_context"] = assessment_context
    write_internal_assessment_context_fn(builder.root_dir, assessment_context)

    common_flags = dict(
        has_assignments=any((e.get("category") in assignment_categories) for e in live_manifest_entries),
        has_code=any((e.get("category") in code_categories) for e in live_manifest_entries),
        has_whiteboard=any((e.get("category") in whiteboard_categories) for e in live_manifest_entries),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_CLAUDE_PROJETO.md",
        generate_claude_project_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_GPT_PROJETO.md",
        generate_gpt_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_GEMINI_PROJETO.md",
        generate_gemini_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
    write_text(builder.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md_fn(builder.course_meta, builder.subject_profile))
    write_text(builder.root_dir / "system" / "PEDAGOGY.md", pedagogy_md_fn())
    write_text(builder.root_dir / "system" / "MODES.md", modes_md_fn(builder.course_meta, builder.subject_profile))
    write_text(builder.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md_fn(builder.course_meta, builder.subject_profile))
    write_text(builder.root_dir / "README.md", root_readme_fn(builder.course_meta))
    write_text(builder.root_dir / ".gitignore", generated_repo_gitignore_text_fn())

    # Approach C: refs mapeadas viram linhas de apoio no COURSE_MAP.
    # Lê manifest.json fresco (mesma fonte que gerou a curation) para alinhar ids.
    try:
        _manifest_entries = json.loads(
            (builder.root_dir / "manifest.json").read_text(encoding="utf-8")
        ).get("entries", [])
        runtime_course_meta["_reference_nav_index"] = build_unit_topic_reference_index(
            _manifest_entries, load_reference_curation(builder.root_dir)
        )
    except Exception as exc:
        logger.warning("Approach C: índice de referência não construído: %s", exc)
        runtime_course_meta["_reference_nav_index"] = {"by_unit": {}, "by_topic": {}}

    course_map_text = course_map_md_fn(runtime_course_meta, builder.subject_profile)
    write_text(builder.root_dir / "course" / "COURSE_MAP.md", course_map_text)

    glossary_text = glossary_md_fn(
        builder.course_meta,
        builder.subject_profile,
        root_dir=builder.root_dir,
        manifest_entries=live_manifest_entries,
    )
    write_text(builder.root_dir / "course" / "GLOSSARY.md", glossary_text)

    tag_catalog = write_tag_catalog_fn(
        builder.root_dir,
        builder.subject_profile,
        live_manifest_entries,
        course_map_text=course_map_text,
        glossary_text=glossary_text,
    )
    live_manifest_entries = refresh_manifest_auto_tags_fn(builder.root_dir, live_manifest_entries, tag_catalog)

    live_manifest_entries = resolve_unit_block_tags_fn(
        live_manifest_entries,
        runtime_course_meta,
        builder.subject_profile,
    )

    # Camada 2: residuo via Gemini (opt-in EXPLICITO). Ver run_material_residual.
    live_manifest_entries = run_material_residual(builder, live_manifest_entries)

    _code_curation = builder._load_code_curation()
    live_manifest_entries = attach_block_summary_fields(live_manifest_entries, _code_curation)
    if bool(builder.options.get("use_concept_resolver", False)):
        from src.builder.routing.resolver_apply import apply_concept_resolver
        live_manifest_entries = apply_concept_resolver(
            live_manifest_entries,
            enriched_timeline_index.get("blocks") or [],
            content_taxonomy.get("units") or [],
            _code_curation,
            builder.root_dir,
        )

    manifest["entries"] = live_manifest_entries

    try:
        all_entries = [FileEntry.from_dict(e) for e in live_manifest_entries]
    except Exception:
        all_entries = []

    if builder.subject_profile and builder.subject_profile.syllabus:
        write_text(builder.root_dir / "course" / "SYLLABUS.md", syllabus_md_fn(builder.subject_profile))

    exam_entries = [e for e in all_entries if e.category in exam_categories]
    if exam_entries:
        write_text(builder.root_dir / "exams" / "EXAM_INDEX.md", exam_index_md_fn(builder.course_meta, exam_entries))

    exercise_entries = [e for e in all_entries if e.category in exercise_categories]
    if exercise_entries:
        write_text(
            builder.root_dir / "exercises" / "EXERCISE_INDEX.md",
            exercise_index_md_fn(builder.course_meta, exercise_entries),
        )

    bib_entries = [e for e in all_entries if e.category == "bibliografia"]
    if bib_entries or getattr(builder.subject_profile, "teaching_plan", ""):
        write_text(
            builder.root_dir / "content" / "BIBLIOGRAPHY.md",
            bibliography_md_fn(
                builder.course_meta, bib_entries, builder.subject_profile,
                reference_curation=load_reference_curation(builder.root_dir),
            ),
        )

    assignment_entries = [e for e in all_entries if e.category in assignment_categories]
    if assignment_entries:
        write_text(
            builder.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
            assignment_index_md_fn(builder.course_meta, assignment_entries),
        )

    code_entries = [e for e in all_entries if e.category in code_categories]
    if code_entries:
        _code_curation = builder._load_code_curation()
        _timeline_blocks = builder._load_timeline_blocks()
        write_text(
            builder.root_dir / "code" / "CODE_INDEX.md",
            code_index_md_fn(
                builder.course_meta,
                code_entries,
                builder.subject_profile,
                code_curation=_code_curation,
                timeline_blocks=_timeline_blocks,
            ),
        )
        if _timeline_blocks:
            from src.builder.artifacts.repo import cronograma_detalhado_md as _cronograma_detalhado_md
            write_text(
                builder.root_dir / "course" / "CRONOGRAMA_DETALHADO.md",
                _cronograma_detalhado_md(
                    builder.course_meta,
                    code_entries,
                    _code_curation,
                    _timeline_blocks,
                    builder.subject_profile,
                ),
            )

    from src.builder.artifacts.repo import code_health_md as _code_health_md
    write_text(
        builder.root_dir / "course" / "CODE_HEALTH.md",
        _code_health_md(
            builder.course_meta,
            all_entries,
            code_curation=builder._load_code_curation(),
            timeline_blocks=builder._load_timeline_blocks(),
            glossary_terms=builder._load_glossary_terms() if hasattr(builder, "_load_glossary_terms") else None,
        ),
    )

    from src.builder.artifacts.temporal_context import temporal_context_md as _temporal_context_md
    write_text(
        builder.root_dir / "setup" / "CONTEXTO_TEMPORAL.md",
        _temporal_context_md(builder.course_meta, builder._load_timeline_blocks()),
    )

    from src.builder.artifacts.cronograma_health import cronograma_health_md as _cronograma_health_md
    write_text(
        builder.root_dir / "course" / "CRONOGRAMA_HEALTH.md",
        _cronograma_health_md(
            builder.course_meta,
            live_manifest_entries,
            builder._load_timeline_blocks(),
        ),
    )

    wb_entries = [e for e in all_entries if e.category in whiteboard_categories]
    if wb_entries:
        write_text(builder.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md", whiteboard_index_md_fn(builder.course_meta, wb_entries))

    write_text(
        builder.root_dir / "course" / "FILE_MAP.md",
        file_map_md_fn(runtime_course_meta, live_manifest_entries, builder.subject_profile),
    )

    if builder.student_profile:
        write_text(builder.root_dir / "student" / "STUDENT_PROFILE.md", student_profile_md_fn(builder.student_profile))
    state_path = builder.root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        write_text(state_path, student_state_md_fn(builder.course_meta, builder.student_profile))
    ensure_unit_battery_directories(
        builder.root_dir,
        builder.subject_profile,
        parse_units_from_teaching_plan_fn=parse_units_from_teaching_plan_fn,
        slugify_fn=slugify,
    )

    active_unit = derive_active_unit_slug_from_state(builder.root_dir)
    if active_unit:
        teaching_plan = getattr(builder.subject_profile, "teaching_plan", "") or ""
        parsed_units = parse_units_from_teaching_plan_fn(teaching_plan)
        course_topics_by_unit = {
            slugify(title): [(slugify(topic_text_fn(t)), topic_text_fn(t)) for t in topics]
            for title, topics in parsed_units
        }
        topics = course_topics_by_unit.get(active_unit, [])
        if topics:
            try:
                student_state_v2.refresh_active_unit_progress(
                    root_dir=builder.root_dir,
                    active_unit_slug=active_unit,
                    course_map_topics=topics,
                )
            except Exception as exc:
                logger.warning("refresh_active_unit_progress falhou: %s", exc)

    builder._resolve_content_images()
    builder._inject_all_image_descriptions()
    content_dir = builder.root_dir / "content"
    if content_dir.exists():
        for md in content_dir.rglob("*.md"):
            if md.name.endswith("_INDEX.md"):
                continue
            if md.name in {"BIBLIOGRAPHY.md", "FILE_MAP.md", "COURSE_MAP.md"}:
                continue
            try:
                inject_executive_summary_fn(md)
            except Exception as exc:
                logger.warning("Falha ao atualizar sumário executivo de %s: %s", md, exc)
