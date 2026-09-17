# Brief 2 para segunda opiniao (Codex astra, read-only) — regime CRU: a regua esta congelada, e agora? 2026-09-12 (tarde)

Voce ja opinou hoje de manha sobre esta frente (`resposta_codex_astra_regime_cru.md`). **Este brief NAO e uma repeticao:**
o usuario pediu que voce refizesse a analise com o contexto INTEIRO do produto, e no meio disso as tres coisas que voce
mandou fazer antes de decidir qualquer coisa foram feitas e mudaram os numeros. Leia a secao 2 antes de tudo.

Responda como sempre: MEDIDO x HIPOTESE, evidencia com arquivo:linha, e diga quando o dado nao sustenta a pergunta.
Voce esta read-only; nao rode o motor.

---

## 1. O CONTEXTO DO PRODUTO (isto voce nao tinha, e a pergunta 1 depende disto)

O que o sistema faz: um app desktop converte os materiais academicos de uma disciplina (PDF, HTML, video, codigo, links,
baixados do Moodle da faculdade) num **repositorio-tutor em Markdown por materia**, que o aluno abre num LLM (Claude, GPT,
Gemini) para estudar. O repo-tutor e organizado pela **estrutura curricular do professor**: unidades e subunidades vem do
PLANO DE ENSINO daquela disciplina, nao de uma ontologia nossa.

Tres eixos de atribuicao, por material:
  - BLOCO: a aula/semana em que o material foi dado (eixo temporal, ancorado no Moodle e no SARC, o sistema academico).
  - UNIDADE: a unidade do plano de ensino (u01, u02, ...). Hoje reconciliada com o bloco.
  - SUBUNIDADE: o subtopico dentro da unidade (o "1.4 Aplicacoes" do plano). **E o eixo desta frente.**

O que decide o problema, e que um brief so de numeros esconde:
  1. **O alvo e curso NOVO, sem gold.** O valor do produto e um professor jogar a pasta do Moodle dele e sair um tutor.
     Gold existe em 7 cursos porque nos construimos; num curso novo nao existe e nunca vai existir.
  2. **Nao pode haver LLM em runtime na atribuicao.** Hoje o vocabulario vem de uma passada de LLM que compila sinonimos
     por topico ("vocab LLM"), e e isso que queremos matar: sem ele o aceito cai de 89,2% para 58,6%.
  3. **O erro nao e simetrico.** Material na subunidade errada dentro da unidade certa e um aborrecimento; material na
     unidade errada quebra o tutor. Por isso existe uma FILA de revisao (`revisar`) e a metrica que o usuario usa para
     decidir e "precisao do confiante": do que o motor NAO poe na fila, quanto esta certo.
  4. **Aceito x primario.** O gold de subunidade tem um rotulo primario e zero ou mais extras aceitaveis (material
     multitematico). ACEITO = a predicao esta no conjunto; PRIMARIO = e exatamente o rotulo principal.

## 2. O QUE VOCE MANDOU FAZER ANTES DE DECIDIR — feito, e mudou o chao (MEDIDO)

Voce escreveu: *"resolver primeiro as duas divergencias CG declaradas no §7.6; depois congelar avaliacao primaria e aceita,
incluindo perdas individuais"* e *"falta a coluna gold; produto errado nao informa o destino correto"*. Resultado:

**(a) As divergencias replay x produto eram 10, nao 2, por DUAS causas independentes.**
  - Causa A, copia defasada: `.ablacao/CG` e `.ablacao/ES2` eram de 00:47; a curadoria E4 (curvas do CG) e E5 (gateway do
    ES2) entrou no produto as 00:59-01:01. 7 divergencias. `content/` e `code_curation.json` ja eram identicos; so
    `course/` e `manifest.json` diferiam. Recopiados.
  - Causa B, **bug de escopo no replay com vazamento do produto para dentro do regime cru**:
    `replay_subunidade.CATEGORIAS` lista `"referencias"` (PT); o Moodle grava `"references"` (EN). O replay processava 68
    das 93 entradas do CG. As 25 puladas (i) nao entravam no `df` nem nos `owners` da 2a passada — e o teto de df e
    *relativo a* `len(passe1)`, entao a populacao menor apertava o corte — e (ii) **ficavam com o `computed_subunit_slug`
    do manifest do produto**, porque `pred` e montado sobre TODAS as entradas, inclusive as puladas com `continue`.
    **23 ids do gold (22 CG + 1 MF) nunca foram recalculados: 16 aceito e 14 primario eram creditados ao "regime cru"
    vindos de decisao tomada COM vocab LLM.** Corrigido com `_no_escopo(e, escopo)`, `escopo="produto"` = o predicado do
    produto (`src/builder/routing/resolver_apply.py:421-436`).
  - **Agora: 0 divergencias replay x produto em 251/251, nos 7 cursos.** O replay reproduz o produto.

