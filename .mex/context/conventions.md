---
name: conventions
description: Code conventions, naming rules, structure patterns, and the verify checklist
triggers:
  - convention
  - naming
  - code style
  - verify
  - review
  - how to write
  - pattern
edges:
  - target: context/architecture.md
    condition: when understanding where new code should live
  - target: context/decisions.md
    condition: when a convention traces back to an architectural decision
last_updated: 2025-04-22
---

# Conventions

## Naming

- Test files: `tests/test_<module>.py`
- Test fixtures: `tests/fixtures/`
- No other naming constraints documented — follow existing module names in each subpackage.

## Structure

- `engine.py` is a facade. No new logic goes there. New consumers import from focused submodules directly.
- New logic goes into the correct subpackage under `src/builder/`.
- `Optional[X]` with default `None` for optional fields in dataclasses.
- Imports must come from focused submodules, never from `engine.py`.

## Comments and Docstrings

- No obvious comments — only non-obvious WHY comments.
- No multi-paragraph docstrings.

## Verify Checklist

Run these checks item by item after writing any code:

- [ ] New logic is in the correct subpackage, not in `engine.py`.
- [ ] Imports come from focused submodules, not from `engine.py`.
- [ ] Optional dataclass fields use `Optional[X]` with default `None`.
- [ ] No obvious comments added — only non-obvious WHY.
- [ ] No multi-paragraph docstrings added.
- [ ] Any new MCP tool call is preceded by `ToolSearch select:<n>` to load the schema.
- [ ] If using `pymupdf4llm` for a `math_heavy` file — this is wrong. Switch to Datalab or Marker.
- [ ] If touching `RepoTaskStore` — verify the queue is not being manually recreated.