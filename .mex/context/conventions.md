---
name: conventions
description: Code patterns, naming, file organization, and verification rules
triggers:
  - convention
  - naming
  - code style
  - verify
  - review
  - file organization
edges:
  - target: context/architecture.md
    condition: when deciding where new logic should live
  - target: context/decisions.md
    condition: when a convention comes from an architectural decision
last_updated: 2026-05-04
---

# Conventions

## Source Organization

From the brief:

| Path | Role |
|---|---|
| `app.py` | Main application entry point. |
| `src/` | Application source, 71 files. |
| `tests/` | Test suite, 28 files. |
| `docs/` | Project documentation, 3 files. |
| `.github/` | GitHub metadata, 1 file. |

## Naming

Observed from the brief:

| Kind | Pattern |
|---|---|
| Tests | `tests/test_<topic>.py` |
| Unit fallback tests | `tests/test_unit_fallback.py` |
| Timeline tests | `tests/test_timeline_*.py` |
| Student state tests | `tests/test_student_state_*.py` |
| Tag catalog tests | `tests/test_tag_catalog.py` |

Use existing topic names when adding tests. Do not introduce a new naming scheme without a specific reason.

## Behavioral Patterns

The README flow establishes these project patterns:

- Imports are configured as entries before processing.
- Processing is queue-based.
- Difficult outputs are routed through `manual-review/`.
- Image processing has a dedicated Image Curator flow.
- Repository builds and reprocesses are available as repository tasks.
- Dashboard state reflects repository task progress.
- Generated output is Markdown plus LLM instruction artifacts.

## Documentation Discipline

- Use manifest data exactly: `pyproject.toml`, project name `academic-tutor-repo-builder`, version `3.0.0`.
- If dependencies, scripts, linter, formatter, or package manager are not declared, document them as not declared instead of guessing.
- Prefer precise paths from the brief.
- Do not assert source module internals unless they were read for the task.

## Verify Checklist

Run this checklist after code or scaffold changes:

- [ ] Manifest facts match the brief or the actual manifest that was read.
- [ ] No undeclared dependency, script, linter, formatter, or package manager was invented.
- [ ] Entry points and paths match repository spelling and separators.
- [ ] New tests follow the `tests/test_<topic>.py` convention.
- [ ] Generated-repository behavior remains compatible with the README flow.
- [ ] If changing tag behavior, update or add coverage near `tests/test_tag_catalog.py` and relevant unit/timeline scoring tests.
