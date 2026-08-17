---
name: router
description: Session bootstrap. Read this before any task. Points to the single source of truth for each kind of fact.
last_updated: 2026-08-14
---

# ROUTER.md - Session Bootstrap

Read this file before starting any task.

---

## Current Project State

GPT-Tutor-Generator: app desktop Python/Tkinter que converte materiais acadêmicos (PDF,
links, código, imagens) em repositórios-tutor Markdown por matéria (Claude/GPT/Gemini),
com atribuição arquivo→bloco→unidade dirigida por sinais Moodle/SARC/plano de ensino.

**Este arquivo NÃO duplica estado.** Cada tipo de fato mora em UM lugar:

| Fato | Fonte única |
|---|---|
| Estado vivo, pendências, dívidas, números de gate | `docs/reports/pendencias.md` (tracker, sempre atualizado) |
| O que a última sessão fez e a fila decidida | handoff mais recente em `docs/reports/` |
| Estrutura do código (quem chama quem, onde vive) | `graphify query "<pergunta>"` / `graphify-out/` |
| Por que cada escolha existe | `context/decisions.md` |
| Contratos de dados reais (Moodle/SARC/manifest/índices) | `context/institutional.md` §Contratos |
| Como escrever/verificar código e fixtures | `context/conventions.md` |
| Saída gerada (formato do repo-tutor) | `context/repo-output.md` |
| Pipeline de PDF (backends, falhas conhecidas) | `context/pdf-pipeline.md` |
| Setup/stack/manifest | `context/setup.md`, `context/stack.md` |

Estado atual (branch, números de suite, fases, rollouts, foco da campanha): SEMPRE no
tracker `docs/reports/pendencias.md` + handoff mais recente em `docs/reports/`. Este
arquivo não carrega snapshot — snapshot aqui envelhece e mente.

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `graphify query`/`graphify explain` (estrutura) + `context/decisions.md` (intenção) |
| Understanding the faculty/source platforms (Moodle, SARC, Plano de Ensino) | `context/institutional.md` |
| Writing tests or fixtures with third-party data | `context/institutional.md` §Contratos + `context/conventions.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| PDF processing, backends, conversion failures | `context/pdf-pipeline.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.
