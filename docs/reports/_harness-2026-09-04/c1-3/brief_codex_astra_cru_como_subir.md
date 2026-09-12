# Brief 3 para o astra (read-only): COMO AUMENTAR O NUMERO DO CRU — 2026-09-12, noite

Pergunta literal do usuario: **"como podemos aumentar o numero do cru? Eu imagino que quanto menos erros confiantes,
melhor."** Este brief e a terceira rodada de hoje. O v1 (manha) mediu a partida; o v2 (tarde) trouxe o contexto do
produto e a regua congelada, e voce mudou o enquadramento. Agora o que voce mandou medir esta medido, e o quadro e pior
do que qualquer numero anterior mostrava.

Regras de sempre: MEDIDO x HIPOTESE, evidencia com arquivo:linha, diga quando o dado nao sustenta a pergunta. Voce esta
read-only; nao rode o motor.

---

## 1. O QUE MUDOU DESDE O SEU v2 (tudo MEDIDO hoje a tarde)

Voce apontou tres coisas; as tres foram feitas e duas mudaram o numero:

1. **"`calibra_fila_como_regua` le o manifest do PRODUTO: a precisao do confiante do CRU nunca foi medida."**
   Medida agora (`c1-3/calibra_fila_cru_12-09.{py,log}`), e e o achado central deste brief — secao 2.
2. **"O `--limpo` nao limpava o LLM."** Confirmado: `--limpo` so tirava o sidecar MANUAL, e **501 dos 841 aliases dos 6
   cursos (60%) sao de origem LLM** e sobreviviam. Modo `--cru` novo. **Mas o efeito e o INVERSO do que supusemos: o teto
   SOBE de 61% para 64%** quando os aliases do LLM saem — `nomeia()` exige candidato unico, entao alias a mais vira
   empate e o detector abstem. Seu corolario estava certo: "NENHUMA" mede ambiguidade tanto quanto ausencia.
3. **"Ainda ha 3 regressoes inversas."** Confirmado (ES2 `microsservicos2`, ES2 `microsservicos3`, CG
   `pagina-com-videos-sobre-manipulacao-de-imagens-61ddde`): o vocab LLM vale **+77 liquidos, nao +80**.

O usuario tambem decidiu, no Gate 1: a metrica que ordena a frente passa a ser a **precisao ACEITA do confiante, com
cobertura e tamanho da fila**; e a regua de unidade passou a aceitar CONJUNTO nos transversais adjudicados (205/212 =
96,7% -> 209/216 = 96,8%).

## 2. O NUMERO CENTRAL: a precisao do confiante no regime cru (MEDIDO, `c1-3/calibra_fila_cru_12-09.log`)

```
A PRECISAO DO CONFIANTE, POR REGIME (base 251; 'confiante' = o motor NAO poe na fila)
regime        n  confiante  cobertura   ACEITO do confiante   PRIMARIO do confiante  fila   recall da fila   alarme falso
produto     251        193     76.9%    178/193    92.2%     154/193     79.8%    58   12/27     44%   46/58    79%
cru         251        190     75.7%    113/190    59.5%      83/190     43.7%    61   27/104    26%   34/61    56%
so_codigo   251        183     72.9%     93/183    50.8%      70/183     38.3%    68   48/138    35%   20/68    29%

```

Lido em uma linha: **sem o vocabulario do LLM o motor nao sabe que esta inseguro.** A cobertura quase nao muda
(75,7% no cru contra 76,9% no produto) — o que o vocab compra nao e decisao a mais, e decisao CERTA, e com ela a
capacidade de abster. Os erros confiantes vao de 15 para 77.

**A metrica que nao da para enganar.** O usuario escreveu "quanto menos erros confiantes, melhor", e eu respondi a ele
que isso sozinho e trivialmente satisfeito abstendo de tudo (motor que joga os 251 na fila tem zero erro confiante e e
inutil). Entao proponho, e quero seu veredito, a metrica combinada **ENTREGA CONFIAVEL = confiantes CERTOS / 251**:
material entregue certo e sem pedir revisao. Nao infla abstendo (abster tira do numerador) nem chutando (erro nao conta).

| regime | entrega confiavel | precisao do confiante | cobertura | erro confiante (% do acervo) |
|---|---|---|---|---|
| produto | **178/251 = 70,9%** | 92,2% | 76,9% | 15 = 6,0% |
| **cru** | **113/251 = 45,0%** | 59,5% | 75,7% | **77 = 30,7%** |
| so codigo de outline | 93/251 = 37,1% | 50,8% | 72,9% | 90 = 35,9% |

Por curso, o aceito do confiante no cru: **IA 5/39 = 13%** · FR 7/17 = 41% · ES2 13/19 = 68% · SO 8/11 = 73% ·
MF 36/48 = 75% · CG 36/46 = 78% · TCC 8/10 = 80%.

