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
last_updated: 2026-06-18
---

# Conventions

## Source Organization

Tracked repository layout:

| Path | Role |
|---|---|
| `app.py` | Main application entry point. |
| `src/` | Application source, 108 tracked files. |
| `tests/` | Test suite, 122 files. |
| `docs/` | Project documentation, 125 files. |
| `scripts/` | Eval/diff harnesses and dev scripts, 28 files. |
| `plans/` | Planning notes, 6 files. |
| `.github/` | GitHub metadata, 2 files. |
| `schemas/` | Data/model schemas, 1 file. |

## Naming

Observed from the brief:

| Kind | Pattern |
|---|---|
| Tests | `tests/test_<topic>.py` |
| Unit fallback tests | `tests/test_unit_fallback.py` |
| Timeline tests | Examples include `tests/test_timeline_signals.py`, `tests/test_timeline_index_kind.py`, and `tests/test_timeline_scoring_ignored.py` |
| Student state tests | Examples include `tests/test_student_state_v2.py`, `tests/test_student_state_manual_import.py`, and `tests/test_student_state_integration.py` |
| Tag catalog tests | `tests/test_tag_catalog.py` |
| Moodle/SARC signal tests | Examples include `tests/test_moodle.py`, `tests/test_moodle_labels.py`, `tests/test_migrate_signals.py`, and `tests/test_posting_date_probe.py` |
| Concept resolver tests | Examples include `tests/test_concept_resolver.py`, `tests/test_resolver_fusion.py`, and `tests/test_resolver_wiring.py` |

Use existing topic names when adding tests. Do not introduce a new naming scheme without a specific reason.

## Behavioral Patterns

The README flow establishes these project patterns:

- Imports are configured as entries before processing.
- Processing is queue-based.
- Difficult outputs are routed through the generated repository's manual review area.
- Image processing is handled in the `Imagens` tab of the unified Curadoria workspace.
- Repository builds and reprocesses are available as repository tasks.
- Dashboard state reflects repository task progress.
- Cronograma state exposes file-to-block allocation and manual timeline overrides.
- Reference/bibliography entries can become tutor context through BIBLIOGRAPHY and COURSE_MAP support lines.
- Timeline/unit/tag metadata is regenerated into manifest `auto_tags` and internal course dotfiles.
- Moodle/SARC-derived signals remain separate metadata fields (`source_section`, `moodle_label`, `posting_date`, `turma`, `schedule_url`) and should not overwrite display titles.
- The concept resolver is feature-flagged; default routing behavior should not change unless the flag/cutover work is explicit.
- Generated output is Markdown plus LLM instruction artifacts.

## Documentation Discipline

- Use manifest data exactly: `pyproject.toml`, project name `academic-tutor-repo-builder`, version `3.0.0`, and the declared dependencies/extras.
- If scripts, linter, formatter, build-system table, or package metadata are not declared, document them as not declared instead of guessing.
- Prefer precise paths from the brief.
- Do not assert source module internals unless they were read for the task.

## Verify Checklist

Run this checklist after code or scaffold changes:

- [ ] Manifest facts match the brief or the actual manifest that was read.
- [ ] No undeclared dependency, script, linter, formatter, build backend, or package manager was invented.
- [ ] Entry points and paths match repository spelling and separators.
- [ ] New tests follow the `tests/test_<topic>.py` convention.
- [ ] Generated-repository behavior remains compatible with the README flow.
- [ ] If changing tag behavior, update or add coverage near `tests/test_tag_catalog.py` and relevant unit/timeline scoring tests.
- [ ] If changing timeline allocation behavior, update or add coverage near `tests/test_unit_matcher.py`, `tests/test_cronograma_health.py`, and relevant timeline scoring tests.
- [ ] If changing Moodle/SARC signal capture or consumed attribution signals, update or add coverage near `tests/test_moodle.py`, `tests/test_moodle_labels.py`, and `tests/test_migrate_signals.py`.
- [ ] If changing concept-resolver behavior, update or add coverage near `tests/test_concept_resolver.py`, `tests/test_resolver_fusion.py`, and `tests/test_resolver_wiring.py`.
