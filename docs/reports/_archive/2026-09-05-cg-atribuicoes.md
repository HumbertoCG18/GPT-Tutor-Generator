# CG — atribuicoes apos a curadoria de unidade (2026-09-05 tarde; CG `2c5e01e`)

93 materiais · blocos por metodo: {'janela-1': 24, 'llm': 32, 'disamb': 8, 'titulo-topico': 13, 'irmao-card': 2, 'disamb-curto': 3, 'llm-funil': 8, 'prep-prova': 1, 'meta-generica': 2} · flagadas 15 · unidades: {'01-introduca': 12, '03-processam': 17, '07-represent': 15, '06-processo-': 10, '08-sintese-d': 5, '04-processo-': 18, '02-fundament': 16}
Unidade: 22/93 erradas -> **1/93** (`texturas-v3`, sem bloco, u01 por conteudo; u08 sem termo no GLOSSARY.md) + 2 por erro de BLOCO (texturas no bloco-06, flagadas).
Subunidade (gold proposto v2, aguarda aprovacao): 82 pontuaveis, produto acerta 49 com extras.

| entry | card | bloco | metodo | unidade | subunidade (produto) | gold sub (proposta) | ok? |
|---|---|---|---|---|---|---|---|
| `intro` | 1 - Origens da Computaçã | bloco-01 | janela-1 | 01-introducao- | - | conceitos | ERRO |
| `origensdacomputacaografica` | 1 - Origens da Computaçã | bloco-01 | janela-1 | 01-introducao- | origens | origens | ok |
| `segmentacaopptx` | 10 - Segmentação de Imag | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `segmentacaodetexturas` | 10 - Segmentação de Imag | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `morfologiamatematicapptx` | 11 - Morfologia Matemáti | bloco-08 | disamb | 03-processamen | cores-e-tipos-de-imagens | segmentacao | ERRO |
| `csg` | 12 - Modelagem Geométric | bloco-15 | llm | 07-representac | geometria-solida-construtiva | geometria-solida-construtiva-csg | ok |
| `modelagem3d` | 12 - Modelagem Geométric | bloco-15 | titulo-topico | 07-representac | representacao-aramada | formas-de-representacao | ok |
| `atividade` | 13 - Computação Gráfica  | bloco-19 | llm | 06-processo-de | conceito-de-camera-sintetica | conceito-de-camera-sintetica | ok |
| `basico3d-py` | 13 - Computação Gráfica  | bloco-18 | llm | 06-processo-de | perspectiva | conceito-de-camera-sintetica | ERRO |
| `opengl3d` | 13 - Computação Gráfica  | bloco-19 | llm | 06-processo-de | conceito-de-camera-sintetica | conceito-de-camera-sintetica | ok |
| `opengl3dcpp-vdi` | 13 - Computação Gráfica  | bloco-19 | irmao-card | 06-processo-de | conceito-de-camera-sintetica | conceito-de-camera-sintetica | ok |
| `opengl3dcpp` | 13 - Computação Gráfica  | bloco-19 | irmao-card | 06-processo-de | perspectiva | conceito-de-camera-sintetica | ERRO |
| `vis3d` | 13 - Computação Gráfica  | bloco-18 | llm | 06-processo-de | paralela | projecoes | ok |
| `basico3d-cpp` | 14 - Exercícios sobre Mo | bloco-15 | llm | 07-representac | representacao-de-curvas-para | tecnicas-de-modelagem-3d | ERRO |
| `basico3d-py-zip` | 14 - Exercícios sobre Mo | bloco-15 | llm | 07-representac | tecnicas-de-modelagem-3d | tecnicas-de-modelagem-3d | ok |
| `exerciciodemodelagem` | 14 - Exercícios sobre Mo | bloco-15 | llm | 07-representac | tecnicas-de-modelagem-3d | varredura | ok |
| `elemoculto` | 15 - Remoção de Elemento | bloco-20 | janela-1 | 06-processo-de | algoritmo-z-buffer | algoritmos-de-remocao-de-elementos-ocultos | ok |
| `exemplozbuffer` | 15 - Remoção de Elemento | bloco-20 | janela-1 ⚑ | 06-processo-de | algoritmo-z-buffer | algoritmo-z-buffer | ok |
| `iluminacao` | 16 - Síntese de Imagens  | bloco-21 | titulo-topico | 08-sintese-de- | modelos-de-reflexao-ambiente | modelos-de-iluminacao-luz-pontual-direcional-spot | ok |
| `programabasico3d` | 16 - Síntese de Imagens  | bloco-21 | llm | 08-sintese-de- | modelos-de-reflexao-ambiente | modelos-de-reflexao-ambiente-difusa-especular | ok |
| `maptextures` | 17 - Mapeamento de Textu | bloco-06 | janela-1 | 04-processo-de | sistema-de-coordenadas-carte | - | fora |
| `exercicios` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | (vazio) | ERRO |
| `opengl-cpp` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | (vazio) | ERRO |
| `opengl-py` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | (vazio) | ERRO |
| `openglbasico` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | (vazio) | ERRO |
| `texturas-v3` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | - | fora |
| `exemplodemanipulacaodeimagens` | 3 - Fundamentos Matemáti | bloco-03 | llm | 02-fundamentos | entidades-geometricas | - | fora |
| `exercicio-com-animacao` | 3 - Fundamentos Matemáti | bloco-03 | llm | 02-fundamentos | - | operacoes-com-vetores | ERRO |
| `exercicio-com-poligonos` | 3 - Fundamentos Matemáti | bloco-03 | llm | 02-fundamentos | algoritmos-de-poligonos | algoritmos-de-poligonos | ok |
| `exercicio-de-animacao-foguete` | 3 - Fundamentos Matemáti | bloco-03 | llm | 02-fundamentos | algoritmos-de-poligonos | operacoes-com-vetores | ok |
| `fundamentosmatematicos` | 3 - Fundamentos Matemáti | bloco-03 | titulo-topico | 02-fundamentos | entidades-geometricas | entidades-geometricas | ok |
| `matematica` | 3 - Fundamentos Matemáti | bloco-03 | llm | 02-fundamentos | entidades-geometricas | operacoes-com-vetores | ok |
| `colisao` | 4 - Detecção de Colisão | bloco-04 | janela-1 | 02-fundamentos | algoritmos-de-deteccao-e-cal | algoritmos-de-deteccao-e-calculo-de-interseccao | ok |
| `geomcomp` | 5 - Geometria Computacio | bloco-05 | titulo-topico | 02-fundamentos | algoritmos-de-geometria-comp | algoritmos-de-geometria-computacional | ok |
| `animacao-v2` | 6 - Processo de Visualiz | bloco-06 | llm | 04-processo-de | desenho-de-linhas | (vazio) | ERRO |
| `exercicios-teoricos-sobre-processo` | 6 - Processo de Visualiz | bloco-06 | disamb | 04-processo-de | desenho-de-linhas | sistema-de-coordenadas-cartesianas | ERRO |
| `instanciamento` | 6 - Processo de Visualiz | bloco-06 | llm | 04-processo-de | 2d-3d-mao-direita-e-mao-esqu | (vazio) | ERRO |
| `mapeamento` | 6 - Processo de Visualiz | bloco-06 | disamb | 04-processo-de | sistema-de-coordenadas-carte | sistema-de-coordenadas-cartesianas | ok |
| `pagina-com-videos-sobre-instanciam` | 6 - Processo de Visualiz | bloco-06 | disamb-curto | 04-processo-de | desenho-de-linhas | (vazio) | ERRO |
| `recorte` | 6 - Processo de Visualiz | bloco-06 | titulo-topico | 04-processo-de | recorte | recorte | ok |
| `transformacoesgeometricas` | 6 - Processo de Visualiz | bloco-06 | disamb-curto | 04-processo-de | - | (vazio) | ok |
| `transformacoesgl` | 6 - Processo de Visualiz | bloco-06 | llm | 04-processo-de | sistema-de-coordenadas-carte | (vazio) | ERRO |
| `vis2d` | 6 - Processo de Visualiz | bloco-06 | disamb-curto | 04-processo-de | recorte | sistema-de-coordenadas-cartesianas | ok |
| `bezier-animacao` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | - | bezier-e-algoritmo-de-casteljau | ERRO |
| `bezier-cpp` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | - | bezier-e-algoritmo-de-casteljau | ERRO |
| `bezier-py` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | - | bezier-e-algoritmo-de-casteljau | ERRO |
| `bezier-python` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | - | bezier-e-algoritmo-de-casteljau | ERRO |
| `curvas` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | hermite | representacao-de-curvas-parametricas | ok |
| `curvasparametricas` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | - | representacao-de-curvas-parametricas | ERRO |
| `exercicios-sobre-curvas` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | hermite | catmull-rom | ERRO |
| `floodfill` | 8 - Manipulação de Image | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `img` | 8 - Manipulação de Image | bloco-07 | llm | 03-processamen | filtros | cores-e-tipos-de-imagens | ok |
| `remocaoderuido` | 8 - Manipulação de Image | bloco-07 | llm | 03-processamen | filtros | filtros | ok |
| `exercicios-de-processamento-de-ima` | 9 - Introdução ao Proces | bloco-07 | disamb | 03-processamen | cores-e-tipos-de-imagens | algoritmos-de-quantizacao-e-amostragem | ok |
| `introducaoprocimg` | 9 - Introdução ao Proces | bloco-07 | llm | 03-processamen | filtros | filtros | ok |
| `exercicios-de-geometria-computacio` | Exercícios 2D | bloco-05 | llm-funil ⚑ | 02-fundamentos | entidades-geometricas | algoritmos-de-geometria-computacional | ERRO |
| `exercicios-sobre-curvas-html` | Exercícios 2D | bloco-13 | llm-funil ⚑ | 07-representac | hermite | catmull-rom | ERRO |
| `exercicios-teoricos-sobre-processo` | Exercícios 2D | bloco-06 | llm-funil ⚑ | 04-processo-de | desenho-de-linhas | sistema-de-coordenadas-cartesianas | ERRO |
| `exerciciosfundamentosmatematicos` | Exercícios 2D | bloco-03 | llm-funil ⚑ | 02-fundamentos | algoritmos-de-poligonos | algoritmos-de-poligonos | ok |
| `resolucao-de-prova-de-computacao-g` | Exercícios 2D | bloco-06 | llm-funil ⚑ | 04-processo-de | desenho-de-linhas | - | fora |
| `listadeexercicios2026-1` | Exercícios para P2 | bloco-21 | prep-prova | 08-sintese-de- | - | - | fora |
| `cronograma2026-2` | Plano de Ensino | bloco-01 | meta-generica | 01-introducao- | - | - | fora |
| `planodeensino-4645z-04-fundamentos` | Plano de Ensino | bloco-01 | meta-generica | 01-introducao- | - | - | fora |
| `videoscg-v2` | Plano de Ensino | bloco-01 | llm-funil ⚑ | 01-introducao- | conceitos | - | fora |
| `resolucao-de-prova-de-computacao-g` | Provas Resolvidas | bloco-06 | llm-funil ⚑ | 04-processo-de | desenho-de-linhas | - | fora |
| `resolucao-de-prova-de-computacao-g` | Provas Resolvidas | bloco-29 | llm-funil ⚑ | 08-sintese-de- | mapeamento-de-textura | - | fora |
| `domina` | 5 - Geometria Computacio | bloco-05 | titulo-topico | 02-fundamentos | entidades-geometricas | algoritmos-de-geometria-computacional | ERRO |
| `planesweep` | 5 - Geometria Computacio | bloco-05 | titulo-topico | 02-fundamentos | algoritmos-de-geometria-comp | algoritmos-de-geometria-computacional | ok |
| `slab` | 5 - Geometria Computacio | bloco-05 | titulo-topico | 02-fundamentos | algoritmos-de-poligonos | algoritmos-de-geometria-computacional | ok |
| `exercicioduascores` | 8 - Manipulação de Image | bloco-07 | llm | 03-processamen | - | algoritmos-de-quantizacao-e-amostragem | ERRO |
| `video-sobre-origens-da-computacao-` | 1 - Origens da Computaçã | bloco-01 | janela-1 | 01-introducao- | origens | origens | ok |
| `video-com-instrucoes-para-usar-ope` | 2 - Biblioteca OpenGL | bloco-02 | janela-1 ⚑ | 01-introducao- | conceitos | (vazio) | ERRO |
| `pagina-com-videos-sobre-fundamento` | 3 - Fundamentos Matemáti | bloco-03 | titulo-topico | 02-fundamentos | - | entidades-geometricas | ERRO |
| `videos-sobre-algoritmos-de-detecao` | 4 - Detecção de Colisão | bloco-04 | janela-1 | 02-fundamentos | - | algoritmos-de-deteccao-e-calculo-de-interseccao | ERRO |
| `pagina-com-videos-sobre-geometria-` | 5 - Geometria Computacio | bloco-05 | titulo-topico | 02-fundamentos | algoritmos-de-geometria-comp | algoritmos-de-geometria-computacional | ok |
| `pagina-com-videos-sobre-recorte-e2` | 6 - Processo de Visualiz | bloco-06 | titulo-topico | 04-processo-de | recorte | recorte | ok |
| `video-sobre-o-algoritmo-de-recorte` | 6 - Processo de Visualiz | bloco-06 | titulo-topico | 04-processo-de | recorte | recorte | ok |
| `pagina-com-videos-sobre-mapeamento` | 6 - Processo de Visualiz | bloco-06 | llm | 04-processo-de | sistema-de-coordenadas-carte | sistema-de-coordenadas-cartesianas | ok |
| `video-sobre-mapeamento-em-opengl-1` | 6 - Processo de Visualiz | bloco-06 | disamb | 04-processo-de | 2d-3d-mao-direita-e-mao-esqu | sistema-de-coordenadas-cartesianas | ERRO |
| `pagina-com-videos-sobre-curvas-par` | 7 - Curvas Paramétricas | bloco-13 | janela-1 | 07-representac | representacao-de-curvas-para | representacao-de-curvas-parametricas | ok |
| `pagina-com-videos-sobre-manipulaca` | 8 - Manipulação de Image | bloco-07 | llm | 03-processamen | cores-e-tipos-de-imagens | cores-e-tipos-de-imagens | ok |
| `pagina-com-videos-sobre-introducao` | 9 - Introdução ao Proces | bloco-07 | disamb | 03-processamen | - | introducao-e-exemplos-de-aplicacoes | ERRO |
| `pagina-com-videos-sobre-segmentaca` | 10 - Segmentação de Imag | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `pagina-com-videos-sobre-segmentaca` | 10 - Segmentação de Imag | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `aula-gravada-975b85` | 11 - Morfologia Matemáti | bloco-08 | disamb | 03-processamen | - | segmentacao | ERRO |
| `pagina-com-videos-sobre-morfologia` | 11 - Morfologia Matemáti | bloco-08 | disamb | 03-processamen | - | segmentacao | ERRO |
| `video-sobre-prechimento-de-areas-d` | Exercícios de Processame | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `video-sobre-prechimento-de-areas-d` | Exercícios de Processame | bloco-07 | llm | 03-processamen | segmentacao | segmentacao | ok |
| `paginas-com-videos-sobre-modelagem` | 12 - Modelagem Geométric | bloco-15 | titulo-topico | 07-representac | tecnicas-de-modelagem-3d | tecnicas-de-modelagem-3d | ok |
| `pagina-com-videos-sobre-visualizac` | 13 - Computação Gráfica  | bloco-18 | llm | 06-processo-de | pipeline-de-visualizacao-3d | pipeline-de-visualizacao-3d | ok |
| `pagina-com-videos-sobre-remocao-de` | 15 - Remoção de Elemento | bloco-20 | janela-1 | 06-processo-de | algoritmos-de-remocao-de-ele | algoritmos-de-remocao-de-elementos-ocultos | ok |
| `pagina-com-videos-sobre-sintese-de` | 16 - Síntese de Imagens  | bloco-21 | llm | 08-sintese-de- | modelos-de-reflexao-ambiente | modelos-de-iluminacao-luz-pontual-direcional-spot | ok |
| `pagina-com-videos-sobre-mapeamento` | 17 - Mapeamento de Textu | bloco-06 | janela-1 | 04-processo-de | sistema-de-coordenadas-carte | - | fora |
