# W-S — guarda de escopo + declaracao por material (CRU-02, 22/09)

JSON: `ws_declaracao_por_material_22-09.json` sha256 `30faff12223f6db9b18378793b5badb36250a0ca9e88d5c8b1690666ad6b79bb` (sobrescrito a cada estado)  
Congelamento CAP-25 (herdado do W-P2') sha256 `38185c126de98f08b71d4fbbadd4f9176c877f3467a64916063785a4cdf4059d`  
Congelamento W-P1 sha256 `114c6f5efbfe16f3e4ca6b6af0d9713ccaac9182d485041cf917c3e9865d1af3`  
Estado: branch `feat/motor-atribuicao`, HEAD `b726d4c`, `src/` e `tests/` intocados.

## 1. Base (0 declaracoes, wrapper por entrada ativo)

- primaria 84/251, aceita 108/251, ausentes 8
- fidelidade do replay contra o manifest gravado: 329/329

| curso | n | primaria | aceita | ausente | alvos | perguntas CAP-25 |
|---|---|---|---|---|---|---|
| CG | 82 | 28 | 42 | 7 | 47 | 17 |
| ES2 | 28 | 7 | 8 | 0 | 21 | 7 |
| FR | 18 | 6 | 7 | 0 | 12 | 8 |
| IA | 39 | 4 | 5 | 0 | 35 | 12 |
| MF | 58 | 25 | 29 | 1 | 30 | 18 |
| SO | 15 | 7 | 8 | 0 | 8 | 8 |
| TCC | 11 | 7 | 9 | 0 | 4 | 6 |

## 2. Totais: variante x prefixo

| variante | prefixo | exam. expr | declaradas | depende | perg. material | custo | primaria/251 | (W-P2' sem guarda) | aceita/251 | ganhos | perdas | abst->dec (certas/erradas) | alvos corrigidos | tempo (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V-G | 5 | 35 | 6 | 29 | 0 | 35 | 100 | 99 | 124 | 16 | 0 | 1 (1/0) | 16/157 | 37.82 |
| V-G | 10 | 59 | 16 | 43 | 0 | 59 | 112 | 113 | 136 | 29 | 1 | 10 (7/3) | 29/157 | 39.74 |
| V-G | 20 | 76 | 27 | 49 | 0 | 76 | 127 | 118 | 148 | 45 | 2 | 16 (13/3) | 45/157 | 36.52 |
| V-G | 40 | 76 | 27 | 49 | 0 | 76 | 127 | 118 | 148 | 45 | 2 | 16 (13/3) | 45/157 | 36.52 |
| V-GM | 5 | 35 | 6 | 29 | 147 | 182 | 180 | 99 | 191 | 99 | 3 | 22 (20/2) | 99/157 | 51.57 |
| V-GM | 10 | 59 | 16 | 43 | 177 | 236 | 200 | 113 | 204 | 119 | 3 | 27 (25/2) | 119/157 | 58.01 |
| V-GM | 20 | 76 | 27 | 49 | 185 | 261 | 213 | 118 | 215 | 130 | 1 | 31 (29/2) | 130/157 | 64.97 |
| V-GM | 40 | 76 | 27 | 49 | 185 | 261 | 213 | 118 | 215 | 130 | 1 | 31 (29/2) | 130/157 | 64.97 |

## 3. Por curso

### V-G

| prefixo | curso | exam. | decl. | dep. | perg. mat. | custo | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | CG | 5 | 0 | 5 | 0 | 5 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.1 |
| 5 | ES2 | 5 | 1 | 4 | 0 | 5 | 9 | 10 | 2 | 0 | 0 (0/0) | 2/21 | 2.46 |
| 5 | FR | 5 | 1 | 4 | 0 | 5 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 1.04 |
| 5 | IA | 5 | 1 | 4 | 0 | 5 | 12 | 13 | 8 | 0 | 0 (0/0) | 8/35 | 10.56 |
| 5 | MF | 5 | 0 | 5 | 0 | 5 | 25 | 29 | 0 | 0 | 0 (0/0) | 0/30 | 15.76 |
| 5 | SO | 5 | 2 | 3 | 0 | 5 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 1.88 |
| 5 | TCC | 5 | 1 | 4 | 0 | 5 | 7 | 9 | 0 | 0 | 0 (0/0) | 0/4 | 3.02 |
| 10 | CG | 10 | 1 | 9 | 0 | 10 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 2.39 |
| 10 | ES2 | 7 | 2 | 5 | 0 | 7 | 11 | 13 | 4 | 0 | 0 (0/0) | 4/21 | 2.35 |
| 10 | FR | 8 | 2 | 6 | 0 | 8 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.79 |
| 10 | IA | 10 | 3 | 7 | 0 | 10 | 18 | 19 | 14 | 0 | 0 (0/0) | 14/35 | 11.87 |
| 10 | MF | 10 | 2 | 8 | 0 | 10 | 31 | 34 | 6 | 0 | 5 (5/0) | 6/30 | 17.1 |
| 10 | SO | 8 | 4 | 4 | 0 | 8 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.13 |
| 10 | TCC | 6 | 2 | 4 | 0 | 6 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 3.11 |
| 20 | CG | 17 | 5 | 12 | 0 | 17 | 30 | 42 | 2 | 0 | 0 (0/0) | 2/47 | 2.28 |
| 20 | ES2 | 7 | 2 | 5 | 0 | 7 | 11 | 13 | 4 | 0 | 0 (0/0) | 4/21 | 2.35 |
| 20 | FR | 8 | 2 | 6 | 0 | 8 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.79 |
| 20 | IA | 12 | 4 | 8 | 0 | 12 | 19 | 20 | 15 | 0 | 0 (0/0) | 15/35 | 9.48 |
| 20 | MF | 18 | 8 | 10 | 0 | 18 | 43 | 45 | 19 | 1 | 11 (11/0) | 19/30 | 16.38 |
| 20 | SO | 8 | 4 | 4 | 0 | 8 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.13 |
| 20 | TCC | 6 | 2 | 4 | 0 | 6 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 3.11 |
| 40 | CG | 17 | 5 | 12 | 0 | 17 | 30 | 42 | 2 | 0 | 0 (0/0) | 2/47 | 2.28 |
| 40 | ES2 | 7 | 2 | 5 | 0 | 7 | 11 | 13 | 4 | 0 | 0 (0/0) | 4/21 | 2.35 |
| 40 | FR | 8 | 2 | 6 | 0 | 8 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.79 |
| 40 | IA | 12 | 4 | 8 | 0 | 12 | 19 | 20 | 15 | 0 | 0 (0/0) | 15/35 | 9.48 |
| 40 | MF | 18 | 8 | 10 | 0 | 18 | 43 | 45 | 19 | 1 | 11 (11/0) | 19/30 | 16.38 |
| 40 | SO | 8 | 4 | 4 | 0 | 8 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.13 |
| 40 | TCC | 6 | 2 | 4 | 0 | 6 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 3.11 |

### V-GM

| prefixo | curso | exam. | decl. | dep. | perg. mat. | custo | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | CG | 5 | 0 | 5 | 42 | 47 | 50 | 57 | 22 | 0 | 6 (6/0) | 22/47 | 2.62 |
| 5 | ES2 | 5 | 1 | 4 | 23 | 28 | 25 | 25 | 18 | 0 | 4 (3/1) | 18/21 | 5.33 |
| 5 | FR | 5 | 1 | 4 | 11 | 16 | 16 | 17 | 10 | 0 | 2 (2/0) | 10/12 | 1.66 |
| 5 | IA | 5 | 1 | 4 | 28 | 33 | 31 | 31 | 27 | 0 | 0 (0/0) | 27/35 | 15.43 |
| 5 | MF | 5 | 0 | 5 | 31 | 36 | 38 | 41 | 16 | 3 | 8 (7/1) | 16/30 | 20.77 |
| 5 | SO | 5 | 2 | 3 | 5 | 10 | 9 | 9 | 2 | 0 | 1 (1/0) | 2/8 | 1.68 |
| 5 | TCC | 5 | 1 | 4 | 7 | 12 | 11 | 11 | 4 | 0 | 1 (1/0) | 4/4 | 4.08 |
| 10 | CG | 10 | 1 | 9 | 54 | 64 | 56 | 60 | 28 | 0 | 6 (6/0) | 28/47 | 3.42 |
| 10 | ES2 | 7 | 2 | 5 | 25 | 32 | 25 | 25 | 18 | 0 | 4 (3/1) | 18/21 | 9.88 |
| 10 | FR | 8 | 2 | 6 | 14 | 22 | 17 | 17 | 11 | 0 | 2 (2/0) | 11/12 | 1.66 |
| 10 | IA | 10 | 3 | 7 | 33 | 43 | 37 | 37 | 33 | 0 | 0 (0/0) | 33/35 | 16.72 |
| 10 | MF | 10 | 2 | 8 | 38 | 48 | 45 | 45 | 22 | 2 | 11 (11/0) | 22/30 | 19.34 |
| 10 | SO | 8 | 4 | 4 | 6 | 14 | 10 | 10 | 3 | 0 | 2 (2/0) | 3/8 | 1.58 |
| 10 | TCC | 6 | 2 | 4 | 7 | 13 | 10 | 10 | 4 | 1 | 2 (1/1) | 4/4 | 5.41 |
| 20 | CG | 17 | 5 | 12 | 59 | 76 | 59 | 61 | 31 | 0 | 6 (6/0) | 31/47 | 3.02 |
| 20 | ES2 | 7 | 2 | 5 | 25 | 32 | 25 | 25 | 18 | 0 | 4 (3/1) | 18/21 | 9.88 |
| 20 | FR | 8 | 2 | 6 | 14 | 22 | 17 | 17 | 11 | 0 | 2 (2/0) | 11/12 | 1.66 |
| 20 | IA | 12 | 4 | 8 | 34 | 46 | 39 | 39 | 35 | 0 | 0 (0/0) | 35/35 | 16.81 |
| 20 | MF | 18 | 8 | 10 | 40 | 58 | 53 | 53 | 28 | 0 | 15 (15/0) | 28/30 | 26.61 |
| 20 | SO | 8 | 4 | 4 | 6 | 14 | 10 | 10 | 3 | 0 | 2 (2/0) | 3/8 | 1.58 |
| 20 | TCC | 6 | 2 | 4 | 7 | 13 | 10 | 10 | 4 | 1 | 2 (1/1) | 4/4 | 5.41 |
| 40 | CG | 17 | 5 | 12 | 59 | 76 | 59 | 61 | 31 | 0 | 6 (6/0) | 31/47 | 3.02 |
| 40 | ES2 | 7 | 2 | 5 | 25 | 32 | 25 | 25 | 18 | 0 | 4 (3/1) | 18/21 | 9.88 |
| 40 | FR | 8 | 2 | 6 | 14 | 22 | 17 | 17 | 11 | 0 | 2 (2/0) | 11/12 | 1.66 |
| 40 | IA | 12 | 4 | 8 | 34 | 46 | 39 | 39 | 35 | 0 | 0 (0/0) | 35/35 | 16.81 |
| 40 | MF | 18 | 8 | 10 | 40 | 58 | 53 | 53 | 28 | 0 | 15 (15/0) | 28/30 | 26.61 |
| 40 | SO | 8 | 4 | 4 | 6 | 14 | 10 | 10 | 3 | 0 | 2 (2/0) | 3/8 | 1.58 |
| 40 | TCC | 6 | 2 | 4 | 7 | 13 | 10 | 10 | 4 | 1 | 2 (1/1) | 4/4 | 5.41 |

## 4. Perdas (declaracao derruba material hoje certo)

| variante | prefixo | curso | gold_id | base | novo | gold primario |
|---|---|---|---|---|---|---|
| V-G | 10 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| V-G | 20 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| V-G | 20 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| V-G | 40 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| V-G | 40 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| V-GM | 5 | MF | conjuntosindutivos | `especificacao-de-conjuntos-indutivos` | `especificacao-de-funcoes-recursivas` | especificacao-de-conjuntos-indutivos |
| V-GM | 5 | MF | exerciciosespecificacao-respostas | `linguagens-de-especificacao-e-logicas` | `fundamentos-de-logica-de-primeira-ordem` | linguagens-de-especificacao-e-logicas |
| V-GM | 5 | MF | exerciciosespecificacao | `linguagens-de-especificacao-e-logicas` | `fundamentos-de-logica-de-primeira-ordem` | linguagens-de-especificacao-e-logicas |
| V-GM | 10 | MF | exerciciosespecificacao-respostas | `linguagens-de-especificacao-e-logicas` | `fundamentos-de-logica-de-primeira-ordem` | linguagens-de-especificacao-e-logicas |
| V-GM | 10 | MF | exerciciosespecificacao | `linguagens-de-especificacao-e-logicas` | `fundamentos-de-logica-de-primeira-ordem` | linguagens-de-especificacao-e-logicas |
| V-GM | 10 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| V-GM | 20 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| V-GM | 40 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |

## 5. Teto analitico (materiais que V-GM esgotada nao alcanca)

- alcancaveis 211/251; causas: {'bloqueio_pela_unidade': 17, 'entry_ausente': 8, 'nao_alcancado_pela_ordem': 9, 'sem_gold_primario': 6}

| curso | n | alcancavel | entry ausente | sem gold | gold fora da taxonomia | bloqueio pela unidade | nao alcancado pela ordem |
|---|---|---|---|---|---|---|---|
| CG | 82 | 59 | 7 | 5 | 0 | 9 | 2 |
| ES2 | 28 | 25 | 0 | 0 | 0 | 3 | 0 |
| FR | 18 | 17 | 0 | 0 | 0 | 0 | 1 |
| IA | 39 | 39 | 0 | 0 | 0 | 0 | 0 |
| MF | 58 | 53 | 1 | 0 | 0 | 0 | 4 |
| SO | 15 | 8 | 0 | 0 | 0 | 5 | 2 |
| TCC | 11 | 10 | 0 | 1 | 0 | 0 | 0 |

## 5b. Marcos 50/80% dos alvos por CORRECAO EFETIVA (custo = expressao + material)

| variante | marco | prefixo | custo | corrigidos/alvos | primaria/251 |
|---|---|---|---|---|---|
| V-G | p50 | nao atingido | - | - | - |
| V-G | p80 | nao atingido | - | - | - |
| V-G | final (ordem esgotada) | 40 | 76 | 45/157 (28.7%) | - |
| V-GM | p50 | 5 | 182 | 99/157 | 180 |
| V-GM | p80 | 20 | 261 | 130/157 | 213 |
| V-GM | final (ordem esgotada) | 40 | 261 | 130/157 (82.8%) | - |

Por curso (ordem esgotada e marcos):

| variante | curso | alvos | corrigidos finais | % | custo final | p50 (prefixo/custo) | p80 (prefixo/custo) |
|---|---|---|---|---|---|---|---|
| V-G | CG | 47 | 2 | 4.3 | 17 | - | - |
| V-G | ES2 | 21 | 4 | 19.0 | 7 | - | - |
| V-G | FR | 12 | 3 | 25.0 | 8 | - | - |
| V-G | IA | 35 | 15 | 42.9 | 12 | - | - |
| V-G | MF | 30 | 19 | 63.3 | 18 | 20/18 | - |
| V-G | SO | 8 | 2 | 25.0 | 8 | - | - |
| V-G | TCC | 4 | 0 | 0.0 | 6 | - | - |
| V-GM | CG | 47 | 31 | 66.0 | 76 | 10/64 | - |
| V-GM | ES2 | 21 | 18 | 85.7 | 32 | 5/28 | 5/28 |
| V-GM | FR | 12 | 11 | 91.7 | 22 | 5/16 | 5/16 |
| V-GM | IA | 35 | 35 | 100.0 | 46 | 5/33 | 10/43 |
| V-GM | MF | 30 | 28 | 93.3 | 58 | 5/36 | 20/58 |
| V-GM | SO | 8 | 3 | 37.5 | 14 | - | - |
| V-GM | TCC | 4 | 4 | 100.0 | 13 | 5/12 | 5/12 |

## 6. Perguntas por material feitas (V-GM, prefixos 5 e 10)

### prefixo 5

| curso | expr. que gerou | gold_id | gold primario | resposta | topico | n aliases |
|---|---|---|---|---|---|---|
| CG | `videos` | pagina-com-videos-sobre-curvas-parametricas-63d902 | representacao-de-curvas-parametricas | declara | representacao-de-curvas-parametricas | 8 |
| CG | `videos` | pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9 | entidades-geometricas | declara | entidades-geometricas | 10 |
| CG | `videos` | pagina-com-videos-sobre-geometria-computacional-ebca9a | algoritmos-de-geometria-computacional | declara | algoritmos-de-geometria-computacional | 8 |
| CG | `videos` | pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156 | introducao-e-exemplos-de-aplicacoes | declara | introducao-e-exemplos-de-aplicacoes | 12 |
| CG | `videos` | pagina-com-videos-sobre-manipulacao-de-imagens-61ddde | cores-e-tipos-de-imagens | declara | cores-e-tipos-de-imagens | 11 |
| CG | `videos` | pagina-com-videos-sobre-mapeamento-9f410e | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 8 |
| CG | `videos` | pagina-com-videos-sobre-morfologia-matematica-06265a | segmentacao | declara | segmentacao | 12 |
| CG | `videos` | pagina-com-videos-sobre-recorte-e257d3 | recorte | declara | recorte | 8 |
| CG | `videos` | pagina-com-videos-sobre-remocao-de-elementos-ocultos-20c34a | algoritmos-de-remocao-de-elementos-ocultos | declara | algoritmos-de-remocao-de-elementos-ocultos | 9 |
| CG | `videos` | pagina-com-videos-sobre-segmentacao-de-imagens-d0627f | segmentacao | declara | segmentacao | 44 |
| CG | `videos` | pagina-com-videos-sobre-segmentacao-por-texturas-e03566 | segmentacao | declara | segmentacao | 10 |
| CG | `videos` | pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea | modelos-de-iluminacao-luz-pontual-direcional-spot | declara | modelos-de-iluminacao-luz-pontual-direcional-spot | 14 |
| CG | `videos` | pagina-com-videos-sobre-visualizacao-3d-35a833 | pipeline-de-visualizacao-3d | declara | pipeline-de-visualizacao-3d | 8 |
| CG | `videos` | paginas-com-videos-sobre-modelagem-geometrica-f2614a | tecnicas-de-modelagem-3d | declara | tecnicas-de-modelagem-3d | 10 |
| CG | `videos` | videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84 | algoritmos-de-deteccao-e-calculo-de-interseccao | declara | algoritmos-de-deteccao-e-calculo-de-interseccao | 9 |
| CG | `ponto` | basico3d-py | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 24 |
| CG | `ponto` | basico3d-py-zip | tecnicas-de-modelagem-3d | declara | tecnicas-de-modelagem-3d | 23 |
| CG | `ponto` | bezier-animacao | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 42 |
| CG | `ponto` | bezier-python | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 28 |
| CG | `ponto` | exerciciosfundamentosmatematicos | algoritmos-de-poligonos | declara | algoritmos-de-poligonos | 21 |
| CG | `ponto` | fundamentosmatematicos | entidades-geometricas | declara | entidades-geometricas | 64 |
| CG | `ponto` | opengl-py | aplicacoes | declara | aplicacoes | 35 |
| CG | `ponto` | vis3d | projecoes | declara | projecoes | 32 |
| CG | `opengl` | elemoculto | algoritmos-de-remocao-de-elementos-ocultos | declara | algoritmos-de-remocao-de-elementos-ocultos | 42 |
| CG | `opengl` | exercicios | aplicacoes | declara | aplicacoes | 3 |
| CG | `opengl` | opengl-cpp | aplicacoes | declara | aplicacoes | 45 |
| CG | `opengl` | opengl3d | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 96 |
| CG | `opengl` | opengl3dcpp | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 52 |
| CG | `opengl` | opengl3dcpp-vdi | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 49 |
| CG | `opengl` | openglbasico | aplicacoes | declara | aplicacoes | 97 |
| CG | `proces` | exercicios-de-processamento-de-imagens | algoritmos-de-quantizacao-e-amostragem | declara | algoritmos-de-quantizacao-e-amostragem | 22 |
| CG | `proces` | exercicios-teoricos-sobre-processo-de-visualizacao-2d | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 7 |
| CG | `proces` | exercicios-teoricos-sobre-processo-de-visualizacao-2d-html | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 7 |
| CG | `proces` | mapeamento | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 33 |
| CG | `proces` | recorte | recorte | declara | recorte | 17 |
| CG | `proces` | vis2d | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 8 |
| CG | `slides` | colisao | algoritmos-de-deteccao-e-calculo-de-interseccao | declara | algoritmos-de-deteccao-e-calculo-de-interseccao | 63 |
| CG | `slides` | curvasparametricas | representacao-de-curvas-parametricas | declara | representacao-de-curvas-parametricas | 13 |
| CG | `slides` | introducaoprocimg | filtros | declara | filtros | 24 |
| CG | `slides` | morfologiamatematicapptx | segmentacao | declara | segmentacao | 7 |
| CG | `slides` | origensdacomputacaografica | origens | declara | origens | 24 |
| CG | `slides` | segmentacaopptx | segmentacao | declara | segmentacao | 36 |
| ES2 | `projet` | microsservicos | orientada-a-microsservicos | declara | orientada-a-microsservicos | 63 |
| ES2 | `projet` | microsservicos2 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 32 |
| ES2 | `projet` | microsservicos3 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 10 |
| ES2 | `projet` | microsservicos4 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 15 |
| ES2 | `projet` | microsservicos5 | plataformas-de-devops | declara | plataformas-de-devops | 63 |
| ES2 | `projet` | microsservicos7 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 42 |
| ES2 | `projet` | revisaoarquiteturapadroes | conceito-de-arquitetura-de-software | declara | conceito-de-arquitetura-de-software | 128 |
| ES2 | `basead prof bernar` | roteiro1-introducao | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 46 |
| ES2 | `basead prof bernar` | roteiro2-nameserver | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 50 |
| ES2 | `basead prof bernar` | roteiro3-gateway | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 39 |
| ES2 | `basead prof bernar` | roteiro4-circuitbreaker | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 76 |
| ES2 | `basead prof bernar` | roteiro5-conteiners | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 137 |
| ES2 | `basead prof bernar` | roteiro6-conteiners-composicao | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 34 |
| ES2 | `basead prof bernar` | roteiro7-filas | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 51 |
| ES2 | `applic curren` | roteiro1 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 43 |
| ES2 | `applic curren` | roteiro2 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 43 |
| ES2 | `applic curren` | roteiro3 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 51 |
| ES2 | `applic curren` | roteiro4 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro5 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro6 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro7 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `execut` | devops | conceito-de-devops | declara | conceito-de-devops | 125 |
| ES2 | `execut` | kubernetes | plataformas-de-devops | declara | plataformas-de-devops | 15 |
| FR | `format` | 02-modelos-de-referencia | modelos-osi-e-tcpip | declara | modelos-osi-e-tcpip | 96 |
| FR | `format` | 04-protocolo-http | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 81 |
| FR | `format` | 05-protocolo-dns | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 120 |
| FR | `format` | 07-protocolos-de-e-mail | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 114 |
| FR | `proces` | 04-camada-de-aplicacao | funcoes-e-caracteristicas-do-nivel-de-aplicacao | declara | funcoes-e-caracteristicas-do-nivel-de-aplicacao | 28 |
| FR | `proces` | 06-protocolo-dhcp | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 79 |
| FR | `proces` | 08-desenvolvimento-de-aplicacoes | implementacao-de-sockets | declara | implementacao-de-sockets | 22 |
| FR | `cache` | unidade2-exercicios-dns | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 12 |
| FR | `cache` | unidade2-exercicios-http | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 20 |
| FR | `protoc rede` | 01-protocolos-de-rede | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | declara | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | 64 |
| FR | `protoc rede` | unidade1-exercicios | modelos-osi-e-tcpip | declara | modelos-osi-e-tcpip | 9 |
| IA | `visual` | agrupamento-hierarquico-exemplo-1 | modelos-descritivos | declara | modelos-descritivos | 98 |
| IA | `visual` | agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris | modelos-descritivos | declara | modelos-descritivos | 102 |
| IA | `visual` | agrupamento-usando-k-means-exemplo-1-ipynb | modelos-descritivos | declara | modelos-descritivos | 101 |
| IA | `visual` | agrupamento-usando-k-means-exemplo-2-ipynb | modelos-descritivos | declara | modelos-descritivos | 41 |
| IA | `visual` | arvores-de-decisao | modelos-preditivos | declara | modelos-preditivos | 225 |
| IA | `visual` | exemplo-1-arvores-de-decisao-classificacao-planta-iris | modelos-preditivos | declara | modelos-preditivos | 114 |
| IA | `visual` | exemplo-2-arvores-de-decisao-regressao-diabetes | modelos-preditivos | declara | modelos-preditivos | 106 |
| IA | `visual` | exemplo-complementar-classificacao-com-arvores-de-decisao | modelos-preditivos | declara | modelos-preditivos | 67 |
| IA | `analis` | analise-exploratoria-de-dados-exemplo-1 | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 75 |
| IA | `analis` | analise-exploratoria-dos-dados-exemplo-2 | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 18 |
| IA | `analis` | artigo-usando-k-nn-em-texto | modelos-preditivos | declara | modelos-preditivos | 62 |
| IA | `analis` | aula-sobre-agrupamento-parte-2-hierarquico | modelos-descritivos | declara | modelos-descritivos | 27 |
| IA | `analis` | caracteristicas-dos-dados | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 179 |
| IA | `analis` | como-analisar-resultados-acc-pr-re-e-f1 | metricas-de-avaliacao | declara | metricas-de-avaliacao | 60 |
| IA | `artifi` | algoritmo-de-classificacao-k-nn | modelos-preditivos | declara | modelos-preditivos | 32 |
| IA | `artifi` | aula-sobre-agrupamento-parte-1-particional | modelos-descritivos | declara | modelos-descritivos | 28 |
| IA | `artifi` | introducao-a-ml | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 54 |
| IA | `artifi` | introducao-a-redes-neurais | modelos-preditivos | declara | modelos-preditivos | 179 |
| IA | `artifi` | mlp | modelos-preditivos | declara | modelos-preditivos | 146 |
| IA | `artifi` | rede-perceptron | modelos-preditivos | declara | modelos-preditivos | 228 |
| IA | `print` | exemplo-2-k-nn-com-iriscsv-mais-completo | modelos-preditivos | declara | modelos-preditivos | 17 |
| IA | `print` | exercicio-2-solucao-com-rede-perceptron-atualizado | modelos-preditivos | declara | modelos-preditivos | 50 |
| IA | `print` | k-nn-para-classificacao-exemplo-cardio | modelos-preditivos | declara | modelos-preditivos | 18 |
| IA | `print` | mlp-classificacao-iris-atualizado | modelos-preditivos | declara | modelos-preditivos | 36 |
| IA | `print` | rede-perceptron-classificacao-de-cliente | modelos-preditivos | declara | modelos-preditivos | 39 |
| IA | `print` | rede-perceptron-classificacao-planta-iris | modelos-preditivos | declara | modelos-preditivos | 55 |
| IA | `print` | rede-perceptron-exemplo-atualizado | modelos-preditivos | declara | modelos-preditivos | 33 |
| IA | `print` | rede-perceptron-or-em-python | modelos-preditivos | declara | modelos-preditivos | 25 |
| MF | `formal` | exerciciosformalizacaoalgoritmosinvariantes | invariante-e-variante-de-laco | declara | invariante-e-variante-de-laco | 15 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao2 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao3 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosisabelle | provadores-de-teoremas | declara | provadores-de-teoremas | 27 |
| MF | `formal` | exerciciosisabelle2 | provadores-de-teoremas | declara | provadores-de-teoremas | 27 |
| MF | `formal` | formalizacaoalgoritmos-invarianteslaco | invariante-e-variante-de-laco | declara | invariante-e-variante-de-laco | 26 |
| MF | `formal` | formalizacaoalgoritmos-recursao | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 34 |
| MF | `formal` | formalizacaoalgoritmos-recursao2 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | formalizacaoalgoritmos-recursao3 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 25 |
| MF | `formal` | logicapredicados-sintaxe | fundamentos-de-logica-de-primeira-ordem | declara | fundamentos-de-logica-de-primeira-ordem | 15 |
| MF | `provas` | arvores | provadores-de-teoremas | declara | provadores-de-teoremas | 5 |
| MF | `provas` | exercicioscorrecaoinducaomatematica | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 16 |
| MF | `provas` | listas | provadores-de-teoremas | declara | provadores-de-teoremas | 2 |
| MF | `provas` | provas | provadores-de-teoremas | declara | provadores-de-teoremas | 7 |
| MF | `provas` | provasindutivas-especificacoesrecursivas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 26 |
| MF | `provas` | provasindutivas-especificacoesrecursivas-arvores | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 18 |
| MF | `provas` | provasindutivas-especificacoesrecursivas-listas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 12 |
| MF | `progra` | exerciciosdafny1 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 9 |
| MF | `progra` | exerciciosdafny2 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 13 |
| MF | `progra` | exerciciosdafny3 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 15 |
| MF | `progra` | exerciciosdafny4 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 19 |
| MF | `progra` | exerciciosdafny5 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 13 |
| MF | `progra` | logicadehoare | logica-de-hoare | declara | logica-de-hoare | 40 |
| MF | `logica` | logicadehoare-exercicios-respostas | logica-de-hoare | declara | logica-de-hoare | 4 |
| MF | `logica` | logicapredicados-semantica | fundamentos-de-logica-de-primeira-ordem | declara | fundamentos-de-logica-de-primeira-ordem | 14 |
| MF | `logica` | logicaproposicional-semantica | linguagens-de-especificacao-e-logicas | declara | linguagens-de-especificacao-e-logicas | 41 |
| MF | `logica` | logicaproposicional-sintaxe | linguagens-de-especificacao-e-logicas | declara | linguagens-de-especificacao-e-logicas | 10 |
| MF | `arrays` | colecoes-arrays | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 3 |
| MF | `arrays` | exercicios-arrays | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 1 |
| MF | `arrays` | logicadehoare2 | logica-de-hoare | declara | logica-de-hoare | 14 |
| SO | `estado` | 1203-processos | chamadas-de-sistema | declara | chamadas-de-sistema | 25 |
| SO | `estado` | 1903-estruturas-de-controle | conceitos-basicos | declara | conceitos-basicos | 32 |
| SO | `multip` | 2603-algoritmos-de-escalonamento | algoritmos-de-escalonamento | declara | algoritmos-de-escalonamento | 31 |
| SO | `multip` | definicao-e-historico | evolucao-historica | declara | evolucao-historica | 42 |
| SO | `contex` | 2403-escalonamento-de-processos | escalonamento | declara | escalonamento | 20 |
| TCC | `cadeia` | aula-08-maquinas-de-turing-como-processadoras-de-funcoes | conjectura-de-church-turing | declara | conjectura-de-church-turing | 96 |
| TCC | `relac` | aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade | conjuntos-enumeraveis | declara | conjuntos-enumeraveis | 86 |
| TCC | `relac` | aula-07-maquinas-de-turing-e-linguagens-recursivamente-enumeraveis | maquinas-de-turing | declara | maquinas-de-turing | 105 |
| TCC | `fitas` | aula-09-variacoes-de-maquinas-de-turing | variacoes-de-maquinas-de-turing | declara | variacoes-de-maquinas-de-turing | 81 |
| TCC | `fitas` | aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf | linguagens-reconheciveis-e-decidiveis | declara | linguagens-reconheciveis-e-decidiveis | 101 |
| TCC | `centra` | aula-02-conjuntos-enumeraveis-e-nao-enumeraveis-argumento-da-diagonalizacao-de-cantor | argumento-diagonal-de-cantor-e-conjuntos-incontaveis | declara | argumento-diagonal-de-cantor-e-conjuntos-incontaveis | 120 |
| TCC | `centra` | aula-03-funcoes-recursivas-primitivas-e-composicao-de-funcoes | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais | 119 |

### prefixo 10

| curso | expr. que gerou | gold_id | gold primario | resposta | topico | n aliases |
|---|---|---|---|---|---|---|
| CG | `videos` | pagina-com-videos-sobre-curvas-parametricas-63d902 | representacao-de-curvas-parametricas | declara | representacao-de-curvas-parametricas | 8 |
| CG | `videos` | pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9 | entidades-geometricas | declara | entidades-geometricas | 10 |
| CG | `videos` | pagina-com-videos-sobre-geometria-computacional-ebca9a | algoritmos-de-geometria-computacional | declara | algoritmos-de-geometria-computacional | 8 |
| CG | `videos` | pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156 | introducao-e-exemplos-de-aplicacoes | declara | introducao-e-exemplos-de-aplicacoes | 12 |
| CG | `videos` | pagina-com-videos-sobre-manipulacao-de-imagens-61ddde | cores-e-tipos-de-imagens | declara | cores-e-tipos-de-imagens | 11 |
| CG | `videos` | pagina-com-videos-sobre-mapeamento-9f410e | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 8 |
| CG | `videos` | pagina-com-videos-sobre-morfologia-matematica-06265a | segmentacao | declara | segmentacao | 12 |
| CG | `videos` | pagina-com-videos-sobre-recorte-e257d3 | recorte | declara | recorte | 8 |
| CG | `videos` | pagina-com-videos-sobre-remocao-de-elementos-ocultos-20c34a | algoritmos-de-remocao-de-elementos-ocultos | declara | algoritmos-de-remocao-de-elementos-ocultos | 9 |
| CG | `videos` | pagina-com-videos-sobre-segmentacao-de-imagens-d0627f | segmentacao | declara | segmentacao | 44 |
| CG | `videos` | pagina-com-videos-sobre-segmentacao-por-texturas-e03566 | segmentacao | declara | segmentacao | 10 |
| CG | `videos` | pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea | modelos-de-iluminacao-luz-pontual-direcional-spot | declara | modelos-de-iluminacao-luz-pontual-direcional-spot | 14 |
| CG | `videos` | pagina-com-videos-sobre-visualizacao-3d-35a833 | pipeline-de-visualizacao-3d | declara | pipeline-de-visualizacao-3d | 8 |
| CG | `videos` | paginas-com-videos-sobre-modelagem-geometrica-f2614a | tecnicas-de-modelagem-3d | declara | tecnicas-de-modelagem-3d | 10 |
| CG | `videos` | videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84 | algoritmos-de-deteccao-e-calculo-de-interseccao | declara | algoritmos-de-deteccao-e-calculo-de-interseccao | 9 |
| CG | `ponto` | basico3d-py | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 24 |
| CG | `ponto` | basico3d-py-zip | tecnicas-de-modelagem-3d | declara | tecnicas-de-modelagem-3d | 23 |
| CG | `ponto` | bezier-animacao | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 42 |
| CG | `ponto` | bezier-python | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 28 |
| CG | `ponto` | exerciciosfundamentosmatematicos | algoritmos-de-poligonos | declara | algoritmos-de-poligonos | 21 |
| CG | `ponto` | fundamentosmatematicos | entidades-geometricas | declara | entidades-geometricas | 64 |
| CG | `ponto` | opengl-py | aplicacoes | declara | aplicacoes | 35 |
| CG | `ponto` | vis3d | projecoes | declara | projecoes | 32 |
| CG | `opengl` | elemoculto | algoritmos-de-remocao-de-elementos-ocultos | declara | algoritmos-de-remocao-de-elementos-ocultos | 42 |
| CG | `opengl` | exercicios | aplicacoes | declara | aplicacoes | 3 |
| CG | `opengl` | opengl-cpp | aplicacoes | declara | aplicacoes | 45 |
| CG | `opengl` | opengl3d | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 96 |
| CG | `opengl` | opengl3dcpp | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 52 |
| CG | `opengl` | opengl3dcpp-vdi | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 49 |
| CG | `opengl` | openglbasico | aplicacoes | declara | aplicacoes | 97 |
| CG | `proces` | exercicios-de-processamento-de-imagens | algoritmos-de-quantizacao-e-amostragem | declara | algoritmos-de-quantizacao-e-amostragem | 22 |
| CG | `proces` | exercicios-teoricos-sobre-processo-de-visualizacao-2d | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 7 |
| CG | `proces` | exercicios-teoricos-sobre-processo-de-visualizacao-2d-html | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 7 |
| CG | `proces` | mapeamento | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 33 |
| CG | `proces` | recorte | recorte | declara | recorte | 17 |
| CG | `proces` | vis2d | sistema-de-coordenadas-cartesianas | declara | sistema-de-coordenadas-cartesianas | 8 |
| CG | `slides` | colisao | algoritmos-de-deteccao-e-calculo-de-interseccao | declara | algoritmos-de-deteccao-e-calculo-de-interseccao | 63 |
| CG | `slides` | curvasparametricas | representacao-de-curvas-parametricas | declara | representacao-de-curvas-parametricas | 13 |
| CG | `slides` | introducaoprocimg | filtros | declara | filtros | 24 |
| CG | `slides` | morfologiamatematicapptx | segmentacao | declara | segmentacao | 7 |
| CG | `slides` | origensdacomputacaografica | origens | declara | origens | 24 |
| CG | `slides` | segmentacaopptx | segmentacao | declara | segmentacao | 36 |
| CG | `ativid` | atividade | conceito-de-camera-sintetica | declara | conceito-de-camera-sintetica | 3 |
| CG | `ativid` | exerciciodemodelagem | varredura | declara | varredura | 33 |
| CG | `ativid` | floodfill | segmentacao | declara | segmentacao | 8 |
| CG | `ativid` | remocaoderuido | filtros | declara | filtros | 6 |
| CG | `codigo` | bezier-cpp | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 13 |
| CG | `codigo` | bezier-py | bezier-e-algoritmo-de-casteljau | declara | bezier-e-algoritmo-de-casteljau | 16 |
| CG | `codigo` | programabasico3d | modelos-de-reflexao-ambiente-difusa-especular | declara | modelos-de-reflexao-ambiente-difusa-especular | 25 |
| CG | `manipu imagen` | basico3d-cpp | tecnicas-de-modelagem-3d | declara | tecnicas-de-modelagem-3d | 48 |
| CG | `manipu imagen` | exercicioduascores | algoritmos-de-quantizacao-e-amostragem | declara | algoritmos-de-quantizacao-e-amostragem | 7 |
| CG | `manipu imagen` | img | cores-e-tipos-de-imagens | declara | cores-e-tipos-de-imagens | 7 |
| CG | `animac` | exercicio-com-animacao | operacoes-com-vetores | declara | operacoes-com-vetores | 2 |
| CG | `animac` | exercicio-de-animacao-foguete | operacoes-com-vetores | declara | operacoes-com-vetores | 4 |
| ES2 | `projet` | microsservicos | orientada-a-microsservicos | declara | orientada-a-microsservicos | 63 |
| ES2 | `projet` | microsservicos2 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 32 |
| ES2 | `projet` | microsservicos3 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 10 |
| ES2 | `projet` | microsservicos4 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 15 |
| ES2 | `projet` | microsservicos5 | plataformas-de-devops | declara | plataformas-de-devops | 63 |
| ES2 | `projet` | microsservicos7 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 42 |
| ES2 | `projet` | revisaoarquiteturapadroes | conceito-de-arquitetura-de-software | declara | conceito-de-arquitetura-de-software | 128 |
| ES2 | `basead prof bernar` | roteiro1-introducao | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 46 |
| ES2 | `basead prof bernar` | roteiro2-nameserver | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 50 |
| ES2 | `basead prof bernar` | roteiro3-gateway | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 39 |
| ES2 | `basead prof bernar` | roteiro4-circuitbreaker | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 76 |
| ES2 | `basead prof bernar` | roteiro5-conteiners | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 137 |
| ES2 | `basead prof bernar` | roteiro6-conteiners-composicao | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 34 |
| ES2 | `basead prof bernar` | roteiro7-filas | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 51 |
| ES2 | `applic curren` | roteiro1 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 43 |
| ES2 | `applic curren` | roteiro2 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 43 |
| ES2 | `applic curren` | roteiro3 | estudo-de-caso-arquitetura-orientada-a-microsservicos | declara | estudo-de-caso-arquitetura-orientada-a-microsservicos | 51 |
| ES2 | `applic curren` | roteiro4 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro5 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro6 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `applic curren` | roteiro7 | estudo-de-caso-integracao-e-implantacao-de-microsservicos | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos | 46 |
| ES2 | `execut` | devops | conceito-de-devops | declara | conceito-de-devops | 125 |
| ES2 | `execut` | kubernetes | plataformas-de-devops | declara | plataformas-de-devops | 15 |
| ES2 | `http` | servicos | orientada-a-servicos | declara | orientada-a-servicos | 19 |
| ES2 | `http` | web | cliente-servidor | declara | cliente-servidor | 35 |
| FR | `format` | 02-modelos-de-referencia | modelos-osi-e-tcpip | declara | modelos-osi-e-tcpip | 96 |
| FR | `format` | 04-protocolo-http | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 81 |
| FR | `format` | 05-protocolo-dns | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 120 |
| FR | `format` | 07-protocolos-de-e-mail | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 114 |
| FR | `proces` | 04-camada-de-aplicacao | funcoes-e-caracteristicas-do-nivel-de-aplicacao | declara | funcoes-e-caracteristicas-do-nivel-de-aplicacao | 28 |
| FR | `proces` | 06-protocolo-dhcp | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 79 |
| FR | `proces` | 08-desenvolvimento-de-aplicacoes | implementacao-de-sockets | declara | implementacao-de-sockets | 22 |
| FR | `cache` | unidade2-exercicios-dns | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat | 12 |
| FR | `cache` | unidade2-exercicios-http | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap | 20 |
| FR | `protoc rede` | 01-protocolos-de-rede | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | declara | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | 64 |
| FR | `protoc rede` | unidade1-exercicios | modelos-osi-e-tcpip | declara | modelos-osi-e-tcpip | 9 |
| FR | `histor` | 03-tipos-de-redes | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | declara | conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | 42 |
| FR | `server` | tcp-chat-c | implementacao-de-sockets | declara | implementacao-de-sockets | 10 |
| FR | `server` | udp-example-c | implementacao-de-sockets | declara | implementacao-de-sockets | 6 |
| IA | `visual` | agrupamento-hierarquico-exemplo-1 | modelos-descritivos | declara | modelos-descritivos | 98 |
| IA | `visual` | agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris | modelos-descritivos | declara | modelos-descritivos | 102 |
| IA | `visual` | agrupamento-usando-k-means-exemplo-1-ipynb | modelos-descritivos | declara | modelos-descritivos | 101 |
| IA | `visual` | agrupamento-usando-k-means-exemplo-2-ipynb | modelos-descritivos | declara | modelos-descritivos | 41 |
| IA | `visual` | arvores-de-decisao | modelos-preditivos | declara | modelos-preditivos | 225 |
| IA | `visual` | exemplo-1-arvores-de-decisao-classificacao-planta-iris | modelos-preditivos | declara | modelos-preditivos | 114 |
| IA | `visual` | exemplo-2-arvores-de-decisao-regressao-diabetes | modelos-preditivos | declara | modelos-preditivos | 106 |
| IA | `visual` | exemplo-complementar-classificacao-com-arvores-de-decisao | modelos-preditivos | declara | modelos-preditivos | 67 |
| IA | `analis` | analise-exploratoria-de-dados-exemplo-1 | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 75 |
| IA | `analis` | analise-exploratoria-dos-dados-exemplo-2 | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 18 |
| IA | `analis` | artigo-usando-k-nn-em-texto | modelos-preditivos | declara | modelos-preditivos | 62 |
| IA | `analis` | aula-sobre-agrupamento-parte-2-hierarquico | modelos-descritivos | declara | modelos-descritivos | 27 |
| IA | `analis` | caracteristicas-dos-dados | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 179 |
| IA | `analis` | como-analisar-resultados-acc-pr-re-e-f1 | metricas-de-avaliacao | declara | metricas-de-avaliacao | 60 |
| IA | `artifi` | algoritmo-de-classificacao-k-nn | modelos-preditivos | declara | modelos-preditivos | 32 |
| IA | `artifi` | aula-sobre-agrupamento-parte-1-particional | modelos-descritivos | declara | modelos-descritivos | 28 |
| IA | `artifi` | introducao-a-ml | introducao-ao-aprendizado-de-maquina | declara | introducao-ao-aprendizado-de-maquina | 54 |
| IA | `artifi` | introducao-a-redes-neurais | modelos-preditivos | declara | modelos-preditivos | 179 |
| IA | `artifi` | mlp | modelos-preditivos | declara | modelos-preditivos | 146 |
| IA | `artifi` | rede-perceptron | modelos-preditivos | declara | modelos-preditivos | 228 |
| IA | `print` | exemplo-2-k-nn-com-iriscsv-mais-completo | modelos-preditivos | declara | modelos-preditivos | 17 |
| IA | `print` | exercicio-2-solucao-com-rede-perceptron-atualizado | modelos-preditivos | declara | modelos-preditivos | 50 |
| IA | `print` | k-nn-para-classificacao-exemplo-cardio | modelos-preditivos | declara | modelos-preditivos | 18 |
| IA | `print` | mlp-classificacao-iris-atualizado | modelos-preditivos | declara | modelos-preditivos | 36 |
| IA | `print` | rede-perceptron-classificacao-de-cliente | modelos-preditivos | declara | modelos-preditivos | 39 |
| IA | `print` | rede-perceptron-classificacao-planta-iris | modelos-preditivos | declara | modelos-preditivos | 55 |
| IA | `print` | rede-perceptron-exemplo-atualizado | modelos-preditivos | declara | modelos-preditivos | 33 |
| IA | `print` | rede-perceptron-or-em-python | modelos-preditivos | declara | modelos-preditivos | 25 |
| IA | `refere` | artigo-usando-agrupamento | modelos-descritivos | declara | modelos-descritivos | 57 |
| IA | `refere` | survey-on-clustering | modelos-descritivos | declara | modelos-descritivos | 116 |
| IA | `regres` | k-nn-para-regressao-exemplo-imc | modelos-preditivos | declara | modelos-preditivos | 6 |
| IA | `regres` | mlp-regressao-cardio | modelos-preditivos | declara | modelos-preditivos | 37 |
| IA | `versic` | exemplo-com-k-nn | modelos-preditivos | declara | modelos-preditivos | 14 |
| MF | `formal` | exerciciosformalizacaoalgoritmosinvariantes | invariante-e-variante-de-laco | declara | invariante-e-variante-de-laco | 15 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao2 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosformalizacaoalgoritmosrecursao3 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | exerciciosisabelle | provadores-de-teoremas | declara | provadores-de-teoremas | 27 |
| MF | `formal` | exerciciosisabelle2 | provadores-de-teoremas | declara | provadores-de-teoremas | 27 |
| MF | `formal` | formalizacaoalgoritmos-invarianteslaco | invariante-e-variante-de-laco | declara | invariante-e-variante-de-laco | 26 |
| MF | `formal` | formalizacaoalgoritmos-recursao | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 34 |
| MF | `formal` | formalizacaoalgoritmos-recursao2 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 19 |
| MF | `formal` | formalizacaoalgoritmos-recursao3 | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 25 |
| MF | `formal` | logicapredicados-sintaxe | fundamentos-de-logica-de-primeira-ordem | declara | fundamentos-de-logica-de-primeira-ordem | 15 |
| MF | `provas` | arvores | provadores-de-teoremas | declara | provadores-de-teoremas | 5 |
| MF | `provas` | exercicioscorrecaoinducaomatematica | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 16 |
| MF | `provas` | listas | provadores-de-teoremas | declara | provadores-de-teoremas | 2 |
| MF | `provas` | provas | provadores-de-teoremas | declara | provadores-de-teoremas | 7 |
| MF | `provas` | provasindutivas-especificacoesrecursivas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 26 |
| MF | `provas` | provasindutivas-especificacoesrecursivas-arvores | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 18 |
| MF | `provas` | provasindutivas-especificacoesrecursivas-listas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 12 |
| MF | `progra` | exerciciosdafny1 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 9 |
| MF | `progra` | exerciciosdafny2 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 13 |
| MF | `progra` | exerciciosdafny3 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 15 |
| MF | `progra` | exerciciosdafny4 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 19 |
| MF | `progra` | exerciciosdafny5 | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 13 |
| MF | `progra` | logicadehoare | logica-de-hoare | declara | logica-de-hoare | 40 |
| MF | `logica` | logicadehoare-exercicios-respostas | logica-de-hoare | declara | logica-de-hoare | 4 |
| MF | `logica` | logicapredicados-semantica | fundamentos-de-logica-de-primeira-ordem | declara | fundamentos-de-logica-de-primeira-ordem | 14 |
| MF | `logica` | logicaproposicional-semantica | linguagens-de-especificacao-e-logicas | declara | linguagens-de-especificacao-e-logicas | 41 |
| MF | `logica` | logicaproposicional-sintaxe | linguagens-de-especificacao-e-logicas | declara | linguagens-de-especificacao-e-logicas | 10 |
| MF | `arrays` | colecoes-arrays | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 3 |
| MF | `arrays` | exercicios-arrays | softwares-de-suporte-a-verificacao-formal-de-programas | declara | softwares-de-suporte-a-verificacao-formal-de-programas | 1 |
| MF | `arrays` | logicadehoare2 | logica-de-hoare | declara | logica-de-hoare | 14 |
| MF | `concei` | introducao | abordagens-para-verificacao-formal | declara | abordagens-para-verificacao-formal | 16 |
| MF | `concei` | revisao | sistemas-formais | declara | sistemas-formais | 39 |
| MF | `concei` | verificacaomodelos | verificacao-de-modelos-model-checking | declara | verificacao-de-modelos-model-checking | 30 |
| MF | `pagina` | exerciciosformalizacaoalgoritmosrecursao-respostas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 1 |
| MF | `pagina` | exerciciosformalizacaoalgoritmosrecursao3-respostas | especificacao-de-funcoes-recursivas | declara | especificacao-de-funcoes-recursivas | 1 |
| MF | `arvore` | classes-parte2 | verificacao-de-programas | declara | verificacao-de-programas | 28 |
| MF | `arvore` | conjuntosindutivos | especificacao-de-conjuntos-indutivos | declara | especificacao-de-conjuntos-indutivos | 37 |
| SO | `estado` | 1203-processos | chamadas-de-sistema | declara | chamadas-de-sistema | 25 |
| SO | `estado` | 1903-estruturas-de-controle | conceitos-basicos | declara | conceitos-basicos | 32 |
| SO | `multip` | 2603-algoritmos-de-escalonamento | algoritmos-de-escalonamento | declara | algoritmos-de-escalonamento | 31 |
| SO | `multip` | definicao-e-historico | evolucao-historica | declara | evolucao-historica | 42 |
| SO | `contex` | 2403-escalonamento-de-processos | escalonamento | declara | escalonamento | 20 |
| SO | `estrut` | 1703-chamada-de-sistema | chamadas-de-sistema | declara | chamadas-de-sistema | 23 |
| TCC | `cadeia` | aula-08-maquinas-de-turing-como-processadoras-de-funcoes | conjectura-de-church-turing | declara | conjectura-de-church-turing | 96 |
| TCC | `relac` | aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade | conjuntos-enumeraveis | declara | conjuntos-enumeraveis | 86 |
| TCC | `relac` | aula-07-maquinas-de-turing-e-linguagens-recursivamente-enumeraveis | maquinas-de-turing | declara | maquinas-de-turing | 105 |
| TCC | `fitas` | aula-09-variacoes-de-maquinas-de-turing | variacoes-de-maquinas-de-turing | declara | variacoes-de-maquinas-de-turing | 81 |
| TCC | `fitas` | aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf | linguagens-reconheciveis-e-decidiveis | declara | linguagens-reconheciveis-e-decidiveis | 101 |
| TCC | `centra` | aula-02-conjuntos-enumeraveis-e-nao-enumeraveis-argumento-da-diagonalizacao-de-cantor | argumento-diagonal-de-cantor-e-conjuntos-incontaveis | declara | argumento-diagonal-de-cantor-e-conjuntos-incontaveis | 120 |
| TCC | `centra` | aula-03-funcoes-recursivas-primitivas-e-composicao-de-funcoes | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais | 119 |

## 7. Perguntas de expressao e resposta simulada (V-G, prefixo 20)

| curso | # | expressao | mat. alcancados | escopo (entries) | resposta | topico |
|---|---|---|---|---|---|---|
| CG | 1 | `videos` | 16 | 16 | depende |  |
| CG | 2 | `ponto` | 11 | 11 | depende |  |
| CG | 3 | `opengl` | 10 | 10 | depende |  |
| CG | 4 | `proces` | 8 | 8 | depende |  |
| CG | 5 | `slides` | 9 | 9 | depende |  |
| CG | 6 | `ativid` | 4 | 4 | depende |  |
| CG | 7 | `codigo` | 7 | 7 | depende |  |
| CG | 8 | `pagina geomet` | 4 | 4 | declara | algoritmos-de-geometria-computacional |
| CG | 9 | `manipu imagen` | 7 | 7 | depende |  |
| CG | 10 | `animac` | 6 | 6 | depende |  |
| CG | 11 | `pinho` | 7 | 7 | depende |  |
| CG | 12 | `modela geomet` | 3 | 3 | depende |  |
| CG | 13 | `includ` | 3 | 3 | depende |  |
| CG | 14 | `imagen realis` | 2 | 2 | declara | modelos-de-iluminacao-luz-pontual-direcional-spot |
| CG | 15 | `intro` | 1 | 1 | declara | origens |
| CG | 16 | `pagina curvas` | 1 | 1 | declara | representacao-de-curvas-parametricas |
| CG | 17 | `zbuffe` | 1 | 1 | declara | algoritmo-z-buffer |
| ES2 | 1 | `projet` | 7 | 7 | depende |  |
| ES2 | 2 | `basead prof bernar` | 7 | 7 | depende |  |
| ES2 | 3 | `applic curren` | 7 | 7 | depende |  |
| ES2 | 4 | `autori` | 2 | 2 | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| ES2 | 5 | `execut` | 3 | 3 | depende |  |
| ES2 | 6 | `http` | 2 | 2 | depende |  |
| ES2 | 7 | `rabbit` | 3 | 3 | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| FR | 1 | `format` | 4 | 4 | depende |  |
| FR | 2 | `exampl` | 3 | 3 | declara | implementacao-de-sockets |
| FR | 3 | `proces` | 3 | 3 | depende |  |
| FR | 4 | `cache` | 4 | 4 | depende |  |
| FR | 5 | `protoc rede` | 2 | 2 | depende |  |
| FR | 6 | `histor` | 2 | 2 | depende |  |
| FR | 7 | `dhcp relay` | 2 | 2 | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat |
| FR | 8 | `server` | 4 | 4 | depende |  |
| IA | 1 | `rede percep` | 9 | 9 | declara | modelos-preditivos |
| IA | 2 | `visual` | 8 | 8 | depende |  |
| IA | 3 | `analis` | 6 | 6 | depende |  |
| IA | 4 | `artifi` | 8 | 8 | depende |  |
| IA | 5 | `print` | 9 | 9 | depende |  |
| IA | 6 | `neuron` | 6 | 6 | declara | modelos-preditivos |
| IA | 7 | `refere` | 5 | 5 | depende |  |
| IA | 8 | `redes` | 5 | 5 | declara | modelos-preditivos |
| IA | 9 | `regres` | 8 | 8 | depende |  |
| IA | 10 | `versic` | 3 | 3 | depende |  |
| IA | 11 | `ipynb` | 3 | 3 | depende |  |
| IA | 12 | `java` | 1 | 1 | declara | modelos-preditivos |
| MF | 1 | `formal` | 11 | 11 | depende |  |
| MF | 2 | `provas` | 9 | 9 | depende |  |
| MF | 3 | `progra` | 6 | 6 | depende |  |
| MF | 4 | `logica` | 6 | 6 | depende |  |
| MF | 5 | `arrays` | 4 | 4 | depende |  |
| MF | 6 | `termin` | 3 | 3 | declara | correcao-parcial-e-total |
| MF | 7 | `concei` | 3 | 3 | depende |  |
| MF | 8 | `pagina` | 3 | 3 | depende |  |
| MF | 9 | `arvore` | 5 | 5 | depende |  |
| MF | 10 | `coleco` | 3 | 3 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| MF | 11 | `seguin` | 2 | 2 | declara | linguagens-de-especificacao-e-logicas |
| MF | 12 | `nusmv` | 2 | 2 | declara | softwares-de-suporte-a-verificacao-formal-de-modelos |
| MF | 13 | `dafny` | 6 | 6 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| MF | 14 | `floyd hoare` | 3 | 3 | declara | logica-de-hoare |
| MF | 15 | `classe` | 3 | 3 | depende |  |
| MF | 16 | `defini` | 4 | 4 | depende |  |
| MF | 17 | `intro` | 1 | 1 | declara | provadores-de-teoremas |
| MF | 18 | `tiposi` | 1 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| SO | 1 | `includ pthrea` | 3 | 3 | declara | conceitos-basicos |
| SO | 2 | `estado` | 2 | 2 | depende |  |
| SO | 3 | `multip` | 2 | 2 | depende |  |
| SO | 4 | `includ types` | 2 | 2 | declara | chamadas-de-sistema |
| SO | 5 | `contex` | 2 | 2 | depende |  |
| SO | 6 | `estrut` | 2 | 2 | depende |  |
| SO | 7 | `thread proces` | 1 | 1 | declara | conceitos-basicos |
| SO | 8 | `homewo` | 1 | 1 | declara | algoritmos-de-escalonamento |
| TCC | 1 | `cadeia` | 2 | 2 | depende |  |
| TCC | 2 | `kleene` | 2 | 2 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |
| TCC | 3 | `relac` | 2 | 2 | depende |  |
| TCC | 4 | `fitas` | 2 | 2 | depende |  |
| TCC | 5 | `centra` | 2 | 2 | depende |  |
| TCC | 6 | `anders robert pinhei` | 2 | 2 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |
