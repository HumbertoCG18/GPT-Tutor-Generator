---
name: setup
description: How to set up, run, and test GPT-Tutor-Generator
triggers:
  - setup
  - install
  - run
  - environment
  - test
  - pytest
  - gitleaks
  - credentials
edges:
  - target: context/stack.md
    condition: when exact technology or manifest details are needed
  - target: context/architecture.md
    condition: when understanding runtime behavior after startup
last_updated: 2026-09-24
---

# Setup

## Requirements From Brief

| Requirement | Source |
|---|---|
| Python `3.8+` | README badge and requirements section reference. |
| Tkinter | README identifies the UI as Tkinter. |
| Ollama | README identifies Vision support through Ollama. |
| Datalab | README identifies the PDF backend as Datalab. |
| pytest | Brief tooling identifies `pytest` as the test runner. |

The brief does not declare package dependencies, development dependencies, scripts, a formatter, a linter, or a package manager.

## Install

Use a Python virtual environment. Exact dependency installation command is not declared in the brief, because `pyproject.toml` dependencies and dev dependencies are listed as empty.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If a task needs an exact install command, read `pyproject.toml` before documenting or running one.

## Run

The application main entry point is:

```powershell
python app.py
```

## Test

The test runner is `pytest`.

```powershell
python -m pytest tests -q
```

Known test entry points from the brief include:

```powershell
python -m pytest tests/test_unit_fallback.py -q
python -m pytest tests/test_ui_queue_dashboard.py -q
python -m pytest tests/test_timeline_signals.py -q
python -m pytest tests/test_timeline_scoring_ignored.py -q
python -m pytest tests/test_timeline_index_kind.py -q
python -m pytest tests/test_task_queue.py -q
python -m pytest tests/test_tag_catalog.py -q
python -m pytest tests/test_student_state_v2.py -q
python -m pytest tests/test_student_state_manual_import.py -q
```

## Segredos e credenciais (#80-#82; incidente de 24/09/2026)

- Hook obrigatorio, compartilhado por todas as worktrees:
  `cp scripts/hooks/pre-commit.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"`.
  Sem gitleaks 8.30.1 ou sem Python 3.8+, o commit falha; nao ha modo de aviso.
- gitleaks fixado: `python scripts/security/gitleaks_scan.py install --dest <dir no PATH>` baixa a release oficial e
  confere o SHA-256 antes de extrair (Windows x64, Linux e macOS x64/arm64). Na nuvem, o SessionStart de
  `.claude/settings.json` roda `scripts/security/setup_nuvem.sh` (so com `CLAUDE_CODE_REMOTE=true`): instala o
  gitleaks em `~/.local/bin` e o pre-commit com `chmod +x`. Se o download falhar, os commits ficam bloqueados.
- Varredura manual, saida so com regra, arquivo, linha e commit:
  `gitleaks_scan.py staged | range BASE..HEAD | history`. Higiene: `check_repo_hygiene.py tree | range BASE..HEAD | staged`.
- CI: `.github/workflows/security.yml` roda as duas verificacoes nos commits novos de PR e de push na `main`.
- Token M365: fora do repositorio, protegido pelo Windows (DPAPI), em
  `%LOCALAPPDATA%\GPTTutorGenerator\credentials\m365_refresh_token.dpapi`. `GPT_TUTOR_CREDENTIALS_DIR` (absoluto, fora
  do repositorio) troca o diretorio; `GPT_TUTOR_M365_NO_PERSIST=1` desliga a persistencia (login a cada sessao; unico
  modo fora do Windows). O cache antigo `moddle/.m365_token.json` nao e lido nem migrado: apagar manualmente.

## Operational Flow

After launching the app:

1. Create or select a subject.
2. Define the generated repository folder.
3. Import files and links.
4. Process the queue.
5. Review outputs in the generated repository's manual review area when needed.
6. Use Image Curator for extracted images or photos.
7. Build or update the final repository.
8. Use Reprocess Repository to reapply the current architecture to existing repositories.
9. Use Repository Tasks to queue builds, reprocessing, and individual processing.
10. Use Dashboard to monitor operational repository state.
