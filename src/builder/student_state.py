"""
STUDENT_STATE v2: YAML puro compacto + baterias de estudo.

Gera e reconcilia student/STUDENT_STATE.md no formato YAML plano, e dá
suporte a consolidação/migração de unidades fechadas via summaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class ActiveTopic:
    unit: str
    topic: str
    status: str
    sessions: int
    file: str


@dataclass(frozen=True)
class ProgressRow:
    topic: str
    status: str  # pendente | em_progresso | compreendido | revisao


@dataclass(frozen=True)
class RecentEntry:
    topic: str
    unit: str
    date: str


def render_student_state_md(
    *,
    course_name: str,
    student_nickname: str,
    today: str,
    active: Optional[ActiveTopic],
    active_unit_progress: Iterable[ProgressRow],
    recent: Iterable[RecentEntry],
    closed_units: Iterable[str],
    next_topic: str,
) -> str:
    lines = [
        "---",
        f"course: {course_name}",
        f"student: {student_nickname}",
        f"updated: {today}",
        "",
    ]
    if active is not None:
        lines += [
            "active:",
            f"  unit: {active.unit}",
            f"  topic: {active.topic}",
            f"  status: {active.status}",
            f"  sessions: {active.sessions}",
            f"  file: {active.file}",
            "",
        ]
    progress = list(active_unit_progress)
    if progress:
        lines.append("active_unit_progress:")
        for row in progress:
            lines.append(f"  - {{topic: {row.topic}, status: {row.status}}}")
        lines.append("")
    recent_list = list(recent)
    if recent_list:
        lines.append("recent:")
        for r in recent_list:
            lines.append(f"  - {{topic: {r.topic}, unit: {r.unit}, date: {r.date}}}")
        lines.append("")
    closed = list(closed_units)
    if closed:
        lines.append(f"closed_units: [{', '.join(closed)}]")
        lines.append("")
    if next_topic:
        lines.append(f"next_topic: {next_topic}")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)
