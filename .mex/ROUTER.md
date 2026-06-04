---
name: router
description: Session bootstrap. Read this before any task. Contains project state, routing table, and behavioural contract.
last_updated: 2026-06-03
---

# ROUTER.md - Session Bootstrap

Read this file before starting any task.

---

## Current Project State

### Working

- Python desktop app with Tkinter UI, launched through `app.py`.
- Manifest is `pyproject.toml` with package name `academic-tutor-repo-builder` and version `3.0.0`.
- Academic-material import flow supports files and links.
- Processing flow handles PDFs, links, images, and code.
- Problematic processing outputs are reviewed through the generated repository's manual review area.
- Image Curator supports images extracted from PDFs and imported photos.
- Repository builder consolidates content into Markdown.
- Generated tutor artifacts target Claude, GPT, and Gemini.
- Repository task queue supports builds, reprocessing, and individual material processing.
- Queue state persists between app sessions.
- Dashboard monitors operational repository state.
- Reprocess Repository reapplies the current architecture to existing generated repositories.
- Test runner is `pytest`; brief lists 28 files under `tests/`.
- Auto-tags de unidade/subunidade/bloco geradas em `resolve_unit_block_tags()`:
  tags `unit:`, `subunit:`, `bloco:` persistidas em `auto_tags` do manifest após
  cada regeneração pedagógica.
- Sinal DD.MM: arquivo `12.03 Processos.pdf` recebe boost +0.30 no bloco do
  cronograma correspondente em `score_entry_against_timeline_block()`.
- Code summarization via Gemini API (`gemini-2.5-flash`): bundle each code entry, persist summary + concept-based timeline block assignment in the generated repo's course/code_curation.json. Lazy: without `gemini_api_key` in config the pipeline is a no-op.
- Generated artifacts add course/CODE_HEALTH.md (coverage report) and course/CRONOGRAMA_DETALHADO.md (block-by-block render) to the generated repo.
- Harness de avaliacao de atribuicao bloco em `scripts/eval_assignments.py`:
  roda o gold set `tests/fixtures/eval/assignments_gold.json` pelo scorer real
  (resolve_unit_block_tags) e reporta acuracia/confusao/calibracao de band.
  Gate de regressao em `tests/test_eval_assignments.py` (baseline no fixture).
- Sinal de sequencia (ordinal de aula) em `src/builder/routing/sequence.py`:
  "Aula 03" recebe boost de desempate `SEQUENCE_BOOST=0.20` no 3o bloco
  `kind=class` (numerado por `annotate_class_ordinals`), somado em
  `score_entry_against_timeline_block`. So marcadores `aula`/`encontro`.
- Referencias como contexto do tutor (`src/builder/core/reference_*.py`):
  entries `category in {referencias, bibliografia}` buscam conteudo leve sem
  clone (README via API GitHub / texto de pagina via `url_markdown`), resumo
  Gemini lazy (`ReferenceSummary`), e mapeamento determinístico a
  unidade/topico (`assign_concepts_to_unit`). Surfaceado na BIBLIOGRAPHY.md
  (resumo + mapa de relevancia). Cache por hash em `references_curation.json`.
  Wiring em `build_workflow._run_auto_code_summarization` (referencias mapeiam
  mesmo sem chave Gemini; reload do manifest pos-enriquecimento).

### Not Declared In Brief

- Runtime dependencies are not declared in the manifest brief.
- Development dependencies are not declared in the manifest brief.
- Project scripts are not declared in the manifest brief.
- Build tool, linter, formatter, and package manager are not declared in the brief.
- Exact Datalab API/package version is not declared in the brief.
- Exact Ollama model/version is not declared in the brief.

### Current Design Focus

- ENTREGUE: Referencias como contexto base do tutor (8 tasks TDD + 2 fixes de
  wiring). Spec `docs/.../2026-06-04-referencias-contexto-tutor-design.md`,
  plano `docs/.../plans/2026-06-04-referencias-contexto-tutor.md`. Resolve
  "tutor so tem link/titulo da referencia". 841 testes verdes.
- Itens PARADOS (retomar): ver `docs/superpowers/BACKLOG.md` — verbosidade do
  manifest (`to_dict` serializa todos os defaults), #3 decay de data, #4 piso
  de band, Horario, conserto do clone github, token github, referencias
  Approach C, harness de referencias, medicao de correcao com ground-truth.

> Historico: o redesign do sistema de tags (unit/subunit/bloco) e a precisao de
> atribuicao bloco/unidade ja foram implementados (auto_tags, bandas de
> confianca Fase 1-4, harness de avaliacao, sinal de sequencia). Foco migrou de
> "precisao de bloco" (resolvida, ~98% band alta nos repos reais) para
> "referencias usaveis pelo tutor".

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `context/architecture.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.
