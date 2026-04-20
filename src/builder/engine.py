from __future__ import annotations
# Stable facade for builder functionality during modularization.
# Policy:
# - RepoBuilder, backend selection, and compatibility helpers remain importable here.
# - Implementations should keep moving into focused subpackages.
# - New direct consumers should prefer the focused modules instead of adding more
#   engine-level helper imports.
# Focused builder subsystems already live in:
# - src.builder.extraction.content_taxonomy
# - src.builder.extraction.image_markdown
# - src.builder.timeline.index
# - src.builder.timeline.signals
# - src.builder.artifacts.navigation
# - src.builder.artifacts.prompts / pedagogy / repo / student_state
# - src.builder.vision.*
import csv
import difflib
import html as html_lib
import json
import logging
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import asdict
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.builder.datalab_client import (
    convert_document_to_markdown,
    get_datalab_base_url,
    has_datalab_api_key,
)
from src.builder.extraction.image_markdown import (
    _IMAGE_DESC_BLOCK_RE,
    _image_curation_heading as _image_curation_heading_label,
    _low_token_inject_image_descriptions,
)
from src.builder.extraction.entry_signals import (
    collect_entry_unit_signals as _entry_signals_collect_entry_unit_signals,
    entry_image_source_dirs as _entry_signals_image_source_dirs,
    normalize_match_text as _entry_signals_normalize_match_text,
    score_text_against_row as _entry_signals_score_text_against_row,
)
from src.builder.file_map_routing import (
    UNIT_GENERIC_TOKENS as _FILE_MAP_UNIT_GENERIC_TOKENS,
    UnitMatchResult,
    auto_map_entry_subtopic as _file_map_auto_map_entry_subtopic,
    auto_map_entry_unit as _file_map_auto_map_entry_unit,
    build_file_map_content_taxonomy_from_course as _file_map_build_file_map_content_taxonomy_from_course,
    build_file_map_unit_index as _file_map_build_file_map_unit_index,
    build_file_map_unit_index_from_course as _file_map_build_file_map_unit_index_from_course,
    format_file_map_unit_cell as _file_map_format_file_map_unit_cell,
    resolve_entry_manual_timeline_block as _file_map_resolve_entry_manual_timeline_block,
    resolve_entry_manual_unit_slug as _file_map_resolve_entry_manual_unit_slug,
    score_card_evidence_against_entry as _file_map_score_card_evidence_against_entry,
    score_entry_against_timeline_block as _file_map_score_entry_against_timeline_block,
    score_entry_against_unit as _file_map_score_entry_against_unit,
    select_probable_period_for_entry as _file_map_select_probable_period_for_entry,
    strip_outline_prefix as _file_map_strip_outline_prefix,
    timeline_block_matches_preferred_topic as _file_map_timeline_block_matches_preferred_topic,
    timeline_block_rows_for_scoring as _file_map_timeline_block_rows_for_scoring,
)
from src.builder.backend_runtime import (
    MARKER_OLLAMA_SERVICE,
    advanced_cli_stall_timeout as _backend_advanced_cli_stall_timeout,
    build_marker_page_chunks as _backend_build_marker_page_chunks,
    build_page_chunks as _backend_build_page_chunks,
    configure_docling_python_standard_gpu as _backend_configure_docling_python_standard_gpu,
    datalab_chunk_size_for_workload as _backend_datalab_chunk_size_for_workload,
    datalab_should_chunk as _backend_datalab_should_chunk,
    detect_marker_capabilities as _backend_detect_marker_capabilities,
    load_docling_python_api as _backend_load_docling_python_api,
    marker_chunk_size_for_workload as _backend_marker_chunk_size_for_workload,
    marker_effective_torch_device as _backend_marker_effective_torch_device,
    marker_model_is_cloud_variant as _backend_marker_model_is_cloud_variant,
    marker_model_is_probably_vision as _backend_marker_model_is_probably_vision,
    marker_model_is_qwen3_vl_8b as _backend_marker_model_is_qwen3_vl_8b,
    marker_model_slug as _backend_marker_model_slug,
    marker_ollama_model as _backend_marker_ollama_model,
    marker_progress_hints as _backend_marker_progress_hints,
    marker_should_redo_inline_math as _backend_marker_should_redo_inline_math,
    marker_should_use_llm as _backend_marker_should_use_llm,
    marker_torch_device as _backend_marker_torch_device,
    prepare_docling_python_source_pdf as _backend_prepare_docling_python_source_pdf,
    run_cli_with_timeout as _backend_run_cli_with_timeout,
    selected_page_count as _backend_selected_page_count,
    should_force_ocr_for_marker as _backend_should_force_ocr_for_marker,
)
from src.builder.artifacts.prompts import (
    generate_claude_project_instructions,
    generate_gemini_instructions,
    generate_gpt_instructions,
)
from src.builder.text_sanitization import (
    detect_latex_corruption as _text_detect_latex_corruption,
    hybridize_marker_markdown_with_base as _text_hybridize_marker_markdown_with_base,
    is_plain_text_recovery_candidate as _text_is_plain_text_recovery_candidate,
    mojibake_score as _text_mojibake_score,
    normalize_unicode_math as _text_normalize_unicode_math,
    normalize_tex_accents_in_math as _text_normalize_tex_accents_in_math,
    repair_mojibake_text as _text_repair_mojibake_text,
    sanitize_external_markdown_text as _text_sanitize_external_markdown_text,
)
from src.builder.url_markdown import (
    content_score as _url_markdown_content_score,
    extract_url_page_metadata as _url_markdown_extract_url_page_metadata,
    html_to_structured_markdown as _url_markdown_html_to_structured_markdown,
    inline_html_to_markdown as _url_markdown_inline_html_to_markdown,
    is_probably_noise_container as _url_markdown_is_probably_noise_container,
    pick_best_content_root as _url_markdown_pick_best_content_root,
    render_html_block_to_markdown as _url_markdown_render_html_block_to_markdown,
    truncate_markdown_blocks as _url_markdown_truncate_markdown_blocks,
)
from src.builder.markdown_utils import (
    compact_notebook_markdown as _markdown_utils_compact_notebook_markdown,
    generated_repo_gitignore_text as _markdown_utils_generated_repo_gitignore_text,
    merge_numeric_dicts as _markdown_utils_merge_numeric_dicts,
    rewrite_markdown_asset_paths as _markdown_utils_rewrite_markdown_asset_paths,
    strip_frontmatter_block as _markdown_utils_strip_frontmatter_block,
    strip_markdown_image_refs as _markdown_utils_strip_markdown_image_refs,
)
from src.builder.core_utils import (
    collapse_ws as _core_utils_collapse_ws,
    effective_document_profile as _core_utils_effective_document_profile,
    merge_manual_and_auto_tags as _core_utils_merge_manual_and_auto_tags,
    pdf_image_extraction_policy as _core_utils_pdf_image_extraction_policy,
    persist_enriched_timeline_index as _core_utils_persist_enriched_timeline_index,
    strip_topic_prefix as _core_utils_strip_topic_prefix,
    topic_support_tokens as _core_utils_topic_support_tokens,
)
from src.builder.pdf_analysis import (
    apply_math_normalization as _pdf_analysis_apply_math_normalization,
    profile_pdf as _pdf_analysis_profile_pdf,
    quick_page_count as _pdf_analysis_quick_page_count,
)
from src.builder.pdf_assets import (
    convert_image_format as _pdf_assets_convert_image_format,
    detect_tables_pymupdf as _pdf_assets_detect_tables_pymupdf,
    extract_pdf_images as _pdf_assets_extract_pdf_images,
    extract_tables_pdfplumber as _pdf_assets_extract_tables_pdfplumber,
    image_format as _pdf_assets_image_format,
    is_noise_image as _pdf_assets_is_noise_image,
    should_keep_extracted_pdf_image as _pdf_assets_should_keep_extracted_pdf_image,
)
from src.builder.pdf_pipeline import (
    log_backend_result as _pdf_pipeline_log_backend_result,
    process_pdf as _pdf_pipeline_process_pdf,
)
from src.builder.pdf_scanned import (
    render_scanned_pdf_as_images as _pdf_scanned_render_scanned_pdf_as_images,
)
from src.builder.pedagogical_regeneration import (
    regenerate_pedagogical_files as _pedagogical_regeneration_regenerate_pedagogical_files,
)
from src.builder.operational_artifacts import (
    compact_manifest as _operational_artifacts_compact_manifest,
    write_build_report as _operational_artifacts_write_build_report,
    write_bundle_seed as _operational_artifacts_write_bundle_seed,
    write_source_registry as _operational_artifacts_write_source_registry,
)
from src.builder.incremental_build import (
    incremental_build_impl as _incremental_build_incremental_build_impl,
)
from src.builder.lifecycle_ops import (
    process_single_impl as _lifecycle_ops_process_single_impl,
    reject as _lifecycle_ops_reject,
    unprocess as _lifecycle_ops_unprocess,
)
from src.builder.bootstrap_ops import (
    create_structure as _bootstrap_ops_create_structure,
    write_root_files as _bootstrap_ops_write_root_files,
)
from src.builder.source_importers import (
    process_code as _source_importers_process_code,
    process_github_repo as _source_importers_process_github_repo,
    process_image as _source_importers_process_image,
    process_zip as _source_importers_process_zip,
)
from src.builder.artifacts import student_state as student_state_v2
from src.builder.artifacts.pedagogy import (
    _code_review_profile,
    modes_md,
    output_templates_md,
    pedagogy_md,
    tutor_policy_md,
)
from src.builder.artifacts.navigation import (
    _clean_extraction_noise,
    _entry_markdown_path_for_file_map,
    _entry_markdown_text_for_file_map,
    _entry_priority_label,
    _entry_usage_hint,
    _extract_section_headers,
    _file_map_markdown_cell,
    _get_entry_sections,
    _inject_executive_summary,
    _infer_unit_confidence,
    budgeted_file_map_md as _navigation_budgeted_file_map_md,
    course_map_md as _navigation_course_map_md,
    file_map_md as _navigation_file_map_md,
    low_token_course_map_md as _navigation_low_token_course_map_md,
    low_token_course_map_md_v2 as _navigation_low_token_course_map_md_v2,
    low_token_file_map_md as _navigation_low_token_file_map_md,
)
from src.builder.extraction import content_taxonomy as _content_taxonomy
from src.builder.artifacts import repo as _repo_artifacts
from src.builder.semantic_config import (
    resolve_semantic_profile,
)
from src.builder.timeline.index import (
    TopicMatchResult,
    _aggregate_unit_periods_from_blocks as _timeline_aggregate_unit_periods_from_blocks,
    _assign_timeline_block_to_topic,
    _build_timeline_candidate_rows,
    _build_assessment_context_from_course as _timeline_build_assessment_context_from_course,
    _build_file_map_timeline_context_from_course as _timeline_build_file_map_timeline_context_from_course,
    _build_timeline_block_topic_signals,
    _build_timeline_index,
    _derive_unit_from_topic_match,
    _empty_timeline_index,
    _iter_content_taxonomy_topics,
    _infer_timeline_keys,
    _parse_syllabus_timeline,
    _parse_timeline_date_value,
    _parse_timeline_period_bounds,
    _row_looks_like_continuation,
    _rows_belong_to_same_thematic_block,
    _score_entry_against_taxonomy_topic,
    _score_timeline_block_against_taxonomy_topic,
    _score_timeline_row_against_unit,
    _score_timeline_unit_phrase,
    _serialize_timeline_index,
    _timeline_block_is_administrative_only,
    _timeline_block_is_noninstructional,
    _timeline_block_is_soft_continuation,
    _timeline_core_text,
    _timeline_period_label,
    _timeline_row_is_review_or_assessment,
    _timeline_unit_number_from_text,
    _timeline_unit_number_from_unit,
    _TIMELINE_UNIT_NEUTRAL_TOKENS,
    _timeline_row_is_unit_anchor_only,
    _timeline_specific_tokens,
    _timeline_text_is_administrative,
    _extract_timeline_topics,
    _assign_timeline_block_to_unit,
    _match_timeline_to_units_generic as _timeline_match_timeline_to_units_generic,
    _write_internal_timeline_index,
)
from src.builder.timeline.signals import (
    extract_date_range_signal,
    extract_timeline_session_signals,
)
from src.builder.extraction.teaching_plan import (
    _parse_bibliography_from_teaching_plan as _teaching_plan_parse_bibliography_from_teaching_plan,
    _normalize_teaching_plan_heading as _teaching_plan_normalize_heading,
    _normalize_unit_slug as _teaching_plan_normalize_unit_slug,
    _parse_units_from_teaching_plan as _teaching_plan_parse_units_from_teaching_plan,
    _topic_depth as _teaching_plan_topic_depth,
    _topic_text as _teaching_plan_topic_text,
)
from src.models.core import (
    BackendRunResult, DocumentProfileReport, FileEntry,
    PipelineDecision, StudentProfile, SubjectProfile
)
from src.utils.helpers import (
    APP_NAME, DOCLING_CLI, EXAM_CATEGORIES, EXERCISE_CATEGORIES,
    HAS_PDFPLUMBER, HAS_PYMUPDF, HAS_PYMUPDF4LLM, IMAGE_CATEGORIES, MARKER_CLI,
    CODE_EXTENSIONS, LANG_MAP, CODE_CATEGORIES, ASSIGNMENT_CATEGORIES,
    WHITEBOARD_CATEGORIES, STUDENT_BRANCHES,
    ensure_dir, json_str, pages_to_marker_range,
    normalize_document_profile, parse_page_range, safe_rel, slugify, write_text,
)
from src.utils.power import prevent_system_sleep

