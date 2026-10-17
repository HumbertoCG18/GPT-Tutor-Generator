# Motor P1/A+P1 — histórico consolidado

Síntese criada em 2026-10-08 na limpeza de Markdown. Não é estado vivo nem norma nova: as fontes continuam intactas nos
lugares originais. O estado vivo está no bloco `MOTOR` de `.workflow/campanhas.json` (MOTOR-01, estado em `:94`) e o
handoff da campanha em [2026-10-02-handoff-motor-p1-moodle-claude.md](2026-10-02-handoff-motor-p1-moodle-claude.md).
Citações `arquivo:linha` usam o nome do arquivo (único no conjunto); as pastas estão nos links da tabela abaixo.

## Linha do tempo

Datas de 2026-10-02 e 2026-10-04 vêm do texto ou da pasta; `relatorio-tentativa2.md` e `resumo-noturno.md` não trazem
data própria além da pasta e do título (`resumo-noturno.md:1`).

| Data | Documento | Papel | O que estabeleceu | Superado por |
|---|---|---|---|---|
| 2026-10-02 | [relatorio-p1-implementacao](2026-10-02-p1-implementacao/relatorio-p1-implementacao.md) | implementação | P1 implementado e verificado, desligado por padrão, sem avaliação nem integração (`relatorio-p1-implementacao.md:3`); nenhum chamador de produção passa o parâmetro (`:32`) | Ativação no callback comum (`relatorio-integracao.md:25`) |
| 2026-10-02 | [revisao_job-30](2026-10-02-p1-implementacao/registros/revisao_job-30.md) | revisão | SEM BLOQUEADOR; 2 MINOR de cobertura (`revisao_job-30.md:9`, `:23`, `:24`); pytest não rodou no ambiente do revisor (`:26`) | Lacunas fechadas por 4 testes novos (`relatorio-p1-implementacao.md:80-88`) |
| 2026-10-02 | [relatorio-p1-avaliacao](2026-10-02-p1-avaliacao/relatorio-p1-avaliacao.md) | tentativa | Tentativa 1 interrompida, sem placar, sem `consolidado.json` (`relatorio-p1-avaliacao.md:3`) | Tentativa 2 (`relatorio-tentativa2.md:3`) |
| 2026-10-02 | [resumo-noturno](2026-10-02-p1-avaliacao/resumo-noturno.md) | tentativa | Resumo da tentativa 1: avaliação incompleta, tentativa consumida (`resumo-noturno.md:3`) | Tentativa 2 |
| 2026-10-02 | [plano-retomada](2026-10-02-p1-avaliacao/plano-retomada.md) | plano | Retomada em 5 passos, pendente de autorização do usuário (`plano-retomada.md:5`, `:7`) | Execução em `relatorio-tentativa2.md`; autorização em `relatorio-avaliacao-final.md:5` |
| 2026-10-02 | [relatorio-tentativa2](2026-10-02-p1-avaliacao/tentativa2/relatorio-tentativa2.md) | tentativa | Execução congelada concluída: P1 e A+P1 passam contra a base (`relatorio-tentativa2.md:3`) | Relatório canônico `relatorio-avaliacao-final.md` (`relatorio-tentativa2.md:72`) |
| 2026-10-02 | [relatorio-avaliacao-final](2026-10-02-p1-avaliacao/relatorio-avaliacao-final.md) | avaliação | P1 e A+P1 aprovados separadamente: 86/251 → 87/251, zero perda por ID (`relatorio-avaliacao-final.md:3`); usuário escolheu A+P1 (`:71`) | Plano de integração (mesmo dia) |
| 2026-10-02 | [plano-integracao-acentos-p1](2026-10-02-p1-avaliacao/plano-integracao-acentos-p1.md) | plano | 5 passos para o Gate de integração; Gate de execução e commit não concedidos (`plano-integracao-acentos-p1.md:3`, `:13-17`) | Execução em `relatorio-integracao.md` |
| 2026-10-04 | [relatorio-integracao](2026-10-04-integracao-ap1/relatorio-integracao.md) | integração | Integração A+P1 verificada; sem commit, merge ou push (`relatorio-integracao.md:3`); Gate 2 pendente (`:65`) | Estado vivo em `.workflow/campanhas.json` |

## Resultados medidos

Réguas: bloco 237, unidade 284, subunidade 251 (350 IDs), salvo indicação (`relatorio-tentativa2.md:34`). Contagens de
suíte vêm de árvores diferentes e não se somam nem se comparam entre linhas.

