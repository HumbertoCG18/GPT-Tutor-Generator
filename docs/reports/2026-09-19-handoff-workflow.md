# Handoff — fechamento da rodada de construção do workflow

Data: 2026-09-19. Branch: `codex/audit-html-refresh-33`. Base: `origin/main`
em `5838569`. Issue ativa: [#33](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/33).

## Objetivo da próxima sessão

Fechar a rodada atual de governança antes de construir outra capacidade. O loop noturno
é a última entrega planejada: sua severidade permanece P0, mas sua implementação começa
somente depois dos gaps 1–4 abaixo.

## Estado verificado

- #10/#17: contratos, templates e referências seletivas entregues pelo PR #31.
- #13: gate Python `core` obrigatório, entregue pelo PR #30.
- #18/#19/#22: MCP isolado 10/10; hooks rejeitados; medição real 12/12 executada,
  com 10/12 respostas corretas e 9/12 conformes. Claude permanece manual/restrito;
  Codex e AGY foram removidos desse caminho. PR #32 mesclado; #22 continua aberta.
- #33: HTML/JSON/Markdown regenerados e validados nesta worktree. A inspeção visual
  via HTTP local confirmou as cinco abas, contagens principais e layout desktop sem quebra.
  O diff continua sem commit por Gate 2.
- Limpeza local de plugins desativados: sete instalações Claude, uma Codex e cinco
  registros Gemini/AGY removidos. Backup em
  `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/backups/plugin-off-cleanup-20260919-001529`.
  Cinco plugins sincronizados ainda exigem exclusão na conta Claude.ai: Desktop Commander,
  PDF Viewer, Engineering, Design e `cowork-plugin-management`.
- A branch `feat/motor-atribuicao` e seu estado local pertencem à frente de produto.
  Não transportar seus diffs para esta worktree.

## Gaps na ordem de execução

1. **Fechar #33:** validar o HTML via servidor local, revisar o diff fixado, obter Gate 2,
   commitar, abrir PR com `Closes #33`, aguardar `core` e mesclar após autorização.
2. **Provar retomada real:** na próxima interrupção real, retomar por `active-task.md`
   conferindo branch/HEAD/diff/testes e sem repetir chamada Astra.
3. **Encerrar #16/#22:** registrar em #16 a limitação do laboratório sem remote; em #22,
   separar defeitos Codex ainda acionáveis da medição já concluída e fechar a rodada sem
   repetir um piloto genérico.
4. **Manter produto separado:** #11, #12 e #14 seguem válidas, mas não bloqueiam o workflow.
   Tkinter recebe só correção funcional; #12 começa local-first; #14 espera a stack C6.
5. **Construir o loop noturno por último:** abrir issue e piloto isolado no
   `agent-workflow-lab`; só depois integrar às três CLIs.

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

1. Abrir `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-audit-html-33`.
2. Conferir `git status --short --branch` e `git diff --cached --check`.
3. Regenerar pela fonte privada em
   `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/private/skills-audit-20260917`.
4. Rodar `validate_report.py` e `validate_refresh.py`.
5. Servir a raiz da worktree por HTTP e inspecionar o painel.
6. Apresentar o diff fixado para Gate 2. Não commitar antes dele.