## 3. OS 77 ERROS CONFIANTES DO CRU, UM A UM (MEDIDO, `c1-3/lista_erros_confiantes_cru_12-09.{py,log,csv}`)

Recorte por curso e por origem da decisao:

```
curso    n  erro confiante  produto acerta  produto erra tb  na 1a passada
MF      58              12               9                3             10
SO      15               3               3                0              2
IA      39              34              31                3             22
ES2     28               6               6                0              5
TCC     11               2               1                1              1
CG      82              10               3                7              7
FR      18              10              10                0              6
```

Distribuicao que importa:
- **63 dos 77 o PRODUTO acerta** (o vocab LLM resolve) e **14 o produto tambem erra**.
- **53 foram decididos na 1a passada; 24 na 2a** (19 `propagado-headings`, 5 `rotulo-decomposto`).
- 3 tem predicao VAZIA e mesmo assim ficam fora da fila.
- **Colapso por destino:** IA manda **34** para `introducao-ao-aprendizado-de-maquina`; FR manda 6 para
  `paradigmas-clienteservidor-e-p2p`; MF manda 5 para `abordagens-para-verificacao-formal`. Ou seja, quase metade dos
  erros confiantes do cru inteiro e UM curso indo para UM destino.

A lista (conf = confianca gravada; score = `winner_score`; prod = o produto acerta?):

