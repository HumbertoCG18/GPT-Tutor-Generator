# Brief para segunda opinião (Codex astra, read-only) — Fase 2 do plano "confiança antes de acurácia", 2026-09-11 (noite)

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`.

## 1. O que aconteceu

Plano de 08/09, Fase 2 (acurácia), dimensionada com o produto em 161/251 na subunidade. Antes de a Fase 2 ser tocada, o
produto foi a 216/251 por outras alavancas: 2.4 (vocabulário LLM nos 4 cursos bloqueados), camada 3 cortada (produtor
determinístico de resumo de código), zips íntegros, regra "rótulo meta não recebe doação do LLM" (SO 8 → 15/15) e M1 (CG
55 → 57/82). A Fase 1 fechou no gate (precisão do confiante da subunidade 90,6%); sua revisão das 16:55 já está
incorporada. Hoje à noite medimos os 3 itens restantes da Fase 2 e fechamos todos SEM código de motor (commit `5971c37`).

| item | estimativa de 08/09 (base 161) | medido em 11/09 (base 216) | leitura minha (HIPÓTESE) |
|---|---|---|---|
| 2.1 propagação por similaridade | +5 | +1 no produto | simulador sem `secao-nomeia-subtopico`; 3 dos 4 ganhos o produto já acertava |
| 2.2 filtro do vocabulário | teto +2 | regra 1 (rótulo meta) +9 · regra 2 (núcleo em outra unidade) −6 | a ablação mediu "tirar o vocab inteiro", não o filtro |
| 2.3 `conflito` | "48 itens, metade da fila" | bloco (regra atual) acerta 20/22 | contagem, não medida |
| 2.4 compilador nos 4 cursos | sem estimativa | +53 junto com camada 3 e zips | veio de ler os erros reais do SO e do CG |

Conclusão que quero que você tente derrubar: **o motor esgotou o que a régua de 7 cursos consegue ver; a próxima alavanca
é dado (gold de unidade do CG, item 3.2 do plano), não código.** Dos 35 erros que sobram, 25 são do CG, que não tem gold
de unidade: 14 conflitos e 11 erros confiantes ficam cegos.

## 2. Item 2.1 — propagação por similaridade (MEDIDO, `c1-3/simula_propaga_similaridade_11-09.log`, 0 chamadas)

Regra simulada: material indeciso depois da 1ª e da 2ª passada herda a subunidade do vizinho mais similar (Jaccard, mesma
unidade) acima do piso. Régua 251 (7 cursos, FR incluído). "sim vazio & produto cheio" = onde a simulação em memória
diverge do produto: o produto aplica `secao-nomeia-subtopico` na 1ª passada e a simulação não; por isso a base ATUAL é 201
e o produto 216.
```

=== regime LIMPO (sem vocabulario nenhum) ===
  base (1a + 2a passada real): 116/251
    piso  certos  delta  ganha  perde  muda
    0.05     121     +5      7      2    31
    0.10     118     +2      2      0    16
    0.20     117     +1      1      0    10
    0.30     116     +0      0      0     8
  [SO] sim 12/15 · produto 15/15 · sim vazio & produto cheio: 3 (certos no produto: 3)
  [IA] sim 36/39 · produto 36/39 · sim vazio & produto cheio: 0 (certos no produto: 0)
      GANHA IA mlp-xoripynb -> modelos-preditivos | produto tem: -
  [ES2] sim 25/28 · produto 25/28 · sim vazio & produto cheio: 0 (certos no produto: 0)
  [TCC] sim 10/11 · produto 10/11 · sim vazio & produto cheio: 0 (certos no produto: 0)
  [MF] sim 55/58 · produto 55/58 · sim vazio & produto cheio: 0 (certos no produto: 0)
  [CG] sim 45/82 · produto 57/82 · sim vazio & produto cheio: 11 (certos no produto: 9)
      GANHA CG morfologiamatematicapptx -> filtros | produto tem: segmentacao
      GANHA CG aula-gravada-975b85 -> segmentacao | produto tem: segmentacao
      GANHA CG pagina-com-videos-sobre-morfologia-matematica-0626 -> segmentacao | produto tem: segmentacao
  [FR] sim 18/18 · produto 18/18 · sim vazio & produto cheio: 0 (certos no produto: 0)

