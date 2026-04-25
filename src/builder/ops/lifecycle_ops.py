from __future__ import annotations

import json
import logging
import shutil
import sys
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.helpers import write_text

logger = logging.getLogger(__name__)


def process_single_impl(
    builder,
    entry,
    *,
    force: bool = False,
    app_name: str,
    has_pymupdf: bool,
    has_pymupdf4llm: bool,
    has_pdfplumber: bool,
    has_datalab_api_key_fn,
    docling_cli,
    has_docling_python_api_fn,
    marker_cli,
) -> str:
    manifest_path = builder.root_dir / "manifest.json"

    builder._create_structure()

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest = builder._compact_manifest(manifest)
    else:
        builder._write_root_files()
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
            "logs": [],
        }

    existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
    if entry.source_path in existing_sources:
        if not force:
            logger.info("Entry already processed: %s", entry.source_path)
            return "already_exists"
        old_id = entry.id()
        logger.info("Reprocessing (force): removing old entry %s", old_id)
        builder.unprocess(old_id)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    logger.info("Processing single entry: %s (%s)", entry.title, entry.file_type)
    item_result = builder._process_entry(entry)
    manifest["entries"].append(item_result)
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).extend(builder.logs)
    builder.logs = []
    manifest = builder._compact_manifest(manifest)

    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._write_build_report(manifest)

    builder._regenerate_pedagogical_files(manifest)
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

    logger.info("Single entry processed: %s", entry.id())
    return "ok"


def _remove_paths(root_dir, rel_paths: List[str], *, log_prefix: str = "") -> int:
    removed_count = 0
    for rel_path in rel_paths:
        full = root_dir / rel_path
        try:
            if full.is_dir():
                shutil.rmtree(full)
                removed_count += 1
            elif full.is_file():
                full.unlink()
                removed_count += 1
        except Exception as exc:
            prefix = f"{log_prefix}: " if log_prefix else ""
            logger.warning("%snão foi possível remover %s: %s", prefix, full, exc)
    return removed_count


def unprocess(builder, entry_id: str) -> bool:
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("No manifest found at %s", manifest_path)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    builder.course_meta = builder._effective_course_meta(manifest)

    target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
    if not target:
        logger.warning("Entry not found in manifest: %s", entry_id)
        return False

    paths_to_remove: List[str] = []
    for key in [
        "raw_target",
        "base_markdown",
        "advanced_markdown",
        "advanced_markdown_raw",
        "manual_review",
        "images_dir",
        "tables_dir",
        "table_detection_dir",
        "advanced_asset_dir",
        "asset_dir",
        "advanced_metadata_path",
        "approved_markdown",
        "curated_markdown",
        "rendered_pages_dir",
    ]:
        val = target.get(key)
        if val:
            paths_to_remove.append(val)

    removed_count = _remove_paths(builder.root_dir, paths_to_remove, log_prefix="Could not remove")
    removed_count += builder._remove_entry_consolidated_images(entry_id)

    manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest = builder._compact_manifest(manifest)

    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._resolve_content_images()

    logger.info("Unprocessed entry %s (%d files removed)", entry_id, removed_count)
    return True


def reject(builder, entry_id: str) -> Optional[Dict[str, object]]:
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("reject: manifest não encontrado em %s", manifest_path)
        return None

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
    if not target:
        logger.warning("reject: entry %s não encontrada no manifest", entry_id)
        return None

    entry_data = dict(target)

    keys_to_clean = [
        "base_markdown",
        "advanced_markdown",
        "advanced_markdown_raw",
        "manual_review",
        "images_dir",
        "tables_dir",
        "table_detection_dir",
        "advanced_asset_dir",
        "advanced_metadata_path",
        "approved_markdown",
        "curated_markdown",
        "rendered_pages_dir",
    ]
    rel_paths = [target.get(key) for key in keys_to_clean if target.get(key)]
    removed_count = _remove_paths(builder.root_dir, rel_paths, log_prefix="reject")
    removed_count += builder._remove_entry_consolidated_images(entry_id)

    manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).append(
        {
            "entry": entry_id,
            "step": "curator_reject",
            "status": "ok",
        }
    )
    manifest = builder._compact_manifest(manifest)

    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._resolve_content_images()

    logger.info("Rejected entry %s (%d files removed, raw preserved)", entry_id, removed_count)
    return entry_data
