---
name: agents
description: Project identity, non-negotiables, commands, and scaffold growth instructions
last_updated: 2026-08-06
---

# GPT-Tutor-Generator

Reviewed against `.mex/ROUTER.md` and current scaffold commands on 2026-06-21.

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
- Gemini integration uses `google-genai` (NOT `google-generativeai`). Imports via `from google import genai` and must stay lazy inside method bodies — never at module top level. Anti-patterns to grep: `google.generativeai`, `genai.GenerativeModel`.
- The generated repo's code_curation.json is a generated artifact (not source). Treat it like manifest cache: prune stale entries before reads, write atomically.
- **Arquivamento de concluídos (NÃO-NEGOCIÁVEL):** quando um plano termina de executar e passa 100%
  (gate verde — golden/eval/pytest verdes, sem drift), MOVER os arquivos Markdown concluídos (plano + spec + report associados)
  para a subpasta de concluídos do diretório de origem: `docs/superpowers/plans/Feitos/`,
  `docs/superpowers/specs/Feitos/`, `docs/reports/Feitos/`, `.git/sdd/Feitos/`. Usar `git mv` quando
  trackeado (preserva histórico). A RAIZ desses diretórios só contém trabalho em andamento ou a-fazer.
- **Tracker de pendências (NÃO-NEGOCIÁVEL):** manter `docs/reports/pendencias.md` SEMPRE
  atualizado: ao concluir um item, removê-lo da lista viva e registrá-lo na seção "Concluído"; ao
  descobrir nova pendência, adicioná-la com tag [USER|CODE|DECISION].
- **Fixtures copiam contrato real (NÃO-NEGOCIÁVEL, 2026-08-06):** dado sintético de teste
  reproduz o contrato REAL da fonte (nome/tipo/formato/encoding) com proveniência declarada.
  Regra completa: `context/conventions.md` §Fixtures; dicionário campo-a-campo:
  `context/institutional.md` §Contratos.
- **Fonte única de fatos (dieta MEX 2026-08-06):** estado vivo mora no tracker de pendências
  (nunca duplicar em ROUTER/context); estrutura de código mora no graphify (`graphify update .`
  após mudar código); MEX guarda só intenção, decisões, convenções e contratos externos.

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
- If no pattern exists for this task type, create one and add it to `.mex/patterns/INDEX.md`.
- If a pattern was deviated from or a new gotcha was found, update it.
- If any context file is now outdated, update it surgically.
- Estado vivo (números, gates, pendências) vai para `docs/reports/pendencias.md` — NÃO para o
  ROUTER (que só aponta fontes; dieta 2026-08-06). Se mudou código, rodar `graphify update .`.
- **Living overview:** if the architecture, pipeline, or attribution logic changed, update
  `docs/Overview-Sistema.html` — the single living visual overview of the system (tabs 1–5
  attribution, 6 audit/debts, 7 system report). It must always reflect the current state.

## Navigation

Read `.mex/ROUTER.md` before starting any task.
