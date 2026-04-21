from __future__ import annotations

from functools import partial


def build_navigation_template_aliases(
    *,
    repo_artifacts_module,
    navigation_low_token_course_map_md,
    navigation_low_token_file_map_md,
    navigation_budgeted_file_map_md,
    navigation_low_token_course_map_md_v2,
    navigation_course_map_md,
    navigation_file_map_md,
    json_str_fn,
    safe_rel_fn,
    ensure_dir_fn,
    write_text_fn,
    logger,
    clamp_navigation_artifact,
    build_file_map_timeline_context_from_course,
    aggregate_unit_periods_from_blocks,
    normalize_unit_slug,
    parse_units_from_teaching_plan,
    topic_text,
    topic_depth,
    build_assessment_context_from_course,
    assessment_conflict_section_lines,
    filter_live_manifest_entries,
    build_file_map_content_taxonomy_from_course,
    build_file_map_unit_index_from_course,
    iter_content_taxonomy_topics,
    merge_manual_and_auto_tags,
    resolve_entry_manual_timeline_block,
    entry_markdown_text_for_file_map,
    auto_map_entry_subtopic,
    resolve_entry_manual_unit_slug,
    unit_match_result_factory,
    derive_unit_from_topic_match,
    auto_map_entry_unit,
    select_probable_period_for_entry,
    file_map_markdown_cell,
    entry_markdown_path_for_file_map,
    get_entry_sections,
    infer_unit_confidence,
    entry_usage_hint,
    entry_priority_label,
    collapse_ws,
):
    root_readme = repo_artifacts_module.root_readme
    wrap_frontmatter = partial(repo_artifacts_module.wrap_frontmatter, json_str_fn=json_str_fn)
    rows_to_markdown_table = repo_artifacts_module.rows_to_markdown_table
    manual_pdf_review_template = partial(repo_artifacts_module.manual_pdf_review_template, json_str_fn=json_str_fn)
    manual_image_review_template = partial(repo_artifacts_module.manual_image_review_template, safe_rel_fn=safe_rel_fn)
    manual_url_review_template = partial(repo_artifacts_module.manual_url_review_template, json_str_fn=json_str_fn)
    migrate_legacy_url_manual_reviews = partial(
        repo_artifacts_module.migrate_legacy_url_manual_reviews,
        ensure_dir_fn=ensure_dir_fn,
        safe_rel_fn=safe_rel_fn,
        write_text_fn=write_text_fn,
        logger=logger,
    )
    pdf_curation_guide = repo_artifacts_module.pdf_curation_guide
    backend_architecture_md = repo_artifacts_module.backend_architecture_md
    backend_policy_yaml = partial(repo_artifacts_module.backend_policy_yaml, json_str_fn=json_str_fn)

    low_token_course_map_md = partial(
        navigation_low_token_course_map_md,
        build_file_map_timeline_context_from_course=build_file_map_timeline_context_from_course,
        aggregate_unit_periods_from_blocks=aggregate_unit_periods_from_blocks,
        normalize_unit_slug=normalize_unit_slug,
        parse_units_from_teaching_plan=parse_units_from_teaching_plan,
        topic_text=topic_text,
        topic_depth=topic_depth,
        build_assessment_context_from_course=build_assessment_context_from_course,
        assessment_conflict_section_lines=assessment_conflict_section_lines,
        clamp_navigation_artifact=clamp_navigation_artifact,
        logger=logger,
    )
    low_token_file_map_md = partial(
        navigation_low_token_file_map_md,
        build_file_map_content_taxonomy_from_course=build_file_map_content_taxonomy_from_course,
        build_file_map_unit_index_from_course=build_file_map_unit_index_from_course,
        build_file_map_timeline_context_from_course=build_file_map_timeline_context_from_course,
        iter_content_taxonomy_topics=iter_content_taxonomy_topics,
        merge_manual_and_auto_tags=merge_manual_and_auto_tags,
        resolve_entry_manual_timeline_block=resolve_entry_manual_timeline_block,
        entry_markdown_text_for_file_map=entry_markdown_text_for_file_map,
        auto_map_entry_subtopic=auto_map_entry_subtopic,
        resolve_entry_manual_unit_slug=resolve_entry_manual_unit_slug,
        unit_match_result_factory=unit_match_result_factory,
        derive_unit_from_topic_match=derive_unit_from_topic_match,
        auto_map_entry_unit=auto_map_entry_unit,
        select_probable_period_for_entry=select_probable_period_for_entry,
        file_map_markdown_cell=file_map_markdown_cell,
        entry_markdown_path_for_file_map=entry_markdown_path_for_file_map,
        get_entry_sections=get_entry_sections,
        infer_unit_confidence=infer_unit_confidence,
        entry_usage_hint=entry_usage_hint,
        entry_priority_label=entry_priority_label,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    budgeted_file_map_md = partial(
        navigation_budgeted_file_map_md,
        filter_live_manifest_entries=filter_live_manifest_entries,
        low_token_file_map_md_fn=low_token_file_map_md,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    low_token_course_map_md_v2 = partial(
        navigation_low_token_course_map_md_v2,
        low_token_course_map_md_fn=low_token_course_map_md,
    )
    exercise_index_md_v2 = partial(
        repo_artifacts_module.exercise_index_md,
        collapse_ws_fn=collapse_ws,
        merge_manual_and_auto_tags_fn=merge_manual_and_auto_tags,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    course_map_md = partial(
        navigation_course_map_md,
        low_token_course_map_md_v2_fn=low_token_course_map_md_v2,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    file_map_md = partial(
        navigation_file_map_md,
        budgeted_file_map_md_fn=budgeted_file_map_md,
    )
    exercise_index_md = exercise_index_md_v2

    return {
        "root_readme": root_readme,
        "wrap_frontmatter": wrap_frontmatter,
        "rows_to_markdown_table": rows_to_markdown_table,
        "manual_pdf_review_template": manual_pdf_review_template,
        "manual_image_review_template": manual_image_review_template,
        "manual_url_review_template": manual_url_review_template,
        "migrate_legacy_url_manual_reviews": migrate_legacy_url_manual_reviews,
        "pdf_curation_guide": pdf_curation_guide,
        "backend_architecture_md": backend_architecture_md,
        "backend_policy_yaml": backend_policy_yaml,
        "_low_token_course_map_md": low_token_course_map_md,
        "_low_token_file_map_md": low_token_file_map_md,
        "_budgeted_file_map_md": budgeted_file_map_md,
        "_low_token_course_map_md_v2": low_token_course_map_md_v2,
        "_exercise_index_md_v2": exercise_index_md_v2,
        "course_map_md": course_map_md,
        "file_map_md": file_map_md,
        "exercise_index_md": exercise_index_md,
    }

