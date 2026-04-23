---
name: debug-build-failure
description: Diagnosing failures during repository builds — the most common failure boundary in this project.
triggers:
  - "build failed"
  - "build error"
  - "processing failed"
  - "entry failed"
  - "manifest error"
  - "conversion error"
  - "stall"
  - "timeout"
edges:
  - target: context/pdf-pipeline.md
    condition: when the failure is in PDF conversion or backend selection
  - target: context/architecture.md
    condition: when tracing the failure through the build flow
  - target: patterns/pdf-backend-integration.md
    condition: when the failure is in a specific PDF backend
  - target: patterns/ollama-vision.md
    condition: when the build failure occurs during image classification or vision processing
last_updated: 2026-04-22
---

# Debug Build Failure

## Context

Builds run in a background thread via `TaskQueueRunner`. Failures are recorded in two places:
1. `manifest.json` → `failed_entries` array (each entry has `error_type` and `error_message`)
2. `manifest.json` → `logs` array (step-by-step log for each entry)
3. Python `logging` output (visible in terminal or log file)

## Steps

1. **Check manifest first** — open `<repo_root>/manifest.json` and read `failed_entries`; note `error_type` (`missing_source`, `conversion_error`, etc.)
2. **Check logs array** — find entries with `status: "error"` for the failing entry; `step` field tells you which stage failed
3. **Check Python log output** — if the app was run from terminal, look for `ERROR` lines from `src.builder.*` loggers
4. **Identify the stage** from `context/pdf-pipeline.md` stages 1-6 — the `step` field in logs maps to stage names
5. **Check backend availability** — run in Python console: `from src.builder.runtime.backend_runtime import detect_marker_capabilities; print(detect_marker_capabilities())`
6. **Check API key** — for Datalab failures: `from src.builder.runtime.datalab_client import has_datalab_api_key; print(has_datalab_api_key())`
7. **Reproduce in isolation** — create a minimal test that calls the specific backend function directly on the failing PDF

## Failure Types and First Actions

| `error_type` | First action |
|---|---|
| `missing_source` | Check `source_path` in the entry — file was moved or deleted |
| `conversion_error` (Datalab) | Check `DATALAB_API_KEY`; check Datalab status page; check `parse_quality_score` in logs |
| `conversion_error` (Marker) | Check Ollama patch is applied; check `qwen3-vl:8b` model is pulled; try with `qwen3-vl:8b q4_K_M` |
| `conversion_error` (LaTeX) | `pymupdf4llm` used on math-heavy PDF — switch `document_profile` to `math_heavy` and re-process |
| Timeout / stall | Check which phase stalled in logs; only `LLM processors running` has phase override; increase general timeout or reduce PDF size |
| `FileNotFoundError` in incremental build | `manifest.json` references a path that no longer exists; remove the entry from the manifest or re-add the source file |

## Gotchas

- `RepoTaskStore` persists tasks that previously failed — they will retry on next app start unless removed. Use the UI task dashboard to cancel stuck tasks.
- Incremental build (`incremental_build_impl`) skips entries already in `manifest.json` by `source_path`. If you change a file and want it reprocessed, either remove it from the manifest or use "Full Rebuild".
- Marker capabilities are cached for the process lifetime (`_MARKER_CAPABILITIES_CACHE`). If you install Marker mid-session, restart the app.
- Datalab polling has a 1800-second ceiling. If a job is stuck on Datalab's side, the build thread hangs silently. Kill and retry.

## Verify (After Fix)

- [ ] `failed_entries` in manifest is empty for the repaired entry
- [ ] `logs` shows `status: "ok"` for all stages of the entry
- [ ] `images_dir` populated if image extraction was expected
- [ ] Re-run `python -m pytest tests -q` to confirm no regressions

## Update Scaffold
- [ ] If this was a new failure mode not listed above, add it to the table in this pattern
- [ ] If the fix required a code change, add a Gotcha to `context/pdf-pipeline.md`
