from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from src.utils.helpers import write_text

logger = logging.getLogger(__name__)


def incremental_build_impl(builder, *, student_state_md_fn, progress_schema_md_fn) -> None:
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

        total = len(new_entries)
        for i, entry in enumerate(new_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if builder.progress_callback:
                builder.progress_callback(i, total, entry.title)
            item_result = builder._process_entry(entry)
            manifest["entries"].append(item_result)
            manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
            manifest.setdefault("logs", []).extend(builder.logs)
            builder.logs = []
            manifest = builder._compact_manifest(manifest)
            write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
            logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
        if builder.progress_callback:
            builder.progress_callback(total, total, "")

    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).extend(builder.logs)
    manifest = builder._compact_manifest(manifest)

    builder._regenerate_pedagogical_files(manifest)

    state_path = builder.root_dir / "student" / "STUDENT_STATE.md"
    if state_path.exists():
        content = state_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        content = re.sub(r"^updated:.*$", f"updated: {today}", content, flags=re.MULTILINE)
        state_path.write_text(content, encoding="utf-8")
    else:
        write_text(state_path, student_state_md_fn(builder.course_meta, builder.student_profile))
    progress_path = builder.root_dir / "build" / "PROGRESS_SCHEMA.md"
    if not progress_path.exists():
        write_text(progress_path, progress_schema_md_fn())

    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._write_build_report(manifest)
    logger.info("Incremental build completed. %d new entries added.", len(new_entries))
