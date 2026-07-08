"""Contratos do motor: tipos de resultado/contexto + Protocols dos 3 tiers.

Sem lógica de negócio — só shape. A implementação vive em window_provider.py,
disambiguator.py, anchor_engine.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol


@dataclass
class AnchorDecision:
    """Decisão do motor para uma entry (grão de bloco DISPLAY, não uuid).

    band ∈ {"alta","media","baixa",""}; flag=True => entra na fila humana / TIER 3.
    provider = qual WindowProvider rendeu a janela ("manual"|"labels"|"data"|"topic"|"").
    method = tier/caminho que decidiu ("janela-1"|"disamb"|"funil"|"d6"|...).
    window = janela DISPLAY considerada (para auditoria/serialização Dashboard).
    """
    block_ref: str
    conf: float = 0.0
    band: str = ""
    flag: bool = False
    provider: str = ""
    method: str = ""
    window: List[str] = field(default_factory=list)


@dataclass
class MotorContext:
    """Contexto READ-ONLY de um curso: blocos + card_block_map + lessons_index.

    blocks ficam ORDENADOS por period_start; _by_ref indexa id E block_uuid.
    course_name = nome da disciplina (manifest course.course_name / gold
    subject); tokens dele são BOILERPLATE local e saem das assinaturas de
    bloco no disambiguator ("" = sem desconto, comportamento FASE 0).
    """
    blocks: List[dict]
    card_block_map: Dict[str, dict]
    lessons_index: Dict[str, str]  # {date_iso: topico} (by_date do .lessons_index.json)
    course_name: str = ""
    _by_ref: Dict[str, dict] = field(default_factory=dict, repr=False)

    @classmethod
    def from_artifacts(
        cls,
        *,
        blocks: List[dict],
        card_block_map: Dict[str, dict],
        lessons_index: Dict[str, str],
        course_name: str = "",
    ) -> "MotorContext":
        ordered = sorted(blocks or [], key=lambda b: str(b.get("period_start") or ""))
        by_ref: Dict[str, dict] = {}
        for b in ordered:
            for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
                if key:
                    by_ref[key] = b
        return cls(
            blocks=ordered,
            card_block_map=dict(card_block_map or {}),
            lessons_index=dict(lessons_index or {}),
            course_name=str(course_name or ""),
            _by_ref=by_ref,
        )

    def block_by_ref(self, ref: str) -> Optional[dict]:
        return self._by_ref.get(str(ref or ""))


class WindowProvider(Protocol):
    """1º provider que rende janela não-vazia; [] = sem janela (funil-piso)."""
    def __call__(self, entry: dict, ctx: MotorContext) -> List[str]: ...


class Disambiguator(Protocol):
    """Escolhe DENTRO da janela (só roda se |janela| > 1)."""
    def __call__(self, entry: dict, window: List[str], ctx: MotorContext,
                 markdown: str = "") -> AnchorDecision: ...


class AnchorEngineProtocol(Protocol):
    """Orquestra tiers; None = sem âncora -> funil.

    Nome com sufixo Protocol: a implementação concreta anchor_engine.AnchorEngine
    tinha shadowing com este Protocol na FASE 0 (dívida do tracker)."""
    def resolve(self, entry: dict, ctx: MotorContext,
                markdown: str = "") -> Optional[AnchorDecision]: ...
