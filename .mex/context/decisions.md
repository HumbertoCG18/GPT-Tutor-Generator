---
name: decisions
description: Architectural choices and rationale for GPT-Tutor-Generator
triggers:
  - decision
  - why
  - rationale
  - architectural choice
edges:
  - target: context/architecture.md
    condition: when a decision affects system structure
  - target: context/stack.md
    condition: when a decision affects technology choice
last_updated: 2026-06-17
---

# Decisions

Append-only log. When a decision changes, mark the old entry as superseded and add the new decision above it.

---

### Generated Tutor Artifacts Carry Timeline Health and Temporal Context

**Date:** 2026-06-17
**Status:** Active
**Decision:** Regeneration writes cronograma health and temporal context artifacts alongside COURSE_MAP and FILE_MAP.
**Reasoning:** Timeline-aware tutoring needs both a compact current-schedule context and a visible audit surface for timeline/unit conflicts, stale overrides, and allocation health.
**Consequences:** Generated-output documentation and artifact tests must include both files. Tutor instructions may refer to the temporal context artifact, while operational diagnostics should use the cronograma health artifact.

---

### References Are First-Class Tutor Context

**Date:** 2026-06-17
**Status:** Active
**Decision:** Entries in reference/bibliography categories are fetched lightly, optionally summarized with Gemini, deterministically mapped to units/topics, cached in generated reference curation, surfaced in BIBLIOGRAPHY, and linked from COURSE_MAP support lines.
**Reasoning:** A tutor that only sees reference links and titles cannot use bibliography as grounding context. The cache keeps enrichment incremental, and the deterministic mapping still works when Gemini is unavailable.
**Consequences:** Reference changes must preserve no-key degradation, cache-by-hash behavior, COURSE_MAP support-line limits, and BIBLIOGRAPHY as the deep-reference target.

---

### Timeline Block Unit Assignment Uses Positional Matching

**Date:** 2026-06-17
**Status:** Active
**Decision:** Timeline blocks receive `auto_unit_slug` through the positional matcher in `src/builder/timeline/unit_matcher.py`, with authoritative non-class kinds excluded from unit assignment and manual overrides remaining dominant.
**Reasoning:** The previous keyword-only block-to-unit path produced confident but wrong unit inheritance. Monotonic positional assignment better matches course chronology and reduces fragile vocabulary coupling.
**Consequences:** Timeline/unit changes should be verified with unit matcher tests and rebuild-diff/eval harnesses where possible. Conflict reporting should compare manual overrides against the positional auto suggestion.

---

### Code Summarization Uses Gemini at Build Time (Optional Layer)

**Date:** 2026-06-02
**Status:** Active
**Decision:** Code entries can be summarized at build time through `google-genai`'s structured-output mode (`response_schema=CodeSummary`) with a content-hash cache in the generated repo's course/code_curation.json. Timeline block assignment is done locally via concept overlap, not via a second LLM call.
**Reasoning:** Code bundles benefit from semantic enrichment (inferred title, role, concepts) for richer downstream artifacts (CODE_INDEX, CRONOGRAMA_DETALHADO, CODE_HEALTH) and tutor grounding. Structured output prevents JSON parsing failures; the local matcher keeps the per-build cost bounded to one LLM call per changed entry. Without an API key the entire layer is bypassed via lazy import.
**Consequences:** Build pipeline must keep the no-key path identical to current behavior. New artifacts must be tolerant of empty code_curation.json. Future material types (PDF, exercises) follow the same hash-cache + local-link pattern.

---

### Generated Repositories Are Markdown-First

**Date:** 2026-05-04
**Status:** Active
**Decision:** The application consolidates imported academic materials into a structured Markdown repository.
**Reasoning:** Markdown is portable, reviewable, and directly usable as knowledge-base content for LLM tutors.
**Consequences:** Build and reprocess flows must preserve navigable Markdown output and tutor instruction artifacts.

---

### Desktop Application Instead of Web Service

**Date:** 2026-05-04
**Status:** Active
**Decision:** The product is a Python desktop application using Tkinter, with `app.py` as the main entry point.
**Reasoning:** The README describes a local academic-material processing workflow with UI-driven subject setup, file import, review, image curation, repository tasks, and dashboard monitoring.
**Consequences:** Setup and operational documentation should prioritize local Python execution rather than server deployment.

---

### Queue-Based Processing Persists Across Sessions

**Date:** 2026-05-04
**Status:** Active
**Decision:** Builds, reprocessing, and individual material processing run through a repository task queue that persists between app sessions.
**Reasoning:** The README states that the queue is persistent, which protects long-running repository work from app restarts.
**Consequences:** Task state is part of the product architecture and must be considered when changing build, reprocess, dashboard, or processing behavior.

---

### Manual Review Is an Explicit Stage

**Date:** 2026-05-04
**Status:** Active
**Decision:** Problematic processing outputs are routed to the generated repository's manual review area instead of being silently accepted.
**Reasoning:** Academic materials can contain difficult PDFs, images, links, and code. A manual correction point prevents low-quality generated repositories from being treated as complete.
**Consequences:** Processing changes should preserve a failure or uncertainty path into manual review.

---

### Image Understanding Is a Separate Curator Flow

**Date:** 2026-05-04
**Status:** Active
**Decision:** Images extracted from PDFs or imported as photos are handled through an Image Curator workflow with description extraction.
**Reasoning:** Academic images often carry pedagogical content that text-only processing misses.
**Consequences:** PDF processing and image curation should stay coordinated, but image review remains a distinct workflow.

---

### Multi-LLM Instruction Output

**Date:** 2026-05-04
**Status:** Active
**Decision:** The repository builder generates instructions/artifacts for Claude, GPT, and Gemini.
**Reasoning:** The README states that generated repositories are prepared for multiple LLM tutor targets.
**Consequences:** Changes to generated instructions must account for all supported LLM outputs.
