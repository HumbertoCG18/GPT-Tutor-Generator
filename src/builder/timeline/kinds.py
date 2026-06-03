"""BlockKind enum + requirements + display metadata.

Single source of truth para classificacao de blocos do cronograma.
Enum fechado (14 valores) catalogado a partir de auditoria de 5 cursos
(92 blocos analisados via scripts/audit_timeline.py).

Novo kind exige: 1 entrada aqui + 1 keyword em classifier.KIND_KEYWORDS.
Zero refactor no resto do pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet


class BlockKind(str, Enum):
    CLASS = "class"
    ASSESSMENT = "assessment"
    REVIEW = "review"
    HOLIDAY = "holiday"
    SUSPENDED = "suspended"
    MAKEUP = "makeup"
    ACADEMIC_EVENT = "academic_event"
    OFFICE_HOURS = "office_hours"
    WORKSHOP = "workshop"
    DELIVERABLE = "deliverable"
    PLANNING = "planning"
    RESERVED = "reserved"
    RESULTS = "results"
    OVERVIEW = "overview"
    UNKNOWN = "unknown"


# Campos exigidos por kind para status=ok.
# Valores: True=obrigatorio, False=nao-aplicavel, "inherit"=herda do parent.
KIND_REQUIREMENTS: Dict[BlockKind, Dict[str, object]] = {
    BlockKind.CLASS:         {"unit": True,      "topic": True,  "files": True},
    BlockKind.ASSESSMENT:    {"unit": False,     "topic": True,  "files": False},
    BlockKind.REVIEW:        {"unit": "inherit", "topic": False, "files": False},
    BlockKind.MAKEUP:        {"unit": "inherit", "topic": True,  "files": True},
    # DELIVERABLE/trabalho atravessa conteudo de varias unidades — unit nao
    # obrigatorio (semana de trabalho/entrega nao mapeia 1 unidade unica).
    BlockKind.DELIVERABLE:   {"unit": False,     "topic": True,  "files": True},
    BlockKind.WORKSHOP:      {"unit": False,     "topic": True,  "files": False},
    # OVERVIEW: aula de apresentacao/introducao/plano de ensino. Academica
    # (visivel ao aluno) mas pre-unidade — nao exige unit/topic/files.
    BlockKind.OVERVIEW:      {"unit": False,     "topic": False, "files": False},
    BlockKind.HOLIDAY:        {"unit": False, "topic": False, "files": False},
    BlockKind.SUSPENDED:      {"unit": False, "topic": False, "files": False},
    BlockKind.ACADEMIC_EVENT: {"unit": False, "topic": False, "files": False},
    BlockKind.OFFICE_HOURS:   {"unit": False, "topic": False, "files": False},
    BlockKind.PLANNING:       {"unit": False, "topic": False, "files": False},
    BlockKind.RESERVED:       {"unit": False, "topic": False, "files": False},
    BlockKind.RESULTS:        {"unit": False, "topic": False, "files": False},
    BlockKind.UNKNOWN:        {"unit": False, "topic": False, "files": False},
}


# Lookup table de UI. Driver unico de icone/cor/label.
KIND_DISPLAY: Dict[BlockKind, Dict[str, str]] = {
    BlockKind.CLASS:          {"icon": "📚", "label": "Aula",              "color": "blue"},
    BlockKind.ASSESSMENT:     {"icon": "📝", "label": "Avaliação",         "color": "red"},
    BlockKind.REVIEW:         {"icon": "🔁", "label": "Revisão",           "color": "orange"},
    BlockKind.HOLIDAY:        {"icon": "🏖", "label": "Feriado",           "color": "gray"},
    BlockKind.SUSPENDED:      {"icon": "⏸",  "label": "Suspensão",         "color": "gray"},
    BlockKind.MAKEUP:         {"icon": "🔄", "label": "Reposição",         "color": "purple"},
    BlockKind.ACADEMIC_EVENT: {"icon": "📅", "label": "Evento acadêmico",  "color": "teal"},
    BlockKind.OFFICE_HOURS:   {"icon": "💬", "label": "Atendimento",       "color": "cyan"},
    BlockKind.WORKSHOP:       {"icon": "🛠", "label": "Oficina",           "color": "indigo"},
    BlockKind.DELIVERABLE:    {"icon": "📤", "label": "Entrega",           "color": "pink"},
    BlockKind.PLANNING:       {"icon": "🗓", "label": "Planejamento",      "color": "gray"},
    BlockKind.RESERVED:       {"icon": "⏳", "label": "Reserva",           "color": "gray"},
    BlockKind.RESULTS:        {"icon": "📊", "label": "Resultados",        "color": "green"},
    BlockKind.OVERVIEW:       {"icon": "📋", "label": "Introdução",        "color": "blue"},
    BlockKind.UNKNOWN:        {"icon": "❓", "label": "Não classificado",  "color": "yellow"},
}


# Conjunto de kinds nao-academicos (sem unit/topic/files esperados).
NON_ACADEMIC_KINDS: FrozenSet[BlockKind] = frozenset({
    BlockKind.HOLIDAY,
    BlockKind.SUSPENDED,
    BlockKind.ACADEMIC_EVENT,
    BlockKind.OFFICE_HOURS,
    BlockKind.PLANNING,
    BlockKind.RESERVED,
    BlockKind.RESULTS,
})


def requires(kind: BlockKind, field: str) -> object:
    """Retorna requirement do campo: True/False/'inherit'."""
    return KIND_REQUIREMENTS.get(kind, {}).get(field, False)
