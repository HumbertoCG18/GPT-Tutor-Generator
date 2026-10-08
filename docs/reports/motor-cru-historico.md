# Motor no regime cru — histórico consolidado

Síntese criada em 2026-10-08 na limpeza de Markdown. Não é estado vivo nem norma nova: consolida contexto e decisões de quatro documentos de 12 a 24/09/2026, que continuam intactos no lugar. O estado vivo está em `.workflow/campanhas.json` (campanha `MOTOR`, linhas 66-77, handoff apontado: `docs/reports/2026-10-02-handoff-motor-p1-moodle-claude.md`), em `.workflow/HANDOFF.md` e em `.mex/ROUTER.md` (linha 18). Citações no formato `arquivo:linha`; os nomes abreviam o prefixo de data: `12/09` = `2026-09-12-handoff-regime-cru.md`, `14/09` = `2026-09-14-handoff-codex-regime-cru.md`, `23/09` = `2026-09-23-handoff-motor-wz-waa-claude.md`, `24/09` = `2026-09-24-teto-regime-cru.md`.

## Linha do tempo

| Data | Documento | Papel | O que estabeleceu | Superado por |
|---|---|---|---|---|
| 12/09 (seções até 14/09) | [handoff-regime-cru](2026-09-12-handoff-regime-cru.md) | Referência detalhada §1–§41 (`14/09:339`) | Congelou a régua do cru, mediu bloco, unidade e subunidade sem LLM, fechou várias alavancas por medição (lista em `14/09:121-137`) e registrou as correções de suas próprias conclusões | Ponto de entrada passou ao handoff de 14/09 (`12/09:2988`); segue como referência por § (`14/09:10`) |
| 14/09 | [handoff-codex-regime-cru](2026-09-14-handoff-codex-regime-cru.md) | Ponto de entrada autocontido para o Codex (`14/09:3`) | Placar do cru honesto, leis de processo, decisões do usuário, 3 opções medidas, defeito do teto de 14.000 caracteres do glossário, meta revista não adotada | Placar substituído pela régua v2 de 22-23/09 (`23/09:28`); decisões abertas da §10 (`14/09:222-229`) não aparecem resolvidas nestas quatro fontes |
| 23/09 | [handoff-motor-wz-waa-claude](2026-09-23-handoff-motor-wz-waa-claude.md) | Handoff da sessão Claude 843a75cb (`23/09:3`) | Placar na régua v2; W-Z, W-Z2 (diagnóstico causal) e W-AA reprovados; issues #63–#65 do D9; pendências em ordem | Unidade 248 → 249 com M1 (`24/09:29-30`); `.mex/ROUTER.md:18` o cita como handoff do motor |
| 24/09 | [teto-regime-cru](2026-09-24-teto-regime-cru.md) | Relatório de teto, "não é previsão" (`24/09:4`) | Placar por curso, tetos do cru, famílias de erro, varredura W-AC, mecanismos fechados | Sem sucessor nestas fontes. O ROUTER cita o regime VOCAB (handoff de 26/09) e a campanha aponta o handoff de 02/10; não foram lidos aqui |

## Resultados medidos

Formato: data, base, denominador, valor (fonte). Três réguas distintas aparecem; não somar nem comparar entre grupos (ver "Réguas e divergências").

### Grupo A — 12/09, régua curricular de unidade, produto em disco e replay (subunidade, base 251)

- 12/09, produto em disco, 251: aceito 224 (89,2 %), primário 186 (74,1 %) (`12/09:21`).
- 12/09, cru por replay (sem vocabulário LLM, curadoria humana mantida), 251: aceito 147 (58,6 %), primário 105 (41,8 %) (`12/09:26`); replay x produto, 0 divergências em 251/251 (`12/09:35`).
- 12/09, só código de outline, 251: 113 (45,0 %) e 84 (33,5 %) (`12/09:27`).
- 12/09, precisão do confiante, 251: produto 178/193 (92,2 %); cru 113/190 (59,5 %), 77 erros confiantes (`12/09:404-407`).
- 12/09, teto das fontes do professor no cru (`--so-llm`), primário, 227: 100 (44 %); o 64 % anterior estava errado (`12/09:240-249`).
- 12/09, SARC posicional, 251: controle cru 147 aceito, entrega 113, erros 77; SARC-A 141/110/85. Produto 224/178/15 contra 209/165/34. Fechado por negativo (`12/09:674-676`, `12/09:688`).

### Grupo B — 12 a 14/09, motor completo, uma configuração por vez, 0 chamadas de rede

