# Student State Manual Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken `FILE_MAP` button with a `Student State` import flow that validates tutor-generated session markdown against the course structure and saves it into canonical student battery/state files.

**Architecture:** Add a dedicated Tkinter window under `src/ui/` and keep file mutation logic inside focused student-state artifact helpers so UI code only orchestrates parsing, validation, and user feedback. Reuse existing teaching-plan parsing and student-state conventions instead of inventing parallel formats.

**Tech Stack:** Python, tkinter, existing builder artifact helpers, pytest

---

### Task 1: Map Canonical Course Units And Topics For UI Validation

**Files:**
- Modify: `src/builder/artifacts/student_state.py`
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Write the failing tests**

```python
from src.builder.artifacts.student_state import build_course_unit_topic_index


def test_build_course_unit_topic_index_returns_unit_and_topic_slugs():
    subject = type("Subject", (), {
        "teaching_plan": "\n".join(
            [
                "Unidade 1 - Limites",
                "- Definicao de limite",
                "- Continuidade",
            ]
        )
    })()

    index = build_course_unit_topic_index(subject)

    assert index[0]["unit_slug"] == "unidade-01-limites"
    assert index[0]["topics"][0]["topic_slug"] == "definicao-de-limite"


def test_build_course_unit_topic_index_returns_empty_without_teaching_plan():
    subject = type("Subject", (), {"teaching_plan": ""})()
    assert build_course_unit_topic_index(subject) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: FAIL with `ImportError` or missing function for `build_course_unit_topic_index`

- [ ] **Step 3: Write minimal implementation**

```python
from src.builder.extraction.teaching_plan import _normalize_unit_slug, _parse_units_from_teaching_plan, _topic_text
from src.utils.helpers import slugify