**(b) A regua congelada, aceito E primario, base 251:**

| regime | aceito | primario |
|---|---|---|
| produto (taxonomia como esta: codigo + plano + manual + LLM) | 224 = 89,2% | 186 = 74,1% |
| **cru** (sem os sinonimos do `.glossary_curation.llm.json`; curadoria humana mantida) | **147 = 58,6%** | **105 = 41,8%** |
| so codigo de outline (o mais cru possivel) | 113 = 45,0% | 84 = 33,5% |

O brief de hoje de manha dizia 139 aceito / 97 primario. **Aquele numero estava errado pelas duas causas acima.**

**(c) Precisao do confiante, agora com o primario (o gate da C1 so publicava o aceito):**

```

eixo             PRECISAO do confiante   RECALL da fila   alarme falso
bloco             188/189     99.5%    1/2      50%   47/48    98%
unidade           205/212     96.7%   14/21     67%   53/67    79%
subunidade        178/193     92.2%   12/27     44%   46/58    79%
subunid(prim)     154/193     79.8%   26/65     40%   32/58    55%
qualquer eixo     219/241     90.9%   26/48     54%   44/70    63%
```

**(d) Voce apontou "ha uma regressao inversa omitida da triagem".** Confirmado e identificado: era
`exercicioduascores` do CG — uma das divergencias replay x produto, nao erro do produto. Com a regua congelada, a conta e:
104 erros do cru por aceito, o produto acerta 80 deles, e **24 erros do cru que o produto TAMBEM erra** (o vocab LLM nao
resolve). Os 251 estao no CSV, nao so os 80.

## 3. OS 104 ERROS DO CRU, MATERIAL A MATERIAL, COM A COLUNA GOLD QUE VOCE PEDIU (MEDIDO)

`CRU` = predicao sem vocab LLM · `PRODUTO` = predicao atual do produto · `tipo`: vazio = o cru nao decidiu; trocado = decidiu outra coisa.
Slugs inteiros, sem truncar. Fonte: `c1-3/congela_regua_cru_12-09.csv` (251 linhas, todas as colunas) e `.log`.

```
curso    n  erros(aceito)  vazios  trocados  produto acerta  nao-primarios
MF      58             15       3        12              12             35
SO      15              6       1         5               6              7
IA      39             34       0        34              31             35
ES2     28              9       4         5               9             11
TCC     11              3       0         3               2              5
CG      82             26       9        17               9             41
FR      18             11       1        10              11             12
```

