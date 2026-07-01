from __future__ import annotations

import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.helpers import write_text, write_json_manifest, slugify

logger = logging.getLogger(__name__)


def _entry_dedup_tokens(entry) -> tuple[str, str]:
    """(extensão, pasta-imediata) do source_path, para o sufixo do dedup."""
    sp = str(getattr(entry, "source_path", "") or "")
    p = Path(sp)
    return p.suffix.lstrip(".").lower(), p.parent.name


def _dedup_entry_id(entry_id: str, existing_ids: set, *, ext: str = "", folder: str = "") -> str:
    """Id colidiu: sufixa EXTENSÃO, depois pasta, depois contador.

    Ids são diretórios de assets (sobrescrita silenciosa, bug B5) — nunca colidir.
    Extensão distingue o caso real (mesmo nome, formato diferente: pdf×zip, thy×zip);
    pasta distingue mesmo-nome-mesma-extensão em cards diferentes; contador é o último
    recurso. NÃO retroativo: só a entry sendo inserida. (fix c v2: antes sufixava categoria.)
    """
    if entry_id not in existing_ids:
        return entry_id
    ext = slugify(ext) if ext else ""
    folder = slugify(folder) if folder else ""
    for suffix in (ext, folder):
        if suffix:
            candidate = f"{entry_id}-{suffix}"
            if candidate not in existing_ids:
                return candidate
    base = f"{entry_id}-{ext}" if ext else entry_id
    i = 2
    candidate = f"{base}-{i}"
    while candidate in existing_ids:
        i += 1
        candidate = f"{base}-{i}"
    return candidate


def assign_dedup_id(entry, existing_ids: set) -> str:
    """Dedup de id para os laços de build BATCH (espelha o caminho single-entry).

    Se o id base do entry colide com um já presente em existing_ids, seta
    entry.id_override (sufixo de extensão/pasta / contador via _dedup_entry_id) para
    que TODO o pipeline use o id final. Registra o id final em existing_ids e o
    retorna. Sem colisão, mantém o id base e não toca id_override.
    """
    base_id = entry.id()
    final_id = base_id
    if base_id in existing_ids:
        ext, folder = _entry_dedup_tokens(entry)
        final_id = _dedup_entry_id(base_id, existing_ids, ext=ext, folder=folder)
        entry.id_override = final_id
        logger.warning(
            "Entry id collision: %s -> %s (ext=%s folder=%s)",
            base_id, final_id, ext, folder,
        )
    existing_ids.add(final_id)
    return final_id


