# Workflow comum das três CLIs

Fonte canônica: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/workflow.md.
Ler uma vez por sessão; reler somente se mudar ou faltar no contexto após compactação.
Snapshots locais são fallback quando a fonte estiver indisponível; registrar a limitação.

## Núcleo obrigatório

- Claude Code é o terminal principal e implementa/testa pelo nível definido pelo investigador em references/routing.md. Codex planeja/orquestra tarefas complexas, revisa, audita, busca código, escreve documentação/pesquisa e implementa T1/T2 quando a cota do Claude aperta. Antigravity (AGY) entra só por escolha explícita. Uma tarefa tem um coordenador e cada arquivo um escritor; papéis não autorizam trocar modelo silenciosamente.
- Tarefa pequena fica no executor atual. Decomposição complexa pode ir ao Codex, com brief delimitado; planejamento não consome nem substitui a revisão independente. Não abrir chamada apenas para ocupar as três assinaturas.
- Gate 1: plano aprovado antes de implementação nova. Gate 2: diff confirmado antes de commit. Autorização já dada no escopo persiste; continuar não autoriza commit, merge/deploy nem outra revisão.
- Grilling (T2/T3, antes do plano): todas as perguntas abertas numa única mensagem, cada uma com resposta sugerida; o plano só sai depois das respostas. T0/T1 não passam por isso.
- Medição de planos (T2/T3): cada versão do plano apresentada ao Gate 1 conta; cada versão reprovada (dono nega ou pede novo plano) vira uma linha em `.workflow/local/gates.jsonl` do checkout principal (`python bin/gates.py gate1-reprovado --tarefa ID --motivo "…" [--grilling]`). O Gate 2 do dono também: `bin/gates.py gate2 --tarefa ID --aprovador dono --citacao "texto literal" [--issue N --pr N]`. O Gate 2 de merge é gravado a partir do cartão (`gates.py cartao --pr N`), depois do push: `gate2 --pr N --sha X`; linha gravada antes do commit prende o head velho e `verificar --pr` a recusa. Retenção: até a campanha EFICIENCIA fechar. Métrica: reprovadas ÷ apresentadas, antes e depois da regra. Sem baseline medido ainda.
- Código relevante recebe uma revisão read-only do revisor, sem recursão/retry; o executor selecionado corrige. Registrar a tentativa antes da chamada; falha/timeout/quota também a consomem. Documentação simples recebe conferência local.
- Persistir tarefa/escopo, branch/HEAD, Gates, contador e chamada em .workflow/local/active-task.md (legado: .workflow-local/) antes de delegar. Só o coordenador atualiza esse estado; tracker/handoff guarda resultados e pendências. Não reabrir tarefa concluída nem zerar contador.
- Quota esgotada: salvar estado e aguardar orientação; sem troca silenciosa de provider; a reserva de routing.md › Camadas é registrada no estado. Gate técnico indisponível deve ser declarado. Arquivo presente, configuração concluída e execução observada são provas distintas; check não rodado fica "não executado", nunca aprovado.
- Issue antes de mudança; branch por escopo, PR relacionado e verificações proporcionais. Preservar alterações de outras sessões. Conferir artefato/testes, nunca concluir só pelo exit code.
- Ler apenas fontes da tarefa/fase; não repetir conteúdo inalterado. Resultados pequenos podem ser agrupados; documento grande fica isolado e, se necessário, em blocos consecutivos até EOF. Meta de saída por ferramenta: 2.000 tokens, com exceção explícita quando necessária.
- Não embutir segredos, históricos completos ou catálogos no brief. Logs completos ficam locais; retornar resultado/evidência decisiva.

## Rotas obrigatórias por ação

Ler a referência da ação antes de executá-la; não carregar a tabela inteira.

| Ação | Fonte |
|---|---|
| Classificar tarefa e escolher responsável | [Roteamento por tarefa](references/routing.md) |
| Implementar mudança, abrir issue/PR ou preparar release | [Issues, PRs e releases](references/delivery.md) |
| Chamar revisor independente | [Executor selecionado e revisor](references/review.md) + delegação |
| Revisar segurança (só leitura) | [Revisão de segurança](references/seguranca.md) + review.md |
| Delegar implementação, planejamento, auditoria ou pesquisa | [Delegação com contexto delimitado](references/delegation.md) |
| Retomar tarefa/chamada interrompida | [Retomada e limites](references/resume.md) |
| Adotar/remover ferramenta, plugin ou skill | [Descoberta, adoção e remoção de capacidades](references/capabilities.md) |
| Propor regra, comando ou skill a partir de padrões repetidos | [Aprendizado](references/learning.md) |
| Usar ferramentas compartilhadas, ECC, Graphify ou RTK | [Ferramentas locais](references/tooling.md) |
| Rodar trabalhadores simultâneos | [Enxame experimental](references/parallel.md) |
| Usar Context7 ou saída estruturada AGY | [Context7 e segredos](references/services.md) |
| Consultar, selecionar, reservar ou atualizar campanhas | [Fila de campanhas](references/campaigns.md) |
| Coordenar trabalho noturno | [Agente noturno](references/noite.md) |

## Estado da automação

Esta política governa a sessão ativa; não instala daemon nem scheduler; hooks só pelo manifesto `hooks/registration.json`, conferido pelo `verify.py`.
Antes de afirmar automação, conferir configuração e prova de execução na tarefa correspondente.
Night-agent e fila de campanhas são acompanhados no estado local do projeto (tracker e issues ali indicadas); usar seus estados próprios.
A noite deve consumir os mesmos contratos e IDs, respeitando preflight e capacidades efetivamente disponíveis.