```
curso material                                           GOLD (primario | extras)                                   CRU (errado, confiante)                      conf   score passada                prod
MF    archive-of-formal-proofs-355fb8                    provadores-de-teoremas                                     abordagens-para-verificacao-formal          0.276   16.49 2a:propagado-headings  ERRA
MF    logicapredicados-semantica                         fundamentos-de-logica-de-primeira-ordem                    especificacao-de-funcoes-recursivas         0.895    1.20 1a                     ok
MF    logicaproposicional-sintaxe                        linguagens-de-especificacao-e-logicas | fundamentos-de-logica-de-primeira-ordem especificacao-de-funcoes-recursivas         0.862    0.12 1a                     ok
MF    revisao                                            sistemas-formais                                           especificacao-de-conjuntos-indutivos        0.837    8.29 1a                     ok
MF    exerciciosespecificacao-respostas                  linguagens-de-especificacao-e-logicas                      especificacao-de-funcoes-recursivas         0.624    1.12 1a                     ok
MF    arvores                                            provadores-de-teoremas | especificacao-de-funcoes-recursivas abordagens-para-verificacao-formal          0.862    0.91 1a                     ok
MF    exemplos                                           provadores-de-teoremas | especificacao-de-funcoes-recursivas;especificacao-de-conjuntos-indutivos exemplos-de-aplicacoes                      0.989   11.09 1a                     ERRA
MF    intro                                              provadores-de-teoremas | especificacao-de-conjuntos-indutivos;especificacao-de-funcoes-recursivas abordagens-para-verificacao-formal          0.677    2.90 2a:propagado-headings  ok
MF    listas                                             provadores-de-teoremas | especificacao-de-funcoes-recursivas abordagens-para-verificacao-formal          0.862    0.91 1a                     ok
MF    provas                                             provadores-de-teoremas | especificacao-de-funcoes-recursivas abordagens-para-verificacao-formal          0.862    0.91 1a                     ok
MF    hoare                                              logica-de-hoare | softwares-de-suporte-a-verificacao-formal-de-programas;verificacao-de-programas correcao-parcial-e-total                    0.964    3.49 1a                     ok
MF    tiposindutivos                                     softwares-de-suporte-a-verificacao-formal-de-programas     verificacao-de-programas                    0.862    0.12 1a                     ERRA
SO    1903-estruturas-de-controle                        conceitos-basicos                                          escalonamento                               0.946    2.00 1a                     ok
SO    exercicios                                         algoritmos-de-escalonamento                                (vazio)                                     0.000       0 1a                     ok
SO    exemplo-threads-em-c-exemplo3                      conceitos-basicos                                          escalonamento                               1.000   11.09 2a:propagado-headings  ok
IA    algoritmo-de-classificacao-k-nn                    modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.917    1.30 1a                     ok
IA    exemplo-com-k-nn                                   modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    exemplo-2-k-nn-com-iriscsv-mais-completo           modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    exemplo-de-programa-com-k-nn-em-java               modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   11.92 1a                     ERRA
IA    artigo-usando-k-nn-em-texto                        modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.968   32.27 2a:propagado-headings  ok
IA    k-nn-para-classificacao-exemplo-cardio             modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    k-nn-para-regressao-exemplo-imc                    modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    introducao-a-redes-neurais                         modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.987   68.51 2a:propagado-headings  ok
IA    rede-perceptron                                    modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.908    1.17 1a                     ok
IA    rede-perceptron-classificacao-de-cliente           modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   31.16 2a:propagado-headings  ok
IA    rede-perceptron-classificacao-planta-iris          modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    rede-perceptron-exemplo-atualizado                 modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.881    0.91 1a                     ok
IA    rede-perceptron-or-em-python                       modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   31.16 2a:propagado-headings  ok
IA    rede-perceptron-reconhecendo-letras                modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   34.53 2a:propagado-headings  ok
IA    exercicio-2-solucao-com-rede-perceptron-atualizado modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   50.29 2a:propagado-headings  ok
IA    mlp                                                modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.981   48.73 2a:propagado-headings  ok
IA    mlp-xoripynb                                       modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000   21.87 2a:propagado-headings  ERRA
IA    mlp-classificacao-iris-atualizado                  modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.881    0.91 1a                     ok
IA    mlp-regressao-cardio                               modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.11 1a                     ok
IA    rede-perceptron-e-equacao-de-reta                  modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        1.000    0.91 1a                     ok
IA    xor-backpropagation-em-python                      modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.995   22.41 2a:propagado-headings  ok
IA    mlp-classificacao-inadimplencia-normalizacao-e-gridsearchcv modelos-preditivos | metricas-de-avaliacao                 introducao-ao-aprendizado-de-maquina        0.997   42.55 2a:propagado-headings  ok
IA    como-analisar-resultados-acc-pr-re-e-f1            metricas-de-avaliacao                                      introducao-ao-aprendizado-de-maquina        0.897    8.79 1a                     ok
IA    arvores-de-decisao                                 modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.988    8.97 1a                     ok
IA    exemplo-1-arvores-de-decisao-classificacao-planta-iris modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.908    1.17 1a                     ok
IA    exemplo-2-arvores-de-decisao-regressao-diabetes    modelos-preditivos                                         introducao-ao-aprendizado-de-maquina        0.908    1.17 1a                     ok
IA    aula-sobre-agrupamento-parte-1-particional         modelos-descritivos | paradigmas-de-aprendizado            introducao-ao-aprendizado-de-maquina        0.991  104.06 2a:propagado-headings  ok
IA    agrupamento-usando-k-means-exemplo-1-ipynb         modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.924    1.43 1a                     ok
IA    agrupamento-usando-k-means-exemplo-2-ipynb         modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.988    8.79 1a                     ok
IA    artigo-usando-agrupamento                          modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.967   31.09 2a:propagado-headings  ok
IA    survey-on-clustering                               modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        1.000    0.91 1a                     ok
IA    aula-sobre-agrupamento-parte-2-hierarquico         modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.957    2.52 1a                     ERRA
IA    agrupamento-hierarquico-exemplo-1                  modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.988    8.97 1a                     ok
IA    agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris modelos-descritivos                                        introducao-ao-aprendizado-de-maquina        0.993   15.77 1a                     ok
ES2   revisaoarquiteturapadroes                          conceito-de-arquitetura-de-software | estilos-e-padroes-arquiteturais (vazio)                                     0.000    4.84 1a                     ok
ES2   microsservicos                                     orientada-a-microsservicos                                 estilos-e-padroes-arquiteturais             0.270    2.96 2a:rotulo-decomposto   ok
ES2   devops                                             conceito-de-devops | gerenciamento-da-configuracao         integracao-continua-ci                      0.869   10.14 1a                     ok
ES2   roteiro2-nameserver                                estudo-de-caso-arquitetura-orientada-a-microsservicos      cliente-servidor                            0.330    1.35 1a                     ok
ES2   microsservicos6                                    estudo-de-caso-integracao-e-implantacao-de-microsservicos  gerenciamento-da-configuracao               1.000    1.32 1a                     ok
ES2   roteiro8-autenticacao-autorizacao                  estudo-de-caso-integracao-e-implantacao-de-microsservicos  gerenciamento-da-configuracao               1.000    0.11 1a                     ok
TCC   aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos (vazio)                                                    maquinas-de-turing                          0.909   14.28 1a                     ERRA
TCC   aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf linguagens-reconheciveis-e-decidiveis | maquinas-de-turing-universais maquinas-de-turing                          0.589   25.73 2a:propagado-headings  ok
CG    basico3d-py                                        conceito-de-camera-sintetica | pipeline-de-visualizacao-3d;projecoes perspectiva                                 0.978    4.84 1a                     ERRA
CG    programabasico3d                                   modelos-de-reflexao-ambiente-difusa-especular | modelos-de-iluminacao-luz-pontual-direcional-spot;projecoes metodos-de-sombreamento-flat-gouraud-phong  0.666    3.45 2a:rotulo-decomposto   ERRA
CG    exercicios-teoricos-sobre-processo-de-visualizacao-2d sistema-de-coordenadas-cartesianas                         desenho-de-linhas                           0.887    1.41 1a                     ERRA
CG    pagina-com-videos-sobre-instanciamento             (vazio)                                                    desenho-de-linhas                           0.986    1.35 1a                     ERRA
CG    introducaoprocimg                                  filtros | introducao-e-exemplos-de-aplicacoes;cores-e-tipos-de-imagens segmentacao                                 0.120   10.46 1a                     ok
CG    exercicios-teoricos-sobre-processo-de-visualizacao-2d-html sistema-de-coordenadas-cartesianas                         desenho-de-linhas                           0.887    1.41 1a                     ERRA
CG    pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9 entidades-geometricas | operacoes-com-vetores              algoritmos-de-poligonos                     0.722    0.44 1a                     ERRA
CG    videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84 algoritmos-de-deteccao-e-calculo-de-interseccao            (vazio)                                     0.000       0 1a                     ok
CG    pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156 introducao-e-exemplos-de-aplicacoes | filtros              segmentacao                                 0.387    7.84 2a:propagado-headings  ok
CG    paginas-com-videos-sobre-modelagem-geometrica-f2614a tecnicas-de-modelagem-3d | formas-de-representacao         geometria-solida-construtiva-csg            0.326    8.58 2a:rotulo-decomposto   ERRA
FR    01-protocolos-de-rede                              conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | conceitos-de-redes-de-computadores-e-internet modelos-osi-e-tcpip                         1.000   12.10 1a                     ok
FR    03-tipos-de-redes                                  conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | classificacao-e-topologias-de-redes-de-computadores modelos-osi-e-tcpip                         0.816    7.06 1a                     ok
FR    04-camada-de-aplicacao                             funcoes-e-caracteristicas-do-nivel-de-aplicacao | paradigmas-clienteservidor-e-p2p protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap  0.673    7.16 2a:rotulo-decomposto   ok
FR    04-protocolo-http                                  protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap paradigmas-clienteservidor-e-p2p            0.721    4.64 2a:propagado-headings  ok
FR    05-protocolo-dns                                   protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap  0.800    5.18 2a:rotulo-decomposto   ok
FR    unidade2-exercicios-http                           protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap paradigmas-clienteservidor-e-p2p            0.713    4.72 2a:propagado-headings  ok
FR    udp-example-c                                      implementacao-de-sockets | protocolo-udp                   paradigmas-clienteservidor-e-p2p            0.981    0.91 1a                     ok
FR    udp-example-java                                   implementacao-de-sockets | protocolo-udp                   paradigmas-clienteservidor-e-p2p            0.981    0.91 1a                     ok
FR    tcp-chat-c                                         implementacao-de-sockets | protocolo-tcp                   paradigmas-clienteservidor-e-p2p            0.981    0.91 1a                     ok
FR    tcp-example                                        implementacao-de-sockets | protocolo-tcp                   paradigmas-clienteservidor-e-p2p            0.981    0.91 1a                     ok
```

