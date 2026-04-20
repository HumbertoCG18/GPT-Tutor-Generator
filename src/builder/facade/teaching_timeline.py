from __future__ import annotations

from functools import partial


def build_teaching_timeline_aliases(
    *,
    teaching_plan_normalize_heading,
    teaching_plan_parse_units,
    teaching_plan_topic_text,
    teaching_plan_topic_depth,
    timeline_match_timeline_to_units_generic,
    normalize_unit_slug,
    entry_signals_score_text_against_row,
    file_map_timeline_block_rows_for_scoring,
    file_map_timeline_block_matches_preferred_topic,
    file_map_score_card_evidence_against_entry,
    file_map_score_entry_against_timeline_block,
    file_map_select_probable_period_for_entry,
    collect_entry_unit_signals,
    build_timeline_index,
    timeline_period_label,
    collapse_ws,
    normalize_match_text,
    extract_date_range_signal,
    extract_timeline_session_signals,
    parse_timeline_date_value,
    timeline_aggregate_unit_periods_from_blocks,
    timeline_build_file_map_timeline_context_from_course,
    build_file_map_unit_index_from_course,
    build_file_map_content_taxonomy_from_course,
    teaching_plan_parse_bibliography,
    timeline_build_assessment_context_from_course,
    repo_artifacts_module,
    write_text_fn,
):
    normalize_teaching_plan_heading = teaching_plan_normalize_heading
    parse_units_from_teaching_plan = teaching_plan_parse_units
    topic_text = teaching_plan_topic_text
    topic_depth = teaching_plan_topic_depth

    def match_timeline_to_units_generic(timeline, units):
        return timeline_match_timeline_to_units_generic(
            timeline,
            units,
            normalize_unit_slug=normalize_unit_slug,
            topic_text=topic_text,
        )

    match_timeline_to_units = match_timeline_to_units_generic
    score_text_against_row = entry_signals_score_text_against_row
    timeline_block_rows_for_scoring = file_map_timeline_block_rows_for_scoring
    timeline_block_matches_preferred_topic = file_map_timeline_block_matches_preferred_topic

    def score_card_evidence_against_entry(signals, card_items):
        return file_map_score_card_evidence_against_entry(
            signals,
            card_items,
            normalize_match_text=normalize_match_text,
        )

    def score_entry_against_timeline_block(
        signals,
        block,
        preferred_unit_slug="",
        preferred_topic_slug="",
    ):
        return file_map_score_entry_against_timeline_block(
            signals,
            block,
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=score_card_evidence_against_entry,
            preferred_unit_slug=preferred_unit_slug,
            preferred_topic_slug=preferred_topic_slug,
        )

    def select_probable_period_for_entry(
        entry,
        unit,
        candidate_rows,
        markdown_text,
        preferred_topic_slug="",
    ):
        return file_map_select_probable_period_for_entry(
            entry,
            unit,
            candidate_rows,
            markdown_text,
            preferred_topic_slug=preferred_topic_slug,
            collect_entry_unit_signals=collect_entry_unit_signals,
            build_timeline_index=build_timeline_index,
            timeline_period_label=timeline_period_label,
            collapse_ws=collapse_ws,
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            extract_date_range_signal=extract_date_range_signal,
            extract_timeline_session_signals=extract_timeline_session_signals,
            parse_timeline_date_value=parse_timeline_date_value,
        )

    aggregate_unit_periods_from_blocks = timeline_aggregate_unit_periods_from_blocks

    def build_file_map_timeline_context_from_course(course_meta, subject_profile=None, content_taxonomy=None):
        return timeline_build_file_map_timeline_context_from_course(
            course_meta,
            subject_profile,
            content_taxonomy,
            build_file_map_unit_index_from_course=build_file_map_unit_index_from_course,
            build_file_map_content_taxonomy_from_course=build_file_map_content_taxonomy_from_course,
        )

    parse_bibliography_from_teaching_plan = teaching_plan_parse_bibliography

    def build_assessment_context_from_course(course_meta, subject_profile=None, timeline_context=None):
        return timeline_build_assessment_context_from_course(
            course_meta,
            subject_profile,
            timeline_context,
            build_file_map_unit_index_from_course=build_file_map_unit_index_from_course,
            build_file_map_timeline_context_from_course=build_file_map_timeline_context_from_course,
            normalize_match_text=normalize_match_text,
            normalize_teaching_plan_heading=normalize_teaching_plan_heading,
        )

    write_internal_assessment_context = partial(
        repo_artifacts_module.write_internal_assessment_context,
        write_text_fn=write_text_fn,
    )
    assessment_conflict_section_lines = repo_artifacts_module.assessment_conflict_section_lines

    return {
        "_normalize_teaching_plan_heading": normalize_teaching_plan_heading,
        "_parse_units_from_teaching_plan": parse_units_from_teaching_plan,
        "_topic_text": topic_text,
        "_topic_depth": topic_depth,
        "_match_timeline_to_units_generic": match_timeline_to_units_generic,
        "_match_timeline_to_units": match_timeline_to_units,
        "_score_text_against_row": score_text_against_row,
        "_timeline_block_rows_for_scoring": timeline_block_rows_for_scoring,
        "_timeline_block_matches_preferred_topic": timeline_block_matches_preferred_topic,
        "_score_card_evidence_against_entry": score_card_evidence_against_entry,
        "_score_entry_against_timeline_block": score_entry_against_timeline_block,
        "_select_probable_period_for_entry": select_probable_period_for_entry,
        "_aggregate_unit_periods_from_blocks": aggregate_unit_periods_from_blocks,
        "_build_file_map_timeline_context_from_course": build_file_map_timeline_context_from_course,
        "_parse_bibliography_from_teaching_plan": parse_bibliography_from_teaching_plan,
        "_build_assessment_context_from_course": build_assessment_context_from_course,
        "_write_internal_assessment_context": write_internal_assessment_context,
        "_assessment_conflict_section_lines": assessment_conflict_section_lines,
    }