```
curso material                                             GOLD (primario | extras)                                       CRU (sem vocab LLM)                      PRODUTO                                  tipo  prod_ok
MF    archive-of-formal-proofs-355fb8                      provadores-de-teoremas                                         abordagens-para-verificacao-formal       abordagens-para-verificacao-formal       trocado  NAO
MF    logicapredicados-semantica                           fundamentos-de-logica-de-primeira-ordem                        especificacao-de-funcoes-recursivas      fundamentos-de-logica-de-primeira-ordem  trocado  sim
MF    logicaproposicional-sintaxe                          linguagens-de-especificacao-e-logicas | fundamentos-de-logica-de-primeira-ordem especificacao-de-funcoes-recursivas      linguagens-de-especificacao-e-logicas    trocado  sim
MF    revisao                                              sistemas-formais                                               especificacao-de-conjuntos-indutivos     sistemas-formais                         trocado  sim
MF    exerciciosespecificacao-respostas                    linguagens-de-especificacao-e-logicas                          especificacao-de-funcoes-recursivas      linguagens-de-especificacao-e-logicas    trocado  sim
MF    exerciciosespecificacao                              linguagens-de-especificacao-e-logicas                          (vazio)                                  linguagens-de-especificacao-e-logicas    vazio    sim
MF    logicaproposicional-semantica                        linguagens-de-especificacao-e-logicas | fundamentos-de-logica-de-primeira-ordem (vazio)                                  linguagens-de-especificacao-e-logicas    vazio    sim
MF    arvores                                              provadores-de-teoremas | especificacao-de-funcoes-recursivas   abordagens-para-verificacao-formal       provadores-de-teoremas                   trocado  sim
MF    exemplos                                             provadores-de-teoremas | especificacao-de-funcoes-recursivas;especificacao-de-conjuntos-indutivos exemplos-de-aplicacoes                   exemplos-de-aplicacoes                   trocado  NAO
MF    intro                                                provadores-de-teoremas | especificacao-de-conjuntos-indutivos;especificacao-de-funcoes-recursivas abordagens-para-verificacao-formal       especificacao-de-conjuntos-indutivos     trocado  sim
MF    listas                                               provadores-de-teoremas | especificacao-de-funcoes-recursivas   abordagens-para-verificacao-formal       provadores-de-teoremas                   trocado  sim
MF    provas                                               provadores-de-teoremas | especificacao-de-funcoes-recursivas   abordagens-para-verificacao-formal       provadores-de-teoremas                   trocado  sim
MF    hoare                                                logica-de-hoare | softwares-de-suporte-a-verificacao-formal-de-programas;verificacao-de-programas correcao-parcial-e-total                 logica-de-hoare                          trocado  sim
MF    terminacao                                           correcao-parcial-e-total | invariante-e-variante-de-laco       (vazio)                                  correcao-parcial-e-total                 vazio    sim
MF    tiposindutivos                                       softwares-de-suporte-a-verificacao-formal-de-programas         verificacao-de-programas                 verificacao-de-programas                 trocado  NAO
SO    1903-estruturas-de-controle                          conceitos-basicos                                              escalonamento                            conceitos-basicos                        trocado  sim
SO    3103-threads                                         conceitos-basicos                                              escalonamento                            conceitos-basicos                        trocado  sim
SO    exercicios                                           algoritmos-de-escalonamento                                    (vazio)                                  algoritmos-de-escalonamento              vazio    sim
SO    exemplo-threads-em-c-exemplo1                        conceitos-basicos                                              escalonamento                            conceitos-basicos                        trocado  sim
SO    exemplo-threads-em-c-exemplo2                        conceitos-basicos                                              escalonamento                            conceitos-basicos                        trocado  sim
SO    exemplo-threads-em-c-exemplo3                        conceitos-basicos                                              escalonamento                            conceitos-basicos                        trocado  sim
IA    algoritmo-de-classificacao-k-nn                      modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exemplo-com-k-nn                                     modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exemplo-2-k-nn-com-iriscsv-mais-completo             modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exemplo-de-programa-com-k-nn-em-java                 modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     introducao-ao-aprendizado-de-maquina     trocado  NAO
IA    artigo-usando-k-nn-em-texto                          modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    k-nn-para-classificacao-exemplo-cardio               modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    k-nn-para-regressao-exemplo-imc                      modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    introducao-a-redes-neurais                           modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron                                      modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-classificacao-de-cliente             modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-classificacao-planta-iris            modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-exemplo-atualizado                   modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-or-em-python                         modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-reconhecendo-letras                  modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exercicio-2-solucao-com-rede-perceptron-atualizado   modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    mlp                                                  modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    mlp-xoripynb                                         modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     (vazio)                                  trocado  NAO
IA    mlp-classificacao-iris-atualizado                    modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    mlp-regressao-cardio                                 modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    rede-perceptron-e-equacao-de-reta                    modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    xor-backpropagation-em-python                        modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    mlp-classificacao-inadimplencia-normalizacao-e-gridsearchcv modelos-preditivos | metricas-de-avaliacao                     introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    como-analisar-resultados-acc-pr-re-e-f1              metricas-de-avaliacao                                          introducao-ao-aprendizado-de-maquina     metricas-de-avaliacao                    trocado  sim
IA    arvores-de-decisao                                   modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exemplo-1-arvores-de-decisao-classificacao-planta-iris modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    exemplo-2-arvores-de-decisao-regressao-diabetes      modelos-preditivos                                             introducao-ao-aprendizado-de-maquina     modelos-preditivos                       trocado  sim
IA    aula-sobre-agrupamento-parte-1-particional           modelos-descritivos | paradigmas-de-aprendizado                introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    agrupamento-usando-k-means-exemplo-1-ipynb           modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    agrupamento-usando-k-means-exemplo-2-ipynb           modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    artigo-usando-agrupamento                            modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    survey-on-clustering                                 modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    aula-sobre-agrupamento-parte-2-hierarquico           modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     introducao-ao-aprendizado-de-maquina     trocado  NAO
IA    agrupamento-hierarquico-exemplo-1                    modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
IA    agrupamento-hierarquico-exemplo-2-use-o-dataset-da-planta-iris modelos-descritivos                                            introducao-ao-aprendizado-de-maquina     modelos-descritivos                      trocado  sim
ES2   revisaoarquiteturapadroes                            conceito-de-arquitetura-de-software | estilos-e-padroes-arquiteturais (vazio)                                  conceito-de-arquitetura-de-software      vazio    sim
ES2   microsservicos                                       orientada-a-microsservicos                                     estilos-e-padroes-arquiteturais          orientada-a-microsservicos               trocado  sim
ES2   roteiro1                                             estudo-de-caso-arquitetura-orientada-a-microsservicos          (vazio)                                  estudo-de-caso-arquitetura-orientada-a-microsservicos vazio    sim
ES2   devops                                               conceito-de-devops | gerenciamento-da-configuracao             integracao-continua-ci                   gerenciamento-da-configuracao            trocado  sim
ES2   kubernetes                                           plataformas-de-devops                                          (vazio)                                  plataformas-de-devops                    vazio    sim
ES2   roteiro2-nameserver                                  estudo-de-caso-arquitetura-orientada-a-microsservicos          cliente-servidor                         estudo-de-caso-arquitetura-orientada-a-microsservicos trocado  sim
ES2   roteiro2                                             estudo-de-caso-arquitetura-orientada-a-microsservicos          (vazio)                                  estudo-de-caso-arquitetura-orientada-a-microsservicos vazio    sim
ES2   microsservicos6                                      estudo-de-caso-integracao-e-implantacao-de-microsservicos      gerenciamento-da-configuracao            estudo-de-caso-integracao-e-implantacao-de-microsservicos trocado  sim
ES2   roteiro8-autenticacao-autorizacao                    estudo-de-caso-integracao-e-implantacao-de-microsservicos      gerenciamento-da-configuracao            estudo-de-caso-integracao-e-implantacao-de-microsservicos trocado  sim
TCC   aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos (vazio)                                                        maquinas-de-turing                       maquinas-de-turing                       trocado  NAO
TCC   aula-09-variacoes-de-maquinas-de-turing              variacoes-de-maquinas-de-turing                                maquinas-de-turing                       variacoes-de-maquinas-de-turing          trocado  sim
TCC   aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf linguagens-reconheciveis-e-decidiveis | maquinas-de-turing-universais maquinas-de-turing                       linguagens-reconheciveis-e-decidiveis    trocado  sim
CG    atividade                                            conceito-de-camera-sintetica | projecoes                       (vazio)                                  conceito-de-camera-sintetica             vazio    sim
CG    basico3d-py                                          conceito-de-camera-sintetica | pipeline-de-visualizacao-3d;projecoes perspectiva                              perspectiva                              trocado  NAO
CG    opengl3d                                             conceito-de-camera-sintetica | projecoes;pipeline-de-visualizacao-3d perspectiva                              conceito-de-camera-sintetica             trocado  sim
CG    opengl3dcpp-vdi                                      conceito-de-camera-sintetica | projecoes;pipeline-de-visualizacao-3d (vazio)                                  paralela                                 vazio    NAO
CG    opengl3dcpp                                          conceito-de-camera-sintetica | projecoes;pipeline-de-visualizacao-3d (vazio)                                  paralela                                 vazio    NAO
CG    vis3d                                                projecoes | paralela;perspectiva;conceito-de-camera-sintetica;a-matematica-das-projecoes-planares (vazio)                                  paralela                                 vazio    sim
CG    programabasico3d                                     modelos-de-reflexao-ambiente-difusa-especular | modelos-de-iluminacao-luz-pontual-direcional-spot;projecoes metodos-de-sombreamento-flat-gouraud-phong metodos-de-sombreamento-flat-gouraud-phong trocado  NAO
CG    exercicio-com-animacao                               operacoes-com-vetores | entidades-geometricas                  algoritmos-de-poligonos                  (vazio)                                  trocado  NAO
CG    matematica                                           operacoes-com-vetores | entidades-geometricas                  (vazio)                                  entidades-geometricas                    vazio    sim
CG    animacao-v2                                          (vazio)                                                        desenho-de-linhas                        desenho-de-linhas                        trocado  NAO
CG    exercicios-teoricos-sobre-processo-de-visualizacao-2d sistema-de-coordenadas-cartesianas                             desenho-de-linhas                        desenho-de-linhas                        trocado  NAO
CG    instanciamento                                       (vazio)                                                        sistema-de-coordenadas-cartesianas       2d-3d-mao-direita-e-mao-esquerda         trocado  NAO
CG    mapeamento                                           sistema-de-coordenadas-cartesianas                             recorte                                  sistema-de-coordenadas-cartesianas       trocado  sim
CG    pagina-com-videos-sobre-instanciamento               (vazio)                                                        desenho-de-linhas                        desenho-de-linhas                        trocado  NAO
CG    transformacoesgeometricas                            (vazio)                                                        desenho-de-linhas                        desenho-de-linhas                        trocado  NAO
CG    transformacoesgl                                     (vazio)                                                        sistema-de-coordenadas-cartesianas       sistema-de-coordenadas-cartesianas       trocado  NAO
CG    remocaoderuido                                       filtros                                                        cores-e-tipos-de-imagens                 filtros                                  trocado  sim
CG    introducaoprocimg                                    filtros | introducao-e-exemplos-de-aplicacoes;cores-e-tipos-de-imagens segmentacao                              filtros                                  trocado  sim
CG    exercicios-teoricos-sobre-processo-de-visualizacao-2d-html sistema-de-coordenadas-cartesianas                             desenho-de-linhas                        desenho-de-linhas                        trocado  NAO
CG    pagina-com-videos-sobre-fundamentos-matematicos-para-computacao-grafica-d1d4a9 entidades-geometricas | operacoes-com-vetores                  algoritmos-de-poligonos                  algoritmos-de-poligonos                  trocado  NAO
CG    videos-sobre-algoritmos-de-detecao-de-colisao-bd7d84 algoritmos-de-deteccao-e-calculo-de-interseccao                (vazio)                                  algoritmos-de-deteccao-e-calculo-de-interseccao vazio    sim
CG    pagina-com-videos-sobre-mapeamento-9f410e            sistema-de-coordenadas-cartesianas                             (vazio)                                  (vazio)                                  vazio    NAO
CG    video-sobre-mapeamento-em-opengl-1dad3c              sistema-de-coordenadas-cartesianas                             (vazio)                                  2d-3d-mao-direita-e-mao-esquerda         vazio    NAO
CG    pagina-com-videos-sobre-introducao-ao-processamento-de-imagens-61f156 introducao-e-exemplos-de-aplicacoes | filtros                  segmentacao                              filtros                                  trocado  sim
CG    paginas-com-videos-sobre-modelagem-geometrica-f2614a tecnicas-de-modelagem-3d | formas-de-representacao             geometria-solida-construtiva-csg         geometria-solida-construtiva-csg         trocado  NAO
CG    pagina-com-videos-sobre-visualizacao-3d-35a833       pipeline-de-visualizacao-3d | projecoes;conceito-de-camera-sintetica (vazio)                                  paralela                                 vazio    NAO
FR    01-protocolos-de-rede                                conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | conceitos-de-redes-de-computadores-e-internet modelos-osi-e-tcpip                      conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia trocado  sim
FR    03-tipos-de-redes                                    conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia | classificacao-e-topologias-de-redes-de-computadores modelos-osi-e-tcpip                      conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia trocado  sim
FR    04-camada-de-aplicacao                               funcoes-e-caracteristicas-do-nivel-de-aplicacao | paradigmas-clienteservidor-e-p2p protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap paradigmas-clienteservidor-e-p2p         trocado  sim
FR    04-protocolo-http                                    protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap paradigmas-clienteservidor-e-p2p         protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap trocado  sim
FR    05-protocolo-dns                                     protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat  protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat trocado  sim
FR    unidade2-exercicios-http                             protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap paradigmas-clienteservidor-e-p2p         protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap trocado  sim
FR    08-desenvolvimento-de-aplicacoes                     implementacao-de-sockets | paradigmas-clienteservidor-e-p2p    (vazio)                                  implementacao-de-sockets                 vazio    sim
FR    udp-example-c                                        implementacao-de-sockets | protocolo-udp                       paradigmas-clienteservidor-e-p2p         implementacao-de-sockets                 trocado  sim
FR    udp-example-java                                     implementacao-de-sockets | protocolo-udp                       paradigmas-clienteservidor-e-p2p         implementacao-de-sockets                 trocado  sim
FR    tcp-chat-c                                           implementacao-de-sockets | protocolo-tcp                       paradigmas-clienteservidor-e-p2p         implementacao-de-sockets                 trocado  sim
FR    tcp-example                                          implementacao-de-sockets | protocolo-tcp                       paradigmas-clienteservidor-e-p2p         implementacao-de-sockets                 trocado  sim
```