- 12/09, 4 configurações, bloco/237: 221, 222, 221, 235; unidade/284: 244, 253, 255, 263; subunidade aceito/251: 125, 146, 220, 224; primário/251: 85, 103, 184, 186 (`12/09:956-961`); rede 0/0/0 (`12/09:963`).
- 13/09, cru honesto (braço C, sem a curadoria escolhida contra a régua), 237/284/251: bloco 222 (93,7 %), unidade 253 (89,1 %), aceito 142 (56,6 %), primário 100 (39,8 %) (`12/09:1705-1710`, `12/09:1738`). Sem o ruling do OpenGL: unidade 248, aceito 137, primário 95 (`12/09:1708-1710`).
- 13/09, braço V (18 termos em 2 tópicos do IA), 251: aceito 142 → 175 (69,7 %), primário 100 → 134; bloco e unidade sem mudança; IA 5/39 → 38/39 (`12/09:1971-1980`). Efeito de relação fornecida, não de aquisição (`14/09:109-112`).
- 13/09, FR construído do zero, primário/18: 6 cru, 16 com vocabulário compilado por LLM (`12/09:2094-2096`).
- 13/09, `sempropag` nos 7 cursos, 251: 142 e 100 inalterados; 5 ganhos, 5 perdas (`12/09:2240-2244`).
- 13/09, precedência bloco x texto, conflitos: "texto vence sempre" −15 no cru e −7 no produto (`12/09:1302-1303`); regra por método do bloco +38 dentro da amostra e −3 cru, −4 produto no leave-one-course-out (`12/09:1426-1428`).
- 13/09, título como discriminante de unidade, 284: sobrepor sempre −9 no cru, −14 no produto (`12/09:1245`).
- 13/09, pai x filho, 109 erros de aceito: 8 pai vence filho (`12/09:2364`, `12/09:2421`); 0 de 8 com token distintivo do filho (`12/09:2447`).
- 14/09, extrator de relações explícitas (braço R), 251: primário 100 → 101, aceito 142; o único ganho é autodoação (`12/09:2707-2714`).
- 14/09, braços sobre a base 142/100, corte ≥5 primário, ≥5 aceito, 0 perdas: estrito 144/102, 0 perdas; A 142/99, 6 perdas; C (LLM) 120/96, 87 perdas (`12/09:2846-2847`, `12/09:2941`; `14/09:154-157`). Ganho transferível: estrito +1 primário; A −3; C −2 (`14/09:154-157`).
- 14/09, GLOSSARY.md do CG em produção: 13.974 caracteres, truncado, 14 de 59 tópicos sem alias; efeito no placar não medido (`14/09:196-203`).

### Grupo C — 22 a 24/09, régua v2 final + 13 materiais presentes, 237/284/251