=== regime ATUAL (produto como esta hoje) ===
  base (1a + 2a passada real): 201/251
    piso  certos  delta  ganha  perde  muda
    0.05     204     +3      4      1    12
    0.10     205     +4      4      0     7
    0.20     202     +1      1      0     4
    0.30     201     +0      0      0     2
```
Dos 4 ganhos a 0,10 no regime ATUAL, 3 são do CG e o produto já os acerta; sobra IA `mlp-xoripynb` (+1). Decisão: não vira
3ª passada.

## 3. Item 2.3 — `conflito` (MEDIDO, `c1-3/mede_conflito_unidade.{py,log}`)

`unit_block_conflict` = o texto aponta uma unidade e o bloco temporal aponta outra; o bloco vence por desenho. Contra o
gold de unidade (existe em MF, SO, IA, ES2, TCC; "(sem gold)" = curso sem gold de unidade ou material fora dele):
```
curso material                                       bloco decidiu                      texto queria                       gold                               veredito
CG    morfologiamatematicapptx                       unidade-03-processamento-de-imagen unidade-06-processo-de-visualizaca (sem gold)                         -
CG    basico3d-py-zip                                unidade-07-representacao-e-modelag unidade-06-processo-de-visualizaca (sem gold)                         -
CG    programabasico3d                               unidade-08-sintese-de-imagens-real unidade-06-processo-de-visualizaca (sem gold)                         -
CG    exercicios                                     unidade-02-fundamentos-matematicos unidade-04-processo-de-visualizaca (sem gold)                         -
CG    exercicio-de-animacao-foguete                  unidade-02-fundamentos-matematicos unidade-04-processo-de-visualizaca (sem gold)                         -
CG    matematica                                     unidade-02-fundamentos-matematicos unidade-06-processo-de-visualizaca (sem gold)                         -
CG    transformacoesgeometricas                      unidade-04-processo-de-visualizaca unidade-01-introducao-ao-processam (sem gold)                         -
CG    transformacoesgl                               unidade-04-processo-de-visualizaca unidade-02-fundamentos-matematicos (sem gold)                         -
CG    bezier-cpp                                     unidade-07-representacao-e-modelag unidade-01-introducao-ao-processam (sem gold)                         -
CG    bezier-py                                      unidade-07-representacao-e-modelag unidade-01-introducao-ao-processam (sem gold)                         -
CG    bezier-python                                  unidade-07-representacao-e-modelag unidade-02-fundamentos-matematicos (sem gold)                         -
CG    video-sobre-prechimento-de-areas-duracao-330-d unidade-03-processamento-de-imagen unidade-01-introducao-ao-processam (sem gold)                         -
CG    pagina-com-videos-sobre-morfologia-matematica- unidade-03-processamento-de-imagen unidade-06-processo-de-visualizaca (sem gold)                         -
CG    pagina-com-videos-sobre-mapeamento-de-texturas unidade-04-processo-de-visualizaca unidade-08-sintese-de-imagens-real (sem gold)                         -
ES2   microsservicos7                                unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software unidade-02-integracao-de-desenvolv bloco
ES2   roteiro5                                       unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software unidade-02-integracao-de-desenvolv bloco
ES2   roteiro6                                       unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software (sem gold)                         -
ES2   microsservicos4                                unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software unidade-02-integracao-de-desenvolv bloco
ES2   roteiro4                                       unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software unidade-02-integracao-de-desenvolv bloco
ES2   revisao-p2                                     unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software (sem gold)                         -
ES2   revisao-p2-respostas                           unidade-02-integracao-de-desenvolv unidade-01-arquitetura-de-software (sem gold)                         -
FR    entre-a-origem-e-o-destino-um-panorama-dos-blo unidade-02-nivel-de-aplicacao      unidade-01-introducao-a-redes-de-c (sem gold)                         -
IA    p2-202402                                      unidade-de-aprendizagem-03-racioci unidade-de-aprendizagem-02-solucao (sem gold)                         -
MF    exerciciosformalizacaoalgoritmosrecursao-respo unidade-01-metodos-formais         unidade-02-verificacao-de-programa unidade-01-metodos-formais         bloco
MF    t1-2026-1                                      unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    t1-2026-1-thy                                  unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    classes-parte1                                 unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    colecoes-arrays                                unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    colecoes-conjuntos                             unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    exercicios-conjuntos                           unidade-02-verificacao-de-programa unidade-03-verificacao-de-modelos  unidade-02-verificacao-de-programa bloco
MF    introducao-zip                                 unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
MF    t2-2026-1                                      unidade-03-verificacao-de-modelos  unidade-02-verificacao-de-programa (sem gold)                         -
MF    classes-parte2                                 unidade-02-verificacao-de-programa unidade-01-metodos-formais         unidade-02-verificacao-de-programa bloco
SO    laminas-cs-4244-internet-programming-sockets-p unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-03-programacao-concorrente TEXTO
SO    laminas-sockets-material-alternativo-em-pt     unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-03-programacao-concorrente TEXTO
SO    0704-exemplo-threads-em-java                   unidade-04-deadlock                unidade-03-programacao-concorrente unidade-04-deadlock                bloco
SO    3103-threads                                   unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-02-gerencia-do-processador bloco
SO    biblioteca-em-c-pthread                        unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-02-gerencia-do-processador bloco
SO    exemplo-threads-em-c-exemplo1                  unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-02-gerencia-do-processador bloco
SO    exemplo-threads-em-c-exemplo2                  unidade-02-gerencia-do-processador unidade-03-programacao-concorrente unidade-02-gerencia-do-processador bloco
SO    exercicios-p2                                  unidade-06-gerencia-de-arquivos    unidade-05-gerencia-de-memoria     unidade-06-gerencia-de-arquivos    bloco
TCC   aula-13-teorema-de-rice-pdf                    unidade-03-problemas-indecidiveis  unidade-02-turing-computabilidade  unidade-03-problemas-indecidiveis  bloco
TCC   aula-16-exemplo-de-prova-para-revisao          unidade-03-problemas-indecidiveis  unidade-01-conjuntos-enumeraveis-e (sem gold)                         -