## 4. O TETO DAS FONTES DO PROFESSOR (MEDIDO, `c1-3/mede_fontes_do_professor_limpo_12-09.log`, taxonomia limpa, base 227)

```
O SUBTOPICO CERTO E ALCANCAVEL POR CADA FONTE DO PROFESSOR? [TAXONOMIA LIMPA: sem aliases curados]
         n      PLANO  AL-CURADO  AL-HEADIN       SARC      SECAO     TITULO   HEADINGS  PLANO+SAR  SEM-CURAD  PROFESSOR   QUALQUER    NENHUMA
SO      15    3   20%    0    0%    8   53%    0    0%    0    0%    2   13%    4   27%    5   33%    8   53%    8   53%    8   53%    7   47%
IA      39    0    0%    2    5%   38   97%   34   87%    2    5%   32   82%   21   54%   36   92%   39  100%   37   95%   39  100%    0    0%
ES2     28    2    7%   12   43%   28  100%    9   32%   13   46%    3   11%   11   39%   16   57%   28  100%   19   68%   28  100%    0    0%
TCC     10    2   20%    0    0%    9   90%    4   40%    3   30%    5   50%    4   40%    7   70%    9   90%    7   70%    9   90%    1   10%
MF      58    3    5%    0    0%   42   72%    7   12%    4    7%   20   34%   18   31%   27   47%   42   72%   28   48%   42   72%   16   28%
CG      77   17   22%   14   18%   25   32%   26   34%   19   25%   21   27%   17   22%   39   51%   45   58%   39   51%   52   68%   25   32%
TOT    227   27   12%   28   12%  150   66%   80   35%   41   18%   83   37%   75   33%  130   57%  171   75%  138   61%  178   78%   49   22%

gold fora da unidade computada (nao contam acima): 0

LEITURA: 'PLANO' e o que o motor ja tem hoje pelo texto. As colunas SARC/SECAO/TITULO/HEADINGS sao o que as
fontes do professor acrescentariam. 'NENHUMA' e o piso: nenhuma fonte do professor nomeia o subtopico certo.
```

