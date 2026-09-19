# Handoff — fechamento da rodada de construção do workflow

Data: 2026-09-19. Branch: `docs/35-reconciliar-tracker`. Base: `main`
em `c17e01f`. Entrega ativa: [PR #36](https://github.com/HumbertoCG18/GPT-Tutor-Generator/pull/36).

## Objetivo da próxima sessão

Mesclar o PR #36 após Gate 2 e checks, então auditar gaps antes de construir outra
capacidade. O loop noturno continua como última entrega planejada.

## Estado verificado

- #10/#17: contratos, templates e referências seletivas entregues pelo PR #31.
- #13: gate Python `core` obrigatório, entregue pelo PR #30.
- #18/#19/#22: MCP isolado 10/10; hooks rejeitados; medição real 12/12 executada,
  com 10/12 respostas corretas e 9/12 conformes. Context Mode não foi adotado: registro
  e dados ativos removidos das três CLIs; #22 fechada. Backup recuperável em
  `agent-workflow-lab/private/backups/context-mode-removal-20260919-014312`.
- #16: delta sincronizado com SHA-256
  `acc834ac720c940fb82c072f45e07c82007f2bfc0d627fd28a4902fd8e11d084`; 75 arquivos
  verificados sem divergência; issue fechada com a limitação de o laboratório não ter remote.
- #33: PR #34 mesclado em `c17e01f`; issue fechada. Retomada real comprovada com
  `RETOMADA_OK`, branch/HEAD/status/nonce conferidos e zero escaladas automáticas.
- Limpeza local de plugins desativados: sete instalações Claude, uma Codex e cinco
  registros Gemini/AGY removidos. Backup em
  `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/backups/plugin-off-cleanup-20260919-001529`.
  Cinco plugins sincronizados ainda exigem exclusão na conta Claude.ai: Desktop Commander,
  PDF Viewer, Engineering, Design e `cowork-plugin-management`.
- A branch `feat/motor-atribuicao` e seu estado local pertencem à frente de produto.
  Não transportar seus diffs para esta worktree.

## Gaps na ordem de execução

1. **Fechar o PR #36:** conferir o diff ampliado, aprovar Gate 2, executar checks e mesclar;
   a issue #35 fecha pelo PR.
2. **Excluir cinco plugins sincronizados no Claude.ai:** Desktop Commander, PDF Viewer,
   Engineering, Design e `cowork-plugin-management`; exige ação autenticada na conta.
3. **Manter produto separado:** #11, #12 e #14 seguem válidas, mas não bloqueiam o workflow.
   Tkinter recebe só correção funcional; #12 começa local-first; #14 espera a stack C6.
4. **Construir o loop noturno por último:** abrir issue e piloto isolado no
   `agent-workflow-lab`; só depois integrar às três CLIs.

## Medições sem ação agora

- Fable/Astra: amostra concluída, mas pequena; não sustenta alegação de economia de quota
  ou superioridade geral. Nova rodada só com hipótese nova.
- Context7: piloto encerrado em 12/20 tentativas; as oito restantes não são dívida.
- AGY: contratos inline são o fallback aprovado; registro nativo não é requisito.
- Relatório offline: viewport móvel, impressão e download continuam não testados; validar
  somente antes de depender desses caminhos.

## Contrato mínimo do loop noturno

- worktree descartável por job e allowlist imutável de arquivos/comandos;
- rede negada por padrão, segredos fora do prompt/log e fixture sintética de vazamento;
- budget de tempo, tentativas, custo/contexto e diff; kill switch externo;
- checkpoint verificável e rotação de sessão antes de 100k tokens; compactação não conta
  como checkpoint;
- ledger append-only com estado, HEAD, diff, testes, exit code e motivo de parada;
- nenhum commit, push, PR, merge, deploy ou troca de provider sem os Gates existentes;
- Fable executa; Astra revisa uma vez; AGY só pesquisa corpus público quando necessário;
- falha de verificador, quota, rede ou estado contraditório encerra com handoff, sem retry
  recursivo.

## Retomada operacional

1. Abrir `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-capability-audit`.
2. Consultar `gh pr view 36` e `gh pr checks 36`.
3. Confirmar o diff ampliado e registrar Gate 2 antes de commit/push.
4. Após o merge autorizado separadamente, excluir a worktree e a branch já integradas.
5. Não reinstalar ou repetir o piloto Context Mode; a decisão futura exige correção upstream e issue nova.
