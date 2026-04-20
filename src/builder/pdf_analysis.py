from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from src.models.core import DocumentProfileReport, FileEntry
from src.utils.helpers import normalize_document_profile, parse_page_range, write_text

logger = logging.getLogger(__name__)


def quick_page_count(pdf_path: Path, *, has_pymupdf: bool, pymupdf_module) -> int:
    if not has_pymupdf:
        return 0
    try:
        doc = pymupdf_module.open(str(pdf_path))
        n = doc.page_count
        doc.close()
        return n
    except Exception:
        return 0


def apply_math_normalization(
    root_dir: Path,
    md_rel_path: Optional[str],
    *,
    normalize_unicode_math_fn,
) -> None:
    if not md_rel_path:
        return
    try:
        md_path = root_dir / md_rel_path
        if not md_path.exists():
            return
        original = md_path.read_text(encoding="utf-8")
        normalized = normalize_unicode_math_fn(original)
        if normalized != original:
            write_text(md_path, normalized)
            logger.info("  [math-norm] Normalizado símbolos Unicode → LaTeX em %s", md_rel_path)
    except Exception as exc:
        logger.warning("  [math-norm] Falha ao normalizar %s: %s", md_rel_path, exc)


def profile_pdf(
    pdf_path: Path,
    entry: FileEntry,
    *,
    has_pymupdf: bool,
    pymupdf_module,
) -> DocumentProfileReport:
    report = DocumentProfileReport()
    if not has_pymupdf:
        report.suggested_profile = normalize_document_profile(entry.document_profile)
        report.notes.append("PyMuPDF não disponível; perfil automático limitado.")
        return report
    doc = pymupdf_module.open(str(pdf_path))
    try:
        pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
        pages = [p for p in pages if 0 <= p < doc.page_count]
        report.page_count = len(pages)
        total_text = 0
        total_images = 0
        table_candidates = 0
        low_text_pages = 0
        for page_num in pages:
            page = doc[page_num]
            text = page.get_text("text") or ""
            total_text += len(text.strip())
            images = page.get_images(full=True) or []
            total_images += len(images)
            try:
                tables = page.find_tables()
                table_candidates += len(getattr(tables, "tables", []) or [])
            except Exception:
                pass
            if len(text.strip()) < 60 and len(images) > 0:
                low_text_pages += 1
        report.text_chars = total_text
        report.images_count = total_images
        report.table_candidates = table_candidates
        report.text_density = round(total_text / max(report.page_count, 1), 2)
        report.suspected_scan = (low_text_pages / max(report.page_count, 1)) >= 0.5 and total_images > 0
    finally:
        doc.close()
    if entry.document_profile != "auto":
        report.suggested_profile = normalize_document_profile(entry.document_profile)
        report.notes.append("Perfil definido manualmente pelo usuário.")
        return report
    name_hint = f"{entry.title} {entry.tags} {entry.notes}".lower()
    if report.suspected_scan:
        report.suggested_profile = "scanned"
        report.notes.append("Muitas páginas com pouco texto e imagens presentes: provável scan.")
    elif entry.category == "provas" or "prova" in name_hint or "questão" in name_hint or "questao" in name_hint:
        report.suggested_profile = "diagram_heavy"
        report.notes.append("Detectado como material de prova/exame.")
    elif entry.formula_priority or re.search(r"\b(latex|equação|equation|fórmula|teorema|prova formal|indução)\b", name_hint):
        report.suggested_profile = "math_heavy"
        report.notes.append("Sinais de conteúdo matemático/formal.")
    elif report.table_candidates >= 2 or report.images_count >= max(3, report.page_count):
        report.suggested_profile = "diagram_heavy"
        report.notes.append("Layout com tabelas/imagens relevantes.")
    else:
        report.suggested_profile = "auto"
        report.notes.append("Documento geral detectado.")
    return report