**Ressalvas que a auditoria de hoje a tarde levantou sobre esta tabela (MEDIDO):**
  - **O 61% e PRIMARIO e a base e 227**, nao 251 (exclui gold vazio e o FR inteiro). O cru e 58,6% aceito / 41,8%
    primario sobre 251. A frase "o cru esta em 39% contra um teto de 61%" comparava metrica e base diferentes.
    **O teto por ACEITO nunca foi medido.**
  - **O teto nao e 100% cru:** a coluna PLANO varre `md + code_curation_signal_text(rec)`, e esse `md` carrega blocos
    IMAGE_DESCRIPTION (visao do Gemini) em **74/227** materiais e resumo de codigo do Gemini em **33/227**. Medido o
    efeito de limpar: PLANO 27 -> 26, PROFESSOR 138 -> 137 (61% -> 60%). Pequeno, mas enquanto nao for limpo o numero nao
    pode ser chamado de "fontes cruas do professor". A coluna HEADINGS esta limpa (0/227).

## 5. O INVENTARIO DE FONTES FORA DA TABELA QUE VOCE PEDIU (MEDIDO; ganho LIQUIDO, nao existencia)

Voce escreveu: *"Ementa, bibliografia, arquivo e ordem do Moodle merecem inventario"*. Feito, e cada candidata foi passada
pelo MESMO criterio `nomeia()` das 5 colunas atuais, no regime limpo que produz o 61% (base 227):

