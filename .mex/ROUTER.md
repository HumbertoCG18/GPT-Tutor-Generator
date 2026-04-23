---
name: router
description: Session bootstrap — read this before any task. Contains project state, routing table, and behavioural contract.
last_updated: 2025-04-22
---

# ROUTER.md — Session Bootstrap

Read this file before starting any task.

---

## Current Project State

### Working
- Full PDF → GitHub repo pipeline (pymupdf, datalab, docling, marker backends)
- FILE_MAP routing and First Session Protocol for Claude tutor
- Multi-LLM output: separate instruction files for Claude, GPT, Gemini
- RepoTaskStore persistent task queue (survives restarts)
- Vision pipeline via Ollama (local, independent of PDF backend)
- Image extraction and curation via Datalab + `BackendRunResult.images_dir`
- 109-test suite covering Increment 1 features
- tkinter UI with theme, curator studio, repo dashboard, image curator

### Not Yet Built
- Post-extraction noise cleanup
- Per-file summaries inside FILE_MAP
- Confidence column in FILE_MAP
- Temporal history in STUDENT_STATE
- Corrupted LaTeX validation (silent corruption from pymupdf4llm)
- Claude Code CLI prompts pending execution: `CLAUDE_CODE_TOKEN_OPTIMIZATION.md`, `CLAUDE_CODE_MULTI_LLM.md`

### Known Issues
1. **Local patch outside repo** — `.venv/.../marker/services/ollama.py` has a manual patch. If `.venv` is recreated, the patch is lost. No committed version of the patch exists.
2. **Marker + cloud models unstable** — `qwen3-vl:235b-cloud` causes 500 errors with Marker; use `qwen3-vl:8b q4_K_M` (stable on RTX 4050 6GB).
3. **Silent LaTeX corruption** — `pymupdf4llm` can corrupt formulas without signaling; use Marker or Datalab for `math_heavy` content.
4. **Stall timeout incomplete** — only `LLM processors running` phase has an override; other phases use a general timeout calculated per backend.

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `context/architecture.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** — Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** — Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** — Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** — If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** — After completing the task, update scaffold files as described in `AGENTS.md → Scaffold Growth`.