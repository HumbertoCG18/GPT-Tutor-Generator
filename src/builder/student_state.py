"""
STUDENT_STATE v2: YAML puro compacto + baterias de estudo.

Gera e reconcilia student/STUDENT_STATE.md no formato YAML plano, e dá
suporte a consolidação/migração de unidades fechadas via summaries.
"""
from __future__ import annotations

import re
import shutil
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


_SESSION_HEADER_RE = re.compile(r"^##\s*(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^-\s*(\*\*)?([^:]+):\*?\*?\s*(.+)$", re.MULTILINE)


def _extract_bullet_values(bullets: list[tuple[str, str]], key_prefix: str) -> list[str]:
    out: list[str] = []
    for key, value in bullets:
        if key.strip().lower().startswith(key_prefix):
            text = value.strip().strip(".")
            if text and text.lower() not in {"nenhuma", "[nenhuma]"}:
                out.append(text)
    return out


def render_unit_summary_md(
    *,
    unit_slug: str,
    closed_date: str,
    topic_order: list[str],
    batteries: list[tuple[str, str]],
) -> str:
    total_sessions = 0
    all_bullets: list[tuple[str, str]] = []
    for _name, content in batteries:
        total_sessions += len(_SESSION_HEADER_RE.findall(content))
        for m in _BULLET_RE.finditer(content):
            all_bullets.append((m.group(2), m.group(3)))

    resolvidas = _extract_bullet_values(all_bullets, "resolveu") + \
                 _extract_bullet_values(all_bullets, "dúvida")
    abertas = _extract_bullet_values(all_bullets, "em aberto")

    lines = [
        "---",
        f"unit: {unit_slug}",
        "status: consolidado",
        f"sessions_total: {total_sessions}",
        f"closed: {closed_date}",
        f"topics: [{', '.join(topic_order)}]",
        "---",
        "",
        f"**Tópicos cobertos:** {', '.join(topic_order)}",
        f"**Dúvidas resolvidas:** {', '.join(resolvidas) if resolvidas else 'nenhuma registrada'}",
        f"**Aberturas ainda em aberto:** {', '.join(abertas) if abertas else 'nenhuma'}",
        "",
    ]
    return "\n".join(lines)


class UnitNotReadyError(Exception):
    def __init__(self, unit_slug: str, pending: list[str]) -> None:
        super().__init__(f"Unit {unit_slug} not ready: pending {pending}")
        self.unit_slug = unit_slug
        self.pending = pending


@dataclass(frozen=True)
class ConsolidationResult:
    unit_slug: str
    summary_path: Path
    backup_path: Optional[Path]
    deleted_files: list[str]


def consolidate_unit(
    *,
    root_dir: Path,
    unit_slug: str,
    today: str,
    topic_order: list[str],
    force: bool = False,
) -> ConsolidationResult:
    batteries_root = root_dir / "student" / "batteries"
    unit_dir = batteries_root / unit_slug
    if not unit_dir.is_dir():
        raise FileNotFoundError(f"Unit directory not found: {unit_dir}")

    battery_files: list[tuple[str, str]] = []
    pending: list[str] = []
    for md in sorted(unit_dir.glob("*.md")):
        content = md.read_text(encoding="utf-8")
        fm = parse_battery_frontmatter(content)
        battery_files.append((md.name, content))
        if fm.get("status") != "compreendido" and not force:
            pending.append(fm.get("topic_slug") or md.stem)
    if pending and not force:
        raise UnitNotReadyError(unit_slug, pending)

    existing_summary = batteries_root / f"{unit_slug}.summary.md"
    revision_section = _read_existing_summary_revisions(existing_summary)
    summary_md = render_unit_summary_md(
        unit_slug=unit_slug,
        closed_date=today,
        topic_order=topic_order,
        batteries=battery_files,
    )
    if revision_section:
        summary_md = summary_md.rstrip() + "\n\n" + revision_section + "\n"

    backup_path = root_dir / "build" / "consolidation-backup" / today / unit_slug
    backup_path.mkdir(parents=True, exist_ok=True)
    for md in unit_dir.glob("*.md"):
        shutil.copy2(md, backup_path / md.name)
    if existing_summary.exists():
        shutil.copy2(existing_summary, backup_path / existing_summary.name)

    existing_summary.write_text(summary_md, encoding="utf-8")
    deleted = [p.name for p in unit_dir.glob("*.md")]
    shutil.rmtree(unit_dir)

    _update_student_state_after_consolidation(root_dir, unit_slug)

    return ConsolidationResult(
        unit_slug=unit_slug,
        summary_path=existing_summary,
        backup_path=backup_path,
        deleted_files=deleted,
    )


def _read_existing_summary_revisions(summary_path: Path) -> str:
    if not summary_path.exists():
        return ""
    text = summary_path.read_text(encoding="utf-8")
    idx = text.find("## Revisão ")
    return text[idx:].rstrip() if idx >= 0 else ""


def _update_student_state_after_consolidation(root_dir: Path, unit_slug: str) -> None:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")

    block_re = re.compile(r"active_unit_progress:\s*\n(?:\s*-\s*\{[^}]*\}\s*\n)*")
    text = block_re.sub("active_unit_progress: []\n", text, count=1)

    closed_re = re.compile(r"closed_units:\s*\[(.*?)\]")
    m = closed_re.search(text)
    if m:
        existing = [s.strip() for s in m.group(1).split(",") if s.strip()]
        if unit_slug not in existing:
            existing.append(unit_slug)
        text = closed_re.sub(f"closed_units: [{', '.join(existing)}]", text, count=1)
    else:
        text = text.replace("\n---\n", f"\nclosed_units: [{unit_slug}]\n\n---\n", 1)
    state_path.write_text(text, encoding="utf-8")