| Data | Base da medição | Denominador | Valor | Fonte |
|---|---|---|---|---|
| 2026-10-02 | Testes do contrato P1, worktree p1 | 14 testes | 14/14 verdes | `relatorio-p1-implementacao.md:92` |
| 2026-10-02 | Replay offline, P1 desligado × base `e024d396` | 350 IDs | 350/350 idênticos | `relatorio-p1-implementacao.md:42` |
| 2026-10-02 | Suíte da worktree p1, CPython 3.11.9 | coleta da árvore p1 | 2461 aprovados, 4 pulados, 2 falhas (as mesmas da base, por ID; base 2447) | `relatorio-p1-implementacao.md:96`, `:41` |
| 2026-10-02 | Tentativa 1 (job-31) | — | Sem placar; job de 232,166 s, limite 600 s; interrupção por estimativa do executor, não timeout | `relatorio-p1-avaliacao.md:13`, `resumo-noturno.md:9` |
| 2026-10-02 | Tentativa 2, base `e024d396` | bloco 237, unidade 284, sub 251 | bloco 223, unidade 249, sub primária 86, aceita 109 | `relatorio-tentativa2.md:37`, `relatorio-avaliacao-final.md:11` |
| 2026-10-02 | Tentativa 2, A (só acentos) `0216122c` | idem | 223, 249, sub 85, aceita 108 (−1 primária) | `relatorio-tentativa2.md:38`, `relatorio-avaliacao-final.md:12` |
| 2026-10-02 | Tentativa 2, P1 ligado | idem | 223, 249, sub **87**, aceita 110 | `relatorio-tentativa2.md:39`, `relatorio-avaliacao-final.md:13` |
| 2026-10-02 | Tentativa 2, A+P1 ligado | idem | 223, 249, sub **87**, aceita 110 | `relatorio-tentativa2.md:40`, `relatorio-avaliacao-final.md:14` |
| 2026-10-02 | A+P1 desligado × A (`replay_candidato.json`) | 350 IDs, 3 eixos | 350/350, 0 divergências | `relatorio-tentativa2.md:30` |
| 2026-10-02 | Contraste A+P1 × A por ID | sub primária e aceita | +2/−0 (TCC aula-09 e aula-10); primária 85 → 87 | `relatorio-avaliacao-final.md:20`, `relatorio-tentativa2.md:50`, `:70` |
| 2026-10-02 | Grupo desenvolvimento (MF/SO/IA/ES2/TCC), sub primária | 151 | base 50, A 49, P1 51, A+P1 51 | `relatorio-avaliacao-final.md:26` |
| 2026-10-02 | Grupo CG/FR (descritivos, expostos), sub primária | 100 | 36 nos quatro braços | `relatorio-avaliacao-final.md:27` |
| 2026-10-02 | Curso TCC, sub primária | 11 | base 7, P1 8 (único curso que muda) | `relatorio-avaliacao-final.md:30` |
| 2026-10-02 | Suíte A+P1, árvore isolada (preliminar) | 2446 coletados | 2442 aprovados, 4 pulados, 0 falhas; não comparável por ID com a base | `relatorio-tentativa2.md:55-56` |
| 2026-10-02 | Suíte A+P1 comparável, `TUTOR_REPOS` explícito | 2474 coletados (2467 anteriores + 7 de acentos) | 2469 aprovados, 4 pulados, 1 falha preexistente (`Fundamentos-de-Redes-Tutor`) | `relatorio-avaliacao-final.md:39-40`, `relatorio-tentativa2.md:68` |
| 2026-10-04 | Árvore integrada `feat/motor-integracao-ap1`, callback real da produção | 350 IDs, 237/284/251 | 0 mudanças × candidato 87 `6299edfd`; 223, 249, sub 87, aceita 110 | `relatorio-integracao.md:11`, `:14` |
| 2026-10-04 | Árvore revertida (= `dev`) | idem | 0 mudanças × referência 86 `e024d396`; 223, 249, sub 86, aceita 109 | `relatorio-integracao.md:12` |
| 2026-10-04 | Suíte, `TUTOR_REPOS` explícito | 2453 → 2476 IDs coletados (23 novos) | base 2448/4 pulados/1 falha; integrada 2471/4/1; mesma falha nas duas | `relatorio-integracao.md:39-41`, `:43` |

Efeito líquido: +1 ID (TCC `aula-09`) em 251, num único curso de desenvolvimento; sem curso independente, sem
generalização demonstrada (`relatorio-avaliacao-final.md:32`, `relatorio-tentativa2.md:61`).