def process_single_impl(
    builder,
    entry,
    *,
    force: bool = False,
    app_name: str,
    has_pymupdf: bool,
    has_pymupdf4llm: bool,
    has_pdfplumber: bool,
    has_datalab_api_key_fn,
    docling_cli,
    has_docling_python_api_fn,
    marker_cli,
) -> str:
    manifest_path = builder.root_dir / "manifest.json"

    builder._create_structure()

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest = builder._compact_manifest(manifest)
    else:
        builder._write_root_files()
        manifest = {
            "app": app_name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "course": builder.course_meta,
            "options": builder.options,
            "environment": {
                "python": sys.version.split()[0],
                "pymupdf": has_pymupdf,
                "pymupdf4llm": has_pymupdf4llm,
                "pdfplumber": has_pdfplumber,
                "datalab_api": has_datalab_api_key_fn(),
                "docling_cli": bool(docling_cli),
                "docling_python": has_docling_python_api_fn(),
                "marker_cli": bool(marker_cli),
            },
            "entries": [],
            "logs": [],
        }

    existing_entries = manifest.get("entries", [])
    existing_entry = next(
        (e for e in existing_entries if e.get("source_path") == entry.source_path),
        None,
    )
    if existing_entry is not None:
        if not force:
            logger.info("Entry already processed: %s", entry.source_path)
            return "already_exists"
        # Usa o id que está no manifest (pode ser deduplicado via id_override),
        # não entry.id() que recomputa do source_path e retornaria o id base —
        # o qual pode pertencer a outra entry (reintroduziria o bug B5).
        old_id = existing_entry["id"]
        logger.info("Reprocessing (force): removing old entry %s", old_id)
        builder.unprocess(old_id)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    # Dedup de id ANTES do processamento (bug B5): se o id colide com entry
    # de OUTRO source_path, seta entry.id_override para que TODO o pipeline
    # (raw/, staging/assets/, manual-review/, manifest) use o id final
    # consistente — dedup pós-processamento deixava os assets em disco no id
    # antigo, compartilhados com a entry original (sobrescrita + unprocess
    # de uma apagava os arquivos da outra). O fluxo already_exists/force
    # (acima) já garante que o mesmo source_path não chega aqui duas vezes,
    # então toda colisão aqui é de path diferente.
    existing_ids = {e.get("id") for e in manifest.get("entries", []) if e.get("id")}
    base_id = entry.id()
    if base_id in existing_ids:
        ext, folder = _entry_dedup_tokens(entry)
        entry.id_override = _dedup_entry_id(base_id, existing_ids, ext=ext, folder=folder)
        logger.warning(
            "Entry id collision: %s -> %s (ext=%s folder=%s)",
            base_id, entry.id_override, ext, folder,
        )

    logger.info("Processing single entry: %s (%s)", entry.title, entry.file_type)
    item_result = builder._process_entry(entry)
    manifest["entries"].append(item_result)
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).extend(builder.logs)
    builder.logs = []
    manifest = builder._compact_manifest(manifest)

    write_json_manifest(manifest_path, manifest)
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._write_build_report(manifest)

    builder._regenerate_pedagogical_files(manifest)
    write_json_manifest(manifest_path, manifest)

    logger.info("Single entry processed: %s", entry.id())
    return "ok"


ASSET_PATH_KEYS = (
    "raw_target", "base_markdown", "advanced_markdown", "advanced_markdown_raw",
    "manual_review", "images_dir", "tables_dir", "table_detection_dir",
    "advanced_asset_dir", "asset_dir", "advanced_metadata_path",
    "approved_markdown", "curated_markdown", "rendered_pages_dir",
)


def _entry_asset_paths(entry: dict) -> List[str]:
    """Paths de asset (relativos ao repo) do entry + filhos de zip
    (``extracted_files``). Inclui os filhos para o unprocess de um ZIP não deixar
    resíduo das entries virtuais extraídas (o caminho antigo só limpava o entry
    de topo → assets dos filhos ficavam órfãos em disco)."""
    out: List[str] = []
    sources = [entry, *(c for c in (entry.get("extracted_files") or []) if isinstance(c, dict))]
    for src in sources:
        for key in ASSET_PATH_KEYS:
            val = src.get(key)
            if val:
                out.append(val)
    return out


def _remove_paths(root_dir, rel_paths: List[str], *, log_prefix: str = "") -> int:
    removed_count = 0
    for rel_path in rel_paths:
        full = root_dir / rel_path
        try:
            if full.is_dir():
                shutil.rmtree(full)
                removed_count += 1
            elif full.is_file():
                full.unlink()
                removed_count += 1
        except Exception as exc:
            prefix = f"{log_prefix}: " if log_prefix else ""
            logger.warning("%snão foi possível remover %s: %s", prefix, full, exc)
    return removed_count


def unprocess(builder, entry_id: str) -> bool:
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("No manifest found at %s", manifest_path)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    builder.course_meta = builder._effective_course_meta(manifest)

    target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
    if not target:
        logger.warning("Entry not found in manifest: %s", entry_id)
        return False

    paths_to_remove: List[str] = _entry_asset_paths(target)

    removed_count = _remove_paths(builder.root_dir, paths_to_remove, log_prefix="Could not remove")
    removed_count += builder._remove_entry_consolidated_images(entry_id)

    manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest = builder._compact_manifest(manifest)

    write_json_manifest(manifest_path, manifest)
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)

    # Purga sidecars derivativos para evitar resíduo de entry removido
    try:
        builder._prune_stale_code_curation()
    except Exception as exc:
        logger.warning("unprocess: prune code_curation falhou: %s", exc)
    try:
        builder._prune_stale_image_curation()
    except Exception as exc:
        logger.warning("unprocess: prune image_curation falhou: %s", exc)
    try:
        builder._regenerate_pedagogical_files(manifest)
        write_json_manifest(manifest_path, manifest)
    except Exception as exc:
        logger.warning("unprocess: regeneração pedagógica falhou: %s", exc)

    logger.info("Unprocessed entry %s (%d files removed)", entry_id, removed_count)
    return True


