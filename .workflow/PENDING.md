# Pendências do workflow

- [USER] Excluir na conta Claude.ai os cinco plugins sincronizados já desativados; a limpeza local não consegue removê-los.
- [CODE] Fechar #33 e reconciliar #16/#22 antes de abrir o loop noturno.
- [CODE] Na próxima interrupção real, verificar a retomada pelo estado salvo sem repetir chamada Astra. As revisões de #31/#32 provam revisão read-only, mas não a retomada fim a fim.
- [LATER] Construir o loop noturno por último, em piloto isolado no `agent-workflow-lab`, com contenção externa e rotação antes de 100k tokens.

Comparação Fable/Astra concluída: ambos 23/23 no parser e 12/12 no roteamento, sem retries.
Relatório: ../docs/reports/Feitos/workflow-medicao-fable-astra_16-09.md. Amostra pequena,
contextos distintos; não comprova economia de quota ou superioridade de Astra na revisão.
Fable executa; Astra revisa por preferência aprovada, uma chamada automática por tarefa
relevante. Fable corrige os achados. Nenhuma troca automática de executor por quota.

AGY usa contratos inline; registro de agentes nativos permanece não comprovado.
Context7 autenticado nas três CLIs; piloto conservador 12/20 tentativas, sem novas consultas.
