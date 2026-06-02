---
name: gemini-code-summarization
description: Pattern for adding a Gemini-backed batch summarization layer with content-hash cache and lazy import
triggers:
  - gemini
  - summarization
  - batch llm
  - structured output
edges:
  - target: ../context/decisions.md
    condition: when revisiting why Gemini is optional
  - target: ../context/architecture.md
    condition: when wiring a new summarization layer
last_updated: 2026-06-02
---

# Gemini Batch Summarization Pattern

Use when adding a build-time Gemini layer that enriches a class of entries (code, PDFs, exercises) with structured summaries, cached by content hash, with lazy degradation when no API key is configured.

## Reference implementation

| Piece | File |
|---|---|
| Lazy client + retry | `src/builder/runtime/gemini_client.py` |
| Engine (schemas, hash, bundle, prune) | `src/builder/core/code_summarization.py` |
| Settings UI | `src/ui/dialogs.py` (Gemini section) |
| Engine wiring | `src/builder/engine.py` (`_load_code_curation`, `_summarize_code_entries`, `_prune_stale_code_curation`) |
| Build pipeline prune call | `src/builder/ops/build_workflow.py` + `incremental_build.py` |
| Renderers consuming curation | `src/builder/core/source_importers.py`, `src/builder/artifacts/repo.py` (CODE_INDEX, CRONOGRAMA_DETALHADO, CODE_HEALTH) |

## Steps for a new entry class (e.g. PDFs)

1. Define a `BaseModel` schema + `SYSTEM_INSTRUCTION` mirroring `CodeSummary`. Concepts list MUST be 3-8 normalized strings — the local block matcher depends on it.
2. Write a `_build_bundle_text(builder, entry_data)` that flattens base + extracted children into <200k chars (clip + marker if larger).
3. Reuse `compute_entry_hash` semantics: hash the bundle text, not the entry dict.
4. Persist in `<class>_curation.json` with shape `{version, entries: {id: {content_hash, model, generated_at, summary}}}`. Atomic write only.
5. Add a `prune_stale_<class>_curation(builder)` that removes ids not in `manifest.json`. Call it from `build_workflow.py` and `incremental_build.py` after manifest reload.
6. Block matching: reuse `assign_code_to_block` if concepts shape is identical; otherwise duplicate the matcher with the same thresholds (`primary=0.4`, `secondary=0.25`, `margin=0.15`) and calibrate later.
7. Lazy import: never `import google.genai` at module top. Always inside method bodies. Anti-pattern grep: `google.generativeai`, `genai.GenerativeModel`.

## Anti-patterns

- Module-level `from google import genai` — breaks no-key flow.
- `response_format={...}` wrapper — Gemini SDK uses `response_mime_type` + `response_schema`.
- Re-hashing entry dicts instead of the bundle text (cache becomes stale on cosmetic edits).
- LLM call inside `assign_*_to_block`: matcher must stay local.
- Logging the API key. Treat as secret.

## Verification

Mirror plan §1.5: anti-pattern grep, `py_compile`, smoke `has_gemini_api_key({})/({key})`, matcher smoke with synthetic blocks.