def build_course_unit_topic_index(subject_profile) -> list[dict]:
    teaching_plan = getattr(subject_profile, "teaching_plan", "") or ""
    if not teaching_plan.strip():
        return []

    units = []
    for unit_title, topics in _parse_units_from_teaching_plan(teaching_plan):
        unit_slug = _normalize_unit_slug(unit_title)
        topic_rows = []
        for topic in topics:
            text = _topic_text(topic).strip()
            if not text:
                continue
            topic_rows.append(
                {
                    "topic_slug": slugify(text),
                    "topic_title": text,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: PASS for the two new tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_student_state_manual_import.py src/builder/artifacts/student_state.py
git commit -m "feat: add student state course topic index"
```

### Task 2: Parse And Normalize Tutor Import Markdown

**Files:**
- Modify: `src/builder/artifacts/student_state.py`
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Write the failing tests**

```python
from src.builder.artifacts.student_state import parse_student_state_manual_import


def test_parse_student_state_manual_import_reads_frontmatter_and_body():
    raw = """---
unit: unidade-01-limites
unit_title: Unidade 1 - Limites
topic: definicao-de-limite
topic_title: Definicao de limite
status: em_progresso
date: 22-04-26
time: 14-35
next_topic: continuidade
---

## Resumo
Conteudo estudado.
"""

    parsed = parse_student_state_manual_import(raw)

    assert parsed["unit_slug"] == "unidade-01-limites"
    assert parsed["topic_slug"] == "definicao-de-limite"
    assert parsed["status"] == "em_progresso"
    assert "Conteudo estudado." in parsed["body"]


def test_parse_student_state_manual_import_defaults_missing_date_time(monkeypatch):
    raw = """---
unit: unidade-01-limites
topic: definicao-de-limite
status: compreendido
---
texto
"""

    parsed = parse_student_state_manual_import(raw, now_text=("22-04-26", "14-35"))

    assert parsed["date"] == "22-04-26"
    assert parsed["time"] == "14-35"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: FAIL with missing `parse_student_state_manual_import`

- [ ] **Step 3: Write minimal implementation**

```python
VALID_MANUAL_IMPORT_STATUSES = {"pendente", "em_progresso", "compreendido", "revisao"}


def parse_student_state_manual_import(raw: str, now_text: tuple[str, str] | None = None) -> dict:
    frontmatter = parse_battery_frontmatter(raw)
    body = _FRONTMATTER_RE.sub("", raw or "", count=1).strip()
    now_date, now_time = now_text or datetime.now().strftime("%d-%m-%y"), datetime.now().strftime("%H-%M")
    status = str(frontmatter.get("status") or "em_progresso").strip()
    return {
        "unit_slug": str(frontmatter.get("unit") or "").strip(),
        "unit_title": str(frontmatter.get("unit_title") or "").strip(),
        "topic_slug": str(frontmatter.get("topic") or "").strip(),
        "topic_title": str(frontmatter.get("topic_title") or "").strip(),
        "status": status if status in VALID_MANUAL_IMPORT_STATUSES else "em_progresso",
        "date": str(frontmatter.get("date") or now_date).strip(),
        "time": str(frontmatter.get("time") or now_time).strip(),
        "next_topic": str(frontmatter.get("next_topic") or "").strip(),
        "body": body,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: PASS for parser tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_student_state_manual_import.py src/builder/artifacts/student_state.py
git commit -m "feat: parse student state manual import markdown"
```

### Task 3: Validate Imports And Persist Topic Batteries

**Files:**
- Modify: `src/builder/artifacts/student_state.py`
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from src.builder.artifacts.student_state import save_manual_import_battery


def test_save_manual_import_battery_creates_new_topic_file(tmp_path: Path):
    payload = {
        "unit_slug": "unidade-01-limites",
        "unit_title": "Unidade 1 - Limites",
        "topic_slug": "definicao-de-limite",
        "topic_title": "Definicao de limite",
        "status": "em_progresso",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "continuidade",
        "body": "## Resumo\nConteudo estudado.\n",
    }
    save_manual_import_battery(tmp_path, payload)

    created = tmp_path / "student" / "batteries" / "unidade-01-limites" / "definicao-de-limite.md"
    text = created.read_text(encoding="utf-8")
    assert "topic_slug: definicao-de-limite" in text
    assert "## 22-04-26 14-35 (sessao 1)" in text


def test_save_manual_import_battery_appends_existing_topic_file(tmp_path: Path):
    target = tmp_path / "student" / "batteries" / "unidade-01-limites"
    target.mkdir(parents=True)
    existing = target / "definicao-de-limite.md"
    existing.write_text(
        "\n".join(
            [
                "---",
                "topic: Definicao de limite",
                "topic_slug: definicao-de-limite",
                "unit: unidade-01-limites",
                "status: em_progresso",
                "---",
                "",
                "## 21-04-26 10-00 (sessao 1)",
                "- Status: em_progresso",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = {
        "unit_slug": "unidade-01-limites",
        "unit_title": "Unidade 1 - Limites",
        "topic_slug": "definicao-de-limite",
        "topic_title": "Definicao de limite",
        "status": "compreendido",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "",
        "body": "## Resumo\nConteudo estudado.\n",
    }
    save_manual_import_battery(tmp_path, payload)

    text = existing.read_text(encoding="utf-8")
    assert "## 22-04-26 14-35 (sessao 2)" in text
    assert text.count("## ") == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: FAIL with missing `save_manual_import_battery`

- [ ] **Step 3: Write minimal implementation**

```python
def save_manual_import_battery(root_dir: Path, payload: dict) -> Path:
    unit_slug = payload["unit_slug"]
    topic_slug = payload["topic_slug"]
    topic_title = payload["topic_title"] or topic_slug.replace("-", " ").title()
    status = payload["status"]
    target = root_dir / "student" / "batteries" / unit_slug / f"{topic_slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        current = target.read_text(encoding="utf-8")
        session_number = len(_SESSION_HEADER_RE.findall(current)) + 1
        frontmatter = parse_battery_frontmatter(current)
        prefix = _FRONTMATTER_RE.match(current).group(0) if _FRONTMATTER_RE.match(current) else ""
        body = _FRONTMATTER_RE.sub("", current, count=1).rstrip()
        status = str(payload.get("status") or frontmatter.get("status") or "em_progresso")
    else:
        session_number = 1
        prefix = "\n".join(
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
        body = ""

    session_block = "\n".join(
        [
            f"## {payload['date']} {payload['time']} (sessao {session_number})",
            f"- Status: {status}",
            payload["body"].strip(),
            "",
        ]
    )
    target.write_text(prefix + (body + "\n\n" if body else "") + session_block, encoding="utf-8")
    return target
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: PASS for create and append battery tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_student_state_manual_import.py src/builder/artifacts/student_state.py
git commit -m "feat: persist manual student state batteries"
```

### Task 4: Patch STUDENT_STATE And Refresh Unit Progress

**Files:**
- Modify: `src/builder/artifacts/student_state.py`
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Write the failing tests**

```python
from src.builder.artifacts.student_state import apply_manual_import_to_student_state


def test_apply_manual_import_to_student_state_updates_active_and_recent(tmp_path):
    state_path = tmp_path / "student" / "STUDENT_STATE.md"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        "\n".join(
            [
                "---",
                "course: Calculo",
                "student: Humberto",
                "updated: 21-04-26",
                "",
                "active:",
                "  unit: unidade-00-anterior",
                "  topic: anterior",
                "  status: pendente",
                "  sessions: 1",
                "  file: student/batteries/unidade-00-anterior/anterior.md",
                "",
                "active_unit_progress:",
                "  - {topic: definicao-de-limite, status: pendente}",
                "",
                "recent:",
                "  - {topic: anterior, unit: unidade-00-anterior, date: 21-04-26}",
                "",
                "next_topic: continuidade",
                "",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = {
        "unit_slug": "unidade-01-limites",
        "topic_slug": "definicao-de-limite",
        "status": "em_progresso",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "continuidade",
    }

    apply_manual_import_to_student_state(
        tmp_path,
        payload=payload,
        battery_rel_path="student/batteries/unidade-01-limites/definicao-de-limite.md",
        course_map_topics=[("definicao-de-limite", "Definicao de limite"), ("continuidade", "Continuidade")],
    )

    text = state_path.read_text(encoding="utf-8")
    assert "unit: unidade-01-limites" in text
    assert "topic: definicao-de-limite" in text
    assert "file: student/batteries/unidade-01-limites/definicao-de-limite.md" in text
    assert "updated: 22-04-26" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: FAIL with missing `apply_manual_import_to_student_state`

- [ ] **Step 3: Write minimal implementation**

```python
def apply_manual_import_to_student_state(
    root_dir: Path,
    *,
    payload: dict,
    battery_rel_path: str,
    course_map_topics: list[tuple[str, str]],
) -> None:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    text = state_path.read_text(encoding="utf-8")
    sessions = len(_SESSION_HEADER_RE.findall((root_dir / battery_rel_path).read_text(encoding="utf-8")))
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
    text = re.sub(r"updated:\s*.+", f"updated: {payload['date']}", text, count=1)
    text = re.sub(r"active:\s*\n(?:  .*\n)+", active_block, text, count=1)
    recent_entry = f"  - {{topic: {payload['topic_slug']}, unit: {payload['unit_slug']}, date: {payload['date']}}}\n"
    if "recent:\n" in text:
        text = text.replace("recent:\n", "recent:\n" + recent_entry, 1)
    else:
        text = text.replace("\n---\n", "\nrecent:\n" + recent_entry + "\n---\n", 1)
    if payload.get("next_topic"):
        text = re.sub(r"next_topic:\s*.*", f"next_topic: {payload['next_topic']}", text, count=1)
    state_path.write_text(text, encoding="utf-8")
    refresh_active_unit_progress(
        root_dir=root_dir,
        active_unit_slug=payload["unit_slug"],
        course_map_topics=course_map_topics,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: PASS for state patching test

- [ ] **Step 5: Commit**

```bash
git add tests/test_student_state_manual_import.py src/builder/artifacts/student_state.py
git commit -m "feat: patch student state after manual import"
```

### Task 5: Add Student State Import Window To The Tkinter App

**Files:**
- Create: `src/ui/student_state_curator.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Write the failing tests**

```python
from src.builder.artifacts.student_state import validate_manual_import_selection


def test_validate_manual_import_selection_rejects_unknown_topic():
    course_index = [
        {
            "unit_slug": "unidade-01-limites",
            "unit_title": "Unidade 1 - Limites",
            "topics": [{"topic_slug": "definicao-de-limite", "topic_title": "Definicao de limite"}],
        }
    ]

    errors = validate_manual_import_selection(
        unit_slug="unidade-01-limites",
        topic_slug="continuidade",
        course_index=course_index,
    )

    assert errors == ["topic_slug"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: FAIL with missing validator helper

- [ ] **Step 3: Write minimal implementation**

```python
def validate_manual_import_selection(*, unit_slug: str, topic_slug: str, course_index: list[dict]) -> list[str]:
    unit = next((item for item in course_index if item["unit_slug"] == unit_slug), None)
    if not unit:
        return ["unit_slug"]
    if not any(topic["topic_slug"] == topic_slug for topic in unit.get("topics", [])):
        return ["topic_slug"]
    return []
```

```python
# src/ui/student_state_curator.py
class StudentStateCurator(tk.Toplevel):
    ...
```

```python
# src/ui/app.py
ttk.Button(build_actions, text="🧠 Student State", command=self.open_student_state_curator).grid(...)

def open_student_state_curator(self):
    from src.ui.student_state_curator import StudentStateCurator
    repo_dir = self._repo_dir_from_active_subject()
    subject = self._active_subject()
    StudentStateCurator(self, repo_dir=str(repo_dir), subject_profile=subject, theme_mgr=self.theme_mgr)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_student_state_manual_import.py -q`
Expected: PASS for validator helper and no regressions in test file

- [ ] **Step 5: Commit**

```bash
git add tests/test_student_state_manual_import.py src/ui/student_state_curator.py src/ui/app.py src/builder/artifacts/student_state.py
git commit -m "feat: add student state import window"
```

### Task 6: Verify End-To-End And Update Scaffolding

**Files:**
- Modify: `.mex/ROUTER.md`
- Modify: `.mex/patterns/INDEX.md` only if a new reusable pattern is discovered
- Test: `tests/test_student_state_manual_import.py`

- [ ] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_student_state_manual_import.py -q
```

Expected: PASS

- [ ] **Step 2: Run existing student-state regression tests**

```bash
python -m pytest tests/test_student_state_v2.py tests/test_student_state_integration.py tests/test_consolidate_unit.py -q
```

Expected: PASS

- [ ] **Step 3: Manual verification checklist**

```text
1. Open the app.
2. Confirm the toolbar shows "Student State" where "FILE_MAP" used to be.
3. Open a repo with valid `student/STUDENT_STATE.md`.
4. Paste tutor markdown with valid unit/topic and import it.
5. Save and confirm:
   - battery file created or appended
   - `student/STUDENT_STATE.md` patched
   - no task queue job created
6. Repeat with invalid topic and confirm dropdown correction is required before save.
```

- [ ] **Step 4: Update project state**

```md
Add a bullet under `.mex/ROUTER.md` -> "Current Project State / Working" describing the Student State manual import window and direct battery update flow.
```

- [ ] **Step 5: Commit**

```bash
git add .mex/ROUTER.md tests/test_student_state_manual_import.py src/ui/student_state_curator.py src/ui/app.py src/builder/artifacts/student_state.py
git commit -m "feat: wire student state manual import flow"
```