## Decisões e o que ficou superado

Decisões:

1. P1 entra desligado por padrão; a divisão só ocorre no acerto, `exact_hits` não muda (`relatorio-p1-implementacao.md:24-26`, `:32`).
2. Falta de pytest no ambiente do revisor documentada e aceita, sem nova revisão (`relatorio-p1-implementacao.md:76-77`).
3. Tentativa 1 consumida, sem retry automático; nova execução exige decisão explícita (`relatorio-p1-avaliacao.md:15`).
4. Critérios do contrato v2 §5 mantidos na tentativa 2, sem ajuste de regra, divisor ou escopo (`relatorio-avaliacao-final.md:5`).
5. A sozinho reprovado (85/251, −1) (`relatorio-avaliacao-final.md:12`).
6. A+P1 escolhido pela correção textual, sem superioridade de acurácia demonstrada sobre P1 (`relatorio-avaliacao-final.md:71`, `plano-integracao-acentos-p1.md:9`).
7. Reversão válida é conjunta (normalização + ativação P1); desligar só P1 deixa A, 85/251 (`plano-integracao-acentos-p1.md:16`, `relatorio-integracao.md:48`).
8. Referência vigente continua 86 até integração e decisão própria (`relatorio-avaliacao-final.md:69`); a 87 só é promovida após o Gate 2, mantendo a 86 identificada (`relatorio-integracao.md:55`).

Superado:

- Relatório da tentativa 1: "NÃO verificado" para A+P1 desligado × A e para a suíte A+P1 (`relatorio-p1-avaliacao.md:9`), fechado em `relatorio-tentativa2.md:30` e `:68`.
- Suíte 2442/0 falhas "não comparável" (`relatorio-tentativa2.md:56`): superada pela suíte comparável (`relatorio-tentativa2.md:72`).
- Aula-10 "inferida pelo placar" (`relatorio-tentativa2.md:50`): conferida por ID (`relatorio-tentativa2.md:70`).
- Expectativa descritiva anterior do contrato, contrariada pelo resultado; o desenho não foi alterado (`relatorio-avaliacao-final.md:20`). Mecanismo sem diagnóstico (`plano-integracao-acentos-p1.md:9`).
- Guarda ABORT do runner da tentativa 2: defeito não exercido (3 manifests, 0 ABORT) e não corrigido (`relatorio-avaliacao-final.md:44`); a integração usou `verifica_integracao.py` sem a barreira (`relatorio-integracao.md:44`).
- Plano de retomada (5 passos, prazo real de 600 s): executado com autorização posterior (`plano-retomada.md:9`, `relatorio-avaliacao-final.md:5`).

## Onde continuar

- Estado vivo e próximo passo: bloco `MOTOR` de `.workflow/campanhas.json` e o handoff
  [2026-10-02-handoff-motor-p1-moodle-claude.md](2026-10-02-handoff-motor-p1-moodle-claude.md).
- Pendentes declarados em 2026-10-04 (podem estar superados pelo estado vivo): Gate 2 do diff, PR para `dev`, merge,
  replay integral na `dev` após o merge, grafo, remoção da worktree temporária (`relatorio-integracao.md:65-71`).
- Distância até 90% na régua 237/284/251: +7 em unidade e +139 na primária com o candidato 87 (`relatorio-integracao.md:60`).
  Com a referência 86, a conta anterior dava +140 (`resumo-noturno.md:59`).

## Divergências entre fontes

- `dev` de partida: `9e4137b3` em `plano-integracao-acentos-p1.md:13`, `6a55857c` em `relatorio-integracao.md:12`. Momentos diferentes; não reconciliado.
- Suíte: 2461 (`relatorio-p1-implementacao.md:96`), 2442 e 2469 (`relatorio-tentativa2.md:55`, `:68`), 2448 e 2471 (`relatorio-integracao.md:39-40`); coletas 2474 e 2476 (`relatorio-avaliacao-final.md:40`, `relatorio-integracao.md:43`). Árvores e ambientes distintos.
- Falhas preexistentes: 2 em `relatorio-p1-implementacao.md:96`, 1 em `relatorio-avaliacao-final.md:39`; a de ActualText não reapareceu, sem atribuir correção de produto (`relatorio-avaliacao-final.md:39`).
- Slug da aula-10: `linguagens-reconheciveis-e-decidiveis` em `relatorio-tentativa2.md:50`, com `ı` sem ponto em `relatorio-avaliacao-final.md:20`. Grafia, mesmo material.
