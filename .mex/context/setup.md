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
last_updated: 2026-06-17
---

# Setup

## Requirements From Brief

| Requirement | Source |
|---|---|
| Python `>=3.8`; `3.11` recommended | `pyproject.toml` and README requirements section. |
| Tkinter | README identifies the UI as Tkinter. |
| Git | README requirements section. |
| Ollama | README identifies Vision support through Ollama. |
| Datalab | README identifies the PDF backend as Datalab. |
| pytest | Brief tooling identifies `pytest` as the test runner. |

The manifest declares runtime dependencies and the `dev`/`code-summarization` extras. It still does not declare project scripts, a formatter, or a linter.

## Install

Use a Python virtual environment and install the editable package with the development extra.

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]
```

For Gemini-backed code/reference summarization, install the optional extra:

```powershell
pip install -e .[code-summarization]
```

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

Representative targeted test entry points include:

```powershell
python -m pytest tests/test_datalab_image_extraction.py -q
python -m pytest tests/test_cronograma_health.py -q
python -m pytest tests/test_reference_summary.py -q
python -m pytest tests/test_reference_navigation.py -q
python -m pytest tests/test_unit_matcher.py -q
python -m pytest tests/test_eval_ground_truth.py -q
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
5. Review outputs in the generated repository's manual review area when needed.
6. Use Image Curator for extracted images or photos.
7. Build or update the final repository.
8. Use Reprocess Repository to reapply the current architecture to existing repositories.
9. Use Repository Tasks to queue builds, reprocessing, and individual processing.
10. Use Dashboard to monitor operational repository state.
11. Use Cronograma to inspect file-to-block allocation and persist manual block overrides.
