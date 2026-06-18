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
last_updated: 2026-06-18
---

# Stack

## Manifest

The authoritative manifest in the brief is `pyproject.toml`.

| Field | Value |
|---|---|
| Project name | `academic-tutor-repo-builder` |
| Version | `3.0.0` |
| Dependencies | `beautifulsoup4>=4.12.0`, `pillow>=10.0.0`, `requests>=2.31.0`, `pymupdf>=1.24.0`, `pymupdf4llm>=0.0.10`, `pdfplumber>=0.10.0`, `jsonschema>=4.0.0` |
| Dev dependencies | `pytest>=7.0` |
| Optional extras | `code-summarization`: `google-genai>=0.3.0` |
| Scripts | none declared in brief |

Do not invent dependency names, package versions, extras, or scripts. If a task needs exact dependency metadata, read `pyproject.toml` before asserting it.

## Runtime Technologies

| Technology | Version / Source |
|---|---|
| Python | `pyproject.toml` requires `>=3.8`; README recommends Python `3.11`. |
| Tkinter | README identifies Tkinter as the desktop UI framework. |
| Markdown | Generated repository output format. |
| Ollama | README identifies Ollama as the Vision backend. Exact model/version not declared in the brief. |
| Datalab | README identifies Datalab as the PDF backend. Exact package/API version not declared in the brief. |
| `beautifulsoup4` | HTML parsing for URL/reference content. |
| `requests` | HTTP/cloud integration helper. |
| `pymupdf`, `pymupdf4llm`, `pdfplumber` | Local PDF processing backends. |
| `Pillow` | UI image handling. |
| `jsonschema` | Schema validation. |
| `google-genai` | Optional extra for code/reference summarization. SDK used: `from google import genai` (NOT `google.generativeai`). |

## Tooling

| Tool | Status |
|---|---|
| Test runner | `pytest` |
| Build tool | no `[build-system]` table declared; README install uses `pip install -e .[dev]` after upgrading `setuptools`/`wheel` |
| Linter | not declared in brief |
| Formatter | not declared in brief |
| Package manager | `pip` commands documented in README |

## Known Test Entry Points

The tracked test suite has 122 files. Representative entry points include:

```text
tests/__init__.py
tests/test_datalab_image_extraction.py
tests/test_cronograma_health.py
tests/test_reference_summary.py
tests/test_reference_navigation.py
tests/test_unit_matcher.py
tests/test_eval_ground_truth.py
tests/test_unit_fallback.py
tests/test_ui_queue_dashboard.py
tests/test_timeline_signals.py
tests/test_timeline_scoring_ignored.py
tests/test_timeline_index_kind.py
tests/test_task_queue.py
tests/test_tag_catalog.py
tests/test_student_state_v2.py
tests/test_student_state_manual_import.py
tests/test_moodle.py
tests/test_moodle_labels.py
tests/test_concept_resolver.py
tests/test_resolver_wiring.py
tests/test_migrate_signals.py
tests/test_posting_date_probe.py
```

## Integration Notes

- Vision support is implemented through Ollama, per README.
- PDF processing support includes Datalab, per README.
- Generated tutor instructions target Claude, GPT, and Gemini.
- Moodle/SARC import support now persists course signals such as `source_section`, `moodle_label`, `posting_date`, `turma`, and `schedule_url` for routing and audit tooling.
- The manifest now declares the core Python libraries listed above; exact external service versions for Datalab and Ollama are still not declared.
