# Pendências do workflow

- [USER] Confirmar conversa nova no Alethe sem aviso de orçamento de skills; sessão direta já aceita.
- [CODE] Na próxima tarefa real, verificar uma revisão Astra read-only e a retomada pelo estado salvo. Classificar cenários no piloto não prova delegação em execução.
- [DESIGN] Piloto de continuação noturna nas três CLIs. Gatilho explícito equivalente a
  "vou dormir, pode continuar desenvolvendo" deve iniciar um controlador externo em
  worktree isolado; não ampliar permissões da sessão nem trocar provider automaticamente.
  Exigir contrato aprovado, paths/comandos permitidos, bloqueio de rede/push/merge/deploy,
  snapshot/hash de arquivos protegidos, limites de tempo/tentativas/diff, validação externa,
  ledger append-only, kill switch e Gate 2 humano. Rotacionar a sessão antes de 100k tokens:
  persistir estado/handoff compacto, encerrar a sessão antiga e iniciar outra; autocompact
  nativo é otimização, não fonte de continuidade. Avaliar ZeroShot como referência/benchmark;
  não instalar enquanto não suportar AGY/Antigravity e a política de uma revisão Astra.
  Roteamento aprovado: Opus desenvolve e testa a infraestrutura do loop; Fable permanece
  reservado ao desenvolvimento do GPT-Tutor-Generator. O loop não troca modelos por quota.

Comparação Fable/Astra concluída: ambos 23/23 no parser e 12/12 no roteamento, sem retries.
Relatório: ../docs/reports/Feitos/workflow-medicao-fable-astra_16-09.md. Amostra pequena,
contextos distintos; não comprova economia de quota ou superioridade de Astra na revisão.
Fable executa; Astra revisa por preferência aprovada, uma chamada automática por tarefa
relevante. Fable corrige os achados. Nenhuma troca automática de executor por quota.

AGY usa contratos inline; registro de agentes nativos permanece não comprovado.
Context7 autenticado nas três CLIs; piloto conservador 12/20 tentativas, sem novas consultas.
