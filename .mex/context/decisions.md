---
name: decisions
description: Append-only architectural decision log for GPT-Tutor-Generator
triggers:
  - decision
  - why
  - rationale
  - architectural choice
  - why was X chosen
edges:
  - target: context/architecture.md
    condition: when a decision affects the overall system structure
  - target: context/stack.md
    condition: when a decision involves a technology or backend choice
last_updated: 2025-04-22
---

# Decisions

Append-only log. Never delete entries. When a decision changes, mark the old entry as "Superseded by [new title]" and add the new decision above it.

---

### Multi-LLM Output — Separate Instruction Files per LLM

**Date:** 2025-04-22
**Status:** Active
**Decision:** The build generates separate instruction files for Claude, GPT, and Gemini from a single build run, rather than one generic file.
**Reasoning:** Each LLM has different prompt conventions and context window behaviors. A single file produces suboptimal results across all three.
**Alternatives considered:** Single generic instruction file; runtime LLM selection.
**Consequences:** `preferred_llm` and `github_url` fields added to `SubjectProfile`. Build output includes `INSTRUCOES_CLAUDE_PROJETO.md`, `INSTRUCOES_GPT_PROJETO.md`, and `INSTRUCOES_GEMINI_PROJETO.md`.

---

### First Session Protocol Replaces Auto-Categorization LLM

**Date:** 2025-04-22
**Status:** Active
**Decision:** Removed the auto-categorization LLM in favor of a First Session Protocol where the Claude tutor maps files to course units on first use.
**Reasoning:** Auto-categorization did not work as expected and was corrected manually. Moving categorization to runtime (inside the generated repo) removes a fragile build-time LLM dependency and makes the mapping more accurate because the tutor has full student context at that point.
**Alternatives considered:** Keeping auto-categorization with fixes; manual categorization UI.
**Consequences:** FILE_MAP is generated without pre-assigned categories. The Claude tutor performs unit mapping during the first session using FILE_MAP as a navigation index.

---

### FILE_MAP.md as Navigation Index

**Date:** 2025-04-22
**Status:** Active
**Decision:** Introduced `FILE_MAP.md` as a dedicated navigation index inside the generated repo.
**Reasoning:** Without a structured index, the Claude tutor was spending tokens exploring the filesystem. FILE_MAP gives it a pre-built lookup table — faster and cheaper per session.
**Alternatives considered:** Relying on COURSE_MAP alone; directory listing at runtime.
**Consequences:** FILE_MAP is a required artifact of every build. `builder/routing/file_map.py` owns the matching and routing logic.

---

### Internal Documentation Moved to build/

**Date:** 2025-04-22
**Status:** Active
**Decision:** Internal documentation files (bundle.seed.json, etc.) moved to `build/` inside the generated repo to reduce token overhead.
**Reasoning:** Files in the root of a Claude Project knowledge base are loaded eagerly. Moving internal docs to a subdirectory keeps them available without polluting the top-level context on every session.
**Alternatives considered:** Keeping everything at root; separate repo for internal docs.
**Consequences:** Claude tutor instructions reference `build/` paths explicitly.

---

### engine.py is a Facade — No New Logic

**Date:** 2025-04-22
**Status:** Active
**Decision:** `engine.py` is progressively emptied. All new logic goes into the correct subpackage. New consumers import from focused modules, not from `engine.py`.
**Reasoning:** `engine.py` was becoming a god object. Splitting logic into focused subpackages improves testability and makes impact radius of changes smaller.
**Alternatives considered:** Keeping engine.py as the main logic hub.
**Consequences:** Any new feature must identify the correct subpackage before writing code. Imports from `engine.py` in new code are a convention violation.

---

### BackendRunResult.images_dir

**Date:** 2025-04-22
**Status:** Active
**Decision:** `images_dir: Optional[str]` field added to `BackendRunResult` in `src/models/core.py`, propagated from Datalab backend when images are extracted.
**Reasoning:** The image curation pipeline needs to know where Datalab saved images. Propagating via the result object keeps the pipeline decoupled from Datalab internals.
**Alternatives considered:** Hardcoded path convention; separate images manifest file.
**Consequences:** `images_dir` appears in the item manifest and is consumed by the image curation UI.

---

### RepoTaskStore Persists Queue in JSON

**Date:** 2025-04-22
**Status:** Active
**Decision:** `RepoTaskStore` persists the task queue to JSON between sessions.
**Reasoning:** Long builds can be interrupted. Persisting the queue means work survives app restarts without manual reconstruction.
**Alternatives considered:** In-memory queue only; SQLite.
**Consequences:** Do not manually recreate `RepoTaskStore`. The queue survives restarts by design.

---

### Vision Backend: Ollama (Local), Independent of PDF Backend

**Date:** 2025-04-22
**Status:** Active
**Decision:** Vision pipeline uses Ollama locally and is fully independent of the PDF backend.
**Reasoning:** Separating vision from PDF processing allows using the best tool for each task (e.g., Datalab for PDF + Ollama for vision simultaneously).
**Alternatives considered:** Unified backend handling both PDF and vision; cloud vision API.
**Consequences:** Vision endpoint defaults to `http://localhost:11434/api/chat`. Stable model on RTX 4050 6GB: `qwen3-vl:8b q4_K_M`.