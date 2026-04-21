from __future__ import annotations

import json
import logging

from src.builder.artifacts import student_state as student_state_v2
from src.builder.ops.state_ops import (
    derive_active_unit_slug_from_state,
    ensure_unit_battery_directories,
)
from src.models.core import FileEntry
from src.utils.helpers import slugify, write_text

logger = logging.getLogger(__name__)


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
    progress_schema_md_fn,
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
            bibliography_md_fn(builder.course_meta, bib_entries, builder.subject_profile),
        )

    assignment_entries = [e for e in all_entries if e.category in assignment_categories]
    if assignment_entries:
        write_text(
            builder.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
            assignment_index_md_fn(builder.course_meta, assignment_entries),
        )

    code_entries = [e for e in all_entries if e.category in code_categories]
    if code_entries:
        write_text(builder.root_dir / "code" / "CODE_INDEX.md", code_index_md_fn(builder.course_meta, code_entries, builder.subject_profile))

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
    progress_path = builder.root_dir / "build" / "PROGRESS_SCHEMA.md"
    if not progress_path.exists():
        write_text(progress_path, progress_schema_md_fn())
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
