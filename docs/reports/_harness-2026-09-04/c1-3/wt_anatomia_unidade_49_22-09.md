# W-T (CRU-03 unidade) - anatomia dos erros no estado #49, bloqueios de subunidade, regra candidata

Data: 2026-09-22. HEAD `410592d` (#49). Medicao em memoria, fora de `src/`; nada em `src/` ou `tests/` foi tocado.
Cadeia real bloco -> unidade -> subunidade (molde de `aceite_v1_49_22-09.py`), voter=None, sem build/rede/LLM.
Gold carregado DEPOIS do congelamento das decisoes por sha256. Ambos os JSON foram gravados com `assert not exists`.

## 1. Reproducao do estado #49

| eixo | medido | esperado |
|---|---|---|
| bloco | 217/237 | 217/237 |
| unidade | 246/284 | 246/284 |
| subunidade primaria | 84/251 | 84/251 |
| subunidade aceita | 107/251 | 107/251 |

Checks: `{'bloco_217_de_237': True, 'erros_de_unidade_sao_38': True, 'sub_primaria_84_aceita_107_de_251': True, 'unidade_246_de_284': True}`. sha256 do congelamento das decisoes: `1b56f1dda165335a51d622b7e80eabaa65eceb2d45356e18098132e2f960c18e`.

## 2. Os 38 erros de unidade, por classe

| classe | n |
|---|---|
| ausente | 13 |
| herdada_do_bloco_certo_mas_gold_diverge | 12 |
| herdada_do_bloco_errado | 9 |
| texto_vence_errado | 4 |

Por curso: **CG** {'ausente': 7, 'herdada_do_bloco_certo_mas_gold_diverge': 1, 'herdada_do_bloco_errado': 7, 'texto_vence_errado': 4}; **ES2** {'herdada_do_bloco_certo_mas_gold_diverge': 2, 'herdada_do_bloco_errado': 1}; **IA** {'ausente': 2, 'herdada_do_bloco_certo_mas_gold_diverge': 1}; **MF** {'ausente': 4, 'herdada_do_bloco_certo_mas_gold_diverge': 1}; **SO** {'herdada_do_bloco_certo_mas_gold_diverge': 6, 'herdada_do_bloco_errado': 1}; **TCC** {'herdada_do_bloco_certo_mas_gold_diverge': 1}

`regua_ambigua` e flag paralela (gold com mais de uma unidade aceita e predicao fora): 1 caso(s) - [['CG', 'resolucao-de-prova-de-computacao-grafica-3d']].

Lista completa (bloco predito/gold, unidade predita/gold, vencedor bruto do scorer com confianca e ambiguidade, razoes):

| # | classe | curso | id | bloco pred/gold | unidade pred | unidade gold | scorer bruto (conf, amb) | bruto acertaria | razoes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ausente | MF | `eth2` | - / bloco-01 | (vazia) | unidade-02-verificacao-de-programas | - (, None) | nao | - |
| 2 | ausente | MF | `aws-encryption-sdk` | - / bloco-01 | (vazia) | unidade-02-verificacao-de-programas | - (, None) | nao | - |
| 3 | ausente | MF | `archive-of-formal-proofs-355fb8` | - / bloco-01 | (vazia) | unidade-01-metodos-formais | - (, None) | nao | - |
| 4 | ausente | MF | `t1-2026-1` | - / bloco-11 | (vazia) | unidade-01-metodos-formais | - (, None) | nao | - |
| 5 | herdada_do_bloco_certo_mas_gold_diverge | MF | `t1-2026-1-thy` | bloco-11 / bloco-11 | unidade-02-verificacao-de-programas | unidade-01-metodos-formais | unidade-02-verificacao-de-programas (0.97, False) | nao | winner_score=2.81; topic_score=0.02; herdada_do_vizinho=bloco-10 |
| 6 | herdada_do_bloco_errado | SO | `laminas-sockets-material-alternativo-em-pt` | bloco-06 / bloco-09 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-03-programacao-concorrente (0.01, True) | sim | winner_score=6.87; topic_score=2.00; ambiguous; herdada_do_bloco=bloco-06 |
| 7 | herdada_do_bloco_certo_mas_gold_diverge | SO | `0704-exemplo-threads-em-java` | bloco-06 / bloco-06 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-02-gerencia-do-processador (0.00, True) | nao | winner_score=0.23; topic_score=0.11; ambiguous; herdada_do_bloco=bloco-06 |
| 8 | herdada_do_bloco_certo_mas_gold_diverge | SO | `3103-threads` | bloco-04 / bloco-04 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-03-programacao-concorrente (0.58, False) | sim | winner_score=16.03; topic_score=15.36; reconciliada_do_bloco=bloco-04 |
| 9 | herdada_do_bloco_certo_mas_gold_diverge | SO | `biblioteca-em-c-pthread` | bloco-04 / bloco-04 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-03-programacao-concorrente (0.68, False) | sim | winner_score=19.12; topic_score=15.11; reconciliada_do_bloco=bloco-04 |
| 10 | herdada_do_bloco_certo_mas_gold_diverge | SO | `exemplo-threads-em-c-exemplo1` | bloco-04 / bloco-04 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-07-gerencia-de-entrada-e-saida (0.63, False) | nao | winner_score=0.58; topic_score=0.11; reconciliada_do_bloco=bloco-04 |
| 11 | herdada_do_bloco_certo_mas_gold_diverge | SO | `exemplo-threads-em-c-exemplo2` | bloco-04 / bloco-04 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-07-gerencia-de-entrada-e-saida (0.63, False) | nao | winner_score=0.58; topic_score=0.11; reconciliada_do_bloco=bloco-04 |
| 12 | herdada_do_bloco_certo_mas_gold_diverge | SO | `exemplo-threads-em-c-exemplo3` | bloco-04 / bloco-04 | unidade-02-gerencia-do-processador | unidade-03-programacao-concorrente | unidade-07-gerencia-de-entrada-e-saida (1.00, False) | nao | winner_score=5.57; topic_score=0.91; reconciliada_do_bloco=bloco-04 |
| 13 | ausente | IA | `o-que-é-inteligência-artificial-ia-oracle-brasil-43437f` | - / bloco-01 | (vazia) | unidade-de-aprendizagem-01-visao-geral | - (, None) | nao | - |
| 14 | ausente | IA | `ia-responsável-7c4626` | - / bloco-01 | (vazia) | unidade-de-aprendizagem-01-visao-geral | - (, None) | nao | - |
| 15 | herdada_do_bloco_certo_mas_gold_diverge | IA | `visao-geral-introducao-e-historico` | bloco-02 / bloco-02 | unidade-de-aprendizagem-05-aprendizado-de-maquina | unidade-de-aprendizagem-01-visao-geral | unidade-de-aprendizagem-01-visao-geral (0.79, False) | sim | winner_score=47.27; topic_score=11.92; reconciliada_do_bloco=bloco-02 |
| 16 | herdada_do_bloco_certo_mas_gold_diverge | ES2 | `microsservicos5` | bloco-08 / bloco-08 | unidade-02-integracao-de-desenvolvimento-e-operacao-devops | unidade-01-arquitetura-de-software | unidade-01-arquitetura-de-software (0.12, True) | sim | winner_score=14.52; topic_score=2.29; ambiguous; herdada_do_bloco=bloco-08 |
| 17 | herdada_do_bloco_certo_mas_gold_diverge | ES2 | `microsservicos7` | bloco-09 / bloco-09 | unidade-02-integracao-de-desenvolvimento-e-operacao-devops | unidade-01-arquitetura-de-software | unidade-01-arquitetura-de-software (0.95, False) | sim | winner_score=24.67; topic_score=9.16; reconciliada_do_bloco=bloco-09 |
| 18 | herdada_do_bloco_errado | ES2 | `azure` | bloco-08 / bloco-09 | unidade-02-integracao-de-desenvolvimento-e-operacao-devops | unidade-01-arquitetura-de-software | unidade-01-arquitetura-de-software (0.00, True) | sim | winner_score=0.57; topic_score=0.14; ambiguous; herdada_do_bloco=bloco-08 |
| 19 | herdada_do_bloco_certo_mas_gold_diverge | TCC | `aula-11-o-problema-da-parada-halting-problem-halteproblem-pdf` | bloco-10 / bloco-10 | unidade-02-turing-computabilidade | unidade-03-problemas-indecidiveis | unidade-03-problemas-indecidiveis (0.60, False) | sim | winner_score=33.47; topic_score=12.29; reconciliada_do_bloco=bloco-10 |
| 20 | texto_vence_errado | CG | `morfologiamatematicapptx` | bloco-08 / bloco-08 | unidade-06-processo-de-visualizacao-3d | unidade-03-processamento-de-imagens-e-visao-computacional | unidade-06-processo-de-visualizacao-3d (1.00, False) | nao | winner_score=10.16; topic_score=10.39 |
| 21 | herdada_do_bloco_errado | CG | `basico3d-cpp` | bloco-05 / bloco-15 | unidade-02-fundamentos-matematicos | unidade-07-representacao-e-modelagem-de-objetos | unidade-04-processo-de-visualizacao-2d (0.72, False) | nao | winner_score=23.23; topic_score=16.99; reconciliada_do_bloco=bloco-05 |
| 22 | herdada_do_bloco_errado | CG | `basico3d-py-zip` | bloco-05 / bloco-15 | unidade-02-fundamentos-matematicos | unidade-07-representacao-e-modelagem-de-objetos | unidade-01-introducao-ao-processamento-grafico (0.81, False) | nao | winner_score=10.20; topic_score=4.80; reconciliada_do_bloco=bloco-05 |
| 23 | herdada_do_bloco_errado | CG | `exercicios` | bloco-02 / - | unidade-02-fundamentos-matematicos | unidade-01-introducao-ao-processamento-grafico | unidade-03-processamento-de-imagens-e-visao-computacional (0.40, True) | nao | winner_score=0.48; topic_score=0.14; ambiguous; herdada_do_bloco=bloco-02; herdada_do_vizinho=bloco-03 |
| 24 | texto_vence_errado | CG | `openglbasico` | bloco-02 / - | unidade-03-processamento-de-imagens-e-visao-computacional | unidade-01-introducao-ao-processamento-grafico | unidade-03-processamento-de-imagens-e-visao-computacional (0.58, False) | nao | winner_score=13.05; topic_score=9.16; texto-vence-vizinho=bloco-03 |
| 25 | texto_vence_errado | CG | `texturas-v3` | bloco-02 / - | unidade-01-introducao-ao-processamento-grafico | unidade-08-sintese-de-imagens-realisticas | unidade-01-introducao-ao-processamento-grafico (0.81, False) | nao | winner_score=10.20; topic_score=4.80; texto-vence-vizinho=bloco-03 |
| 26 | herdada_do_bloco_certo_mas_gold_diverge | CG | `exemplodemanipulacaodeimagens` | bloco-03 / bloco-03 | unidade-02-fundamentos-matematicos | unidade-03-processamento-de-imagens-e-visao-computacional | unidade-05-transformacoes-geometricas (0.12, True) | nao | winner_score=2.53; topic_score=0.91; ambiguous; herdada_do_bloco=bloco-03 |
| 27 | herdada_do_bloco_errado | CG | `exercicios-sobre-curvas-html` | - / - | unidade-02-fundamentos-matematicos | unidade-07-representacao-e-modelagem-de-objetos | unidade-07-representacao-e-modelagem-de-objetos (0.80, False) | sim | winner_score=22.38; topic_score=4.92; reconciliada_do_bloco=bloco-03 |
| 28 | herdada_do_bloco_errado | CG | `resolucao-de-prova-de-computacao-grafica-2d` | - / - | unidade-01-introducao-ao-processamento-grafico | unidade-04-processo-de-visualizacao-2d | unidade-01-introducao-ao-processamento-grafico (0.00, True) | nao | winner_score=0.01; topic_score=0.00; ambiguous; herdada_do_bloco=bloco-01 |
| 29 | herdada_do_bloco_errado | CG | `resolucao-de-prova-de-computacao-grafica-2d-html` | - / - | unidade-01-introducao-ao-processamento-grafico | unidade-04-processo-de-visualizacao-2d | unidade-01-introducao-ao-processamento-grafico (0.00, True) | nao | winner_score=0.01; topic_score=0.00; ambiguous; herdada_do_bloco=bloco-01 |
| 30 | herdada_do_bloco_errado | CG | `resolucao-de-prova-de-computacao-grafica-3d` | - / - | unidade-01-introducao-ao-processamento-grafico | unidade-06-processo-de-visualizacao-3d, unidade-07-representacao-e-modelagem-de-objetos, unidade-08-sintese-de-imagens-realisticas | unidade-01-introducao-ao-processamento-grafico (0.00, True) | nao | winner_score=0.01; topic_score=0.00; ambiguous; herdada_do_bloco=bloco-01 |
| 31 | ausente | CG | `video-sobre-origens-da-computacao-grafica-806e66` | - / - | (vazia) | unidade-01-introducao-ao-processamento-grafico | - (, None) | nao | - |
| 32 | ausente | CG | `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758` | - / - | (vazia) | unidade-01-introducao-ao-processamento-grafico | - (, None) | nao | - |
| 33 | ausente | CG | `video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e` | - / - | (vazia) | unidade-04-processo-de-visualizacao-2d | - (, None) | nao | - |
| 34 | ausente | CG | `video-sobre-mapeamento-em-opengl-1dad3c` | - / - | (vazia) | unidade-04-processo-de-visualizacao-2d | - (, None) | nao | - |
| 35 | ausente | CG | `aula-gravada-975b85` | - / - | (vazia) | unidade-03-processamento-de-imagens-e-visao-computacional | - (, None) | nao | - |
| 36 | ausente | CG | `video-sobre-prechimento-de-areas-duracao-330-defae7` | - / - | (vazia) | unidade-03-processamento-de-imagens-e-visao-computacional | - (, None) | nao | - |
| 37 | ausente | CG | `video-sobre-prechimento-de-areas-duracao-1300-d87e5f` | - / - | (vazia) | unidade-03-processamento-de-imagens-e-visao-computacional | - (, None) | nao | - |
| 38 | texto_vence_errado | CG | `pagina-com-videos-sobre-morfologia-matematica-06265a` | bloco-08 / - | unidade-06-processo-de-visualizacao-3d | unidade-03-processamento-de-imagens-e-visao-computacional | unidade-06-processo-de-visualizacao-3d (0.95, False) | nao | winner_score=10.72; topic_score=10.95 |

Recuperaveis sem tocar o bloco (o vencedor bruto do scorer esta no gold): **9** - [['CG', 'exercicios-sobre-curvas-html'], ['ES2', 'azure'], ['ES2', 'microsservicos5'], ['ES2', 'microsservicos7'], ['IA', 'visao-geral-introducao-e-historico'], ['SO', '3103-threads'], ['SO', 'biblioteca-em-c-pthread'], ['SO', 'laminas-sockets-material-alternativo-em-pt'], ['TCC', 'aula-11-o-problema-da-parada-halting-problem-halteproblem-pdf']].

## 3. Bloqueios de subunidade por (unidade, slug) no estado #49

Total **10** ({'CG': 7, 'ES2': 3}), sobre 245 materiais com gold primario nao vazio.

| curso | gold_id | unidade vigente (#49) | gold primario | unidade(s) que contem o topico |
|---|---|---|---|---|
| ES2 | `roteiro4-circuitbreaker` | unidade-01-arquitetura-de-software | estudo-de-caso-integracao-e-implantacao-de-microsservicos | unidade-02-integracao-de-desenvolvimento-e-operacao-devops |
| ES2 | `microsservicos4` | unidade-01-arquitetura-de-software | estudo-de-caso-integracao-e-implantacao-de-microsservicos | unidade-02-integracao-de-desenvolvimento-e-operacao-devops |
| ES2 | `roteiro4` | unidade-01-arquitetura-de-software | estudo-de-caso-integracao-e-implantacao-de-microsservicos | unidade-02-integracao-de-desenvolvimento-e-operacao-devops |
| CG | `morfologiamatematicapptx` | unidade-06-processo-de-visualizacao-3d | segmentacao | unidade-03-processamento-de-imagens-e-visao-computacional |
| CG | `basico3d-cpp` | unidade-02-fundamentos-matematicos | tecnicas-de-modelagem-3d | unidade-07-representacao-e-modelagem-de-objetos |
| CG | `basico3d-py-zip` | unidade-02-fundamentos-matematicos | tecnicas-de-modelagem-3d | unidade-07-representacao-e-modelagem-de-objetos |
| CG | `exercicios` | unidade-02-fundamentos-matematicos | aplicacoes | unidade-01-introducao-ao-processamento-grafico |
| CG | `openglbasico` | unidade-03-processamento-de-imagens-e-visao-computacional | aplicacoes | unidade-01-introducao-ao-processamento-grafico |
| CG | `exercicios-sobre-curvas-html` | unidade-02-fundamentos-matematicos | catmull-rom | unidade-07-representacao-e-modelagem-de-objetos |
| CG | `pagina-com-videos-sobre-morfologia-matematica-06265a` | unidade-06-processo-de-visualizacao-3d | segmentacao | unidade-03-processamento-de-imagens-e-visao-computacional |

Reconciliacao por ID: W-T 10, W-P1 10, W-S 17. Intersecao dos tres: 10. Nada so no W-T; nada do W-P1 fora do W-T.

Os 7 que so o W-S contava:

| curso | id | por que sai no estado #49 |
|---|---|---|
| CG | `opengl-cpp` | a #48 mudou a unidade para `unidade-01-introducao-ao-processamento-grafico`, que CONTEM `aplicacoes`; o W-S usou a unidade gravada no manifest (pre-#48) |
| CG | `opengl-py` | idem |
| SO | `1903-estruturas-de-controle` | unidade vigente `unidade-02-gerencia-do-processador` CONTEM `conceitos-basicos` (slug duplicado: existe em `unidade-02-gerencia-do-processador` E em `unidade-04-deadlock`); casando por (unidade, slug) nao ha bloqueio |
| SO | `3103-threads` | unidade vigente `unidade-02-gerencia-do-processador` CONTEM `conceitos-basicos` (slug duplicado: existe em `unidade-02-gerencia-do-processador` E em `unidade-04-deadlock`); casando por (unidade, slug) nao ha bloqueio |
| SO | `exemplo-threads-em-c-exemplo1` | unidade vigente `unidade-02-gerencia-do-processador` CONTEM `conceitos-basicos` (slug duplicado: existe em `unidade-02-gerencia-do-processador` E em `unidade-04-deadlock`); casando por (unidade, slug) nao ha bloqueio |
| SO | `exemplo-threads-em-c-exemplo2` | unidade vigente `unidade-02-gerencia-do-processador` CONTEM `conceitos-basicos` (slug duplicado: existe em `unidade-02-gerencia-do-processador` E em `unidade-04-deadlock`); casando por (unidade, slug) nao ha bloqueio |
| SO | `exemplo-threads-em-c-exemplo3` | unidade vigente `unidade-02-gerencia-do-processador` CONTEM `conceitos-basicos` (slug duplicado: existe em `unidade-02-gerencia-do-processador` E em `unidade-04-deadlock`); casando por (unidade, slug) nao ha bloqueio |

Bloqueios que dependem do slug duplicado: **0**. Os 5 do SO nao sao bloqueio em nenhuma leitura de (unidade, slug) do estado #49 - a unidade vigente e uma das duas que hospedam o slug. O erro de subunidade de `3103-threads` e dos tres `exemplo-threads-em-c-*` e erro de UNIDADE (o gold curricular pede `unidade-03-programacao-concorrente`), nao bloqueio de taxonomia.

## 4. Regras candidatas (pre-declaradas) - REPROVADAS

Declaracao congelada antes de medir, sha256 `278ba0eec23432858d0102463bbc469632716426cc2e85457414d3fe7d076f0d`; congelamento das decisoes das 7 variantes `93fac811a6e589584a378ce30d8d7935584f14abc8c8d73b47228beb4e75bd19`.

Familia atacada: 6 erros com razao `reconciliada_do_bloco=<id>`, scorer nao ambiguo, acima do gate, vencedor bruto igual ao gold (SO `3103-threads`, SO `biblioteca-em-c-pthread`, IA `visao-geral-introducao-e-historico`, ES2 `microsservicos7`, TCC `aula-11-...-halting-problem`, CG `exercicios-sobre-curvas-html`). Mesma clausula que a #48 abriu para o vizinho.

- **R2** (sem parametro): no ramo final de `reconcile_unit_with_block`, se a unidade gated nao e vazia, o texto vence o bloco.
- **R1** (R2 + limiar): o texto so vence se `unit_confidence >= tau`, tau escolhido por LOCO no grid [0.5, 0.6, 0.7, 0.8, 0.9].

Risco pre-declarado medido: a clausula `reconciliada_do_bloco=` cobre **49** materiais avaliados no eixo unidade, dos quais **38 JA ACERTAM** (MF 7 (7 acertos), SO 13 (8 acertos), IA 1 (0 acertos), ES2 9 (8 acertos), TCC 1 (0 acertos), CG 18 (15 acertos)).

| variante | unidade/284 | sub prim/251 | sub aceita/251 | bloco/237 |
|---|---|---|---|---|
| base | 246 | 84 | 107 | 217 |
| R2 | 215 | 63 | 84 | 217 |
| R1_tau0.50 | 215 | 63 | 84 | 217 |
| R1_tau0.60 | 219 | 64 | 85 | 217 |
| R1_tau0.70 | 228 | 72 | 92 | 217 |
| R1_tau0.80 | 236 | 77 | 97 | 217 |
| R1_tau0.90 | 237 | 80 | 101 | 217 |

LOCO (so para escolher o limiar; cursos ja estudados nao sao holdout novo), por fold:

| fold | tau escolhido nos 6 de treino | unidade no fold |
|---|---|---|
| CG | R1_tau0.90 | 65/93 |
| ES2 | R1_tau0.90 | 26/28 |
| FR | R1_tau0.90 | 0/0 |
| IA | R1_tau0.90 | 39/42 |
| MF | R1_tau0.80 | 59/66 |
| SO | R1_tau0.90 | 30/37 |
| TCC | R1_tau0.90 | 17/18 |

tau final por LOCO: **R1_tau0.90**.

### R2

- Unidade por curso: CG 60, ES2 19, IA 40, MF 54, SO 24, TCC 18
- Ganhos de unidade (6): [['CG', 'exercicios-sobre-curvas-html'], ['ES2', 'microsservicos7'], ['IA', 'visao-geral-introducao-e-historico'], ['SO', '3103-threads'], ['SO', 'biblioteca-em-c-pthread'], ['TCC', 'aula-11-o-problema-da-parada-halting-problem-halteproblem-pdf']]
- Perdas de unidade (37): [['CG', 'animacao-v2'], ['CG', 'basico3d-py'], ['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python'], ['CG', 'colisao'], ['CG', 'exercicio-de-animacao-foguete'], ['CG', 'matematica'], ['CG', 'opengl3d'], ['CG', 'opengl3dcpp'], ['CG', 'opengl3dcpp-vdi'], ['CG', 'programabasico3d'], ['CG', 'transformacoesgeometricas'], ['CG', 'transformacoesgl'], ['ES2', 'roteiro1'], ['ES2', 'roteiro2'], ['ES2', 'roteiro3'], ['ES2', 'roteiro4'], ['ES2', 'roteiro5'], ['ES2', 'roteiro7'], ['ES2', 'roteiro7-history-service'], ['MF', 'colecoes-conjuntos'], ['MF', 'exemplos-zip'], ['MF', 'exercicioscorrecaoinducaomatematica'], ['MF', 'exerciciosespecificacao'], ['MF', 'exerciciosespecificacao-respostas'], ['MF', 'formalizacaoalgoritmos-recursao'], ['MF', 'logicaproposicional-sintaxe'], ['SO', '0206-laminas-mecanismos-de-interrupcao'], ['SO', '2306-laminas-laminas-armazenamento-em-massa'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-filho'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste01'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste02'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste03'], ['SO', 'exercicios-p2'], ['SO', 'lista-exercicios-p1']]
- Subunidade primaria: ganhos 0, perdas 21 -> [['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python'], ['CG', 'colisao'], ['CG', 'programabasico3d'], ['ES2', 'roteiro5'], ['ES2', 'roteiro6'], ['ES2', 'roteiro7'], ['ES2', 'roteiro7-history-service'], ['MF', 'exercicioscorrecaoinducaomatematica'], ['MF', 'exerciciosespecificacao'], ['MF', 'exerciciosespecificacao-respostas'], ['MF', 'exerciciosformalizacaoalgoritmosinvariantes'], ['MF', 'formalizacaoalgoritmos-recursao'], ['MF', 'logicadehoare'], ['MF', 'provasindutivas-especificacoesrecursivas'], ['MF', 'provasindutivas-especificacoesrecursivas-arvores'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste01'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste02'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste03']]
- Subunidade aceita: ganhos 0, perdas 23 -> [['CG', 'basico3d-py'], ['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python'], ['CG', 'colisao'], ['CG', 'exercicio-de-animacao-foguete'], ['CG', 'programabasico3d'], ['ES2', 'roteiro5'], ['ES2', 'roteiro6'], ['ES2', 'roteiro7'], ['ES2', 'roteiro7-history-service'], ['MF', 'exercicioscorrecaoinducaomatematica'], ['MF', 'exerciciosespecificacao'], ['MF', 'exerciciosespecificacao-respostas'], ['MF', 'exerciciosformalizacaoalgoritmosinvariantes'], ['MF', 'exerciciosisabelle2'], ['MF', 'formalizacaoalgoritmos-recursao'], ['MF', 'provasindutivas-especificacoesrecursivas'], ['MF', 'provasindutivas-especificacoesrecursivas-arvores'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste01'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste02'], ['SO', 'exemplo-criacao-de-processos-no-unix-linux-teste03']]
- Cursos que regridem: ['MF', 'SO', 'ES2', 'CG']
- Ids de unidade tocados (inclusive sem gold): 55; ids de subunidade tocados: 62
- Aceite: `{'bloco_217_237': True, 'nenhum_curso_regride': False, 'sub_aceita_107': False, 'sub_primaria_84': False, 'unidade_maior_igual_247': False, 'zero_perda_unidade': False}`

### R1_tau0.90

- Unidade por curso: CG 65, ES2 26, IA 39, MF 60, SO 30, TCC 17
- Ganhos de unidade (1): [['ES2', 'microsservicos7']]
- Perdas de unidade (10): [['CG', 'animacao-v2'], ['CG', 'basico3d-py'], ['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python'], ['CG', 'exercicio-de-animacao-foguete'], ['CG', 'matematica'], ['CG', 'transformacoesgl'], ['MF', 'exemplos-zip']]
- Subunidade primaria: ganhos 0, perdas 4 -> [['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python']]
- Subunidade aceita: ganhos 0, perdas 6 -> [['CG', 'basico3d-py'], ['CG', 'bezier-animacao'], ['CG', 'bezier-cpp'], ['CG', 'bezier-py'], ['CG', 'bezier-python'], ['CG', 'exercicio-de-animacao-foguete']]
- Cursos que regridem: ['MF', 'CG']
- Ids de unidade tocados (inclusive sem gold): 16; ids de subunidade tocados: 14
- Aceite: `{'bloco_217_237': True, 'nenhum_curso_regride': False, 'sub_aceita_107': False, 'sub_primaria_84': False, 'unidade_maior_igual_247': False, 'zero_perda_unidade': False}`

Conclusao medida: nenhuma das duas regras cumpre o aceite. A confianca do scorer de unidade nao ordena essa decisao - os 6 casos recuperaveis tem confianca 0.58-0.95 e os acertos que se perdem tambem estao acima de 0.90. No melhor tau (0.90) o saldo e +1 / -10 na unidade e -4 / -6 na subunidade primaria/aceita. A precedencia bloco > texto continua sendo o melhor agregado.

## 5. Efeito na subunidade do cru (84/107 de 251)

Medido pelo replay integral da cadeia unidade -> subunidade (a fase real `apply_unit_subunit_fields` decide os dois eixos na mesma passada), por curso, para cada variante - tabela da secao 4. Com R1 tau=0.90: primaria 84 -> 80, aceita 107 -> 101, todas as perdas no CG (`bezier-animacao`, `bezier-cpp`, `bezier-py`, `bezier-python`, `basico3d-py`, `exercicio-de-animacao-foguete`), zero ganho. Com R2: primaria 84 -> 63, aceita 107 -> 84, 21/23 perdas e nenhum ganho. Nenhum bloqueio de subunidade se desfaz com aceite: o unico bloqueio dentro da familia atacada, CG `exercicios-sobre-curvas-html`, so muda de unidade com tau <= 0.80, faixa em que a unidade global ja caiu para 236 ou menos.

## 6. O que fica

- **13 ausentes** (12 links + 1 PDF com `source_path` divergente): MF 4, IA 2, CG 7. Exigem entrada offline; nenhuma regra de motor os alcanca.
- **9 `herdada_do_bloco_errado`**: SO 1, ES2 1, CG 7. Dependem de CRU-04 (bloco certo primeiro). Destes, so 2 (SO `laminas-sockets-material-alternativo-em-pt`, ES2 `azure`) teriam o texto certo, e ambos com scorer AMBIGUO - nem a regra sem limiar os pega.
- **12 `herdada_do_bloco_certo_mas_gold_diverge`**: o bloco esta certo e a unidade do bloco diverge do gold curricular. E a fila de adjudicacao ja conhecida (`contradicoes_unidade_material_gt_vs_bloco.csv`), nao falha de sinal. 6 formam a familia medida e rejeitada acima; os outros 6 tem scorer errado ou ambiguo.
- **4 `texto_vence_errado`** (todos CG): 2 por `texto-vence-vizinho` (#48) e 2 sem bloco com unidade propria - custo conhecido da #48.
- **0 abstencoes** no eixo unidade.

## 7. sha256

- `wt_anatomia_unidade_49_22-09.json`: `1962ef5a51c134929d49e8e23f4f39c17026b2358757a2e5db1d605ab38e19e7`
- `wt_regra_unidade_22-09.json`: `01b73dc8dcd8baabfb0275494a2e1588151d1a2464490410ffd7f74401ca90b2`
- congelamento das decisoes (anatomia, antes do gold): `1b56f1dda165335a51d622b7e80eabaa65eceb2d45356e18098132e2f960c18e`
- congelamento das decisoes (7 variantes da regra): `93fac811a6e589584a378ce30d8d7935584f14abc8c8d73b47228beb4e75bd19`
- declaracao das regras, congelada antes de medir: `278ba0eec23432858d0102463bbc469632716426cc2e85457414d3fe7d076f0d`

## Limitacoes

- `scorer_bruto` e a saida de `auto_map_entry_unit` (pos-scorer, pre-reconciliacao). O ranking completo pre-gate nao e persistido.
- Ausentes permanecem no denominador em todos os eixos.
- LOCO so escolhe o limiar; os 7 cursos ja foram estudados e nao sao holdout novo.
- FR nao tem regua de unidade (0 no denominador); entra so nos eixos de bloco e subunidade.
