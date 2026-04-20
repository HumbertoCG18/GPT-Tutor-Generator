from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.helpers import ensure_dir, safe_rel

logger = logging.getLogger(__name__)

IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


def find_image(root_dir: Path, raw_path: str, md_file: Path) -> Optional[Path]:
    normalized = raw_path.replace("\\", "/")

    p = Path(normalized)
    if p.is_absolute() and p.exists():
        return p

    rel_to_md = md_file.parent / normalized
    if rel_to_md.exists():
        return rel_to_md

    rel_to_root = root_dir / normalized
    if rel_to_root.exists():
        return rel_to_root

    for marker in ("staging/assets/", "staging/markdown-auto/"):
        idx = normalized.find(marker)
        if idx >= 0:
            staging_rel = normalized[idx:]
            candidate = root_dir / staging_rel
            if candidate.exists():
                return candidate

    return None


def resolve_content_images(builder) -> None:
    images_dir = builder.root_dir / "content" / "images"
    ensure_dir(images_dir)

    existing_files = {f for f in images_dir.iterdir() if f.is_file()} if images_dir.exists() else set()
    referenced_files: set = set()

    scan_dirs = [
        builder.root_dir / "content",
        builder.root_dir / "staging" / "markdown-auto",
    ]

    target_ext = f".{builder._image_format}" if builder._image_format != "jpeg" else ".jpg"
    seen: Dict[str, Path] = {}
    copied = 0

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for md_file in scan_dir.rglob("*.md"):
            if images_dir in md_file.parents:
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            replacements: List[tuple] = []
            for match in IMG_RE.finditer(text):
                alt = match.group(1)
                raw_path = match.group(2)

                if "content/images/" in raw_path.replace("\\", "/"):
                    ref_path = find_image(builder.root_dir, raw_path, md_file)
                    if ref_path and ref_path.exists():
                        referenced_files.add(ref_path)
                    continue

                img_path = find_image(builder.root_dir, raw_path, md_file)
                if img_path is None or not img_path.exists():
                    continue

                if img_path.stat().st_size < builder._MIN_IMG_BYTES:
                    continue
                if builder._is_noise_image(img_path.read_bytes()):
                    continue

                img_key = str(img_path)
                if img_key in seen:
                    new_path = seen[img_key]
                else:
                    parent_slug = builder.slugify(img_path.parent.name) if img_path.parent.name else ""
                    short_name = f"{parent_slug}-{img_path.name}" if parent_slug else img_path.name
                    new_path = images_dir / short_name

                    if new_path.exists() and new_path.stat().st_size != img_path.stat().st_size:
                        stem = new_path.stem
                        suffix = new_path.suffix
                        counter = 2
                        while new_path.exists():
                            new_path = images_dir / f"{stem}-{counter}{suffix}"
                            counter += 1

                    if not new_path.exists():
                        shutil.copy2(str(img_path), str(new_path))
                        new_path = builder._convert_image_format(new_path)
                        copied += 1
                    elif new_path.suffix.lower() not in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
                        new_path = builder._convert_image_format(new_path)
                    seen[img_key] = new_path

                referenced_files.add(new_path)

                try:
                    rel = Path(new_path).relative_to(md_file.parent)
                except ValueError:
                    rel = Path(new_path).relative_to(builder.root_dir)

                rel_str = str(rel).replace("\\", "/")
                old_ref = match.group(0)
                new_ref = f"![{alt}]({rel_str})"
                if old_ref != new_ref:
                    replacements.append((old_ref, new_ref))

            if replacements:
                for old, new in replacements:
                    text = text.replace(old, new)
                md_file.write_text(text, encoding="utf-8")

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


def inject_all_image_descriptions(builder, *, resolve_entry_markdown_targets_fn) -> None:
    manifest_path = builder.root_dir / "manifest.json"
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

        target_markdowns = resolve_entry_markdown_targets_fn(entry_data)

        if not target_markdowns:
            content_dir = builder.root_dir / "content"
            if not content_dir.exists():
                continue
            target_markdowns = list(content_dir.rglob("*.md"))

        for md_file in target_markdowns:
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            new_text = builder.inject_image_descriptions(text, curation)
            if new_text != text:
                md_file.write_text(new_text, encoding="utf-8")
                injected_count += 1
                try:
                    rel_md = safe_rel(md_file, builder.root_dir)
                except Exception:
                    rel_md = str(md_file)
                logger.info(
                    "Injected image descriptions into %s for entry %s.",
                    rel_md,
                    entry_data.get("id") or entry_data.get("title") or "<unknown>",
                )

    if injected_count:
        logger.info("Injected image descriptions into %d markdown files.", injected_count)
