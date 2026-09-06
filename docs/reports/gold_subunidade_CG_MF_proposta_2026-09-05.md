# Gold de subunidade CG e MF — PROPOSTA v2 (proposto-claude 2026-09-05, apos curadoria de unidade do CG; aguarda aprovacao)

Regras: subtopico dentro da UNIDADE COMPUTADA (CG com pinos nos blocos 06/08/15); unidade errada -> `scorable=no` com a causa; meta -> `scorable=no`;
ferramenta sem subtopico (OpenGL) -> vazio; bloco-06 = u04 pelo oraculo (transformacoes/instanciamento sem subtopico em u04 -> vazio; mapeamento ->
sistema-de-coordenadas-cartesianas); codigo pelo conteudo e, com resumo errado (zips do MF), pelo label. Marque `ok?`: sim / nao / outro.

## CG — 93 materiais, 82 pontuaveis (49 o produto ja acerta), 11 fora

### Pontuaveis

| ok? | entry | unidade | pred (produto) | GOLD | extras | fonte | nota |
|---|---|---|---|---|---|---|---|
| | `intro` | 01-introduca | - X | **conceitos** | areas-relacionadas | conteudo | pagina 'Origens' mas o texto e a classificacao de CG passiva/interativa (Rogers e Adams) = conceitos |
| | `origensdacomputacaografica` | 01-introduca | origens = | **origens** |  | conteudo | Whirlwind, SAGE, Sketchpad, mouse |
| | `segmentacaopptx` | 03-processam | segmentacao = | **segmentacao** |  | conteudo |  |
| | `segmentacaodetexturas` | 03-processam | segmentacao = | **segmentacao** |  | conteudo | co-ocorrencia de niveis de cinza para segmentar texturas |
| | `morfologiamatematicapptx` | 03-processam | cores-e-tipos-de-imagens X | **segmentacao** | filtros | conteudo | u03 por pino (oraculo: sessao 12 entre processamento de imagens e exercicios); plano sem topico de morfologia  |
| | `csg` | 07-represent | geometria-solida-construtiva-csg = | **geometria-solida-construtiva-csg** | tecnicas-de-modelagem-3d | conteudo | u07 por pino; CSG com poligonos |
| | `modelagem3d` | 07-represent | representacao-aramada ~ | **formas-de-representacao** | tecnicas-de-modelagem-3d ; representacao-aramada ; superficies-limitantes | conteudo | u07 por pino; pagina 'Modelagem de Solidos': formas de armazenamento de solidos |
| | `atividade` | 06-processo- | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes | conteudo | tarefas: coordenadas do observador e do alvo, mover o observador |
| | `basico3d-py` | 06-processo- | perspectiva X | **conceito-de-camera-sintetica** | pipeline-de-visualizacao-3d ; projecoes | conteudo | resumo: cena 3D, gluLookAt, iluminacao, ModelView |
| | `opengl3d` | 06-processo- | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | conteudo | 'funcoes de projecao e manipulacao da camera em OpenGL' |
| | `opengl3dcpp-vdi` | 06-processo- | conceito-de-camera-sintetica = | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | card | bundle misto (2D/3D/Bezier/imagens); rotulado pelo LABEL 'Projeto VDI de OpenGL 3D' + card 13 — RULING pendent |
| | `opengl3dcpp` | 06-processo- | perspectiva X | **conceito-de-camera-sintetica** | projecoes ; pipeline-de-visualizacao-3d | card | bundle misto; LABEL 'Projeto de OpenGL 3D em C++' + card 13 — RULING pendente |
| | `vis3d` | 06-processo- | paralela ~ | **projecoes** | paralela ; perspectiva ; conceito-de-camera-sintetica ; a-matematica-das-projecoes-planares | conteudo | PROJECOES, paralela ortografica, perspectiva, observador, sistema da camera |
| | `basico3d-cpp` | 07-represent | representacao-de-curvas-parametricas X | **tecnicas-de-modelagem-3d** | varredura ; bezier-e-algoritmo-de-casteljau | conteudo | u07 por pino; card 14 'Exercicios sobre Modelagem'; resumo: extrusao de poligonos, Bezier |
| | `basico3d-py-zip` | 07-represent | tecnicas-de-modelagem-3d = | **tecnicas-de-modelagem-3d** | varredura | conteudo | u07 por pino; modelagem por extrusao |
| | `exerciciodemodelagem` | 07-represent | tecnicas-de-modelagem-3d ~ | **varredura** | tecnicas-de-modelagem-3d | conteudo | u07 por pino; CriaObjetoPorExtrusao (extrusao = varredura) |
| | `elemoculto` | 06-processo- | algoritmo-z-buffer ~ | **algoritmos-de-remocao-de-elementos-ocultos** | eliminacao-de-faces-traseiras ; algoritmo-do-pintor ; algoritmo-z-buffer ; arvores-bsp | conteudo | slides-roteiro da remocao de elementos ocultos (faces traseiras, z-buffer, pintor) |
| | `exemplozbuffer` | 06-processo- | algoritmo-z-buffer = | **algoritmo-z-buffer** |  | conteudo |  |
| | `iluminacao` | 08-sintese-d | modelos-de-reflexao-ambiente-difusa-especular ~ | **modelos-de-iluminacao-luz-pontual-direcional-spot** | modelos-de-reflexao-ambiente-difusa-especular ; metodos-de-sombreamento-flat-gouraud-phong | conteudo | pagina: modelos de iluminacao + modelos de tonalizacao |
| | `programabasico3d` | 08-sintese-d | modelos-de-reflexao-ambiente-difusa-especular = | **modelos-de-reflexao-ambiente-difusa-especular** | modelos-de-iluminacao-luz-pontual-direcional-spot ; projecoes | conteudo | codigo usado em aula (card 16): configura ambiente/difusa/especular |
| | `exercicios` | 01-introduca | conceitos X | **(vazio)** |  | conteudo | exercicios de introducao a OpenGL: ferramenta, sem subtopico na taxonomia; resposta honesta = vazio (pred 'con |
| | `opengl-cpp` | 01-introduca | conceitos X | **(vazio)** |  | conteudo | bundle de projetos OpenGL (ferramenta): sem subtopico; vazio |
| | `opengl-py` | 01-introduca | conceitos X | **(vazio)** |  | conteudo | bundle de projetos OpenGL (ferramenta): sem subtopico; vazio |
| | `openglbasico` | 01-introduca | conceitos X | **(vazio)** |  | conteudo | tutorial de instalacao/uso de OpenGL: ferramenta; vazio |
| | `exercicio-com-animacao` | 02-fundament | - X | **operacoes-com-vetores** | entidades-geometricas | conteudo | triangulo atravessa a tela em tempo fixo = deslocamento por vetor |
| | `exercicio-com-poligonos` | 02-fundament | algoritmos-de-poligonos = | **algoritmos-de-poligonos** |  | conteudo | ponto dentro/fora do poligono |
| | `exercicio-de-animacao-foguete` | 02-fundament | algoritmos-de-poligonos ~ | **operacoes-com-vetores** | algoritmos-de-poligonos | conteudo | foguete de poligonos deslocado por PosFoguete (vetor) |
| | `fundamentosmatematicos` | 02-fundament | entidades-geometricas = | **entidades-geometricas** | operacoes-com-vetores | conteudo | pontos, vetores, retas; operacoes |
| | `matematica` | 02-fundament | entidades-geometricas ~ | **operacoes-com-vetores** | entidades-geometricas | conteudo | classe Vetor 2D: translacao, escala, vetor resultante; label 'Produto Escalar' |
| | `colisao` | 02-fundament | algoritmos-de-deteccao-e-calculo-de-interseccao = | **algoritmos-de-deteccao-e-calculo-de-interseccao** |  | conteudo | AABB/OOBB, envelopes |
| | `geomcomp` | 02-fundament | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | conteudo |  |
| | `animacao-v2` | 04-processo- | desenho-de-linhas X | **(vazio)** |  | conteudo | u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05 |
| | `exercicios-teoricos-sobre-processo-de-vi` | 04-processo- | desenho-de-linhas X | **sistema-de-coordenadas-cartesianas** |  | conteudo | u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window |
| | `instanciamento` | 04-processo- | 2d-3d-mao-direita-e-mao-esquerda X | **(vazio)** |  | conteudo | u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05 |
| | `mapeamento` | 04-processo- | sistema-de-coordenadas-cartesianas = | **sistema-de-coordenadas-cartesianas** |  | conteudo | u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window |
| | `pagina-com-videos-sobre-instanciamento` | 04-processo- | desenho-de-linhas X | **(vazio)** |  | conteudo | u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05 |
| | `recorte` | 04-processo- | recorte = | **recorte** |  | conteudo | Cohen-Sutherland |
| | `transformacoesgeometricas` | 04-processo- | - = | **(vazio)** |  | conteudo | u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05 |
| | `transformacoesgl` | 04-processo- | sistema-de-coordenadas-cartesianas X | **(vazio)** |  | conteudo | u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05 |
| | `vis2d` | 04-processo- | recorte ~ | **sistema-de-coordenadas-cartesianas** | recorte | conteudo | introducao ao processo 2D (instanciamento, recorte, mapeamento, sistemas de referencia); alternativa u05/pipel |
| | `bezier-animacao` | 07-represent | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-cpp` | 07-represent | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-py` | 07-represent | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo |  |
| | `bezier-python` | 07-represent | - X | **bezier-e-algoritmo-de-casteljau** | representacao-de-curvas-parametricas | conteudo | quadraticas e cubicas; animacao |
| | `curvas` | 07-represent | hermite ~ | **representacao-de-curvas-parametricas** | bezier-e-algoritmo-de-casteljau ; hermite ; catmull-rom ; b-spline | conteudo | pagina geral de curvas parametricas |
| | `curvasparametricas` | 07-represent | - X | **representacao-de-curvas-parametricas** | bezier-e-algoritmo-de-casteljau ; hermite ; catmull-rom ; b-spline | conteudo | slides: forma parametrica x nao parametrica |
| | `exercicios-sobre-curvas` | 07-represent | hermite X | **catmull-rom** | representacao-de-curvas-parametricas ; bezier-e-algoritmo-de-casteljau | conteudo | 1a questao: Catmull-Rom por 4 pontos |
| | `floodfill` | 03-processam | segmentacao = | **segmentacao** |  | conteudo | flood fill = crescimento de regiao; alternativa u04/preenchimento-de-poligonos (card 8 Manipulacao de Imagens) |
| | `img` | 03-processam | filtros ~ | **cores-e-tipos-de-imagens** | filtros ; algoritmos-de-quantizacao-e-amostragem | conteudo | 1. Tipos de imagens (true-color...) |
| | `remocaoderuido` | 03-processam | filtros = | **filtros** |  | conteudo |  |
| | `exercicios-de-processamento-de-imagens` | 03-processam | cores-e-tipos-de-imagens ~ | **algoritmos-de-quantizacao-e-amostragem** | cores-e-tipos-de-imagens ; filtros ; segmentacao | conteudo | 1a questao: copia de imagem de 64 tons (quantizacao); lista cobre varios |
| | `introducaoprocimg` | 03-processam | filtros = | **filtros** | introducao-e-exemplos-de-aplicacoes ; cores-e-tipos-de-imagens | conteudo | histogramas, equalizacao, convolucao, Sobel |
| | `exercicios-de-geometria-computacional` | 02-fundament | entidades-geometricas X | **algoritmos-de-geometria-computacional** |  | conteudo | matriz de dominancia |
| | `exercicios-sobre-curvas-html` | 07-represent | hermite X | **catmull-rom** | representacao-de-curvas-parametricas ; bezier-e-algoritmo-de-casteljau | conteudo | duplicata html de exercicios-sobre-curvas |
| | `exercicios-teoricos-sobre-processo-de-vi` | 04-processo- | desenho-de-linhas X | **sistema-de-coordenadas-cartesianas** |  | conteudo | u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window |
| | `exerciciosfundamentosmatematicos` | 02-fundament | algoritmos-de-poligonos = | **algoritmos-de-poligonos** | operacoes-com-vetores | conteudo | 3 de 4 questoes sobre poligonos (concavidade, inclusao de ponto) |
| | `domina` | 02-fundament | entidades-geometricas X | **algoritmos-de-geometria-computacional** |  | conteudo | contagem geometrica / matriz de dominancia |
| | `planesweep` | 02-fundament | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | conteudo |  |
| | `slab` | 02-fundament | algoritmos-de-poligonos ~ | **algoritmos-de-geometria-computacional** | algoritmos-de-poligonos | conteudo | pesquisa geometrica: em qual poligono esta o ponto (slab) |
| | `exercicioduascores` | 03-processam | - X | **algoritmos-de-quantizacao-e-amostragem** | cores-e-tipos-de-imagens | conteudo | padroes de halftone (2 cores) = quantizacao |
| | `video-sobre-origens-da-computacao-grafic` | 01-introduca | origens = | **origens** |  | titulo |  |
| | `video-com-instrucoes-para-usar-opengl-na` | 01-introduca | conceitos X | **(vazio)** |  | titulo | ferramenta (OpenGL na VDI): vazio |
| | `pagina-com-videos-sobre-fundamentos-mate` | 02-fundament | - X | **entidades-geometricas** | operacoes-com-vetores | titulo | conteudo capturado = pagina de login do Moodle; rotulo pelo titulo |
| | `videos-sobre-algoritmos-de-detecao-de-co` | 02-fundament | - ~ | **algoritmos-de-deteccao-e-calculo-de-interseccao** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-geometria-comput` | 02-fundament | algoritmos-de-geometria-computacional = | **algoritmos-de-geometria-computacional** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-recorte-e257d3` | 04-processo- | recorte = | **recorte** |  | titulo | conteudo capturado = login do Moodle |
| | `video-sobre-o-algoritmo-de-recorte-por-s` | 04-processo- | recorte = | **recorte** |  | titulo |  |
| | `pagina-com-videos-sobre-mapeamento-9f410` | 04-processo- | sistema-de-coordenadas-cartesianas = | **sistema-de-coordenadas-cartesianas** |  | conteudo | u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window |
| | `video-sobre-mapeamento-em-opengl-1dad3c` | 04-processo- | 2d-3d-mao-direita-e-mao-esquerda X | **sistema-de-coordenadas-cartesianas** |  | conteudo | u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window |
| | `pagina-com-videos-sobre-curvas-parametri` | 07-represent | representacao-de-curvas-parametricas = | **representacao-de-curvas-parametricas** |  | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-manipulacao-de-i` | 03-processam | cores-e-tipos-de-imagens = | **cores-e-tipos-de-imagens** | filtros | titulo | mesmo assunto da pagina 'img' (tipos de imagens) |
| | `pagina-com-videos-sobre-introducao-ao-pr` | 03-processam | - X | **introducao-e-exemplos-de-aplicacoes** | filtros | titulo | conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-segmentacao-de-i` | 03-processam | segmentacao = | **segmentacao** |  | titulo |  |
| | `pagina-com-videos-sobre-segmentacao-por-` | 03-processam | segmentacao = | **segmentacao** |  | titulo |  |
| | `aula-gravada-975b85` | 03-processam | - X | **segmentacao** | filtros | titulo | u03 por pino; aula gravada de morfologia |
| | `pagina-com-videos-sobre-morfologia-matem` | 03-processam | - X | **segmentacao** | filtros | titulo | u03 por pino; conteudo capturado = login do Moodle |
| | `video-sobre-prechimento-de-areas-duracao` | 03-processam | segmentacao = | **segmentacao** |  | titulo | preenchimento de area (flood fill), como floodfill; alternativa u04/preenchimento-de-poligonos |
| | `video-sobre-prechimento-de-areas-duracao` | 03-processam | segmentacao = | **segmentacao** |  | titulo | idem |
| | `paginas-com-videos-sobre-modelagem-geome` | 07-represent | tecnicas-de-modelagem-3d = | **tecnicas-de-modelagem-3d** | formas-de-representacao | titulo | u07 por pino; conteudo capturado = login do Moodle |
| | `pagina-com-videos-sobre-visualizacao-3d-` | 06-processo- | pipeline-de-visualizacao-3d = | **pipeline-de-visualizacao-3d** | projecoes ; conceito-de-camera-sintetica | titulo |  |
| | `pagina-com-videos-sobre-remocao-de-eleme` | 06-processo- | algoritmos-de-remocao-de-elementos-ocultos = | **algoritmos-de-remocao-de-elementos-ocultos** |  | titulo |  |
| | `pagina-com-videos-sobre-sintese-de-image` | 08-sintese-d | modelos-de-reflexao-ambiente-difusa-especular ~ | **modelos-de-iluminacao-luz-pontual-direcional-spot** | modelos-de-reflexao-ambiente-difusa-especular ; metodos-de-sombreamento-flat-gouraud-phong | titulo |  |

### Fora da regua (scorable=no)

| ok? | entry | unidade computada | motivo |
|---|---|---|---|
| | `maptextures` | unidade-04-processo-de-visualizaca | BLOCO ERRADO: bloco-06 por colisao do token 'mapeamento' com a sessao 'processo de visualizacao 2d mapeamento' (flagado; voter decide); unid |
| | `texturas-v3` | unidade-01-introducao-ao-processam | UNIDADE ERRADA: computada u01 (card 2 OpenGL, sem bloco); conteudo texturas+iluminacao = u08; GLOSSARY.md do CG para em 7.1.2 -> u08 sem ter |
| | `exemplodemanipulacaodeimagens` | unidade-02-fundamentos-matematicos | CONFLITO: label do Moodle 'Classe Vetor' (u02) x conteudo do .cpp = processamento de imagens (u03/filtros); computada u02 — RULING pendente |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-04-processo-de-visualizaca | prova resolvida: cobre varias unidades |
| | `listadeexercicios2026-1` | unidade-08-sintese-de-imagens-real | lista para P2: iluminacao + projecao + modelagem (u06/u07/u08) |
| | `cronograma2026-2` | unidade-01-introducao-ao-processam | meta (cronograma) |
| | `planodeensino-4645z-04-fundamentos-de-co` | unidade-01-introducao-ao-processam | meta (plano de ensino) |
| | `videoscg-v2` | unidade-01-introducao-ao-processam | playlist da disciplina inteira |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-04-processo-de-visualizaca | prova resolvida (duplicata html) |
| | `resolucao-de-prova-de-computacao-grafica` | unidade-08-sintese-de-imagens-real | prova resolvida: cobre varias unidades |
| | `pagina-com-videos-sobre-mapeamento-de-te` | unidade-04-processo-de-visualizaca | BLOCO ERRADO (idem maptextures): verdade u08/mapeamento-de-textura |

## MF — 66 materiais, 58 pontuaveis (51 o produto ja acerta), 8 fora

### Pontuaveis

| ok? | entry | unidade | pred (produto) | GOLD | extras | fonte | nota |
|---|---|---|---|---|---|---|---|
| | `archive-of-formal-proofs-355fb8` | 01-metodos-f | abordagens-para-verificacao-formal X | **provadores-de-teoremas** |  | conteudo | AFP = provas em Isabelle |
| | `exerciciosformalizacaoalgoritmosrecursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | arvores binarias: definicao indutiva + equacoes recursivas |
| | `formalizacaoalgoritmos-recursao2` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | listas: definicao indutiva + equacoes recursivas |
| | `exerciciosconjuntosindutivos` | 01-metodos-f | especificacao-de-conjuntos-indutivos = | **especificacao-de-conjuntos-indutivos** |  | conteudo |  |
| | `conjuntosindutivos` | 01-metodos-f | especificacao-de-conjuntos-indutivos = | **especificacao-de-conjuntos-indutivos** |  | conteudo |  |
| | `logicapredicados-semantica` | 01-metodos-f | fundamentos-de-logica-de-primeira-ordem = | **fundamentos-de-logica-de-primeira-ordem** |  | conteudo |  |
| | `logicapredicados-sintaxe` | 01-metodos-f | fundamentos-de-logica-de-primeira-ordem = | **fundamentos-de-logica-de-primeira-ordem** |  | conteudo |  |
| | `logicaproposicional-sintaxe` | 01-metodos-f | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** | fundamentos-de-logica-de-primeira-ordem | conteudo | logica proposicional: taxonomia u01 sem subtopico proprio |
| | `revisao` | 01-metodos-f | sistemas-formais = | **sistemas-formais** |  | conteudo | revisao de pre-requisitos (conjuntos, relacoes, funcoes, linguagens formais); alternativa vazio (revisao sem a |
| | `introducao` | 01-metodos-f | exemplos-de-aplicacoes ~ | **abordagens-para-verificacao-formal** | exemplos-de-aplicacoes | conteudo | V&V, tecnicas, 'o que e um metodo formal'; Ariane/Therac/Pentium como exemplos |
| | `provasindutivas-especificacoesrecursivas` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | provas por inducao de especificacoes recursivas: taxonomia u01 sem subtopico 'inducao' |
| | `provasindutivas-especificacoesrecursivas` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | inducao estrutural sobre arvores |
| | `provasindutivas-especificacoesrecursivas` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | inducao estrutural sobre listas |
| | `exercicioscorrecaoinducaomatematica` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | abordagens-para-verificacao-formal | conteudo | provas por inducao de especificacoes equacionais recursivas |
| | `exerciciosespecificacao-respostas` | 01-metodos-f | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** |  | conteudo | especificacao formal (pre/pos de busca em array) escrita em logica; card 'Revisao - Logica e Especificacao' |
| | `exerciciosespecificacao` | 01-metodos-f | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** |  | conteudo | idem |
| | `exerciciosformalizacaoalgoritmosrecursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | listas |
| | `exerciciosisabelle2` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | provas em Isabelle |
| | `logicaproposicional-semantica` | 01-metodos-f | linguagens-de-especificacao-e-logicas = | **linguagens-de-especificacao-e-logicas** | fundamentos-de-logica-de-primeira-ordem | conteudo | logica proposicional: sem subtopico proprio |
| | `exerciciosformalizacaoalgoritmosrecursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | gabarito (scanned) |
| | `formalizacaoalgoritmos-recursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | equacoes recursivas, tipos de recursao, maquina de estados |
| | `formalizacaoalgoritmos-recursao3` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** | especificacao-de-conjuntos-indutivos | conteudo | arvores |
| | `exerciciosisabelle` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | provas em Isabelle |
| | `exerciciosformalizacaoalgoritmosrecursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | parte 1 |
| | `arvores` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: datatype arvore + prova por inducao em Isabelle |
| | `exemplos` | 01-metodos-f | exemplos-de-aplicacoes X | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas ; especificacao-de-conjuntos-indutivos | conteudo | .thy: tipos indutivos, predicados, funcoes recursivas em Isabelle |
| | `intro` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-conjuntos-indutivos ; especificacao-de-funcoes-recursivas | conteudo | .thy: naturais, recursao primitiva, regras de inducao |
| | `listas` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: cat e associatividade |
| | `provas` | 01-metodos-f | provadores-de-teoremas = | **provadores-de-teoremas** | especificacao-de-funcoes-recursivas | conteudo | .thy: add, propriedades indutivas, Isar |
| | `correcaoterminacao` | 02-verificac | correcao-parcial-e-total = | **correcao-parcial-e-total** | invariante-e-variante-de-laco | conteudo | correcao parcial/total, ordens bem-fundamentadas, terminacao |
| | `exercicioscorrecaoterminacao` | 02-verificac | correcao-parcial-e-total = | **correcao-parcial-e-total** | invariante-e-variante-de-laco ; softwares-de-suporte-a-verificacao-formal-de-programas | conteudo | terminacao em Dafny |
| | `exerciciosformalizacaoalgoritmosinvarian` | 02-verificac | invariante-e-variante-de-laco = | **invariante-e-variante-de-laco** |  | conteudo |  |
| | `formalizacaoalgoritmos-invarianteslaco` | 02-verificac | invariante-e-variante-de-laco = | **invariante-e-variante-de-laco** |  | conteudo |  |
| | `logicadehoare` | 02-verificac | logica-de-hoare = | **logica-de-hoare** | pre-e-pos-condicoes | conteudo | triplas de Hoare |
| | `logicadehoare2` | 02-verificac | logica-de-hoare = | **logica-de-hoare** | invariante-e-variante-de-laco ; pre-e-pos-condicoes | conteudo | lacos enquanto, arrays |
| | `exerciciosdafny1` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; pre-e-pos-condicoes | conteudo | CONVENCAO proposta: listas 'Programacao e Verificacao com Dafny (X)' = softwares-de-suporte (Dafny), extra ver |
| | `exerciciosdafny2` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (arrays); convencao Dafny |
| | `exerciciosdafny3` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (sequences); convencao Dafny |
| | `exerciciosdafny4` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | Dafny (sets, multisets); convencao Dafny |
| | `exerciciosdafny5` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; pre-e-pos-condicoes | conteudo | Dafny (classes, frames); convencao Dafny |
| | `verificacaomodelos` | 03-verificac | especificacao-de-propriedades-para-sistemas-sequenciais-e-concorrentes ~ | **verificacao-de-modelos-model-checking** | fundamentos-de-logicas-temporais ; especificacao-de-propriedades-para-sistemas-sequenciais-e-concorrentes ; modelos-de-kripke | conteudo | slides gerais da unidade |
| | `exercicioslogicatemporal` | 03-verificac | verificacao-de-modelos-model-checking ~ | **fundamentos-de-logicas-temporais** | verificacao-de-modelos-model-checking ; logica-temporal-linear ; logica-temporal-ramificada | conteudo |  |
| | `exerciciosnusmv` | 03-verificac | softwares-de-suporte-a-verificacao-formal-de-modelos = | **softwares-de-suporte-a-verificacao-formal-de-modelos** | verificacao-de-modelos-model-checking | conteudo | NuSMV/NuXMV/Fasten |
| | `classes-parte1` | 02-verificac | verificacao-de-programas ~ | **pre-e-pos-condicoes** | softwares-de-suporte-a-verificacao-formal-de-programas ; verificacao-de-programas | conteudo | classe Contador com contratos em Dafny |
| | `colecoes-arrays` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | RESUMO DE CODIGO ERRADO (repete 'datatype Cor'); rotulado pelo label 'Exemplos (Arrays)' + convencao Dafny |
| | `colecoes-conjuntos` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | resumo repetido; label 'Exemplos (Conjuntos e sequencias)' |
| | `colecoes-sequences` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | label | resumo repetido; label 'Exemplos (Sequencias)' |
| | `exercicios-conjuntos` | 02-verificac | invariante-e-variante-de-laco ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; invariante-e-variante-de-laco | conteudo | respostas: metodos verificados sobre arrays/sequencias (maximo, permutacao, busca) |
| | `hoare` | 02-verificac | logica-de-hoare = | **logica-de-hoare** | softwares-de-suporte-a-verificacao-formal-de-programas ; verificacao-de-programas | label | label 'Exemplos (Logica de Floyd-Hoare)'; resumo amplo cita Hoare |
| | `introducao-zip` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas | conteudo | introducao a Dafny: funcoes e predicados, transparencia |
| | `invariantes` | 02-verificac | - ~ | **invariante-e-variante-de-laco** |  | label | RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (invariantes de laco)' |
| | `terminacao` | 02-verificac | - X | **correcao-parcial-e-total** | invariante-e-variante-de-laco | label | RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (Terminacao)' |
| | `tiposindutivos` | 02-verificac | verificacao-de-programas X | **softwares-de-suporte-a-verificacao-formal-de-programas** |  | label | tipos indutivos em Dafny (conteudo de u01 na ferramenta de u02); por card u02 = softwares-de-suporte |
| | `exemplos-zip` | 03-verificac | - X | **softwares-de-suporte-a-verificacao-formal-de-modelos** | verificacao-de-modelos-model-checking | label | RESUMO DE CODIGO ERRADO (diz Dafny); label 'Exemplos NuSMV', card 'Especificacao e Verificacao de Modelos' |
| | `exerciciosformalizacaoalgoritmosrecursao` | 01-metodos-f | especificacao-de-funcoes-recursivas = | **especificacao-de-funcoes-recursivas** |  | conteudo | equacoes recursivas III (arvores) |
| | `classes-parte2` | 02-verificac | correcao-parcial-e-total X | **verificacao-de-programas** | invariante-e-variante-de-laco ; pre-e-pos-condicoes ; softwares-de-suporte-a-verificacao-formal-de-programas | conteudo | BST verificada com ghost e invariantes de classe |
| | `exercicios-arrays` | 02-verificac | verificacao-de-programas ~ | **softwares-de-suporte-a-verificacao-formal-de-programas** | verificacao-de-programas ; invariante-e-variante-de-laco ; pre-e-pos-condicoes | conteudo | respostas: algoritmos em arrays verificados em Dafny |
| | `logicadehoare-exercicios-respostas` | 02-verificac | logica-de-hoare = | **logica-de-hoare** |  | conteudo |  |

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
