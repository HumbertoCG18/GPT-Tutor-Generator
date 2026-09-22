# W-P1 — inventario dos 251, residual e ordem das perguntas (22/09)

JSON: `wp1_inventario_matriz_22-09.json` sha256 `d1650b8a0897a8f04def866a2bd99de45aadfb3e2a4e99dfd78e812c4ed8ffae`  
Congelamento (selecao/ordem, pre-gold) sha256 `114c6f5efbfe16f3e4ca6b6af0d9713ccaac9182d485041cf917c3e9865d1af3`  
Estado: branch `feat/motor-atribuicao`, HEAD `9220a57` + diff nao commitado da #48 em `src/`.

## 1. Inventario por curso (regua de subunidade)

| curso | n | certos prim. | certos aceit. | indisp. | bloq.unid. | gold fora tax. | relacao ausente | falha selecao | abstencao | escolha errada |
|---|---|---|---|---|---|---|---|---|---|---|
| MF | 58 | 25 | 29 | 1 | 0 | 0 | 26 | 6 | 0 | 6 |
| SO | 15 | 7 | 8 | 0 | 0 | 0 | 7 | 1 | 0 | 1 |
| IA | 39 | 4 | 5 | 0 | 0 | 0 | 27 | 8 | 0 | 8 |
| ES2 | 28 | 7 | 8 | 0 | 3 | 0 | 6 | 15 | 0 | 15 |
| TCC | 11 | 7 | 9 | 0 | 0 | 0 | 0 | 4 | 1 | 3 |
| CG | 82 | 28 | 42 | 7 | 7 | 5 | 37 | 10 | 4 | 6 |
| FR | 18 | 6 | 7 | 0 | 0 | 0 | 3 | 9 | 1 | 8 |
| **TOTAL** | 251 | 84 | 108 | 8 | 10 | 5 | 106 | 53 | 6 | 47 |

### ids por classe

