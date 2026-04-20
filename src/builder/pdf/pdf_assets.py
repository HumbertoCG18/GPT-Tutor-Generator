from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.builder.artifacts import repo as _repo_artifacts
from src.utils.helpers import ensure_dir, write_text


def is_noise_image(
    data: bytes,
    *,
    max_aspect_ratio: float,
    max_noise_colors: int,
) -> bool:
    try:
        from PIL import Image as PILImage
        import io

        img = PILImage.open(io.BytesIO(data))
        w, h = img.size

        if w > 0 and h > 0:
            ratio = max(w / h, h / w)
            if ratio > max_aspect_ratio:
                return True

        colors = img.getcolors(maxcolors=max_noise_colors + 1)
        if colors is not None and len(colors) <= max_noise_colors:
            return True

        return False
    except Exception:
        return False


def should_keep_extracted_pdf_image(
    *,
    data: bytes,
    width: int,
    height: int,
    policy: Dict[str, object],
    is_noise_image_fn,
) -> bool:
    if len(data) < int(policy["min_bytes"]):
        return False
    if width < int(policy["min_dimension"]) or height < int(policy["min_dimension"]):
        return False

    ratio = max(width / max(height, 1), height / max(width, 1))
    if ratio > float(policy["max_aspect_ratio"]):
        return False

    if policy.get("keep_low_color"):
        return True
    return not is_noise_image_fn(data)


def image_format(options: dict) -> str:
    fmt = options.get("image_format", "png")
    return fmt if fmt in ("png", "jpeg") else "png"


def convert_image_format(src: Path, *, options: dict) -> Path:
    target_format = image_format(options)
    target_ext = f".{target_format}" if target_format != "jpeg" else ".jpg"
    if src.suffix.lower() in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
        return src
    try:
        from PIL import Image as PILImage

        img = PILImage.open(src)
        if target_format == "jpeg" and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        new_path = src.with_suffix(target_ext)
        save_kwargs = {"quality": 90} if target_format == "jpeg" else {}
        img.save(new_path, **save_kwargs)
        if new_path != src:
            src.unlink(missing_ok=True)
        return new_path
    except Exception:
        return src


def extract_pdf_images(
    pdf_path: Path,
    out_dir: Path,
    *,
    pymupdf_module,
    pages: Optional[List[int]] = None,
    policy: Dict[str, object],
    should_keep_image_fn,
) -> int:
    ensure_dir(out_dir)
    doc = pymupdf_module.open(str(pdf_path))
    seen_xrefs: set = set()
    try:
        target_pages = pages or list(range(doc.page_count))
        count = 0
        for page_num in target_pages:
            if not (0 <= page_num < doc.page_count):
                continue
            page = doc[page_num]
            for img_idx, img in enumerate(page.get_images(full=True), start=1):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                image = doc.extract_image(xref)
                if not image or "image" not in image:
                    continue

                data = image["image"]
                w = image.get("width", 0)
                h = image.get("height", 0)

                if not should_keep_image_fn(
                    data=data,
                    width=w,
                    height=h,
                    policy=policy,
                ):
                    continue

                ext = image.get("ext", "png")
                fname = out_dir / f"page-{page_num + 1:03d}-img-{img_idx:02d}.{ext}"
                fname.write_bytes(data)
                count += 1
        return count
    finally:
        doc.close()


def extract_tables_pdfplumber(pdf_path: Path, out_dir: Path, *, pdfplumber_module, pages: Optional[List[int]] = None) -> int:
    ensure_dir(out_dir)
    count = 0
    with pdfplumber_module.open(str(pdf_path)) as pdf:
        selected = pages or list(range(len(pdf.pages)))
        for page_num in selected:
            if not (0 <= page_num < len(pdf.pages)):
                continue
            page = pdf.pages[page_num]
            tables = page.extract_tables() or []
            for table_idx, table in enumerate(tables, start=1):
                normalized = [
                    [("" if cell is None else str(cell).strip()) for cell in row]
                    for row in table
                    if row and any(cell not in (None, "", " ") for cell in row)
                ]
                if not normalized:
                    continue
                csv_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.csv"
                ensure_dir(csv_path.parent)
                with csv_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(normalized)
                md_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.md"
                write_text(md_path, _repo_artifacts.rows_to_markdown_table(normalized))
                count += 1
    return count


def detect_tables_pymupdf(pdf_path: Path, out_dir: Path, *, pymupdf_module, pages: Optional[List[int]] = None) -> int:
    ensure_dir(out_dir)
    doc = pymupdf_module.open(str(pdf_path))
    try:
        selected = pages or list(range(doc.page_count))
        count = 0
        for page_num in selected:
            if not (0 <= page_num < doc.page_count):
                continue
            page = doc[page_num]
            try:
                tables = page.find_tables()
                found = getattr(tables, "tables", []) or []
                if not found:
                    continue
                serializable = []
                for idx, tbl in enumerate(found, start=1):
                    bbox = getattr(tbl, "bbox", None)
                    rows = []
                    try:
                        extracted = tbl.extract() or []
                        rows = [["" if cell is None else str(cell) for cell in row] for row in extracted]
                    except Exception:
                        pass
                    serializable.append({"table_index": idx, "bbox": list(bbox) if bbox else None, "rows": rows})
                meta_path = out_dir / f"page-{page_num + 1:03d}.json"
                write_text(meta_path, json.dumps(serializable, indent=2, ensure_ascii=False))
                count += len(serializable)
            except Exception:
                continue
        return count
    finally:
        doc.close()
