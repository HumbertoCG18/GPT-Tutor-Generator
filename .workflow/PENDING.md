# Pendências do workflow

- [USER] Excluir na conta Claude.ai os cinco plugins sincronizados já desativados; a limpeza local não consegue removê-los.
- [CODE] Mesclar o PR #36 após Gate 2 e checks; ele registra #33 fechada, retomada comprovada e #16/#22 encerradas.
- [LATER] Construir o loop noturno por último, em piloto isolado no `agent-workflow-lab`, com contenção externa e rotação antes de 100k tokens.

Comparação Fable/Astra concluída: ambos 23/23 no parser e 12/12 no roteamento, sem retries.
Relatório: ../docs/reports/Feitos/workflow-medicao-fable-astra_16-09.md. Amostra pequena,
contextos distintos; não comprova economia de quota ou superioridade de Astra na revisão.
Fable executa; Astra revisa por preferência aprovada, uma chamada automática por tarefa
relevante. Fable corrige os achados. Nenhuma troca automática de executor por quota.

AGY usa contratos inline; registro de agentes nativos não é requisito nem medição pendente.
Context7 autenticado nas três CLIs; piloto encerrado em 12/20 tentativas, sem consumir as oito
restantes sem caso real.
Context Mode não adotado: removido das três CLIs; #22 fechada. Dados ativos preservados em backup recuperável.
