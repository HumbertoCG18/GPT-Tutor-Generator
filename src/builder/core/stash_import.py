"""Import ciente de pasta-card a partir do stash da matéria.

Convenção: ``<stash>/<card>/<arquivos>``. A subpasta imediata é o card
(seção do Moodle feita pelo professor) — sinal autoritativo para a
atribuição file->bloco. Arquivos soltos na raiz do stash ficam sem card
(``card_name=""``) e seguem o caminho lexical atual.

Módulo PURO: sem Tkinter, sem I/O além de varrer o filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from src.utils.helpers import CODE_EXTENSIONS, DEFAULT_OCR_LANGUAGE, auto_detect_category
from src.models.core import FileEntry

# Extensões de imagem suportadas pela importação (espelha os filtros da UI).
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


@dataclass
class StashItem:
    source_path: str
    card_name: str
    file_type: str   # "pdf" | "image" | "zip" | "code"
    category: str


@dataclass
class StashScanResult:
    items: List[StashItem] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)  # paths de ext. desconhecida


def _classify_file_type(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext == ".zip":
        return "zip"
    if ext in CODE_EXTENSIONS:
        return "code"
    return ""  # desconhecido -> skip


def _card_for(path: Path, root: Path) -> str:
    """Nome do primeiro componente abaixo de root; "" se o arquivo está na raiz."""
    rel_parts = path.relative_to(root).parts
    return rel_parts[0] if len(rel_parts) > 1 else ""


def scan_stash_cards(stash_root) -> StashScanResult:
    root = Path(stash_root)
    result = StashScanResult()
    if not root.is_dir():
        return result
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        ftype = _classify_file_type(path.suffix)
        if not ftype:
            result.skipped.append(str(path))
            continue
        # .zip = código do professor por convenção (fica dentro do card);
        # demais tipos usam a heurística de nome existente.
        if ftype == "zip":
            category = "codigo-professor"
        else:
            category = auto_detect_category(path.name, is_image=(ftype == "image"))
        result.items.append(StashItem(
            source_path=str(path),
            card_name=_card_for(path, root),
            file_type=ftype,
            category=category,
        ))
    return result


def filter_already_processed(scan: StashScanResult, backlog_basenames) -> StashScanResult:
    """Remove do scan os itens cujo basename já está no backlog (já processados).
    Casamento por nome de arquivo — o source_path do stash difere do source_path
    original no manifest, então dedup por path não pega. Preserva `skipped`.
    """
    known = {str(n).strip() for n in (backlog_basenames or set())}
    kept = [i for i in scan.items if Path(i.source_path).name not in known]
    return StashScanResult(items=kept, skipped=list(scan.skipped))


def build_stash_entries(scan: StashScanResult, existing_source_paths, defaults=None) -> List[FileEntry]:
    """Converte itens varridos em FileEntry, pulando paths já presentes."""
    existing = set(existing_source_paths or set())
    defaults = defaults or {}
    entries: List[FileEntry] = []
    for item in scan.items:
        if item.source_path in existing:
            continue
        entries.append(FileEntry(
            source_path=item.source_path,
            file_type=item.file_type,
            category=item.category,
            title=Path(item.source_path).stem,
            source_section=item.card_name,
            processing_mode=defaults.get("processing_mode", "auto"),
            ocr_language=defaults.get("ocr_language", DEFAULT_OCR_LANGUAGE),
        ))
    return entries
