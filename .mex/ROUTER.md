---
name: router
description: Session bootstrap. Read this before any task. Points to the single source of truth for each kind of fact.
last_updated: 2026-09-08
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
| O que a última sessão fez e a fila decidida | **`docs/reports/2026-09-14-handoff-codex-regime-cru.md`** (ponto de entrada vivo, autocontido; `2026-09-12-handoff-regime-cru.md` é a referência detalhada por §; o de 11/09 é histórico) |
| O plano a revisar antes de executar | `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` |
| Estrutura do código (quem chama quem, onde vive) | `graphify explain "<símbolo>"` ou `graphify path "A" "B"`; `query` aberto só com `--budget` |
| Segunda opinião de diff (Codex) ou leitura de corpus (agy) | `patterns/delegar-codex-agy.md` |
| Por que cada escolha existe | `context/decisions.md` |
| Contratos de dados reais (Moodle/SARC/manifest/índices) | `context/institutional.md` §Contratos |
| Como escrever/verificar código e fixtures | `context/conventions.md` |
| Saída gerada (formato do repo-tutor) | `context/repo-output.md` |
| Pipeline de PDF (backends, falhas conhecidas) | `context/pdf-pipeline.md` |
| Cadeia do TEXTO (staging → Curator Studio → o que o motor pontua; descrições de imagem) | `context/text-chain.md` |
| Retrato verificado do sistema (o que existe, o que está inerte, o que não existe, código morto) | `context/audit-2026-09-07.md` (inclui os achados de 08/09: circularidade do gold, calibração da confiança, cobertura da régua) |
| Serviço externo, custo, API paga, backend de extração, descrição de imagem | `context/external-services.md` |
| Histórico de arquitetura, roadmap e changelogs (retrato de 03/09, parcialmente vencido) | `docs/Overview-Sistema.html` |
| Inventário do motor de atribuição (quem decide cada eixo, o que já existe) | `docs/reports/_harness-2026-09-04/c1-3/inventario_motor_2026-09-07.md` |
| Setup/stack/manifest | `context/setup.md`, `context/stack.md` |

Estado atual (branch, números de suite, fases, rollouts, foco da campanha): SEMPRE no
tracker `docs/reports/pendencias.md` + handoff mais recente em `docs/reports/`. Este
arquivo não carrega snapshot — snapshot aqui envelhece e mente.

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `graphify explain` (estrutura) + `context/decisions.md` (intenção) |
| Understanding the faculty/source platforms (Moodle, SARC, Plano de Ensino) | `context/institutional.md` |
| Writing tests or fixtures with third-party data | `context/institutional.md` §Contratos + `context/conventions.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| PDF processing, backends, conversion failures | `context/pdf-pipeline.md` |
| Curadoria de markdown, aprovação, staging, descrição de imagem | `context/text-chain.md` |
| "Isso já existe no sistema?" antes de construir/refatorar | `context/audit-2026-09-07.md` (retrato verificado) — só então `docs/Overview-Sistema.html` (histórico) |
| Custo, API paga, trocar backend (Marker/MinerU/docling), provedor de descrição | `context/external-services.md` |
| Mexer no motor de atribuição (bloco/unidade/subunidade) | `docs/reports/_harness-2026-09-04/c1-3/inventario_motor_2026-09-07.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |
| Sessão passada que não está no tracker nem no handoff | `mem-search` (quarta fonte, não a primeira) |

## Harness Ownership

Uma fase, um dono. Configurado no settings.json pessoal do Claude Code, via skillOverrides.
Este arquivo roteia; o settings.json é a fonte do que está ligado.

| Fase | Dono |
|---|---|
| Critérios de aceite antes de codar | `ecc:intent-driven-development` (substituiu `superpowers:brainstorming`) |
| Capacidade que ainda não existe | `ecc:orch-add-feature` |
| Estrutura melhora, comportamento não muda | `ecc:orch-refine-code` |
| Comportamento quebrado ou errado | `ecc:orch-fix-defect` (primeira jogada: teste de regressão vermelho) |
| Medição repetida em N cursos ou N tutores | `ecc:parallel-execution-optimizer` |
| Implementação TDD dentro dos `orch-*` | agent `ecc:tdd-guide` (dono único da fase 4) |
| Review | agent `ecc:python-reviewer` + `/code-review` nativo |
| Governança dos relatórios em `docs/reports/` | `ecc:living-docs-governance` |
| Contratos e fixtures | `ecc:contract-first` |

Os `orch-*` param em Gate 1 (plano aprovado antes de escrever código) e Gate 2
(diff confirmado antes do commit). Entre os dois o pipeline corre sem parar.
Os gates são instrução dentro do SKILL.md, não hook: nada no arquivo de hooks do ECC
os impõe. O risco é pular o gate, não travar nele.

Deriva de acurácia agregada não é defeito reproduzível e não vai por
`orch-fix-defect`. Vai por harness de medição (`ecc:eval-harness`).

MCP ativo no Claude Code: `context7` e, desde 10/09, `graphify` (`.mcp.json` do
projeto, gitignored; servidor `python -m graphify.serve graph.json`). `code-review-graph`
foi removido em 08/09 por uso zero medido em 15.840 chamadas de ferramenta registradas.
No agy o mesmo servidor entrou via `agy mcp add`. No Codex está `enabled = false` no
config.toml global do Codex (pasta ~/.codex): o Alethe reescreve a entrada do projeto com um comando
que não existe; a skill `$graphify-windows` cobre. Detalhes em
`patterns/debug-graphify-mcp.md`. Estrutura de código continua no `graphify`, conforme
a tabela de fonte única acima.

Busca estrutural, ordem medida em 08/09: `Grep` para localizar o símbolo, então
`graphify explain` ou `graphify path`, e `Read` com offset só no que sobrar.
`graphify explain` custou 379 tokens contra 58.838 de ler `src/ui/dialogs.py`
inteiro. `graphify query` aberto truncou em 64 de 607 nós e avisou que a resposta
podia estar entre os 543 cortados: é indício, não resultado. O grafo indexa
`docs/` junto com o código, então pergunta de código volta com ruído de relatório.
`claude-mem:smart-explore` fica desligada: o tree-sitter dela falha em Python e
JavaScript nesta instalação, com as gramáticas presentes em disco.

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.
