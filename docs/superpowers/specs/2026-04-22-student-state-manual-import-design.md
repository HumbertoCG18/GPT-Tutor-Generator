# Student State Manual Import Design

**Date:** 2026-04-22

**Goal**

Replace the unusable `FILE_MAP` toolbar button with a `Student State` workflow that lets the student paste a tutor-generated markdown block, validate it against the current `COURSE_MAP`, save or append the corresponding battery file, and patch `student/STUDENT_STATE.md` without going through the PDF pipeline.

## Problem

Current study continuity depends on the tutor reading a cold repository state at the start of every chat. That causes two failures:

- cold starts: the tutor does not know where the student stopped
- context flooding: users compensate by stuffing long history into prompt files

The existing repo already has `student/STUDENT_STATE.md` plus topic batteries under `student/batteries/`, but there is no desktop workflow for quickly importing a tutor-produced session update into that structure.

## Non-Goals

- no new PDF pipeline stage
- no new task queue job
- no Datalab dependency
- no changes to `engine.py` business logic beyond facade exposure if strictly needed
- no fallback save to free-form `manual/` when course validation fails

## User Workflow

1. User clicks `Student State` in the main toolbar where `FILE_MAP` used to be.
2. App opens a dedicated `Student State` window inspired by Curator Studio but simpler.
3. User pastes a tutor-generated markdown block into an import area.
4. User clicks `Importar`.
5. App parses frontmatter and content, then validates `unit` and `topic` against the current course structure derived from `COURSE_MAP` inputs.
6. If tutor metadata is invalid, the UI shows the problem and allows manual correction through dropdowns populated from the valid course units and topics.
7. User reviews the normalized battery content.
8. On save, the app:
   - creates or updates `student/batteries/<unit>/<topic>.md`
   - appends a new session section to the topic battery
   - patches `student/STUDENT_STATE.md`
9. User commits and pushes the changed repo for the tutor to consume in later chats.

## Tutor Contract

The tutor should be updated later to emit an importable markdown block with frontmatter containing:

- `unit`
- `unit_title`
- `topic`
- `topic_title`
- `status`
- `date`
- `time`
- `next_topic` optional

The app treats tutor output as a draft, not as ground truth.

## Validation Rules

Validation source must stay aligned with the current builder architecture:

- read canonical unit/topic structure from the same course data used to generate `COURSE_MAP`
- do not parse `FILE_MAP`
- do not invent unit/topic names

Rules:

- `unit` must match a known unit slug
- `topic` must match a known topic slug within the selected unit
- `status` must be one of: `pendente`, `em_progresso`, `compreendido`, `revisao`
- if `date` or `time` is missing, fill with current local timestamp
- if tutor values fail validation, save stays blocked until the user corrects them

## Data Model Decisions

### Battery Persistence

Topic batteries remain canonical and continue to live at:

- `student/batteries/<unit>/<topic>.md`

Save behavior:

- if the battery file does not exist, create it with current frontmatter
- if it exists, preserve frontmatter and append a new session block

### Session Append Format

Imported sessions must normalize into the current battery style already used by `student_state.py`:

- YAML frontmatter with `topic`, `topic_slug`, `unit`, `status`
- body sections appended as `## <date> (sessao N)` style history blocks

The app owns normalization. Raw tutor markdown is never written verbatim if it breaks the canonical battery format.

### STUDENT_STATE Patch

Saving a battery update must patch these fields in `student/STUDENT_STATE.md`:

- `updated`
- `active.unit`
- `active.topic`
- `active.status`
- `active.file`
- `active.sessions`
- `recent`
- `next_topic` when provided

`active_unit_progress` should be refreshed via existing student-state helpers using the real unit slug so the manual import participates in the current progress model.

## UI Design

New window responsibilities:

- import textbox for pasted tutor markdown
- `Importar` action
- validation summary
- unit dropdown
- topic dropdown filtered by selected unit
- status dropdown
- read-only target path preview
- editable normalized markdown/session content area
- `Salvar` action

The window is local and synchronous. No queue task is created.

## Architecture Placement

To respect current subdirectory boundaries:

- UI lives in `src/ui/`
- student-state file mutation helpers live in `src/builder/artifacts/student_state.py` or a focused neighbor under `src/builder/artifacts/`
- course unit/topic derivation should reuse existing teaching-plan and course-map related functions, not duplicate parsing inside the UI

`engine.py` must remain a facade only.

## Error Handling

Expected errors:

- repo root missing
- `student/STUDENT_STATE.md` missing
- invalid import markdown
- unknown unit slug
- unknown topic slug
- topic not belonging to selected unit
- battery write failure
- state patch failure

Save must be transactional enough to avoid a false-success state:

- validate first
- write battery
- patch `STUDENT_STATE`
- if patch fails after battery write, report failure clearly so the user can fix and save again

## Testing Scope

Tests should cover:

- parsing tutor import frontmatter
- dropdown correction path
- create new battery file
- append to existing battery file
- patch `STUDENT_STATE.md`
- refresh unit progress after save
- reject invalid unit/topic

## Risks

Main risks:

- current battery format expectations are stricter than tutor output
- patching `STUDENT_STATE.md` by ad hoc regex could corrupt the file
- unit/topic validation may drift if UI logic does not reuse canonical course parsing

Mitigations:

- normalize all imports into the existing battery format
- add dedicated helper functions in the student-state artifact layer
- reuse existing teaching-plan parsing and topic slug generation

## Acceptance Criteria

- toolbar shows `Student State` instead of `FILE_MAP`
- pasted tutor markdown can populate the window
- invalid unit/topic can be corrected manually by dropdown
- valid save creates or appends `student/batteries/<unit>/<topic>.md`
- valid save patches `student/STUDENT_STATE.md`
- imported session becomes readable by the tutor through existing repo structure
