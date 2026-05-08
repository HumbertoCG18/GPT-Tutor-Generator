---
name: router
description: Session bootstrap. Read this before any task. Contains project state, routing table, and behavioural contract.
last_updated: 2026-05-04
---

# ROUTER.md - Session Bootstrap

Read this file before starting any task.

---

## Current Project State

### Working

- Python desktop app with Tkinter UI, launched through `app.py`.
- Manifest is `pyproject.toml` with package name `academic-tutor-repo-builder` and version `3.0.0`.
- Academic-material import flow supports files and links.
- Processing flow handles PDFs, links, images, and code.
- Problematic processing outputs are reviewed through `manual-review/`.
- Image Curator supports images extracted from PDFs and imported photos.
- Repository builder consolidates content into Markdown.
- Generated tutor artifacts target Claude, GPT, and Gemini.
- Repository task queue supports builds, reprocessing, and individual material processing.
- Queue state persists between app sessions.
- Dashboard monitors operational repository state.
- Reprocess Repository reapplies the current architecture to existing generated repositories.
- Test runner is `pytest`; brief lists 28 files under `tests/`.
- Auto-tags de unidade/subunidade/bloco geradas em `resolve_unit_block_tags()`:
  tags `unit:`, `subunit:`, `bloco:` persistidas em `auto_tags` do manifest após
  cada regeneração pedagógica.
- Sinal DD.MM: arquivo `12.03 Processos.pdf` recebe boost +0.30 no bloco do
  cronograma correspondente em `score_entry_against_timeline_block()`.

### Not Declared In Brief

- Runtime dependencies are not declared in the manifest brief.
- Development dependencies are not declared in the manifest brief.
- Project scripts are not declared in the manifest brief.
- Build tool, linter, formatter, and package manager are not declared in the brief.
- Exact Datalab API/package version is not declared in the brief.
- Exact Ollama model/version is not declared in the brief.

### Current Design Focus

- Tag system needs redesign before implementation.
- Desired tag role: improve confidence and precision for automatic block and unit assignment.
- Desired extension: infer subunits from tags using a scoring system compatible with existing assignment logic.
- Refactor should be planned to avoid repeated large rewrites.

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

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.
