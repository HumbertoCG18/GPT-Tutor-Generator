from __future__ import annotations

import json
import logging
import sys
from datetime import datetime

from src.utils.helpers import write_text

logger = logging.getLogger(__name__)


def build_impl(
    builder,
    *,
    app_name: str,
    has_pymupdf: bool,
    has_pymupdf4llm: bool,
    has_pdfplumber: bool,
    has_datalab_api_key_fn,
    docling_cli,
    has_docling_python_api_fn,
    marker_cli,
    file_map_md_fn,
) -> None:
    logger.info("Building repository at %s", builder.root_dir)
    logger.info("Creating directory structure...")
    builder._create_structure()
    logger.info("Writing root/pedagogical files...")
    builder._write_root_files()
    logger.info("Root files written. Starting entry processing...")

    manifest = {
        "app": app_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "course": builder.course_meta,
        "options": builder.options,
        "environment": {
            "python": sys.version.split()[0],
            "pymupdf": has_pymupdf,
            "pymupdf4llm": has_pymupdf4llm,
            "pdfplumber": has_pdfplumber,
            "datalab_api": has_datalab_api_key_fn(),
            "docling_cli": bool(docling_cli),
            "docling_python": has_docling_python_api_fn(),
            "marker_cli": bool(marker_cli),
        },
        "entries": [],
    }

    manifest_path = builder.root_dir / "manifest.json"
    active_entries = [e for e in builder.entries if getattr(e, "enabled", True)]
    skipped = len(builder.entries) - len(active_entries)
    if skipped:
        logger.info("Pulando %d entries desabilitados.", skipped)
    total = len(active_entries)
    for i, entry in enumerate(active_entries):
        logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
        if builder.progress_callback:
            builder.progress_callback(i, total, entry.title)
        item_result = builder._process_entry(entry)
        manifest["entries"].append(item_result)
        manifest["logs"] = builder.logs
        manifest = builder._compact_manifest(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
    if builder.progress_callback:
        builder.progress_callback(total, total, "")

    manifest["logs"] = builder.logs
    manifest = builder._compact_manifest(manifest)
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._write_build_report(manifest)

    write_text(
        builder.root_dir / "course" / "FILE_MAP.md",
        file_map_md_fn(
            {**builder.course_meta, "_repo_root": builder.root_dir},
            manifest["entries"],
            builder.subject_profile,
        ),
    )

    builder._resolve_content_images()
    builder._inject_all_image_descriptions()
    builder._regenerate_pedagogical_files(manifest)
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

    logger.info("Repository built successfully at %s", builder.root_dir)