### 3.1 Os 14 em que o vocabulario do LLM TAMBEM nao resolve

```
MF   archive-of-formal-proofs-355fb8                  gold provadores-de-teoremas                               cru abordagens-para-verificacao-formal     produto abordagens-para-verificacao-formal
MF   exemplos                                         gold provadores-de-teoremas | especificacao-de-funcoes-recursivas;especificacao-de-conjuntos-indutivos cru exemplos-de-aplicacoes                 produto exemplos-de-aplicacoes
MF   tiposindutivos                                   gold softwares-de-suporte-a-verificacao-formal-de-programas cru verificacao-de-programas               produto verificacao-de-programas
IA   exemplo-de-programa-com-k-nn-em-java             gold modelos-preditivos                                   cru introducao-ao-aprendizado-de-maquina   produto introducao-ao-aprendizado-de-maquina
IA   mlp-xoripynb                                     gold modelos-preditivos                                   cru introducao-ao-aprendizado-de-maquina   produto (vazio)
IA   aula-sobre-agrupamento-parte-2-hierarquico       gold modelos-descritivos                                  cru introducao-ao-aprendizado-de-maquina   produto introducao-ao-aprendizado-de-maquina
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos gold (vazio)                                              cru maquinas-de-turing                     produto maquinas-de-turing
CG   basico3d-py                                      gold conceito-de-camera-sintetica | pipeline-de-visualizacao-3d;projecoes cru perspectiva                            produto perspectiva
CG   programabasico3d                                 gold modelos-de-reflexao-ambiente-difusa-especular | modelos-de-iluminacao-luz-pontual-direcional-spot;projecoes cru metodos-de-sombreamento-flat-gouraud-phong produto metodos-de-sombreamento-flat-gouraud-phong
CG   exercicios-teoricos-sobre-processo-de-visualizacao-2d gold sistema-de-coordenadas-cartesianas                   cru desenho-de-linhas                      produto desenho-de-linhas
CG   pagina-com-videos-sobre-instanciamento           gold (vazio)                                              cru desenho-de-linhas                      produto desenho-de-linhas
CG   exercicios-teoricos-sobre-processo-de-visualizacao-2d-html gold sistema-de-coordenadas-cartesianas                   cru desenho-de-linhas                      produto desenho-de-linhas
CG   pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9 gold entidades-geometricas | operacoes-com-vetores        cru algoritmos-de-poligonos                produto algoritmos-de-poligonos
CG   paginas-com-videos-sobre-modelagem-geometrica-f2614a gold tecnicas-de-modelagem-3d | formas-de-representacao   cru geometria-solida-construtiva-csg       produto geometria-solida-construtiva-csg
```

