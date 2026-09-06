"""Gera docs/reports/subunit_gt_{CG,MF}.csv PROPOSTO-CLAUDE (2026-09-05) para aprovacao do user, no formato dos golds de 25/08.
Regras usadas: subtopico dentro da UNIDADE COMPUTADA; unidade computada errada -> scorable=no com a unidade/subtopico
verdadeiros na nota; meta (plano, cronograma, playlist, provas, listas de revisao) -> scorable=no; ferramenta sem subtopico
na taxonomia (OpenGL) -> gold vazio; codigo rotulado pelo CONTEUDO (resumo) e, quando o resumo esta errado, pelo LABEL do Moodle.
Uso: gera_gold_subunidade.py [--write]"""
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402

PROV = "proposto-claude 2026-09-05 (aguarda aprovacao do user)"
COLS = ["entry_id", "title", "category", "posting_date", "unit_slug", "card", "evidencia", "pred_subunit", "gold_subunit",
        "gold_subunits_extra", "gold_fonte", "scorable", "notas"]

# (gold, extras, fonte, scorable, nota)
NO = "no"
CG = {
    "intro": ("conceitos", "areas-relacionadas", "conteudo", "yes", "pagina 'Origens' mas o texto e a classificacao de CG passiva/interativa (Rogers e Adams) = conceitos"),
    "origensdacomputacaografica": ("origens", "", "conteudo", "yes", "Whirlwind, SAGE, Sketchpad, mouse"),
    "segmentacaopptx": ("segmentacao", "", "conteudo", "yes", ""),
    "segmentacaodetexturas": ("segmentacao", "", "conteudo", "yes", "co-ocorrencia de niveis de cinza para segmentar texturas"),
    "morfologiamatematicapptx": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u01; morfologia matematica e processamento de imagens (u03); taxonomia u03 sem subtopico proprio (filtros ou segmentacao)"),
    "csg": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u06; CSG = u07/geometria-solida-construtiva-csg"),
    "modelagem3d": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u06; modelagem de solidos = u07/formas-de-representacao"),
    "atividade": ("conceito-de-camera-sintetica", "projecoes", "conteudo", "yes", "tarefas: coordenadas do observador e do alvo, mover o observador"),
    "basico3d-py": ("conceito-de-camera-sintetica", "pipeline-de-visualizacao-3d;projecoes", "conteudo", "yes", "resumo: cena 3D, gluLookAt, iluminacao, ModelView"),
    "opengl3d": ("conceito-de-camera-sintetica", "projecoes;pipeline-de-visualizacao-3d", "conteudo", "yes", "'funcoes de projecao e manipulacao da camera em OpenGL'"),
    "opengl3dcpp-vdi": ("conceito-de-camera-sintetica", "projecoes;pipeline-de-visualizacao-3d", "card", "yes", "bundle misto (2D/3D/Bezier/imagens); rotulado pelo LABEL 'Projeto VDI de OpenGL 3D' + card 13 — RULING pendente: apoio misto rotula pelo card?"),
    "opengl3dcpp": ("conceito-de-camera-sintetica", "projecoes;pipeline-de-visualizacao-3d", "card", "yes", "bundle misto; LABEL 'Projeto de OpenGL 3D em C++' + card 13 — RULING pendente"),
    "vis3d": ("projecoes", "paralela;perspectiva;conceito-de-camera-sintetica;a-matematica-das-projecoes-planares", "conteudo", "yes", "PROJECOES, paralela ortografica, perspectiva, observador, sistema da camera"),
    "basico3d-cpp": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u06; card 14 'Exercicios sobre Modelagem' + resumo (extrusao, Bezier) = u07/varredura ou tecnicas-de-modelagem-3d"),
    "basico3d-py-zip": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u06; modelagem por extrusao = u07/varredura"),
    "exerciciodemodelagem": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u06; CriaObjetoPorExtrusao = u07/varredura"),
    "elemoculto": ("algoritmos-de-remocao-de-elementos-ocultos", "eliminacao-de-faces-traseiras;algoritmo-do-pintor;algoritmo-z-buffer;arvores-bsp", "conteudo", "yes", "slides-roteiro da remocao de elementos ocultos (faces traseiras, z-buffer, pintor)"),
    "exemplozbuffer": ("algoritmo-z-buffer", "", "conteudo", "yes", ""),
    "iluminacao": ("modelos-de-iluminacao-luz-pontual-direcional-spot", "modelos-de-reflexao-ambiente-difusa-especular;metodos-de-sombreamento-flat-gouraud-phong", "conteudo", "yes", "pagina: modelos de iluminacao + modelos de tonalizacao"),
    "programabasico3d": ("modelos-de-reflexao-ambiente-difusa-especular", "modelos-de-iluminacao-luz-pontual-direcional-spot;projecoes", "conteudo", "yes", "codigo usado em aula (card 16): configura ambiente/difusa/especular"),
    "maptextures": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; texturas = u08/mapeamento-de-textura"),
    "exercicios": ("", "", "conteudo", "yes", "exercicios de introducao a OpenGL: ferramenta, sem subtopico na taxonomia; resposta honesta = vazio (pred 'conceitos' 1.0 e errada)"),
    "opengl-cpp": ("", "", "conteudo", "yes", "bundle de projetos OpenGL (ferramenta): sem subtopico; vazio"),
    "opengl-py": ("", "", "conteudo", "yes", "bundle de projetos OpenGL (ferramenta): sem subtopico; vazio"),
    "openglbasico": ("", "", "conteudo", "yes", "tutorial de instalacao/uso de OpenGL: ferramenta; vazio"),
    "texturas-v3": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u01 (card 2 OpenGL); texturas + iluminacao = u08/mapeamento-de-textura"),
    "exemplodemanipulacaodeimagens": ("", "", "conteudo", NO, "CONFLITO: label do Moodle 'Classe Vetor' (u02) x conteudo do .cpp = processamento de imagens (u03/filtros); computada u02 — RULING pendente"),
    "exercicio-com-animacao": ("operacoes-com-vetores", "entidades-geometricas", "conteudo", "yes", "triangulo atravessa a tela em tempo fixo = deslocamento por vetor"),
    "exercicio-com-poligonos": ("algoritmos-de-poligonos", "", "conteudo", "yes", "ponto dentro/fora do poligono"),
    "exercicio-de-animacao-foguete": ("operacoes-com-vetores", "algoritmos-de-poligonos", "conteudo", "yes", "foguete de poligonos deslocado por PosFoguete (vetor)"),
    "fundamentosmatematicos": ("entidades-geometricas", "operacoes-com-vetores", "conteudo", "yes", "pontos, vetores, retas; operacoes"),
    "matematica": ("operacoes-com-vetores", "entidades-geometricas", "conteudo", "yes", "classe Vetor 2D: translacao, escala, vetor resultante; label 'Produto Escalar'"),
    "colisao": ("algoritmos-de-deteccao-e-calculo-de-interseccao", "", "conteudo", "yes", "AABB/OOBB, envelopes"),
    "geomcomp": ("algoritmos-de-geometria-computacional", "", "conteudo", "yes", ""),
    "animacao-v2": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; animacao com translacao/rotacao = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d"),
    "exercicios-teoricos-sobre-processo-de-visualizacao-2d": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; viewport x window = u05/mapeamento-window-e-viewport"),
    "instanciamento": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; translacao/escala/rotacao = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d"),
    "mapeamento": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; janela de selecao/exibicao = u05/mapeamento-window-e-viewport"),
    "pagina-com-videos-sobre-instanciamento": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u04; instanciamento = u05/transformacoes-geometricas (conteudo capturado = listagem de codigo)"),
    "recorte": ("recorte", "", "conteudo", "yes", "Cohen-Sutherland"),
    "transformacoesgeometricas": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; transformacoes 2D hierarquicas = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d"),
    "transformacoesgl": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; transformacoes em OpenGL = u05/transformacoes-geometricas-e-coordenadas-homogeneas-2d"),
    "vis2d": ("sistema-de-coordenadas-cartesianas", "recorte", "conteudo", "yes", "introducao ao processo 2D (instanciamento, recorte, mapeamento, sistemas de referencia); alternativa u05/pipeline-de-visualizacao-2d"),
    "bezier-animacao": ("bezier-e-algoritmo-de-casteljau", "representacao-de-curvas-parametricas", "conteudo", "yes", ""),
    "bezier-cpp": ("bezier-e-algoritmo-de-casteljau", "representacao-de-curvas-parametricas", "conteudo", "yes", ""),
    "bezier-py": ("bezier-e-algoritmo-de-casteljau", "representacao-de-curvas-parametricas", "conteudo", "yes", ""),
    "bezier-python": ("bezier-e-algoritmo-de-casteljau", "representacao-de-curvas-parametricas", "conteudo", "yes", "quadraticas e cubicas; animacao"),
    "curvas": ("representacao-de-curvas-parametricas", "bezier-e-algoritmo-de-casteljau;hermite;catmull-rom;b-spline", "conteudo", "yes", "pagina geral de curvas parametricas"),
    "curvasparametricas": ("representacao-de-curvas-parametricas", "bezier-e-algoritmo-de-casteljau;hermite;catmull-rom;b-spline", "conteudo", "yes", "slides: forma parametrica x nao parametrica"),
    "exercicios-sobre-curvas": ("catmull-rom", "representacao-de-curvas-parametricas;bezier-e-algoritmo-de-casteljau", "conteudo", "yes", "1a questao: Catmull-Rom por 4 pontos"),
    "floodfill": ("segmentacao", "", "conteudo", "yes", "flood fill = crescimento de regiao; alternativa u04/preenchimento-de-poligonos (card 8 Manipulacao de Imagens)"),
    "img": ("cores-e-tipos-de-imagens", "filtros;algoritmos-de-quantizacao-e-amostragem", "conteudo", "yes", "1. Tipos de imagens (true-color...)"),
    "remocaoderuido": ("filtros", "", "conteudo", "yes", ""),
    "exercicios-de-processamento-de-imagens": ("algoritmos-de-quantizacao-e-amostragem", "cores-e-tipos-de-imagens;filtros;segmentacao", "conteudo", "yes", "1a questao: copia de imagem de 64 tons (quantizacao); lista cobre varios"),
    "introducaoprocimg": ("filtros", "introducao-e-exemplos-de-aplicacoes;cores-e-tipos-de-imagens", "conteudo", "yes", "histogramas, equalizacao, convolucao, Sobel"),
    "exercicios-de-geometria-computacional": ("algoritmos-de-geometria-computacional", "", "conteudo", "yes", "matriz de dominancia"),
    "exercicios-sobre-curvas-html": ("catmull-rom", "representacao-de-curvas-parametricas;bezier-e-algoritmo-de-casteljau", "conteudo", "yes", "duplicata html de exercicios-sobre-curvas"),
    "exercicios-teoricos-sobre-processo-de-visualizacao-2d-html": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u04; viewport x window = u05/mapeamento-window-e-viewport (duplicata html)"),
    "exerciciosfundamentosmatematicos": ("algoritmos-de-poligonos", "operacoes-com-vetores", "conteudo", "yes", "3 de 4 questoes sobre poligonos (concavidade, inclusao de ponto)"),
    "resolucao-de-prova-de-computacao-grafica-2d": ("", "", "", NO, "prova resolvida: cobre varias unidades"),
    "listadeexercicios2026-1": ("", "", "", NO, "lista para P2: iluminacao + projecao + modelagem (u06/u07/u08)"),
    "cronograma2026-2": ("", "", "", NO, "meta (cronograma)"),
    "planodeensino-4645z-04-fundamentos-de-computacao-grafica": ("", "", "", NO, "meta (plano de ensino)"),
    "videoscg-v2": ("", "", "", NO, "playlist da disciplina inteira"),
    "resolucao-de-prova-de-computacao-grafica-2d-html": ("", "", "", NO, "prova resolvida (duplicata html)"),
    "resolucao-de-prova-de-computacao-grafica-3d": ("", "", "", NO, "prova resolvida: cobre varias unidades"),
    "domina": ("algoritmos-de-geometria-computacional", "", "conteudo", "yes", "contagem geometrica / matriz de dominancia"),
    "planesweep": ("algoritmos-de-geometria-computacional", "", "conteudo", "yes", ""),
    "slab": ("algoritmos-de-geometria-computacional", "algoritmos-de-poligonos", "conteudo", "yes", "pesquisa geometrica: em qual poligono esta o ponto (slab)"),
    "exercicioduascores": ("algoritmos-de-quantizacao-e-amostragem", "cores-e-tipos-de-imagens", "conteudo", "yes", "padroes de halftone (2 cores) = quantizacao"),
    "video-sobre-origens-da-computacao-grafica-806e66": ("origens", "", "titulo", "yes", ""),
    "video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758": ("", "", "titulo", "yes", "ferramenta (OpenGL na VDI): vazio"),
    "pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9": ("entidades-geometricas", "operacoes-com-vetores", "titulo", "yes", "conteudo capturado = pagina de login do Moodle; rotulo pelo titulo"),
    "videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84": ("algoritmos-de-deteccao-e-calculo-de-interseccao", "", "titulo", "yes", "conteudo capturado = login do Moodle"),
    "pagina-com-videos-sobre-geometria-computacional-ebca9a": ("algoritmos-de-geometria-computacional", "", "titulo", "yes", "conteudo capturado = login do Moodle"),
    "pagina-com-videos-sobre-recorte-e257d3": ("recorte", "", "titulo", "yes", "conteudo capturado = login do Moodle"),
    "video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e": ("recorte", "", "titulo", "yes", ""),
    "pagina-com-videos-sobre-mapeamento-9f410e": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u04; mapeamento = u05/mapeamento-window-e-viewport"),
    "video-sobre-mapeamento-em-opengl-1dad3c": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u04; mapeamento = u05/mapeamento-window-e-viewport"),
    "pagina-com-videos-sobre-curvas-parametricas-63d902": ("representacao-de-curvas-parametricas", "", "titulo", "yes", "conteudo capturado = login do Moodle"),
    "pagina-com-videos-sobre-manipulacao-de-imagens-61ddde": ("cores-e-tipos-de-imagens", "filtros", "titulo", "yes", "mesmo assunto da pagina 'img' (tipos de imagens)"),
    "pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156": ("introducao-e-exemplos-de-aplicacoes", "filtros", "titulo", "yes", "conteudo capturado = login do Moodle"),
    "pagina-com-videos-sobre-segmentacao-de-imagens-d0627f": ("segmentacao", "", "titulo", "yes", ""),
    "pagina-com-videos-sobre-segmentacao-por-texturas-e03566": ("segmentacao", "", "titulo", "yes", ""),
    "aula-gravada-975b85": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u01; aula sobre Morfologia Matematica = u03"),
    "pagina-com-videos-sobre-morfologia-matematica-06265a": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u01; morfologia = u03"),
    "video-sobre-prechimento-de-areas-duracao-330-defae7": ("segmentacao", "", "titulo", "yes", "preenchimento de area (flood fill), como floodfill; alternativa u04/preenchimento-de-poligonos"),
    "video-sobre-prechimento-de-areas-duracao-1300-d87e5f": ("segmentacao", "", "titulo", "yes", "idem"),
    "paginas-com-videos-sobre-modelagem-geometrica-f2614a": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u06; modelagem geometrica = u07"),
    "pagina-com-videos-sobre-visualizacao-3d-35a833": ("pipeline-de-visualizacao-3d", "projecoes;conceito-de-camera-sintetica", "titulo", "yes", ""),
    "pagina-com-videos-sobre-remocao-de-elementos-ocultos-20c34a": ("algoritmos-de-remocao-de-elementos-ocultos", "", "titulo", "yes", ""),
    "pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea": ("modelos-de-iluminacao-luz-pontual-direcional-spot", "modelos-de-reflexao-ambiente-difusa-especular;metodos-de-sombreamento-flat-gouraud-phong", "titulo", "yes", ""),
    "pagina-com-videos-sobre-mapeamento-de-texturas-07bbe3": ("", "", "titulo", NO, "UNIDADE ERRADA: computada u04; texturas = u08/mapeamento-de-textura"),
}

