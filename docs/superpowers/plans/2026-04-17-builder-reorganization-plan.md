# Builder Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce `src/builder/engine.py` further and reorganize `src/builder/` into domain-based subpackages without breaking the current facade contract or the open modularization PR flow.

**Architecture:** Keep `src/builder/engine.py` as the stable facade and orchestration entrypoint while moving cohesive helper domains into subpackages. Do the work in two phases: first finish logical extraction behind the facade, then do the physical path reorganization into directories once domains are stable.

**Tech Stack:** Python 3.11, pytest, Tkinter app, git branch workflow, existing builder facade pattern

---

## Current State

- `src/builder/engine.py` is still large: about `7170` lines.
- Stable extracted modules already exist:
  - `content_taxonomy.py`
  - `entry_signals.py`
  - `image_markdown.py`
  - `navigation_artifacts.py`
  - `pedagogical_prompts.py`
  - `prompt_generation.py`
  - `repo_artifacts.py`
  - `student_state.py`
  - `teaching_plan_utils.py`
  - `timeline_index.py`
  - `timeline_signals.py`
- Recent consumers already stopped importing some internals from `engine.py`.
- Tests are green at the time of this plan:
  - `python -m pytest tests/test_core.py -q`
  - `python -m pytest tests/ -q`

## Target Builder Layout

Do not create all directories at once. This is the intended end state:

```text
src/builder/
  engine.py
  datalab_client.py
  semantic_config.py
  task_queue_runner.py

  artifacts/
    navigation.py
    prompts.py
    pedagogy.py
    repo.py
    student_state.py

  extraction/
    content_taxonomy.py
    entry_signals.py
    image_markdown.py
    teaching_plan.py

  timeline/
    index.py
    signals.py

  vision/
    image_classifier.py
    ollama_client.py
    vision_client.py
    card_evidence.py
```

## Non-Goals

- Do not rewrite `RepoBuilder` behavior.
- Do not change UI behavior as part of directory moves.
- Do not rename public facade functions unless there is already a wrapper in `engine.py`.
- Do not mix functional changes with file moves.
- Do not move everything in one batch.

## Safety Rules

- `engine.py` remains the compatibility facade until the end of the full migration.
- Every extraction batch must end with green tests before any path move starts.
- Every physical move batch must preserve import compatibility or update all imports in the same batch.
- Stop after any green checkpoint if token budget is low. Each batch below is designed to be independently resumable.

## Phase 1: Finish Logical Extraction

This phase reduces `engine.py` further without introducing new directories yet.

### Batch 1: Assessment and course/timeline context helpers

**Intent:** Move timeline-context assembly and assessment-context derivation out of `engine.py` into focused modules behind the facade.

**Primary files:**
- Modify: `src/builder/engine.py`
- Modify or create: `src/builder/timeline_index.py`
- Modify or create: `src/builder/repo_artifacts.py`
- Test: `tests/test_core.py`
- Test: `tests/test_file_map_unit_mapping.py`

**Move candidates:**
- `_build_file_map_timeline_context_from_course`
- `_build_assessment_context_from_course`
- small helper chains they uniquely depend on

**Checkpoint to stop safely:**
- `engine.py` wraps the moved functions
- all existing imports still work
- `python -m pytest tests/test_core.py -q`
- `python -m pytest tests/test_file_map_unit_mapping.py -q`
- `python -m pytest tests/ -q`

### Batch 2: Remaining file-map matching helpers

**Intent:** Finish extracting helper logic that still couples file-map routing to `engine.py`.

**Primary files:**
- Modify: `src/builder/engine.py`
- Modify: `src/builder/entry_signals.py`
- Modify: `src/builder/navigation_artifacts.py`
- Test: `tests/test_core.py`
- Test: `tests/test_file_map_unit_mapping.py`

**Move candidates:**
- helper functions used only by file-map routing
- lightweight normalization/scoring code still embedded in `engine.py`

**Checkpoint to stop safely:**
- no UI module imports these helpers from `engine.py`
- tests green

### Batch 3: Extraction backend helper grouping

**Intent:** Pull out non-UI, non-RepoBuilder helper logic for Marker/Docling/Datalab orchestration where it is already separable.

**Primary files:**
- Modify: `src/builder/engine.py`
- Create or modify focused backend helper modules only if cohesive
- Test: `tests/test_core.py`
- Test: backend-related tests if they exist

**Constraint:**
- Keep `RepoBuilder` in `engine.py`
- Do not split long worker methods if they are still tightly coupled to build state

