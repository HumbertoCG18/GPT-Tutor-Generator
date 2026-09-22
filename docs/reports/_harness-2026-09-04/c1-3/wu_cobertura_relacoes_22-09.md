# W-U (CRU-02) - cobertura de relacoes explicitas recuperaveis do proprio pacote

Read-only, fora de `src/`. Branch `feat/motor-atribuicao`, HEAD `410592d`, 22/09.
Gold SO AVALIA: indice construido para todos os topicos/materiais e congelado antes de ler o gold.

- congelamento do indice (sha256, antes do gold): `c17786ef89c2e59ab0ee3e786bb03e8d8713e27c8affc9289e39a609aafb3d0e`
- sha256 do JSON: `bd7a6ccb70ff1d8ee1ba825adec84fb3a28f120e9a7beb4bb25444bbf6cc07e7`

## 1. Definicoes congeladas

- **E**: chave stem6 do W-P1
- **T**: (unit_slug, slug) da taxonomia
- **P1**: E em heading/lista de outro material sob heading ancestral que menciona T
- **P2**: E e mencao a T na mesma linha de heading/lista/tabela
- **P3**: E no texto de bloco/sessao do plano cujo texto menciona T
- **P4**: E sob heading que menciona T em syllabus/glossario/cronograma/plano de ensino
- n-grama 1..3 tokens, stem6, trecho <= 160 c. Relacao so vale se o documento de origem NAO e o proprio material.

## 2. Documentos do pacote: usados e excluidos

| curso | markdown de materiais | docs de course/ | plano+ementa (_inputs_15-09.json) | timeline | lessons |
|---|---|---|---|---|---|
| CG | 72 | 5 | 2 | sim | nao |
| ES2 | 27 | 5 | 2 | sim | sim |
| FR | 15 | 5 | 2 | sim | nao |
| IA | 57 | 5 | 2 | sim | sim |
| MF | 54 | 5 | 2 | sim | sim |
| SO | 41 | 5 | 2 | sim | nao |
| TCC | 27 | 5 | 2 | sim | nao |

Docs de `course/` usados: SYLLABUS.md, CRONOGRAMA_DETALHADO.md, GLOSSARY.md, COURSE_IDENTITY.md, SOURCE_REGISTRY.yaml.
`course/.lessons_index.json` so existe em ES2, IA e MF.

Excluidos por proveniencia (vazamento da propria classificacao do motor):

- `BUILD_REPORT.md` - relatorio do build
- `README.md` - boilerplate do pacote
- `course/.assessment_context.json` - contexto computado no build
- `course/.block_identity.json` - identidade de bloco computada no build
- `course/.card_block_map.json` - mapa card->bloco computado no build
- `course/.semantic_profile.generated.json` - perfil gerado pelo build
- `course/.tag_catalog.json` - tags auto computadas
- `course/CODE_HEALTH.md` - relatorio derivado do build
- `course/COURSE_MAP.md` - deriva do file map
- `course/CRONOGRAMA_HEALTH.md` - relatorio derivado do build
- `course/FILE_MAP.md` - saida do file map (classificacao do motor)
- `course/FILE_MAP_TRACE.md` - trace da classificacao do motor
- `manifest.json (computed_*)` - campos computados pelo motor

De `.timeline_index.json` usou-se apenas o TEXTO (topic_text, topics, period_label, sessions[].label);
`primary_topic_slug` e `topic_candidates` sao escore do proprio motor sobre a taxonomia e ficaram de fora.

## 3. Tamanho do indice

- relacoes (E, T, doc, trecho, padrao) distintas: **11663**
- por padrao: P1=2681, P2=7258, P3=254, P4=1470
- por curso: CG=1909, ES2=732, FR=4188, IA=2337, MF=648, SO=663, TCC=1186
- E distintas com ao menos uma relacao: **1971** (dessas, 1726 nao sao `ja_conhecida` do W-P1)
- universo de E por curso: CG=1028, ES2=803, FR=608, IA=1632, MF=410, SO=196, TCC=840
- topicos (unit_slug, slug) alcancados: **199**
- distribuicao de T por E: 1 topico=922, 2-4=615, >=5=434 -> **1049 de 1971 E sao ambiguas (>=2 topicos)**

## 4. Cobertura A / A-conflitante / B

