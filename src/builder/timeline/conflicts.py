"""Guard de conflito entre override manual de bloco e auto-atribuicao forte.

Deteccao pura sobre blocos serializados (.timeline_index.json), sem recomputar
taxonomia. Override manual continua vencendo funcionalmente; este modulo so
torna o conflito visivel para health-check/UI.
"""

from __future__ import annotations

from typing import Iterable, List, Mapping

# _normalize_unit_slug: reusa o helper de teaching_plan (modulo leve, sem ciclo);
# evita 4a copia da normalizacao. Mesma fn existe em index.py (modulo pesado).
from src.builder.extraction.teaching_plan import _normalize_unit_slug

# Gate do fallback topic-derive abaixo (so vale para blocos SEM auto_unit_slug).
# A decisao primaria do auto e o matcher POSICIONAL, gravado em auto_unit_slug
# (index.py:2198-2204). O topic-derive cobre os blocos que o posicional NAO
# atribui mas que ainda recebem topico: nao-aula (source_kind != class, fora dos
# class_candidates), herdados por soft-continuation (unit_slug sem auto_unit_slug)
# e posicional-vazio. Esses serializam sem auto_unit_slug (so grava se truthy,
# index.py:932) porem com topic_candidates -> ramo alcancavel em prod (verificado
# 17/06). 0.65 = mesmo piso de confianca do voto de unidade do build.
UNIT_AUTO_MIN_CONFIDENCE = 0.65


def auto_suggested_unit(block: Mapping) -> tuple[str, float]:
    """(unit_slug, confidence) que o auto atribuiria, ignorando override.

    Precedencia: auto_unit_slug (decisao do matcher posicional) > topic-derive
    (fallback para blocos sem auto_unit_slug — nao-aula/herdados/posicional-vazio,
    que ainda tem topico). Abstem ("", 0.0) quando o topico e ambiguo, pouco
    confiante ou sem candidatos.
    """
    auto = str(block.get("auto_unit_slug") or "").strip()
    if auto:
        return (auto, float(block.get("unit_confidence") or 0.0))

    if block.get("topic_ambiguous"):
        return ("", 0.0)
    conf = float(block.get("primary_topic_confidence") or 0.0)
    if conf < UNIT_AUTO_MIN_CONFIDENCE:
        return ("", 0.0)
    candidates = block.get("topic_candidates") or []
    if not candidates:
        return ("", 0.0)
    # NOTA: usa o unit_slug do candidato de maior score (== topico vencedor).
    # O build resolve via _derive_unit_from_topic_match (normaliza vs taxonomia);
    # divergem so quando o slug do vencedor nao e unidade valida — caso raro que
    # no maximo gera um aviso extra/faltante, nunca erro.
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