if HAS_PYMUPDF:
    import pymupdf
if HAS_PYMUPDF4LLM:
    import pymupdf4llm
if HAS_PDFPLUMBER:
    import pdfplumber

logger = logging.getLogger(__name__)

_DOCLING_PYTHON_API_CACHE = None


_effective_document_profile = _core_utils_effective_document_profile


_persist_enriched_timeline_index = _core_utils_persist_enriched_timeline_index


_collapse_ws = _core_utils_collapse_ws


_strip_topic_prefix = _core_utils_strip_topic_prefix


_looks_like_tool_candidate = _content_taxonomy._looks_like_tool_candidate
_looks_like_bibliography_candidate = _content_taxonomy._looks_like_bibliography_candidate
_looks_like_goal_or_section_candidate = _content_taxonomy._looks_like_goal_or_section_candidate
_looks_like_weak_heading_candidate = _content_taxonomy._looks_like_weak_heading_candidate
_is_valid_topic_candidate = _content_taxonomy._is_valid_topic_candidate


_extract_topic_candidates = _content_taxonomy._extract_topic_candidates
_extract_tool_candidates = _content_taxonomy._extract_tool_candidates


_topic_support_tokens = lambda text: _core_utils_topic_support_tokens(
    text,
    normalize_match_text_fn=_normalize_match_text,
)


_select_supported_taxonomy_topic = _content_taxonomy._select_supported_taxonomy_topic
_heading_topic_has_vocab_support = _content_taxonomy._heading_topic_has_vocab_support
_extract_topic_code = _content_taxonomy._extract_topic_code
_strip_topic_code = _content_taxonomy._strip_topic_code
_parse_glossary_terms = _content_taxonomy._parse_glossary_terms
_glossary_aliases_for_topic = _content_taxonomy._glossary_aliases_for_topic
_dedupe_taxonomy_topics = _content_taxonomy._dedupe_taxonomy_topics
_infer_course_slug_from_units = _content_taxonomy._infer_course_slug_from_units

def _build_content_taxonomy(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
) -> dict:
    return _content_taxonomy.build_content_taxonomy(
        teaching_plan=teaching_plan,
        course_map_md=course_map_md,
        glossary_md=glossary_md,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text,
        normalize_unit_slug=_normalize_unit_slug,
    )


_write_internal_content_taxonomy = _content_taxonomy.write_internal_content_taxonomy
_collect_strong_heading_candidates = _content_taxonomy.collect_strong_heading_candidates
_entry_tag_signal_text = _content_taxonomy._entry_tag_signal_text
_signal_token_set = _content_taxonomy._signal_token_set
_matches_tag_slug = _content_taxonomy._matches_tag_slug


def _write_tag_catalog(
    root_dir: Path,
    subject_profile: Optional[SubjectProfile],
    manifest_entries: Optional[List[dict]],
    *,
    course_map_text: str,
    glossary_text: str,
) -> dict:
    return _content_taxonomy.write_tag_catalog(
        root_dir,
        course_name=(subject_profile.name if subject_profile and subject_profile.name else root_dir.name),
        teaching_plan=getattr(subject_profile, "teaching_plan", "") or "",
        course_map_text=course_map_text,
        glossary_text=glossary_text,
        manifest_entries=manifest_entries,
    )


def _refresh_manifest_auto_tags(root_dir: Path, manifest_entries: List[dict], vocabulary: dict) -> List[dict]:
    return _content_taxonomy.refresh_manifest_auto_tags(
        root_dir,
        manifest_entries,
        vocabulary,
        entry_markdown_text_for_file_map=_entry_markdown_text_for_file_map,
    )


_merge_manual_and_auto_tags = _core_utils_merge_manual_and_auto_tags


_strip_frontmatter_block = _markdown_utils_strip_frontmatter_block
_rewrite_markdown_asset_paths = _markdown_utils_rewrite_markdown_asset_paths
_strip_markdown_image_refs = _markdown_utils_strip_markdown_image_refs


_build_page_chunks = _backend_build_page_chunks
_build_marker_page_chunks = _backend_build_marker_page_chunks
_selected_page_count = _backend_selected_page_count


_prepare_docling_python_source_pdf = lambda ctx, out_dir: _backend_prepare_docling_python_source_pdf(
    ctx,
    out_dir,
    has_pymupdf=HAS_PYMUPDF,
    pymupdf_module=pymupdf if HAS_PYMUPDF else None,
)


_configure_docling_python_standard_gpu = _backend_configure_docling_python_standard_gpu


_marker_chunk_size_for_workload = lambda ctx: _backend_marker_chunk_size_for_workload(
    ctx,
    effective_document_profile_fn=_effective_document_profile,
    selected_page_count_fn=_selected_page_count,
)


_datalab_chunk_size_for_workload = lambda ctx: _backend_datalab_chunk_size_for_workload(
    ctx,
    effective_document_profile_fn=_effective_document_profile,
    selected_page_count_fn=_selected_page_count,
)


_datalab_should_chunk = lambda ctx: _backend_datalab_should_chunk(
    ctx,
    datalab_chunk_size_for_workload_fn=_datalab_chunk_size_for_workload,
    selected_page_count_fn=_selected_page_count,
)


_merge_numeric_dicts = _markdown_utils_merge_numeric_dicts


_should_force_ocr_for_marker = _backend_should_force_ocr_for_marker
_marker_should_use_llm = _backend_marker_should_use_llm
_marker_ollama_model = _backend_marker_ollama_model
_marker_torch_device = _backend_marker_torch_device
_marker_effective_torch_device = _backend_marker_effective_torch_device
_marker_model_slug = _backend_marker_model_slug
_marker_model_is_qwen3_vl_8b = _backend_marker_model_is_qwen3_vl_8b
_marker_model_is_cloud_variant = _backend_marker_model_is_cloud_variant
_marker_model_is_probably_vision = _backend_marker_model_is_probably_vision
_marker_should_redo_inline_math = _backend_marker_should_redo_inline_math
_marker_progress_hints = _backend_marker_progress_hints
_load_docling_python_api = _backend_load_docling_python_api
has_docling_python_api = lambda: bool(_load_docling_python_api())


_advanced_cli_stall_timeout = lambda backend_name, ctx: _backend_advanced_cli_stall_timeout(
    backend_name,
    ctx,
    effective_document_profile_fn=_effective_document_profile,
    selected_page_count_fn=_selected_page_count,
)


def _pdf_image_extraction_policy(ctx: "BackendContext") -> Dict[str, object]:
    return _core_utils_pdf_image_extraction_policy(
        entry_profile=ctx.entry.document_profile,
        suggested_profile=ctx.report.suggested_profile,
        suspected_scan=ctx.report.suspected_scan,
        default_min_bytes=RepoBuilder._MIN_IMG_BYTES,
        default_min_dimension=RepoBuilder._MIN_IMG_DIMENSION,
        default_max_aspect_ratio=RepoBuilder._MAX_ASPECT_RATIO,
    )
_truncate_markdown_blocks = _url_markdown_truncate_markdown_blocks


_compact_notebook_markdown = _markdown_utils_compact_notebook_markdown
_generated_repo_gitignore_text = _markdown_utils_generated_repo_gitignore_text


_extract_url_page_metadata = partial(
    _url_markdown_extract_url_page_metadata,
    collapse_ws=_collapse_ws,
)
_is_probably_noise_container = _url_markdown_is_probably_noise_container
_content_score = _url_markdown_content_score
_pick_best_content_root = _url_markdown_pick_best_content_root
_inline_html_to_markdown = partial(
    _url_markdown_inline_html_to_markdown,
    collapse_ws=_collapse_ws,
)
_render_html_block_to_markdown = partial(
    _url_markdown_render_html_block_to_markdown,
    collapse_ws=_collapse_ws,
)
_html_to_structured_markdown = partial(
    _url_markdown_html_to_structured_markdown,
    collapse_ws=_collapse_ws,
    truncate_markdown_blocks=_truncate_markdown_blocks,
)


# ---------------------------------------------------------------------------
# Unicode math -> LaTeX normalization
# ---------------------------------------------------------------------------

_normalize_tex_accents_in_math = _text_normalize_tex_accents_in_math
_normalize_unicode_math = _text_normalize_unicode_math
_mojibake_score = _text_mojibake_score
_repair_mojibake_text = _text_repair_mojibake_text
_sanitize_external_markdown_text = _text_sanitize_external_markdown_text
_detect_latex_corruption = _text_detect_latex_corruption
_is_plain_text_recovery_candidate = _text_is_plain_text_recovery_candidate
_hybridize_marker_markdown_with_base = _text_hybridize_marker_markdown_with_base


# ---------------------------------------------------------------------------
# Backend architecture
# ---------------------------------------------------------------------------

class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport,
                 cancel_check=None, stall_timeout: int = 300, marker_chunking_mode: str = "fallback",
                 marker_use_llm: bool = False, marker_llm_model: str = "", marker_torch_device: str = "auto", ollama_base_url: str = "",
                 vision_model: str = ""):
        self.root_dir = root_dir
        self.raw_target = raw_target
        self.entry = entry
        self.report = report
        self.entry_id = entry.id()
        self.pages = parse_page_range(entry.page_range)
        self.cancel_check = cancel_check    # callable que levanta InterruptedError se cancelado
        self.stall_timeout = stall_timeout  # segundos sem output antes de matar o processo
        self.marker_chunking_mode = str(marker_chunking_mode or "fallback").strip().lower()
        self.marker_use_llm = bool(marker_use_llm)
        self.marker_llm_model = str(marker_llm_model or "").strip()
        self.marker_torch_device = str(marker_torch_device or "auto").strip().lower() or "auto"
        self.ollama_base_url = str(ollama_base_url or "").strip()
        self.vision_model = str(vision_model or "").strip()

    def page_label(self) -> str:
        return self.entry.page_range.strip() or "all"


class ExtractionBackend:
    name = "base"
    layer = "base"

    def available(self) -> bool:
        return False

    def run(self, ctx: BackendContext) -> BackendRunResult:
        raise NotImplementedError


class PyMuPDF4LLMBackend(ExtractionBackend):
    name = "pymupdf4llm"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF4LLM

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf4llm"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        # Nota: NÃO usar force_ocr=True — pymupdf4llm tem um bug onde chama
        # ocr_function(page) sem verificar se é None quando force_ocr=True.
        # Em vez disso, usamos use_ocr=True (default) que detecta páginas
        # scaneadas automaticamente e usa o OCR embutido do pymupdf (pdfocr_tobytes).
        wants_ocr = bool(ctx.entry.force_ocr) or ctx.report.suspected_scan
        kwargs = {
            "pages": ctx.pages,
            "write_images": bool(ctx.entry.preserve_pdf_images_in_markdown),
            "image_path": str((ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id).resolve()),
            "use_ocr": wants_ocr,
            "page_separators": True,
        }
        if wants_ocr:
            kwargs["ocr_language"] = ctx.entry.ocr_language.replace(",", "+")
        if not ctx.entry.preserve_pdf_images_in_markdown:
            kwargs["write_images"] = False
            kwargs.pop("image_path", None)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        md = pymupdf4llm.to_markdown(str(ctx.raw_target), **kwargs)
        if isinstance(md, list):
            body = "\n\n".join(chunk.get("text", "") for chunk in md)
        else:
            body = md

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id, ctx.root_dir) if ctx.entry.preserve_pdf_images_in_markdown else None,
            notes=["Markdown gerado com PyMuPDF4LLM."],
        )


class PyMuPDFBackend(ExtractionBackend):
    name = "pymupdf"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        doc = pymupdf.open(str(ctx.raw_target))
        try:
            target_pages = ctx.pages or list(range(doc.page_count))
            pieces = [f"# {ctx.entry.title}", ""]
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    continue
                page = doc[i]
                pieces.append(f"## Página {i + 1}")
                pieces.append("")
                text = page.get_text("text")
                text = re.sub(r"[ \t]+\n", "\n", text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                pieces.append(text.strip())
                pieces.append("")
            body = "\n".join(pieces).strip() + "\n"
        finally:
            doc.close()

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            notes=["Markdown bruto gerado com PyMuPDF."],
        )


_run_cli_with_timeout = lambda cmd, backend_name, ctx, stall_timeout=None: _backend_run_cli_with_timeout(
    cmd,
    backend_name,
    ctx,
    logger_obj=logger,
    marker_effective_torch_device_fn=_marker_effective_torch_device,
    marker_progress_hints_fn=_marker_progress_hints,
    marker_should_use_llm_fn=_marker_should_use_llm,
    marker_ollama_model_fn=_marker_ollama_model,
    marker_model_is_qwen3_vl_8b_fn=_marker_model_is_qwen3_vl_8b,
    stall_timeout=stall_timeout,
)

_MARKER_CAPABILITIES_CACHE = None


def _detect_marker_capabilities() -> Dict[str, object]:
    global _MARKER_CAPABILITIES_CACHE

    if _MARKER_CAPABILITIES_CACHE is not None:
        return dict(_MARKER_CAPABILITIES_CACHE)

    caps = _backend_detect_marker_capabilities(
        MARKER_CLI,
        use_cache=False,
        run_cmd=subprocess.run,
    )
    _MARKER_CAPABILITIES_CACHE = dict(caps)
    return dict(caps)

class DoclingCLIBackend(ExtractionBackend):
    name = "docling"
    layer = "advanced"

    def available(self) -> bool:
        return bool(DOCLING_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling" / ctx.entry_id
        ensure_dir(out_dir)
        stall_timeout = _advanced_cli_stall_timeout("docling", ctx)

        cmd = [
            DOCLING_CLI,
            str(ctx.raw_target),
            "--to", "md",
            "--output", str(out_dir),
            "--image-export-mode", "referenced",
            "--tables",
            "--ocr",
            "--ocr-lang", ctx.entry.ocr_language,
            "--table-mode", "accurate",
            "-vv",
        ]

        if ctx.entry.force_ocr or ctx.report.suspected_scan:
            cmd.append("--force-ocr")
        suggested_profile = normalize_document_profile(ctx.report.suggested_profile)
        if ctx.entry.formula_priority or suggested_profile == "math_heavy":
            cmd.append("--enrich-formula")
        if suggested_profile == "diagram_heavy":
            cmd.append("--enrich-picture-classes")

        logger.info("  [docling] Comando: %s", " ".join(cmd))
        logger.info(
            "  [docling] Stall timeout efetivo: %ss para %d páginas selecionadas.",
            stall_timeout,
            _selected_page_count(ctx),
        )
        logger.info("  [docling] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(
                cmd,
                "docling",
                ctx,
                stall_timeout=stall_timeout,
            )
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [docling] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Docling CLI falhou")[-4000:]
            logger.error("  [docling] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "docling-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
            "stall_timeout": stall_timeout,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Docling CLI."],
        )


class DoclingPythonBackend(ExtractionBackend):
    name = "docling_python"
    layer = "advanced"

    def available(self) -> bool:
        return has_docling_python_api()

    def run(self, ctx: BackendContext) -> BackendRunResult:
        api = _load_docling_python_api()
        if not api:
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error="Docling Python API não está disponível no ambiente atual.",
            )

        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling-python" / ctx.entry_id
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        DocumentConverter = api["DocumentConverter"]
        PdfFormatOption = api["PdfFormatOption"]
        PdfPipelineOptions = api["PdfPipelineOptions"]
        ThreadedPdfPipelineOptions = api.get("ThreadedPdfPipelineOptions", PdfPipelineOptions)
        InputFormat = api["InputFormat"]
        settings_obj = api.get("settings")

        pipeline_options = ThreadedPdfPipelineOptions()
        suggested_profile = normalize_document_profile(ctx.report.suggested_profile)
        formula_enrichment = bool(ctx.entry.formula_priority or suggested_profile == "math_heavy")
        if hasattr(pipeline_options, "do_formula_enrichment"):
            pipeline_options.do_formula_enrichment = formula_enrichment
        gpu_config = _configure_docling_python_standard_gpu(api, pipeline_options)

        logger.info(
            "  [docling_python] Iniciando API Python com do_formula_enrichment=%s para %s (gpu_standard=%s, device=%s).",
            formula_enrichment,
            ctx.entry_id,
            gpu_config["enabled"],
            gpu_config["device"],
        )
        source_pdf, page_range_applied = _prepare_docling_python_source_pdf(ctx, out_dir)
        if page_range_applied:
            logger.info(
                "  [docling_python] Aplicando page_range=%s via PDF temporario com %d paginas selecionadas.",
                ctx.entry.page_range or "all",
                len(ctx.pages or []),
            )
        if ctx.pages and not page_range_applied:
            logger.info(
                "  [docling_python] A API Python será testada sem page_range; processando o documento inteiro."
            )

        previous_page_batch_size = gpu_config.get("previous_page_batch_size")
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            result = converter.convert(str(source_pdf))
            body = result.document.export_to_markdown()
        except Exception as e:
            logger.error("  [docling_python] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )
        finally:
            if settings_obj is not None and previous_page_batch_size is not None:
                settings_obj.perf.page_batch_size = previous_page_batch_size

        write_text(out_path, body)
        metadata_path = out_dir / "docling-python-run.json"
        write_text(metadata_path, json.dumps({
            "source_pdf": str(ctx.raw_target),
            "effective_source_pdf": str(source_pdf),
            "formula_enrichment": formula_enrichment,
            "gpu_standard": gpu_config,
            "page_range_requested": ctx.entry.page_range,
            "page_range_applied": page_range_applied,
            "selected_pages_count": len(ctx.pages or []) if page_range_applied else None,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=["Saída avançada gerada com Docling Python API."],
        )


class DatalabCloudBackend(ExtractionBackend):
    name = "datalab"
    layer = "advanced"

    def available(self) -> bool:
        return has_datalab_api_key()

    def _convert_range(
        self,
        ctx: BackendContext,
        *,
        mode: str,
        page_range: Optional[str],
        max_wait_seconds: int,
    ):
        result = convert_document_to_markdown(
            ctx.raw_target,
            output_format="markdown",
            mode=mode,
            page_range=page_range,
            disable_image_captions=True,
            disable_image_extraction=True,
            paginate=False,
            token_efficient_markdown=False,
            request_timeout=60,
            poll_interval=2.0,
            max_wait_seconds=max_wait_seconds,
        )
        markdown = _sanitize_external_markdown_text(result.markdown)
        markdown = _strip_markdown_image_refs(markdown)
        return result, markdown

    def _run_single_datalab(
        self,
        ctx: BackendContext,
        out_dir: Path,
        *,
        mode: str,
        page_range: Optional[str],
        max_wait_seconds: int,
    ) -> BackendRunResult:
        out_path = out_dir / f"{ctx.entry_id}.md"

        logger.info(
            "  [datalab] Enviando documento para a API (mode=%s, page_range=%s, max_wait=%ss).",
            mode,
            page_range or "all",
            max_wait_seconds,
        )

        try:
            result, markdown = self._convert_range(
                ctx,
                mode=mode,
                page_range=page_range,
                max_wait_seconds=max_wait_seconds,
            )
        except Exception as e:
            logger.error("  [datalab] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )

        write_text(out_path, markdown)

        metadata_path = out_dir / "datalab-run.json"
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "chunked": False,
            "request_id": result.request_id,
            "request_check_url": result.request_check_url,
            "mode": mode,
            "page_range": page_range,
            "selected_pages_count": _selected_page_count(ctx),
            "page_count": result.page_count,
            "parse_quality_score": result.parse_quality_score,
            "cost_breakdown": result.cost_breakdown,
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "metadata": result.metadata,
            "raw_response_tail": {
                "status": result.raw_response.get("status"),
                "success": result.raw_response.get("success"),
                "error": result.raw_response.get("error"),
            },
        }, indent=2, ensure_ascii=False))

        notes = [
            "SaÃ­da avanÃ§ada gerada com Datalab Document Conversion API.",
            f"Modo: {mode}.",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if result.parse_quality_score is not None:
            notes.append(f"parse_quality_score={result.parse_quality_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )

    def _run_chunked_datalab(
        self,
        ctx: BackendContext,
        out_dir: Path,
        *,
        mode: str,
        max_wait_seconds: int,
    ) -> BackendRunResult:
        chunk_size = _datalab_chunk_size_for_workload(ctx)
        chunks = _build_page_chunks(ctx.pages, ctx.report.page_count, chunk_size=chunk_size)
        if len(chunks) <= 1:
            return self._run_single_datalab(
                ctx,
                out_dir,
                mode=mode,
                page_range=pages_to_marker_range(ctx.pages),
                max_wait_seconds=max_wait_seconds,
            )

        logger.info(
            "  [datalab] Documento longo; processando em %d chunks de atÃ© %d pÃ¡ginas.",
            len(chunks),
            chunk_size,
        )

        out_path = out_dir / f"{ctx.entry_id}.md"
        chunks_dir = out_dir / "chunks"
        ensure_dir(chunks_dir)
        combined_parts: List[str] = []
        chunk_meta: List[Dict[str, object]] = []
        parse_scores: List[float] = []
        cost_breakdowns: List[Dict[str, object]] = []
        total_pages = 0

        for idx, chunk_pages in enumerate(chunks, start=1):
            chunk_range = pages_to_marker_range(chunk_pages)
            logger.info(
                "  [datalab] Chunk %d/%d â€” pÃ¡ginas %d-%d",
                idx,
                len(chunks),
                chunk_pages[0] + 1,
                chunk_pages[-1] + 1,
            )
            try:
                result, markdown = self._convert_range(
                    ctx,
                    mode=mode,
                    page_range=chunk_range,
                    max_wait_seconds=max_wait_seconds,
                )
            except Exception as e:
                logger.error("  [datalab] Erro no chunk %d/%d: %s", idx, len(chunks), e)
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    error=f"Chunk {idx}/{len(chunks)} falhou: {e}",
                )

            chunk_path = chunks_dir / f"chunk-{idx:03d}.md"
            write_text(chunk_path, markdown)

            chunk_body = _strip_frontmatter_block(markdown).strip()
            if chunk_body:
                combined_parts.append(
                    f"<!-- DATALAB_CHUNK {idx}: pages {chunk_pages[0] + 1}-{chunk_pages[-1] + 1} -->\n\n{chunk_body}"
                )

            if result.parse_quality_score is not None:
                parse_scores.append(float(result.parse_quality_score))
            cost_breakdowns.append(dict(result.cost_breakdown or {}))
            total_pages += int(result.page_count or 0)
            chunk_meta.append({
                "chunk_index": idx,
                "page_range": chunk_range,
                "page_count": result.page_count,
                "request_id": result.request_id,
                "request_check_url": result.request_check_url,
                "parse_quality_score": result.parse_quality_score,
                "cost_breakdown": result.cost_breakdown,
                "markdown_path": safe_rel(chunk_path, ctx.root_dir),
                "raw_response_tail": {
                    "status": result.raw_response.get("status"),
                    "success": result.raw_response.get("success"),
                    "error": result.raw_response.get("error"),
                },
            })

        combined_markdown = "\n\n".join(part for part in combined_parts if part).strip()
        if combined_markdown:
            combined_markdown += "\n"
        write_text(out_path, combined_markdown)

        metadata_path = out_dir / "datalab-run.json"
        average_score = round(sum(parse_scores) / len(parse_scores), 4) if parse_scores else None
        effective_page_range = pages_to_marker_range(ctx.pages)
        if not effective_page_range:
            flattened_pages = [page for chunk_pages in chunks for page in chunk_pages]
            effective_page_range = pages_to_marker_range(flattened_pages)
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "chunked": True,
            "chunk_size": chunk_size,
            "mode": mode,
            "page_range": effective_page_range,
            "selected_pages_count": _selected_page_count(ctx),
            "page_count": total_pages,
            "parse_quality_score": average_score,
            "cost_breakdown": _merge_numeric_dicts(cost_breakdowns),
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "chunks": chunk_meta,
        }, indent=2, ensure_ascii=False))

        notes = [
            "SaÃ­da avanÃ§ada gerada com Datalab Document Conversion API em chunks.",
            f"Modo: {mode}.",
            f"Chunking aplicado para documento longo ({len(chunks)} chunks de atÃ© {chunk_size} pÃ¡ginas).",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if average_score is not None:
            notes.append(f"parse_quality_score={average_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "datalab" / ctx.entry_id
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
        page_range = pages_to_marker_range(ctx.pages)
        requested_mode = str(getattr(ctx.entry, "datalab_mode", "") or "").strip().lower()
        mode = requested_mode if requested_mode in {"fast", "balanced", "accurate"} else ("accurate" if effective_profile == "math_heavy" else "balanced")
        max_wait_seconds = _advanced_cli_stall_timeout("docling", ctx)
        should_chunk = _datalab_should_chunk(ctx)

        logger.info(
            "  [datalab] Long-doc policy: should_chunk=%s (selected_pages=%d, chunk_size=%d).",
            should_chunk,
            _selected_page_count(ctx),
            _datalab_chunk_size_for_workload(ctx),
        )
        if should_chunk:
            return self._run_chunked_datalab(
                ctx,
                out_dir,
                mode=mode,
                max_wait_seconds=max_wait_seconds,
            )
        return self._run_single_datalab(
            ctx,
            out_dir,
            mode=mode,
            page_range=page_range,
            max_wait_seconds=max_wait_seconds,
        )

        logger.info(
            "  [datalab] Enviando documento para a API (mode=%s, page_range=%s, max_wait=%ss).",
            mode,
            page_range or "all",
            max_wait_seconds,
        )

        try:
            result = convert_document_to_markdown(
                ctx.raw_target,
                output_format="markdown",
                mode=mode,
                page_range=page_range,
                disable_image_captions=True,
                disable_image_extraction=True,
                paginate=False,
                token_efficient_markdown=False,
                request_timeout=60,
                poll_interval=2.0,
                max_wait_seconds=max_wait_seconds,
            )
        except Exception as e:
            logger.error("  [datalab] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )

        markdown = _sanitize_external_markdown_text(result.markdown)
        markdown = _strip_markdown_image_refs(markdown)
        write_text(out_path, markdown)

        metadata_path = out_dir / "datalab-run.json"
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "request_id": result.request_id,
            "request_check_url": result.request_check_url,
            "mode": mode,
            "page_range": page_range,
            "page_count": result.page_count,
            "parse_quality_score": result.parse_quality_score,
            "cost_breakdown": result.cost_breakdown,
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "metadata": result.metadata,
            "raw_response_tail": {
                "status": result.raw_response.get("status"),
                "success": result.raw_response.get("success"),
                "error": result.raw_response.get("error"),
            },
        }, indent=2, ensure_ascii=False))

        notes = [
            "Saída avançada gerada com Datalab Document Conversion API.",
            f"Modo: {mode}.",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if result.parse_quality_score is not None:
            notes.append(f"parse_quality_score={result.parse_quality_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )


class MarkerCLIBackend(ExtractionBackend):
    name = "marker"
    layer = "advanced"

    def available(self) -> bool:
        return bool(MARKER_CLI)

    def _run_single_marker(
        self,
        ctx: BackendContext,
        out_dir: Path,
        caps: Dict[str, object],
        pages: Optional[List[int]],
        stall_timeout: int,
    ) -> BackendRunResult:
        ensure_dir(out_dir)

        cmd = [
            MARKER_CLI,
            str(ctx.raw_target),
            "--output_format", "markdown",
            "--output_dir", str(out_dir),
        ]

        marker_range = pages_to_marker_range(pages)
        page_range_flag = caps.get("page_range_flag")
        if marker_range and page_range_flag:
            cmd.extend([page_range_flag, marker_range])
        elif marker_range:
            logger.info("  [marker] Versão atual não suporta page_range; processando o documento inteiro.")

        wants_force_ocr = _should_force_ocr_for_marker(ctx)
        force_ocr_flag = caps.get("force_ocr_flag")
        if wants_force_ocr and force_ocr_flag:
            cmd.append(force_ocr_flag)
        elif wants_force_ocr:
            logger.info("  [marker] Versão atual não suporta force_ocr; prosseguindo sem essa flag.")

        marker_llm_active = False
        marker_model = ""
        marker_ollama_url = str(getattr(ctx, "ollama_base_url", "") or "").strip()
        marker_torch_device = _marker_effective_torch_device(ctx)

        if _marker_should_use_llm(ctx):
            use_llm_flag = caps.get("use_llm_flag")
            llm_service_flag = caps.get("llm_service_flag")
            ollama_base_url_flag = caps.get("ollama_base_url_flag")
            ollama_model_flag = caps.get("ollama_model_flag")
            redo_inline_math_flag = caps.get("redo_inline_math_flag")
            marker_model = _marker_ollama_model(ctx)

            if not marker_model:
                logger.warning(
                    "  [marker] LLM habilitado, mas nenhum modelo do Marker foi configurado. "
                    "Defina 'Modelo Ollama do Marker' nas configurações para ativar --use_llm."
                )
            elif use_llm_flag:
                cmd.append(use_llm_flag)
                marker_llm_active = True
            else:
                logger.info("  [marker] Versão atual não suporta use_llm; prosseguindo sem LLM.")

            if marker_model and llm_service_flag:
                cmd.extend([llm_service_flag, MARKER_OLLAMA_SERVICE])
            elif marker_model and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta llm_service; mantendo serviço padrão.")

            if marker_model and ollama_base_url_flag and marker_ollama_url:
                cmd.extend([ollama_base_url_flag, marker_ollama_url])
            elif marker_model and marker_ollama_url and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta ollama_base_url; usando URL padrão do Marker.")

            if marker_model and ollama_model_flag:
                cmd.extend([ollama_model_flag, marker_model])
            elif marker_model and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta ollama_model; usando modelo padrão do Marker.")

            if marker_model and redo_inline_math_flag and _marker_should_redo_inline_math(ctx):
                cmd.append(redo_inline_math_flag)

            # Desativar LLM em processors visuais quando o modelo não é vision.
            # Modelos texto-only (gemma3, llama3.1, etc) alucinam ao "descrever"
            # imagens que não conseguem ver. O Image Curator com qwen3-vl
            # cuida das descrições separadamente.
            if marker_model and not _marker_model_is_probably_vision(marker_model):
                _visual_overrides = {
                    "LLMImageDescriptionProcessor_use_llm": False,
                    "LLMComplexRegionProcessor_use_llm": False,
                    "LLMHandwritingProcessor_use_llm": False,
                }
                config_json_path = out_dir / "marker-llm-config.json"
                write_text(config_json_path, json.dumps(_visual_overrides, indent=2))
                cmd.extend(["--config_json", str(config_json_path)])
                logger.info(
                    "  [marker] Processors visuais desativados via config_json "
                    "(modelo '%s' não é vision). Imagens serão tratadas pelo Image Curator.",
                    marker_model,
                )

            # Aumentar timeout do OllamaService para modelos locais (default=30s
            # é insuficiente quando GPU é compartilhada com layout models).
            ollama_timeout_flag = caps.get("ollama_timeout_flag")
            if marker_model and ollama_timeout_flag:
                cmd.extend([ollama_timeout_flag, "120"])

        if marker_llm_active:
            if _marker_model_is_cloud_variant(marker_model):
                logger.warning(
                    "  [marker] O modelo '%s' parece ser variante cloud. Para estabilidade no Marker, prefira um modelo local como gemma3:4b.",
                    marker_model,
                )
            elif not _marker_model_is_probably_vision(marker_model):
                logger.info(
                    "  [marker] Modelo texto-only '%s' detectado. Extração de imagens desabilitada automaticamente; "
                    "LLM será usado apenas para math, tabelas e headers.",
                    marker_model,
                )
            logger.info(
                "  [marker] LLM ativo: service=%s model=%s base_url=%s redo_inline_math=%s torch_device=%s",
                MARKER_OLLAMA_SERVICE,
                marker_model,
                marker_ollama_url or "(padrão do Marker)",
                "sim" if "--redo_inline_math" in cmd or "--redo-inline-math" in cmd else "não",
                marker_torch_device,
            )
        else:
            logger.info("  [marker] LLM inativo para esta execução. TORCH_DEVICE=%s", marker_torch_device)

        llm_metadata = {
            "enabled": marker_llm_active,
            "service": MARKER_OLLAMA_SERVICE if marker_llm_active else None,
            "model": marker_model or None,
            "base_url": marker_ollama_url or None,
            "redo_inline_math": bool("--redo_inline_math" in cmd or "--redo-inline-math" in cmd),
            "recommended_model": _marker_model_is_qwen3_vl_8b(marker_model) if marker_model else False,
            "is_cloud_variant": _marker_model_is_cloud_variant(marker_model) if marker_model else False,
            "is_probably_vision": _marker_model_is_probably_vision(marker_model) if marker_model else False,
            "visual_processors_disabled": bool(marker_model and not _marker_model_is_probably_vision(marker_model)),
        }

        logger.info("  [marker] Comando: %s", " ".join(cmd))
        logger.info("  [marker] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(
                cmd, "marker", ctx, stall_timeout=stall_timeout
            )
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [marker] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)
        ollama_failures = [line for line in stderr_lines if "Ollama inference failed:" in line]

        if ollama_failures:
            logger.warning(
                "  [marker] O modelo '%s' retornou uma resposta inválida para o Marker. "
                "O serviço Ollama respondeu, mas o conteúdo não pôde ser interpretado como JSON estruturado. "
                "Teste outro modelo em 'Modelo Ollama do Marker' ou desative o LLM do Marker.",
                _marker_ollama_model(ctx) or "(não configurado)",
            )

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Marker CLI falhou")[-4000:]
            logger.error("  [marker] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        if md_path and md_path.exists():
            try:
                marker_text = _sanitize_external_markdown_text(md_path.read_text(encoding="utf-8", errors="replace"))
                md_path.write_text(marker_text, encoding="utf-8")
            except Exception as e:
                logger.warning("  [marker] Falha ao sanitizar markdown gerado: %s", e)
        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
            "capabilities": caps,
            "page_range": marker_range,
            "stall_timeout": stall_timeout,
            "torch_device": {
                "configured": _marker_torch_device(ctx) or "auto",
                "effective": marker_torch_device,
            },
            "llm": llm_metadata,
            "ollama_failures": ollama_failures[-20:],
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Marker CLI."],
        )

    def _run_chunked_marker(
        self,
        ctx: BackendContext,
        out_dir: Path,
        caps: Dict[str, object],
        stall_timeout: int,
    ) -> BackendRunResult:
        chunk_size = _marker_chunk_size_for_workload(ctx)
        chunks = _build_marker_page_chunks(ctx.pages, ctx.report.page_count, chunk_size=chunk_size)
        if len(chunks) <= 1:
            return self._run_single_marker(ctx, out_dir, caps, ctx.pages, stall_timeout)

        logger.info(
            "  [marker] Documento grande/pesado; processando em %d chunks de até %d páginas.",
            len(chunks),
            chunk_size,
        )
        logger.info(
            "  [marker] Chunk policy: %d páginas por chunk para %d páginas selecionadas.",
            chunk_size,
            _selected_page_count(ctx),
        )
        combined_path = out_dir / f"{ctx.entry_id}.md"
        combined_parts: List[str] = []
        chunk_meta = []

        for idx, chunk_pages in enumerate(chunks, start=1):
            chunk_dir = out_dir / f"chunk-{idx:03d}"
            logger.info(
                "  [marker] Chunk %d/%d — páginas %d-%d",
                idx, len(chunks), chunk_pages[0] + 1, chunk_pages[-1] + 1,
            )
            result = self._run_single_marker(ctx, chunk_dir, caps, chunk_pages, stall_timeout)
            if result.status != "ok" or not result.markdown_path:
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    command=result.command,
                    error=f"Chunk {idx}/{len(chunks)} falhou: {result.error or 'sem markdown gerado'}",
                )

            md_abs = ctx.root_dir / result.markdown_path
            try:
                chunk_text = _sanitize_external_markdown_text(
                    md_abs.read_text(encoding="utf-8", errors="replace")
                )
            except Exception as e:
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    error=f"Falha ao ler markdown do chunk {idx}: {e}",
                )

            chunk_body = _strip_frontmatter_block(chunk_text).strip()
            chunk_body = _rewrite_markdown_asset_paths(chunk_body, md_abs.parent, combined_path.parent)
            combined_parts.append(
                f"<!-- MARKER_CHUNK {idx}: pages {chunk_pages[0] + 1}-{chunk_pages[-1] + 1} -->\n\n{chunk_body}"
            )
            chunk_meta.append({
                "chunk_index": idx,
                "page_range": pages_to_marker_range(chunk_pages),
                "markdown_path": result.markdown_path,
                "metadata_path": result.metadata_path,
            })

        write_text(combined_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, "\n\n".join(part for part in combined_parts if part).strip() + "\n"))

        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "capabilities": caps,
            "stall_timeout": stall_timeout,
            "chunked": True,
            "chunks": chunk_meta,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(combined_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=["Saída avançada gerada com Marker CLI em chunks."],
        )

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "marker" / ctx.entry_id
        ensure_dir(out_dir)

        caps = _detect_marker_capabilities()
        stall_timeout = _advanced_cli_stall_timeout("marker", ctx)
        effective_profile = (
            ctx.entry.document_profile
            if ctx.entry.document_profile != "auto"
            else ctx.report.suggested_profile
        )
        supports_chunking = bool(caps.get("page_range_flag"))
        selected_page_count = _selected_page_count(ctx)
        chunk_size = _marker_chunk_size_for_workload(ctx)
        chunking_mode = getattr(ctx, "marker_chunking_mode", "fallback")
        chunking_would_help = (
            effective_profile in {"math_heavy", "diagram_heavy"}
            and selected_page_count > chunk_size
            and supports_chunking
        )
        should_chunk = chunking_mode == "always" and chunking_would_help
        logger.info(
            "  [marker] Stall timeout efetivo: %ss para %d páginas selecionadas.",
            stall_timeout,
            selected_page_count,
        )

        logger.info(
            "  [marker] Chunking mode=%s (supports_chunking=%s, policy_match=%s).",
            chunking_mode,
            supports_chunking,
            chunking_would_help,
        )
        if should_chunk:
            result = self._run_chunked_marker(ctx, out_dir, caps, stall_timeout)
        else:
            result = self._run_single_marker(ctx, out_dir, caps, ctx.pages, stall_timeout)
            if (
                result.status == "error"
                and chunking_mode == "fallback"
                and chunking_would_help
                and result.error
                and "travou (sem output por" in result.error
            ):
                logger.warning("  [marker] Timeout detectado; repetindo em chunks como fallback.")
                result = self._run_chunked_marker(ctx, out_dir, caps, stall_timeout)

        if result.status == "ok":
            return result

        if DOCLING_CLI:
            logger.warning("  [marker] Falhou; tentando fallback para docling: %s", result.error)
            fallback = DoclingCLIBackend().run(ctx)
            if fallback.status == "ok":
                fallback.notes.append("Fallback automático após falha do Marker.")
            return fallback

        return result