conflitos 43 · com gold de unidade 22 · bloco (decisao atual) certo 20 · texto certo 2
```
Decisão: regra mantida. Os 2 do SO (sockets: texto u03 = gold, bloco u02) não têm sinal que os separe dos 20 em que o texto
erraria.

## 4. Item 2.2, regra 2 — corte por núcleo em outra unidade (MEDIDO, `c1-3/mede_corte_nucleo_outra_unidade.{py,log}`, 42 s)

O §2.2 do plano tinha DUAS regras: (1) recusar doação do LLM a tópico de rótulo meta — aplicada em 11/09 (`META_LABELS` em
`src/builder/core/vocabulary_compile.py:56`); (2) cortar termo doado cujo núcleo aparece no vocabulário ou nos materiais
de outra unidade — nunca medida até hoje. Termo doado = synonym do `course/.glossary_curation.llm.json`; núcleo = termo
normalizado; "aparece" = casador de frase do motor (`_matches_normalized_phrase`). Replay determ com o produtor do
produto (`c1-3/replay_subunidade.py`), 7 cursos. V1 = no vocabulário (aliases, labels, título) de outra unidade; V2 = em
título, label Moodle, headings e membros de zip de material de outra unidade (o que o LLM viu); V3 = no `.md` inteiro de
material de outra unidade; V12 = V1 ou V2. `corta N` = termos doados removidos.
```
    MF V1: gain [] loss ['hoare']
    MF V1 cortados (5): ['composicao', 'consequencia', 'formalizacao de algoritmos', 'logica de floyd hoare', 'sistemas']
    MF V2 cortados (7): ['composicao', 'consequencia', 'especificacoes equacionais', 'formalizacao de algoritmos', 'modelos', 'propriedades', 'sistemas']
    MF V3: gain [] loss ['logicapredicados-sintaxe', 'exerciciosespecificacao-respostas', 'exerciciosespecificacao', 'arvores', 'intro', 'listas', 'provas', 'terminacao']
    MF V12: gain [] loss ['hoare']
