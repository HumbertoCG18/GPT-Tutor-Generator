# W-P2' — curva de microdeclaracoes do professor por prefixo (22/09)

JSON: `wp2_curva_microdeclaracoes_22-09.json` sha256 `f3a83039dcee0da4dcb1a85ff6c5414094fb621dd7e5f42b339cae423e435287`  
Congelamento (3 ordens, pre-gold) sha256 `38185c126de98f08b71d4fbbadd4f9176c877f3467a64916063785a4cdf4059d`  
Congelamento herdado do W-P1 sha256 `114c6f5efbfe16f3e4ca6b6af0d9713ccaac9182d485041cf917c3e9865d1af3`  
Estado: branch `feat/motor-atribuicao`, HEAD `b726d4c`, `src/` intocado.

## 1. Base (0 declaracoes)

- primaria 84/251, aceita 108/251, ausentes 8
- fidelidade do replay contra o manifest gravado: 329/329

| curso | n | primaria | aceita | ausente | alvos |
|---|---|---|---|---|---|
| CG | 82 | 28 | 42 | 7 | 47 |
| ES2 | 28 | 7 | 8 | 0 | 21 |
| FR | 18 | 6 | 7 | 0 | 12 |
| IA | 39 | 4 | 5 | 0 | 35 |
| MF | 58 | 25 | 29 | 1 | 30 |
| SO | 15 | 7 | 8 | 0 | 8 |
| TCC | 11 | 7 | 9 | 0 | 4 |

## 2. Totais por ordem x prefixo