# ---------------------------------------------------------------------------
# Selection / profiling
# ---------------------------------------------------------------------------

class BackendSelector:
    def __init__(self):
        self.backends: Dict[str, ExtractionBackend] = {
            "pymupdf4llm": PyMuPDF4LLMBackend(),
            "pymupdf": PyMuPDFBackend(),
            "datalab": DatalabCloudBackend(),
            "docling": DoclingCLIBackend(),
            "docling_python": DoclingPythonBackend(),
            "marker": MarkerCLIBackend(),
        }

    def available_backends(self) -> Dict[str, bool]:
        return {name: backend.available() for name, backend in self.backends.items()}

    def decide(self, entry: FileEntry, report: DocumentProfileReport) -> PipelineDecision:
        mode = entry.processing_mode or "auto"
        effective_profile = _effective_document_profile(entry.document_profile, report.suggested_profile)
        reasons: List[str] = []

        available = self.available_backends()

        def pick_first(names: Iterable[str]) -> Optional[str]:
            for name in names:
                if available.get(name):
                    return name
            return None

        def pick_advanced_for_profile(profile: str) -> Optional[str]:
            if profile == "math_heavy":
                return pick_first(["datalab", "marker", "docling"])
            if profile == "diagram_heavy":
                return pick_first(["docling", "marker"])
            return pick_first(["docling", "marker"])

        base_backend: Optional[str] = None
        advanced_backend: Optional[str] = None

        if entry.preferred_backend != "auto" and available.get(entry.preferred_backend):
            preferred = entry.preferred_backend
            if preferred in {"datalab", "docling", "docling_python", "marker"}:
                advanced_backend = preferred
                base_backend = pick_first(["pymupdf4llm", "pymupdf"])
                reasons.append(f"Backend preferido manualmente: {preferred}.")
            else:
                base_backend = preferred
                reasons.append(f"Backend base preferido manualmente: {preferred}.")

        if mode == "quick":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            reasons.append("Modo quick prioriza velocidade e baixo custo.")

        elif mode == "manual_assisted":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
            reasons.append("Modo manual_assisted gera base automática e exige revisão humana guiada.")

        elif mode == "high_fidelity":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile == "math_heavy":
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append("Documento math_heavy pede backend avançado com enrich-formula.")
            elif effective_profile in {"diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append("Documento visual/scanned pede backend avançado.")
            else:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                if advanced_backend:
                    reasons.append("Modo high_fidelity tenta saída avançada além da base.")

        else:  # auto
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append(f"Modo auto detectou perfil {effective_profile} e ativou camada avançada.")
            else:
                reasons.append("Modo auto detectou documento comum; saída base é suficiente.")

        if entry.formula_priority and not advanced_backend:
            advanced_backend = pick_advanced_for_profile(effective_profile)
            if advanced_backend:
                reasons.append("formula_priority ativou backend avançado.")

        if not base_backend and advanced_backend:
            reasons.append("Sem backend base disponível; usando apenas backend avançado.")

        return PipelineDecision(
            entry_id=entry.id(),
            processing_mode=mode,
            effective_profile=effective_profile,
            base_backend=base_backend,
            advanced_backend=advanced_backend,
            reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Repo builder
# ---------------------------------------------------------------------------

class RepoBuilder:
    HAS_PYMUPDF = HAS_PYMUPDF
    HAS_PDFPLUMBER = HAS_PDFPLUMBER

    def __init__(self, root_dir: Path, course_meta: Dict[str, str], entries: List[FileEntry],
                 options: Dict[str, object], *,
                 student_profile: Optional[StudentProfile] = None,
                 subject_profile: Optional[SubjectProfile] = None,
                 progress_callback=None):
        self.root_dir = root_dir
        self.course_meta = course_meta
        self.entries = entries
        self.options = options
        self.student_profile = student_profile
        self.subject_profile = subject_profile
        self.progress_callback = progress_callback  # Callable[[int, int, str], None] | None
        self.logs: List[Dict[str, object]] = []
        self.selector = BackendSelector()

    def _effective_course_meta(self, manifest: Optional[Dict[str, object]] = None) -> Dict[str, str]:
        return _repo_artifacts.effective_course_meta(
            self.course_meta,
            self.root_dir,
            manifest=manifest,
        )

    def _sleep_guard(self, reason: str):
        return prevent_system_sleep(
            enabled=bool(self.options.get("prevent_sleep_during_build", True)),
            reason=reason,
        )

    def build(self) -> None:
        with self._sleep_guard("build do repositorio"):
            self._build_impl()

    def _build_impl(self) -> None:
        logger.info("Building repository at %s", self.root_dir)
        logger.info("Creating directory structure...")
        self._create_structure()
        logger.info("Writing root/pedagogical files...")
        self._write_root_files()
        logger.info("Root files written. Starting entry processing...")

        manifest = {
            "app": APP_NAME,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "course": self.course_meta,
            "options": self.options,
            "environment": {
                "python": sys.version.split()[0],
                "pymupdf": HAS_PYMUPDF,
                "pymupdf4llm": HAS_PYMUPDF4LLM,
                "pdfplumber": HAS_PDFPLUMBER,
                "datalab_api": has_datalab_api_key(),
                "docling_cli": bool(DOCLING_CLI),
                "docling_python": has_docling_python_api(),
                "marker_cli": bool(MARKER_CLI),
            },
            "entries": [],
        }

        manifest_path = self.root_dir / "manifest.json"
        active_entries = [e for e in self.entries if getattr(e, "enabled", True)]
        skipped = len(self.entries) - len(active_entries)
        if skipped:
            logger.info("Pulando %d entries desabilitados.", skipped)
        total = len(active_entries)
        for i, entry in enumerate(active_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if self.progress_callback:
                self.progress_callback(i, total, entry.title)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)
            # Salva manifest após cada entry para não perder progresso
            manifest["logs"] = self.logs
            manifest = self._compact_manifest(manifest)
            write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
            logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
        if self.progress_callback:
            self.progress_callback(total, total, "")

        manifest["logs"] = self.logs
        manifest = self._compact_manifest(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

        # FILE_MAP — generated after all entries are processed
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(
                       {**self.course_meta, "_repo_root": self.root_dir},
                       manifest["entries"],
                       self.subject_profile,
                   ))

        # Resolve image references in markdowns → content/images/
        self._resolve_content_images()
        self._inject_all_image_descriptions()
        self._regenerate_pedagogical_files(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

        logger.info("Repository built successfully at %s", self.root_dir)

    def _create_structure(self) -> None:
        _bootstrap_ops_create_structure(self.root_dir)

    def _write_root_files(self) -> None:
        _bootstrap_ops_write_root_files(
            self,
            tutor_policy_md_fn=tutor_policy_md,
            pedagogy_md_fn=pedagogy_md,
            modes_md_fn=modes_md,
            output_templates_md_fn=output_templates_md,
            pdf_curation_guide_fn=pdf_curation_guide,
            backend_architecture_md_fn=backend_architecture_md,
            backend_policy_yaml_fn=backend_policy_yaml,
            course_map_md_fn=course_map_md,
            glossary_md_fn=glossary_md,
            student_state_md_fn=student_state_md,
            progress_schema_md_fn=progress_schema_md,
            student_profile_md_fn=student_profile_md,
            syllabus_md_fn=syllabus_md,
            bibliography_md_fn=bibliography_md,
            exam_index_md_fn=exam_index_md,
            exercise_index_md_fn=exercise_index_md,
            assignment_index_md_fn=assignment_index_md,
            code_index_md_fn=code_index_md,
            whiteboard_index_md_fn=whiteboard_index_md,
            root_readme_fn=root_readme,
            generated_repo_gitignore_text_fn=_generated_repo_gitignore_text,
            generate_claude_project_instructions_fn=generate_claude_project_instructions,
            generate_gpt_instructions_fn=generate_gpt_instructions,
            generate_gemini_instructions_fn=generate_gemini_instructions,
            exam_categories=EXAM_CATEGORIES,
            exercise_categories=EXERCISE_CATEGORIES,
            assignment_categories=ASSIGNMENT_CATEGORIES,
            code_categories=CODE_CATEGORIES,
            whiteboard_categories=WHITEBOARD_CATEGORIES,
        )

    # ------------------------------------------------------------------
    # Image resolution — copies referenced images into content/images/
    # ------------------------------------------------------------------

    _IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def _resolve_content_images(self) -> None:
        """Scan markdowns under content/ and staging/markdown-auto/ for image
        references.  Copy each referenced image into ``content/images/`` with a
        short, deterministic name and rewrite the markdown link to a relative
        path.  This keeps the repo uploadable to Claude Projects without
        thousands of staging assets.

        Incremental: keeps existing images and only copies new ones.
        Stale images (from removed entries) are cleaned up at the end.
        """
        images_dir = self.root_dir / "content" / "images"
        ensure_dir(images_dir)

        # Track existing files for stale cleanup later
        existing_files = {f for f in images_dir.iterdir() if f.is_file()} if images_dir.exists() else set()
        referenced_files: set = set()

        # Directories to scan for markdowns that the tutor will read
        scan_dirs = [
            self.root_dir / "content",
            self.root_dir / "staging" / "markdown-auto",
        ]

        target_ext = f".{self._image_format}" if self._image_format != "jpeg" else ".jpg"
        seen: Dict[str, Path] = {}  # original_path -> new_path (dedup)
        copied = 0

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for md_file in scan_dir.rglob("*.md"):
                # Skip markdowns inside content/images/ itself
                if images_dir in md_file.parents:
                    continue
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                replacements: List[tuple] = []
                for match in self._IMG_RE.finditer(text):
                    alt = match.group(1)
                    raw_path = match.group(2)

                    # Skip references already pointing to content/images/
                    if "content/images/" in raw_path.replace("\\", "/"):
                        # Track the file as referenced so it doesn't get cleaned up
                        ref_path = self._find_image(raw_path, md_file)
                        if ref_path and ref_path.exists():
                            referenced_files.add(ref_path)
                        continue

                    # Resolve the image file
                    img_path = self._find_image(raw_path, md_file)
                    if img_path is None or not img_path.exists():
                        continue

                    # Skip noise images (too small or solid color)
                    if img_path.stat().st_size < self._MIN_IMG_BYTES:
                        continue
                    if self._is_noise_image(img_path.read_bytes()):
                        continue

                    img_key = str(img_path)
                    if img_key in seen:
                        new_path = seen[img_key]
                    else:
                        # Build a short name: <parent-slug>-<filename>
                        parent_slug = slugify(img_path.parent.name) if img_path.parent.name else ""
                        short_name = f"{parent_slug}-{img_path.name}" if parent_slug else img_path.name
                        new_path = images_dir / short_name

                        # Handle collisions
                        if new_path.exists() and new_path.stat().st_size != img_path.stat().st_size:
                            stem = new_path.stem
                            suffix = new_path.suffix
                            counter = 2
                            while new_path.exists():
                                new_path = images_dir / f"{stem}-{counter}{suffix}"
                                counter += 1

                        if not new_path.exists():
                            shutil.copy2(str(img_path), str(new_path))
                            new_path = self._convert_image_format(new_path)
                            copied += 1
                        elif new_path.suffix.lower() not in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
                            # Existing file in wrong format — convert
                            new_path = self._convert_image_format(new_path)
                        seen[img_key] = new_path

                    referenced_files.add(new_path)

                    # Build relative path from this markdown to the image
                    try:
                        rel = Path(new_path).relative_to(md_file.parent)
                    except ValueError:
                        # Different directory trees — use repo-relative path
                        rel = Path(new_path).relative_to(self.root_dir)

                    rel_str = str(rel).replace("\\", "/")
                    old_ref = match.group(0)
                    new_ref = f"![{alt}]({rel_str})"
                    if old_ref != new_ref:
                        replacements.append((old_ref, new_ref))

                if replacements:
                    for old, new in replacements:
                        text = text.replace(old, new)
                    md_file.write_text(text, encoding="utf-8")

        # Clean up stale images (from removed entries)
        stale = existing_files - referenced_files
        for f in stale:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        if stale:
            logger.info("Cleaned up %d stale images from content/images/", len(stale))

        if copied:
            logger.info("Resolved %d new images into content/images/", copied)

    def _find_image(self, raw_path: str, md_file: Path) -> Optional[Path]:
        """Try to locate an image file from a markdown reference path."""
        # Normalize separators
        normalized = raw_path.replace("\\", "/")

        # 1) Absolute path — use directly
        p = Path(normalized)
        if p.is_absolute() and p.exists():
            return p

        # 2) Try relative to the markdown file's directory
        rel_to_md = md_file.parent / normalized
        if rel_to_md.exists():
            return rel_to_md

        # 3) Try relative to repo root
        rel_to_root = self.root_dir / normalized
        if rel_to_root.exists():
            return rel_to_root

        # 4) Extract the staging-relative portion from absolute paths
        # Pattern: .../staging/assets/... or .../staging/markdown-auto/...
        for marker in ("staging/assets/", "staging/markdown-auto/"):
            idx = normalized.find(marker)
            if idx >= 0:
                staging_rel = normalized[idx:]
                candidate = self.root_dir / staging_rel
                if candidate.exists():
                    return candidate

        return None

    _IMG_DESC_BLOCK_RE = _IMAGE_DESC_BLOCK_RE
    _image_curation_heading = staticmethod(_image_curation_heading_label)

    @staticmethod
    def inject_image_descriptions(markdown: str, image_curation: dict) -> str:
        return _low_token_inject_image_descriptions(
            markdown,
            image_curation,
            desc_block_re=RepoBuilder._IMG_DESC_BLOCK_RE,
            image_heading=RepoBuilder._image_curation_heading,
        )

    def _inject_all_image_descriptions(self) -> None:
        """Inject image descriptions into the most relevant markdowns for each entry."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return

        entries = manifest.get("entries", [])

        injected_count = 0
        for entry_data in entries:
            curation = entry_data.get("image_curation")
            if not curation:
                continue

            status = (curation.get("status") or "").strip().lower()
            if status not in {"described", "curated"} and not curation.get("pages"):
                continue

            target_markdowns = self._resolve_entry_markdown_targets(entry_data)

            if not target_markdowns:
                content_dir = self.root_dir / "content"
                if not content_dir.exists():
                    continue
                target_markdowns = list(content_dir.rglob("*.md"))

            for md_file in target_markdowns:
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                new_text = self.inject_image_descriptions(text, curation)
                if new_text != text:
                    md_file.write_text(new_text, encoding="utf-8")
                    injected_count += 1
                    try:
                        rel_md = safe_rel(md_file, self.root_dir)
                    except Exception:
                        rel_md = str(md_file)
                    logger.info(
                        "Injected image descriptions into %s for entry %s.",
                        rel_md,
                        entry_data.get("id") or entry_data.get("title") or "<unknown>",
                    )

        if injected_count:
            logger.info("Injected image descriptions into %d markdown files.", injected_count)

    def _resolve_entry_markdown_targets(self, entry_data: dict) -> List[Path]:
        return _repo_artifacts.resolve_entry_markdown_targets(self.root_dir, entry_data)

    def _heal_manifest_markdown_paths(self, manifest: dict) -> dict:
        manifest, healed = _repo_artifacts.heal_manifest_markdown_paths(
            self.root_dir,
            manifest,
        )
        if healed:
            logger.info("Healed markdown targets for %d manifest entries.", healed)
        return manifest

    def _write_source_registry(self, manifest: Dict[str, object]) -> None:
        _operational_artifacts_write_source_registry(
            self.root_dir,
            manifest,
            write_text_fn=write_text,
            repo_artifacts_module=_repo_artifacts,
        )

    def _write_bundle_seed(self, manifest: Dict[str, object]) -> None:
        _operational_artifacts_write_bundle_seed(
            self.root_dir,
            manifest,
            course_meta=self._effective_course_meta(manifest),
            bundle_priority_score_fn=_bundle_priority_score,
            bundle_seed_candidate_fn=_bundle_seed_candidate,
            write_text_fn=write_text,
            repo_artifacts_module=_repo_artifacts,
        )

    def _write_build_report(self, manifest: Dict[str, object]) -> None:
        platform = (
            getattr(self, "_selected_platform", None)
            or getattr(self.subject_profile, "preferred_llm", "claude")
            or "claude"
        )
        _operational_artifacts_write_build_report(
            self.root_dir,
            manifest,
            preferred_platform=platform,
            has_pymupdf=HAS_PYMUPDF,
            has_pymupdf4llm=HAS_PYMUPDF4LLM,
            has_pdfplumber=HAS_PDFPLUMBER,
            has_datalab_api_key_fn=has_datalab_api_key,
            docling_cli=DOCLING_CLI,
            has_docling_python_api_fn=has_docling_python_api,
            marker_cli=MARKER_CLI,
            write_text_fn=write_text,
            repo_artifacts_module=_repo_artifacts,
        )

    def _remove_entry_consolidated_images(self, entry_id: str) -> int:
        """Remove consolidated content/images assets that belong to one entry."""
        if not entry_id:
            return 0

        removed_count = 0
        images_dir = self.root_dir / "content" / "images"
        if not images_dir.exists():
            return 0

        entry_prefix = entry_id.lower()
        for img_path in images_dir.iterdir():
            if not img_path.is_file():
                continue
            lower_name = img_path.name.lower()
            if not (
                lower_name == entry_prefix
                or lower_name.startswith(entry_prefix + "-")
                or lower_name.startswith(entry_prefix + "_")
            ):
                continue
            try:
                img_path.unlink()
                removed_count += 1
            except Exception as e:
                logger.warning("Could not remove consolidated image %s: %s", img_path, e)

        scanned_dir = images_dir / "scanned" / entry_id
        if scanned_dir.exists():
            try:
                shutil.rmtree(scanned_dir)
                removed_count += 1
            except Exception as e:
                logger.warning("Could not remove scanned image dir %s: %s", scanned_dir, e)

        return removed_count

    def _process_entry(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "id": entry.id(),
            "title": entry.title,
            "category": entry.category,
            "file_type": entry.file_type,
            "source_path": entry.source_path,
            "tags": entry.tags,
            "manual_tags": list(entry.manual_tags or []),
            "auto_tags": list(entry.auto_tags or []),
            "manual_unit_slug": entry.manual_unit_slug,
            "manual_timeline_block_id": entry.manual_timeline_block_id,
            "notes": entry.notes,
            "professor_signal": entry.professor_signal,
            "include_in_bundle": entry.include_in_bundle,
            "relevant_for_exam": entry.relevant_for_exam,
            "processing_mode": entry.processing_mode,
            "document_profile": entry.document_profile,
            "preferred_backend": entry.preferred_backend,
            "datalab_mode": entry.datalab_mode,
            "formula_priority": entry.formula_priority,
            "preserve_pdf_images_in_markdown": entry.preserve_pdf_images_in_markdown,
            "force_ocr": entry.force_ocr,
            "extract_images": entry.extract_images,
            "extract_tables": entry.extract_tables,
            "page_range": entry.page_range,
            "ocr_language": entry.ocr_language,
        }

        src = Path(entry.source_path)
        if entry.file_type not in ("url", "github-repo") and not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        if entry.file_type == "url":
            item.update(self._process_url(entry))
            return item

        if entry.file_type == "github-repo":
            item.update(self._process_github_repo(entry))
            return item

        safe_name = f"{entry.id()}{src.suffix.lower()}"

        if entry.file_type == "code":
            code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
            raw_target  = self.root_dir / "raw" / "code" / code_subdir / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_code(entry, raw_target))
            return item

        if entry.file_type == "zip":
            raw_target = self.root_dir / "raw" / "zip" / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_zip(entry, raw_target))
            return item

        if entry.file_type == "pdf":
            raw_target = self.root_dir / "raw" / "pdfs" / entry.category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_pdf(entry, raw_target))
        else:
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "outros"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_url(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None, "pipeline_decision": None,
            "base_markdown": None, "advanced_markdown": None,
            "advanced_backend": None, "base_backend": "url_fetcher",
            "manual_review": None,
        }
        url_dest = self.root_dir / "staging" / "markdown-auto" / "url_fetcher"
        ensure_dir(url_dest)
        md_file = url_dest / f"{entry.id()}.md"
        url = entry.source_path
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                charset = response.info().get_content_charset('utf-8')
                html = response.read().decode(charset, errors='replace')
            try:
                markdown_content = _html_to_structured_markdown(html, url, entry.title)
            except ImportError:
                markdown_content = (
                    f"# {entry.title}\n\n"
                    f"- URL: [{url}]({url})\n\n"
                    "> BeautifulSoup não instalado. Conteúdo HTML não foi convertido para Markdown estruturado.\n"
                )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "ok"})
        except Exception as e:
            logger.warning(f"Failed to fetch content from URL {url}: {e}")
            markdown_content = (
                f"# {entry.title}\n\n"
                f"- URL: [{url}]({url})\n\n"
                f"> Não foi possível carregar o conteúdo: {e}\n"
            )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "error", "error": str(e)})
        write_text(md_file, markdown_content)
        item["base_markdown"] = safe_rel(md_file, self.root_dir)
        manual = self.root_dir / "manual-review" / "web" / f"{entry.id()}.md"
        write_text(manual, manual_url_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _check_cancel(self):
        """Levanta InterruptedError se o build foi cancelado."""
        if self.progress_callback:
            # O progress_callback da UI verifica o cancel_event e levanta InterruptedError
            try:
                self.progress_callback(-1, -1, "")
            except InterruptedError:
                raise

    @staticmethod
    def _quick_page_count(pdf_path: Path) -> int:
        return _pdf_analysis_quick_page_count(
            pdf_path,
            has_pymupdf=HAS_PYMUPDF,
            pymupdf_module=pymupdf if HAS_PYMUPDF else None,
        )

    def _apply_math_normalization(self, md_rel_path: Optional[str]) -> None:
        _pdf_analysis_apply_math_normalization(
            self.root_dir,
            md_rel_path,
            normalize_unicode_math_fn=_normalize_unicode_math,
        )

    
    def _render_scanned_pdf_as_images(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        return _pdf_scanned_render_scanned_pdf_as_images(
            self.root_dir,
            entry,
            raw_target,
            has_pymupdf=HAS_PYMUPDF,
            pymupdf_module=pymupdf if HAS_PYMUPDF else None,
            wrap_frontmatter_fn=wrap_frontmatter,
        )
        



    def _process_pdf(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        return _pdf_pipeline_process_pdf(
            self,
            entry,
            raw_target,
            backend_context_factory=BackendContext,
            manual_pdf_review_template_fn=manual_pdf_review_template,
            detect_latex_corruption_fn=_detect_latex_corruption,
            hybridize_marker_markdown_with_base_fn=_hybridize_marker_markdown_with_base,
        )

    def _process_image(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        return _source_importers_process_image(self, entry, raw_target)

    def _process_code(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        return _source_importers_process_code(self, entry, raw_target)

    def _process_zip(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        return _source_importers_process_zip(self, entry, raw_target)

    def _process_github_repo(self, entry: FileEntry) -> Dict[str, object]:
        return _source_importers_process_github_repo(self, entry)

    def _profile_pdf(self, pdf_path: Path, entry: FileEntry) -> DocumentProfileReport:
        return _pdf_analysis_profile_pdf(
            pdf_path,
            entry,
            has_pymupdf=HAS_PYMUPDF,
            pymupdf_module=pymupdf if HAS_PYMUPDF else None,
        )

    def _log_backend_result(self, entry_id: str, result: BackendRunResult) -> None:
        _pdf_pipeline_log_backend_result(self.logs, entry_id, result)

    # Minimum thresholds to skip noise images (tiny icons, solid-color rects, etc.)
    _MIN_IMG_BYTES = 2000     # < 2 KB is almost always an artifact
    _MIN_IMG_DIMENSION = 20   # width or height < 20px
    _MAX_ASPECT_RATIO = 8.0   # extreme aspect ratios are banners/bars (e.g. 1500x74)
    _MAX_NOISE_COLORS = 4     # images with ≤4 unique colors are decorative

    @staticmethod
    def _is_noise_image(data: bytes) -> bool:
        return _pdf_assets_is_noise_image(
            data,
            max_aspect_ratio=RepoBuilder._MAX_ASPECT_RATIO,
            max_noise_colors=RepoBuilder._MAX_NOISE_COLORS,
        )

    @staticmethod
    def _should_keep_extracted_pdf_image(
        *,
        data: bytes,
        width: int,
        height: int,
        policy: Dict[str, object],
    ) -> bool:
        return _pdf_assets_should_keep_extracted_pdf_image(
            data=data,
            width=width,
            height=height,
            policy=policy,
            is_noise_image_fn=RepoBuilder._is_noise_image,
        )

    @property
    def _image_format(self) -> str:
        return _pdf_assets_image_format(self.options)

    def _convert_image_format(self, src: Path) -> Path:
        return _pdf_assets_convert_image_format(src, options=self.options)

    def _extract_pdf_images(
        self,
        pdf_path: Path,
        out_dir: Path,
        pages: Optional[List[int]] = None,
        ctx: Optional[BackendContext] = None,
    ) -> int:
        policy = _pdf_image_extraction_policy(ctx) if ctx is not None else {
            "mode": "standard",
            "min_bytes": self._MIN_IMG_BYTES,
            "min_dimension": self._MIN_IMG_DIMENSION,
            "max_aspect_ratio": self._MAX_ASPECT_RATIO,
            "keep_low_color": False,
        }
        return _pdf_assets_extract_pdf_images(
            pdf_path,
            out_dir,
            pymupdf_module=pymupdf,
            pages=pages,
            policy=policy,
            should_keep_image_fn=self._should_keep_extracted_pdf_image,
        )

    def _extract_tables_pdfplumber(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        return _pdf_assets_extract_tables_pdfplumber(
            pdf_path,
            out_dir,
            pdfplumber_module=pdfplumber,
            pages=pages,
        )

    def _detect_tables_pymupdf(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        return _pdf_assets_detect_tables_pymupdf(
            pdf_path,
            out_dir,
            pymupdf_module=pymupdf,
            pages=pages,
        )

    def _pdf_image_extraction_policy(self, ctx: BackendContext) -> Dict[str, object]:
        return _pdf_image_extraction_policy(ctx)

    def _compact_manifest(self, manifest: dict) -> dict:
        return _operational_artifacts_compact_manifest(
            self.root_dir,
            manifest,
            filter_live_manifest_entries_fn=_filter_live_manifest_entries,
            heal_manifest_markdown_paths_fn=_repo_artifacts.heal_manifest_markdown_paths,
            manifest_log_limit=_MANIFEST_LOG_LIMIT,
            repo_artifacts_module=_repo_artifacts,
        )

    def incremental_build(self) -> None:
        with self._sleep_guard("build incremental do repositorio"):
            self._incremental_build_impl()

    def _incremental_build_impl(self) -> None:
        _incremental_build_incremental_build_impl(
            self,
            student_state_md_fn=student_state_md,
            progress_schema_md_fn=progress_schema_md,
        )

    def _derive_active_unit_slug_from_state(self) -> str:
        state = self.root_dir / "student" / "STUDENT_STATE.md"
        if not state.exists():
            return ""
        text = state.read_text(encoding="utf-8")
        m = re.search(r"active:\s*\n(?:.*\n)*?\s*unit:\s*(\S+)", text)
        return m.group(1).strip() if m else ""

    def _ensure_unit_battery_directories(self) -> None:
        teaching_plan = getattr(self.subject_profile, "teaching_plan", "") or ""
        if not teaching_plan:
            return
        batteries_root = self.root_dir / "student" / "batteries"
        for title, _topics in _parse_units_from_teaching_plan(teaching_plan):
            slug = slugify(title)
            if slug:
                (batteries_root / slug).mkdir(parents=True, exist_ok=True)

    def _regenerate_pedagogical_files(self, manifest: dict) -> None:
        _pedagogical_regeneration_regenerate_pedagogical_files(
            self,
            manifest,
            filter_live_manifest_entries_fn=_filter_live_manifest_entries,
            build_file_map_content_taxonomy_from_course_fn=_build_file_map_content_taxonomy_from_course,
            write_internal_content_taxonomy_fn=_write_internal_content_taxonomy,
            build_file_map_timeline_context_from_course_fn=_build_file_map_timeline_context_from_course,
            persist_enriched_timeline_index_fn=_persist_enriched_timeline_index,
            empty_timeline_index_fn=_empty_timeline_index,
            build_assessment_context_from_course_fn=_build_assessment_context_from_course,
            write_internal_assessment_context_fn=_write_internal_assessment_context,
            generate_claude_project_instructions_fn=generate_claude_project_instructions,
            generate_gpt_instructions_fn=generate_gpt_instructions,
            generate_gemini_instructions_fn=generate_gemini_instructions,
            tutor_policy_md_fn=tutor_policy_md,
            pedagogy_md_fn=pedagogy_md,
            modes_md_fn=modes_md,
            output_templates_md_fn=output_templates_md,
            root_readme_fn=root_readme,
            generated_repo_gitignore_text_fn=_generated_repo_gitignore_text,
            course_map_md_fn=course_map_md,
            glossary_md_fn=glossary_md,
            write_tag_catalog_fn=_write_tag_catalog,
            refresh_manifest_auto_tags_fn=_refresh_manifest_auto_tags,
            syllabus_md_fn=syllabus_md,
            exam_index_md_fn=exam_index_md,
            exercise_index_md_fn=exercise_index_md,
            bibliography_md_fn=bibliography_md,
            assignment_index_md_fn=assignment_index_md,
            code_index_md_fn=code_index_md,
            whiteboard_index_md_fn=whiteboard_index_md,
            file_map_md_fn=file_map_md,
            student_profile_md_fn=student_profile_md,
            student_state_md_fn=student_state_md,
            progress_schema_md_fn=progress_schema_md,
            parse_units_from_teaching_plan_fn=_parse_units_from_teaching_plan,
            topic_text_fn=_topic_text,
            inject_executive_summary_fn=_inject_executive_summary,
            exam_categories=EXAM_CATEGORIES,
            exercise_categories=EXERCISE_CATEGORIES,
            assignment_categories=ASSIGNMENT_CATEGORIES,
            code_categories=CODE_CATEGORIES,
            whiteboard_categories=WHITEBOARD_CATEGORIES,
        )

    def process_single(self, entry: "FileEntry", force: bool = False) -> str:
        with self._sleep_guard(f"processamento de {entry.title}"):
            return self._process_single_impl(entry, force=force)

    def _process_single_impl(self, entry: "FileEntry", force: bool = False) -> str:
        return _lifecycle_ops_process_single_impl(
            self,
            entry,
            force=force,
            app_name=APP_NAME,
            has_pymupdf=HAS_PYMUPDF,
            has_pymupdf4llm=HAS_PYMUPDF4LLM,
            has_pdfplumber=HAS_PDFPLUMBER,
            has_datalab_api_key_fn=has_datalab_api_key,
            docling_cli=DOCLING_CLI,
            has_docling_python_api_fn=has_docling_python_api,
            marker_cli=MARKER_CLI,
        )

    def unprocess(self, entry_id: str) -> bool:
        return _lifecycle_ops_unprocess(self, entry_id)

    def reject(self, entry_id: str) -> Optional[Dict[str, object]]:
        return _lifecycle_ops_reject(self, entry_id)


# ---------------------------------------------------------------------------
# Free functions — Pedagogical file generators
# ---------------------------------------------------------------------------

_TEACHING_PLAN_SECTION_STOP = re.compile(
    r'^(?:PROCEDIMENTOS|AVALIA[ÇC][AÃ]O|BIBLIOGRAFIA|METODOLOGIA)',
    re.IGNORECASE,
)

_normalize_teaching_plan_heading = _teaching_plan_normalize_heading
_parse_units_from_teaching_plan = _teaching_plan_parse_units_from_teaching_plan
_topic_text = _teaching_plan_topic_text
_topic_depth = _teaching_plan_topic_depth


def _match_timeline_to_units_generic(
    timeline: List[Dict[str, str]],
    units: list,
) -> list:
    return _timeline_match_timeline_to_units_generic(
        timeline,
        units,
        normalize_unit_slug=_normalize_unit_slug,
        topic_text=_topic_text,
    )


_match_timeline_to_units = _match_timeline_to_units_generic


_score_text_against_row = _entry_signals_score_text_against_row
_timeline_block_rows_for_scoring = _file_map_timeline_block_rows_for_scoring
_timeline_block_matches_preferred_topic = _file_map_timeline_block_matches_preferred_topic


_score_card_evidence_against_entry = lambda signals, card_items: _file_map_score_card_evidence_against_entry(
    signals,
    card_items,
    normalize_match_text=_normalize_match_text,
)


_score_entry_against_timeline_block = lambda signals, block, preferred_unit_slug="", preferred_topic_slug="": _file_map_score_entry_against_timeline_block(
    signals,
    block,
    normalize_match_text=_normalize_match_text,
    score_text_against_row=_score_text_against_row,
    score_card_evidence_against_entry_fn=_score_card_evidence_against_entry,
    preferred_unit_slug=preferred_unit_slug,
    preferred_topic_slug=preferred_topic_slug,
)


_select_probable_period_for_entry = lambda entry, unit, candidate_rows, markdown_text, preferred_topic_slug="": _file_map_select_probable_period_for_entry(
    entry,
    unit,
    candidate_rows,
    markdown_text,
    preferred_topic_slug=preferred_topic_slug,
    collect_entry_unit_signals=_collect_entry_unit_signals,
    build_timeline_index=_build_timeline_index,
    timeline_period_label=_timeline_period_label,
    collapse_ws=_collapse_ws,
    normalize_match_text=_normalize_match_text,
    score_text_against_row=_score_text_against_row,
    extract_date_range_signal=extract_date_range_signal,
    extract_timeline_session_signals=extract_timeline_session_signals,
    parse_timeline_date_value=_parse_timeline_date_value,
)

_aggregate_unit_periods_from_blocks = _timeline_aggregate_unit_periods_from_blocks


_build_file_map_timeline_context_from_course = lambda course_meta, subject_profile=None, content_taxonomy=None: _timeline_build_file_map_timeline_context_from_course(
    course_meta,
    subject_profile,
    content_taxonomy,
    build_file_map_unit_index_from_course=_build_file_map_unit_index_from_course,
    build_file_map_content_taxonomy_from_course=_build_file_map_content_taxonomy_from_course,
)


_parse_bibliography_from_teaching_plan = _teaching_plan_parse_bibliography_from_teaching_plan


_build_assessment_context_from_course = lambda course_meta, subject_profile=None, timeline_context=None: _timeline_build_assessment_context_from_course(
    course_meta,
    subject_profile,
    timeline_context,
    build_file_map_unit_index_from_course=_build_file_map_unit_index_from_course,
    build_file_map_timeline_context_from_course=_build_file_map_timeline_context_from_course,
    normalize_match_text=_normalize_match_text,
    normalize_teaching_plan_heading=_normalize_teaching_plan_heading,
)


_write_internal_assessment_context = partial(
    _repo_artifacts.write_internal_assessment_context,
    write_text_fn=write_text,
)


_assessment_conflict_section_lines = _repo_artifacts.assessment_conflict_section_lines


syllabus_md = _repo_artifacts.syllabus_md
student_profile_md = _repo_artifacts.student_profile_md


glossary_md = lambda course_meta, subject_profile=None, *, root_dir=None, manifest_entries=None: _repo_artifacts.glossary_md(
    course_meta,
    subject_profile,
    root_dir=root_dir,
    manifest_entries=manifest_entries,
    parse_units_from_teaching_plan_fn=_parse_units_from_teaching_plan,
    topic_text_fn=_topic_text,
    collect_glossary_evidence_fn=_collect_glossary_evidence,
    find_glossary_evidence_fn=_find_glossary_evidence,
    seed_glossary_fields_fn=lambda term, unit_title, evidence="": _seed_glossary_fields(
        term,
        unit_title,
        evidence=evidence,
    ),
    clamp_navigation_artifact_fn=_clamp_navigation_artifact,
)

_clamp_navigation_artifact = _repo_artifacts.clamp_navigation_artifact
_glossary_tokens = _repo_artifacts.glossary_tokens


_extract_markdown_headings = partial(
    _repo_artifacts.extract_markdown_headings,
    collapse_ws=_collapse_ws,
)
_trim_glossary_prefix = partial(
    _repo_artifacts.trim_glossary_prefix,
    collapse_ws=_collapse_ws,
)


_shorten_glossary_sentence = lambda sentence, max_chars=180: _repo_artifacts.shorten_glossary_sentence(
    sentence,
    collapse_ws=_collapse_ws,
    max_chars=max_chars,
)


_is_bad_glossary_evidence = partial(
    _repo_artifacts.is_bad_glossary_evidence,
    collapse_ws=_collapse_ws,
)

_collect_glossary_evidence = lambda root_dir, manifest_entries=None: _repo_artifacts.collect_glossary_evidence(
    root_dir,
    manifest_entries=manifest_entries,
    collapse_ws=_collapse_ws,
    strip_frontmatter_block=_strip_frontmatter_block,
    extract_markdown_headings_fn=_extract_markdown_headings,
)

_find_glossary_evidence = partial(
    _repo_artifacts.find_glossary_evidence,
    glossary_tokens_fn=_glossary_tokens,
    best_glossary_sentence_fn=lambda term, unit_title, doc: _best_glossary_sentence(term, unit_title, doc),
)
_best_glossary_sentence = partial(
    _repo_artifacts.best_glossary_sentence,
    collapse_ws=_collapse_ws,
    glossary_tokens_fn=_glossary_tokens,
    trim_glossary_prefix_fn=_trim_glossary_prefix,
    is_bad_glossary_evidence_fn=_is_bad_glossary_evidence,
    normalize_glossary_sentence_fn=lambda term, unit_title, sentence: _normalize_glossary_sentence(term, unit_title, sentence),
    shorten_glossary_sentence_fn=_shorten_glossary_sentence,
)
_normalize_glossary_sentence = partial(
    _repo_artifacts.normalize_glossary_sentence,
    collapse_ws=_collapse_ws,
    shorten_glossary_sentence_fn=_shorten_glossary_sentence,
)
_seed_glossary_fields = partial(
    _repo_artifacts.seed_glossary_fields,
    collapse_ws=_collapse_ws,
    refine_glossary_definition_from_evidence_fn=lambda term, unit_hint, evidence: _refine_glossary_definition_from_evidence(term, unit_hint, evidence),
)
_refine_glossary_definition_from_evidence = partial(
    _repo_artifacts.refine_glossary_definition_from_evidence,
    collapse_ws=_collapse_ws,
    glossary_tokens_fn=_glossary_tokens,
    normalize_glossary_sentence_fn=lambda term, unit_title, sentence: _normalize_glossary_sentence(term, unit_title, sentence),
    shorten_glossary_sentence_fn=_shorten_glossary_sentence,
)

_NO_UNIT_CATEGORIES = {"cronograma", "bibliografia", "referencias"}
_bundle_priority_score = partial(
    _repo_artifacts.bundle_priority_score,
    normalize_document_profile_fn=normalize_document_profile,
    exam_categories=EXAM_CATEGORIES,
    exercise_categories=EXERCISE_CATEGORIES,
)
_bundle_reason_labels = partial(
    _repo_artifacts.bundle_reason_labels,
    normalize_document_profile_fn=normalize_document_profile,
    exam_categories=EXAM_CATEGORIES,
    exercise_categories=EXERCISE_CATEGORIES,
)


_MANIFEST_LOG_LIMIT = 200
_entry_image_source_dirs = _entry_signals_image_source_dirs
_entry_existing_reference_count = partial(
    _repo_artifacts.entry_existing_reference_count,
    entry_image_source_dirs_fn=_entry_image_source_dirs,
)
_filter_live_manifest_entries = partial(
    _repo_artifacts.filter_live_manifest_entries,
    entry_existing_reference_count_fn=_entry_existing_reference_count,
)
_bundle_seed_candidate = partial(
    _repo_artifacts.bundle_seed_candidate,
    bundle_reason_labels_fn=_bundle_reason_labels,
)


_normalize_match_text = _entry_signals_normalize_match_text


_strip_outline_prefix = _file_map_strip_outline_prefix
_UNIT_GENERIC_TOKENS = _FILE_MAP_UNIT_GENERIC_TOKENS


_normalize_unit_slug = _teaching_plan_normalize_unit_slug


_build_file_map_unit_index = partial(
    _file_map_build_file_map_unit_index,
    normalize_match_text=_normalize_match_text,
    normalize_unit_slug=_normalize_unit_slug,
    strip_outline_prefix=_strip_outline_prefix,
    topic_text=_topic_text,
    unit_generic_tokens=_UNIT_GENERIC_TOKENS,
)


_collect_entry_unit_signals = _entry_signals_collect_entry_unit_signals


_build_file_map_content_taxonomy_from_course = partial(
    _file_map_build_file_map_content_taxonomy_from_course,
    parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
    topic_text=_topic_text,
    glossary_md_fn=glossary_md,
    collect_strong_heading_candidates=_collect_strong_heading_candidates,
    resolve_semantic_profile_fn=resolve_semantic_profile,
    build_content_taxonomy_fn=_build_content_taxonomy,
)

_auto_map_entry_subtopic = partial(
    _file_map_auto_map_entry_subtopic,
    collect_entry_unit_signals=_collect_entry_unit_signals,
    iter_content_taxonomy_topics=_iter_content_taxonomy_topics,
    score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
    topic_match_result_factory=TopicMatchResult,
)


_score_entry_against_unit = partial(
    _file_map_score_entry_against_unit,
    score_timeline_unit_phrase=_score_timeline_unit_phrase,
    timeline_unit_neutral_tokens=_TIMELINE_UNIT_NEUTRAL_TOKENS,
)


_auto_map_entry_unit = lambda entry, units, markdown_text, topic_index=None: _file_map_auto_map_entry_unit(
    entry,
    units,
    markdown_text,
    topic_index=topic_index,
    build_file_map_unit_index=_build_file_map_unit_index,
    collect_entry_unit_signals=_collect_entry_unit_signals,
    score_entry_against_unit=_score_entry_against_unit,
    normalize_unit_slug=_normalize_unit_slug,
    score_entry_against_taxonomy_topic=_score_entry_against_taxonomy_topic,
    unit_match_result_factory=UnitMatchResult,
)


_format_file_map_unit_cell = _file_map_format_file_map_unit_cell


_resolve_entry_manual_unit_slug = partial(
    _file_map_resolve_entry_manual_unit_slug,
    normalize_unit_slug=_normalize_unit_slug,
)


_resolve_entry_manual_timeline_block = _file_map_resolve_entry_manual_timeline_block


_build_file_map_unit_index_from_course = partial(
    _file_map_build_file_map_unit_index_from_course,
    build_file_map_unit_index_fn=_build_file_map_unit_index,
    parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
    glossary_md_fn=glossary_md,
    parse_glossary_terms_fn=_parse_glossary_terms,
    normalize_match_text_fn=_normalize_match_text,
    collapse_ws_fn=_collapse_ws,
    unit_generic_tokens=_UNIT_GENERIC_TOKENS,
    timeline_unit_neutral_tokens=_TIMELINE_UNIT_NEUTRAL_TOKENS,
)

student_state_md = partial(
    _repo_artifacts.student_state_md,
    render_student_state_md_fn=student_state_v2.render_student_state_md,
)


progress_schema_md = _repo_artifacts.progress_schema_md


bibliography_md = partial(
    _repo_artifacts.bibliography_md,
    parse_bibliography_from_teaching_plan_fn=_parse_bibliography_from_teaching_plan,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)
exam_index_md = partial(
    _repo_artifacts.exam_index_md,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)
assignment_index_md = partial(
    _repo_artifacts.assignment_index_md,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)
code_index_md = partial(
    _repo_artifacts.code_index_md,
    code_review_profile_fn=_code_review_profile,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)
whiteboard_index_md = partial(
    _repo_artifacts.whiteboard_index_md,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)


# ---------------------------------------------------------------------------
# Free functions — existing templates (unchanged)
# ---------------------------------------------------------------------------

root_readme = _repo_artifacts.root_readme
wrap_frontmatter = partial(_repo_artifacts.wrap_frontmatter, json_str_fn=json_str)
rows_to_markdown_table = _repo_artifacts.rows_to_markdown_table

manual_pdf_review_template = partial(_repo_artifacts.manual_pdf_review_template, json_str_fn=json_str)
manual_image_review_template = partial(_repo_artifacts.manual_image_review_template, safe_rel_fn=safe_rel)
manual_url_review_template = partial(_repo_artifacts.manual_url_review_template, json_str_fn=json_str)
migrate_legacy_url_manual_reviews = partial(
    _repo_artifacts.migrate_legacy_url_manual_reviews,
    ensure_dir_fn=ensure_dir,
    safe_rel_fn=safe_rel,
    write_text_fn=write_text,
    logger=logger,
)
pdf_curation_guide = _repo_artifacts.pdf_curation_guide
backend_architecture_md = _repo_artifacts.backend_architecture_md
backend_policy_yaml = partial(_repo_artifacts.backend_policy_yaml, json_str_fn=json_str)


_low_token_course_map_md = partial(
    _navigation_low_token_course_map_md,
    build_file_map_timeline_context_from_course=_build_file_map_timeline_context_from_course,
    aggregate_unit_periods_from_blocks=_aggregate_unit_periods_from_blocks,
    normalize_unit_slug=_normalize_unit_slug,
    parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
    topic_text=_topic_text,
    topic_depth=_topic_depth,
    build_assessment_context_from_course=_build_assessment_context_from_course,
    assessment_conflict_section_lines=_assessment_conflict_section_lines,
    clamp_navigation_artifact=_clamp_navigation_artifact,
    logger=logger,
)


_low_token_file_map_md = partial(
    _navigation_low_token_file_map_md,
    build_file_map_content_taxonomy_from_course=_build_file_map_content_taxonomy_from_course,
    build_file_map_unit_index_from_course=_build_file_map_unit_index_from_course,
    build_file_map_timeline_context_from_course=_build_file_map_timeline_context_from_course,
    iter_content_taxonomy_topics=_iter_content_taxonomy_topics,
    merge_manual_and_auto_tags=_merge_manual_and_auto_tags,
    resolve_entry_manual_timeline_block=_resolve_entry_manual_timeline_block,
    entry_markdown_text_for_file_map=_entry_markdown_text_for_file_map,
    auto_map_entry_subtopic=_auto_map_entry_subtopic,
    resolve_entry_manual_unit_slug=_resolve_entry_manual_unit_slug,
    unit_match_result_factory=UnitMatchResult,
    derive_unit_from_topic_match=_derive_unit_from_topic_match,
    auto_map_entry_unit=_auto_map_entry_unit,
    select_probable_period_for_entry=_select_probable_period_for_entry,
    file_map_markdown_cell=_file_map_markdown_cell,
    entry_markdown_path_for_file_map=_entry_markdown_path_for_file_map,
    get_entry_sections=_get_entry_sections,
    infer_unit_confidence=_infer_unit_confidence,
    entry_usage_hint=_entry_usage_hint,
    entry_priority_label=_entry_priority_label,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)


_budgeted_file_map_md = partial(
    _navigation_budgeted_file_map_md,
    filter_live_manifest_entries=_filter_live_manifest_entries,
    low_token_file_map_md_fn=_low_token_file_map_md,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)


_low_token_course_map_md_v2 = partial(
    _navigation_low_token_course_map_md_v2,
    low_token_course_map_md_fn=_low_token_course_map_md,
)


_exercise_index_md_v2 = partial(
    _repo_artifacts.exercise_index_md,
    collapse_ws_fn=_collapse_ws,
    merge_manual_and_auto_tags_fn=_merge_manual_and_auto_tags,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)


course_map_md = partial(
    _navigation_course_map_md,
    low_token_course_map_md_v2_fn=_low_token_course_map_md_v2,
    clamp_navigation_artifact=_clamp_navigation_artifact,
)


file_map_md = partial(
    _navigation_file_map_md,
    budgeted_file_map_md_fn=_budgeted_file_map_md,
)


exercise_index_md = _exercise_index_md_v2


__all__ = [
    "BackendContext",
    "ExtractionBackend",
    "PyMuPDF4LLMBackend",
    "PyMuPDFBackend",
    "DoclingCLIBackend",
    "DoclingPythonBackend",
    "DatalabCloudBackend",
    "MarkerCLIBackend",
    "BackendSelector",
    "RepoBuilder",
    "has_docling_python_api",
    "generate_claude_project_instructions",
    "generate_gemini_instructions",
    "generate_gpt_instructions",
    "modes_md",
    "output_templates_md",
    "syllabus_md",
    "student_profile_md",
    "glossary_md",
    "student_state_md",
    "progress_schema_md",
    "bibliography_md",
    "exam_index_md",
    "assignment_index_md",
    "code_index_md",
    "whiteboard_index_md",
    "course_map_md",
    "file_map_md",
    "exercise_index_md",
    "root_readme",
    "wrap_frontmatter",
    "rows_to_markdown_table",
    "manual_pdf_review_template",
    "manual_image_review_template",
    "manual_url_review_template",
    "migrate_legacy_url_manual_reviews",
    "pdf_curation_guide",
    "backend_architecture_md",
    "backend_policy_yaml",
    "UnitMatchResult",
    "TopicMatchResult",
    "_auto_map_entry_subtopic",
    "_auto_map_entry_unit",
    "_build_assessment_context_from_course",
    "_build_content_taxonomy",
    "_build_file_map_timeline_context_from_course",
    "_build_file_map_unit_index",
    "_build_file_map_unit_index_from_course",
    "_build_marker_page_chunks",
    "_build_timeline_candidate_rows",
    "_build_timeline_index",
    "_bundle_priority_score",
    "_collect_entry_unit_signals",
    "_compact_notebook_markdown",
    "_detect_latex_corruption",
    "_derive_unit_from_topic_match",
    "_entry_markdown_text_for_file_map",
    "_file_map_markdown_cell",
    "_filter_live_manifest_entries",
    "_find_glossary_evidence",
    "_format_file_map_unit_cell",
    "_generated_repo_gitignore_text",
    "_html_to_structured_markdown",
    "_hybridize_marker_markdown_with_base",
    "_marker_progress_hints",
    "_match_timeline_to_units",
    "_normalize_unicode_math",
    "_parse_bibliography_from_teaching_plan",
    "_parse_syllabus_timeline",
    "_parse_timeline_date_value",
    "_repair_mojibake_text",
    "_resolve_entry_manual_timeline_block",
    "_sanitize_external_markdown_text",
    "_score_entry_against_timeline_block",
    "_score_entry_against_unit",
    "_seed_glossary_fields",
    "_select_probable_period_for_entry",
    "_serialize_timeline_index",
    "_write_internal_content_taxonomy",
]

