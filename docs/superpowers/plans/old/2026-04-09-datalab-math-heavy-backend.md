# Datalab Math-Heavy Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new cloud backend for `math_heavy` PDFs using the Datalab conversion API while preserving the existing tutor repo pipeline.

**Architecture:** Implement a dedicated Datalab client module for API submission/polling, then integrate it as an advanced backend in the existing selector. Keep tags, units, manifest generation, and downstream tutor-repo features unchanged by feeding the returned markdown into the current staging and build flow.

**Tech Stack:** Python, `requests`, existing `RepoBuilder` backend architecture, `.env` configuration.

---

### Task 1: Environment and API client
- [x] Add lightweight `.env` loading in `src/utils/helpers.py`.
- [x] Add `src/builder/datalab_client.py` with API key lookup, submit/poll flow, and image decoding helpers.

### Task 2: Backend integration
- [x] Add `DatalabCloudBackend` to `src/builder/engine.py`.
- [x] Save markdown and extracted images into `staging/markdown-auto/datalab/<entry>/`.
- [x] Persist Datalab metadata in `datalab-run.json`.

### Task 3: Backend selection and UI
- [x] Add `datalab` to `PREFERRED_BACKENDS` in `src/utils/helpers.py`.
- [x] Make `math_heavy` auto-selection prefer `datalab` when available.
- [x] Surface Datalab availability in status/diagnostics UI.

### Task 4: Tests
- [x] Add backend execution test for markdown/image persistence.
- [x] Add selector tests for `math_heavy` preference and manual override.