- **MF / indisponivel** (1): archive-of-formal-proofs-355fb8
- **MF / relacao_ausente** (26): arvores, classes-parte1, classes-parte2, colecoes-arrays, colecoes-conjuntos, colecoes-sequences, exemplos, exemplos-zip, exercicios-arrays, exercicios-conjuntos, exerciciosdafny1, exerciciosdafny2, exerciciosdafny3, exerciciosdafny4, exerciciosdafny5, exerciciosnusmv, intro, introducao-zip, listas, logicapredicados-semantica, logicaproposicional-semantica, logicaproposicional-sintaxe, provas, revisao, terminacao, tiposindutivos
- **MF / falha_selecao** (6): exercicioscorrecaoterminacao, exerciciosisabelle2, exercicioslogicatemporal, hoare, invariantes, logicadehoare2
- **MF / escolha_errada** (6): exercicioscorrecaoterminacao, exerciciosisabelle2, exercicioslogicatemporal, hoare, invariantes, logicadehoare2
- **SO / relacao_ausente** (7): 1903-estruturas-de-controle, 3103-threads, exemplo-criacao-de-processos-no-unix-linux-filho, exemplo-threads-em-c-exemplo1, exemplo-threads-em-c-exemplo2, exemplo-threads-em-c-exemplo3, exercicios
- **SO / falha_selecao** (1): definicao-e-historico
- **SO / escolha_errada** (1): definicao-e-historico
- **IA / relacao_ausente** (27): agrupamento-hierarquico-exemplo-1, agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris, agrupamento-usando-k-means-exemplo-1-ipynb, agrupamento-usando-k-means-exemplo-2-ipynb, artigo-usando-k-nn-em-texto, aula-sobre-agrupamento-parte-1-particional, aula-sobre-agrupamento-parte-2-hierarquico, exemplo-2-k-nn-com-iriscsv-mais-completo, exemplo-com-k-nn, exemplo-complementar-classificacao-com-arvores-de-decisao, exemplo-de-programa-com-k-nn-em-java, exercicio-2-solucao-com-rede-perceptron-atualizado, introducao-a-redes-neurais, k-nn-para-classificacao-exemplo-cardio, k-nn-para-regressao-exemplo-imc, mlp-classificacao-inadimplencia-normalizacao-e-gridsearchcv, mlp-classificacao-iris-atualizado, mlp-regressao-cardio, mlp-xoripynb, rede-perceptron-classificacao-de-cliente, rede-perceptron-classificacao-planta-iris, rede-perceptron-e-equacao-de-reta, rede-perceptron-exemplo-atualizado, rede-perceptron-or-em-python, rede-perceptron-reconhecendo-letras, survey-on-clustering, xor-backpropagation-em-python
- **IA / falha_selecao** (8): algoritmo-de-classificacao-k-nn, artigo-usando-agrupamento, arvores-de-decisao, como-analisar-resultados-acc-pr-re-e-f1, exemplo-1-arvores-de-decisao-classificacao-planta-iris, exemplo-2-arvores-de-decisao-regressao-diabetes, mlp, rede-perceptron
- **IA / escolha_errada** (8): algoritmo-de-classificacao-k-nn, artigo-usando-agrupamento, arvores-de-decisao, como-analisar-resultados-acc-pr-re-e-f1, exemplo-1-arvores-de-decisao-classificacao-planta-iris, exemplo-2-arvores-de-decisao-regressao-diabetes, mlp, rede-perceptron
- **ES2 / bloqueio_unidade** (3): microsservicos4, roteiro4, roteiro4-circuitbreaker
- **ES2 / relacao_ausente** (6): kubernetes, microsservicos6, roteiro1, roteiro2, roteiro3, roteiro4
- **ES2 / falha_selecao** (15): devops, microsservicos, microsservicos2, microsservicos3, microsservicos4, microsservicos5, microsservicos7, revisaoarquiteturapadroes, roteiro1-introducao, roteiro2-nameserver, roteiro3-gateway, roteiro4-circuitbreaker, roteiro6-conteiners-composicao, roteiro7-filas, roteiro8-autenticacao-autorizacao
- **ES2 / escolha_errada** (15): devops, microsservicos, microsservicos2, microsservicos3, microsservicos4, microsservicos5, microsservicos7, revisaoarquiteturapadroes, roteiro1-introducao, roteiro2-nameserver, roteiro3-gateway, roteiro4-circuitbreaker, roteiro6-conteiners-composicao, roteiro7-filas, roteiro8-autenticacao-autorizacao
- **TCC / falha_selecao** (4): aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade, aula-02-conjuntos-enumeraveis-e-nao-enumeraveis-argumento-da-diagonalizacao-de-cantor, aula-08-maquinas-de-turing-como-processadoras-de-funcoes, aula-09-variacoes-de-maquinas-de-turing
- **TCC / abstencao** (1): aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade
- **TCC / escolha_errada** (3): aula-02-conjuntos-enumeraveis-e-nao-enumeraveis-argumento-da-diagonalizacao-de-cantor, aula-08-maquinas-de-turing-como-processadoras-de-funcoes, aula-09-variacoes-de-maquinas-de-turing
- **CG / indisponivel** (7): aula-gravada-975b85, video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758, video-sobre-mapeamento-em-opengl-1dad3c, video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e, video-sobre-origens-da-computacao-grafica-806e66, video-sobre-prechimento-de-areas-duracao-1300-d87e5f, video-sobre-prechimento-de-areas-duracao-330-defae7
- **CG / bloqueio_unidade** (7): basico3d-cpp, basico3d-py-zip, exercicios, exercicios-sobre-curvas-html, morfologiamatematicapptx, openglbasico, pagina-com-videos-sobre-morfologia-matematica-06265a
- **CG / gold_fora_da_taxonomia** (5): animacao-v2, instanciamento, pagina-com-videos-sobre-instanciamento, transformacoesgeometricas, transformacoesgl
- **CG / relacao_ausente** (37): animacao-v2, atividade, basico3d-cpp, basico3d-py, basico3d-py-zip, exercicio-com-animacao, exercicio-de-animacao-foguete, exerciciodemodelagem, exercicioduascores, exercicios, exercicios-de-processamento-de-imagens, exercicios-sobre-curvas, exercicios-sobre-curvas-html, exercicios-teoricos-sobre-processo-de-visualizacao-2d, exercicios-teoricos-sobre-processo-de-visualizacao-2d-html, floodfill, fundamentosmatematicos, instanciamento, mapeamento, matematica, modelagem3d, morfologiamatematicapptx, opengl-cpp, opengl-py, opengl3dcpp, opengl3dcpp-vdi, openglbasico, pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9, pagina-com-videos-sobre-instanciamento, pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156, pagina-com-videos-sobre-mapeamento-9f410e, pagina-com-videos-sobre-morfologia-matematica-06265a, pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea, remocaoderuido, transformacoesgeometricas, transformacoesgl, vis2d
- **CG / falha_selecao** (10): curvas, elemoculto, exerciciosfundamentosmatematicos, iluminacao, opengl3d, pagina-com-videos-sobre-curvas-parametricas-63d902, pagina-com-videos-sobre-visualizacao-3d-35a833, paginas-com-videos-sobre-modelagem-geometrica-f2614a, videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84, vis3d
- **CG / abstencao** (4): opengl3d, pagina-com-videos-sobre-visualizacao-3d-35a833, videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84, vis3d
- **CG / escolha_errada** (6): curvas, elemoculto, exerciciosfundamentosmatematicos, iluminacao, pagina-com-videos-sobre-curvas-parametricas-63d902, paginas-com-videos-sobre-modelagem-geometrica-f2614a
- **FR / relacao_ausente** (3): 04-camada-de-aplicacao, lista-de-exercicios-1-camada-de-aplicacao, unidade1-exercicios
- **FR / falha_selecao** (9): 01-protocolos-de-rede, 04-protocolo-http, 05-protocolo-dns, 08-desenvolvimento-de-aplicacoes, tcp-chat-c, tcp-example, udp-example-c, udp-example-java, unidade2-exercicios-http
- **FR / abstencao** (1): 08-desenvolvimento-de-aplicacoes
- **FR / escolha_errada** (8): 01-protocolos-de-rede, 04-protocolo-http, 05-protocolo-dns, tcp-chat-c, tcp-example, udp-example-c, udp-example-java, unidade2-exercicios-http

