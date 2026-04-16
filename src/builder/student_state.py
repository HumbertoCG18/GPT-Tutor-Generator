"""
STUDENT_STATE v2: YAML puro compacto + baterias de estudo.

Gera e reconcilia student/STUDENT_STATE.md no formato YAML plano, e dá
suporte a consolidação/migração de unidades fechadas via summaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
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


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_battery_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter simples (chave: valor por linha)."""
    m = _FRONTMATTER_RE.match(content or "")
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


def derive_active_unit_progress(
    *,
    unit_slug: str,
    course_map_topics: list[tuple[str, str]],
    batteries_root: Path,
) -> list[ProgressRow]:
    """Para a unidade ativa, cruza a ordem do COURSE_MAP com os status
    das baterias existentes em batteries/<unit_slug>/*.md."""
    unit_dir = batteries_root / unit_slug
    by_slug: dict[str, str] = {}
    if unit_dir.is_dir():
        for md in sorted(unit_dir.glob("*.md")):
            fm = parse_battery_frontmatter(md.read_text(encoding="utf-8"))
            slug = fm.get("topic_slug") or md.stem
            status = fm.get("status") or "pendente"
            by_slug[slug] = status
    rows: list[ProgressRow] = []
    for slug, _label in course_map_topics:
        rows.append(ProgressRow(topic=slug, status=by_slug.get(slug, "pendente")))
    return rows


_ACTIVE_PROGRESS_BLOCK_RE = re.compile(
    r"(active_unit_progress:\s*\n)(?:\s*-\s*\{[^}]*\}\s*\n)*",
    re.MULTILINE,
)


def refresh_active_unit_progress(
    *,
    root_dir: Path,
    active_unit_slug: str,
    course_map_topics: list[tuple[str, str]],
) -> None:
    """Reconcilia o bloco active_unit_progress do STUDENT_STATE.md
    sem tocar nos outros campos."""
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return
    current = state_path.read_text(encoding="utf-8")
    rows = derive_active_unit_progress(
        unit_slug=active_unit_slug,
        course_map_topics=course_map_topics,
        batteries_root=root_dir / "student" / "batteries",
    )
    new_block = "active_unit_progress:\n" + "".join(
        f"  - {{topic: {r.topic}, status: {r.status}}}\n" for r in rows
    )
    if _ACTIVE_PROGRESS_BLOCK_RE.search(current):
        updated = _ACTIVE_PROGRESS_BLOCK_RE.sub(new_block, current, count=1)
    else:
        updated = current.replace("\n---\n", "\n" + new_block + "\n---\n", 1)
    state_path.write_text(updated, encoding="utf-8")