MF   base  55/58  doados  81 | V1 corta   5 ->  54 (+0 -1) | V2 corta   7 ->  55 (+0 -0) | V3 corta  26 ->  47 (+0 -8) | V12 corta   8 ->  54 (+0 -1)
    SO V1: gain [] loss ['3103-threads', 'exemplo-threads-em-c-exemplo1', 'exemplo-threads-em-c-exemplo2', 'exemplo-threads-em-c-exemplo3']
    SO V1 cortados (6): ['comunicacao entre processos', 'multithread', 'multithreading', 'processos', 'sincronizacao', 'troca de mensagens']
    SO V2: gain [] loss ['exemplo-threads-em-c-exemplo1', 'exemplo-threads-em-c-exemplo2', 'exemplo-threads-em-c-exemplo3']
    SO V2 cortados (15): ['codigo java com threads', 'exec', 'execvp', 'gerencia de arquivos', 'multithreading', 'ponte de pista unica', 'processo multithread', 'processos', 'programacao de sockets', 'semaforos', 'sincronizacao', 'socket', 'socket programming', 'sockets', 'wait']
    SO V3: gain [] loss ['exemplo-threads-em-c-exemplo1', 'exemplo-threads-em-c-exemplo2', 'exemplo-threads-em-c-exemplo3']
    SO V12: gain [] loss ['3103-threads', 'exemplo-threads-em-c-exemplo1', 'exemplo-threads-em-c-exemplo2', 'exemplo-threads-em-c-exemplo3']
SO   base  15/15  doados  99 | V1 corta   6 ->  11 (+0 -4) | V2 corta  15 ->  12 (+0 -3) | V3 corta  38 ->  12 (+0 -3) | V12 corta  18 ->  11 (+0 -4)
    IA V1 cortados (1): ['ambientes']
    IA V2 cortados (2): ['inteligencia artificial', 'selecao']
    IA V3: gain ['mlp-xoripynb'] loss ['introducao-a-ml', 'exemplo-com-k-nn', 'exemplo-2-k-nn-com-iriscsv-mais-completo', 'k-nn-para-classificacao-exemplo-cardio', 'k-nn-para-regressao-exemplo-imc', 'rede-perceptron-classificacao-planta-iris', 'mlp-classificacao-iris-atualizado', 'mlp-regressao-cardio', 'xor-backpropagation-em-python', 'aula-sobre-agrupamento-parte-1-particional', 'agrupamento-usando-k-means-exemplo-1-ipynb', 'agrupamento-usando-k-means-exemplo-2-ipynb', 'artigo-usando-agrupamento', 'agrupamento-hierarquico-exemplo-1', 'agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris']
IA   base  36/39  doados  80 | V1 corta   1 ->  36 (+0 -0) | V2 corta   2 ->  36 (+0 -0) | V3 corta  29 ->  22 (+1 -15) | V12 corta   3 ->  36 (+0 -0)
    ES2 V1 cortados (1): ['microsservicos']
    ES2 V2: gain [] loss ['roteiro1']
    ES2 V2 cortados (9): ['apigatewayapplication', 'currencyconversion', 'currencyexchange', 'currencyexchangeproxy', 'decisoes arquiteturais', 'microservicos', 'microsservicos', 'padroes', 'padroes de projeto']
    ES2 V3: gain ['microsservicos3', 'roteiro3-gateway'] loss ['roteiro1', 'kubernetes', 'roteiro2', 'roteiro4', 'roteiro5', 'roteiro6']
    ES2 V12: gain [] loss ['roteiro1']
