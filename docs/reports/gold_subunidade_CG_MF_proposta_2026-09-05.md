# Gold de subunidade CG e MF — PROPOSTA (proposto-claude 2026-09-05, aguarda aprovacao)

Regras: subtopico dentro da UNIDADE COMPUTADA; unidade computada errada -> `scorable=no` com a unidade verdadeira na nota; meta (plano,
cronograma, playlist, provas, revisao para prova) -> `scorable=no`; ferramenta sem subtopico na taxonomia (OpenGL) -> gold vazio; codigo pelo
CONTEUDO (resumo) e, quando o resumo esta errado (colisao de nomes nos zips do MF), pelo LABEL do Moodle. Marque na coluna `ok?`: sim / nao / outro.

## CG — 93 materiais, 63 pontuaveis, 30 fora

### Pontuaveis

| ok? | entry | card | pred (produto) | GOLD | extras | fonte | nota |
|---|---|---|---|---|---|---|---|
| | `intro` | 1 - Origens da Computação Gr | areas-relacionadas ~ | **conceitos** | areas-relacionadas | conteudo | pagina 'Origens' mas o texto e a classificacao de CG passiva/interativa (Rogers e Adams) = conceitos |
| | `origensdacomputacaografica` | 1 - Origens da Computação Gr | origens = | **origens** |  | conteudo | Whirlwind, SAGE, Sketchpad, mouse |
| | `segmentacaopptx` | 10 - Segmentação de Imagens | segmentacao = | **segmentacao** |  | conteudo |  |
| | `segmentacaodetexturas` | 10 - Segmentação de Imagens | segmentacao = | **segmentacao** |  | conteudo | co-ocorrencia de niveis de cinza para segmentar texturas |
| | `atividade` | 13 - Computação Gráfica 3D | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes | conteudo | tarefas: coordenadas do observador e do alvo, mover o observador |
| | `basico3d-py` | 13 - Computação Gráfica 3D | perspectiva X | **conceito-de-camera-sintetica** | pipeline-de-visualizacao-3d ; projecoes | conteudo | resumo: cena 3D, gluLookAt, iluminacao, ModelView |
| | `opengl3d` | 13 - Computação Gráfica 3D | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | conteudo | 'funcoes de projecao e manipulacao da camera em OpenGL' |
| | `opengl3dcpp-vdi` | 13 - Computação Gráfica 3D | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | card | bundle misto (2D/3D/Bezier/imagens); rotulado pelo LABEL 'Projeto VDI de OpenGL 3D' + card 13 — RULING pendent |
| | `opengl3dcpp` | 13 - Computação Gráfica 3D | perspectiva X | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | card | bundle misto; LABEL 'Projeto de OpenGL 3D em C++' + card 13 — RULING pendente |
| | `vis3d` | 13 - Computação Gráfica 3D | paralela ~ | **projecoes** | paralela ; perspectiva ; conceito-de-camera-sintetica ; a-matematica-das-projecoes-planares | conteudo | PROJECOES, paralela ortografica, perspectiva, observador, sistema da camera |
| | `elemoculto` | 15 - Remoção de Elementos Oc | algoritmo-z-buffer ~ | **algoritmos-de-remocao-de-elementos-ocultos** | eliminacao-de-faces-traseiras ; algoritmo-do-pintor ; algoritmo-z-buffer ; arvores-bsp | conteudo | slides-roteiro da remocao de elementos ocultos (faces traseiras, z-buffer, pintor) |
| | `exemplozbuffer` | 15 - Remoção de Elementos Oc | algoritmo-z-buffer = | **algoritmo-z-buffer** |  | conteudo |  |
| | `iluminacao` | 16 - Síntese de Imagens Real | modelos-de-reflexao-ambiente-difusa-especular ~ | **modelos-de-iluminacao-luz-pontual-direcional-spot** | modelos-de-reflexao-ambiente-difusa-especular ; metodos-de-sombreamento-flat-gouraud-phong | conteudo | pagina: modelos de iluminacao + modelos de tonalizacao |
| | `programabasico3d` | 16 - Síntese de Imagens Real | modelos-de-reflexao-ambiente-difusa-especular = | **modelos-de-reflexao-ambiente-difusa-especular** | modelos-de-iluminacao-luz-pontual-direcional-spot ; projecoes | conteudo | codigo usado em aula (card 16): configura ambiente/difusa/especular |
| | `exercicios` | 2 - Biblioteca OpenGL | conceitos X | **(vazio)** |  | conteudo | exercicios de introducao a OpenGL: ferramenta, sem subtopico na taxonomia; resposta honesta = vazio (pred 'con |
| | `opengl-cpp` | 2 - Biblioteca OpenGL | conceitos X | **(vazio)** |  | conteudo | bundle de projetos OpenGL (ferramenta): sem subtopico; vazio |
| | `opengl-py` | 2 - Biblioteca OpenGL | conceitos X | **(vazio)** |  | conteudo | bundle de projetos OpenGL (ferramenta): sem subtopico; vazio |
| | `openglbasico` | 2 - Biblioteca OpenGL | conceitos X | **(vazio)** |  | conteudo | tutorial de instalacao/uso de OpenGL: ferramenta; vazio |
| | `exercicio-com-animacao` | 3 - Fundamentos Matemáticos  | - X | **operacoes-com-vetores** | entidades-geometricas | conteudo | triangulo atravessa a tela em tempo fixo = deslocamento por vetor |
| | `exercicio-com-poligonos` | 3 - Fundamentos Matemáticos  | algoritmos-de-poligonos = | **algoritmos-de-poligonos** |  | conteudo | ponto dentro/fora do poligono |
| | `exercicio-de-animacao-foguete` | 3 - Fundamentos Matemáticos  | algoritmos-de-poligonos ~ | **operacoes-com-vetores** | algoritmos-de-poligonos | conteudo | foguete de poligonos deslocado por PosFoguete (vetor) |
| | `fundamentosmatematicos` | 3 - Fundamentos Matemáticos  | entidades-geometricas = | **entidades-geometricas** | operacoes-com-vetores | conteudo | pontos, vetores, retas; operacoes |
| | `matematica` | 3 - Fundamentos Matemáticos  | entidades-geometricas ~ | **operacoes-com-vetores** | entidades-geometricas | conteudo | classe Vetor 2D: translacao, escala, vetor resultante; label 'Produto Escalar' |
| | `colisao` | 4 - Detecção de Colisão | algoritmos-de-deteccao-e-calculo-de-interseccao = | **algoritmos-de-deteccao-e-calculo-de-interseccao** |  | conteudo | AABB/OOBB, envelopes |
| | `geomcomp` | 5 - Geometria Computacional | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | conteudo |  |
| | `recorte` | 6 - Processo de Visualização | recorte = | **recorte** |  | conteudo | Cohen-Sutherland |
| | `vis2d` | 6 - Processo de Visualização | recorte ~ | **sistema-de-coordenadas-cartesianas** | recorte | conteudo | introducao ao processo 2D (instanciamento, recorte, mapeamento, sistemas de referencia); alternativa u05/pipel |
| | `bezier-animacao` | 7 - Curvas Paramétricas | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-cpp` | 7 - Curvas Paramétricas | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-py` | 7 - Curvas Paramétricas | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-python` | 7 - Curvas Paramétricas | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo | quadraticas e cubicas; animacao |
| | `curvas` | 7 - Curvas Paramétricas | hermite ~ | **representacao-de-curvas-parametricas** | bezier-e-algoritmo-de-casteljau ; hermite ; catmull-rom ; b-spline | conteudo | pagina geral de curvas parametricas |
| | `curvasparametricas` | 7 - Curvas Paramétricas | - X | **representacao-de-curvas-parametricas** | bezier-e-algoritmo-de-casteljau ; hermite ; catmull-rom ; b-spline | conteudo | slides: forma parametrica x nao parametrica |
| | `exercicios-sobre-curvas` | 7 - Curvas Paramétricas | hermite X | **catmull-rom** | representacao-de-curvas-parametricas ; bezier-e-algoritmo-de-casteljau | conteudo | 1a questao: Catmull-Rom por 4 pontos |
| | `floodfill` | 8 - Manipulação de Imagens | segmentacao = | **segmentacao** |  | conteudo | flood fill = crescimento de regiao; alternativa u04/preenchimento-de-poligonos (card 8 Manipulacao de Imagens) |
| | `img` | 8 - Manipulação de Imagens | filtros ~ | **cores-e-tipos-de-imagens** | filtros ; algoritmos-de-quantizacao-e-amostragem | conteudo | 1. Tipos de imagens (true-color...) |
| | `remocaoderuido` | 8 - Manipulação de Imagens | filtros = | **filtros** |  | conteudo |  |
| | `exercicios-de-processamento-de-imagens` | 9 - Introdução ao Processame | cores-e-tipos-de-imagens ~ | **algoritmos-de-quantizacao-e-amostragem** | cores-e-tipos-de-imagens ; filtros ; segmentacao | conteudo | 1a questao: copia de imagem de 64 tons (quantizacao); lista cobre varios |
| | `introducaoprocimg` | 9 - Introdução ao Processame | filtros = | **filtros** | introducao-e-exemplos-de-aplicacoes ; cores-e-tipos-de-imagens | conteudo | histogramas, equalizacao, convolucao, Sobel |
| | `exercicios-de-geometria-computacional` | Exercícios 2D | entidades-geometricas X | **algoritmos-de-geometria-computacional** |  | conteudo | matriz de dominancia |
| | `exercicios-sobre-curvas-html` | Exercícios 2D | hermite X | **catmull-rom** | representacao-de-curvas-parametricas ; bezier-e-algoritmo-de-casteljau | conteudo | duplicata html de exercicios-sobre-curvas |
| | `exerciciosfundamentosmatematicos` | Exercícios 2D | algoritmos-de-poligonos = | **algoritmos-de-poligonos** | operacoes-com-vetores | conteudo | 3 de 4 questoes sobre poligonos (concavidade, inclusao de ponto) |
| | `domina` | 5 - Geometria Computacional | entidades-geometricas X | **algoritmos-de-geometria-computacional** |  | conteudo | contagem geometrica / matriz de dominancia |
| | `planesweep` | 5 - Geometria Computacional | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | conteudo |  |
| | `slab` | 5 - Geometria Computacional | algoritmos-de-poligonos ~ | **algoritmos-de-geometria-computacional** | algoritmos-de-poligonos | conteudo | pesquisa geometrica: em qual poligono esta o ponto (slab) |
| | `exercicioduascores` | 8 - Manipulação de Imagens | - X | **algoritmos-de-quantizacao-e-amostragem** | cores-e-tipos-de-imagens | conteudo | padroes de halftone (2 cores) = quantizacao |
| | `video-sobre-origens-da-computacao-grafic` | 1 - Origens da Computação Gr | origens = | **origens** |  | titulo |  |
| | `video-com-instrucoes-para-usar-opengl-na` | 2 - Biblioteca OpenGL | conceitos X | **(vazio)** |  | titulo | ferramenta (OpenGL na VDI): vazio |
| | `pagina-com-videos-sobre-fundamentos-mate` | 3 - Fundamentos Matemáticos  | - X | **entidades-geometricas** | operacoes-com-vetores | titulo | conteudo capturado = pagina de login do Moodle; rotulo pelo titulo |
| | `videos-sobre-algoritmos-de-detecao-de-co` | 4 - Detecção de Colisão | - ~ | **algoritmos-de-deteccao-e-calculo-de-interseccao** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-geometria-comput` | 5 - Geometria Computacional | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-recorte-e257d3` | 6 - Processo de Visualização | recorte = | **recorte** |  | titulo | conteudo capturado = login do Moodle |
| | `video-sobre-o-algoritmo-de-recorte-por-s` | 6 - Processo de Visualização | recorte = | **recorte** |  | titulo |  |
| | `pagina-com-videos-sobre-curvas-parametri` | 7 - Curvas Paramétricas | representacao-de-curvas-parametricas = | **representacao-de-curvas-parametricas** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-manipulacao-de-i` | 8 - Manipulação de Imagens | cores-e-tipos-de-imagens = | **cores-e-tipos-de-imagens** | filtros | titulo | mesmo assunto da pagina 'img' (tipos de imagens) |
| | `pagina-com-videos-sobre-introducao-ao-pr` | 9 - Introdução ao Processame | - X | **introducao-e-exemplos-de-aplicacoes** | filtros | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-segmentacao-de-i` | 10 - Segmentação de Imagens | segmentacao = | **segmentacao** |  | titulo |  |
| | `pagina-com-videos-sobre-segmentacao-por-` | 10 - Segmentação de Imagens | segmentacao = | **segmentacao** |  | titulo |  |
| | `video-sobre-prechimento-de-areas-duracao` | Exercícios de Processamento  | segmentacao = | **segmentacao** |  | titulo | preenchimento de area (flood fill), como floodfill; alternativa u04/preenchimento-de-poligonos |
| | `video-sobre-prechimento-de-areas-duracao` | Exercícios de Processamento  | segmentacao = | **segmentacao** |  | titulo | idem |
| | `pagina-com-videos-sobre-visualizacao-3d-` | 13 - Computação Gráfica 3D | pipeline-de-visualizacao-3d = | **pipeline-de-visualizacao-3d** | projecoes ; conceito-de-camera-sintetica | titulo |  |
| | `pagina-com-videos-sobre-remocao-de-eleme` | 15 - Remoção de Elementos Oc | algoritmos-de-remocao-de-elementos-ocultos = | **algoritmos-de-remocao-de-elementos-ocultos** |  | titulo |  |
| | `pagina-com-videos-sobre-sintese-de-image` | 16 - Síntese de Imagens Real | modelos-de-reflexao-ambiente-difusa-especular ~ | **modelos-de-iluminacao-luz-pontual-direcional-spot** | modelos-de-reflexao-ambiente-difusa-especular ; metodos-de-sombreamento-flat-gouraud-phong | titulo |  |

### Fora da regua (scorable=no)

| ok? | entry | unidade computada | motivo |
|---|---|---|---|
| | `morfologiamatematicapptx` | unidade-01-introducao-ao-processam | UNIDADE ERRADA: computada u01; morfologia matematica e processamento de imagens (u03); taxonomia u03 sem subtopico proprio (filtros ou segme |
| | `csg` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; CSG = u07/geometria-solida-construtiva-csg |
| | `modelagem3d` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; modelagem de solidos = u07/formas-de-representacao |
| | `basico3d-cpp` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; card 14 'Exercicios sobre Modelagem' + resumo (extrusao, Bezier) = u07/varredura ou tecnicas-de-modelagem-3d |
| | `basico3d-py-zip` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; modelagem por extrusao = u07/varredura |
| | `exerciciodemodelagem` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; CriaObjetoPorExtrusao = u07/varredura |
| | `maptextures` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; texturas = u08/mapeamento-de-textura |
| | `texturas-v3` | unidade-01-introducao-ao-processam | UNIDADE ERRADA: computada u01 (card 2 OpenGL); texturas + iluminacao = u08/mapeamento-de-textura |
| | `exemplodemanipulacaodeimagens` | unidade-02-fundamentos-matematicos | CONFLITO: label do Moodle 'Classe Vetor' (u02) x conteudo do .cpp = processamento de imagens (u03/filtros); computada u02 — RULING pendente |
| | `animacao-v2` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; animacao com translacao/rotacao = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d |
| | `exercicios-teoricos-sobre-processo-de-vi` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; viewport x window = u05/mapeamento-window-e-viewport |
| | `instanciamento` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; translacao/escala/rotacao = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d |
| | `mapeamento` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; janela de selecao/exibicao = u05/mapeamento-window-e-viewport |
| | `pagina-com-videos-sobre-instanciamento` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; instanciamento = u05/transformacoes-geometricas (conteudo capturado = listagem de codigo) |
| | `transformacoesgeometricas` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; transformacoes 2D hierarquicas = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d |
| | `transformacoesgl` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; transformacoes em OpenGL = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d |
| | `exercicios-teoricos-sobre-processo-de-vi` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; viewport x window = u05/mapeamento-window-e-viewport (duplicata html) |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-04-processo-de-visualizaca | prova resolvida: cobre varias unidades |
| | `listadeexercicios2026-1` | unidade-08-sintese-de-imagens-real | lista para P2: iluminacao + projecao + modelagem (u06/u07/u08) |
| | `cronograma2026-2` | unidade-01-introducao-ao-processam | meta (cronograma) |
| | `planodeensino-4645z-04-fundamentos-de-co` | unidade-01-introducao-ao-processam | meta (plano de ensino) |
| | `videoscg-v2` | unidade-01-introducao-ao-processam | playlist da disciplina inteira |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-04-processo-de-visualizaca | prova resolvida (duplicata html) |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-08-sintese-de-imagens-real | prova resolvida: cobre varias unidades |
| | `pagina-com-videos-sobre-mapeamento-9f410` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; mapeamento = u05/mapeamento-window-e-viewport |
| | `video-sobre-mapeamento-em-opengl-1dad3c` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; mapeamento = u05/mapeamento-window-e-viewport |
| | `aula-gravada-975b85` | unidade-01-introducao-ao-processam | UNIDADE ERRADA: computada u01; aula sobre Morfologia Matematica = u03 |
| | `pagina-com-videos-sobre-morfologia-matem` | unidade-01-introducao-ao-processam | UNIDADE ERRADA: computada u01; morfologia = u03 |
| | `paginas-com-videos-sobre-modelagem-geome` | unidade-06-processo-de-visualizaca | UNIDADE ERRADA: computada u06; modelagem geometrica = u07 |
| | `pagina-com-videos-sobre-mapeamento-de-te` | unidade-04-processo-de-visualizaca | UNIDADE ERRADA: computada u04; texturas = u08/mapeamento-de-textura |

## MF — 66 materiais, 58 pontuaveis, 8 fora

### Pontuaveis

| ok? | entry | card | pred (produto) | GOLD | extras | fonte | nota |
|---|---|---|---|---|---|---|---|
| | `archive-of-formal-proofs-355fb8` |  | abordagens-para-verificacao-formal X | **provadores-de-teoremas** |  | conteudo | AFP = provas em Isabelle |
| | `exerciciosformalizacaoalgoritmosrecursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | arvores binarias: definicao indutiva + equacoes recursivas |
| | `formalizacaoalgoritmos-recursao2` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | listas: definicao indutiva + equacoes recursivas |
| | `exerciciosconjuntosindutivos` | Especificações Indutivas e R | especificacao-de-conjuntos-indutivos = | **especificacao-de-conjuntos-indutivos** |  | conteudo |  |
| | `conjuntosindutivos` | Especificações Indutivas e R | especificacao-de-conjuntos-indutivos = | **especificacao-de-conjuntos-indutivos** |  | conteudo |  |
| | `logicapredicados-semantica` | Revisão - Lógica e Especific | fundamentos-de-logica-de-primeira-ordem = | **fundamentos-de-logica-de-primeira-ordem** |  | conteudo |  |
| | `logicapredicados-sintaxe` | Revisão - Lógica e Especific | fundamentos-de-logica-de-primeira-ordem = | **fundamentos-de-logica-de-primeira-ordem** |  | conteudo |  |
| | `logicaproposicional-sintaxe` | Revisão - Lógica e Especific | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** | fundamentos-de-logica-de-primeira-ordem | conteudo | logica proposicional: taxonomia u01 sem subtopico proprio |
| | `revisao` | Revisão - Lógica e Especific | sistemas-formais = | **sistemas-formais** |  | conteudo | revisao de pre-requisitos (conjuntos, relacoes, funcoes, linguagens formais); alternativa vazio (revisao sem a |
| | `introducao` | Introdução a Métodos Formais | exemplos-de-aplicacoes ~ | **abordagens-para-verificacao-formal** | exemplos-de-aplicacoes | conteudo | V&V, tecnicas, 'o que e um metodo formal'; Ariane/Therac/Pentium como exemplos |
| | `provasindutivas-especificacoesrecursivas` | Provas por Indução | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | provas por inducao de especificacoes recursivas: taxonomia u01 sem subtopico 'inducao' |
| | `provasindutivas-especificacoesrecursivas` | Provas por Indução | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | inducao estrutural sobre arvores |
| | `provasindutivas-especificacoesrecursivas` | Provas por Indução | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | inducao estrutural sobre listas |
| | `exercicioscorrecaoinducaomatematica` | Provas por Indução | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | provas por inducao de especificacoes equacionais recursivas |
| | `exerciciosespecificacao-respostas` | Revisão - Lógica e Especific | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** |  | conteudo | especificacao formal (pre/pos de busca em array) escrita em logica; card 'Revisao - Logica e Especificacao' |
| | `exerciciosespecificacao` | Revisão - Lógica e Especific | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** |  | conteudo | idem |
| | `exerciciosformalizacaoalgoritmosrecursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | listas |
| | `exerciciosisabelle2` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | provas em Isabelle |
| | `logicaproposicional-semantica` | Revisão - Lógica e Especific | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** | fundamentos-de-logica-de-primeira-ordem | conteudo | logica proposicional: sem subtopico proprio |
| | `exerciciosformalizacaoalgoritmosrecursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | gabarito (scanned) |
| | `formalizacaoalgoritmos-recursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | equacoes recursivas, tipos de recursao, maquina de estados |
| | `formalizacaoalgoritmos-recursao3` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | arvores |
| | `exerciciosisabelle` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | provas em Isabelle |
| | `exerciciosformalizacaoalgoritmosrecursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | parte 1 |
| | `arvores` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: datatype arvore + prova por inducao em Isabelle |
| | `exemplos` | Provas por Indução | exemplos-de-aplicacoes X | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas ; especificacao-de-conjuntos-indutivos | conteudo | .thy: tipos indutivos, predicados, funcoes recursivas em Isabelle |
| | `intro` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-conjuntos-indutivos ; especificacao-de-funcoes-recursivas | conteudo | .thy: naturais, recursao primitiva, regras de inducao |
| | `listas` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: cat e associatividade |
| | `provas` | Provas por Indução | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: add, propriedades indutivas, Isar |
| | `correcaoterminacao` | Verificação de Programas | correcao-parcial-e-total = | **correcao-parcial-e-total** | invariante-e-variante-de-laco | conteudo | correcao parcial/total, ordens bem-fundamentadas, terminacao |
| | `exercicioscorrecaoterminacao` | Verificação de Programas | correcao-parcial-e-total = | **correcao-parcial-e-total** | invariante-e-variante-de-laco ; softwares-de-suporte-a-verificacao-formal-de-programas | conteudo | terminacao em Dafny |
| | `exerciciosformalizacaoalgoritmosinvarian` | Verificação de Programas | invariante-e-variante-de-laco = | **invariante-e-variante-de-laco** |  | conteudo |  |
| | `formalizacaoalgoritmos-invarianteslaco` | Verificação de Programas | invariante-e-variante-de-laco = | **invariante-e-variante-de-laco** |  | conteudo |  |
| | `logicadehoare` | Verificação de Programas | logica-de-hoare = | **logica-de-hoare** | pre-e-pos-condicoes | conteudo | triplas de Hoare |
| | `logicadehoare2` | Verificação de Programas | logica-de-hoare = | **logica-de-hoare** | invariante-e-variante-de-laco ; pre-e-pos-condicoes | conteudo | lacos enquanto, arrays |
| | `exerciciosdafny1` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; pre-e-pos-condicoes | conteudo | CONVENCAO proposta: listas 'Programacao e Verificacao com Dafny (X)' = softwares-de-suporte (Dafny), extra ver |
| | `exerciciosdafny2` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (arrays); convencao Dafny |
| | `exerciciosdafny3` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (sequences); convencao Dafny |
| | `exerciciosdafny4` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (sets, multisets); convencao Dafny |
| | `exerciciosdafny5` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; pre-e-pos-condicoes | conteudo | Dafny (classes, frames); convencao Dafny |
| | `verificacaomodelos` | Especificação e Verificação  | especificacao-de-propriedades-para-sistemas-sequenciais-e-concorrentes ~ | **verificacao-de-modelos-model-checking** | fundamentos-de-logicas-temporais ; especificacao-de-propriedades-para-sistemas-sequenciais-e-concorrentes ; modelos-de-kripke | conteudo | slides gerais da unidade |
| | `exercicioslogicatemporal` | Especificação e Verificação  | verificacao-de-modelos-model-checking ~ | **fundamentos-de-logicas-temporais** | verificacao-de-modelos-model-checking ; logica-temporal-linear ; logica-temporal-ramificada | conteudo |  |
| | `exerciciosnusmv` | Especificação e Verificação  | softwares-de-suporte-a-verificacao-formal-de-modelos = | **softwares-de-suporte-a-verificacao-formal-de-modelos** | verificacao-de-modelos-model-checking | conteudo | NuSMV/NuXMV/Fasten |
| | `classes-parte1` | Verificação de Programas | verificacao-de-programas ~ | **pre-e-pos-condicoes** | softwares-de-suporte-a-verificacao-formal-de-programas ; verificacao-de-programas | conteudo | classe Contador com contratos em Dafny |
| | `colecoes-arrays` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | RESUMO DE CODIGO ERRADO (repete 'datatype Cor'); rotulado pelo label 'Exemplos (Arrays)' + convencao Dafny |
| | `colecoes-conjuntos` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | resumo repetido; label 'Exemplos (Conjuntos e sequencias)' |
| | `colecoes-sequences` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | resumo repetido; label 'Exemplos (Sequencias)' |
| | `exercicios-conjuntos` | Verificação de Programas | invariante-e-variante-de-laco ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; invariante-e-variante-de-laco | conteudo | respostas: metodos verificados sobre arrays/sequencias (maximo, permutacao, busca) |
| | `hoare` | Verificação de Programas | logica-de-hoare = | **logica-de-hoare** | softwares-de-suporte-a-verificacao-formal-de-programas ; verificacao-de-programas | label | label 'Exemplos (Logica de Floyd-Hoare)'; resumo amplo cita Hoare |
| | `introducao-zip` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | introducao a Dafny: funcoes e predicados, transparencia |
| | `invariantes` | Verificação de Programas | - ~ | **invariante-e-variante-de-laco** |  | label | RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (invariantes de laco)' |
| | `terminacao` | Verificação de Programas | - X | **correcao-parcial-e-total** | invariante-e-variante-de-laco | label | RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (Terminacao)' |
| | `tiposindutivos` | Verificação de Programas | verificacao-de-programas X | **softwares-de-suporte-a-verificacao-formal-de-programas** |  | label | tipos indutivos em Dafny (conteudo de u01 na ferramenta de u02); por card u02 = softwares-de-suporte |
| | `exemplos-zip` | Especificação e Verificação  | - X | **softwares-de-suporte-a-verificacao-formal-de-modelos** | verificacao-de-modelos-model-checking | label | RESUMO DE CODIGO ERRADO (diz Dafny); label 'Exemplos NuSMV', card 'Especificacao e Verificacao de Modelos' |
| | `exerciciosformalizacaoalgoritmosrecursao` | Especificações Indutivas e R | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | equacoes recursivas III (arvores) |
| | `classes-parte2` | Verificação de Programas | correcao-parcial-e-total X | **verificacao-de-programas** | invariante-e-variante-de-laco ; pre-e-pos-condicoes ; softwares-de-suporte-a-verificacao-formal-de-programas | conteudo | BST verificada com ghost e invariantes de classe |
| | `exercicios-arrays` | Verificação de Programas | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; invariante-e-variante-de-laco ; pre-e-pos-condicoes | conteudo | respostas: algoritmos em arrays verificados em Dafny |
| | `logicadehoare-exercicios-respostas` | Verificação de Programas | logica-de-hoare = | **logica-de-hoare** |  | conteudo |  |

### Fora da regua (scorable=no)

| ok? | entry | unidade computada | motivo |
|---|---|---|---|
| | `eth2` | unidade-01-metodos-formais | UNIDADE: gold u02 (ruling 31/08), computada u01; subtopico seria softwares-de-suporte (Dafny) |
| | `aws-encryption-sdk` | unidade-01-metodos-formais | UNIDADE: gold u02 (ruling 31/08), computada u01; subtopico seria softwares-de-suporte (Dafny) |
| | `revisao-p1` | unidade-01-metodos-formais | lista de revisao para P1: cobre a unidade inteira |
| | `t1-2026-1` | unidade-02-verificacao-de-programa | UNIDADE ERRADA: computada u02, gold u01 (material_gt); subtopico seria especificacao-de-funcoes-recursivas |
| | `t1-2026-1-thy` | unidade-02-verificacao-de-programa | UNIDADE ERRADA: computada u02, gold u01; subtopico seria provadores-de-teoremas |
| | `revisao-p1-gabarito` | unidade-01-metodos-formais | gabarito da revisao para P1 |
| | `plano` | unidade-01-metodos-formais | meta (plano de ensino) |
| | `t2-2026-1` | unidade-03-verificacao-de-modelos | UNIDADE ERRADA: computada u03, gold u02 (material_gt: cita dafny e invariante); subtopico seria invariante-e-variante-de-laco |