| fonte | existe | nomeia o gold | ganho liquido sobre as 5 colunas |
|---|---|---|---|
| `moodle_week_label` (label datado que o professor escreve na secao do Moodle) | 98/227 | 19 | **+6** (todo em ES2 e MF) |
| nome ORIGINAL do arquivo (`raw/moodle/contents.json`, via casador oficial) | 183/227 casados | 35 | **+3** |
| `/Title` dos metadados do PDF | 57/227 | 5 | **+1** |
| limpar a coluna PLANO (tirar IMAGE_DESCRIPTION e code_curation) | — | — | **-1** |

  - **EMENTA: existe nos 8 planos, e inutil para atribuicao.** E course-level, e a cabeca do plano (25 a 43 linhas, onde
    moram ementa e objetivos) parseia **0 unidades nos 8 cursos** (`src/builder/extraction/teaching_plan.py:183`, so
    acumula topico dentro de `if current_title is not None`). Nao distingue material dentro do curso.
  - **BIBLIOGRAFIA: existe nos 8 planos e hoje parseia 0 basica / 0 complementar nos 8** — o regex exige `^BASICA\s*:` e
    os planos escrevem `## * **BASICA**` ou `BIBLIOGRAFIA BASICA:`. Nenhum caminho do motor de atribuicao le bibliografia.
  - **ORDEM NO MOODLE: existe e esta inerte onde importa.** `moodle_section_index`/`moodle_module_index` em 203/227,
    consumidos SO no eixo temporal (`routing/motor/card_stream.py:110-119`, que ainda descarta toda entrada sem
    `moodle_week_label`, reduzindo o alcance real a 98/227) e em `anchor_engine.resolve_general_section`.
    **Zero consumo nos eixos unidade e subunidade.**
  - **`/Title` do PDF nao paga**, apesar da cobertura aparente: dos 45 "nao-triviais", 34 sao template velho de PowerPoint
    — `"Algoritmos e Programacao II"` 8x (no MF e **disciplina errada**: entraria como sinal ativamente falso),
    `"Programacao javaEE"` 10x no ES2, `"Apresentacao do PowerPoint"` 4x, e 10 do TCC sao o nome do arquivo em UTF-16.
  - Nunca lidos por ninguem: `indent` do modulo (75 modulos nos 8), `posting_date` (217 materiais em 5 cursos),
    `sortorder`, `mimetype`, `author`.
  - Descartados por medicao: numero da secao do Moodle (so o CG numera, e a numeracao e a sequencia didatica dele, nao as
    9 unidades do plano), `section.summary` (1-2 secoes por curso, texto administrativo), cronograma do plano (o do TCC
    diz "Disponivel no Moodle"), nome de pasta (e o slug do curso em 5 de 6).