## 4. O QUE UMA INVESTIGACAO PARALELA MEDIU HOJE (3 frentes, cada uma com um refutador independente)

Três frentes medidas em paralelo hoje à noite, cada uma com um refutador independente que reproduziu os números com as
próprias mãos. Tudo com o replay in-memory, `escopo="produto"`, base 251, 0 chamadas. Duas frentes sustentaram; uma teve
a recomendação principal REFUTADA e substituída por uma alternativa mais barata.

### 4.1 Por que o IA colapsa (REFUTADOR: sustenta, `refutado=false`)

**A causa é ausência de vocabulário, não desempate — e há um auto-envenenamento da taxonomia no meio.**

1. **Nos 34 erros do IA o tópico do gold tem score ZERO em 30.** Em 25 desses o vencedor tem score > 0 (o motor escolhe
   errado com evidência mínima); em 5 TODOS os tópicos da unidade dão 0 (o motor não tinha nada). Só 4 casos têm gold com
   score > 0, e em 3 ele perde por margem enorme (0,108 × 8,966). **A unidade está certa em 39/39** — o erro é só de
   subunidade. Isto é a diferença entre "escolheu errado" e "não tinha como escolher certo".
2. **Contrafactual que separa as hipóteses (medido, base 39):** cru = 5 aceito. Matar o rótulo-aspirador (tirar os 5
   aliases doados ao tópico vencedor) = **7** (+2). Devolver só o vocabulário de domínio dos 3 tópicos do gold = **36**
   (+31), idêntico ao produto. **A alavanca é vocabulário; o aspirador é amplificador, não causa.**