DAFNY = "softwares-de-suporte-a-verificacao-formal-de-programas"
FR = "especificacao-de-funcoes-recursivas"
CI = "especificacao-de-conjuntos-indutivos"
PT = "provadores-de-teoremas"
MF = {
    "eth2": ("", "", "conteudo", NO, "UNIDADE: gold u02 (ruling 31/08), computada u01; subtopico seria softwares-de-suporte (Dafny)"),
    "aws-encryption-sdk": ("", "", "conteudo", NO, "UNIDADE: gold u02 (ruling 31/08), computada u01; subtopico seria softwares-de-suporte (Dafny)"),
    "archive-of-formal-proofs-355fb8": (PT, "", "conteudo", "yes", "AFP = provas em Isabelle"),
    "exerciciosformalizacaoalgoritmosrecursao3": (FR, CI, "conteudo", "yes", "arvores binarias: definicao indutiva + equacoes recursivas"),
    "formalizacaoalgoritmos-recursao2": (FR, CI, "conteudo", "yes", "listas: definicao indutiva + equacoes recursivas"),
    "exerciciosconjuntosindutivos": (CI, "", "conteudo", "yes", ""),
    "conjuntosindutivos": (CI, "", "conteudo", "yes", ""),
    "logicapredicados-semantica": ("fundamentos-de-logica-de-primeira-ordem", "", "conteudo", "yes", ""),
    "logicapredicados-sintaxe": ("fundamentos-de-logica-de-primeira-ordem", "", "conteudo", "yes", ""),
    "logicaproposicional-sintaxe": ("linguagens-de-especificacao-e-logicas", "fundamentos-de-logica-de-primeira-ordem", "conteudo", "yes", "logica proposicional: taxonomia u01 sem subtopico proprio"),
    "revisao": ("sistemas-formais", "", "conteudo", "yes", "revisao de pre-requisitos (conjuntos, relacoes, funcoes, linguagens formais); alternativa vazio (revisao sem assunto dominante)"),
    "introducao": ("abordagens-para-verificacao-formal", "exemplos-de-aplicacoes", "conteudo", "yes", "V&V, tecnicas, 'o que e um metodo formal'; Ariane/Therac/Pentium como exemplos"),
    "provasindutivas-especificacoesrecursivas": (FR, "abordagens-para-verificacao-formal", "conteudo", "yes", "provas por inducao de especificacoes recursivas: taxonomia u01 sem subtopico 'inducao'"),
    "provasindutivas-especificacoesrecursivas-arvores": (FR, "abordagens-para-verificacao-formal", "conteudo", "yes", "inducao estrutural sobre arvores"),
    "provasindutivas-especificacoesrecursivas-listas": (FR, "abordagens-para-verificacao-formal", "conteudo", "yes", "inducao estrutural sobre listas"),
    "exercicioscorrecaoinducaomatematica": (FR, "abordagens-para-verificacao-formal", "conteudo", "yes", "provas por inducao de especificacoes equacionais recursivas"),
    "exerciciosespecificacao-respostas": ("linguagens-de-especificacao-e-logicas", "", "conteudo", "yes", "especificacao formal (pre/pos de busca em array) escrita em logica; card 'Revisao - Logica e Especificacao'"),
    "exerciciosespecificacao": ("linguagens-de-especificacao-e-logicas", "", "conteudo", "yes", "idem"),
    "exerciciosformalizacaoalgoritmosrecursao2": (FR, CI, "conteudo", "yes", "listas"),
    "exerciciosisabelle2": (PT, FR, "conteudo", "yes", "provas em Isabelle"),
    "logicaproposicional-semantica": ("linguagens-de-especificacao-e-logicas", "fundamentos-de-logica-de-primeira-ordem", "conteudo", "yes", "logica proposicional: sem subtopico proprio"),
    "exerciciosformalizacaoalgoritmosrecursao-respostas": (FR, "", "conteudo", "yes", "gabarito (scanned)"),
    "formalizacaoalgoritmos-recursao": (FR, "", "conteudo", "yes", "equacoes recursivas, tipos de recursao, maquina de estados"),
    "formalizacaoalgoritmos-recursao3": (FR, CI, "conteudo", "yes", "arvores"),
    "exerciciosisabelle": (PT, FR, "conteudo", "yes", "provas em Isabelle"),
    "revisao-p1": ("", "", "", NO, "lista de revisao para P1: cobre a unidade inteira"),
    "t1-2026-1": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u02, gold u01 (material_gt); subtopico seria especificacao-de-funcoes-recursivas"),
    "t1-2026-1-thy": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u02, gold u01; subtopico seria provadores-de-teoremas"),
    "exerciciosformalizacaoalgoritmosrecursao": (FR, "", "conteudo", "yes", "parte 1"),
    "revisao-p1-gabarito": ("", "", "", NO, "gabarito da revisao para P1"),
    "arvores": (PT, FR, "conteudo", "yes", ".thy: datatype arvore + prova por inducao em Isabelle"),
    "exemplos": (PT, f"{FR};{CI}", "conteudo", "yes", ".thy: tipos indutivos, predicados, funcoes recursivas em Isabelle"),
    "intro": (PT, f"{CI};{FR}", "conteudo", "yes", ".thy: naturais, recursao primitiva, regras de inducao"),
    "listas": (PT, FR, "conteudo", "yes", ".thy: cat e associatividade"),
    "provas": (PT, FR, "conteudo", "yes", ".thy: add, propriedades indutivas, Isar"),
    "correcaoterminacao": ("correcao-parcial-e-total", "invariante-e-variante-de-laco", "conteudo", "yes", "correcao parcial/total, ordens bem-fundamentadas, terminacao"),
    "exercicioscorrecaoterminacao": ("correcao-parcial-e-total", f"invariante-e-variante-de-laco;{DAFNY}", "conteudo", "yes", "terminacao em Dafny"),
    "exerciciosformalizacaoalgoritmosinvariantes": ("invariante-e-variante-de-laco", "", "conteudo", "yes", ""),
    "formalizacaoalgoritmos-invarianteslaco": ("invariante-e-variante-de-laco", "", "conteudo", "yes", ""),
    "logicadehoare": ("logica-de-hoare", "pre-e-pos-condicoes", "conteudo", "yes", "triplas de Hoare"),
    "logicadehoare2": ("logica-de-hoare", "invariante-e-variante-de-laco;pre-e-pos-condicoes", "conteudo", "yes", "lacos enquanto, arrays"),
    "exerciciosdafny1": (DAFNY, "verificacao-de-programas;pre-e-pos-condicoes", "conteudo", "yes", "CONVENCAO proposta: listas 'Programacao e Verificacao com Dafny (X)' = softwares-de-suporte (Dafny), extra verificacao-de-programas — RULING pendente"),
    "exerciciosdafny2": (DAFNY, "verificacao-de-programas", "conteudo", "yes", "Dafny (arrays); convencao Dafny"),
    "exerciciosdafny3": (DAFNY, "verificacao-de-programas", "conteudo", "yes", "Dafny (sequences); convencao Dafny"),
    "exerciciosdafny4": (DAFNY, "verificacao-de-programas", "conteudo", "yes", "Dafny (sets, multisets); convencao Dafny"),
    "exerciciosdafny5": (DAFNY, "verificacao-de-programas;pre-e-pos-condicoes", "conteudo", "yes", "Dafny (classes, frames); convencao Dafny"),
    "verificacaomodelos": ("verificacao-de-modelos-model-checking", "fundamentos-de-logicas-temporais;especificacao-de-propriedades-para-sistemas-sequenciais-e-concorrentes;modelos-de-kripke", "conteudo", "yes", "slides gerais da unidade"),
    "exercicioslogicatemporal": ("fundamentos-de-logicas-temporais", "verificacao-de-modelos-model-checking;logica-temporal-linear;logica-temporal-ramificada", "conteudo", "yes", ""),
    "exerciciosnusmv": ("softwares-de-suporte-a-verificacao-formal-de-modelos", "verificacao-de-modelos-model-checking", "conteudo", "yes", "NuSMV/NuXMV/Fasten"),
    "classes-parte1": ("pre-e-pos-condicoes", f"{DAFNY};verificacao-de-programas", "conteudo", "yes", "classe Contador com contratos em Dafny"),
    "colecoes-arrays": (DAFNY, "verificacao-de-programas", "label", "yes", "RESUMO DE CODIGO ERRADO (repete 'datatype Cor'); rotulado pelo label 'Exemplos (Arrays)' + convencao Dafny"),
    "colecoes-conjuntos": (DAFNY, "verificacao-de-programas", "label", "yes", "resumo repetido; label 'Exemplos (Conjuntos e sequencias)'"),
    "colecoes-sequences": (DAFNY, "verificacao-de-programas", "label", "yes", "resumo repetido; label 'Exemplos (Sequencias)'"),
    "exercicios-conjuntos": (DAFNY, "verificacao-de-programas;invariante-e-variante-de-laco", "conteudo", "yes", "respostas: metodos verificados sobre arrays/sequencias (maximo, permutacao, busca)"),
    "hoare": ("logica-de-hoare", f"{DAFNY};verificacao-de-programas", "label", "yes", "label 'Exemplos (Logica de Floyd-Hoare)'; resumo amplo cita Hoare"),
    "introducao-zip": (DAFNY, "verificacao-de-programas", "conteudo", "yes", "introducao a Dafny: funcoes e predicados, transparencia"),
    "invariantes": ("invariante-e-variante-de-laco", "", "label", "yes", "RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (invariantes de laco)'"),
    "terminacao": ("correcao-parcial-e-total", "invariante-e-variante-de-laco", "label", "yes", "RESUMO DE CODIGO ERRADO ('datatype Cor'); label 'Exemplos (Terminacao)'"),
    "tiposindutivos": (DAFNY, "", "label", "yes", "tipos indutivos em Dafny (conteudo de u01 na ferramenta de u02); por card u02 = softwares-de-suporte"),
    "exemplos-zip": ("softwares-de-suporte-a-verificacao-formal-de-modelos", "verificacao-de-modelos-model-checking", "label", "yes", "RESUMO DE CODIGO ERRADO (diz Dafny); label 'Exemplos NuSMV', card 'Especificacao e Verificacao de Modelos'"),
    "exerciciosformalizacaoalgoritmosrecursao3-respostas": (FR, "", "conteudo", "yes", "equacoes recursivas III (arvores)"),
    "plano": ("", "", "", NO, "meta (plano de ensino)"),
    "t2-2026-1": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u03, gold u02 (material_gt: cita dafny e invariante); subtopico seria invariante-e-variante-de-laco"),
    "classes-parte2": ("verificacao-de-programas", f"invariante-e-variante-de-laco;pre-e-pos-condicoes;{DAFNY}", "conteudo", "yes", "BST verificada com ghost e invariantes de classe"),
    "exercicios-arrays": (DAFNY, "verificacao-de-programas;invariante-e-variante-de-laco;pre-e-pos-condicoes", "conteudo", "yes", "respostas: algoritmos em arrays verificados em Dafny"),
    "logicadehoare-exercicios-respostas": ("logica-de-hoare", "", "conteudo", "yes", ""),
}