## 6. AS 5 FAMILIAS QUE VOCE NOMEOU DE MANHA (para voce conferir contra a lista nova da secao 3)

| Familia | Evidencia que voce citou | Hipotese que voce deixou |
|---|---|---|
| Colapso num candidato | IA: 34 erros -> introducao; SO: cinco -> escalonamento | Prior, desempate ou pontuacao domina evidencia especifica |
| Competicao entre niveis | TCC: variacoes -> maquinas de Turing; ES2: microsservicos -> estilos | Rotulo amplo vence filho explicito |
| Ponte entre codigo e conceito | FR: quatro exemplos TCP/UDP -> cliente/servidor | Evidencia de implementacao nao chega a sockets |
| Literal aparentemente perdido | MF: hoare; ES2: microsservicos; TCC: variacoes | Auditar candidatos, normalizacao e veto da regra existente |
| Residuo pouco ajudado pelo produto | CG: 23 dos 33 erros compartilhados | Separar extracao, granularidade do gold e material multitematico |

## 7. AS RUNS DO FR (curso construido DO ZERO, sem gold no processo; MEDIDO, `c1-3/mede_fr_sem_gold_run*_12-09.log`)

| run | aceito /18 | primario /18 |
|---|---|---|
| crua (pymupdf4llm, sem vocab, sem voter) | 7 | 6 |
| so Datalab (extracao avancada, sem vocab) | 8 | 6 |
| crua + vocab | 18 | 16 |
| Datalab + vocab | 18 | 17 |
| Datalab + LLM viva (voter) | 18 | 17 |
| produto | 18 | 16 |

Achado que o FR produziu: **o motor pontua `base_markdown`; o `advanced_markdown` (Datalab) e a ULTIMA opcao**
(`navigation._entry_markdown_path_for_file_map`: approved > curated > base > advanced). 163 materiais nos 8 cursos tem
Datalab que o motor nunca leu. E: **o vocab compilado mexe no BLOCO** — FR do zero com vocab e sem voter, bloco = produto
cai de 15/20 para 10/20; o voter recompoe (19/20).

## 8. AS DECISOES DO USUARIO QUE NAO SE REABREM (contexto, nao pergunta)

1. OpenGL do CG = u01, subunidade 1.4 Aplicacoes. Os 9 erros do aglomerado u04 do CG sao TETO do motor (so abstencao
   corrigiria; refutada 4x).
2. A regua de unidade e CURRICULAR: `material_gt_<sig>.csv` (adjudicado) sobrepoe o gold por bloco.
3. Frente prioritaria: melhorar o cru e o so-Datalab; **depois** disso, outras engines de extracao (MinerU e derivados).
4. Gold so mede, nunca decide. SARC e Moodle acima do gold. Medir os 3 eixos em todo rollout. Estimativa em proxy nao vale.

## 9. O QUE JA FOI REFUTADO POR MEDICAO (nao proponha de novo sem argumento novo)

Abstencao por piso de score (global e so em topico sem alias: 4x, -2 a -17) · irmaos empatados -> pai (-25) · topicos de
u05 visiveis para u04 (0) · "mapeamento"/"gluLookAt"/"pipeline"/"provadores" como alias (0: token generico) · nucleo em
outra unidade (-6) · "microsservicos" como alias do estudo de caso (ajuste ao gold) · propagacao por similaridade como 3a
passada (+1 candidato) · peso global ao titulo sem rastrear por que a regra existente falhou (voce) · Datalab ao vivo
esperando ganho no motor (o motor nao le o advanced) · trocar a chave do cache de votos por conteudo.