- 23/09, `feat/motor-atribuicao` HEAD `14f0e08d`: bloco 223/237, unidade 248/284, sub primária 86/251 (`23/09:39`).
- 24/09, `feat/motor-atribuicao` `eebc698c` (inclui M1): bloco 223/237 (94,1 %), unidade 249/284 (87,7 %), sub primária 86/251 (34,3 %); mínimos >90 %: 214 / 256 / 226 (`24/09:7`, `24/09:21`).
- 23/09, W-AA, subunidade primária, base 86: S (A) 83, G (B') 76, G+S (B) 73; nenhum braço passa (`23/09:62-64`).
- 23/09, oráculo de unidade: 86 → 92 (8 correções, 2 perdas) (`23/09:57`).
- 24/09, teto de unidade, 284: caminhos admissíveis 253 (89,1 %); medidos 250; implementado 249 (`24/09:29-30`).
- 24/09, teto de subunidade primária (limite ideal): 218 (86,9 %) com a unidade atual, 234 (93,2 %) com unidade perfeita, contra mínimo 226 (`24/09:44`).
- 24/09, W-AC, sobre os 86 acertos, portão precisão >50 % e saldo >0: P1 21 %, saldo −3; P2 13 %, −31; P4 não dispara; P5 65 %, −6; nenhum passa (`24/09:71-78`).
- 24/09, anatomia dos 165 erros de subunidade: F6 65, F4b 33, F8 23, F2 17, F7 11, F4a 8, F1 5, F5 3 (`24/09:51-62`).

### Réguas e divergências

- Mesmos denominadores (237/284/251), valores e réguas diferentes: 14/09 dá 222 / 253 / primário 100 (`14/09:93-98`); 23-24/09 dá 223 / 248-249 / primário 86 (`23/09:39`, `24/09:21`). A régua v2 foi commitada em `9cfdf2c7` (`23/09:73`) e a base de código também mudou (cópia do produto em `.motor3eixos` contra `feat/motor-atribuicao`). Estas fontes não decompõem a diferença; não atribuir à régua ou ao código.
- O 253/284 de `24/09:29` (teto de caminhos admissíveis, régua v2) coincide numericamente com o 253/284 do cru honesto de `14/09:93`; são medidas diferentes.
- Cru de 12/09: 147/105 por replay (`12/09:26`) contra 146/103 no motor completo (`12/09:960-961`); instrumentos diferentes. Cru de 14/09 (142/100) também difere por retirar a curadoria escolhida contra a régua (`12/09:1738-1740`).
- Teto das fontes do professor: o 64 % (`12/09:230`, `12/09:238`) foi corrigido para 44 % no mesmo arquivo (`12/09:246`). Trechos antigos ainda citam 61 % (`12/09:94-95`, `12/09:271`).
- "Teto da aquisição = 32" (`12/09:1779`) foi declarado piso mal calibrado após o braço V (`12/09:1995-1996`).
- Contagem de erros confiantes do cru: 82 na mensagem de commit, 77 na correção (`12/09:416`, `12/09:444`).

## Teto do sinal e decisões

- Regime cru: 0 LLM, 0 rede, 0 embedding; gold só avalia; nada por curso, arquivo ou ID (`24/09:3`). Embedding conta como LLM e o caminho padrão roda em máquina fraca (`14/09:74`).
- Meta do usuário: 95 % em três eixos em 13/09 (`14/09:41-45`). O astra propôs meta revista (≥95 % de precisão automática, ≥80 % de cobertura, cursos inéditos), "decisão do usuário, não adotada" (`14/09:47-50`). Em 21/09 o usuário fixou >90 % em bloco, unidade e subunidade primária, por curso e no total (`24/09:3-4`). Nenhuma das quatro fontes registra a passagem de 95 % para 90 %.
- Métrica de 12/09: precisão aceita do confiante, com cobertura e fila (`12/09:392-393`); a proposta do astra de 14/09 mantém o primário como métrica principal da subunidade (`12/09:2757`) e a meta de 21/09 cobra a subunidade primária (`23/09:13`).
- Gold só avalia; LLM e API totalmente opcionais; motor modular; o motor segue o plano, não o bloco (`14/09:69-73`). Rotulação pelo professor fora do produto; conhecimento externo só como regime separado (`23/09:17-18`, `24/09:91`).
- Teto atual (24/09): placar total 223/237, 249/284, 86/251 (`24/09:21`). Faltam 7 em unidade (CG +10, SO +4) e 140 em subunidade (`24/09:24-25`). O limite ideal da subunidade (218) fica abaixo do mínimo (226) (`24/09:44`, `24/09:95`). "Não é previsão" (`24/09:4`).
- Causa comum: tópicos do plano são categorias e os materiais usam algoritmos e termos; o pacote do professor não traz a relação (`24/09:64-66`; `12/09:646-650`).
- Mecanismos fechados, sem reabrir sem sinal novo: precedência bloco x texto R1–R4 e "seção sozinha"; S e G (W-AA); ConceptNet; pai x filho e H2; sinais da W-AC; rotulação pelo professor (`24/09:85-91`). Antes de 22/09: SARC posicional, título, abstenção, plural, `sempropag`, extrator explícito, regra lexical fraca A (`14/09:121-137`).
- O que mudaria o teto é sempre sinal que o pacote não contém: relação vocabulário → tópico com proveniência (regime separado, guarda contra ajuste ao benchmark) ou plano mais granular (`24/09:97-99`).
- Publicar o cru exige placar por curso e regime, abstenções e ausentes no denominador (`24/09:100-101`).
- Leis de processo: corte declarado antes de rodar; só conta ganho transferível; gold não decide; aceite de integração = ganho positivo, zero perda, nenhum curso regride (`14/09:85-87`, `23/09:13-16`). Não repetir ganho dentro da amostra como regra: leave-one-course-out (`12/09:1426-1435`).
- Defeitos do produto registrados, não implementados: glossário truncado em 14.000 caracteres (`14/09:196-203`); D9 apaga `feature_flags` ao salvar matéria (#63), options x execução (#64), padrão e fallback (#65) (`23/09:70-72`).

## Onde continuar

1. Estado vivo da campanha: bloco `MOTOR` de `.workflow/campanhas.json` (linhas 66-77), tarefas `MOTOR-00` em diante. Handoff apontado ali: `docs/reports/2026-10-02-handoff-motor-p1-moodle-claude.md`.
2. Contexto do motor: `.mex/ROUTER.md:18` (tracker `docs/reports/pendencias.md`, regime VOCAB de 26 e 27/09, handoff de 23/09) e `.workflow/HANDOFF.md` (linhas 25-29, estado de 22/09). Apenas apontados; esta síntese não os altera.
3. Pendências abertas em 23/09, todas dependentes de decisão do usuário: direção da subunidade, régua do CG (5 casos), Gate 1 das issues #63/#64 e decisão da #65, Gate 2 do `fix(timeline)`, adjudicações do W-Y, push/PR (`23/09:76-88`). Podem ter sido tratadas depois; confirmar no estado vivo.
4. Insumos e reprodução: relatório causal `_archive/2026-09-23-diagnostico-causal-tres-eixos.md` (`23/09:49`), [waa-desenho](2026-09-23-waa-desenho.md), [waa-resultado](2026-09-23-waa-resultado.md), harness em `docs/reports/_harness-2026-09-04/c1-3/` (`14/09:14`, receita em `14/09:259-311`). Não repetir medições: capturas congeladas aceitam `--reavaliar` (`23/09:95-97`).
5. Não fazer sem Gate 1: implementar S, G, correções do D9 ou mudar defaults; não salvar matérias no Gerenciador de Matérias enquanto a #63 estiver aberta (`23/09:105-107`).
