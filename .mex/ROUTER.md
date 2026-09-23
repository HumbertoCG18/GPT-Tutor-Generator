---
name: router
description: Mapa de fontes do GPT Tutor. Carregar apenas a rota pertinente.
---

# Mapa do projeto

Aplicativo desktop Python/Tkinter: materiais acadêmicos para repositórios-tutor Markdown.
Identidade e invariantes: [.mex/AGENTS.md](AGENTS.md).
Workflow compartilhado: [.workflow/README.md](../.workflow/README.md).
Engenharia: [patterns/engenharia-produto.md](patterns/engenharia-produto.md).

## Selecionar domínio

| Tarefa | Estado e fontes |
|---|---|
| Workflow, CLIs, skills, hooks | [.workflow/HANDOFF.md](../.workflow/HANDOFF.md); fonte canônica indicada no README |
| Motor/produto | [tracker](../docs/reports/pendencias.md), somente bloco pertinente; [handoff do motor](../docs/reports/2026-09-17-handoff-regime-cru.md) para essa campanha |
| Agente noturno / fila | Issues #42/#43; conferir worktree e estado próprios antes de ler código ou continuar |
| Estrutura/callers | Graphify explain/path, query com budget; confirmar projeto/frescor, verificar no código |
| Decisões | [context/decisions.md](context/decisions.md), seção pertinente |
| Contratos/fixtures | [context/institutional.md](context/institutional.md) e [context/conventions.md](context/conventions.md) |
| Build/testes/setup | [context/setup.md](context/setup.md), [context/stack.md](context/stack.md), convenções |
| Saída do tutor | [context/repo-output.md](context/repo-output.md) |
| PDF/texto | [context/pdf-pipeline.md](context/pdf-pipeline.md), [context/text-chain.md](context/text-chain.md) |
| Serviços/custos | [context/external-services.md](context/external-services.md) |
| Procedimento recorrente | [patterns/INDEX.md](patterns/INDEX.md), escolher só o aplicável |
| História de navegação/diagnósticos do grafo | [context/navigation-history.md](context/navigation-history.md), somente para investigar decisões antigas |

Não ler todos os destinos. Estado: conferir HEAD/diff e .workflow/local/active-task.md (legado: .workflow-local/)
da tarefa; nunca usar o estado de outra campanha como autorização.
Tracker guarda fatos vivos, handoff continuidade, decisões justificativas; mapa não duplica estado.
Snapshots históricos não comprovam checkout atual. Mem-search só para lacuna não coberta nessas fontes.
Graphify é principal; CBM fallback segue [patterns/codegraph-fallback.md](patterns/codegraph-fallback.md).
