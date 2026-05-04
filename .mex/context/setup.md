---
name: setup
description: How to set up, run, and test GPT-Tutor-Generator
triggers:
  - setup
  - install
  - run
  - environment
  - test
  - pytest
edges:
  - target: context/stack.md
    condition: when exact technology or manifest details are needed
  - target: context/architecture.md
    condition: when understanding runtime behavior after startup
last_updated: 2026-05-04
---

# Setup

## Requirements From Brief

| Requirement | Source |
|---|---|
| Python `3.8+` | README badge and requirements section reference. |
| Tkinter | README identifies the UI as Tkinter. |
| Ollama | README identifies Vision support through Ollama. |
| Datalab | README identifies the PDF backend as Datalab. |
| pytest | Brief tooling identifies `pytest` as the test runner. |

The brief does not declare package dependencies, development dependencies, scripts, a formatter, a linter, or a package manager.

## Install

Use a Python virtual environment. Exact dependency installation command is not declared in the brief, because `pyproject.toml` dependencies and dev dependencies are listed as empty.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If a task needs an exact install command, read `pyproject.toml` before documenting or running one.

## Run

The application main entry point is:

```powershell
python app.py
```

## Test

The test runner is `pytest`.

```powershell
python -m pytest tests -q
```

Known test entry points from the brief include:

```powershell
python -m pytest tests/test_unit_fallback.py -q
python -m pytest tests/test_ui_queue_dashboard.py -q
python -m pytest tests/test_timeline_signals.py -q
python -m pytest tests/test_timeline_scoring_ignored.py -q
python -m pytest tests/test_timeline_index_kind.py -q
python -m pytest tests/test_task_queue.py -q
python -m pytest tests/test_tag_catalog.py -q
python -m pytest tests/test_student_state_v2.py -q
python -m pytest tests/test_student_state_manual_import.py -q
```

## Operational Flow

After launching the app:

1. Create or select a subject.
2. Define the generated repository folder.
3. Import files and links.
4. Process the queue.
5. Review outputs in `manual-review/` when needed.
6. Use Image Curator for extracted images or photos.
7. Build or update the final repository.
8. Use Reprocess Repository to reapply the current architecture to existing repositories.
9. Use Repository Tasks to queue builds, reprocessing, and individual processing.
10. Use Dashboard to monitor operational repository state.
