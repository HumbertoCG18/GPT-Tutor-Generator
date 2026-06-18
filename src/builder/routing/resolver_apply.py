"""Helper compartilhado: montagem de inputs + aplicação do concept resolver.

Usado por produção (pedagogical_regeneration, atrás de flag) e pelo harness
(compare_resolver), eliminando duplicação da lógica de montagem de signals.

Por que aqui e não em engine.py: lógica de routing pertence ao pacote routing;
engine.py é reservado para orquestração de alto nível (non-negotiable do projeto).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import List, Optional, Tuple

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
from src.builder.extraction.entry_signals import collect_entry_unit_signals
from src.builder.routing.concept_resolver import resolve_material_assignment
from src.builder.routing.sequence import annotate_class_ordinals


def _is_material(entry: dict) -> bool:
    """Mesmo predicado do harness compare_resolver."""
    return str(entry.get("file_type") or "") == "pdf" or bool(entry.get("category"))


def load_lessons_index(root: Optional[Path]) -> Optional[dict]:
    """Carrega course/.lessons_index.json (índice course-level data->tópico).

    INFRA (não consumida ainda): a captação (build_lesson_topic_index no import)
    está ativa, mas o termo de fusão por lesson foi REVERTIDO — casar o tópico da
    aula contra os `concepts` ruidosos do Gemini regredia o gold (11->10). Será
    consumida pela alavanca 1, quando o `moodle_label` der a identidade LIMPA do
    material pra casar contra a lesson. Ausente/inválido -> None (degradação honesta).
    """
    if root is None:
        return None
    path = Path(root) / "course" / ".lessons_index.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def assemble_resolver_inputs(
    root: Optional[Path],
    entry: dict,
    code_curation: dict,
) -> Tuple[dict, dict, dict]:
    """Monta os três inputs que resolve_material_assignment precisa.

    Fiel ao harness compare_resolver (compare_repo:124-145): markdown cru,
    signals via collect_entry_unit_signals, summary da curation, e injeção
    de entry["concepts"] apenas quando summary.concepts existe.

    Retorna (entry_for_resolver, signals, summary).
    summary é {} quando ausente — passa como llm_curation=None ao resolver.
    """
    entry_id = str(entry.get("id") or "")
    rec = (code_curation.get("entries") or {}).get(entry_id) or {}
    summary_raw = rec.get("summary")
    summary: dict = summary_raw if isinstance(summary_raw, dict) else {}

    markdown = _entry_markdown_text_for_file_map(root, entry) if root is not None else ""
    signals = collect_entry_unit_signals(entry, markdown or "")

    entry_for_resolver = dict(entry)
    if summary.get("concepts"):
        entry_for_resolver["concepts"] = summary["concepts"]

    return entry_for_resolver, signals, summary


def apply_concept_resolver(
    entries: list,
    blocks: List[dict],
    units: List[dict],
    code_curation: dict,
    root: Optional[Path],
) -> list:
    """Aplica o resolver sobre os entries materiais, sobrescrevendo APENAS campos
    de bloco (computed_block_id, band, method, confidence + tag bloco: em auto_tags).

    Unit fields (computed_unit_slug, unit:/subunit: em auto_tags) ficam intocados —
    BLOCK-only cutover (Fase 3.3; a unidade é Fase 4).

    Idêntico ao harness: faz annotate_class_ordinals numa cópia dos blocks antes
    de resolver (o harness também faz isso antes do loop). Muta entries in-place.
    """
    blocks = annotate_class_ordinals(copy.deepcopy(blocks))

    for entry in entries:
        if not _is_material(entry):
            continue
        if not str(entry.get("computed_block_id") or "").strip():
            continue

        entry_for_resolver, signals, summary = assemble_resolver_inputs(root, entry, code_curation)
        assignment = resolve_material_assignment(
            entry_for_resolver,
            blocks,
            units,
            signals=signals,
            llm_curation=summary or None,
        )

        # Sobrescreve SÓ campos de bloco
        entry["computed_block_id"] = assignment["block_id"]
        entry["computed_block_confidence"] = assignment["confidence"]
        entry["computed_block_band"] = assignment["band"]
        entry["computed_block_method"] = assignment["method"]

        # Mirror de tag: troca bloco:<old> por bloco:<new> em auto_tags
        # (mesma mecânica de pedagogical_regeneration.py:110-112)
        new_block_id = assignment["block_id"]
        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("bloco:")]
        if new_block_id:
            tags.append(f"bloco:{new_block_id}")
        entry["auto_tags"] = tags

    return entries
