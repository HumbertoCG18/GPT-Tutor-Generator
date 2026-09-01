"""Import ciente de pasta-card a partir do stash da matéria.

Convenção: ``<stash>/<card>/<arquivos>``. A subpasta imediata é o card
(seção do Moodle feita pelo professor) — sinal autoritativo para a
atribuição file->bloco. Arquivos soltos na raiz do stash ficam sem card
(``card_name=""``) e seguem o caminho lexical atual.

Módulo PURO: sem Tkinter, sem I/O além de varrer o filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
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


def _classify_file_type(name: str) -> str:
    """Tipo pelo NOME (nao por path.suffix: '.tar.gz' tem duplo sufixo e o
    suffix ve so '.gz' — os 5 pacotes de codigo do FR 2026/2 eram pulados)."""
    name = name.lower()
    ext = Path(name).suffix
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    # tar.gz/.tgz seguem o MESMO fluxo do zip (extrair -> sub-entries de
    # codigo); process_zip decide o formato pelo CONTEUDO do arquivo.
    if ext == ".zip" or name.endswith((".tar.gz", ".tgz")):
        return "zip"
    if ext in CODE_EXTENSIONS:
        return "code"
    return ""  # desconhecido -> skip


def _card_for(path: Path, root: Path) -> str:
    """Nome do primeiro componente abaixo de root; "" se o arquivo está na raiz."""
    rel_parts = path.relative_to(root).parts
    return rel_parts[0] if len(rel_parts) > 1 else ""


def scan_stash_cards(stash_root, frases_do_plano=None) -> StashScanResult:
    root = Path(stash_root)
    result = StashScanResult()
    if not root.is_dir():
        return result
    # F10 (censo 2026-08-28): a categoria certa vive ora no nome do MODULO do Moodle
    # ("Tipos de Redes (Slides)"), ora no nome do ARQUIVO ("aula03 - buildroot-intro.pdf").
    # Detecta sobre os dois concatenados — arquivo por ULTIMO preserva a extensao — e a
    # ordem de prioridade dos cues decide ("aula" antes de "livro"). Sem sidecar
    # (stash montado a mao, cursos antigos): comportamento identico ao de antes.
    nomes_moodle: dict = {}
    sidecar = root / ".moodle_nomes.json"
    if sidecar.is_file():
        try:
            nomes_moodle = json.loads(sidecar.read_text(encoding="utf-8")) or {}
        except Exception:
            nomes_moodle = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        ftype = _classify_file_type(path.name)
        if not ftype:
            result.skipped.append(str(path))
            continue
        # .zip = código do professor por convenção (fica dentro do card);
        # demais tipos usam a heurística de nome existente.
        if ftype == "zip":
            category = "codigo-professor"
        else:
            modulo = str(nomes_moodle.get(f"{_card_for(path, root)}/{path.name}") or "")
            nome_para_categoria = f"{modulo} {path.name}" if modulo else path.name
            category = auto_detect_category(nome_para_categoria, is_image=(ftype == "image"),
                                            frases_do_plano=frases_do_plano)
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
        # ".tar.gz": stem devolve "x.tar" — o id herdaria o "tar" (tcp-chat-ctar).
        stem = Path(item.source_path).stem
        if stem.lower().endswith(".tar"):
            stem = stem[:-4]
        entries.append(FileEntry(
            source_path=item.source_path,
            file_type=item.file_type,
            category=item.category,
            title=stem,
            source_section=item.card_name,
            processing_mode=defaults.get("processing_mode", "auto"),
            ocr_language=defaults.get("ocr_language", DEFAULT_OCR_LANGUAGE),
            # Backend de extração só faz sentido p/ PDF/imagem. Código e ZIP vão
            # pro caminho Gemini (code_curation), nunca datalab — não herdam o
            # backend do perfil (senão a lista mostraria datalab pra código).
            preferred_backend=(defaults.get("preferred_backend", "auto")
                               if item.file_type in ("pdf", "image") else "auto"),
            datalab_mode=(defaults.get("datalab_mode", "accurate")
                          if item.file_type == "pdf" else "accurate"),
            document_profile=(defaults.get("document_profile", "auto")
                              if item.file_type in ("pdf", "image") else "auto"),
        ))
    return entries
