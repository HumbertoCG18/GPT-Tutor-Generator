---
name: architecture
description: System components, data flow, and integrations for GPT-Tutor-Generator
triggers:
  - architecture
  - system design
  - data flow
  - integration
  - module structure
edges:
  - target: context/stack.md
    condition: when technology, version, or tooling details are needed
  - target: context/decisions.md
    condition: when understanding why an architectural choice exists
  - target: context/repo-output.md
    condition: when the task involves the generated repository format
last_updated: 2026-06-17
---

# Architecture

## Product Shape

GPT-Tutor-Generator is a local Python desktop application that transforms academic materials into a structured Markdown repository for LLM-based tutoring.

The project manifest is `pyproject.toml`:

| Field | Value |
|---|---|
| Package name | `academic-tutor-repo-builder` |
| Version | `3.0.0` |
| Main entry point | `app.py` |
| Test runner | `pytest` (`tests/`, 111 tracked files) |

## High-Level Flow

The application workflow from the brief is:

```text
Import academic materials
  -> classify and configure entries
  -> process PDFs, links, code, and images
  -> send difficult outputs to manual review
  -> curate images and extract descriptions
  -> map files to schedule blocks and course units
  -> enrich code/references when optional Gemini is configured
  -> consolidate content into Markdown
  -> generate instruction files and pedagogical repository structure
```

Typical UI flow:

```text
Create or select subject
  -> define generated repository folder
  -> import files and links
  -> process queue
  -> review generated manual review outputs when needed
  -> use Curadoria for manual review and extracted images or photos
  -> use Cronograma to inspect and override file-to-block allocation
  -> build or update final repository
  -> optionally reprocess existing repository
  -> monitor repository tasks in dashboard
```

## Components

| Component | Responsibility |
|---|---|
| `app.py` | Application entry point. |
| Desktop UI | Tkinter interface for subject setup, imports, queue processing, image curation, repository tasks, and dashboard monitoring. |
| Import pipeline | Accepts academic files and links, including PDFs, images, code, and URLs. |
| Processing queue | Persistent queue for builds, reprocessing, and individual material processing across app sessions. |
| Curadoria workspace | Unified Tkinter curation window with `Revisão Manual` first and lazy-loaded `Imagens`. |
| Manual review area | Holds problematic generated outputs for user correction. |
| Image Curator panel | Curates images extracted from PDFs or imported photos and extracts descriptions inside the unified curation workspace. |
| Timeline Dashboard | Shows file-to-block allocation, unmapped entries, confidence badges, and manual timeline overrides. |
| PUCRS schedule import | Parses ASP.NET `dgAulas` schedule HTML, including authoritative row kinds for suspensions, exams, holidays, and events. |
| Repository builder | Consolidates processed content into structured Markdown and tutor instruction artifacts. |
| Reprocess Repository action | Reapplies the current architecture to previously generated repositories. |
| Dashboard | Shows operational state for generated repositories and queued repository tasks. |
| Code Summarization (Gemini) | Lazy `google-genai` client + concept-based timeline block matcher. Backbone in `src/builder/core/code_summarization.py` and `src/builder/runtime/gemini_client.py`. |
| Reference context pipeline | Lightweight reference fetch, optional Gemini summary, deterministic unit/topic mapping, BIBLIOGRAPHY output, and COURSE_MAP support lines. |
| Timeline/unit matcher | Positional timeline block-to-unit assignment in `src/builder/timeline/unit_matcher.py`; manual overrides remain authoritative and conflicts are surfaced. |
| Tag and taxonomy pipeline | Generates internal content-taxonomy, tag-catalog, assessment-context, and manifest `auto_tags` data for unit/subunit/block routing. |

## Data Model Context

The generated tutor repository is built with context for:

| Context | Purpose |
|---|---|
| Subject | Identifies the course or discipline. |
| Professor | Preserves teaching context. |
| Semester | Anchors materials to the academic period. |
| Schedule | Supports timeline-aware organization. |
| Student profile | Supports personalized tutor behavior. |
| Processing progress | Tracks build and material processing state. |

## Integrations

| Integration | Role |
|---|---|
| Ollama Vision | Vision support for image understanding and curation. |
| Datalab PDF backend | PDF processing backend referenced by the README. |
| Claude | Generated instruction target for Claude Projects knowledge bases. |
| GPT | Generated instruction target. |
| Gemini | Generated instruction target. |
| Google Gemini (`gemini-2.5-flash`) | Optional. Generates structured JSON summaries of code bundles consumed by CODE_INDEX, header MD, CRONOGRAMA_DETALHADO, and CODE_HEALTH. |
| Google Gemini for references | Optional. Generates prose reference summaries; deterministic reference mapping still runs without a key. |

Exact external service versions for Datalab, Ollama, and Gemini models are not pinned by the manifest. Do not assert those details without reading source, config, or official docs.

## Tracked Repository Layout

| Path | Category | File count |
|---|---:|---:|
| `src` | application source | 105 |
| `tests` | tests | 111 |
| `docs` | documentation | 97 |
| `scripts` | eval/diff harnesses and dev scripts | 19 |
| `plans` | planning notes | 6 |
| `.github` | GitHub metadata | 2 |
| `schemas` | data/model schemas | 1 |

## Entry Points

| Path | Type |
|---|---|
| `app.py` | main |
| `tests/__init__.py` | test package |
| `tests/test_datalab_image_extraction.py` | test |
| `tests/test_cronograma_health.py` | test |
| `tests/test_reference_summary.py` | test |
| `tests/test_reference_navigation.py` | test |
| `tests/test_unit_matcher.py` | test |
| `tests/test_eval_ground_truth.py` | test |
| `tests/test_unit_fallback.py` | test |
| `tests/test_ui_queue_dashboard.py` | test |
| `tests/test_timeline_signals.py` | test |
| `tests/test_timeline_scoring_ignored.py` | test |
| `tests/test_timeline_index_kind.py` | test |
| `tests/test_task_queue.py` | test |
| `tests/test_tag_catalog.py` | test |
| `tests/test_student_state_v2.py` | test |
| `tests/test_student_state_manual_import.py` | test |