| grupo | n | A | A-conflitante | B | A total | % A total |
|---|---|---|---|---|---|---|
| relacao_ausente_106 | 106 | 1 | 55 | 50 | 56 | 53% |
| falha_selecao_53 | 53 | 1 | 52 | 0 | 53 | 100% |
| certos_84 | 84 | 0 | 70 | 14 | 70 | 83% |

### relacao_ausente_106

| curso | A | A-conflitante | B |
|---|---|---|---|
| CG | 0 | 17 | 20 |
| ES2 | 0 | 1 | 5 |
| FR | 0 | 1 | 2 |
| IA | 1 | 26 | 0 |
| MF | 0 | 7 | 19 |
| SO | 0 | 3 | 4 |

Materiais cujo acerto no gold veio de cada padrao (um material pode ter varios): P1=29, P2=35, P3=17, P4=46

Topicos conflitantes por material (entre A/A-conflitante): 0=1, 1-4=5, 5-19=39, >=20=11

Sobreposicao dos B com o residual do W-P1: B_puro=40, bloqueio_unidade=5, gold_fora_da_taxonomia=5

Lista dos B (curso / entry_id / gold / classes do W-P1):

- CG / `animacao-v2` / gold `(vazio)` / gold_fora_da_taxonomia, relacao_ausente
- CG / `atividade` / gold `conceito-de-camera-sintetica` / relacao_ausente
- CG / `basico3d-cpp` / gold `tecnicas-de-modelagem-3d` / bloqueio_unidade, relacao_ausente
- CG / `basico3d-py` / gold `conceito-de-camera-sintetica` / relacao_ausente
- CG / `basico3d-py-zip` / gold `tecnicas-de-modelagem-3d` / bloqueio_unidade, relacao_ausente
- CG / `exercicio-com-animacao` / gold `operacoes-com-vetores` / relacao_ausente
- CG / `exercicio-de-animacao-foguete` / gold `operacoes-com-vetores` / relacao_ausente
- CG / `exercicios` / gold `aplicacoes` / bloqueio_unidade, relacao_ausente
- CG / `instanciamento` / gold `(vazio)` / gold_fora_da_taxonomia, relacao_ausente
- CG / `opengl-cpp` / gold `aplicacoes` / relacao_ausente
- CG / `opengl-py` / gold `aplicacoes` / relacao_ausente
- CG / `opengl3dcpp` / gold `conceito-de-camera-sintetica` / relacao_ausente
- CG / `opengl3dcpp-vdi` / gold `conceito-de-camera-sintetica` / relacao_ausente
- CG / `openglbasico` / gold `aplicacoes` / bloqueio_unidade, relacao_ausente
- CG / `pagina-com-videos-sobre-instanciamento` / gold `(vazio)` / gold_fora_da_taxonomia, relacao_ausente
- CG / `pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156` / gold `introducao-e-exemplos-de-aplicacoes` / relacao_ausente
- CG / `pagina-com-videos-sobre-mapeamento-9f410e` / gold `sistema-de-coordenadas-cartesianas` / relacao_ausente
- CG / `pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea` / gold `modelos-de-iluminacao-luz-pontual-direcional-spot` / relacao_ausente
- CG / `transformacoesgeometricas` / gold `(vazio)` / gold_fora_da_taxonomia, relacao_ausente
- CG / `transformacoesgl` / gold `(vazio)` / gold_fora_da_taxonomia, relacao_ausente
- ES2 / `kubernetes` / gold `plataformas-de-devops` / relacao_ausente
- ES2 / `roteiro1` / gold `estudo-de-caso-arquitetura-orientada-a-microsservicos` / relacao_ausente
- ES2 / `roteiro2` / gold `estudo-de-caso-arquitetura-orientada-a-microsservicos` / relacao_ausente
- ES2 / `roteiro3` / gold `estudo-de-caso-arquitetura-orientada-a-microsservicos` / relacao_ausente
- ES2 / `roteiro4` / gold `estudo-de-caso-integracao-e-implantacao-de-microsservicos` / bloqueio_unidade, relacao_ausente
- FR / `lista-de-exercicios-1-camada-de-aplicacao` / gold `funcoes-e-caracteristicas-do-nivel-de-aplicacao` / relacao_ausente
- FR / `unidade1-exercicios` / gold `modelos-osi-e-tcpip` / relacao_ausente
- MF / `classes-parte2` / gold `verificacao-de-programas` / relacao_ausente
- MF / `colecoes-arrays` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `colecoes-conjuntos` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `colecoes-sequences` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exemplos` / gold `softwares-de-suporte-a-verificacao-formal-de-modelos` / relacao_ausente
- MF / `exercicios-arrays` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exercicios-conjuntos` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosdafny1` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosdafny2` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosdafny3` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosdafny4` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosdafny5` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `exerciciosnusmv` / gold `softwares-de-suporte-a-verificacao-formal-de-modelos` / relacao_ausente
- MF / `intro` / gold `provadores-de-teoremas` / relacao_ausente
- MF / `introducao-zip` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- MF / `logicaproposicional-semantica` / gold `linguagens-de-especificacao-e-logicas` / relacao_ausente
- MF / `logicaproposicional-sintaxe` / gold `linguagens-de-especificacao-e-logicas` / relacao_ausente
- MF / `revisao` / gold `sistemas-formais` / relacao_ausente
- MF / `tiposindutivos` / gold `softwares-de-suporte-a-verificacao-formal-de-programas` / relacao_ausente
- SO / `exemplo-threads-em-c-exemplo1` / gold `conceitos-basicos` / relacao_ausente
- SO / `exemplo-threads-em-c-exemplo2` / gold `conceitos-basicos` / relacao_ausente
- SO / `exemplo-threads-em-c-exemplo3` / gold `conceitos-basicos` / relacao_ausente
- SO / `exercicios` / gold `algoritmos-de-escalonamento` / relacao_ausente

### falha_selecao_53

| curso | A | A-conflitante | B |
|---|---|---|---|
| CG | 0 | 10 | 0 |
| ES2 | 0 | 15 | 0 |
| FR | 0 | 9 | 0 |
| IA | 0 | 8 | 0 |
| MF | 1 | 5 | 0 |
| SO | 0 | 1 | 0 |
| TCC | 0 | 4 | 0 |

Materiais cujo acerto no gold veio de cada padrao (um material pode ter varios): P1=11, P2=53, P3=14, P4=27

Topicos conflitantes por material (entre A/A-conflitante): 0=1, 1-4=3, 5-19=34, >=20=15

### certos_84

| curso | A | A-conflitante | B |
|---|---|---|---|
| CG | 0 | 26 | 2 |
| ES2 | 0 | 3 | 4 |
| FR | 0 | 5 | 1 |
| IA | 0 | 4 | 0 |
| MF | 0 | 19 | 6 |
| SO | 0 | 7 | 0 |
| TCC | 0 | 6 | 1 |

Materiais cujo acerto no gold veio de cada padrao (um material pode ter varios): P1=12, P2=69, P3=18, P4=38

Topicos conflitantes por material (entre A/A-conflitante): 1-4=2, 5-19=47, >=20=21

Sobreposicao dos B com o residual do W-P1: B_puro=14

Lista dos B (curso / entry_id / gold / classes do W-P1):

- CG / `exemplozbuffer` / gold `algoritmo-z-buffer` / 
- CG / `programabasico3d` / gold `modelos-de-reflexao-ambiente-difusa-especular` / 
- ES2 / `roteiro5` / gold `estudo-de-caso-integracao-e-implantacao-de-microsservicos` / 
- ES2 / `roteiro6` / gold `estudo-de-caso-integracao-e-implantacao-de-microsservicos` / 
- ES2 / `roteiro7` / gold `estudo-de-caso-integracao-e-implantacao-de-microsservicos` / 
- ES2 / `roteiro7-history-service` / gold `estudo-de-caso-integracao-e-implantacao-de-microsservicos` / 
- FR / `02-modelos-de-referencia` / gold `modelos-osi-e-tcpip` / 
- MF / `exerciciosespecificacao` / gold `linguagens-de-especificacao-e-logicas` / 
- MF / `exerciciosespecificacao-respostas` / gold `linguagens-de-especificacao-e-logicas` / 
- MF / `exerciciosformalizacaoalgoritmosrecursao-respostas` / gold `especificacao-de-funcoes-recursivas` / 
- MF / `exerciciosformalizacaoalgoritmosrecursao3-respostas` / gold `especificacao-de-funcoes-recursivas` / 
- MF / `logicadehoare-exercicios-respostas` / gold `logica-de-hoare` / 
- MF / `provasindutivas-especificacoesrecursivas-listas` / gold `especificacao-de-funcoes-recursivas` / 
- TCC / `aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos` / gold `(vazio)` / 

## 5. Ruido do indice (controle nos 84 certos)

- certos com relacao para o gold: **70/84**
- certos sem relacao para o gold: **14/84**
- certos que, alem do gold, tem relacao para outros topicos: **70** (todo certo coberto e tambem conflitante)

## 6. Exemplos

Dez relacoes recuperadas para materiais dos 106:

- CG `exerciciodemodelagem` gold `varredura` <- E `objeto` -> T `varredura` [P2] em `material:modelagem3d`: "**Figura 6 - Criação de objetos por varredura translacional**"
- CG `exercicioduascores` gold `algoritmos-de-quantizacao-e-amostragem` <- E `imagen` -> T `algoritmos-de-quantizacao-e-amostragem` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 03 — Processamento de Imagens e Visão Computacional"
- CG `exercicios-de-processamento-de-imagens` gold `algoritmos-de-quantizacao-e-amostragem` <- E `proces` -> T `algoritmos-de-quantizacao-e-amostragem` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 03 — Processamento de Imagens e Visão Computacional"
- CG `exercicios-sobre-curvas` gold `catmull-rom` <- E `curvas` -> T `catmull-rom` [P1] em `material:curvasparametricas`: "- Montada a partir de uma sequência de curvas Hermite"
- CG `exercicios-sobre-curvas-html` gold `catmull-rom` <- E `curvas` -> T `catmull-rom` [P1] em `material:curvasparametricas`: "- Montada a partir de uma sequência de curvas Hermite"
- CG `exercicios-teoricos-sobre-processo-de-visualizacao-2d` gold `sistema-de-coordenadas-cartesianas` <- E `proces` -> T `sistema-de-coordenadas-cartesianas` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 04 — Processo de Visualização 2D"
- CG `exercicios-teoricos-sobre-processo-de-visualizacao-2d-html` gold `sistema-de-coordenadas-cartesianas` <- E `proces` -> T `sistema-de-coordenadas-cartesianas` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 04 — Processo de Visualização 2D"
- CG `floodfill` gold `segmentacao` <- E `extrai` -> T `segmentacao` [P1] em `material:pagina-com-videos-sobre-segmentacao-de-imagens-d0627f`: "Conteúdo Extraído"
- CG `fundamentosmatematicos` gold `entidades-geometricas` <- E `matema` -> T `entidades-geometricas` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 02 — Fundamentos Matemáticos"
- CG `mapeamento` gold `sistema-de-coordenadas-cartesianas` <- E `proces` -> T `sistema-de-coordenadas-cartesianas` [P4] em `course/GLOSSARY.md`: "**Aparece em:** Unidade 04 — Processo de Visualização 2D"

Cinco conflitos:

- CG `exerciciodemodelagem` gold `varredura`: 27 topicos concorrentes (ex.: 2d-3d-mao-direita-e-mao-esquerda, a-matematica-das-projecoes-planares, algoritmo-do-pintor, algoritmo-z-buffer, arvores-bsp)
- CG `exercicioduascores` gold `algoritmos-de-quantizacao-e-amostragem`: 13 topicos concorrentes (ex.: a-matematica-das-projecoes-planares, composicao-de-transformacoes-2d, composicao-de-transformacoes-3d, conceitos, cores-e-tipos-de-imagens)
- CG `exercicios-de-processamento-de-imagens` gold `algoritmos-de-quantizacao-e-amostragem`: 35 topicos concorrentes (ex.: 2d-3d-mao-direita-e-mao-esquerda, a-matematica-das-projecoes-planares, algoritmo-do-pintor, algoritmo-z-buffer, algoritmos-de-rasterizacao)
- CG `exercicios-sobre-curvas` gold `catmull-rom`: 10 topicos concorrentes (ex.: a-matematica-das-projecoes-planares, b-spline, composicao-de-transformacoes-2d, composicao-de-transformacoes-3d, formas-de-representacao)
- CG `exercicios-sobre-curvas-html` gold `catmull-rom`: 10 topicos concorrentes (ex.: a-matematica-das-projecoes-planares, b-spline, composicao-de-transformacoes-2d, composicao-de-transformacoes-3d, formas-de-representacao)

## 7. Limitacoes

- Documentos excluidos por proveniencia de saida do motor listados em documentos[*].excluidos_por_proveniencia.
- P3 usa apenas o TEXTO do bloco/sessao (topic_text/topics/labels); primary_topic_slug e topic_candidates sao escores do proprio motor sobre a taxonomia e foram excluidos.
- Mencao a T exige label/alias contiguo em stem6; topicos cujo label so aparece parafraseado nao sao detectados.
- Relacao = existencia, nao 'assunto principal'.

