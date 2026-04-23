"""
STUDENT_STATE v2: YAML puro compacto + baterias de estudo.

Gera e reconcilia student/STUDENT_STATE.md no formato YAML plano, e dá
suporte a consolidação/migração de unidades fechadas via summaries.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from src.builder.extraction.teaching_plan import (
    _normalize_unit_slug,
    _parse_units_from_teaching_plan,
    _topic_text,
)
from src.utils.helpers import slugify


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
_ACTIVE_BLOCK_RE = re.compile(r"active:\s*\n(?:  .*\n)+", re.MULTILINE)
_RECENT_BLOCK_RE = re.compile(r"(recent:\s*\n)(?:\s*-\s*\{[^}]*\}\s*\n)*", re.MULTILINE)
_NEXT_TOPIC_RE = re.compile(r"next_topic:\s*.*", re.MULTILINE)
VALID_MANUAL_IMPORT_STATUSES = {"pendente", "em_progresso", "compreendido", "revisao"}


def _unit_number_from_title(unit_title: str) -> int:
    match = re.search(r"unidade(?:\s+de\s+aprendizagem)?\s+(\d+)", unit_title or "", re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 1


def _topic_outline_label(unit_title: str, topics: list) -> list[str]:
    unit_number = _unit_number_from_title(unit_title)
    counters: list[int] = []
    labels: list[str] = []
    for topic in topics:
        depth = 0
        if isinstance(topic, tuple) and len(topic) >= 2:
            try:
                depth = max(int(topic[1]), 0)
            except Exception:
                depth = 0
        while len(counters) <= depth:
            counters.append(0)
        counters = counters[:depth + 1]
        counters[depth] += 1
        for idx in range(depth + 1, len(counters)):
            counters[idx] = 0
        parts = [str(unit_number), *[str(value) for value in counters if value > 0]]
        labels.append(".".join(parts))
    return labels


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


def build_course_unit_topic_index(subject_profile) -> list[dict]:
    teaching_plan = getattr(subject_profile, "teaching_plan", "") or ""
    if not teaching_plan.strip():
        return []

    units: list[dict] = []
    for unit_title, topics in _parse_units_from_teaching_plan(teaching_plan):
        unit_slug = _normalize_unit_slug(unit_title)
        outline_labels = _topic_outline_label(unit_title, topics)
        topic_rows = []
        for idx, topic in enumerate(topics):
            topic_title = _topic_text(topic).strip()
            if not topic_title:
                continue
            topic_label = f"{outline_labels[idx]} - {topic_title}" if idx < len(outline_labels) else topic_title
            topic_rows.append(
                {
                    "topic_slug": slugify(topic_title),
                    "topic_title": topic_title,
                    "topic_label": topic_label,
                }
            )
        units.append(
            {
                "unit_slug": unit_slug,
                "unit_title": unit_title,
                "topics": topic_rows,
            }
        )
    return units


def parse_student_state_manual_import(raw: str, now_text: Optional[tuple[str, str]] = None) -> dict:
    frontmatter = parse_battery_frontmatter(raw)
    body = _FRONTMATTER_RE.sub("", raw or "", count=1).strip()
    if now_text is None:
        now_date = datetime.now().strftime("%d-%m-%y")
        now_time = datetime.now().strftime("%H-%M")
    else:
        now_date, now_time = now_text

    status = str(frontmatter.get("status") or "em_progresso").strip()
    if status not in VALID_MANUAL_IMPORT_STATUSES:
        status = "em_progresso"

    return {
        "unit_slug": str(frontmatter.get("unit") or "").strip(),
        "unit_title": str(frontmatter.get("unit_title") or "").strip(),
        "topic_slug": str(frontmatter.get("topic") or "").strip(),
        "topic_title": str(frontmatter.get("topic_title") or "").strip(),
        "status": status,
        "date": str(frontmatter.get("date") or now_date).strip(),
        "time": str(frontmatter.get("time") or now_time).strip(),
        "next_topic": str(frontmatter.get("next_topic") or "").strip(),
        "body": body,
    }


def validate_manual_import_selection(*, unit_slug: str, topic_slug: str, course_index: list[dict]) -> list[str]:
    unit = next((item for item in course_index if item.get("unit_slug") == unit_slug), None)
    if unit is None:
        return ["unit_slug"]
    if not any(topic.get("topic_slug") == topic_slug for topic in unit.get("topics", [])):
        return ["topic_slug"]
    return []


def course_topics_for_unit(course_index: list[dict], unit_slug: str) -> list[tuple[str, str]]:
    unit = next((item for item in course_index if item.get("unit_slug") == unit_slug), None)
    if not unit:
        return []
    return [
        (str(topic.get("topic_slug") or "").strip(), str(topic.get("topic_title") or "").strip())
        for topic in unit.get("topics", [])
        if str(topic.get("topic_slug") or "").strip()
    ]


def _battery_frontmatter_text(*, topic_title: str, topic_slug: str, unit_slug: str, status: str) -> str:
    return "\n".join(
        [
            "---",
            f"topic: {topic_title}",
            f"topic_slug: {topic_slug}",
            f"unit: {unit_slug}",
            f"status: {status}",
            "---",
            "",
        ]
    )


def _render_manual_session_block(*, date: str, time: str, session_number: int, status: str, body: str) -> str:
    lines = [
        f"## {date} {time} (sessao {session_number})",
        f"- Status: {status}",
    ]
    cleaned = (body or "").strip()
    if cleaned:
        lines.append(cleaned)
    lines.append("")
    return "\n".join(lines)


def save_manual_import_battery(root_dir: Path, payload: dict) -> Path:
    unit_slug = str(payload.get("unit_slug") or "").strip()
    topic_slug = str(payload.get("topic_slug") or "").strip()
    topic_title = str(payload.get("topic_title") or "").strip() or topic_slug.replace("-", " ").title()
    status = str(payload.get("status") or "em_progresso").strip() or "em_progresso"
    target = root_dir / "student" / "batteries" / unit_slug / f"{topic_slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        current = target.read_text(encoding="utf-8")
        frontmatter = parse_battery_frontmatter(current)
        session_number = len(_SESSION_HEADER_RE.findall(current)) + 1
        frontmatter_block = _FRONTMATTER_RE.match(current)
        prefix = frontmatter_block.group(0) if frontmatter_block else _battery_frontmatter_text(
            topic_title=topic_title,
            topic_slug=topic_slug,
            unit_slug=unit_slug,
            status=status,
        )
        existing_body = _FRONTMATTER_RE.sub("", current, count=1).rstrip()
        stored_status = str(frontmatter.get("status") or "").strip()
        if stored_status and stored_status != status:
            prefix = _battery_frontmatter_text(
                topic_title=str(frontmatter.get("topic") or topic_title).strip() or topic_title,
                topic_slug=str(frontmatter.get("topic_slug") or topic_slug).strip() or topic_slug,
                unit_slug=str(frontmatter.get("unit") or unit_slug).strip() or unit_slug,
                status=status,
            )
        content = prefix
        if existing_body:
            content += existing_body + "\n\n"
    else:
        session_number = 1
        content = _battery_frontmatter_text(
            topic_title=topic_title,
            topic_slug=topic_slug,
            unit_slug=unit_slug,
            status=status,
        )

    content += _render_manual_session_block(
        date=str(payload.get("date") or "").strip(),
        time=str(payload.get("time") or "").strip(),
        session_number=session_number,
        status=status,
        body=str(payload.get("body") or "").strip(),
    )
    target.write_text(content, encoding="utf-8")
    return target


def apply_manual_import_to_student_state(
    root_dir: Path,
    *,
    payload: dict,
    battery_rel_path: str,
    course_map_topics: list[tuple[str, str]],
) -> None:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        raise FileNotFoundError(f"Student state not found: {state_path}")

    state_text = state_path.read_text(encoding="utf-8")
    battery_path = root_dir / battery_rel_path
    battery_text = battery_path.read_text(encoding="utf-8")
    sessions = len(_SESSION_HEADER_RE.findall(battery_text))
    updated = str(payload.get("date") or "").strip()
    next_topic = str(payload.get("next_topic") or "").strip()
    active_block = "\n".join(
        [
            "active:",
            f"  unit: {payload['unit_slug']}",
            f"  topic: {payload['topic_slug']}",
            f"  status: {payload['status']}",
            f"  sessions: {sessions}",
            f"  file: {battery_rel_path}",
            "",
        ]
    )
    state_text = re.sub(r"updated:\s*.+", f"updated: {updated}", state_text, count=1)
    if _ACTIVE_BLOCK_RE.search(state_text):
        state_text = _ACTIVE_BLOCK_RE.sub(active_block, state_text, count=1)
    else:
        state_text = state_text.replace("\n---\n", "\n" + active_block + "---\n", 1)

    recent_line = f"  - {{topic: {payload['topic_slug']}, unit: {payload['unit_slug']}, date: {updated}}}\n"
    if _RECENT_BLOCK_RE.search(state_text):
        state_text = _RECENT_BLOCK_RE.sub(r"\1" + recent_line, state_text, count=1)
    else:
        state_text = state_text.replace("\n---\n", "\nrecent:\n" + recent_line + "\n---\n", 1)

    if next_topic:
        if _NEXT_TOPIC_RE.search(state_text):
            state_text = _NEXT_TOPIC_RE.sub(f"next_topic: {next_topic}", state_text, count=1)
        else:
            state_text = state_text.replace("\n---\n", f"\nnext_topic: {next_topic}\n\n---\n", 1)

    state_path.write_text(state_text, encoding="utf-8")
    refresh_active_unit_progress(
        root_dir=root_dir,
        active_unit_slug=str(payload.get("unit_slug") or "").strip(),
        course_map_topics=course_map_topics,
    )


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
    first_close = not existing_summary.exists()
    revision_section = _read_existing_summary_revisions(existing_summary)
    summary_md = render_unit_summary_md(
        unit_slug=unit_slug,
        closed_date=today,
        topic_order=topic_order,
        batteries=battery_files,
    )
    if not first_close:
        revision_title = f"## Revisão {today}"
        revision_body = f"**Reestudado:** {', '.join(topic_order)}"
        summary_md = summary_md.rstrip() + f"\n\n{revision_title}\n{revision_body}\n"
        if revision_section:
            summary_md += "\n" + revision_section + "\n"

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


@dataclass(frozen=True)
class MigrationResult:
    skipped: bool
    backup_dir: Path
    created_batteries: list[str]


_V1_MARKER = "## Histórico de sessões"
_HISTORY_ROW_RE = re.compile(
    r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
    r"\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE,
)


def detect_state_version(root_dir: Path) -> str:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return "none"
    text = state_path.read_text(encoding="utf-8")
    if _V1_MARKER in text:
        return "v1"
    if "active_unit_progress:" in text:
        return "v2"
    return "unknown"


def _normalize_status_v1(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "_")
    if s in {"compreendido", "em_progresso", "pendente", "revisao"}:
        return s
    if "dúvida" in s or "duvida" in s:
        return "em_progresso"
    return "em_progresso"


def migrate_v1_to_v2(
    *,
    root_dir: Path,
    course_map_units: list[tuple[str, list[tuple[str, str]]]],
) -> MigrationResult:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = root_dir / "build" / "migration-v1-backup" / today

    if detect_state_version(root_dir) != "v1":
        return MigrationResult(skipped=True, backup_dir=backup_dir, created_batteries=[])

    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(state_path, backup_dir / "STUDENT_STATE.md")

    text = state_path.read_text(encoding="utf-8")
    rows = _HISTORY_ROW_RE.findall(text)

    sessions_by_topic: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for date, topic_label, unit_label, status, duvidas in rows:
        unit_slug = slugify(unit_label) or unit_label.strip()
        topic_slug = slugify(topic_label)
        key = (unit_slug, topic_slug)
        sessions_by_topic.setdefault(key, []).append(
            (date, _normalize_status_v1(status), (duvidas or "").strip())
        )

    all_topics = [t for _u, topics in course_map_units for t in topics]
    label_by_slug = {slug: label for slug, label in all_topics}

    created: list[str] = []
    for (unit_slug, topic_slug), sessions in sessions_by_topic.items():
        dir_ = root_dir / "student" / "batteries" / unit_slug
        dir_.mkdir(parents=True, exist_ok=True)
        final_status = sessions[-1][1]
        topic_label = label_by_slug.get(
            topic_slug,
            topic_slug.replace("-", " ").capitalize(),
        )
        lines = [
            "---",
            f"topic: {topic_label}",
            f"topic_slug: {topic_slug}",
            f"unit: {unit_slug}",
            f"status: {final_status}",
            "---",
            "",
        ]
        for i, (date, status, duvidas) in enumerate(sessions, 1):
            lines.append(f"## {date} (sessão {i})")
            lines.append(f"- Status: {status}")
            if duvidas and duvidas.lower() not in {"[nenhuma]", "nenhuma", ""}:
                lines.append(f"- Dúvidas: {duvidas}")
            lines.append("")
        (dir_ / f"{topic_slug}.md").write_text("\n".join(lines), encoding="utf-8")
        created.append(f"{unit_slug}/{topic_slug}.md")

    course_name = ""
    student_nickname = ""
    m_course = re.search(r"^course:\s*(.+)$", text, re.MULTILINE)
    m_student = re.search(r"^student:\s*(.+)$", text, re.MULTILINE)
    if m_course:
        course_name = m_course.group(1).strip()
    if m_student:
        student_nickname = m_student.group(1).strip()

    new_state = render_student_state_md(
        course_name=course_name or "Curso",
        student_nickname=student_nickname or "Aluno",
        today=today,
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )
    state_path.write_text(new_state, encoding="utf-8")

    for unit_slug, topics in course_map_units:
        unit_dir = root_dir / "student" / "batteries" / unit_slug
        if not unit_dir.is_dir():
            continue
        statuses = [
            parse_battery_frontmatter(
                (unit_dir / f"{slug}.md").read_text(encoding="utf-8")
            ).get("status")
            for slug, _ in topics
            if (unit_dir / f"{slug}.md").exists()
        ]
        if statuses and all(s == "compreendido" for s in statuses):
            try:
                consolidate_unit(
                    root_dir=root_dir,
                    unit_slug=unit_slug,
                    today=today,
                    topic_order=[slug for slug, _ in topics],
                )
            except (UnitNotReadyError, FileNotFoundError):
                pass

    return MigrationResult(skipped=False, backup_dir=backup_dir, created_batteries=created)
