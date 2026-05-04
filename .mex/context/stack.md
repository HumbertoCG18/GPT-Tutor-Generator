---
name: stack
description: Technologies, versions, manifest data, and tooling
triggers:
  - backend
  - pdf backend
  - vision
  - ollama
  - datalab
  - stack
  - technology
  - manifest
edges:
  - target: context/architecture.md
    condition: when understanding how technologies fit into the system
  - target: context/setup.md
    condition: when setup or run commands are needed
last_updated: 2026-05-04
---

# Stack

## Manifest

The authoritative manifest in the brief is `pyproject.toml`.

| Field | Value |
|---|---|
| Project name | `academic-tutor-repo-builder` |
| Version | `3.0.0` |
| Dependencies | none declared in brief |
| Dev dependencies | none declared in brief |
| Scripts | none declared in brief |

Do not invent dependency names, package versions, extras, or scripts. If a task needs exact dependency metadata, read `pyproject.toml` before asserting it.

## Runtime Technologies

| Technology | Version / Source |
|---|---|
| Python | README states Python `3.8+`. |
| Tkinter | README identifies Tkinter as the desktop UI framework. |
| Markdown | Generated repository output format. |
| Ollama | README identifies Ollama as the Vision backend. Exact model/version not declared in the brief. |
| Datalab | README identifies Datalab as the PDF backend. Exact package/API version not declared in the brief. |

## Tooling

| Tool | Status |
|---|---|
| Test runner | `pytest` |
| Build tool | not declared in brief |
| Linter | not declared in brief |
| Formatter | not declared in brief |
| Package manager | not declared in brief |

## Known Test Entry Points

The brief lists these test files:

```text
tests/__init__.py
tests/test_unit_fallback.py
tests/test_ui_queue_dashboard.py
tests/test_timeline_signals.py
tests/test_timeline_scoring_ignored.py
tests/test_timeline_index_kind.py
tests/test_task_queue.py
tests/test_tag_catalog.py
tests/test_student_state_v2.py
tests/test_student_state_manual_import.py
```

## Integration Notes

- Vision support is implemented through Ollama, per README.
- PDF processing support includes Datalab, per README.
- Generated tutor instructions target Claude, GPT, and Gemini.
- The brief does not declare exact Python library dependencies for PDF parsing, HTTP clients, UI theming, or persistence.
