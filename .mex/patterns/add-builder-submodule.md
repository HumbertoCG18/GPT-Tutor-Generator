---
name: add-builder-submodule
description: Adding new processing logic to a builder subpackage. The most common development task — never add new logic to engine.py.
triggers:
  - "add feature"
  - "new logic"
  - "new function"
  - "new module"
  - "extend builder"
edges:
  - target: context/conventions.md
    condition: always — check naming, structure, and verify checklist
  - target: context/architecture.md
    condition: when deciding which subpackage owns the new logic
  - target: patterns/add-ui-feature.md
    condition: when the new builder logic also needs a UI entry point or dialog
last_updated: 2026-04-22
---

# Add Builder Submodule

## Context

All new processing logic goes into a focused subpackage under `src/builder/`. Choose the right subpackage:
- `extraction/` — content analysis, taxonomy, image markdown, entry signals
- `ops/` — build lifecycle operations (build, incremental, cleanup, state)
- `pdf/` — PDF conversion and profiling
- `artifacts/` — generating markdown artifacts (COURSE_MAP, FILE_MAP, prompts)
- `runtime/` — external service clients (Datalab, backend capabilities)
- `vision/` — Ollama image classification
- `routing/` — FILE_MAP matching and scoring
- `facade/` — engine-level wrappers that expose configured submodule functionality
- `core/` — utilities shared within `builder/` (semantic config, markdown utils)

## Steps

1. Identify which existing subpackage owns this concern — read `context/architecture.md` if unclear
2. Create or edit the `.py` file in the correct subpackage
3. Write the function with `from __future__ import annotations` at top and `logger = logging.getLogger(__name__)` if logging is needed
4. For optional dataclass fields: always use `Optional[X] = None` or `field(default_factory=...)`
5. Use `write_text` from `src.utils.helpers` for any file writes; use `ensure_dir` before creating directories
6. If the function needs to be callable from `RepoBuilder`: add a thin delegation method in `engine.py` that imports from your new module — do NOT move the implementation into `engine.py`
7. Write a test in `tests/test_<your_module>.py`; import the function directly from the subpackage

## Gotchas

- `engine.py` re-exports everything with `_`-prefixed aliases. If you see `_file_map_auto_map_entry_unit`, the real implementation is in `src.builder.routing.file_map.auto_map_entry_unit`. Don't duplicate it.
- `src/utils/helpers.py` loads `.env` on import (side effect on first import). Don't replicate this — import from `helpers` instead.
- Mutable default in dataclass: `tags: List[str] = []` is wrong — use `tags: List[str] = field(default_factory=list)`.
- If adding a field to an existing dataclass, also update `to_dict()` / `from_dict()` if they don't use `asdict` / `**data` automatically. Check if the dataclass uses `@classmethod from_dict(cls, data)` with explicit field mapping — it may need updating.

## Verify

- [ ] New code is in a focused subpackage, not in `engine.py`
- [ ] `logger = logging.getLogger(__name__)` at module level (no `print`)
- [ ] Optional fields have `= None` default
- [ ] File writes use `write_text` from `src.utils.helpers`
- [ ] Test file created at `tests/test_<module>.py`
- [ ] No comments explaining WHAT the code does

## Update Scaffold
- [ ] Update `.mex/ROUTER.md` "Current Project State" if a significant new capability was added
- [ ] Update `context/architecture.md` Key Components if a new major component was introduced
- [ ] If this is a new task type without a pattern, create one in `.mex/patterns/` and add to `INDEX.md`