# v2 (05/09 tarde, apos curadoria de unidade do CG): RULING pelo oraculo — bloco-06 e u04 (nome do SARC/Moodle); u04 nao tem subtopico de
# transformacoes/instanciamento (o plano os poe em u05) -> gold vazio; mapeamento window/viewport -> sistema-de-coordenadas-cartesianas.
# Blocos 08 (u03) e 15 (u07) pinados: entries voltam a ser pontuaveis. Texturas: 2 no bloco-06 por erro de BLOCO (colisao 'mapeamento') e
# texturas-v3 por conteudo (u08 sem termo no GLOSSARY.md, sem sinonimo manual possivel) ficam fora com a causa na nota.
_U04_VAZIO = ("", "", "conteudo", "yes", "u04 pelo oraculo (SARC/Moodle 'Processo de Visualizacao 2D'); o plano poe transformacoes/instanciamento em u05: u04 nao tem subtopico -> vazio")
_U04_MAP = ("sistema-de-coordenadas-cartesianas", "", "conteudo", "yes", "u04 pelo oraculo; mapeamento window/viewport = mudanca de sistema de coordenadas (plano: u05/mapeamento-window-e-viewport)")
CG.update({
    "morfologiamatematicapptx": ("segmentacao", "filtros", "conteudo", "yes", "u03 por pino (oraculo: sessao 12 entre processamento de imagens e exercicios); plano sem topico de morfologia -> segmentacao (dilatacao/erosao sobre imagens binarias)"),
    "aula-gravada-975b85": ("segmentacao", "filtros", "titulo", "yes", "u03 por pino; aula gravada de morfologia"),
    "pagina-com-videos-sobre-morfologia-matematica-06265a": ("segmentacao", "filtros", "titulo", "yes", "u03 por pino; conteudo capturado = login do Moodle"),
    "csg": ("geometria-solida-construtiva-csg", "tecnicas-de-modelagem-3d", "conteudo", "yes", "u07 por pino; CSG com poligonos"),
    "modelagem3d": ("formas-de-representacao", "tecnicas-de-modelagem-3d;representacao-aramada;superficies-limitantes", "conteudo", "yes", "u07 por pino; pagina 'Modelagem de Solidos': formas de armazenamento de solidos"),
    "basico3d-cpp": ("tecnicas-de-modelagem-3d", "varredura;bezier-e-algoritmo-de-casteljau", "conteudo", "yes", "u07 por pino; card 14 'Exercicios sobre Modelagem'; resumo: extrusao de poligonos, Bezier"),
    "basico3d-py-zip": ("tecnicas-de-modelagem-3d", "varredura", "conteudo", "yes", "u07 por pino; modelagem por extrusao"),
    "exerciciodemodelagem": ("varredura", "tecnicas-de-modelagem-3d", "conteudo", "yes", "u07 por pino; CriaObjetoPorExtrusao (extrusao = varredura)"),
    "paginas-com-videos-sobre-modelagem-geometrica-f2614a": ("tecnicas-de-modelagem-3d", "formas-de-representacao", "titulo", "yes", "u07 por pino; conteudo capturado = login do Moodle"),
    "animacao-v2": _U04_VAZIO,
    "instanciamento": _U04_VAZIO,
    "pagina-com-videos-sobre-instanciamento": _U04_VAZIO,
    "transformacoesgeometricas": _U04_VAZIO,
    "transformacoesgl": _U04_VAZIO,
    "mapeamento": _U04_MAP,
    "exercicios-teoricos-sobre-processo-de-visualizacao-2d": _U04_MAP,
    "exercicios-teoricos-sobre-processo-de-visualizacao-2d-html": _U04_MAP,
    "pagina-com-videos-sobre-mapeamento-9f410e": _U04_MAP,
    "video-sobre-mapeamento-em-opengl-1dad3c": _U04_MAP,
    "maptextures": ("", "", "conteudo", NO, "BLOCO ERRADO: bloco-06 por colisao do token 'mapeamento' com a sessao 'processo de visualizacao 2d mapeamento' (flagado; voter decide); unidade herdada u04; verdade u08/mapeamento-de-textura, secao 17 sem sessao no SARC"),
    "pagina-com-videos-sobre-mapeamento-de-texturas-07bbe3": ("", "", "titulo", NO, "BLOCO ERRADO (idem maptextures): verdade u08/mapeamento-de-textura"),
    "texturas-v3": ("", "", "conteudo", NO, "UNIDADE ERRADA: computada u01 (card 2 OpenGL, sem bloco); conteudo texturas+iluminacao = u08; GLOSSARY.md do CG para em 7.1.2 -> u08 sem termo, sem sinonimo manual possivel (divida de dados)"),
})


