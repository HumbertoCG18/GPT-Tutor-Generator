---
name: pdf-pipeline
description: How PDFs are profiled, backend-selected, and converted. Load when working on PDF processing, adding/modifying backends, or diagnosing conversion failures.
triggers:
  - "pdf"
  - "backend"
  - "marker"
  - "docling"
  - "datalab"
  - "pymupdf"
  - "conversion"
  - "math_heavy"
  - "document_profile"
  - "formula"
  - "OCR"
  - "scan"
edges:
  - target: context/architecture.md
    condition: when understanding how the PDF pipeline fits into the overall build flow
  - target: context/decisions.md
    condition: when understanding why a specific backend was chosen or rejected
  - target: context/stack.md
    condition: when checking library versions or installation requirements for backends
  - target: patterns/pdf-backend-integration.md
    condition: when adding or modifying a PDF backend
  - target: patterns/debug-build-failure.md
    condition: when a pipeline stage fails and you need to trace the error through manifest logs
last_updated: 2026-06-21
---

# PDF Pipeline

Reviewed against the current PDF pipeline, selector, and backend runtime modules on 2026-06-21.

## Pipeline Stages

Each PDF entry flows through the PDF execution path in `src/builder/pdf/pdf_pipeline.py`; backend selection is still exposed through the `BackendSelector` facade in `src/builder/engine.py`:

1. **Profile** — `builder._profile_pdf(raw_target, entry)` produces a `PDFDocumentReport` with `page_count`, `text_chars`, `image_count`, and scan detection
2. **Decide** — `builder.selector.decide(entry, report)` returns a `PipelineDecision` with `effective_profile` and chosen backends
3. **Scanned branch** — `scanned` PDFs are rendered as page images and routed to manual PDF review instead of normal markdown conversion
4. **Base conversion** — fast local backend (`pymupdf4llm` then `pymupdf`) produces base markdown unless base backends are skipped
5. **Advanced conversion** — optional high-quality backend (`datalab`, `docling`, `docling_python`, `marker`) runs when the selector chooses it; Marker output can be hybridized with base markdown
6. **Extraction and review** — image extraction, table extraction/detection, LaTeX corruption check, and manual-review markdown are written

## Backend Selection Rules

Backend selection happens in `BackendSelector.decide()` in `src/builder/engine.py`.

| Condition | Selector behavior |
|---------|--------------------|
| `entry.preferred_backend` is a concrete available advanced backend | Use that backend plus base backend when available |
| `processing_mode == "quick"` | Use base backend only |
| `processing_mode == "auto"` and profile is `math_heavy`, `diagram_heavy`, or `scanned` | Use base backend plus profile advanced backend |
| `processing_mode == "auto"` and common document | Use base backend only |
| `processing_mode == "high_fidelity"` | Try an advanced backend even for common documents |
| `formula_priority=True` and no advanced backend selected yet | Activate a profile advanced backend |
| `skip_base_backends=True` | Avoid `pymupdf4llm`/`pymupdf` unless no advanced backend is available |

Built-in advanced fallback order:

| Profile | Advanced backend order |
|---------|------------------------|
| `math_heavy` | `datalab`, then `marker`, then `docling` |
| `diagram_heavy` | `docling`, then `marker` |
| `scanned` | `docling`, then `marker` |
| common/high-fidelity fallback | `docling`, then `marker` |

`docling_python` is available as an advanced backend and can be selected manually or through profile backend configuration, but it is not in the built-in fallback order.

Backend availability is detected at runtime:
- `has_datalab_api_key()` — checks `DATALAB_API_KEY` env var
- `has_docling_python_api_fn()` — tries importing the API
- `detect_marker_capabilities()` — checks CLI and Python API availability; result cached in `_MARKER_CAPABILITIES_CACHE`

## Page Chunking

Datalab and Marker both support chunked processing for large PDFs:
- `datalab_should_chunk(ctx)` → True when selected pages are at least 50 and exceed the workload chunk size
- `datalab_chunk_size_for_workload(ctx)` → chunk size (15-25 pages depending on profile and selected page count)
- `build_page_chunks(pages, page_count, chunk_size)` → list of page lists
- `marker_chunk_size_for_workload(ctx)` and `build_marker_page_chunks(...)` support Marker chunking; Marker chunks only when configured to do so or as a fallback after a stall
- For docling_python with a page range: `prepare_docling_python_source_pdf` slices the PDF via PyMuPDF first

## Known Failure Modes

- **LaTeX corruption (silent):** `pymupdf4llm` can corrupt inline math without any error. Always use Datalab or Marker for `math_heavy` documents.
- **Marker stall detection:** Only `"LLM processors running"` phase has a per-phase timeout override; other phases use the general calculated timeout. Long Marker runs may stall without triggering the right timeout.
- **Marker Ollama configuration:** Marker LLM behavior is controlled by builder options plus runtime helpers in `src/builder/runtime/backend_runtime.py`. Avoid depending on manual edits inside the local virtual environment. The `qwen3-vl:235b-cloud` model causes 500 errors; use `qwen3-vl:8b q4_K_M`.
- **Datalab polling:** `convert_document_to_markdown` polls in a loop up to `max_wait_seconds=1800`. If Datalab returns a job that never completes, the build thread hangs. Check `DatalabConvertResult.parse_quality_score` post-conversion.
- **`images_dir` is None:** Means either `extract_images=False`, no images were extracted, the backend doesn't support image extraction, or the entry was not processed by a path that populates `BackendRunResult.images_dir`. Image curation UI reads from manifest `images_dir` field.
- **Datalab captions hidden in Ollama mode:** When `image_description_source != "datalab"`, Datalab image captions are disabled and image descriptions remain app-side through the curator.

## Adding a New Backend

See `patterns/pdf-backend-integration.md` for the step-by-step pattern.
