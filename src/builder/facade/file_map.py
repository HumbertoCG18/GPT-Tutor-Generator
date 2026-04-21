from __future__ import annotations

from functools import partial


def build_file_map_aliases(
    *,
    repo_artifacts_module,
    file_map_auto_map_entry_subtopic,
    file_map_auto_map_entry_unit,
    file_map_build_file_map_content_taxonomy_from_course,
    file_map_build_file_map_unit_index,
    file_map_build_file_map_unit_index_from_course,
    file_map_format_file_map_unit_cell,
    file_map_resolve_entry_manual_timeline_block,
    file_map_resolve_entry_manual_unit_slug,
    file_map_score_entry_against_unit,
    entry_signals_image_source_dirs,
    entry_signals_collect_entry_unit_signals,
    entry_signals_normalize_match_text,
    file_map_strip_outline_prefix,
    file_map_unit_generic_tokens,
    teaching_plan_normalize_unit_slug,
    collapse_ws,
    parse_units_from_teaching_plan,
    topic_text,
    parse_glossary_terms,
    timeline_unit_neutral_tokens,
    score_timeline_unit_phrase,
    glossary_md,
    collect_strong_heading_candidates,
    resolve_semantic_profile_fn,
    build_content_taxonomy_fn,
    iter_content_taxonomy_topics,
    score_entry_against_taxonomy_topic,
    topic_match_result_factory,
    unit_match_result_factory,
    normalize_document_profile_fn,
    exam_categories,
    exercise_categories,
):
    no_unit_categories = {"cronograma", "bibliografia", "referencias"}
    bundle_priority_score = partial(
        repo_artifacts_module.bundle_priority_score,
        normalize_document_profile_fn=normalize_document_profile_fn,
        exam_categories=exam_categories,
        exercise_categories=exercise_categories,
    )
    bundle_reason_labels = partial(
        repo_artifacts_module.bundle_reason_labels,
        normalize_document_profile_fn=normalize_document_profile_fn,
        exam_categories=exam_categories,
        exercise_categories=exercise_categories,
    )
    manifest_log_limit = 200
    entry_image_source_dirs = entry_signals_image_source_dirs
    entry_existing_reference_count = partial(
        repo_artifacts_module.entry_existing_reference_count,
        entry_image_source_dirs_fn=entry_image_source_dirs,
    )
    filter_live_manifest_entries = partial(
        repo_artifacts_module.filter_live_manifest_entries,
        entry_existing_reference_count_fn=entry_existing_reference_count,
    )
    bundle_seed_candidate = partial(
        repo_artifacts_module.bundle_seed_candidate,
        bundle_reason_labels_fn=bundle_reason_labels,
    )

    normalize_match_text = entry_signals_normalize_match_text
    strip_outline_prefix = file_map_strip_outline_prefix
    unit_generic_tokens = file_map_unit_generic_tokens
    normalize_unit_slug = teaching_plan_normalize_unit_slug

    build_file_map_unit_index = partial(
        file_map_build_file_map_unit_index,
        normalize_match_text=normalize_match_text,
        normalize_unit_slug=normalize_unit_slug,
        strip_outline_prefix=strip_outline_prefix,
        topic_text=topic_text,
        unit_generic_tokens=unit_generic_tokens,
    )

    collect_entry_unit_signals = entry_signals_collect_entry_unit_signals

    build_file_map_content_taxonomy_from_course = partial(
        file_map_build_file_map_content_taxonomy_from_course,
        parse_units_from_teaching_plan=parse_units_from_teaching_plan,
        topic_text=topic_text,
        glossary_md_fn=glossary_md,
        collect_strong_heading_candidates=collect_strong_heading_candidates,
        resolve_semantic_profile_fn=resolve_semantic_profile_fn,
        build_content_taxonomy_fn=build_content_taxonomy_fn,
    )

    auto_map_entry_subtopic = partial(
        file_map_auto_map_entry_subtopic,
        collect_entry_unit_signals=collect_entry_unit_signals,
        iter_content_taxonomy_topics=iter_content_taxonomy_topics,
        score_entry_against_taxonomy_topic=score_entry_against_taxonomy_topic,
        topic_match_result_factory=topic_match_result_factory,
    )

    score_entry_against_unit = partial(
        file_map_score_entry_against_unit,
        score_timeline_unit_phrase=score_timeline_unit_phrase,
        timeline_unit_neutral_tokens=timeline_unit_neutral_tokens,
    )

    def auto_map_entry_unit(entry, units, markdown_text, topic_index=None):
        return file_map_auto_map_entry_unit(
            entry,
            units,
            markdown_text,
            topic_index=topic_index,
            build_file_map_unit_index=build_file_map_unit_index,
            collect_entry_unit_signals=collect_entry_unit_signals,
            score_entry_against_unit=score_entry_against_unit,
            normalize_unit_slug=normalize_unit_slug,
            score_entry_against_taxonomy_topic=score_entry_against_taxonomy_topic,
            unit_match_result_factory=unit_match_result_factory,
        )

    format_file_map_unit_cell = file_map_format_file_map_unit_cell
    resolve_entry_manual_unit_slug = partial(
        file_map_resolve_entry_manual_unit_slug,
        normalize_unit_slug=normalize_unit_slug,
    )
    resolve_entry_manual_timeline_block = file_map_resolve_entry_manual_timeline_block

    build_file_map_unit_index_from_course = partial(
        file_map_build_file_map_unit_index_from_course,
        build_file_map_unit_index_fn=build_file_map_unit_index,
        parse_units_from_teaching_plan=parse_units_from_teaching_plan,
        glossary_md_fn=glossary_md,
        parse_glossary_terms_fn=parse_glossary_terms,
        normalize_match_text_fn=normalize_match_text,
        collapse_ws_fn=collapse_ws,
        unit_generic_tokens=unit_generic_tokens,
        timeline_unit_neutral_tokens=timeline_unit_neutral_tokens,
    )

    return {
        "_NO_UNIT_CATEGORIES": no_unit_categories,
        "_bundle_priority_score": bundle_priority_score,
        "_bundle_reason_labels": bundle_reason_labels,
        "_MANIFEST_LOG_LIMIT": manifest_log_limit,
        "_entry_image_source_dirs": entry_image_source_dirs,
        "_entry_existing_reference_count": entry_existing_reference_count,
        "_filter_live_manifest_entries": filter_live_manifest_entries,
        "_bundle_seed_candidate": bundle_seed_candidate,
        "_normalize_match_text": normalize_match_text,
        "_strip_outline_prefix": strip_outline_prefix,
        "_UNIT_GENERIC_TOKENS": unit_generic_tokens,
        "_normalize_unit_slug": normalize_unit_slug,
        "_build_file_map_unit_index": build_file_map_unit_index,
        "_collect_entry_unit_signals": collect_entry_unit_signals,
        "_build_file_map_content_taxonomy_from_course": build_file_map_content_taxonomy_from_course,
        "_auto_map_entry_subtopic": auto_map_entry_subtopic,
        "_score_entry_against_unit": score_entry_against_unit,
        "_auto_map_entry_unit": auto_map_entry_unit,
        "_format_file_map_unit_cell": format_file_map_unit_cell,
        "_resolve_entry_manual_unit_slug": resolve_entry_manual_unit_slug,
        "_resolve_entry_manual_timeline_block": resolve_entry_manual_timeline_block,
        "_build_file_map_unit_index_from_course": build_file_map_unit_index_from_course,
    }

