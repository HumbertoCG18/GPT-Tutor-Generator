# Plano para o Gate — integração e ativação conjunta de acentos + P1

02/10/2026. Candidato escolhido pelo usuário: **A+P1**. Escolha registrada; **Gate de execução e commit não concedidos**. Este documento prepara o próximo Gate, sem editar produto ou repetir a avaliação congelada.

## Evidência e limite

Relatório final, consolidado e verificação do coordenador: **87/251 primária, +1/0 contra base; 223/237 bloco e 249/284 unidade invariantes; nenhum curso regredindo**. Suíte comparável anterior: **2469 aprovados, 4 pulados, 1 falha preexistente FR**, todos os 2467 IDs anteriores presentes e 7 casos adicionais de acentos. Nenhum desses resultados foi reexecutado para elaborar este plano.

P1 altera dois materiais; A+P1 altera sete, com o mesmo placar. A escolha incorpora a correção textual justificada, sem demonstrar superioridade de acurácia sobre P1. O combinado recuperou a aula-10, contrariando a expectativa anterior; o mecanismo detalhado continua sem diagnóstico. Ganho restrito a um material de desenvolvimento; CG/FR descritivos, nenhum curso independente. Faltam +7 em unidade e +139 em primária para superar 90%.

## Cinco passos após o Gate

1. **Isolar a integração.** Abrir branch/worktree própria baseada na `dev`, hoje `9e4137b37b6bc72e66200cf56d58a8997149982e`, após confirmar que não mudou. P1 está em `feat/cru-p1-frases-compartilhadas`, base `bf46d51fc80d1e7dcc62c08cccd0399c056bcbe1`. Issues existentes #89 e #90. Não transportar alterações locais de Moodle, configurações, hooks ou outros trabalhos da principal. Nos cinco fontes examinados, o destino atual não diverge da base P1; conferir novamente antes de aplicar os hunks.
2. **Aplicar o pacote avaliado e ativar o callback comum.** Transportar somente os deltas de `src/builder/text/normalize.py` (acentos), `src/builder/timeline/index.py` e `src/builder/routing/file_map.py` (P1), com os testes existentes. Em `src/builder/facade/file_map.py:100`, vincular `_divisores_de_frase` ao `partial` de subunidade, importando-o do módulo especializado. Esse callback chega à primeira passada em `src/builder/routing/resolver_apply.py:561` e à segunda em `:331`, encaminhado em `:586`; `src/builder/engine.py:2167` já fornece o alias à produção. Não mudar regra, limiar, pesos, taxonomia, propagação ou escopo: os divisores continuam calculados com os concorrentes de cada chamada, inclusive após os aliases da segunda passada. Evitar nova flag ou arquitetura quando a reversão do pacote basta.
3. **Verificar a integração real.** Registrar baseline da nova árvore e comparação posterior no mesmo ambiente, com `TUTOR_REPOS` explícito. Teste vermelho primeiro para provar a ativação no callback de produção nas duas passadas; depois verde, preservando os 14 testes P1 e os 7 de acentos. Rodar a suíte comparável e uma verificação offline da árvore integrada contra as decisões A+P1 já congeladas dos 350 IDs, usando o callback real sem injeção experimental. Registrar no próprio processo paths e SHA256 dos módulos carregados; abortar em identidade desconhecida/divergente, nova perda, curso regredindo ou divergência de bloco/unidade. Gold somente no placar, nunca como insumo. Corrigir a guarda operacional do runner antes de reutilizá-lo: contar somente manifests esperados e checar ABORT também após a barreira. Isso verifica código novo de integração; não reabre a avaliação dos quatro braços nem autoriza tuning/retry/revisão adicional.
4. **Preparar reversão conjunta e referências distintas.** Preservar cópia identificada da referência 86 e candidato 87, sem substituir uma pela outra. Reversão remove juntos os hunks de normalização e ativação P1, restaurando a base; testar o caminho revertido contra as 350 decisões da referência 86. Desligar só P1 deixa A, com 85/251, e não constitui reversão válida. Não reverter arquivos inteiros sobre alterações alheias. Preparar manifesto dos artefatos para versionamento no próximo commit autorizado; não confundir cópia local com referência já versionada.
5. **Entregar o Gate seguinte.** Atualizar `docs/Overview-Sistema.html`, contexto pertinente e grafo após a mudança de atribuição; apresentar diff, identidade, coleta, resultados e reversão. Promover a referência 87 somente após a verificação da integração aprovada, mantendo a 86 identificada e versionada. Integração na `dev`, commit, merge e push continuam sujeitos aos Gates e autorizações correspondentes; não executar por inferência deste plano.

## Identidades preservadas

| artefato | SHA256 |
|---|---|
| contrato v2 §5 | `d30980a3347c9866bbe2a11860310e33497d6b26a2330b408294a6600fa2e3d3` |
| P1 `timeline/index.py` | `28894d0aeed9ed7c57e2ba30efd04934c5261a63d1d8392609b8f1dc491043e5` |
| P1 `routing/file_map.py` | `6ad4f70b6aee2f1ad1c322e10a6ff26aee5789a4c76dff8dea9a5f574c5a4247` |
| normalização A | `f5b9581a38e436bdf73b2f30a89045fe884051639767a832772aa96e2cb17de1` |
| referência 86, `cru05/docs/reports/2026-10-01-cru05-cru03/replay_base.json` | `e024d396bf1cc84c33cc6735718803411cfe6bf2a57a7485501e8c4f81b77dd7` |
| candidato 87, `tentativa2/replay_ap1.json` | `6299edfd3823b2c5fd5c4a373ef221d592216250593428b9f1a2fa994cf79edd` |

O candidato e sua evidência estão em `.alethe/worktrees/job-31/docs/reports/2026-10-02-p1-avaliacao/`. Na árvore integrada, registrar também os hashes do novo vínculo e seus consumidores; não alegar identidade completa da árvore só pelos três hashes experimentais.

## Preparação realizada

Somente leitura de fontes/estado, plano e sincronização de estado/tracker. Graphify ausente nesta worktree; fallback CBM atualizado para a raiz da principal, sem persistência no repositório. O grafo não resolveu os callers do callback indireto; o caminho acima foi confirmado no fonte. Nenhuma implementação, ativação, revisão nova, motor, suíte, gold, commit ou promoção executados nesta preparação. Histórico integral do antigo active-task da principal preservado em `.workflow/local/history/active-task-2026-10-02-pre-selecao-ap1.md`.