def build(sig, repo, dec, write):
    root = GH / repo
    ents = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    rows = []
    faltam = []
    for e in ents:
        if not _is_material(e):
            continue
        d = dec.get(e["id"])
        if d is None:
            faltam.append(e["id"])
            continue
        gold, extras, fonte, scor, nota = d
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        heads = " · ".join(h.strip("# ").strip("* ").strip() for h in re.findall(r"^#{1,4} .+$", md, flags=re.M)[:8])[:200]
        ml = e.get("moodle_label")
        ml = ml.get("text") if isinstance(ml, dict) else ml
        rows.append({
            "entry_id": e["id"], "title": ml or e.get("title") or "", "category": e.get("category") or "",
            "posting_date": str(e.get("posting_date") or "")[:10], "unit_slug": e.get("computed_unit_slug") or "",
            "card": e.get("source_section") or "", "evidencia": heads or (e.get("title") or ""),
            "pred_subunit": e.get("computed_subunit_slug") or "", "gold_subunit": gold, "gold_subunits_extra": extras,
            "gold_fonte": fonte, "scorable": scor, "notas": f"provenance={PROV}" + (f"; {nota}" if nota else ""),
        })
    extra_ids = set(dec) - {e["id"] for e in ents}
    assert not faltam and not extra_ids, (sig, faltam, extra_ids)
    n_yes = sum(r["scorable"] == "yes" for r in rows)
    ok = sum(1 for r in rows if r["scorable"] == "yes" and r["pred_subunit"] in ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))))
    prim = sum(1 for r in rows if r["scorable"] == "yes" and r["pred_subunit"] == r["gold_subunit"])
    print(f"{sig}: {len(rows)} materiais, scorable {n_yes}; motor (produto) com-extras {ok}/{n_yes} · primario {prim}/{n_yes}; unidade errada: {sum('UNIDADE' in r['notas'] for r in rows)}")
    if write:
        out = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        print("  gravado", out)
    return rows


if __name__ == "__main__":
    write = "--write" in sys.argv
    build("CG", "Computacao-Grafica-Tutor", CG, write)
    build("MF", "Metodos-Formais-Tutor", MF, write)
