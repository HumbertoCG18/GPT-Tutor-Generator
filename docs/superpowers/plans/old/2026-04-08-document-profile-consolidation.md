# Document Profile Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the document profile model to `auto`, `math_heavy`, `diagram_heavy`, and `scanned` while preserving compatibility with existing manifests, saved queue entries, and runtime heuristics.

**Architecture:** Introduce a single normalization layer for document profiles and route every entry point through it: UI form options, model deserialization, PDF profiling heuristics, backend selection, and bundle metadata. Legacy profile names remain readable as aliases, but new data and UI choices use only the four canonical profiles.

**Tech Stack:** Python, Tkinter UI, Pytest

---

### Task 1: Add canonical profile normalization

**Files:**
- Modify: `src/utils/helpers.py`
- Modify: `src/models/core.py`
- Test: `tests/test_core.py`

- [ ] Define the four canonical UI profiles and legacy aliases in `src/utils/helpers.py`.
- [ ] Add a normalization helper that maps `general` and unknown/empty values to `auto`, `math_light` to `math_heavy`, and `layout_heavy` / `exam_pdf` to `diagram_heavy`.
- [ ] Normalize `FileEntry.document_profile` during `FileEntry.from_dict()` so persisted queue items and older subject snapshots load cleanly.
- [ ] Add tests covering alias normalization for `general`, `math_light`, `layout_heavy`, `exam_pdf`, and empty values.

### Task 2: Rewire profiling and backend policy

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] Update automatic PDF profiling so the runtime now emits only `math_heavy`, `diagram_heavy`, `scanned`, or `auto`.
- [ ] Update backend selection logic to treat `diagram_heavy` as the visual/layout-heavy branch and stop branching on `math_light`, `layout_heavy`, `exam_pdf`, and `general`.
- [ ] Update docling/marker enrichment, chunk sizing, OCR policy, stall timeout policy, image extraction policy, and bundle prioritization to consume normalized profiles.
- [ ] Add tests for `diagram_heavy` backend choice, `auto` without advanced backend, and normalized image extraction / bundle-reason behavior.

### Task 3: Simplify the UI and help text

**Files:**
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_ui_queue_dashboard.py`
- Test: `tests/test_core.py`

- [ ] Replace the visible profile list in the item form with only `auto`, `math_heavy`, `diagram_heavy`, and `scanned`.
- [ ] Update the profile tooltip/help copy to describe the new semantics in Portuguese.
- [ ] Update `_on_profile_changed()` presets so `diagram_heavy` behaves like the visual-heavy path and `auto` becomes the neutral default.
- [ ] Update any default seeded `document_profile="general"` values to `document_profile="auto"`.
- [ ] Add/update tests that read UI/help source text or default values so they assert only the new canonical profile names.

### Task 4: Preserve compatibility in outputs and cleanup regressions

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `src/ui/curator_studio.py` only if any visible profile labels are surfaced there
- Test: `tests/test_core.py`
- Test: `tests/test_repo_dashboard.py`
- Test: `tests/test_image_curation.py`

- [ ] Ensure generated markdown/frontmatter and manifest-derived paths continue working when older entries still carry legacy profile strings.
- [ ] Normalize profile labels before scoring bundle priority/reasons and before any UI display that depends on `effective_profile`.
- [ ] Run focused regressions on backend selection, profiling, image extraction policy, dashboard/backlog consumption, and image curation support for scanned PDFs.

### Task 5: Save, verify, and close

**Files:**
- Modify: `docs/superpowers/plans/2026-04-08-document-profile-consolidation.md`

- [ ] Run targeted tests for the changed subsystems.
- [ ] Run one wider regression pass that covers the profile-sensitive paths touched in this plan.
- [ ] Mark the plan as executed in practice through the final summary, even if the markdown checklist remains unchecked.
