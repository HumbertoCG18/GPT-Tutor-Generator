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
last_updated: 2026-05-12
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
| Test runner | `pytest` |

## High-Level Flow

The application workflow from the brief is:

```text
Import academic materials
  -> classify and configure entries
  -> process PDFs, links, code, and images
  -> send difficult outputs to manual review
  -> curate images and extract descriptions
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
  -> use Image Curator for extracted images or photos
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
| Manual review area | Holds problematic generated outputs for user correction. |
| Image Curator | Curates images extracted from PDFs or imported photos and extracts descriptions. |
| Repository builder | Consolidates processed content into structured Markdown and tutor instruction artifacts. |
| Reprocess Repository action | Reapplies the current architecture to previously generated repositories. |
| Dashboard | Shows operational state for generated repositories and queued repository tasks. |

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

The brief does not declare network APIs, cloud LLM calls during build, or exact backend client modules. Do not assert those details without reading source or official docs.

## Repository Layout From Brief

| Path | Category | File count |
|---|---:|---:|
| `src` | application source | 71 |
| `tests` | tests | 28 |
| `docs` | documentation | 3 |
| `.github` | GitHub metadata | 1 |

## Entry Points

| Path | Type |
|---|---|
| `app.py` | main |
| `tests/__init__.py` | test package |
| `tests/test_unit_fallback.py` | test |
| `tests/test_ui_queue_dashboard.py` | test |
| `tests/test_timeline_signals.py` | test |
| `tests/test_timeline_scoring_ignored.py` | test |
| `tests/test_timeline_index_kind.py` | test |
| `tests/test_task_queue.py` | test |
| `tests/test_tag_catalog.py` | test |
| `tests/test_student_state_v2.py` | test |
| `tests/test_student_state_manual_import.py` | test |