3. **AUTO-ENVENENAMENTO (achado novo).** `src/builder/extraction/content_taxonomy.py:603-646` doa HEADINGS dos próprios
   materiais como alias de tópico. No IA, 5 headings de slides ("Aprendizado Supervisionado Parte 2", "Aula 29 —
   Aprendizagem de Máquina: Medidas de Avaliação") foram arquivados no tópico `introducao-ao-aprendizado-de-maquina`.
   **Esses aliases NÃO vêm do LLM nem da curadoria manual — vêm do próprio material — então sobrevivem intactos ao corte
   do regime cru.** Resultado concreto: `arvores-de-decisao` pontua 8,97 no tópico errado com 4 exact_hits, todos da
   frase que é o H2 do próprio arquivo; o gold fica com 0,108.
4. **Assimetria de vocabulário na unidade:** no cru, o tópico vencedor fica com 12 tokens próprios contra 3/3/3/4 dos
   quatro concorrentes — e os tokens que ele detém são justamente os roubados deles ("agrupamento", "means", "medidas",
   "avaliacao", "supervisionado").
5. **A confiança é margem RELATIVA sobre o próprio score, sem piso absoluto** (`file_map.py:203`
   `rel_margin = margin / max(winner_score, 1e-6)`): `exemplo-com-k-nn` vence com 0,108 contra 0,000 e sai com
   **confiança 1,000**. Score baixo e confiança alta são grandezas independentes — 14 dos 34 erros saem com confiança 1,000.
6. **A 2ª passada APAGA a abstenção da 1ª.** `resolver_apply.py:339` sobrescreve `subunit_match_reasons`, e
   `revisar._subunidade_em_duvida` só reconhece as strings "ambiguous"/"empate-exato". Medido: **7 dos 39 materiais do IA
   abstiveram na 1ª passada** (5 por `winner_score=0`, 2 por empate exato) e **terminaram como decisão confiante no
   destino errado, sem deixar rastro na fila**. Fila do IA no cru: 0 de 39.
7. **O plano do IA realmente não numera** (verificado no texto do professor): os 0 aliases de código não são falha de
   captura. Corrige uma premissa minha.

### 4.2 Existe sinal de fragilidade disponível? (REFUTADOR: `refutado=true` na recomendação principal)

**O que FECHOU por medição** — não gastar Gate 1 com isto:
- **margem absoluta entre 1º e 2º**: Spearman **0,948** com o próprio `winner_score`. É o piso global com outro nome —
  5ª refutação da mesma ideia.
- **razão s2/s1**: invertida no cru (35% × 41% de erro). Ressalva do refutador: no produto ela separa 4× na direção
  certa (20% × 5%), então é regra de abstenção ruim, não sinal nulo.
- **cobertura de tokens** (50/50 exato), **riqueza de alias do vencedor**, **"sem competição" (n_pos==1)**: não separam.

**O que ABRE DE GRAÇA (sobreviveu à refutação intacto, e é o único item que fecha sozinho):**
**alinhar a fila com as abstenções que o matcher JÁ emite.** `auto_map_entry_subtopic` abstém em `winner_score <= 0`
("sem-sinal") e em "revisao-sem-assunto-dominante", mas `revisar._subunidade_em_duvida` só casa "ambiguous" e
"empate-exato". Resultado: **3 materiais no cru (9 no só-código, 0 no produto) são entregues com slug VAZIO e sem
aviso**. Custo zero, sem limiar, sem gold, sem risco para o produto.

**O que foi REFUTADO (e a alternativa que o refutador mediu):** a proposta de abster quando o vencedor foi decidido por
`markdown_lead`/`markdown_text` SEM casar frase (evita 21 erros por 4 acertos no cru; no produto evita 4 e perde 2).
Três furos: (a) "o motor já calcula e joga fora" é falso no ramo em que a regra atua — ali o score é cego a campo
(`index.py:1908-1913`), então implementar custa bookkeeping novo; (b) **sob a régua PRIMÁRIO a regra PERDE para
`exact_hits == 0` puro**, que o scorer já conta (`index.py:1815/1848`): cru +24 (43,7% → 50,0%) contra +17 da proposta,
produto +1 com precisão maior; (c) o "+2 no produto" é **+1 documento distinto** — dois dos quatro "erros evitados" são o
mesmo material com dois `entry_id`, e a regra foi escolhida varrendo ~20 candidatos no mesmo 251, sem holdout.
**A escolha da régua inverte a conclusão:** por aceito a proposta ganha, por primário a alternativa barata ganha.

**O teto da abstenção, medido:** mesmo a união mais agressiva que não quebra o produto leva o aceito do confiante de
59,5% para **67,3%**, com a cobertura caindo de 75,7% para **64,5%**. **A abstenção não conserta o cru — ela só torna a
falta de vocabulário visível.**

### 4.3 Quanto a 2ª passada pesa no cru (REFUTADOR: sustenta, `refutado=false`)

| regime CRU | aceito | primário | cobertura | aceito do confiante | erros confiantes |
|---|---|---|---|---|---|
| baseline (como está) | 147 = 58,6% | 105 = 41,8% | 190 = 75,7% | **113/190 = 59,5%** | 77 |
| sem a 2ª passada | 136 = 54,2% | 97 = 38,6% | 181 = 72,1% | 107/181 = 59,1% | 74 |
| só propagação por headings | 139 | 97 | 187 | 105/187 = 56,1% | **82** |
| só partes de rótulo | 140 | 100 | 186 | **112/186 = 60,2%** | 74 |
| só regra de título | 137 | 98 | 181 | 108/181 = 59,7% | 73 |
| só regra de seção | 141 | 101 | 184 | 108/184 = 58,7% | 76 |

**No cru a 2ª passada é quase neutra na métrica que ordena** (59,1% → 59,5%, +0,4 pp) e custa 3 erros confiantes, embora
compre +11 aceito bruto e +9 de cobertura. A média esconde peças de sinal oposto: **partes de rótulo paga** (desligá-la
custa −6 aceito e −7 no aceito do confiante) e **propagação por headings custa no cru** (isolada derruba o aceito do
confiante para 56,1% e leva os erros confiantes de 74 para 82). **No produto o sinal se inverte:** headings é a maior
alavanca (−8 aceito se desligada) e não cobra precisão.

Cross-tab no cru: das 9 decisões que a 2ª passada tira da fila, **3 estão certas e 6 erradas** (33% contra a base de
59,5%), e ela quebra 2 acertos confiantes no FR. No produto: 7 saem da fila (5 certas, 2 erradas) e nenhum acerto é quebrado.

**REFUTA uma recomendação minha anterior:** eu havia registrado que a 2ª passada doa token de mídia como alias e que a
higiene mínima era dívida a pagar. Medido: a doação suja é pequena (**4 de 169 tokens doados no cru**: `pptx`, `video`,
`duracao` → `segmentacao` no CG; `ipynb` no IA) e, na conta real, **ela ganha 3 e perde 1** — a higiene mínima custa
**−2 aceito no cru e −3 no produto**. O alias é feio e o acerto é acidental, mas remover piora o número.


## 5. O QUE E O "SO CODIGO" — e um achado que caiu no colo (MEDIDO)

"So codigo" = da taxonomia ficam apenas os aliases que comecam com digito, isto e, **o rotulo do topico prefixado pela
numeracao do plano de ensino** (`1.1 Origens`, `1.2.1 Fundamentos de Logica de Primeira Ordem`). Todo sinonimo cai.

| curso | topicos | aliases | com codigo de outline | topicos sem NENHUM codigo |
|---|---|---|---|---|
| MF | 23 | 141 | 23 | 0/23 |
| SO | 36 | 162 | 36 | 0/36 |
| **IA** | **20** | **151** | **0** | **20/20** |
| ES2 | 21 | 105 | 21 | 0/21 |
| TCC | 26 | 151 | 28 | 0/26 |
| CG | 59 | 131 | 45 | **14/59** |
| FR | 32 | 87 | 32 | 0/32 |

**O IA e o unico curso sem nenhum topico numerado** — e e exatamente o curso onde o cru colapsa (5/39 aceito do
confiante, 34 erros num destino so). No CG, 14 de 59 topicos tambem nao tem numero.

## 6. O TETO DAS FONTES DO PROFESSOR, NOS 3 MODOS (MEDIDO, `c1-3/mede_fontes_do_professor_cru_12-09.log`)

```
########## A) modo --limpo (o que produziu o 61% publicado) ##########
O SUBTOPICO CERTO E ALCANCAVEL POR CADA FONTE DO PROFESSOR? [TAXONOMIA LIMPA: sem aliases curados do sidecar MANUAL; os do LLM sobrevivem]
         n      PLANO  AL-CURADO  AL-HEADIN       SARC      SECAO     TITULO   HEADINGS  PLANO+SAR  SEM-CURAD  PROFESSOR   QUALQUER    NENHUMA
SO      15    3   20%    0    0%    8   53%    0    0%    0    0%    2   13%    4   27%    5   33%    8   53%    8   53%    8   53%    7   47%
IA      39    0    0%    2    5%   38   97%   34   87%    2    5%   32   82%   21   54%   36   92%   39  100%   37   95%   39  100%    0    0%
ES2     28    2    7%   12   43%   28  100%    9   32%   13   46%    3   11%   11   39%   16   57%   28  100%   19   68%   28  100%    0    0%
TCC     10    2   20%    0    0%    9   90%    4   40%    3   30%    5   50%    4   40%    7   70%    9   90%    7   70%    9   90%    1   10%
MF      58    3    5%    0    0%   42   72%    7   12%    4    7%   20   34%   18   31%   27   47%   42   72%   28   48%   42   72%   16   28%
CG      77   17   22%   14   18%   25   32%   26   34%   19   25%   21   27%   17   22%   39   51%   45   58%   39   51%   52   68%   25   32%
TOT    227   27   12%   28   12%  150   66%   80   35%   41   18%   83   37%   75   33%  130   57%  171   75%  138   61%  178   78%   49   22%

gold fora da unidade computada (nao contam acima): 0
```

```
fontes do professor acrescentariam. 'NENHUMA' e o piso: nenhuma fonte do professor nomeia o subtopico certo.

########## B) modo --cru (sem aliases do sidecar LLM tambem) ##########
O SUBTOPICO CERTO E ALCANCAVEL POR CADA FONTE DO PROFESSOR? [CRU: taxonomia sem os aliases dos sidecares manual E LLM]
         n      PLANO  AL-CURADO  AL-HEADIN       SARC      SECAO     TITULO   HEADINGS  PLANO+SAR  SEM-CURAD  PROFESSOR   QUALQUER    NENHUMA
SO      15    3   20%    8   53%    1    7%    0    0%    0    0%    2   13%    4   27%    5   33%    8   53%    8   53%    8   53%    7   47%
IA      39    0    0%   38   97%    0    0%   34   87%    2    5%   32   82%   21   54%   36   92%   37   95%   37   95%   39  100%    0    0%
ES2     28    2    7%   28  100%    0    0%    9   32%   13   46%    8   29%   12   43%   17   61%   20   71%   20   71%   28  100%    0    0%
TCC     10    2   20%    9   90%    7   70%    4   40%    3   30%    5   50%    4   40%    7   70%    8   80%    7   70%    9   90%    1   10%
MF      58    3    5%   41   71%   12   21%    7   12%    4    7%   20   34%   18   31%   27   47%   30   52%   28   48%   42   72%   16   28%
CG      77   17   22%   39   51%    2    3%   31   40%   24   31%   32   42%   20   26%   46   60%   46   60%   46   60%   52   68%   25   32%
TOT    227   27   12%  163   72%   22   10%   85   37%   46   20%   99   44%   79   35%  138   61%  149   66%  146   64%  178   78%   49   22%
```

O teto honesto e **64% = 146/227, PRIMARIO**, contra o cru de 41,8% primario sobre 251 (bases diferentes: 227 exclui
gold vazio e o FR inteiro). O modo `--cru --sem-gemini` (que tambem tira IMAGE_DESCRIPTION e resumo de codigo do texto)
da o mesmo 146; o texto do Gemini so mexe na coluna de alias.

## 7. INVENTARIO DE FONTES: ganho LIQUIDO ja medido pelo criterio `nomeia()` (base 227)

| fonte | existe | nomeia o gold | ganho liquido |
|---|---|---|---|
| `moodle_week_label` | 98/227 | 19 | **+6** (todo em ES2 e MF) |
| nome ORIGINAL do arquivo (`raw/moodle/contents.json`) | 183/227 casados | 35 | **+3** |
| `/Title` do PDF | 57/227 | 5 | **+1** (34 dos 45 "nao-triviais" sao template velho de PowerPoint) |
| limpar a coluna PLANO | — | — | **-1** |

EMENTA e BIBLIOGRAFIA: existem nos 8 planos e sao inuteis para atribuicao hoje — a ementa e course-level (a cabeca do
plano parseia 0 unidades nos 8) e a bibliografia parseia 0 basica / 0 complementar nos 8 (regex de sub-secao nao casa o
formato dos planos). ORDEM NO MOODLE: existe em 203/227 e e consumida **so no eixo temporal**; zero nos eixos unidade e
subunidade. Nunca lidos: `indent` (75 modulos), `posting_date` (217 materiais), `sortorder`, `mimetype`.

## 8. O QUE JA FOI REFUTADO POR MEDICAO (nao reproponha sem argumento novo)

Abstencao por **piso global de winner_score** (4x: < 0,5 ganha 1 perde 6 · < 1,0 2/19 · < 1,5 4/20 · < 2,0 4/21) ·
irmaos empatados -> pai (-25) · topicos de u05 visiveis para u04 (0) · "mapeamento"/"gluLookAt"/"pipeline"/"provadores"
como alias (0) · nucleo em outra unidade (-6) · "microsservicos" como alias do estudo de caso (ajuste ao gold) ·
propagacao por similaridade como 3a passada (+1) · peso global ao titulo sem rastrear por que a regra existente falhou ·
Datalab ao vivo esperando ganho no motor (o motor nao le o `advanced_markdown`) · trocar a chave do cache de votos.

## 9. O QUE VOCE JA DEIXOU COMO ORDEM (v2) — para voce revisar a luz do numero novo

(1) preparar o CONTROLE limpo do SARC; (2) SARC posicional no IA, com vinculos congelados e abstencao por identificacao
insuficiente; (3) rastrear 1a -> 2a passada nos literais junto com a higiene dos tokens de midia; (4) base x advanced
efetivamente consumidos; (5) lexico congelado com curso alvo reservado.

---

## 10. PERGUNTAS

1. **A metrica.** "Entrega confiavel = confiantes certos / 251" e o alvo certo para esta frente, ou voce prefere outro
   par? E qual e um alvo NUMERICO defensavel para o cru — dado que o produto entrega 70,9% e o teto primario das fontes
   do professor e 64% sobre outra base? Diga explicitamente se o teto de 64% limita a entrega confiavel do cru ou se sao
   coisas independentes.
2. **A hipotese do usuario** ("quanto menos erros confiantes, melhor") vale sob que condicao? Existe um ponto de troca
   aceitavel entre erro confiante e cobertura que voce recomendaria FIXAR antes de medir alavanca, para nao ficarmos
   otimizando uma ponta so?
3. **O IA concentra 34 dos 77 erros confiantes num unico destino e e o unico curso sem numeracao de outline.** Isso e
   (a) um defeito de captura do plano (alavanca barata: numerar recupera o alias estruturado), (b) o efeito do rotulo
   "aspirador" do topico vencedor, (c) ausencia total de termo casavel para o gold sem o vocab LLM, ou (d) outra coisa?
   O que voce mediria PRIMEIRO para separar essas hipoteses?
4. **Os 14 que nem o vocab LLM resolve** (secao 3.1) sao teto de dado, teto de gold, ou defeito do motor? Eles devem sair
   do denominador da frente?
5. **24 dos 77 vem da 2a passada.** Ela deve ser restringida ou desligada no regime cru? Qual e o criterio que voce
   usaria para decidir isso sem cair no "desligar tudo que erra" (a 2a passada tambem acerta)?
6. **A ordem.** Mantem a ordem do v2, ou o numero novo (77 erros confiantes, 30,7% do acervo entregue errado sem aviso)
   muda a prioridade — por exemplo, atacar a ABSTENCAO antes de atacar a acuracia?
7. **O que descartar sem medir**, a luz de tudo.
