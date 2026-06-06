"""Guard de conflito entre override manual de bloco e auto-atribuicao forte.

Deteccao pura sobre blocos serializados (.timeline_index.json), sem recomputar
taxonomia. Override manual continua vencendo funcionalmente; este modulo so
torna o conflito visivel para health-check/UI.
"""

from __future__ import annotations

from typing import Iterable, List, Mapping

from src.builder.extraction.teaching_plan import _normalize_unit_slug

# Espelha o gate de topic-derive do build (index.py): o auto so "teria decidido"
# a unidade quando o topico primario e confiante e nao-ambiguo.
UNIT_AUTO_MIN_CONFIDENCE = 0.65


def auto_suggested_unit(block: Mapping) -> tuple[str, float]:
    """(unit_slug, confidence) que o auto atribuiria, ignorando override.

    Abstem ("", 0.0) quando o topico e ambiguo, pouco confiante, ou sem
    candidatos — espelhando exatamente quando o build NAO topic-derivaria.
    """
    if block.get("topic_ambiguous"):
        return ("", 0.0)
    conf = float(block.get("primary_topic_confidence") or 0.0)
    if conf < UNIT_AUTO_MIN_CONFIDENCE:
        return ("", 0.0)
    candidates = block.get("topic_candidates") or []
    if not candidates:
        return ("", 0.0)
    unit = str((candidates[0] or {}).get("unit_slug") or "")
    return (unit, conf) if unit else ("", 0.0)


def detect_block_conflicts(block: Mapping) -> List[dict]:
    """Conflitos override-vs-auto de UM bloco (unidade e kind)."""
    out: List[dict] = []
    block_id = str(block.get("id") or "")

    manual_unit = str(block.get("block_manual_unit_slug") or "").strip()
    if manual_unit:
        auto_unit, conf = auto_suggested_unit(block)
        if auto_unit and _normalize_unit_slug(auto_unit) != _normalize_unit_slug(manual_unit):
            out.append({
                "block_id": block_id,
                "field": "unit",
                "manual": manual_unit,
                "auto": auto_unit,
                "confidence": conf,
            })

    manual_kind = str(block.get("manual_kind_override") or "").strip()
    source_kind = str(block.get("source_kind") or "").strip()
    if manual_kind and source_kind and manual_kind != source_kind:
        out.append({
            "block_id": block_id,
            "field": "kind",
            "manual": manual_kind,
            "auto": source_kind,
            "confidence": 1.0,
        })
    return out


def detect_timeline_conflicts(blocks: Iterable[Mapping]) -> List[dict]:
    """Achata detect_block_conflicts sobre todos os blocos."""
    result: List[dict] = []
    for block in blocks or []:
        if isinstance(block, Mapping):
            result.extend(detect_block_conflicts(block))
    return result
