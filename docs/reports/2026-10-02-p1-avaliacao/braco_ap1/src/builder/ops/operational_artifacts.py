from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def write_source_registry(root_dir, manifest, *, write_text_fn, repo_artifacts_module) -> None:
    repo_artifacts_module.write_source_registry(
        root_dir,
        manifest,
        write_text_fn=write_text_fn,
    )


def write_bundle_seed(
    root_dir,
    manifest,
    *,
    course_meta,
    bundle_priority_score_fn,
    bundle_seed_candidate_fn,
    write_text_fn,
    repo_artifacts_module,
) -> None:
    repo_artifacts_module.write_bundle_seed(
        root_dir,
        manifest,
        course_meta=course_meta,
        bundle_priority_score_fn=bundle_priority_score_fn,
        bundle_seed_candidate_fn=bundle_seed_candidate_fn,
        write_text_fn=write_text_fn,
    )


def write_build_report(
    root_dir,
    manifest,
    *,
    preferred_platform,
    has_pymupdf,
    has_pymupdf4llm,
    has_pdfplumber,
    has_datalab_api_key_fn,
    docling_cli,
    has_docling_python_api_fn,
    marker_cli,
    write_text_fn,
    repo_artifacts_module,
) -> None:
    repo_artifacts_module.write_build_report(
        root_dir,
        manifest,
        preferred_platform=preferred_platform,
        has_pymupdf=has_pymupdf,
        has_pymupdf4llm=has_pymupdf4llm,
        has_pdfplumber=has_pdfplumber,
        has_datalab_api_key_fn=has_datalab_api_key_fn,
        docling_cli=docling_cli,
        has_docling_python_api_fn=has_docling_python_api_fn,
        marker_cli=marker_cli,
        write_text_fn=write_text_fn,
    )


def compact_manifest(
    root_dir,
    manifest: dict,
    *,
    filter_live_manifest_entries_fn,
    heal_manifest_markdown_paths_fn,
    manifest_log_limit,
    repo_artifacts_module,
) -> dict:
    manifest, removed, healed = repo_artifacts_module.compact_manifest(
        root_dir,
        manifest,
        filter_live_manifest_entries_fn=filter_live_manifest_entries_fn,
        heal_manifest_markdown_paths_fn=heal_manifest_markdown_paths_fn,
        manifest_log_limit=manifest_log_limit,
    )
    if removed > 0:
        logger.info("Removidas %d entries órfãs do manifest antes de regenerar artefatos.", removed)
    if healed > 0:
        logger.info("Healed markdown targets for %d manifest entries.", healed)
    return manifest
