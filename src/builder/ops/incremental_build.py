from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from src.builder.artifacts.deeptutor import write_deeptutor_export
from src.builder.ops.build_workflow import _run_auto_code_summarization
from src.builder.ops.lifecycle_ops import assign_dedup_id
from src.utils.helpers import write_text, write_json_manifest

logger = logging.getLogger(__name__)


def incremental_build_impl(builder, *, student_state_md_fn) -> None:
    """Adiciona novos arquivos a um repositório existente sem recriar do zero."""
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        logger.info("No existing manifest found, falling back to full build.")
        builder.build()
        return

    logger.info("Incremental build at %s", builder.root_dir)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest = builder._compact_manifest(manifest)

    existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
    new_entries = [e for e in builder.entries if e.source_path not in existing_sources and getattr(e, "enabled", True)]

    if not new_entries:
        logger.info("No new entries to process — regenerating pedagogical files only.")
    else:
        logger.info("Processing %d new entries (skipping %d existing).", len(new_entries), len(builder.entries) - len(new_entries))

        builder._create_structure()

        manifest.setdefault("failed_entries", [])
        total = len(new_entries)
        existing_ids = {
            str(e.get("id") or "")
            for e in manifest.get("entries", [])
            if e.get("id")
        }
        for i, entry in enumerate(new_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if builder.progress_callback:
                builder.progress_callback(i, total, entry.title)
            assign_dedup_id(entry, existing_ids)
            try:
                item_result = builder._process_entry(entry)
                manifest["entries"].append(item_result)
            except FileNotFoundError as exc:
                failure = {
                    "id": entry.id(),
                    "title": entry.title,
                    "file_type": entry.file_type,
                    "source_path": entry.source_path,
                    "error_type": "missing_source",
                    "error_message": str(exc),
                }
                builder.failed_entries.append(failure)
                manifest["failed_entries"].append(failure)
                builder.logs.append(
                    {
                        "entry": entry.title,
                        "step": "source_check",
                        "status": "error",
                        "message": str(exc),
                    }
                )
                logger.warning("[%d/%d] Pulando entry com arquivo ausente: %s", i + 1, total, exc)
                manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
                manifest.setdefault("logs", []).extend(builder.logs)
                builder.logs = []
                manifest = builder._compact_manifest(manifest)
                write_json_manifest(manifest_path, manifest)
                continue
            manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
            manifest.setdefault("logs", []).extend(builder.logs)
            builder.logs = []
            manifest = builder._compact_manifest(manifest)
            write_json_manifest(manifest_path, manifest)
            logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
        if builder.progress_callback:
            builder.progress_callback(total, total, "")

    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).extend(builder.logs)
    manifest = builder._compact_manifest(manifest)

    write_json_manifest(manifest_path, manifest)
    removed = builder._prune_stale_image_curation()
    if removed:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    removed_code = builder._prune_stale_code_curation()
    if removed_code:
        logger.info("Pruned %d stale code_curation entries", removed_code)
    _run_auto_code_summarization(builder, logger)
    builder._regenerate_pedagogical_files(manifest)

    state_path = builder.root_dir / "student" / "STUDENT_STATE.md"
    if state_path.exists():
        content = state_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        content = re.sub(r"^updated:.*$", f"updated: {today}", content, flags=re.MULTILINE)
        state_path.write_text(content, encoding="utf-8")
    else:
        write_text(state_path, student_state_md_fn(builder.course_meta, builder.student_profile))

    write_json_manifest(manifest_path, manifest)
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._write_build_report(manifest)

    write_deeptutor_export(
        builder.root_dir,
        builder.course_meta,
        student_profile=getattr(builder, "student_profile", None),
        subject_profile=getattr(builder, "subject_profile", None),
    )
    logger.info("DeepTutor export written to .deeptutor/")

    logger.info("Incremental build completed. %d new entries added.", len(new_entries))
