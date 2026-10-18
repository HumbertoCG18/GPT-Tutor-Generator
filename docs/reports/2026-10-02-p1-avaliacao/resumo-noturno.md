# P1: resumo da rodada noturna de 02/10/2026

**Resultado: avaliação INCOMPLETA. Tentativa consumida, sem reinício automático. P1 e A+P1 não têm placar nem aceite. Nenhuma integração ou commit.**

O usuário autorizou a única avaliação congelada do contrato v2 (§5, SHA256 d30980a3347c9866bbe2a11860310e33497d6b26a2330b408294a6600fa2e3d3) e pediu execução noturna. Alethe run-16/job-31, planner -hnmeC89k0tw08T3Dpm9m, thread e7cb213e-05d3-4e18-8834-414d6aadcee9; Claude Opus 5.5/high confirmado pelo status, numa worktree isolada de bf46d51f. Nova revisão não foi chamada; job-30 e seu contador permanecem preservados.

## O que ocorreu e por que não houve medição final

O executor montou P1 e A+P1 com cópias exatas das fontes e iniciou dois replays integrais paralelos. Encerrou os processos antes de gravar as saídas, por estimativa de tempo insuficiente. A telemetria do Alethe registra **232,166 s de duração do job, com limite configurado de 600 s**: não ocorreu timeout de 600 s. A estimativa do executor não demonstrava necessidade de parar naquele momento. `outcome=succeeded` atesta somente a entrega do worker, não a conclusão da avaliação.

Os logs registram P1 até MF/SO/IA/ES2 (última linha: ES2, 35, 137 s), e A+P1 até MF/SO/IA (última linha: IA, 63, 130 s). O relato inicial de apenas MF/SO foi corrigido. Não existem `replay_p1.json`, `replay_ap1.json` ou `consolidado.json`. Portanto, nenhuma decisão nova por ID ou pontuação dos candidatos ficou preservada. O executor declarou que não abriu o gold; o runner coloca o scoring após o replay integral. A identidade dos módulos carregados não ficou preservada em JSON, embora as cópias de fonte tenham hashes conferidos.

Conferência do coordenador: os PIDs informados (47940/33544) já não existiam; produto/teste P1 originais permanecem com os hashes selados. Não foi refeita a medição. Qualquer nova execução exige decisão explícita do usuário, mantendo o contrato e sem confundir interrupção com reprovação do mecanismo.

## Arquivos

Na worktree isolada `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-p1/.alethe/worktrees/job-31`:

| superfície | mudança | finalidade |
|---|---|---|
| `src/builder/timeline/index.py` e `src/builder/routing/file_map.py` | duas cópias exatas do delta já existente; 28894d0a… e 6ad4f70b… | compor P1; nenhuma regra nova |
| `tests/test_p1_frases_compartilhadas.py` | cópia exata, 90746e83… | preservar os 14 testes existentes; não executados nesta rodada |
| `docs/reports/2026-10-02-p1-avaliacao/replay_p1.py` | runner adaptado do replay CRU-05 | liga P1 nas duas passadas e prevê registrar paths/hashes |
| `docs/reports/2026-10-02-p1-avaliacao/consolida.py` | script parcial | consolidação dos resultados; contraste de subunidade A+P1 vs A ainda incompleto; não executado |
| `docs/reports/2026-10-02-p1-avaliacao/braco_ap1/src/` | 131 arquivos copiados | árvore P1 com normalize da cru05 (f5b9581a…); nenhuma edição de regra |
| `docs/reports/2026-10-02-p1-avaliacao/log_p1.txt`, `log_ap1.txt` | dois logs parciais | evidência do avanço anterior ao encerramento |
| `docs/reports/2026-10-02-p1-avaliacao/relatorio-p1-avaliacao.md` | relatório parcial, corrigido pelo coordenador | resultado e limitações; não autoriza retomar |

Na árvore P1 original, o coordenador criou este resumo e `job31-telemetria.json` neste diretório, além de `.workflow/local/active-task.md`. Na principal, atualizou somente o estado da tarefa, o registro de campanhas e o trecho pertinente de `docs/reports/pendencias.md`. O arquivo de configuração já modificado não foi editado.

Registro: MOTOR-01 recebeu janela noite por autorização explícita e voltou a bloqueada após interrupção. A dependência administrativa de MOTOR-00 foi removida desta fase: a referência está selada e preservada; MOTOR-00 continua pronta, com versionamento necessário antes de qualquer limpeza. Sem commit/limpeza nesta rodada. Não foi liberado runtime genérico #42, scheduler ou suspensão.

## Testes e condições

| evidência | número | origem nesta rodada |
|---|---|---|
| testes do contrato P1 | 14/14 verdes | herdado do relatório de implementação; não reexecutado |
| mutação contando chaves | detectada pelo teste novo | herdado; não reexecutado |
| suíte P1 | 2461 aprovados, 4 pulos, mesmas 2 falhas da base | herdado; não reexecutado |
| replay com P1 desligado | 350/350 idênticos à base | evidência preservada; não reexecutada |
| novos testes criados/executados | 0/0 | nenhum |
| novos resultados integrais P1/A+P1 | 0/2 | ambos interrompidos |
| A+P1 desligado vs A e suíte combinada | sem evidência nesta rodada | pendentes |
| bloco/unidade invariantes com P1 ligado | sem evidência final | nenhum JSON integral dos candidatos |

## Placar e posição da campanha

Base e A abaixo são controles anteriores, consultados no disco e conferidos por hash nesta sessão; não são resultados novos desta noite. Cada controle preserva 350 IDs, com denominadores de pontuação distintos por eixo.

| braço | bloco | unidade | subunidade primária | aceite |
|---|---:|---:|---:|---|
| base (e024d396…) | 223/237 | 249/284 | 86/251 | referência vigente |
| A: só acentos (0216122c…) | 223/237 | 249/284 | 85/251 | reprovação anterior: −1 primária |
| P1 | sem resultado | sem resultado | sem resultado | SEM EVIDÊNCIA |
| A+P1 | sem resultado | sem resultado | sem resultado | SEM EVIDÊNCIA |

A campanha MOTOR permanece **2/10 tarefas concluídas = 20%**; isso é progresso do catálogo, não porcentagem de acerto nem integração aprovada. MOTOR-02 e MOTOR-03 estão encerradas com resultado reprovado/nulo; MOTOR-01 fica bloqueada pela tentativa interrompida. MOTOR-00 e MOTOR-09 seguem prontas; demais estados preservados.

Referência vigente: bloco **94,1%**, unidade **87,7%**, subunidade primária **34,3%**. Para superar 90% mantendo esses denominadores, são necessários pelo menos 214/237, 256/284 e 226/251: bloco já ultrapassa; faltam **+7** na unidade e **+140** na primária. São contas sobre a referência anterior, não ganhos medidos nesta rodada.

Desenvolvimento permanece MF/SO/IA/ES2/TCC; CG/FR são descritivos, com exposição anterior declarada. Não existe teste independente novo. Nenhum resultado dos sete cursos demonstraria generalização independente. Não há novo placar estratificado porque os candidatos não terminaram.

Próximo passo depende de decisão do usuário sobre a tentativa interrompida. Não há retry automático, alteração de divisor/limiar/escopo, integração ou commit autorizados.
