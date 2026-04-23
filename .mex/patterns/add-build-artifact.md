---
name: add-build-artifact
description: How to add a new generated file to the output repository
triggers:
  - new artifact
  - new generated file
  - add to repo output
edges:
  - target: context/repo-output.md
    condition: when understanding the existing output structure
  - target: context/architecture.md
    condition: when identifying which module should own the new artifact
last_updated: 2025-04-22
---

# Add Build Artifact

## Context

Load `context/repo-output.md` (existing artifacts) and `context/architecture.md` (which module owns generation).

## Steps

1. Identify which subpackage owns this artifact: `builder/artifacts/` for pedagogical files, `builder/facade/` for configured wrappers.
2. Create the generator module in the correct subpackage.
3. Register the artifact in `builder/ops/build_workflow.py` so it runs as part of the build.
4. Add the output path to `context/repo-output.md`.
5. Write tests in `tests/test_<artifact_name>.py`.

## Gotchas

- Internal artifacts (not meant to be loaded eagerly by Claude Projects) must go under `build/` in the output repo.
- Do not add generation logic to `engine.py`.
- If the artifact references other artifacts (e.g., FILE_MAP references COURSE_MAP), ensure build order is correct in `build_workflow.py`.

## Verify

- [ ] Generator lives in the correct subpackage, not in `engine.py`.
- [ ] Artifact is registered in `build_workflow.py`.
- [ ] Internal-only artifacts are output to `build/`, not to the repo root.
- [ ] Tests exist.

## Debug

If the artifact is missing from the output:
1. Check whether the generator is registered in `build_workflow.py`.
2. Check whether a previous step it depends on failed (inspect task queue state via `RepoTaskStore`).

## Update Scaffold

- [ ] Add the new artifact to the table in `context/repo-output.md`.
- [ ] Update `ROUTER.md` "Current Project State" if the artifact is now part of every build.