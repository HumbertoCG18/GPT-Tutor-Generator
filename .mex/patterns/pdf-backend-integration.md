---
name: pdf-backend-integration
description: Adding or modifying a PDF conversion backend. High-risk area with non-obvious gotchas around backend detection, chunking, stall timeouts, and LaTeX corruption.
triggers:
  - "new backend"
  - "pdf backend"
  - "marker"
  - "docling"
  - "datalab"
  - "conversion backend"
  - "add backend"
edges:
  - target: context/pdf-pipeline.md
    condition: always — load first to understand the full pipeline stages
  - target: context/decisions.md
    condition: when understanding why existing backend choices were made
  - target: context/stack.md
    condition: when checking library/CLI availability detection
  - target: patterns/debug-build-failure.md
    condition: when backend changes cause build failures or unexpected conversion errors
last_updated: 2026-06-21
---

# PDF Backend Integration

Reviewed against the current PDF pipeline, selector, and backend runtime modules on 2026-06-21.

## Context

Load `context/pdf-pipeline.md` before starting. Understand the 6 pipeline stages and backend selection matrix.

Key files:
- `src/builder/pdf/pdf_pipeline.py` — calls backends, merges results, manages image extraction
- `src/builder/engine.py` — `BackendSelector`, backend classes, and profile fallback order
- `src/builder/runtime/backend_runtime.py` — backend capability detection, chunking helpers, stall timeouts
- `src/builder/pdf/pdf_analysis.py` — PDF profiling helpers
- `src/models/core.py` — `DocumentProfileReport`, `PipelineDecision`, and `BackendRunResult` dataclasses
- `src/builder/runtime/datalab_client.py` — Datalab HTTP client

## Task: Add a New Backend

### Steps

1. Add capability detection function to `backend_runtime.py` (e.g. `detect_mynewbackend_capabilities()` → returns a dict or bool)
2. Cache the detection result in a module-level `_MYNEWBACKEND_CACHE = None` variable — detection can be expensive
3. Add chunking helpers if the backend supports page ranges: follow `build_page_chunks` / `datalab_chunk_size_for_workload` pattern
4. Add a stall timeout helper if the backend can run for minutes: follow `advanced_cli_stall_timeout` pattern
5. Add conversion logic in `src/builder/pdf/` (new file or extend `pdf_pipeline.py`)
6. Wire the backend into `BackendSelector` in `src/builder/engine.py` by registering the backend class and updating `pick_advanced_for_profile()` or profile-backend configuration behavior
7. Add the backend name to the manifest `environment` dict in `build_workflow.py`
8. Test with a small math-heavy PDF and check `parse_quality_score` or equivalent quality signal

### Gotchas

- Backend capability detection is called on every build — cache aggressively to avoid slow startup
- If the backend invokes a subprocess: use `subprocess.run` with a calculated timeout; never let it run indefinitely
- If the backend can produce broken LaTeX silently: add a `detect_latex_corruption_fn` check after conversion (see Marker/Datalab path in `pdf_pipeline.py`)
- `images_dir` must be set on `BackendRunResult` if the backend extracts images — otherwise image curation UI shows nothing
- If the backend provides image captions, coordinate with `image_description_source`; Datalab captions are intentionally disabled when the app is in Ollama-description mode
- Page range support: if the backend doesn't natively support page ranges, pre-slice the PDF using `prepare_docling_python_source_pdf` (PyMuPDF-based) and pass the sliced file

### Verify

- [ ] Capability detection is cached at module level
- [ ] Stall timeout is implemented for long-running operations
- [ ] `images_dir` is populated when images are extracted
- [ ] `BackendRunResult.name` and `layer` are set correctly for manifest logging
- [ ] New backend name appears in manifest `environment` dict
- [ ] Tested with at least one math-heavy and one simple PDF

## Task: Modify Existing Backend Behavior

### Steps

1. Load `context/pdf-pipeline.md` — understand which stage the change affects
2. Find the relevant capability function in `backend_runtime.py` and check if caching needs to be invalidated
3. Edit only the targeted helper — do not touch `pdf_pipeline.py` main flow unless adding a new stage
4. If modifying Marker behavior: check Marker/Ollama configuration in `src/builder/runtime/backend_runtime.py` and keep it aligned with `context/pdf-pipeline.md`.
5. If modifying selector behavior: update `BackendSelector.decide()` in `src/builder/engine.py` and the Backend Selection Rules table in `context/pdf-pipeline.md`.

### Gotchas

- `_MARKER_CAPABILITIES_CACHE` persists for the app's lifetime — if you change detection logic, test with a fresh process
- Modifying `datalab_chunk_size_for_workload` affects cost — Datalab charges per page
- `marker_should_redo_inline_math` controls a separate math post-processing pass — changing it affects quality for math-heavy docs

### Verify

- [ ] Capability cache invalidated if detection logic changed
- [ ] No change to PDF pipeline stages unless explicitly required
- [ ] Tested end-to-end with a real PDF in the affected profile category

## Update Scaffold
- [ ] Update `context/pdf-pipeline.md` Backend Selection Rules table if a new backend or profile was added
- [ ] Update `context/decisions.md` if this represents a significant architectural choice
- [ ] Update `.mex/ROUTER.md` "Current Project State"