**Checkpoint to stop safely:**
- `engine.py` materially smaller
- no behavior changes
- tests green

## Phase 2: Introduce Subpackages

Only start this phase after Phase 1 leaves `engine.py` in a noticeably smaller, more stable state.

### Batch 4: `artifacts/` package

**Intent:** Group generated-repository artifact modules by responsibility.

**Moves:**
- `navigation_artifacts.py` -> `artifacts/navigation.py`
- `repo_artifacts.py` -> `artifacts/repo.py`
- `pedagogical_prompts.py` -> `artifacts/pedagogy.py`
- `prompt_generation.py` -> `artifacts/prompts.py`
- `student_state.py` -> `artifacts/student_state.py`

**Files:**
- Modify: moved modules
- Modify: `src/builder/engine.py`
- Modify: all imports in UI/tests currently pointing at old flat paths

**Checkpoint to stop safely:**
- `src/builder/artifacts/__init__.py` exists only if needed
- all imports updated in one batch
- full test suite green

### Batch 5: `extraction/` package

**Moves:**
- `content_taxonomy.py` -> `extraction/content_taxonomy.py`
- `entry_signals.py` -> `extraction/entry_signals.py`
- `image_markdown.py` -> `extraction/image_markdown.py`
- `teaching_plan_utils.py` -> `extraction/teaching_plan.py`

**Checkpoint to stop safely:**
- facade imports in `engine.py` still re-export the same public functions
- full test suite green

### Batch 6: `timeline/` package

**Moves:**
- `timeline_index.py` -> `timeline/index.py`
- `timeline_signals.py` -> `timeline/signals.py`

**Checkpoint to stop safely:**
- all timeline-related imports point to the package paths
- test suite green

### Batch 7: `vision/` package

**Moves:**
- `image_classifier.py` -> `vision/image_classifier.py`
- `ollama_client.py` -> `vision/ollama_client.py`
- `vision_client.py` -> `vision/vision_client.py`
- `card_evidence.py` -> `vision/card_evidence.py`

**Checkpoint to stop safely:**
- no functional changes
- imports fixed
- tests green

## Phase 3: Facade Hardening

### Batch 8: Define stable facade exports

**Intent:** Make `engine.py` clearly intentional instead of accidentally broad.

**Tasks:**
- decide which symbols remain public from `engine.py`
- keep `RepoBuilder` and explicit compatibility wrappers
- stop re-exporting helpers that already have stable direct module consumers
- add a short comment block near top of `engine.py` describing facade policy

**Checkpoint to stop safely:**
- tests green
- no accidental consumer breakage

## Recommended Execution Order

1. Finish Phase 1 completely.
2. Move `artifacts/`.
3. Move `extraction/`.
4. Move `timeline/`.
5. Move `vision/`.
6. Harden the facade last.

## Per-Batch Working Rules

- One batch = one commit.
- Do not combine extraction and directory moves in the same commit.
- Run targeted tests first, then the full suite.
- If a batch touches imports across UI and tests, treat that as the natural stopping point.
- If token budget gets low, stop only after a green checkpoint and write a short handoff note in the commit message or session summary.

## Suggested Commit Shapes

- `refactor: extract assessment context behind engine facade`
- `refactor: extract file-map routing helpers behind engine facade`
- `refactor: move artifact modules into builder.artifacts package`
- `refactor: move extraction modules into builder.extraction package`
- `refactor: move timeline modules into builder.timeline package`
- `refactor: harden engine facade exports`

## Verification Matrix

Run these after each meaningful batch:

```bash
python -m pytest tests/test_core.py -q
python -m pytest tests/test_file_map_unit_mapping.py -q
python -m pytest tests/ -q
```

If a batch is only import-path movement and tests are expensive, the minimum acceptable checkpoint is:

```bash
python -m pytest tests/test_core.py -q
python -m pytest tests/test_file_map_unit_mapping.py -q
```

But do not merge or push a large reorganization batch without eventually running:

```bash
python -m pytest tests/ -q
```

## Resume Protocol

If the session dies mid-project, the next agent should:

1. Read this plan.
2. Run `git status --short`.
3. Run `python -m pytest tests/test_core.py -q`.
4. Identify the last completed batch from commits and current imports.
5. Resume from the next unfinished batch only.

## Exit Criteria

The reorganization is complete when:

- `engine.py` is primarily facade + orchestration
- domain modules live under domain subpackages
- UI and tests import dedicated modules directly where appropriate
- only intentional compatibility exports remain in `engine.py`
- full test suite is green