def sweep_orphans(builder) -> Dict[str, object]:
    """Retroativo: pruna curations + regenera sidecars derivativos.

    Não reprocessa entries (zero custo de extractor/AI). Útil para limpar
    resíduos deixados por unprocess/reject anteriores à correção.

    Returns dict com counts e status de cada etapa.
    """
    report: Dict[str, object] = {
        "code_curation_removed": 0,
        "image_curation_removed": 0,
        "regenerated": False,
        "errors": [],
    }

    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        report["errors"].append("manifest.json não encontrado")
        return report

    try:
        report["code_curation_removed"] = builder._prune_stale_code_curation()
    except Exception as exc:
        report["errors"].append(f"prune code_curation: {exc}")

    try:
        report["image_curation_removed"] = builder._prune_stale_image_curation()
    except Exception as exc:
        report["errors"].append(f"prune image_curation: {exc}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        builder.course_meta = builder._effective_course_meta(manifest)
        builder._regenerate_pedagogical_files(manifest)
        write_json_manifest(manifest_path, manifest)
        report["regenerated"] = True
    except Exception as exc:
        report["errors"].append(f"regen pedagogical: {exc}")

    logger.info(
        "[sweep_orphans] code=%s img=%s regen=%s errors=%s",
        report["code_curation_removed"],
        report["image_curation_removed"],
        report["regenerated"],
        len(report["errors"]),
    )
    return report


def reject(builder, entry_id: str) -> Optional[Dict[str, object]]:
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("reject: manifest não encontrado em %s", manifest_path)
        return None

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
    if not target:
        logger.warning("reject: entry %s não encontrada no manifest", entry_id)
        return None

    entry_data = dict(target)

    keys_to_clean = [
        "base_markdown",
        "advanced_markdown",
        "advanced_markdown_raw",
        "manual_review",
        "images_dir",
        "tables_dir",
        "table_detection_dir",
        "advanced_asset_dir",
        "advanced_metadata_path",
        "approved_markdown",
        "curated_markdown",
        "rendered_pages_dir",
    ]
    rel_paths = [target.get(key) for key in keys_to_clean if target.get(key)]
    removed_count = _remove_paths(builder.root_dir, rel_paths, log_prefix="reject")
    removed_count += builder._remove_entry_consolidated_images(entry_id)

    manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("logs", []).append(
        {
            "entry": entry_id,
            "step": "curator_reject",
            "status": "ok",
        }
    )
    manifest = builder._compact_manifest(manifest)

    write_json_manifest(manifest_path, manifest)
    builder._write_source_registry(manifest)
    builder._write_bundle_seed(manifest)
    builder._resolve_content_images()

    # Purga sidecars derivativos (mesma simetria de unprocess)
    try:
        builder._prune_stale_code_curation()
    except Exception as exc:
        logger.warning("reject: prune code_curation falhou: %s", exc)
    try:
        builder._prune_stale_image_curation()
    except Exception as exc:
        logger.warning("reject: prune image_curation falhou: %s", exc)
    try:
        builder._regenerate_pedagogical_files(manifest)
        write_json_manifest(manifest_path, manifest)
    except Exception as exc:
        logger.warning("reject: regeneração pedagógica falhou: %s", exc)

    logger.info("Rejected entry %s (%d files removed, raw preserved)", entry_id, removed_count)
    return entry_data