ES2  base  25/28  doados  60 | V1 corta   1 ->  25 (+0 -0) | V2 corta   9 ->  24 (+0 -1) | V3 corta  24 ->  21 (+2 -6) | V12 corta   9 ->  24 (+0 -1)
    TCC V1 cortados (2): ['complexidade de tempo', 'np compleitude']
    TCC V2 cortados (4): ['composicao de funcoes', 'funcoes computaveis', 'rekursiva', 'robustez']
TCC  base  10/11  doados  96 | V1 corta   2 ->  10 (+0 -0) | V2 corta   4 ->  10 (+0 -0) | V3 corta  34 ->  10 (+0 -0) | V12 corta   6 ->  10 (+0 -0)
    CG V1: gain ['exercicio-com-animacao'] loss ['exercicio-de-animacao-foguete', 'slab']
    CG V1 cortados (2): ['poligonos', 'retas']
    CG V2: gain [] loss ['exercicio-de-animacao-foguete', 'slab']
    CG V2 cortados (6): ['colisao', 'poligono', 'poligonos', 'projecao', 'retas', 'triangulo']
    CG V3: gain [] loss ['exercicio-de-animacao-foguete', 'matematica', 'exercicios-de-processamento-de-imagens']
    CG V12: gain [] loss ['exercicio-de-animacao-foguete', 'slab']
CG   base  53/82  doados  79 | V1 corta   2 ->  52 (+1 -2) | V2 corta   6 ->  51 (+0 -2) | V3 corta  33 ->  50 (+0 -3) | V12 corta   6 ->  51 (+0 -2)
    FR V1 cortados (1): ['bluetooth']
    FR V2 cortados (1): ['internet']
