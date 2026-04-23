---
name: stack
description: Technology choices, PDF backends, vision pipeline, and MCP tools
triggers:
  - backend
  - pdf backend
  - vision
  - ollama
  - datalab
  - stack
  - technology
  - mcp tools
  - marker
  - docling
edges:
  - target: context/architecture.md
    condition: when understanding how the backends fit into the overall system
  - target: context/setup.md
    condition: when needing env vars or how to run each backend
last_updated: 2025-04-22
---

# Stack

## Core Technologies

| Technology | Version / Notes |
|---|---|
| Python | Primary language |
| tkinter | Desktop UI framework |
| pytest | Test runner — `tests/test_<module>.py`, fixtures in `tests/fixtures/` |
| pymupdf / pymupdf4llm | Base PDF processing for all simple cases |

## PDF Backend Models

| Backend | Use case | Notes |
|---|---|---|
| `datalab` | Primary for `math_heavy` content | Requires `DATALAB_API_KEY`; most reliable for formulas |
| `docling` / `docling_python` | Local/GPU alternative | No API key needed |
| `marker` | Available, under investigation | Not the main path; cloud models (qwen3-vl:235b-cloud) cause 500 errors — use `qwen3-vl:8b q4_K_M` instead |
| `pymupdf4llm` / `pymupdf` | Base for all simple cases | Can silently corrupt LaTeX; do not use for `math_heavy` |

Datalab saves images to:
```
staging/markdown-auto/datalab/<entry>/images/
```
The real path comes from `_save_datalab_images` in `datalab_client.py` and is returned via `BackendRunResult.images_dir`.

## Vision Pipeline

- Backend: `ollama` (local)
- Default endpoint: `http://localhost:11434/api/chat`
- Fully independent of the PDF backend — Datalab for PDF and Ollama for Vision can run simultaneously.
- Stable model on RTX 4050 6GB: `qwen3-vl:8b q4_K_M`

## MCP Tools

### code-review-graph

Knowledge graph MCP server. **Always use graph tools BEFORE Grep/Glob/Read.**

| Tool | Use when |
|---|---|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

The graph auto-updates on file changes via hooks.

### token-savior

Complementary structural analysis tools: call chains, dead code, hotspots, symbol impact, file dependencies, structural search via tree-sitter.

Use when: tracing call chains from a specific function, finding dead code, calculating rename impact, checking which tests cover a file.

**Critical**: Both MCP servers are deferred tools. Before calling any `mcp__code-review-graph__*` or `mcp__token-savior__*` tool, use `ToolSearch select:<name>` to load the schema. Calling without loading fails with `InputValidationError`.

## What We Deliberately Do NOT Use

- No cloud LLM API calls during the build pipeline (LLM is used only in the generated repo at runtime).
- No MarkItDown for PDFs (rejected — evaluated and discarded; noted as potentially useful for future PPTX/DOCX use).
- No notebooklm-py (flagged as risky).
- No web framework — this is a local desktop app only.