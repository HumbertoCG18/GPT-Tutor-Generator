---
name: agents
description: Project identity, non-negotiables, commands, and scaffold growth instructions
last_updated: 2025-04-22
---

# GPT-Tutor-Generator

## What This Is

A desktop tool (Python/tkinter) that converts academic PDFs into structured GitHub repositories formatted as Claude Projects knowledge bases, acting as a persistent AI tutor per subject.

## Non-Negotiables

- Read existing files before writing. Do not re-read unless the file changed.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.
- New logic goes into the correct subpackage — never into `engine.py`. `engine.py` is a facade only.
- Imports must come from focused submodules, not from `engine.py`.
- No sycophantic openers, closing fluff, emojis, or em-dashes in output.
- No obvious comments; only non-obvious WHY comments.
- No multi-paragraph docstrings.
- Skip files over 100KB unless strictly required.
- Before calling any `mcp__code-review-graph__*` or `mcp__token-savior__*` tool, use `ToolSearch select:<name>` to load the schema first. Calling without loading fails with `InputValidationError`.

## Commands

```powershell
# Run all tests
python -m pytest tests -q

# Run a specific test file
python -m pytest tests/test_datalab_image_extraction.py -q

# Run the app
python app.py
```

## Scaffold Growth

After every task:
- If no pattern exists for this task type, create one and add it to `patterns/INDEX.md`.
- If a pattern was deviated from or a new gotcha was found, update it.
- If any context file is now outdated, update it surgically.
- Update "Current Project State" in `ROUTER.md` if the work was significant.

## Navigation

Read `.mex/ROUTER.md` before starting any task.