FR   base  18/18  doados  53 | V1 corta   1 ->  18 (+0 -0) | V2 corta   1 ->  18 (+0 -0) | V3 corta   6 ->  18 (+0 -0) | V12 corta   2 ->  18 (+0 -0)
TOTAL 7 cursos (com-extras) /251: {'base': '212/251', 'V1': '206/251', 'V2': '206/251', 'V3': '180/251', 'V12': '204/251'}
```
Base do replay 212 contra 216 no produto: divergência conhecida (CG 53 × 57, TCC 10 × 11). Decisão: descartada; o que
corta é sinal (`processos`, `multithread`, `retas`), não ruído. Os falsos positivos que ela mirava (u01 do CG: OpenGL,
Morfologia) já caíram pela regra 1 + filtro de identidade.

## 5. Os 35 erros que sobram no produto (MEDIDO, `c1-3/erros_subunidade_produto_11-09.log`)

conf = `subunit_match_confidence` (margem relativa vencedor × segundo), score = `winner_score`, revisar = fila (`ok` =
confiante, fora da fila). "(vazio)" no gold = a subunidade certa é nenhuma.
```
curso material                                       tipo  categoria        predito                        gold                           conf score  revisar unidade
MF   archive-of-formal-proofs-355fb8                url   references       abordagens-para-verificacao-fo provadores-de-teoremas         0.30 16.31  ok      unidade-01-metodos-forma
MF   exemplos                                       code  codigo-professor exemplos-de-aplicacoes         provadores-de-teoremas         0.67 13.74  ok      unidade-01-metodos-forma
MF   tiposindutivos                                 zip   codigo-professor verificacao-de-programas       softwares-de-suporte-a-verific 0.86 0.12   ok      unidade-02-verificacao-d
== MF 55/58
== SO 15/15
IA   exemplo-de-programa-com-k-nn-em-java           zip   codigo-professor introducao-ao-aprendizado-de-m modelos-preditivos             0.12 12.10  duvida  unidade-de-aprendizagem-
IA   mlp-xoripynb                                   code  codigo-professor (vazio)                        modelos-preditivos             0.00 -      duvida  unidade-de-aprendizagem-
IA   aula-sobre-agrupamento-parte-2-hierarquico     pdf   material-de-aula introducao-ao-aprendizado-de-m modelos-descritivos            0.03 21.08  duvida  unidade-de-aprendizagem-
== IA 36/39
ES2  microsservicos2                                pdf   material-de-aula orientada-a-microsservicos     estudo-de-caso-arquitetura-ori 0.51 30.69  ok      unidade-01-arquitetura-d
ES2  microsservicos3                                pdf   material-de-aula estilos-e-padroes-arquiteturai estudo-de-caso-arquitetura-ori 0.19 15.05  ok      unidade-01-arquitetura-d
ES2  roteiro3-gateway                               pdf   material-de-aula cliente-servidor               estudo-de-caso-arquitetura-ori 0.27 9.32   ok      unidade-01-arquitetura-d
== ES2 25/28
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hier pdf   material-de-aula maquinas-de-turing             (vazio)                        0.43 20.54  ok      unidade-02-turing-comput
== TCC 10/11
CG   basico3d-py                                    zip   codigo-professor perspectiva                    conceito-de-camera-sintetica   0.62 8.98   ok      unidade-06-processo-de-v
CG   opengl3dcpp-vdi                                zip   codigo-professor paralela                       conceito-de-camera-sintetica   0.28 12.40  mudou   unidade-06-processo-de-v
CG   opengl3dcpp                                    zip   codigo-professor paralela                       conceito-de-camera-sintetica   0.28 12.40  mudou   unidade-06-processo-de-v
CG   programabasico3d                               code  codigo-professor metodos-de-sombreamento-flat-g modelos-de-reflexao-ambiente-d 0.67 3.45   duvida  unidade-08-sintese-de-im
CG   opengl-cpp                                     zip   codigo-professor entidades-geometricas          (vazio)                        0.36 17.79  mudou   unidade-02-fundamentos-m
CG   opengl-py                                      zip   codigo-professor entidades-geometricas          (vazio)                        0.55 17.79  mudou   unidade-02-fundamentos-m
CG   openglbasico                                   pdf   outros           entidades-geometricas          (vazio)                        0.59 7.93   mudou   unidade-02-fundamentos-m
CG   exercicio-com-animacao                         html  listas           (vazio)                        operacoes-com-vetores          0.00 -      duvida  unidade-02-fundamentos-m
CG   animacao-v2                                    zip   codigo-professor desenho-de-linhas              (vazio)                        0.23 1.35   ok      unidade-04-processo-de-v
CG   exercicios-teoricos-sobre-processo-de-visualiz html  listas           desenho-de-linhas              sistema-de-coordenadas-cartesi 0.30 1.41   ok      unidade-04-processo-de-v
CG   instanciamento                                 pdf   outros           2d-3d-mao-direita-e-mao-esquer (vazio)                        0.26 8.29   mudou   unidade-04-processo-de-v
CG   pagina-com-videos-sobre-instanciamento         html  outros           desenho-de-linhas              (vazio)                        0.91 1.35   ok      unidade-04-processo-de-v
CG   transformacoesgeometricas                      zip   codigo-professor desenho-de-linhas              (vazio)                        0.14 0.12   duvida  unidade-04-processo-de-v
CG   transformacoesgl                               html  outros           sistema-de-coordenadas-cartesi (vazio)                        0.98 0.91   duvida  unidade-04-processo-de-v
CG   bezier-python                                  zip   codigo-professor tecnicas-de-modelagem-3d       bezier-e-algoritmo-de-castelja 0.28 15.12  duvida  unidade-07-representacao
CG   exercicios-sobre-curvas                        html  listas           hermite                        catmull-rom                    0.13 4.92   mudou   unidade-07-representacao
CG   exercicios-sobre-curvas-html                   html  listas           hermite                        catmull-rom                    0.13 4.92   mudou   unidade-07-representacao
CG   exercicios-teoricos-sobre-processo-de-visualiz html  listas           desenho-de-linhas              sistema-de-coordenadas-cartesi 0.30 1.41   ok      unidade-04-processo-de-v
CG   pagina-com-videos-sobre-fundamentos-matematico html  references       algoritmos-de-poligonos        entidades-geometricas          0.42 18.93  ok      unidade-02-fundamentos-m
CG   pagina-com-videos-sobre-mapeamento-9f410e      html  references       (vazio)                        sistema-de-coordenadas-cartesi 0.00 -      duvida  unidade-04-processo-de-v
CG   video-sobre-mapeamento-em-opengl-1dad3c        url   references       2d-3d-mao-direita-e-mao-esquer sistema-de-coordenadas-cartesi 0.86 0.14   ok      unidade-04-processo-de-v
CG   pagina-com-videos-sobre-curvas-parametricas-63 html  references       hermite                        representacao-de-curvas-parame 0.13 4.84   ok      unidade-07-representacao
CG   pagina-com-videos-sobre-manipulacao-de-imagens html  references       segmentacao                    cores-e-tipos-de-imagens       0.77 4.46   ok      unidade-03-processamento
CG   paginas-com-videos-sobre-modelagem-geometrica- html  references       geometria-solida-construtiva-c tecnicas-de-modelagem-3d       0.33 8.58   ok      unidade-07-representacao
CG   pagina-com-videos-sobre-visualizacao-3d-35a833 html  references       paralela                       pipeline-de-visualizacao-3d    0.28 12.40  ok      unidade-06-processo-de-v
== CG 57/82
== FR 18/18
TOTAL [216, 251]
```

## 6. Perguntas, em ordem

1. **Método.** Alguma das três medições está mal desenhada? Em especial: (a) 2.1 medido num simulador cuja base (201) não
   é o produto (216); (b) 2.3 só nos 22 conflitos com gold, com 14 do CG cegos; (c) 2.2 regra 2: há variante que eu não
   testei e que teria chance (cortar só termo de 1 token; só termo sem token específico do curso; só quando aparece em
   ≥ 2 outras unidades; só quando aparece como TÍTULO de material de outra unidade)? Diga qual e por que escaparia das
   perdas listadas (SO threads, CG retas, MF hoare).
2. **Os 10 erros dos 6 cursos com gold de unidade.** Há padrão que eu não nomeei e que vira regra de motor com ganho ≥ 3
   em 251, sem gold como insumo? Os 3 do ES2 (vizinho semântico, "estudo de caso" × tópico geral) e os 3 do IA (na fila,
   conf ≤ 0,12) já foram vistos na Fase 1.
3. **Os 25 do CG.** Sem gold de unidade, o que dá para diagnosticar? Hipótese minha: `opengl-cpp`/`opengl-py`/
   `openglbasico` em u02 (fundamentos matemáticos) com gold vazio e `entidades-geometricas` predito são erro de UNIDADE
   (ferramenta OpenGL sem subtópico; "OpenGL" era doação a rótulo meta de u01), não de subunidade; `hermite` × `catmull-rom`
   são vizinhos dentro do tópico de curvas; os 4 `paralela`/`perspectiva` × `conceito-de-camera-sintetica` são zips de u06
   em que o resumo determinístico vê projeção e não câmera. Quais desses viram regra sem gold, quais só o gold resolve?
4. **Desenho do 3.2.** Vou montar `docs/reports/material_gt_CG.csv` no formato dos 5 cursos (`gold_units` por material,
   `|` = qualquer uma vale, vazio = nenhuma) para o usuário rotular. Escopo certo é 93 materiais, ou os 39 (25 erros + 14
   conflitos) primeiro? O que mais a planilha deve capturar para destravar (abster-se, meta-material, "unidade nenhuma")?
5. **Risco.** O que nesta noite pode estar errado: replay 212 × produto 216; conflito medido só onde há gold; a leitura
   "estimativa em proxy" da tabela do §1; a conclusão "próxima alavanca é dado".
