# Workflow dos coding agents — índice histórico

Índice criado em 2026-10-08 na limpeza de Markdown (#100). Lista os registros da época em que o
workflow vivia neste repositório (15–22/09/2026). Não é estado vivo nem norma: a operação atual está
no laboratório (`agent-workflow-lab`: `workflow.md`, `references/routing.md`,
`references/campaigns.md`, `bin/campanhas.py`, `hooks/`) e no snapshot local `.workflow/`. Os
documentos abaixo foram movidos sem alteração de conteúdo além de caminhos.

## Implantação e configuração (15–16/09)

- [Implantação do workflow comum](workflow-implantacao_15-09.md) — 15/09.
- [Inventário e proposta AGY](workflow-inventario-agy_16-09.md) — 16/09.
- [Validação dos papéis AGY](workflow-validacao-agy_16-09.md) — 16/09.
- [Piloto Context7](workflow-context7-piloto_16-09.md) — 16/09.
- [Piloto Fable × Astra](workflow-medicao-fable-astra_16-09.md) — 16/09.
- [Fechamento da configuração](workflow-configuracao-fechamento_16-09.md) — 16/09.
- [Benchmark Graphify × codebase-memory-mcp](benchmark-codegraph_15-09.md) e
  [Graphify primeiro, CBM como fallback](codegraph-fallback_15-09.md) — 15/09.

## Auditorias, pilotos e medições (17–19/09)

- [Auditoria de delegação e leituras](2026-09-17-auditoria-delegacao-leituras.md) — 17/09.
- [Auditoria visual de skills e workflows](2026-09-17-auditoria-skills-workflows.md), com o
  [painel](2026-09-17-auditoria-skills-workflows.html) e os
  [dados](2026-09-17-auditoria-skills-workflows.json) — 17/09, atualizada em 19/09.
- [Handoff do orçamento de skills](2026-09-17-handoff-skills-budget.md) — 17/09.
- [Auditoria de uso de capacidades nas três CLIs](2026-09-18-auditoria-uso-capacidades.md) — 18/09 (#23).
- [Context Mode: medição real](2026-09-18-context-mode-real-measurement.md) — 18/09 (#22).
- [Piloto Context Mode por MCP isolado](2026-09-18-piloto-context-mode-mcp.md) — 18/09 (#18).
- [Medição das issues abertas de workflow e produto](2026-09-18-gaps-issues-abertas.md) — 18/09.
- [Handoff do fechamento da rodada de construção](2026-09-19-handoff-workflow.md) — 19/09.

## Consolidação e organização (20–22/09, #44)

- [Consolidação do contexto e papéis das CLIs](2026-09-20-contexto-workflow-44.md) — 20/09.
- [Medição AGY e fila de campanhas](2026-09-21-medicao-agy-campanhas.md) — 21/09.
- [Modelos, níveis de tarefa/campanha e diagnóstico noturno](2026-09-21-modelos-niveis-workflow.md) — 21/09.
- [Organização do workflow: piloto de versionamento](2026-09-22-organizacao-workflow-piloto-44.md) — 22/09.
- [Auditoria dos diretórios dos coding agents](2026-09-22-auditoria-diretorios-coding-agents.md) — 22/09.

## O que ficou fora do arquivo, e por quê

- [`../Feitos/workflow-validacao-integrada_16-09.md`](../Feitos/workflow-validacao-integrada_16-09.md):
  o laboratório o cita em `agent-workflow-lab/evals/workflow-20260916.md:17`. Ele se move junto
  com a atualização desse consumidor.
- [`../2026-09-18-piloto-hooks-context-mode.md`](../2026-09-18-piloto-hooks-context-mode.md):
  `_context-mode-hooks/validate_result.py` lê esse caminho.
- [`../workflow-handoff-sessao-nova.md`](../workflow-handoff-sessao-nova.md) e
  `.workflow/pendencias_workflow.md`: ainda guardam pendências sem encerramento verificado.
- Pastas com código e dados (`_workflow-audit-2026-09-15/`, `_context-mode-pilot/`,
  `_context-mode-hooks/`, `_capability-usage-audit/`): ficam no lugar.
