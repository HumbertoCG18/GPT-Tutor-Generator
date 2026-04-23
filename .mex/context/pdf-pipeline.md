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
last_updated: 2026-04-22
---

# PDF Pipeline

## Pipeline Stages

Each PDF entry flows through 6 stages in `src/builder/pdf/pdf_pipeline.py`:

1. **Profile** — `builder._profile_pdf(raw_target, entry)` produces a `PDFDocumentReport` with `page_count`, `text_chars`, `image_count`, and scan detection
2. **Decide** — `builder.selector.decide(entry, report)` returns a `PipelineDecision` with `effective_profile` and chosen backends
3. **Base conversion** — fast, local backend (pymupdf4llm, pdfplumber, pymupdf) produces base markdown
4. **Advanced conversion** — optional high-quality backend (Marker, Docling, Datalab) runs if the profile warrants it
5. **Hybrid merge** — if Marker was used, `hybridize_marker_markdown_with_base_fn` merges results
6. **Image/table extraction** — if `extract_images=True` or `extract_tables=True`, images are saved; Datalab path lands in `BackendRunResult.images_dir`

## Backend Selection Rules

| Profile | `formula_priority` | Primary advanced backend |
|---------|--------------------|--------------------------|
| `math_heavy` | any | Datalab (`accurate` mode) |
| any | `True` | Datalab |
| `scanned` | False | Marker (with OCR) |
| `standard` | False | docling_python or Marker |
| `simple` | False | pymupdf4llm only (no advanced) |

Backend availability is detected at runtime:
- `has_datalab_api_key()` — checks `DATALAB_API_KEY` env var
- `has_docling_python_api_fn()` — tries importing the API
- `detect_marker_capabilities()` — checks CLI and Python API availability; result cached in `_MARKER_CAPABILITIES_CACHE`

## Page Chunking

Datalab and Marker both support chunked processing for large PDFs:
- `datalab_should_chunk(ctx)` → True if page count exceeds threshold
- `datalab_chunk_size_for_workload(ctx)` → chunk size (default 20 pages)
- `build_page_chunks(pages, page_count, chunk_size)` → list of page lists
- For docling_python with a page range: `prepare_docling_python_source_pdf` slices the PDF via PyMuPDF first

## Known Failure Modes

- **LaTeX corruption (silent):** `pymupdf4llm` can corrupt inline math without any error. Always use Datalab or Marker for `math_heavy` documents.
- **Marker stall detection:** Only `"LLM processors running"` phase has a per-phase timeout override; other phases use the general calculated timeout. Long Marker runs may stall without triggering the right timeout.
- **Marker Ollama patch:** `.venv/.../marker/services/ollama.py` has a manual patch. Recreating `.venv` loses it. The `qwen3-vl:235b-cloud` model causes 500 errors — use `qwen3-vl:8b q4_K_M`.
- **Datalab polling:** `convert_document_to_markdown` polls in a loop up to `max_wait_seconds=1800`. If Datalab returns a job that never completes, the build thread hangs. Check `DatalabConvertResult.parse_quality_score` post-conversion.
- **`images_dir` is None:** Means either `extract_images=False`, the backend doesn't support image extraction, or the entry was not processed by Datalab. Image curation UI reads from manifest `images_dir` field.

## Adding a New Backend

See `patterns/pdf-backend-integration.md` for the step-by-step pattern.
