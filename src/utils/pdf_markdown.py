"""PDF -> markdown via pymupdf4llm, com duas correcoes de raiz (2026-08-28).

1. `pymupdf4llm >= 1.27` monta o layout com `TEXT_IGNORE_ACTUALTEXT`: PDFs que codificam
   caracteres via `/ActualText` (Google Docs + fonte Inter: `( + ) :`) saem como glifos
   privados (U+E081 `(`, U+E09D `+`, U+E082 `)`, U+E092 `:`). Medido no plano do TCC:
   `G1 = (P1+P2+T)/3` virava `G1 = \ue081P1\ue09dP2\ue09dT\ue082/3`; sem a flag, 0 PUA e
   texto identico ao extraido pela versao anterior (ratio 1,000 em TCC/SO/ES2).
2. `use_ocr=True` (default) OCR-iza e DESCARTA o texto nativo de paginas com logo + texto
   (`needs_ocr: img_text`): SO/Lab SO/Fund. Redes perdiam ~400 chars e acentos. OCR so
   quando a pagina nao tem texto nativo.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def respect_actualtext():
    """Tira TEXT_IGNORE_ACTUALTEXT das FLAGS do layout do pymupdf4llm durante a chamada."""
    try:
        import pymupdf
        import pymupdf4llm.helpers.document_layout as layout
    except ImportError:  # pymupdf4llm ausente ou versao sem o modulo: nada a corrigir
        yield
        return
    flags = getattr(layout, "FLAGS", None)
    if flags is None:
        yield
        return
    layout.FLAGS = flags & ~pymupdf.TEXT_IGNORE_ACTUALTEXT
    try:
        yield
    finally:
        layout.FLAGS = flags


def pdf_has_native_text(pdf_path: str | Path) -> bool:
    import pymupdf
    with pymupdf.open(str(pdf_path)) as doc:
        return any(page.get_text().strip() for page in doc)


def pdf_to_markdown(pdf_path: str | Path, **kwargs) -> str:
    """`pymupdf4llm.to_markdown` com ActualText respeitado e OCR so sem texto nativo
    (a menos que o chamador passe `use_ocr`/`force_ocr` explicitamente)."""
    import pymupdf4llm
    if "use_ocr" not in kwargs and not kwargs.get("force_ocr"):
        kwargs["use_ocr"] = not pdf_has_native_text(pdf_path)
    with respect_actualtext():
        return pymupdf4llm.to_markdown(str(pdf_path), **kwargs)