| ordem | prefixo | examinadas | declaradas | depende | nao assoc. | primaria/251 | aceita/251 | ganhos | perdas | abst->dec (certas/erradas) | alvos corrigidos | tempo (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP25 | 5 | 35 | 6 | 29 | 0 | 99 | 123 | 16 | 1 | 1 (1/0) | 16/157 | 48.08 |
| CAP25 | 10 | 59 | 16 | 43 | 0 | 113 | 135 | 30 | 1 | 10 (7/3) | 30/157 | 45.04 |
| CAP25 | 20 | 76 | 27 | 49 | 0 | 118 | 138 | 46 | 12 | 20 (14/6) | 45/157 | 43.7 |
| CAP25 | 40 | 76 | 27 | 49 | 0 | 118 | 138 | 46 | 12 | 20 (14/6) | 45/157 | 40.76 |
| CAP50 | 5 | 34 | 6 | 28 | 0 | 90 | 113 | 8 | 2 | 3 (1/2) | 8/157 | 38.69 |
| CAP50 | 10 | 51 | 13 | 38 | 0 | 104 | 128 | 35 | 15 | 18 (11/7) | 34/157 | 50.35 |
| CAP50 | 20 | 62 | 19 | 43 | 0 | 112 | 134 | 41 | 13 | 19 (14/5) | 40/157 | 40.45 |
| CAP50 | 40 | 62 | 19 | 43 | 0 | 112 | 134 | 41 | 13 | 19 (14/5) | 40/157 | 49.24 |
| NAIVE | 5 | 29 | 5 | 24 | 0 | 99 | 123 | 16 | 1 | 3 (1/2) | 16/157 | 71.52 |
| NAIVE | 10 | 42 | 10 | 32 | 0 | 101 | 126 | 31 | 14 | 17 (10/7) | 30/157 | 73.51 |
| NAIVE | 20 | 50 | 16 | 34 | 0 | 109 | 132 | 37 | 12 | 18 (13/5) | 36/157 | 40.01 |
| NAIVE | 40 | 50 | 16 | 34 | 0 | 109 | 132 | 37 | 12 | 18 (13/5) | 36/157 | 37.03 |

## 3. Por curso (ordem x prefixo)

### CAP25

| prefixo | curso | exam. | decl. | dep. | n/a | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | CG | 5 | 0 | 5 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.63 |
| 5 | ES2 | 5 | 1 | 4 | 0 | 8 | 9 | 2 | 1 | 0 (0/0) | 2/21 | 2.82 |
| 5 | FR | 5 | 1 | 4 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 1.06 |
| 5 | IA | 5 | 1 | 4 | 0 | 12 | 13 | 8 | 0 | 0 (0/0) | 8/35 | 13.88 |
| 5 | MF | 5 | 0 | 5 | 0 | 25 | 29 | 0 | 0 | 0 (0/0) | 0/30 | 21.25 |
| 5 | SO | 5 | 2 | 3 | 0 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 2.42 |
| 5 | TCC | 5 | 1 | 4 | 0 | 7 | 9 | 0 | 0 | 0 (0/0) | 0/4 | 3.02 |
| 10 | CG | 10 | 1 | 9 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 2.94 |
| 10 | ES2 | 7 | 2 | 5 | 0 | 11 | 12 | 4 | 0 | 0 (0/0) | 4/21 | 2.93 |
| 10 | FR | 8 | 2 | 6 | 0 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.93 |
| 10 | IA | 10 | 3 | 7 | 0 | 18 | 19 | 14 | 0 | 0 (0/0) | 14/35 | 13.12 |
| 10 | MF | 10 | 2 | 8 | 0 | 32 | 35 | 7 | 0 | 5 (5/0) | 7/30 | 20.12 |
| 10 | SO | 8 | 4 | 4 | 0 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.02 |
| 10 | TCC | 6 | 2 | 4 | 0 | 6 | 7 | 0 | 1 | 2 (0/2) | 0/4 | 2.98 |
| 20 | CG | 17 | 5 | 12 | 0 | 30 | 42 | 2 | 0 | 0 (0/0) | 2/47 | 2.93 |
| 20 | ES2 | 7 | 2 | 5 | 0 | 11 | 12 | 4 | 0 | 0 (0/0) | 4/21 | 3.45 |
| 20 | FR | 8 | 2 | 6 | 0 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.91 |
| 20 | IA | 12 | 4 | 8 | 0 | 19 | 20 | 15 | 0 | 0 (0/0) | 15/35 | 15.38 |
| 20 | MF | 18 | 8 | 10 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 15.94 |
| 20 | SO | 8 | 4 | 4 | 0 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.06 |
| 20 | TCC | 6 | 2 | 4 | 0 | 6 | 7 | 0 | 1 | 2 (0/2) | 0/4 | 3.03 |
| 40 | CG | 17 | 5 | 12 | 0 | 30 | 42 | 2 | 0 | 0 (0/0) | 2/47 | 2.28 |
| 40 | ES2 | 7 | 2 | 5 | 0 | 11 | 12 | 4 | 0 | 0 (0/0) | 4/21 | 2.41 |
| 40 | FR | 8 | 2 | 6 | 0 | 9 | 10 | 3 | 0 | 1 (0/1) | 3/12 | 0.72 |
| 40 | IA | 12 | 4 | 8 | 0 | 19 | 20 | 15 | 0 | 0 (0/0) | 15/35 | 16.79 |
| 40 | MF | 18 | 8 | 10 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 14.12 |
| 40 | SO | 8 | 4 | 4 | 0 | 9 | 10 | 2 | 0 | 2 (2/0) | 2/8 | 2.15 |
| 40 | TCC | 6 | 2 | 4 | 0 | 6 | 7 | 0 | 1 | 2 (0/2) | 0/4 | 2.29 |

### CAP50

| prefixo | curso | exam. | decl. | dep. | n/a | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | CG | 5 | 0 | 5 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.05 |
| 5 | ES2 | 5 | 1 | 4 | 0 | 8 | 9 | 2 | 1 | 0 (0/0) | 2/21 | 2.17 |
| 5 | FR | 5 | 2 | 3 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.98 |
| 5 | IA | 5 | 0 | 5 | 0 | 4 | 5 | 0 | 0 | 0 (0/0) | 0/35 | 11.36 |
| 5 | MF | 5 | 0 | 5 | 0 | 25 | 29 | 0 | 0 | 0 (0/0) | 0/30 | 17.18 |
| 5 | SO | 5 | 2 | 3 | 0 | 8 | 8 | 1 | 0 | 1 (1/0) | 1/8 | 1.61 |
| 5 | TCC | 4 | 1 | 3 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 2.34 |
| 10 | CG | 10 | 0 | 10 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.53 |
| 10 | ES2 | 6 | 2 | 4 | 0 | 9 | 10 | 3 | 1 | 0 (0/0) | 3/21 | 3.25 |
| 10 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 1.23 |
| 10 | IA | 8 | 2 | 6 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 12.68 |
| 10 | MF | 10 | 3 | 7 | 0 | 26 | 31 | 14 | 13 | 14 (9/5) | 13/30 | 22.3 |
| 10 | SO | 6 | 3 | 3 | 0 | 9 | 9 | 2 | 0 | 2 (2/0) | 2/8 | 1.83 |
| 10 | TCC | 4 | 1 | 3 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 5.53 |
| 20 | CG | 14 | 1 | 13 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.2 |
| 20 | ES2 | 6 | 2 | 4 | 0 | 9 | 10 | 3 | 1 | 0 (0/0) | 3/21 | 2.85 |
| 20 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.78 |
| 20 | IA | 8 | 2 | 6 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 13.8 |
| 20 | MF | 17 | 8 | 9 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 14.25 |
| 20 | SO | 6 | 3 | 3 | 0 | 9 | 9 | 2 | 0 | 2 (2/0) | 2/8 | 2.8 |
| 20 | TCC | 4 | 1 | 3 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 2.77 |
| 40 | CG | 14 | 1 | 13 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 2.98 |
| 40 | ES2 | 6 | 2 | 4 | 0 | 9 | 10 | 3 | 1 | 0 (0/0) | 3/21 | 2.76 |
| 40 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.76 |
| 40 | IA | 8 | 2 | 6 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 18.36 |
| 40 | MF | 17 | 8 | 9 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 15.32 |
| 40 | SO | 6 | 3 | 3 | 0 | 9 | 9 | 2 | 0 | 2 (2/0) | 2/8 | 6.32 |
| 40 | TCC | 4 | 1 | 3 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 2.74 |

### NAIVE

| prefixo | curso | exam. | decl. | dep. | n/a | primaria | aceita | ganhos | perdas | abst->dec | alvos corr. | tempo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | CG | 5 | 0 | 5 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 4.29 |
| 5 | ES2 | 2 | 0 | 2 | 0 | 7 | 8 | 0 | 0 | 0 (0/0) | 0/21 | 4.04 |
| 5 | FR | 5 | 2 | 3 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 1.24 |
| 5 | IA | 5 | 1 | 4 | 0 | 14 | 15 | 10 | 0 | 0 (0/0) | 10/35 | 22.63 |
| 5 | MF | 5 | 0 | 5 | 0 | 25 | 29 | 0 | 0 | 0 (0/0) | 0/30 | 30.83 |
| 5 | SO | 5 | 1 | 4 | 0 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 4.27 |
| 5 | TCC | 2 | 1 | 1 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 4.22 |
| 10 | CG | 10 | 1 | 9 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 3.99 |
| 10 | ES2 | 2 | 0 | 2 | 0 | 7 | 8 | 0 | 0 | 0 (0/0) | 0/21 | 4.22 |
| 10 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.98 |
| 10 | IA | 6 | 2 | 4 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 17.71 |
| 10 | MF | 10 | 3 | 7 | 0 | 26 | 31 | 14 | 13 | 14 (9/5) | 13/30 | 38.23 |
| 10 | SO | 5 | 1 | 4 | 0 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 3.98 |
| 10 | TCC | 2 | 1 | 1 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 4.4 |
| 20 | CG | 11 | 2 | 9 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 2.99 |
| 20 | ES2 | 2 | 0 | 2 | 0 | 7 | 8 | 0 | 0 | 0 (0/0) | 0/21 | 2.56 |
| 20 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.81 |
| 20 | IA | 6 | 2 | 4 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 11.81 |
| 20 | MF | 17 | 8 | 9 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 16.13 |
| 20 | SO | 5 | 1 | 4 | 0 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 2.87 |
| 20 | TCC | 2 | 1 | 1 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 2.84 |
| 40 | CG | 11 | 2 | 9 | 0 | 28 | 42 | 0 | 0 | 0 (0/0) | 0/47 | 2.97 |
| 40 | ES2 | 2 | 0 | 2 | 0 | 7 | 8 | 0 | 0 | 0 (0/0) | 0/21 | 2.84 |
| 40 | FR | 7 | 2 | 5 | 0 | 11 | 12 | 5 | 0 | 0 (0/0) | 5/12 | 0.87 |
| 40 | IA | 6 | 2 | 4 | 0 | 15 | 16 | 11 | 0 | 0 (0/0) | 11/35 | 11.27 |
| 40 | MF | 17 | 8 | 9 | 0 | 34 | 37 | 20 | 11 | 15 (12/3) | 19/30 | 14.11 |
| 40 | SO | 5 | 1 | 4 | 0 | 8 | 9 | 1 | 0 | 1 (1/0) | 1/8 | 2.12 |
| 40 | TCC | 2 | 1 | 1 | 0 | 6 | 8 | 0 | 1 | 2 (0/2) | 0/4 | 2.85 |

## 3b. Marcos 50/80/100% dos alvos (perguntas na ordem; `declarados` ignora depende/nao associar)

| ordem | modo | curso | alvos | alcance final | ate 50% | ate 80% | ate 100% |
|---|---|---|---|---|---|---|---|
| NAIVE | alcancados | CG | 47 | 47 | 1 | 4 | 7 |
| NAIVE | declarados | CG | 47 | 0 | None | None | None |
| NAIVE | alcancados | ES2 | 21 | 21 | 1 | 1 | 2 |
| NAIVE | declarados | ES2 | 21 | 0 | None | None | None |
| NAIVE | alcancados | FR | 12 | 12 | 2 | 5 | 7 |
| NAIVE | declarados | FR | 12 | 5 | None | None | None |
| NAIVE | alcancados | IA | 35 | 35 | 1 | 2 | 6 |
| NAIVE | declarados | IA | 35 | 12 | None | None | None |
| NAIVE | alcancados | MF | 30 | 30 | 4 | 11 | 17 |
| NAIVE | declarados | MF | 30 | 17 | 16 | None | None |
| NAIVE | alcancados | SO | 8 | 8 | 1 | 3 | 5 |
| NAIVE | declarados | SO | 8 | 1 | None | None | None |
| NAIVE | alcancados | TCC | 4 | 4 | 1 | 1 | 1 |
| NAIVE | declarados | TCC | 4 | 0 | None | None | None |
| CAP25 | alcancados | MF | 30 | 29 | 5 | 13 | None |
| CAP25 | declarados | MF | 30 | 17 | 14 | None | None |
| CAP25 | alcancados | SO | 8 | 8 | 2 | 7 | 8 |
| CAP25 | declarados | SO | 8 | 6 | 4 | None | None |
| CAP25 | alcancados | IA | 35 | 35 | 3 | 6 | 12 |
| CAP25 | declarados | IA | 35 | 15 | None | None | None |
| CAP25 | alcancados | ES2 | 21 | 21 | 2 | 3 | 5 |
| CAP25 | declarados | ES2 | 21 | 4 | None | None | None |
| CAP25 | alcancados | TCC | 4 | 4 | 3 | 5 | 5 |
| CAP25 | declarados | TCC | 4 | 0 | None | None | None |
| CAP25 | alcancados | CG | 47 | 45 | 3 | 9 | None |
| CAP25 | declarados | CG | 47 | 3 | None | None | None |
| CAP25 | alcancados | FR | 12 | 11 | 3 | 5 | None |
| CAP25 | declarados | FR | 12 | 3 | None | None | None |
| CAP50 | alcancados | MF | 30 | 30 | 4 | 11 | 17 |
| CAP50 | declarados | MF | 30 | 17 | 16 | None | None |
| CAP50 | alcancados | SO | 8 | 8 | 3 | 4 | 6 |
| CAP50 | declarados | SO | 8 | 6 | 3 | None | None |
| CAP50 | alcancados | IA | 35 | 35 | 2 | 4 | 8 |
| CAP50 | declarados | IA | 35 | 12 | None | None | None |
| CAP50 | alcancados | ES2 | 21 | 21 | 2 | 3 | 6 |
| CAP50 | declarados | ES2 | 21 | 3 | None | None | None |
| CAP50 | alcancados | TCC | 4 | 4 | 2 | 2 | 2 |
| CAP50 | declarados | TCC | 4 | 0 | None | None | None |
| CAP50 | alcancados | CG | 47 | 45 | 3 | 6 | None |
| CAP50 | declarados | CG | 47 | 0 | None | None | None |
| CAP50 | alcancados | FR | 12 | 12 | 2 | 5 | 7 |
| CAP50 | declarados | FR | 12 | 5 | None | None | None |

Totais (soma das perguntas por curso):

- **NAIVE / alcancados**: alvos 157, alcance final 157, perguntas ate 50% = 11, ate 80% = 27
- **NAIVE / declarados**: alvos 157, alcance final 35, perguntas ate 50% = 16, ate 80% = 0 (cursos sem 80%: CG, ES2, FR, IA, MF, SO, TCC)
- **CAP25 / alcancados**: alvos 157, alcance final 153, perguntas ate 50% = 21, ate 80% = 48
- **CAP25 / declarados**: alvos 157, alcance final 48, perguntas ate 50% = 18, ate 80% = 0 (cursos sem 80%: CG, ES2, FR, IA, MF, SO, TCC)
- **CAP50 / alcancados**: alvos 157, alcance final 155, perguntas ate 50% = 18, ate 80% = 35
- **CAP50 / declarados**: alvos 157, alcance final 43, perguntas ate 50% = 19, ate 80% = 0 (cursos sem 80%: CG, ES2, FR, IA, MF, SO, TCC)

## 4. Selecao das ordens CAP (pre-gold)

| curso | mat. presentes | expr. novas | frag. hifen. excl. | CAP25 limite | CAP25 excl. df | CAP25 perguntas | CAP50 limite | CAP50 excl. df | CAP50 perguntas |
|---|---|---|---|---|---|---|---|---|---|
| CG | 75 | 963 | 6 | 18.75 | 2 | 17 | 37.5 | 1 | 14 |
| ES2 | 28 | 775 | 6 | 7.0 | 20 | 7 | 14.0 | 1 | 6 |
| FR | 18 | 574 | 34 | 4.5 | 5 | 8 | 9.0 | 0 | 7 |
| IA | 39 | 1601 | 35 | 9.75 | 11 | 12 | 19.5 | 3 | 8 |
| MF | 57 | 380 | 9 | 14.25 | 6 | 18 | 28.5 | 0 | 17 |
| SO | 15 | 183 | 6 | 3.75 | 20 | 8 | 7.5 | 5 | 6 |
| TCC | 11 | 796 | 29 | 2.75 | 54 | 6 | 5.5 | 11 | 4 |

Expressoes de maior df excluidas pelo cap 25% (topo por curso):

- **CG**: `extrai`, `pagina`
- **ES2**: `engenh`, `codigo`, `julio`, `julio machad`, `machad`, `prof`, `prof julio`, `prof julio machad`
- **FR**: `refere`, `slides`, `camada`, `rede`, `mensag`
- **IA**: `celula`, `celula codigo`, `codigo`, `dados`, `celula markdo`, `markdo`, `iris`, `percep`
- **MF**: `julio`, `julio machad`, `machad`, `prof`, `prof julio`, `prof julio machad`
- **SO**: `includ`, `includ stdio`, `includ unistd`, `stdio`, `unistd`, `linux`, `miguel`, `miguel xavier`
- **TCC**: `ario`, `encias`, `exerc`, `exerc icio`, `icio`, `refer`, `refer encias`, `resumo`

## 5. Perdas (declaracao derruba material hoje certo)

| ordem | prefixo | curso | gold_id | base | novo | gold primario |
|---|---|---|---|---|---|---|
| NAIVE | 5 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| NAIVE | 10 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| NAIVE | 10 | MF | correcaoterminacao | `correcao-parcial-e-total` | `softwares-de-suporte-a-verificacao-formal-de-programas` | correcao-parcial-e-total |
| NAIVE | 10 | MF | logicadehoare | `logica-de-hoare` | `softwares-de-suporte-a-verificacao-formal-de-programas` | logica-de-hoare |
| NAIVE | 10 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 10 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| NAIVE | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| NAIVE | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 20 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| NAIVE | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| NAIVE | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| NAIVE | 40 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP25 | 5 | ES2 | roteiro5-conteiners | `estudo-de-caso-integracao-e-implantacao-de-microsservicos` | `gerenciamento-da-configuracao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| CAP25 | 10 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP25 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| CAP25 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP25 | 20 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP25 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| CAP25 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP25 | 40 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP50 | 5 | ES2 | roteiro5-conteiners | `estudo-de-caso-integracao-e-implantacao-de-microsservicos` | `gerenciamento-da-configuracao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| CAP50 | 5 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP50 | 10 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| CAP50 | 10 | MF | correcaoterminacao | `correcao-parcial-e-total` | `softwares-de-suporte-a-verificacao-formal-de-programas` | correcao-parcial-e-total |
| CAP50 | 10 | MF | logicadehoare | `logica-de-hoare` | `softwares-de-suporte-a-verificacao-formal-de-programas` | logica-de-hoare |
| CAP50 | 10 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 10 | ES2 | roteiro5-conteiners | `estudo-de-caso-integracao-e-implantacao-de-microsservicos` | `gerenciamento-da-configuracao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| CAP50 | 10 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP50 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| CAP50 | 20 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 20 | ES2 | roteiro5-conteiners | `estudo-de-caso-integracao-e-implantacao-de-microsservicos` | `gerenciamento-da-configuracao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| CAP50 | 20 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |
| CAP50 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | formalizacaoalgoritmos-recursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | provasindutivas-especificacoesrecursivas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | provasindutivas-especificacoesrecursivas-arvores | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | provasindutivas-especificacoesrecursivas-listas | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | exercicioscorrecaoinducaomatematica | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao2 | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | formalizacaoalgoritmos-recursao | `especificacao-de-funcoes-recursivas` | `linguagens-de-especificacao-e-logicas` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | MF | exerciciosisabelle | `provadores-de-teoremas` | `linguagens-de-especificacao-e-logicas` | provadores-de-teoremas |
| CAP50 | 40 | MF | exerciciosformalizacaoalgoritmosrecursao3-respostas | `especificacao-de-funcoes-recursivas` | `` | especificacao-de-funcoes-recursivas |
| CAP50 | 40 | ES2 | roteiro5-conteiners | `estudo-de-caso-integracao-e-implantacao-de-microsservicos` | `gerenciamento-da-configuracao` | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| CAP50 | 40 | TCC | aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos | `` | `funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais` |  |

## 6. Perguntas examinadas e resposta simulada (ate 40 por ordem/curso)

### CAP25

**CG**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | videos | 16 | 16 | depende |  |
| 2 | ponto | 11 | 10 | depende |  |
| 3 | opengl, openglbasico | 10 | 8 | depende |  |
| 4 | processamento, processo | 8 | 6 | depende |  |
| 5 | slides | 9 | 6 | depende |  |
| 6 | atividade, atividades | 4 | 4 | depende |  |
| 7 | codigo | 7 | 4 | depende |  |
| 8 | pagina geometria | 4 | 4 | declara | algoritmos-de-geometria-computacional |
| 9 | manipulacao imagens | 7 | 3 | depende |  |
| 10 | animacao | 6 | 2 | depende |  |
| 11 | pinho | 7 | 2 | depende |  |
| 12 | modelagem geometrica | 3 | 2 | depende |  |
| 13 | include | 3 | 1 | depende |  |
| 14 | imagens realisticas | 2 | 1 | declara | modelos-de-iluminacao-luz-pontual-direcional-spot |
| 15 | intro | 1 | 1 | declara | origens |
| 16 | pagina curvas | 1 | 1 | declara | representacao-de-curvas-parametricas |
| 17 | zbuffer | 1 | 1 | declara | algoritmo-z-buffer |

**ES2**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | projeto | 7 | 7 | depende |  |
| 2 | baseado prof bernardo | 7 | 7 | depende |  |
| 3 | application currency | 7 | 7 | depende |  |
| 4 | autorizacao | 2 | 2 | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| 5 | executar, executavel, execute | 3 | 2 | depende |  |
| 6 | http | 2 | 2 | depende |  |
| 7 | rabbit, rabbitmq | 3 | 1 | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos |

**FR**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | formato | 4 | 4 | depende |  |
| 2 | example | 3 | 3 | declara | implementacao-de-sockets |
| 3 | processo, processos | 3 | 3 | depende |  |
| 4 | cache | 4 | 2 | depende |  |
| 5 | protocolos rede | 2 | 2 | depende |  |
| 6 | historia, historico | 2 | 1 | depende |  |
| 7 | dhcp relay | 2 | 1 | declara | protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat |
| 8 | server, servers | 4 | 1 | depende |  |

**IA**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | rede perceptron | 9 | 9 | declara | modelos-preditivos |
| 2 | visualising, visualizacao, visualizar | 8 | 8 | depende |  |
| 3 | analisa, analisando, analisar, analise | 6 | 6 | depende |  |
| 4 | artificiais, artificial | 8 | 4 | depende |  |
| 5 | print | 9 | 3 | depende |  |
| 6 | neuronio, neuronios | 6 | 2 | declara | modelos-preditivos |
| 7 | references, referencia, referencias | 5 | 2 | depende |  |
| 8 | redes | 5 | 1 | declara | modelos-preditivos |
| 9 | regressao | 8 | 1 | depende |  |
| 10 | versicolor | 3 | 1 | depende |  |
| 11 | ipynb | 3 | 1 | depende |  |
| 12 | java | 1 | 1 | declara | modelos-preditivos |

**MF**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | formalizacao, formalizacaoalgoritmos, formalizando | 11 | 11 | depende |  |
| 2 | provas, provasindutivas | 9 | 7 | depende |  |
| 3 | programacao | 6 | 6 | depende |  |
| 4 | logicadehoare, logicapredicados, logicaproposicional | 6 | 4 | depende |  |
| 5 | arrays | 4 | 3 | depende |  |
| 6 | terminacao | 3 | 3 | declara | correcao-parcial-e-total |
| 7 | conceitos | 3 | 3 | depende |  |
| 8 | pagina | 3 | 2 | depende |  |
| 9 | arvore, arvores | 5 | 2 | depende |  |
| 10 | colecoes | 3 | 2 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 11 | seguinte | 2 | 2 | declara | linguagens-de-especificacao-e-logicas |
| 12 | nusmv | 2 | 2 | declara | softwares-de-suporte-a-verificacao-formal-de-modelos |
| 13 | dafny | 6 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 14 | floyd hoare | 3 | 1 | declara | logica-de-hoare |
| 15 | classes | 3 | 1 | depende |  |
| 16 | definicao, definicoes | 4 | 1 | depende |  |
| 17 | intro | 1 | 1 | declara | provadores-de-teoremas |
| 18 | tiposindutivos | 1 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |

**SO**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | include pthread | 3 | 3 | declara | conceitos-basicos |
| 2 | estado, estados | 2 | 2 | depende |  |
| 3 | multiplas, multiprogramacao, multiprogramming | 2 | 2 | depende |  |
| 4 | include types | 2 | 2 | declara | chamadas-de-sistema |
| 5 | contexto | 2 | 1 | depende |  |
| 6 | estrutura, estruturas | 2 | 1 | depende |  |
| 7 | threads processos | 1 | 1 | declara | conceitos-basicos |
| 8 | homework | 1 | 1 | declara | algoritmos-de-escalonamento |

**TCC**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | cadeia, cadeias | 2 | 2 | depende |  |
| 2 | kleene | 2 | 2 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |
| 3 | relac | 2 | 2 | depende |  |
| 4 | fitas | 2 | 2 | depende |  |
| 5 | central | 2 | 2 | depende |  |
| 6 | anderson roberto pinheiro | 2 | 1 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |

### CAP50

**CG**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | pagina, paginas | 27 | 27 | depende |  |
| 2 | ponto | 11 | 10 | depende |  |
| 3 | slides | 9 | 7 | depende |  |
| 4 | processamento, processo | 8 | 6 | depende |  |
| 5 | glut | 8 | 6 | depende |  |
| 6 | atividade, atividades | 4 | 4 | depende |  |
| 7 | pinho | 7 | 3 | depende |  |
| 8 | animacao | 6 | 2 | depende |  |
| 9 | curvas bezier | 5 | 2 | depende |  |
| 10 | videos | 16 | 1 | depende |  |
| 11 | include | 3 | 1 | depende |  |
| 12 | opengl, openglbasico | 10 | 1 | depende |  |
| 13 | modelagem geometrica | 3 | 1 | depende |  |
| 14 | zbuffer | 1 | 1 | declara | algoritmo-z-buffer |

**ES2**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | codigo | 12 | 12 | depende |  |
| 2 | julio machado | 10 | 8 | depende |  |
| 3 | projeto | 7 | 4 | depende |  |
| 4 | http | 2 | 2 | depende |  |
| 5 | autorizacao | 2 | 1 | declara | estudo-de-caso-integracao-e-implantacao-de-microsservicos |
| 6 | kubernetes | 1 | 1 | declara | plataformas-de-devops |

**FR**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | referencia, referencias | 9 | 9 | depende |  |
| 2 | example | 3 | 3 | declara | implementacao-de-sockets |
| 3 | mensagem, mensagens | 5 | 2 | depende |  |
| 4 | camada, camadas | 8 | 1 | depende |  |
| 5 | requisicao, requisicoes | 2 | 1 | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap |
| 6 | rede | 7 | 1 | depende |  |
| 7 | server, servers | 4 | 1 | depende |  |

**IA**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | dados | 19 | 19 | depende |  |
| 2 | celula markdown | 17 | 8 | depende |  |
| 3 | iris | 12 | 3 | depende |  |
| 4 | artificiais, artificial | 8 | 3 | depende |  |
| 5 | references, referencia, referencias | 5 | 3 | depende |  |
| 6 | rede | 11 | 1 | declara | modelos-preditivos |
| 7 | ipynb | 3 | 1 | depende |  |
| 8 | java | 1 | 1 | declara | modelos-preditivos |

**MF**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | julio machado | 24 | 24 | depende |  |
| 2 | logicadehoare, logicapredicados, logicaproposicional | 6 | 6 | depende |  |
| 3 | arvore, arvores | 5 | 3 | depende |  |
| 4 | arrays | 4 | 3 | depende |  |
| 5 | conceitos | 3 | 3 | depende |  |
| 6 | pagina | 3 | 2 | depende |  |
| 7 | provas, provasindutivas | 9 | 2 | depende |  |
| 8 | colecoes | 3 | 2 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 9 | seguinte | 2 | 2 | declara | linguagens-de-especificacao-e-logicas |
| 10 | dafny | 6 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 11 | floyd hoare | 3 | 1 | declara | logica-de-hoare |
| 12 | classes | 3 | 1 | depende |  |
| 13 | definicao, definicoes | 4 | 1 | depende |  |
| 14 | terminacao | 3 | 1 | declara | correcao-parcial-e-total |
| 15 | intro | 1 | 1 | declara | provadores-de-teoremas |
| 16 | nusmv | 2 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-modelos |
| 17 | tiposindutivos | 1 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |

**SO**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | linux | 5 | 5 | declara | chamadas-de-sistema |
| 2 | defini, definicao | 4 | 4 | depende |  |
| 3 | thread, threads | 4 | 3 | declara | conceitos-basicos |
| 4 | estado, estados | 2 | 1 | depende |  |
| 5 | multiplas, multiprogramacao, multiprogramming | 2 | 1 | depende |  |
| 6 | homework | 1 | 1 | declara | algoritmos-de-escalonamento |

**TCC**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | operac, operacional | 5 | 5 | depende |  |
| 2 | encia | 5 | 3 | depende |  |
| 3 | minimizac, minimizacao | 3 | 2 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |
| 4 | aquina, aquinas | 4 | 1 | depende |  |

### NAIVE

**CG**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | extraido | 43 | 43 | depende |  |
| 2 | ponto | 11 | 8 | depende |  |
| 3 | slides | 9 | 7 | depende |  |
| 4 | glut | 8 | 6 | depende |  |
| 5 | processamento, processo | 8 | 3 | depende |  |
| 6 | python | 8 | 3 | depende |  |
| 7 | include | 3 | 1 | depende |  |
| 8 | segmentacao texturas | 3 | 1 | declara | segmentacao |
| 9 | modelagem geometrica | 3 | 1 | depende |  |
| 10 | curvas bezier | 5 | 1 | depende |  |
| 11 | zbuffer | 1 | 1 | declara | algoritmo-z-buffer |

**ES2**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | engenharia | 20 | 20 | depende |  |
| 2 | codigo | 12 | 8 | depende |  |

**FR**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | referencia, referencias | 9 | 9 | depende |  |
| 2 | example | 3 | 3 | declara | implementacao-de-sockets |
| 3 | mensagem, mensagens | 5 | 2 | depende |  |
| 4 | camada, camadas | 8 | 1 | depende |  |
| 5 | requisicao, requisicoes | 2 | 1 | declara | protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap |
| 6 | rede | 7 | 1 | depende |  |
| 7 | server, servers | 4 | 1 | depende |  |

**IA**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | celula | 24 | 24 | depende |  |
| 2 | artificiais, artificial | 8 | 8 | depende |  |
| 3 | references, referencia, referencias | 5 | 4 | depende |  |
| 4 | rede | 11 | 1 | declara | modelos-preditivos |
| 5 | iris | 12 | 1 | depende |  |
| 6 | java | 1 | 1 | declara | modelos-preditivos |

**MF**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | julio machado | 24 | 24 | depende |  |
| 2 | logicadehoare, logicapredicados, logicaproposicional | 6 | 6 | depende |  |
| 3 | arvore, arvores | 5 | 3 | depende |  |
| 4 | arrays | 4 | 3 | depende |  |
| 5 | conceitos | 3 | 3 | depende |  |
| 6 | pagina | 3 | 2 | depende |  |
| 7 | provas, provasindutivas | 9 | 2 | depende |  |
| 8 | colecoes | 3 | 2 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 9 | seguinte | 2 | 2 | declara | linguagens-de-especificacao-e-logicas |
| 10 | dafny | 6 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |
| 11 | floyd hoare | 3 | 1 | declara | logica-de-hoare |
| 12 | classes | 3 | 1 | depende |  |
| 13 | definicao, definicoes | 4 | 1 | depende |  |
| 14 | terminacao | 3 | 1 | declara | correcao-parcial-e-total |
| 15 | intro | 1 | 1 | declara | provadores-de-teoremas |
| 16 | nusmv | 2 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-modelos |
| 17 | tiposindutivos | 1 | 1 | declara | softwares-de-suporte-a-verificacao-formal-de-programas |

**SO**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | include | 8 | 8 | depende |  |
| 2 | defini, definicao | 4 | 4 | depende |  |
| 3 | estado, estados | 2 | 1 | depende |  |
| 4 | multiplas, multiprogramacao, multiprogramming | 2 | 1 | depende |  |
| 5 | homework | 1 | 1 | declara | algoritmos-de-escalonamento |

**TCC**

| # | expressao (formas) | mat. alcancados | marg. | resposta | topico declarado |
|---|---|---|---|---|---|
| 1 | exerc icio | 10 | 10 | depende |  |
| 2 | minimizac, minimizacao | 3 | 1 | declara | funcoes-recursivas-primitivas-e-funcoes-recursivas-parciais |

