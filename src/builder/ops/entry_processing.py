from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict

from src.utils.helpers import ensure_dir, safe_rel


def process_entry(builder, entry, *, image_categories) -> Dict[str, object]:
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
        item.update(builder._process_url(entry))
        return item

    if entry.file_type == "github-repo":
        item.update(builder._process_github_repo(entry))
        return item

    safe_name = f"{entry.id()}{src.suffix.lower()}"

    if entry.file_type == "code":
        code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
        raw_target = builder.root_dir / "raw" / "code" / code_subdir / safe_name
        ensure_dir(raw_target.parent)
        shutil.copy2(src, raw_target)
        item["raw_target"] = safe_rel(raw_target, builder.root_dir)
        item.update(builder._process_code(entry, raw_target))
        return item

    if entry.file_type == "zip":
        raw_target = builder.root_dir / "raw" / "zip" / safe_name
        ensure_dir(raw_target.parent)
        shutil.copy2(src, raw_target)
        item["raw_target"] = safe_rel(raw_target, builder.root_dir)
        item.update(builder._process_zip(entry, raw_target))
        return item

    if entry.file_type == "pdf":
        raw_target = builder.root_dir / "raw" / "pdfs" / entry.category / safe_name
        ensure_dir(raw_target.parent)
        shutil.copy2(src, raw_target)
        item["raw_target"] = safe_rel(raw_target, builder.root_dir)
        item.update(builder._process_pdf(entry, raw_target))
        return item

    image_category = entry.category if entry.category in image_categories else "outros"
    raw_target = builder.root_dir / "raw" / "images" / image_category / safe_name
    ensure_dir(raw_target.parent)
    shutil.copy2(src, raw_target)
    item["raw_target"] = safe_rel(raw_target, builder.root_dir)
    item.update(builder._process_image(entry, raw_target))
    return item