### conferencia contra a contagem do coordenador (22/09)

- `n`: (251, 251, True)
- `certos_primaria`: (84, 84, True)
- `indisponiveis`: (8, 8, True)
- `bloqueio_unidade`: (10, 10, True)
- `gold_fora_da_taxonomia`: (5, 5, True)
- `mesma_unidade_errada_ou_abstencao`: (144, 144, True)
- `abstencoes_totais_entre_nao_certos`: 32
- `abstencoes_dentro_dos_144`: 31
- `soma_residual_com_sobreposicao`: 159
- divergencia: certos_aceita medido = 108 vs 107 do coordenador: aqui a subunidade e a GRAVADA no manifest (estado 'antes' do aceite #48 = 84/108); os 107 sao o estado DEPOIS de #47 (perda de 1 aceita ja registrada em regra_secao_efeito_subunidade_21-09). A primaria (84) e identica nos dois estados.
- divergencia: abstencoes: 32 materiais nao certos com subunidade predita vazia; 1 deles tambem esta em bloqueio_unidade e por isso sai dos 144 do coordenador -> 31 dentro dos 144. Bate.
- divergencia: relacao_ausente + falha_selecao = 159 > 144 por sobreposicao deliberada (E): a diferenca de 15 e exatamente bloqueio_unidade (10) + gold_fora_da_taxonomia (5), que tambem recebem classe de sinal.

## 2. Expressoes candidatas

| curso | ocorrencias | expressoes | ja conhecidas (taxonomia) | novas | novas >=5 mat. | >=3 | 2 | 1 |
|---|---|---|---|---|---|---|---|---|
| MF | 922 | 410 | 30 | 380 | 19 | 40 | 42 | 298 |
| SO | 483 | 196 | 13 | 183 | 9 | 22 | 10 | 151 |
| IA | 3056 | 1632 | 31 | 1601 | 47 | 106 | 276 | 1219 |
| ES2 | 1470 | 803 | 28 | 775 | 62 | 93 | 66 | 616 |
| TCC | 1429 | 840 | 44 | 796 | 13 | 54 | 98 | 644 |
| CG | 2234 | 1028 | 65 | 963 | 34 | 106 | 102 | 755 |
| FR | 818 | 608 | 34 | 574 | 5 | 13 | 41 | 520 |

## 3. Cobertura sobre os nao certos

| curso | nao certos | com expressao nova | sem nenhuma | perguntas | ate 50% | ate 80% | ate 100% |
|---|---|---|---|---|---|---|---|
| MF | 33 | 30 | 3 | 17 | 4 | 11 | 17 |
| SO | 8 | 8 | 0 | 5 | 1 | 3 | 5 |
| IA | 35 | 35 | 0 | 6 | 1 | 2 | 6 |
| ES2 | 21 | 21 | 0 | 2 | 1 | 1 | 2 |
| TCC | 4 | 4 | 0 | 2 | 1 | 1 | 1 |
| CG | 54 | 47 | 7 | 11 | 1 | 4 | 7 |
| FR | 12 | 12 | 0 | 7 | 2 | 5 | 7 |

## 4. Conflitos das perguntas

| curso | perguntas | >1 unidade vigente | tocam material certo | subunidade divergente entre certos |
|---|---|---|---|---|
| MF | 17 | 5 | 10 | 7 |
| SO | 5 | 4 | 4 | 1 |
| IA | 6 | 0 | 4 | 0 |
| ES2 | 2 | 2 | 2 | 1 |
| TCC | 2 | 1 | 2 | 1 |
| CG | 11 | 7 | 11 | 4 |
| FR | 7 | 3 | 4 | 4 |

## 5. As 20 primeiras perguntas por curso

### MF

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | julio machado | 24 | 24 | 42.1 | unidade-01-metodos-formais, unidade-02-verificacao-de-programas, unida | sim | 15 |
| 2 | logicadehoare | 6 | 30 | 52.6 | unidade-01-metodos-formais, unidade-02-verificacao-de-programas | sim | 3 |
| 3 | arvore | 3 | 33 | 57.9 | unidade-01-metodos-formais, unidade-02-verificacao-de-programas | sim | 3 |
| 4 | arrays | 3 | 36 | 63.2 | unidade-02-verificacao-de-programas |  |  |
| 5 | conceitos | 3 | 39 | 68.4 | unidade-01-metodos-formais, unidade-03-verificacao-de-modelos | sim | 2 |
| 6 | pagina | 2 | 41 | 71.9 | unidade-01-metodos-formais, unidade-02-verificacao-de-programas | sim | 3 |
| 7 | provas | 2 | 43 | 75.4 | unidade-01-metodos-formais |  | 5 |
| 8 | colecoes | 2 | 45 | 78.9 | unidade-02-verificacao-de-programas |  |  |
| 9 | seguinte | 2 | 47 | 82.5 | unidade-01-metodos-formais |  | 2 |
| 10 | dafny | 1 | 48 | 84.2 | unidade-02-verificacao-de-programas |  |  |
| 11 | floyd hoare | 1 | 49 | 86.0 | unidade-02-verificacao-de-programas |  | 1 |
| 12 | classes | 1 | 50 | 87.7 | unidade-02-verificacao-de-programas |  |  |
| 13 | definicao | 1 | 51 | 89.5 | unidade-01-metodos-formais |  | 3 |
| 14 | terminacao | 1 | 52 | 91.2 | unidade-02-verificacao-de-programas |  | 1 |
| 15 | intro | 1 | 53 | 93.0 | unidade-01-metodos-formais |  |  |
| 16 | nusmv | 1 | 54 | 94.7 | unidade-03-verificacao-de-modelos |  |  |
| 17 | tiposindutivos | 1 | 55 | 96.5 | unidade-02-verificacao-de-programas |  |  |

### SO

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | include | 8 | 8 | 53.3 | unidade-01-introducao-ao-estudo-de-sistemas-operacionais, unidade-02-g | sim | 4 |
| 2 | defini | 4 | 12 | 80.0 | unidade-01-introducao-ao-estudo-de-sistemas-operacionais, unidade-02-g | sim | 2 |
| 3 | estado | 1 | 13 | 86.7 | unidade-01-introducao-ao-estudo-de-sistemas-operacionais, unidade-02-g | sim | 1 |
| 4 | multiplas | 1 | 14 | 93.3 | unidade-01-introducao-ao-estudo-de-sistemas-operacionais, unidade-02-g | sim | 1 |
| 5 | homework | 1 | 15 | 100.0 | unidade-02-gerencia-do-processador |  |  |

### IA

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | celula | 24 | 24 | 61.5 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  | 2 |
| 2 | artificiais | 8 | 32 | 82.1 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  | 1 |
| 3 | references | 4 | 36 | 92.3 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  | 1 |
| 4 | rede | 1 | 37 | 94.9 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  |  |
| 5 | iris | 1 | 38 | 97.4 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  | 1 |
| 6 | java | 1 | 39 | 100.0 | unidade-de-aprendizagem-05-aprendizado-de-maquina |  |  |

### ES2

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | engenharia | 20 | 20 | 71.4 | unidade-01-arquitetura-de-software, unidade-02-integracao-de-desenvolv | sim | 3 |
| 2 | codigo | 8 | 28 | 100.0 | unidade-01-arquitetura-de-software, unidade-02-integracao-de-desenvolv | sim | 4 |

### TCC

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | exerc icio | 10 | 10 | 90.9 | unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas, unidade-02-turi | sim | 6 |
| 2 | minimizac | 1 | 11 | 100.0 | unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas |  | 3 |

### CG

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | extraido | 43 | 43 | 57.3 | unidade-01-introducao-ao-processamento-grafico, unidade-02-fundamentos | sim | 14 |
| 2 | ponto | 8 | 51 | 68.0 | unidade-01-introducao-ao-processamento-grafico, unidade-02-fundamentos | sim | 2 |
| 3 | slides | 7 | 58 | 77.3 | unidade-01-introducao-ao-processamento-grafico, unidade-02-fundamentos | sim | 6 |
| 4 | glut | 6 | 64 | 85.3 | unidade-01-introducao-ao-processamento-grafico, unidade-02-fundamentos | sim | 2 |
| 5 | processamento | 3 | 67 | 89.3 | unidade-03-processamento-de-imagens-e-visao-computacional, unidade-04- | sim | 1 |
| 6 | python | 3 | 70 | 93.3 | unidade-01-introducao-ao-processamento-grafico, unidade-02-fundamentos | sim | 2 |
| 7 | include | 1 | 71 | 94.7 | unidade-02-fundamentos-matematicos, unidade-04-processo-de-visualizaca | sim | 1 |
| 8 | segmentacao texturas | 1 | 72 | 96.0 | unidade-03-processamento-de-imagens-e-visao-computacional |  | 3 |
| 9 | modelagem geometrica | 1 | 73 | 97.3 | unidade-07-representacao-e-modelagem-de-objetos |  | 1 |
| 10 | curvas bezier | 1 | 74 | 98.7 | unidade-07-representacao-e-modelagem-de-objetos |  | 5 |
| 11 | zbuffer | 1 | 75 | 100.0 | unidade-06-processo-de-visualizacao-3d |  | 1 |

### FR

| # | expressao (forma) | marg. | acum. | acum.% | unidades vigentes sugeridas | conf.unid | toca certo |
|---|---|---|---|---|---|---|---|
| 1 | referencia | 9 | 9 | 50.0 | unidade-01-introducao-a-redes-de-computadores, unidade-02-nivel-de-apl | sim | 4 |
| 2 | example | 3 | 12 | 66.7 | unidade-02-nivel-de-aplicacao |  |  |
| 3 | mensagem | 2 | 14 | 77.8 | unidade-02-nivel-de-aplicacao |  | 4 |
| 4 | camada | 1 | 15 | 83.3 | unidade-01-introducao-a-redes-de-computadores, unidade-02-nivel-de-apl | sim | 3 |
| 5 | requisicao | 1 | 16 | 88.9 | unidade-02-nivel-de-aplicacao |  |  |
| 6 | rede | 1 | 17 | 94.4 | unidade-01-introducao-a-redes-de-computadores, unidade-02-nivel-de-apl | sim | 3 |
| 7 | server | 1 | 18 | 100.0 | unidade-02-nivel-de-aplicacao |  |  |

