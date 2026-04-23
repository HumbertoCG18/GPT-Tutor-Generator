---
name: architecture
description: How the major pieces of GPT-Tutor-Generator connect and flow
triggers:
  - architecture
  - system design
  - how does X connect to Y
  - module structure
  - folder structure
edges:
  - target: context/stack.md
    condition: when specific technology or backend details are needed
  - target: context/decisions.md
    condition: when understanding why the architecture is structured this way
  - target: context/repo-output.md
    condition: when the task involves the generated repository format
last_updated: 2025-04-22
---

# Architecture

## System Overview

```
app.py
  └── src/ui/app.py          # main window, tab routing
        └── builder/engine.py  # facade — orchestrates subsystems
              ├── builder/ops/         # build lifecycle operations
              ├── builder/pdf/         # PDF pipeline and assets
              ├── builder/artifacts/   # COURSE_MAP, FILE_MAP, prompts, student_state
              ├── builder/extraction/  # taxonomy, entry signals, image markdown
              ├── builder/facade/      # configured wrappers exposed by engine
              ├── builder/routing/     # FILE_MAP matching and routing
              ├── builder/runtime/     # external backend clients (Datalab, Ollama)
              ├── builder/text/        # sanitization, URL→markdown
              ├── builder/timeline/    # schedule index and signals
              ├── builder/vision/      # visual classification
              └── builder/core/       # central utilities (config, markdown, images)
```

## Key Components

| Module | What it does | Depends on |
|---|---|---|
| `engine.py` | Stable facade — orchestrates calls between subsystems. No new logic here. | All builder subpackages |
| `builder/ops/` | Build lifecycle: bootstrap, workflow, entry processing, incremental build, state | engine, models, pdf, artifacts |
| `builder/pdf/` | PDF pipeline, asset extraction, scanned PDF handling | runtime, core |
| `builder/artifacts/` | Generates COURSE_MAP, FILE_MAP, prompts, navigation, student_state | models, extraction |
| `builder/runtime/` | External clients: Datalab API, Ollama Vision | network, env vars |
| `builder/extraction/` | Content taxonomy, entry signals, image markdown, teaching plan | core, pdf |
| `models/core.py` | Central dataclasses: SubjectProfile, BackendRunResult, etc. | — |
| `models/task_queue.py` | RepoTask and RepoTaskStore — persistent JSON task queue | — |
| `src/ui/` | tkinter UI: main window, curator studio, repo dashboard, image curator, dialogs | engine, models |

## Full Directory Map

```
app.py                          # bootstrap: starts TK, calls src/ui/app.py

src/
├── builder/
│   ├── engine.py               # facade — orchestrates calls between subsystems
│   ├── artifacts/              # COURSE_MAP, FILE_MAP, prompts, navigation, student_state
│   │   ├── navigation.py
│   │   ├── pedagogy.py
│   │   ├── prompts.py
│   │   ├── repo.py
│   │   └── student_state.py
│   ├── core/                   # central utilities (semantic config, markdown, images)
│   │   ├── core_utils.py
│   │   ├── image_resolution.py
│   │   ├── markdown_utils.py
│   │   ├── semantic_config.py
│   │   └── source_importers.py
│   ├── extraction/             # taxonomy, entry signals, image markdown
│   │   ├── content_taxonomy.py
│   │   ├── entry_signals.py
│   │   ├── image_markdown.py
│   │   └── teaching_plan.py
│   ├── facade/                 # configured wrappers exposed by engine
│   │   ├── file_map.py
│   │   ├── glossary.py
│   │   ├── navigation_templates.py
│   │   ├── repo_docs.py
│   │   └── teaching_timeline.py
│   ├── ops/                    # build lifecycle operations
│   │   ├── bootstrap_ops.py
│   │   ├── build_workflow.py
│   │   ├── entry_processing.py
│   │   ├── incremental_build.py
│   │   ├── lifecycle_ops.py
│   │   ├── operational_artifacts.py
│   │   ├── pedagogical_regeneration.py
│   │   ├── state_ops.py
│   │   ├── task_queue_runner.py
│   │   └── url_and_cleanup.py
│   ├── pdf/                    # PDF pipeline and assets
│   │   ├── pdf_analysis.py
│   │   ├── pdf_assets.py
│   │   ├── pdf_pipeline.py
│   │   └── pdf_scanned.py
│   ├── routing/                # FILE_MAP matching and routing
│   │   └── file_map.py
│   ├── runtime/                # external backend clients
│   │   ├── backend_runtime.py
│   │   └── datalab_client.py
│   ├── text/                   # sanitization, URL→markdown conversion
│   │   ├── sanitization.py
│   │   └── url_markdown.py
│   ├── timeline/               # schedule index and signals
│   │   ├── index.py
│   │   └── signals.py
│   └── vision/                 # vision and visual classification
│       ├── card_evidence.py
│       ├── image_classifier.py
│       ├── ollama_client.py
│       └── vision_client.py
├── models/
│   ├── core.py                 # central dataclasses (SubjectProfile, BackendRunResult, …)
│   └── task_queue.py           # RepoTask and RepoTaskStore (persistent JSON queue)
├── ui/
│   ├── app.py                  # main window and tab routing
│   ├── consolidate_unit_dialog.py
│   ├── curator_studio.py       # manual entry review
│   ├── dialogs.py              # settings, status, help, and other dialogs
│   ├── image_curator.py        # image curation and visual extraction
│   ├── repo_dashboard.py       # operational repository dashboard
│   └── theme.py                # theme and persisted preferences
└── utils/
    ├── helpers.py              # general helpers, autodetects, OCR/Tesseract
    └── power.py                # prevents sleep during long builds
```

## External Dependencies

| Dependency | What it is | Constraint |
|---|---|---|
| Datalab API | Primary PDF backend for `math_heavy` content | Requires `DATALAB_API_KEY` |
| Ollama | Local vision backend | Default endpoint `http://localhost:11434/api/chat`; independent of PDF backend |
| GitHub | Output destination for generated repos | Configured per SubjectProfile |
| Tesseract | OCR fallback | Must be installed locally |

## What Does NOT Exist Here

- No web server, no HTTP API — this is a local desktop app only.
- No LLM calls during the build pipeline itself — LLM is used only in the generated repo (by the Claude tutor at runtime).
- No centralized logic in `engine.py` — it is a facade only.