## 10. A ORDEM QUE VOCE DEIXOU DE MANHA (e o que o usuario aprovou executar em seguida)

0. Congelar a regua — **FEITO, secao 2**.
1. **SARC posicional limpo:** o material herda o subtopico que a sessao do SARC do seu bloco nomeia; vinculos
   material -> bloco -> unidade produzidos sem gold, pinos manuais separados; sessao que nomeia o pai NAO escolhe o filho
   (fica indeterminado); com e sem SARC contra o gold, ganhos e perdas nominais, aceito e primario. Alvo: IA.
2. Por que a regra de titulo EXISTENTE falha nos literais perdidos (MF `hoare`, ES2 `microsservicos`, TCC `variacoes`).
3. Headings que nomeiam subtopico irmao (2a passada).
4. So Datalab nos 8 (163 materiais com `advanced_markdown`), **vocab AUSENTE**, voter desligado, por tipo pdf/html/video.
5. Lexico embarcado (LR <-> FR mede transferencia, nao independencia de LLM).

## 11. DIVIDAS QUE A AUDITORIA DE HOJE ABRIU (MEDIDO; nenhuma resolvida)

1. **A regua de UNIDADE nao pontua material transversal.** `scripts/eval_entry_unit.py:86-92` descarta as linhas de
   `material_gt_*.csv` com `gold_units` multi-valorado (separador `|`) em vez de virar conjunto aceito, porque os
   consumidores comparam com `==`. Sao **24 materiais** (ES2 12, CG 5, SO 5, MF 1, TCC 1): planos de ensino, cronogramas,
   listas transversais. O comentario no codigo assume a exclusao explicitamente.
2. **A 2a passada doa token de MIDIA como alias de subtopico.** No CG, `pptx`, `video` e `duracao` viraram alias de
   `segmentacao`; o acerto do produto em `morfologiamatematicapptx` e acidental. `_tokens_headings`
   (`src/builder/routing/resolver_apply.py:178-180`) filtra so `MOTOR_GENERIC_STEMS`, que nao cobre extensao de arquivo
   nem termo de midia.
3. Os eixos UNIDADE e BLOCO nao tem aceito/primario, e o bloco nao pode ter (`ground_truth_*.csv` tem coluna unica
   `true_block_id`). No eixo unidade o par de metricas chama-se BRUTO x CERTO (precisao do confiante), com abstencao.

---

## 12. PERGUNTAS, EM ORDEM

1. **Com o contexto do produto da secao 1** (tutor por unidade do plano, curso novo sem gold, zero LLM em runtime, erro
   assimetrico entre unidade e subunidade), **o problema que estamos atacando esta bem posto?** Especificamente: perseguir
   o PRIMARIO da subunidade no regime cru e a meta certa, ou a meta certa e outra coisa (aceito? precisao do confiante com
   abstencao? cobertura por unidade?) — e por que.
2. **Olhando a lista nova da secao 3 (104 erros, com gold e slug inteiro):** que padroes aparecem ALEM das suas 5
   familias, e alguma das 5 nao sobrevive ao dado novo? Interessa especialmente o subconjunto de **24 erros que o produto
   TAMBEM erra** (o vocab LLM nao resolve): eles sao teto de dado, teto de gold, ou defeito do motor?
3. **Desenho do experimento SARC posicional sem circularidade.** O SARC ja e usado para ancorar o BLOCO. Usa-lo tambem
   para a SUBUNIDADE e circular? Se nao, qual e o desenho minimo que prova isso, e qual e a regra de abstencao quando a
   sessao nomeia o pai? (o alvo e o IA: SARC nomeia 87% e o cru faz 5/39).
4. **O que descartar sem medir**, da ordem da secao 10 e do inventario da secao 5. O `/Title` do PDF (+1, com 34/45 de
   template errado) e o filename original (+3, custa um casador) merecem coluna? O `moodle_week_label` (+6, concentrado em
   2 cursos) e alavanca ou e sobreajuste a ES2/MF?
5. **Como o lexico embarcado deve NASCER para nao ser "vocab LLM com outro nome"?** Que proveniencia, que congelamento e
   que teste de transferencia tornam legitimo dizer "determinista em execucao"?
6. **O que mais voce mudaria na ordem da secao 10**, agora que a regua esta congelada e o teto tem as ressalvas da secao 4?
