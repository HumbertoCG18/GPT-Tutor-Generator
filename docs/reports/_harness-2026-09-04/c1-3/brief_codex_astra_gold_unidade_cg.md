# Brief para segunda opinião (Codex astra, read-only) — gold de unidade do CG, proposta de 2026-09-11 (noite)

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`.

## 1. O que é isto

Item 3.2 do plano de 08/09: o CG (93 materiais) não tinha gold de UNIDADE. O usuário perguntou se eu tinha informação para
rotular; rotulei os 93 como PROPOSTA (`docs/reports/material_gt_CG.csv`, gerado por `c1-3/monta_material_gt_CG.py`, colunas
`gold_units`, `gold_fonte`, `status`, `notas`), a ser adjudicada por ele, como foi o gold de subunidade de 05/09 (aprovado
06/09). Sua revisão de hoje à tarde pediu estados explícitos e fonte por linha: estão lá.

**Oráculo escolhido: a estrutura do professor**, não o motor. O Moodle do CG tem 22 seções numeradas pelo professor ("6 -
Processo de Visualização 2D", "17 - Mapeamento de Texturas"); o cronograma dá a aula de cada assunto. A unidade que o
produto grava vem do BLOCO TEMPORAL em 87/93 (os 6 restantes estão em blocos sem unidade); a seção do Moodle não entra na
decisão de unidade do motor (entra só na 1ª passada de subunidade, `secao-nomeia-subtopico`). Logo seção → unidade é uma
medida de fora do mapa bloco → unidade.

Regras, nesta ordem (docstring do script): (1) seção "Plano de Ensino" = meta → todas as unidades (ruling do usuário de
2026-08-19 no SO: "meta-material cobre TODAS as unidades"); (2) prova resolvida e lista de prova → unidades que a prova cobre,
lidas do conteúdo (mesmo ruling: "Lista PX cobre as unidades da PROVA"); (3) regra por material quando o conteúdo contradiz a
seção ou a seção "Exercícios 2D" cruza unidades; (4) seção → unidade. Seção 6 = u04 pelo oráculo (ruling aprovado em 06/09:
"bloco-06 = u04 pelo oráculo; transformações/instanciamento sem subtópico em u04 → vazio"), com nota "plano: u05" onde cabe.

Contagem por fonte: seção → unidade 76 · seção 2 OpenGL + cronograma 5 · conteúdo 5 · meta 3 · prova/lista 4.
**Produto acerta 85/93 na unidade.** Os 8 erros: 3 texturas (plano 8.4 → u08; produto u04/u02 por colisão de token no
bloco-06, nota aprovada 06/09 "BLOCO ERRADO") e 5 da seção "2 - Biblioteca OpenGL" (proposto u01; produto u02).

Verificado hoje com o usuário: "Texturas é unidade 8" (confirma 8.4 do plano). Sobre OpenGL ele disse "OpenGL está no card 2,
2 - Biblioteca OpenGL" e pediu para verificar o plano de ensino: **o plano NÃO lista OpenGL em unidade nenhuma** (só na
bibliografia complementar). O cronograma põe "Introdução à OpenGL" na aula 2 (06/08), entre Origens (u01, aula 1) e
Fundamentos Matemáticos (u02, aulas 3-4). Em 06/09 o gold de subunidade desses materiais foi rotulado com o produto em u01
("card 2 OpenGL, sem bloco"); hoje o produto grava u02 (bloco-02 tem `unit_slug` vazio, conf 0,0).

## 2. Plano de ensino do professor (MEDIDO, texto extraído do PDF `planodeensino-4645z-04-...`)
```
Nº DA UNIDADE : 01 Nº DE HORAS EM PERCENTUAL: 5% CONTEÚDO : Introdução ao Processamento Gráfico
- 1.1. Origens
- 1.2. Conceitos
1.3. Áreas relacionadas
- 1.4. Aplicações
Nº DA UNIDADE: 02 Nº DE HORAS EM PERCENTUAL: 15% CONTEÚDO: Fundamentos Matemáticos
- 2.1. Entidades geométricas
- 2.2. Operações com vetores
- 2.3. Algoritmos de detecção e cálculo de intersecção
- 2.4. Algoritmos de polígonos
- 2.5. Algoritmos de Geometria Computacional
Nº DA UNIDADE: 03 Nº DE HORAS EM PERCENTUAL: 15%
CONTEÚDO: Processamento de Imagens e Visão Computacional
- 3.1. Introdução e Exemplos de Aplicações
- 3.2. Cores e tipos de imagens
- 3.3. Algoritmos de Quantização e Amostragem
- 3.4. Filtros
- 3.5. Segmentação
- 3.6. Visão Computacional e conceito de reconhecimento de padrões
Nº DA UNIDADE: 04 Nº DE HORAS EM PERCENTUAL: 10% CONTEÚDO: Processo de Visualização 2D
- 4.1. Sistema de Coordenadas Cartesianas
- 4.1.1. 2D, 3D (mão direita) e (mão esquerda)
- 4.2. Algoritmos de Rasterização
- 4.2.1. Desenho de Linhas
- 4.2.2. Preenchimento de Polígonos
- 4.2.3. Recorte
Nº DA UNIDADE: 05 Nº DE HORAS EM PERCENTUAL: 12% CONTEÚDO: Transformações geométricas
5.1. Transformações Geométricas e coordenadas homogêneas 2D
- 5.2. Mapeamento _Window_ e _Viewport_
- 5.3. Pipeline de visualização 2D
- 5.4. Composição de transformações 2D
- 5.5. Representação matricial das transformações 3D
- 5.6. Composição de transformações 3D
Nº DA UNIDADE: 06 Nº DE HORAS EM PERCENTUAL: 10% CONTEÚDO: Processo de Visualização 3D
6.1. Pipeline de visualização 3D
- 6.2. Conceito de Câmera Sintética
6.3. Projeções
6.3.1. Paralela
6.3.2. Perspectiva
6.3.3. A matemática das projeções planares
- 6.4. Algoritmos de Remoção de Elementos Ocultos
- 6.4.1. Eliminação de Faces Traseiras
- 6.4.2. Algoritmo do Pintor
6.4.3. Algoritmo _Z-Buffer_
- 6.4.4. Árvores BSP
Nº DA UNIDADE: 07 Nº DE HORAS EM PERCENTUAL: 15% CONTEÚDO: Representação e Modelagem de Objetos
7.1. Formas de Representação
7.1.1. Representação de Curvas Paramétricas
- 7.1.1.1. Bézier e Algoritmo de Casteljau
- 7.1.1.2. Hermite
- 7.1.1.3. B-Spline
- 7.1.1.4. Catmull-Rom
- 7.1.2. Vetorial ou Matricial
- 7.1.3. Enumeração Espacial
- 7.1.4. Representação Aramada
- 7.1.5. Superfícies Limitantes
- 7.2. Técnicas de Modelagem 3D
- 7.2.1. Digitalização
- 7.2.2. Varredura
- 7.2.3. Geometria Sólida Construtiva (CSG)
- 7.2.4. Instanciamento de Primitivas
Nº DA UNIDADE: 8 Nº DE HORAS EM PERCENTUAL: 10% CONTEÚDO: Síntese de Imagens Realísticas
- 8.1. Modelos de Iluminação: luz pontual, direcional, _spot_
- 8.2. Modelos de Reflexão: ambiente, difusa, especular
- 8.3. Métodos de sombreamento: _Flat_ , Gouraud, Phong
- 8.4. Mapeamento de Textura
- 8.5. Conceitos Básicos de _Ray Tracing_ e Radiosidade
Nº DA UNIDADE: 9 Nº DE HORAS EM PERCENTUAL: 8% CONTEÚDO: Tópicos Especiais em Pesquisa em CG
9.1. Temas atuais e avançados de Computação Gráfica
```

## 3. Cronograma 2026/2 (MEDIDO, texto extraído do PDF `cronograma2026-2`, células achatadas)
```
98716-4 COMPUTAÇÃO GRÁFICA (310) - 32/401
1 Apresentação da disciplina e Origens
TER 04/08/2026 JK Aula
da CG
2 Retirar
QUI 06/08/2026 JK Introdução à OpenGL Aula
notebook
3 Fundamentos Matemáticos para CG &
TER 11/08/2026 JK Aula
PI
4 Fundamentos Matemáticos para CG & Retirar
QUI 13/08/2026 JK Aula
PI notebook
5
TER 18/08/2026 JK Algoritmos de Detecção de Colisão Aula
6
QUI 20/08/2026 JK Geometria Computacional Aula
7 Processo de Visualização 2D -
TER 25/08/2026 JK Aula
Instanciamento
8 Processo de Visualização 2D - Recorte Retirar
QUI 27/08/2026 JK Aula
e mapeamento notebook
9 Processamento de Imagens e Visão
TER 01/09/2026 JK Aula
Computacional
10 Processamento de Imagens e Visão
QUI 03/09/2026 JK Aula
Computacional
11
TER 08/09/2026 JK Aula de Exercícios Aula
12
QUI 10/09/2026 JK Morfologia Matemática Aula
13
TER 15/09/2026 JK Aula de Exercícios Aula
14
QUI 17/09/2026 JK Aula de Exercícios Aula
15
TER 22/09/2026 JK Aula de dúvidas Aula
16
QUI 24/09/2026 JK Prova P1 Prova
17 Retirar
TER 29/09/2026 JK Aula de dúvidas Aula
notebook
18
QUI 01/10/2026 JK Trabalho I Trabalho
19
TER 06/10/2026 JK Curvas Paramétricas Aula
20
QUI 08/10/2026 JK Curvas Paramétricas Aula
TER 13/10/2026 JK Feriado Aula
21
QUI 15/10/2026 JK Modelagem Geométrica Aula
22 Evento
TER 20/10/2026 JK Semana Acadêmica
Acadêmico
23 Evento
QUI 22/10/2026 JK Semana Acadêmica
Acadêmico
24
TER 27/10/2026 JK Visualização 3D - Projeção Aula
25
QUI 29/10/2026 JK Visualização 3D - Observador Aula
26
TER 03/11/2026 JK Remoção de Elementos ocultos Aula
27
QUI 05/11/2026 JK Remoção de Elementos Ocultos Aula
28
TER 10/11/2026 JK Iluminação Aula
29
QUI 12/11/2026 JK Aula de Exercícios Aula
30
TER 17/11/2026 JK Aula de dúvidas Aula
31
QUI 19/11/2026 JK Prova P2 Prova
32 Prova de
TER 24/11/2026 JK Prova PS
Substituição
33
QUI 26/11/2026 JK Aula de dúvidas Aula
34
TER 01/12/2026 JK Trabalho 2 Trabalho
35
QUI 03/12/2026 JK Aula de dúvidas Aula
TER 08/12/2026 JK Prova G2 Prova de G2
QUI 10/12/2026 JK Aula
```

## 4. As 93 linhas propostas (MEDIDO, `docs/reports/material_gt_CG.csv`; pred = `computed_unit_slug` do produto)
`todas(9)` = as 9 unidades com `|`. Nota truncada em 110 chars.
```
id | cat | secao Moodle | pred (produto) | gold proposto | fonte | nota
basico3d-cpp | codigo-pro | 14 - Exercícios sobre Modelagem Ge | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.27 revisar=ok
basico3d-py-zip | codigo-pro | 14 - Exercícios sobre Modelagem Ge | unidade-07- | unidade-07- | secao-moodle | conflito: texto queria unidade-06-processo-de-visualizacao-3d · unit_conf=0.61 revisar=duvida
csg | outros | 12 - Modelagem Geométrica | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.59 revisar=mudou
exerciciodemodelagem | listas | 14 - Exercícios sobre Modelagem Ge | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.27 revisar=ok
modelagem3d | outros | 12 - Modelagem Geométrica | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.61 revisar=mudou
paginas-com-videos-sobre-modelagem-geometric | references | 12 - Modelagem Geométrica | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.99 revisar=ok
exemplodemanipulacaodeimagens | codigo-pro | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | subunit_gt scorable=no: CONFLITO: label do Moodle 'Classe Vetor' (u02) x conteudo do .cpp = processamento de i
exercicio-com-animacao | listas | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.95 revisar=duvida
exercicio-com-poligonos | listas | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.96 revisar=ok
exercicio-de-animacao-foguete | listas | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | conflito: texto queria unidade-04-processo-de-visualizacao-2d · unit_conf=0.77 revisar=duvida
exerciciosfundamentosmatematicos | listas | Exercícios 2D | unidade-02- | unidade-02- | conteudo | secao 'Exercicios 2D' cruza unidades; poligonos e vetores · unit_conf=0.95 revisar=mudou
fundamentosmatematicos | material-d | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.95 revisar=mudou
matematica | codigo-pro | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | conflito: texto queria unidade-06-processo-de-visualizacao-3d · unit_conf=0.73 revisar=duvida
pagina-com-videos-sobre-fundamentos-matemati | references | 3 - Fundamentos Matemáticos para C | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.95 revisar=ok
iluminacao | outros | 16 - Síntese de Imagens Realística | unidade-08- | unidade-08- | secao-moodle | unit_conf=0.50 revisar=ok
listadeexercicios2026-1 | listas | Exercícios para P2 | unidade-08- | unidade-06-|unidade-07-|unidade-08- | ruling-user 2026-08-19 (SO): lista | lista para P2: iluminacao + projecao + modelagem (nota aprovada 06/09) · subunit_gt scorable=no: lista para P2
pagina-com-videos-sobre-sintese-de-imagens-r | references | 16 - Síntese de Imagens Realística | unidade-08- | unidade-08- | secao-moodle | unit_conf=0.95 revisar=ok
programabasico3d | codigo-pro | 16 - Síntese de Imagens Realística | unidade-08- | unidade-08- | secao-moodle | conflito: texto queria unidade-06-processo-de-visualizacao-3d · unit_conf=0.63 revisar=duvida
animacao-v2 | codigo-pro | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
exercicios-teoricos-sobre-processo-de-visual | listas | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
exercicios-teoricos-sobre-processo-de-visual | listas | Exercícios 2D | unidade-04- | unidade-04- | conteudo | secao 'Exercicios 2D' cruza unidades; processo de visualizacao 2D, u04 pelo oraculo · unit_conf=0.89 revisar=o
instanciamento | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
mapeamento | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
maptextures | outros | 17 - Mapeamento de Texturas | unidade-04- | unidade-08- | secao-moodle | plano de ensino 8.4 'Mapeamento de Textura' = u08 (user 11/09: 'Texturas e unidade 8'); produto poe em u04 por
pagina-com-videos-sobre-instanciamento | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
pagina-com-videos-sobre-mapeamento-9f410e | references | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
pagina-com-videos-sobre-mapeamento-de-textur | references | 17 - Mapeamento de Texturas | unidade-04- | unidade-08- | secao-moodle | plano de ensino 8.4 'Mapeamento de Textura' = u08 (user 11/09: 'Texturas e unidade 8'); produto poe em u04 por
pagina-com-videos-sobre-recorte-e257d3 | references | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09) · unit_conf=1.00 revisar=ok
recorte | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09) · unit_conf=0.58 revisar=ok
resolucao-de-prova-de-computacao-grafica-2d | provas | Exercícios 2D | unidade-04- | unidade-04-|unidade-05- | ruling-user 2026-08-19 (SO): prova | prova 2D: transformacoes/instanciamento em OpenGL (u04 pelo oraculo, u05 pelo plano) · subunit_gt scorable=no:
resolucao-de-prova-de-computacao-grafica-2d- | provas | Provas Resolvidas | unidade-04- | unidade-04-|unidade-05- | ruling-user 2026-08-19 (SO): prova | duplicata html da prova 2D · subunit_gt scorable=no: prova resolvida (duplicata html) · unit_conf=0.47 revisar
transformacoesgeometricas | codigo-pro | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · confli
transformacoesgl | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · confli
video-sobre-mapeamento-em-opengl-1dad3c | references | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
video-sobre-o-algoritmo-de-recorte-por-subdi | references | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09) · unit_conf=0.95 revisar=ok
vis2d | outros | 6 - Processo de Visualização 2D | unidade-04- | unidade-04- | secao-moodle | u04 pelo oraculo (ruling aprovado 06/09); o plano poe transformacoes/instanciamento/mapeamento em u05 · unit_c
exercicios | listas | 2 - Biblioteca OpenGL | unidade-02- | unidade-01- | secao-moodle + cronograma | RULING pendente: o plano de ensino NAO lista OpenGL em unidade nenhuma (so na bibliografia complementar); cron
opengl-cpp | codigo-pro | 2 - Biblioteca OpenGL | unidade-02- | unidade-01- | secao-moodle + cronograma | RULING pendente: o plano de ensino NAO lista OpenGL em unidade nenhuma (so na bibliografia complementar); cron
opengl-py | codigo-pro | 2 - Biblioteca OpenGL | unidade-02- | unidade-01- | secao-moodle + cronograma | RULING pendente: o plano de ensino NAO lista OpenGL em unidade nenhuma (so na bibliografia complementar); cron
openglbasico | outros | 2 - Biblioteca OpenGL | unidade-02- | unidade-01- | secao-moodle + cronograma | RULING pendente: o plano de ensino NAO lista OpenGL em unidade nenhuma (so na bibliografia complementar); cron
texturas-v3 | codigo-pro | 2 - Biblioteca OpenGL | unidade-02- | unidade-08- | conteudo | texturas + iluminacao = u08 (plano de ensino 8.4; nota aprovada 06/09: UNIDADE ERRADA); a secao 2 OpenGL nao v
video-com-instrucoes-para-usar-opengl-na-vdi | references | 2 - Biblioteca OpenGL | unidade-02- | unidade-01- | secao-moodle + cronograma | RULING pendente: o plano de ensino NAO lista OpenGL em unidade nenhuma (so na bibliografia complementar); cron
elemoculto | material-d | 15 - Remoção de Elementos Ocultos | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.71 revisar=ok
exemplozbuffer | outros | 15 - Remoção de Elementos Ocultos | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.85 revisar=ok
pagina-com-videos-sobre-remocao-de-elementos | references | 15 - Remoção de Elementos Ocultos | unidade-06- | unidade-06- | secao-moodle | unit_conf=1.00 revisar=ok
domina | outros | 5 - Geometria Computacional | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.95 revisar=ok
exercicios-de-geometria-computacional | listas | Exercícios 2D | unidade-02- | unidade-02- | conteudo | secao 'Exercicios 2D' cruza unidades; matriz de dominancia · unit_conf=0.21 revisar=mudou
geomcomp | outros | 5 - Geometria Computacional | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.99 revisar=ok
pagina-com-videos-sobre-geometria-computacio | references | 5 - Geometria Computacional | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.95 revisar=ok
planesweep | outros | 5 - Geometria Computacional | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.16 revisar=ok
slab | outros | 5 - Geometria Computacional | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.66 revisar=ok
colisao | material-d | 4 - Detecção de Colisão | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.93 revisar=ok
videos-sobre-algoritmos-de-detecao-de-colisa | references | 4 - Detecção de Colisão | unidade-02- | unidade-02- | secao-moodle | unit_conf=0.99 revisar=ok
bezier-animacao | codigo-pro | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.28 revisar=ok
bezier-cpp | codigo-pro | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | conflito: texto queria unidade-01-introducao-ao-processamento-grafico · unit_conf=0.50 revisar=duvida
bezier-py | codigo-pro | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | conflito: texto queria unidade-01-introducao-ao-processamento-grafico · unit_conf=0.95 revisar=duvida
bezier-python | codigo-pro | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | conflito: texto queria unidade-02-fundamentos-matematicos · unit_conf=0.58 revisar=duvida
curvas | outros | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.62 revisar=mudou
curvasparametricas | material-d | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.76 revisar=ok
exercicios-sobre-curvas | listas | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.61 revisar=mudou
exercicios-sobre-curvas-html | listas | Exercícios 2D | unidade-07- | unidade-07- | conteudo | secao 'Exercicios 2D' cruza unidades; duplicata de exercicios-sobre-curvas · unit_conf=0.59 revisar=mudou
pagina-com-videos-sobre-curvas-parametricas- | references | 7 - Curvas Paramétricas | unidade-07- | unidade-07- | secao-moodle | unit_conf=0.88 revisar=ok
atividade | outros | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.95 revisar=mudou
opengl3d | outros | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.56 revisar=mudou
opengl3dcpp | codigo-pro | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | bundle misto (2D/3D/Bezier/imagens) rotulado pelo card 13; RULING pendente do 06/09 (apoio misto rotula pelo c
opengl3dcpp-vdi | codigo-pro | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | bundle misto (2D/3D/Bezier/imagens) rotulado pelo card 13; RULING pendente do 06/09 (apoio misto rotula pelo c
aula-gravada-975b85 | references | 11 - Morfologia Matemática | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.00 revisar=ok
morfologiamatematicapptx | material-d | 11 - Morfologia Matemática | unidade-03- | unidade-03- | secao-moodle | conflito: texto queria unidade-06-processo-de-visualizacao-3d · unit_conf=1.00 revisar=duvida
pagina-com-videos-sobre-morfologia-matematic | references | 11 - Morfologia Matemática | unidade-03- | unidade-03- | secao-moodle | conflito: texto queria unidade-06-processo-de-visualizacao-3d · unit_conf=0.95 revisar=duvida
cronograma2026-2 | cronograma | Plano de Ensino | unidade-01- | todas(9) | ruling-user 2026-08-19 (SO): meta  | meta (cronograma, plano, playlist) · subunit_gt scorable=no: meta (cronograma) · unit_conf=0.50 revisar=ok
intro | outros | 1 - Origens da Computação Gráfica | unidade-01- | unidade-01- | secao-moodle | unit_conf=0.49 revisar=mudou
origensdacomputacaografica | material-d | 1 - Origens da Computação Gráfica | unidade-01- | unidade-01- | secao-moodle | unit_conf=0.94 revisar=ok
planodeensino-4645z-04-fundamentos-de-comput | cronograma | Plano de Ensino | unidade-01- | todas(9) | ruling-user 2026-08-19 (SO): meta  | meta (cronograma, plano, playlist) · subunit_gt scorable=no: meta (plano de ensino) · unit_conf=0.25 revisar=o
video-sobre-origens-da-computacao-grafica-80 | references | 1 - Origens da Computação Gráfica | unidade-01- | unidade-01- | secao-moodle | unit_conf=0.98 revisar=ok
videoscg-v2 | outros | Plano de Ensino | unidade-01- | todas(9) | ruling-user 2026-08-19 (SO): meta  | meta (cronograma, plano, playlist) · subunit_gt scorable=no: playlist da disciplina inteira · unit_conf=0.26 r
basico3d-py | codigo-pro | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.47 revisar=ok
pagina-com-videos-sobre-visualizacao-3d-35a8 | references | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.64 revisar=ok
vis3d | outros | 13 - Computação Gráfica 3D | unidade-06- | unidade-06- | secao-moodle | unit_conf=0.64 revisar=duvida
exercicioduascores | listas | 8 - Manipulação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.40 revisar=ok
exercicios-de-processamento-de-imagens | listas | 9 - Introdução ao Processamento de | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.83 revisar=ok
floodfill | listas | 8 - Manipulação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.95 revisar=mudou
img | outros | 8 - Manipulação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.66 revisar=ok
introducaoprocimg | material-d | 9 - Introdução ao Processamento de | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.95 revisar=ok
pagina-com-videos-sobre-introducao-ao-proces | references | 9 - Introdução ao Processamento de | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.99 revisar=ok
pagina-com-videos-sobre-manipulacao-de-image | references | 8 - Manipulação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.99 revisar=ok
pagina-com-videos-sobre-segmentacao-de-image | references | 10 - Segmentação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.99 revisar=ok
pagina-com-videos-sobre-segmentacao-por-text | references | 10 - Segmentação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.95 revisar=ok
remocaoderuido | listas | 8 - Manipulação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.33 revisar=mudou
segmentacaodetexturas | outros | 10 - Segmentação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.93 revisar=ok
segmentacaopptx | material-d | 10 - Segmentação de Imagens | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.89 revisar=ok
video-sobre-prechimento-de-areas-duracao-130 | references | Exercícios de Processamento de Ima | unidade-03- | unidade-03- | secao-moodle | unit_conf=0.95 revisar=ok
video-sobre-prechimento-de-areas-duracao-330 | references | Exercícios de Processamento de Ima | unidade-03- | unidade-03- | secao-moodle | conflito: texto queria unidade-01-introducao-ao-processamento-grafico · unit_conf=0.74 revisar=duvida
resolucao-de-prova-de-computacao-grafica-3d | provas | Provas Resolvidas | unidade-08- | unidade-06-|unidade-07-|unidade-08- | ruling-user 2026-08-19 (SO): prova | prova 3D: iluminacao, sombreamento, z-buffer, projecao, textura, curva · subunit_gt scorable=no: prova resolvi
```

## 5. Perguntas, em ordem

1. **Tabela seção → unidade.** Alguma das 18 seções está mapeada na unidade errada do plano (§2)? Em especial "5 - Geometria
   Computacional" e "4 - Detecção de Colisão" em u02, "13 - Computação Gráfica 3D" em u06, "12/14 Modelagem" em u07.
2. **OpenGL (5 materiais + `exercicios`).** Com o plano mudo, o rótulo honesto é u01 (ferramenta introdutória, aula 2, contexto
   do gold de 06/09), u02 (produto hoje), `u01|u02`, ou `scorable=no`? Diga qual e o custo de cada um para a régua (um gold
   com `|` nunca testa a decisão do bloco-02).
3. **Seção 6 e u05.** O plano tem u05 "Transformações geométricas" (5.1-5.6) e o professor não tem seção nem aula chamada assim:
   ensina instanciamento, transformações e mapeamento window/viewport dentro de "Processo de Visualização 2D". O ruling de
   06/09 fixou u04. Para o gold de UNIDADE, `u04` ou `u04|u05` nos 8 materiais com nota "plano: u05"? O produto nunca grava u05.
4. **Provas e meta.** Aplicar o ruling do SO (meta = todas; prova = unidades da prova, com `|`) ao CG está certo, ou prova 2D
   deveria ser `scorable=no` como no gold de subunidade? A prova 2D tem só transformações em OpenGL (u04|u05) — faltou u02?
5. **Circularidade.** O que nesta proposta NÃO é independente do motor? A seção é lida pelo motor na subunidade; o bloco-06
   "por colisão de token" é decisão do motor; o `pred` está visível na planilha (ancoragem). Onde o gold e o motor podem
   errar juntos sem que a régua veja?
6. **Risco.** Linha a linha, quais das 93 você contestaria e por quê (id + unidade que você daria + evidência do §2/§3/§4)?
