"""Status derivado de bloco. Read-only, puro.

`derive_block_status(block) -> str` retorna um de:
  - "ok"             : todos requisitos atendidos
  - "needs_unit"     : kind exige unit, faltando
  - "needs_topic"    : kind exige topic, faltando
  - "needs_files"    : kind exige files, sessao=0
  - "non_applicable" : kind nao-academico (feriado, atendimento, ...)
  - "needs_review"   : kind=unknown, curadoria manual

NUNCA persistido no JSON. Sempre derivado em read-time.
"""

from __future__ import annotations

from typing import Mapping

from .kinds import BlockKind, NON_ACADEMIC_KINDS, requires


def _truthy(block: Mapping[str, object], key: str) -> bool:
    val = block.get(key)
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, (int, float)):
        return val > 0
    return bool(val)


def derive_block_status(block: Mapping[str, object]) -> str:
    kind_raw = block.get("kind")
    try:
        kind = BlockKind(kind_raw) if isinstance(kind_raw, str) else BlockKind.UNKNOWN
    except ValueError:
        kind = BlockKind.UNKNOWN

    if kind == BlockKind.UNKNOWN:
        return "needs_review"

    if kind in NON_ACADEMIC_KINDS:
        return "non_applicable"

    need_unit = requires(kind, "unit")
    if need_unit is True and not _truthy(block, "unit_slug"):
        return "needs_unit"

    need_topic = requires(kind, "topic")
    if need_topic is True and not (
        _truthy(block, "primary_topic_label") or _truthy(block, "topic_text")
    ):
        return "needs_topic"

    need_files = requires(kind, "files")
    if need_files is True:
        sessions = block.get("sessions")
        if isinstance(sessions, list):
            n = len(sessions)
        else:
            try:
                n = int(sessions or 0)
            except (TypeError, ValueError):
                n = 0
        if n <= 0:
            return "needs_files"

    return "ok"
