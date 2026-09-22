# Workflow comum das três CLIs

Fonte canônica: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/workflow.md.
Ler uma vez por sessão; reler somente se mudar ou faltar no contexto após compactação.
Snapshots locais são fallback quando a fonte estiver indisponível; registrar a limitação.

## Núcleo obrigatório

- Claude Code é o terminal principal e implementa/testa pelo nível definido pelo investigador em references/routing.md. Codex planeja/orquestra tarefas complexas e Astra revisa diffs. Antigravity (AGY) pesquisa, audita em escopo delimitado e escreve achados/documentação. Uma tarefa tem um coordenador e cada arquivo um escritor; papéis não autorizam trocar modelo silenciosamente.
- Tarefa pequena fica no executor atual. Decomposição complexa pode ir ao Codex, com brief delimitado; planejamento não consome nem substitui a revisão independente. Não abrir chamada apenas para ocupar as três assinaturas.
- Gate 1: plano aprovado antes de implementação nova. Gate 2: diff confirmado antes de commit. Autorização já dada no escopo persiste; continuar não autoriza commit, merge/deploy nem outra revisão.
- Código relevante recebe uma revisão Astra read-only, sem recursão/retry; o executor selecionado corrige. Registrar a tentativa antes da chamada; falha/timeout/quota também a consomem. Documentação simples recebe conferência local.
- Persistir tarefa/escopo, branch/HEAD, Gates, contador e chamada em .workflow/local/active-task.md (legado: .workflow-local/) antes de delegar. Só o coordenador atualiza esse estado; tracker/handoff guarda resultados e pendências. Não reabrir tarefa concluída nem zerar contador.
- Quota esgotada: salvar estado e aguardar orientação; sem troca silenciosa de provider. Gate técnico indisponível deve ser declarado. Configuração/documentação não prova execução.
- Issue antes de mudança; branch por escopo, PR relacionado e verificações proporcionais. Preservar alterações de outras sessões. Conferir artefato/testes, nunca concluir só pelo exit code.
- Ler apenas fontes da tarefa/fase; não repetir conteúdo inalterado. Resultados pequenos podem ser agrupados; documento grande fica isolado e, se necessário, em blocos consecutivos até EOF. Meta de saída por ferramenta: 2.000 tokens, com exceção explícita quando necessária.
- Não embutir segredos, históricos completos ou catálogos no brief. Logs completos ficam locais; retornar resultado/evidência decisiva.

## Rotas obrigatórias por ação

Ler a referência da ação antes de executá-la; não carregar a tabela inteira.

| Ação | Fonte |
|---|---|
| Classificar tarefa e escolher responsável | [Roteamento por tarefa](references/routing.md) |
| Implementar mudança, abrir issue/PR ou preparar release | [Issues, PRs e releases](references/delivery.md) |
| Chamar revisor independente | [Executor selecionado e revisor Astra](references/review.md) + delegação |
| Delegar implementação, planejamento, auditoria ou pesquisa | [Delegação com contexto delimitado](references/delegation.md) |
| Retomar tarefa/chamada interrompida | [Retomada e limites](references/resume.md) |
| Adotar/remover ferramenta, plugin ou skill | [Descoberta, adoção e remoção de capacidades](references/capabilities.md) |
| Usar ferramentas compartilhadas, ECC, Graphify/CBM ou RTK | [Ferramentas locais](references/tooling.md) |
| Rodar trabalhadores simultâneos | [Enxame experimental](references/parallel.md) |
| Usar Context7 ou saída estruturada AGY | [Context7 e segredos](references/services.md) |
| Consultar, selecionar, reservar ou atualizar campanhas | [Fila de campanhas](references/campaigns.md) |

## Estado da automação

Esta política governa a sessão ativa; não instala hooks, daemon ou scheduler.
Antes de afirmar automação, conferir configuração e prova de execução na tarefa correspondente.
Night-agent e fila de campanhas são acompanhados no estado local do projeto (tracker e issues ali indicadas); usar seus estados próprios.
A noite deve consumir os mesmos contratos e IDs, respeitando preflight e capacidades efetivamente disponíveis.
