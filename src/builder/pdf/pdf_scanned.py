from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict

from src.utils.helpers import ensure_dir, parse_page_range, safe_rel, write_text


def render_scanned_pdf_as_images(
    root_dir: Path,
    entry,
    raw_target: Path,
    *,
    has_pymupdf: bool,
    pymupdf_module,
    wrap_frontmatter_fn,
) -> Dict[str, object]:
    """
    Para PDFs escaneados:
    - renderiza cada página como imagem
    - cria um markdown base que referencia essas imagens
    - usa JPG / JPEG para reduzir peso
    """
    if not has_pymupdf:
        raise RuntimeError("PyMuPDF é obrigatório para tratar PDFs scanned como imagens.")

    from PIL import Image as PILImage

    entry_id = entry.id()
    images_dir = root_dir / "content" / "images" / "scanned" / entry_id
    md_dir = root_dir / "staging" / "markdown-auto" / "scanned"

    ensure_dir(md_dir)
    if images_dir.exists():
        shutil.rmtree(images_dir)
    ensure_dir(images_dir)

    md_path = md_dir / f"{entry_id}.md"

    doc = pymupdf_module.open(str(raw_target))
    refs = []
    try:
        pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
        pages = [p for p in pages if 0 <= p < doc.page_count]

        for page_num in pages:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=pymupdf_module.Matrix(1.35, 1.35), alpha=False)

            pil_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img_path = images_dir / f"page-{page_num + 1:03d}.jpg"
            pil_img.save(img_path, format="JPEG", quality=82, optimize=True)

            rel = os.path.relpath(str(img_path), str(md_path.parent)).replace("\\", "/")
            refs.append(
                f"## Página {page_num + 1}\n\n"
                f"![Página {page_num + 1}]({rel})\n"
            )
    finally:
        doc.close()

    body = (
        f"# {entry.title}\n\n"
        "> Documento tratado como **imagem** porque o perfil efetivo foi `scanned`.\n"
        "> Cada página foi convertida em imagem para leitura visual.\n\n"
        + "\n".join(refs)
    )

    write_text(
        md_path,
        wrap_frontmatter_fn(
            {
                "entry_id": entry_id,
                "title": entry.title,
                "backend": "scanned-pages",
                "source_pdf": safe_rel(raw_target, root_dir),
                "page_range": entry.page_range,
                "effective_profile": "scanned",
            },
            body,
        ),
    )

    return {
        "base_markdown": safe_rel(md_path, root_dir),
        "base_backend": "scanned-pages",
        "advanced_markdown": None,
        "advanced_backend": None,
        "rendered_pages_dir": safe_rel(images_dir, root_dir),
    }
