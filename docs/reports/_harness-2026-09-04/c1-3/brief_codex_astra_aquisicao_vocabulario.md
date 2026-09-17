# Brief 7 para o astra (read-only): ANALISAR E DESENHAR A AQUISICAO DE VOCABULARIO — 2026-09-13

Ordem do usuario: *"coloque o astra para analisar e para desenhar a aquisicao de vocabulario"*.

Contexto da ordem: hoje fecharam por negativo medido TODAS as alavancas de estrutura do eixo unidade (titulo,
precedencia literal, precedencia condicional com LOCO). **Sobrou uma alavanca so, nos dois eixos que ainda faltam:
vocabulario.** O usuario quer 90% de acuracia total em bloco, unidade e subunidade **no motor cru**.

**O que eu quero de voce: (a) a ANALISE do que a aquisicao de vocabulario e hoje, e (b) o DESENHO da aquisicao que
leva o cru ao alvo** — com fontes, criterio de selecao, ordem, orcamento, e protocolo de validacao **sem o gold do
curso testado**. Nao e revisao: e projeto, com criterio de parada por passo e com o que NAO fazer.

Regras de sempre: separe MEDIDO de HIPOTESE, evidencia com `arquivo:linha`, e diga quando o dado nao sustenta a
conclusao. Read-only, sem chamada de rede.

---

## 1. POR QUE SO SOBROU O VOCABULARIO (medido, hoje)

Os 3 eixos com o motor COMPLETO rodando em copia, `use_llm_voter=False`, rede bloqueada e contada em 0
(`c1-3/motor_3eixos_12-09.py`, `c1-3/mede_3eixos_12-09.py`). Acuracia TOTAL (abster nao tira do denominador):

| eixo | NU | **REGUA (cru)** | VOCAB | PRODUTO |
|---|---|---|---|---|
| bloco (237) | 93,2% | **93,7%** | 93,2% | 99,2% |
| unidade (284) | 85,9% | **89,1%** | 89,8% | 92,6% |
| **subunidade aceito (251)** | 49,8% | **58,2%** | 87,6% | **89,2%** |
| subunidade primario | 33,9% | 41,0% | 73,3% | 74,1% |

**O vocabulario sozinho vale +29,4 pontos na subunidade.** O voter vale mais +1,6.

Fechado hoje por medicao, no eixo unidade (nao reabrir):

| alavanca | resultado |
|---|---|
| "o titulo do material nomeia a unidade" como regra | refutada; o corte que daria +3 foi recusado por ajuste ao benchmark |
| "texto vence o bloco" sempre (`file_map.py:802-807`) | **-15 no cru, -7 no produto** contra a regua curricular |
| "texto vence quando o bloco veio de metodo fraco" (`janela-1`/`due-*`) | +7 dentro da amostra, **-3 FORA** (LOCO, 6 folds) |
| SARC posicional | negativo nos dois regimes |
| abstencao / margem 1o-2o / razao s2s1 / riqueza de alias | a entrega nao sobe (113 -> 112) |
| limpar tokens de midia da doacao | -2 cru, -3 produto |
| Datalab como alavanca de atribuicao | 21/31 nos dois bracos; 3 predicoes mudam |

**A licao do LOCO, que vale para o seu desenho:** uma regra com UM parametro escolhido olhando os 6 cursos deu
**+38 dentro e -3 fora**, com o parametro estavel em 5 dos 6 folds. Nao foi instabilidade de selecao: o ganho
simplesmente nao transfere. **Qualquer criterio que voce desenhar olhando estes 7 cursos tem que vir com o teste de
transferencia embutido, nao depois.**

**No eixo unidade o que sobra com sinal positivo sao os 10 materiais em que o PRODUTO acerta e o cru erra — e o
mecanismo deles tambem e vocabulario** (SO `laminas-sockets`: o cru manda para `deadlock`, o plano quer
`programacao-concorrente`). Ou seja: os dois eixos que faltam dependem da mesma peca.

## 2. O QUE O "CRU" REALMENTE CONTEM — a descoberta de hoje, e ela muda o enquadramento

Eu vinha descrevendo os regimes assim: **cru = curadoria humana, sem vocabulario de LLM**; **vocab = + sidecar do LLM**.
**Medi o conteudo dos dois sidecars e o rotulo "curadoria humana" esta errado.**

O sidecar que o cru conserva (`course/.glossary_curation.json`) **nao e humano**: o `_nota` dele diz

> *"GERADO automaticamente de fontes do PROFESSOR (SARC + secao do Moodle + titulo/headings dos materiais da secao),
> sem olhar gold nenhum — `c1-3/gera_sidecar_professor.py`, 2026-09-07."*

E o conteudo dele, nos 5 cursos que o tem, e **66 termos em 15 topicos** — contra **560 sinonimos** do sidecar do LLM:

| curso | topicos | termos | amostra do que ele contem |
|---|---|---|---|
| CG | 4 | 5 | `OpenGL`, `Catmull-Rom`, `Bezier`, `Casteljau`, `Curvas Parametricas` |
| ES2 | 2 | 22 | `alternativo`, `ativando`, `buildpacks`, `cadastro`, `colocando`, `conteiners`, `education` |
| IA | 2 | 21 | `aluna`, `barabstract`, `braid`, `capitulo`, `cargas`, `chiara`, `demo`, `lacerda`, `luca` |
| SO | 4 | 11 | `about`, `laminas`, `livro`, `logica`, `versus`, `abstrata`, `fato`, `massa`, `mecanico` |
| TCC | 3 | 7 | `classicos`, `detalhado`, `mensagem`, `lemas`, `visoes`, `desfechos`, `revisitado` |

**Dos 66 termos, so os 5 do CG sao termos de dominio.** O resto e token de nome de arquivo e de autor (`chiara`,
`lacerda`, `luca`), boilerplate (`capitulo`, `livro`, `demo`) e palavra comum (`fato`, `massa`, `versus`).

O do LLM, no mesmo curso IA, e outra coisa: `Rede Neural Perceptron`, `MultiLayer Perceptron`, `k-NN`,
`Arvores de Decisao`, `k-Means`, `Clustering`, `Agrupamento Hierarquico`, `Mapa auto-organizavel`, `Matriz de Confusao`.

**Consequencia para o enquadramento, e quero que voce a critique:** a diferenca entre cru e vocab **nao e
humano x LLM**. E **ruido x vocabulario de dominio**. O regime cru, na pratica, **nao tem camada de vocabulario de
dominio nenhuma** — tem 66 tokens, quase todos ruido. Os +29,4 pontos nao sao "o LLM sabendo mais que o professor":
sao a diferenca entre ter e nao ter a camada.

## 3. A AQUISICAO DETERMINISTICA JA FOI CONSTRUIDA E MEDIDA — recupera 11 dos 66 pontos

`c1-3/gera_sidecar_professor.py` (07/09) e a tentativa de aquisicao **sem LLM e sem gold**: a secao do Moodle que
nomeia exatamente um topico doa o vocabulario dos materiais dela (titulo, label, headings); o label da aula do SARC que
nomeia um topico doa os tokens restantes. Filtros: boilerplate academico, frequencia > 15% dos materiais, token que ja
nomeia outro topico, concentracao >= 80% das ocorrencias na secao doadora, < 4 chars, numerico.

| regime | subunidade (base de 233 daquela campanha) |
|---|---|
| sidecar derivado do gold (contaminado) | 201/233 |
| sem sidecar | 135/233 |
| **sidecar do professor (deterministico)** | **146/233** |

**Recupera 11 dos 66 pontos.** Por curso, limpo -> professor: ES2 5->15, SO 9->10, MF 51->52, **IA 4->4**, TCC 8->8,
CG 58->57. **No IA — o curso que concentra o maior buraco — nao recupera nada, e no CG piora 1.**

E uma medicao anterior da mesma familia: **co-heading deterministico 26 -> 31/93; o prompt do LLM, na mesma base,
IA 5 -> 37/39 e FR 12 -> 17/19** (`src/builder/core/vocabulary_compile.py:6-8`).

**Entao a pergunta central do seu desenho ja tem duas tentativas negativas atras dela.** Nao peco que voce repita nem
que defenda nenhuma das duas.

## 4. O QUE O LLM FAZ DE DIFERENTE — medido: nao e a FONTE, e a SELECAO

Auditoria de 12/09 (`§23` do handoff), com refutador adversarial:

- **O motor nunca le arquivo de gold.** Varredura em `src/builder/**`: "gold", "*.csv" e "docs/reports" so aparecem
  em comentario de procedencia; nenhum `open()`.
- **A entrada da compilacao e so o curso**: nome da disciplina, titulo da unidade, rotulos dos topicos do plano e, por
  material, titulo + label do Moodle + ate 24 headings (`vocabulary_compile.py:172-186`).
- **552 dos 560 sinonimos estao literalmente nos titulos/headings do proprio curso (98,6%).**
- **Os filtros escolhidos olhando o gold carregam ZERO do ganho**: devolvendo `_raw` (saida crua, antes dos filtros) em
  vez dos `synonyms` publicados, K=5 = 178 e K=40 = 191 — identicos.

**Leitura que quero que voce confirme ou derrube:** o LLM e o deterministico leem *o mesmo corpus*. O deterministico
devolve `chiara` e `barabstract`; o LLM devolve `k-NN` e `Mapa auto-organizavel`. **A aquisicao nao e um problema de
fonte — e um problema de decidir quais tokens do corpus sao termos de dominio daquele topico.** Se isso estiver certo,
o desenho tem que atacar o classificador de termo, nao a coleta.

**A unica dependencia de gold que sobra em toda a cadeia:** o prompt foi selecionado medindo contra o gold —
`vocabulary_compile.py:72` diz *"Prompt v2 — o unico ajuste permitido, medido (IA 34 -> 37/39). Nao mexer sem remedir."*
**E o IA e exatamente o curso que produz 100% do ganho do seletor.** Nao e testavel offline: exigiria recompilar o
sidecar do IA com o prompt v1, o que custa chamada.

## 5. AS ARMADILHAS JA MEDIDAS QUE O DESENHO TEM QUE RESPEITAR

**(a) Curar tópico a mais PIORA.** Devolvendo vocabulario nos K topicos que o meu criterio aponta (base cru 147/251):

| K | 5 | 10 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| aceito | **178** | 175 | 176 | 173 | 184 | **191** |

**A curva nao e monotonica.** Alias a mais vira empate no detector. O mesmo mecanismo fez o teto SUBIR quando tiramos
aliases (`§11.4`). **O seletor tem que ser preciso, nao abrangente.**

**(b) O meu seletor nao seleciona nada (auditado e admitido).** Os +31 de K=5 sao **2 topicos de 1 curso**:
IA `modelos-preditivos` +23, IA `modelos-descritivos` +6; os outros 3 dao **+0**. O baseline ingenuo **"maior unidade"**
— que ignora inteiramente o criterio lexical — **empata em K=5 (178) e ganha em K=10 (182 x 175) e K=20 (190 x 173)**.
Baseline aleatorio com 7 sementes: 148,4 ± 2,6. **O que existe e um curso com uma unidade de 39 materiais onde o
vocabulario faz diferenca enorme; qualquer ranking que ponha esses 2 topicos no topo chega ao mesmo lugar.**

**(c) "score > 0" nao prova suporte lexical** — seu proprio achado, confirmado em `src/builder/timeline/index.py:1935`:
`if kind == "subtopic": score += 0.04`, incondicional, sem nenhum casamento de texto.

**(d) A 2a passada AUTO-ENVENENA.** `src/builder/extraction/content_taxonomy.py:603-646` doa headings **dos proprios
materiais** como alias de topico. No IA, 5 headings de slides foram arquivados no topico errado; **nao vem do LLM,
entao sobrevivem ao corte do regime cru**. `arvores-de-decisao` pontua 8,97 no topico errado casando a frase que e o H2
do proprio arquivo. `propagado-headings` e a rota mais fragil: 51,4% de precisao contra 59,5% da media.

**(e) O plano de ensino e a fonte MAIS FRACA de vocabulario.** O padrao e sempre o mesmo: **o plano usa a CATEGORIA e o
material usa a TECNICA.** O plano do IA diz "Modelos Preditivos" e os slides dizem perceptron, k-NN, MLP, arvore de
decisao. A ementa do IA (3.569 chars, lida inteira) **nao menciona nenhuma dessas tecnicas uma unica vez.**

## 6. ONDE OS ERROS ESTAO (`c1-3/erros_subunidade_motor_12-09.csv`, 105 de 251)

```
o PRODUTO acerta 80 e tambem erra 25 · na FILA 47 · confiantes e errados 58 · predicao VAZIA 14
DENTRO da unidade certa 83 (dano contido) · com a unidade TAMBEM errada 9 · sem regua de unidade 13
por rota: 1a-passada 77 · propagado-headings 23 · rotulo-decomposto 5
por curso: MF 12 · SO 6 · IA 34 · ES2 10 · TCC 3 · CG 29 · FR 11
concentracao: 10 pares (curso, topico do gold) concentram 71 dos 105 = 68%
   IA modelos-preditivos 25 · IA modelos-descritivos 8 · MF provadores-de-teoremas 6 ·
   SO conceitos-basicos 5 · ES2 estudo-de-caso-arquitetura-microsservicos 5 · CG (vazio) 5 ·
   CG sistema-de-coordenadas-cartesianas 5 · FR implementacao-de-sockets 5 ·
   CG conceito-de-camera-sintetica 4 · CG tecnicas-de-modelagem-3d 3
```

E o recorte que separa **ausencia** de **competicao**: dos 10 alvos, **3 tem suporte por frase** (MF
`provadores-de-teoremas`, ES2 `estudo-de-caso-...`, CG `segmentacao`) — neles o vocabulario **existe e perde a
competicao**. Nao e aquisicao, e ordenacao.

## 7. O QUE EU TENHO EM MAOS

- `erros_subunidade_motor_12-09.csv` — 105 erros com rota, fila, unidade, confianca, e se o produto acerta
- `fronteira_sinais_12-09.csv` — 47 colunas de sinal por material x regime (cobertura do topico entregue, peso do campo
  doador, `exact_hits`, share na unidade, n de candidatos com score > 0, rota, tamanho da frase que casou)
- `congela_regua_cru_12-09.csv` (251 materiais nos 3 regimes) · `onde_esta_o_rotulo_12-09.csv`
- `seletor_topicos_carentes_12-09.csv` · `ganho_do_seletor_12-09.log` · `baseline_aleatorio_12-09.log`
- o motor rodando em copia por configuracao, rede bloqueada e contada (`motor_3eixos_12-09.py`), 4 bracos
- **7 cursos com gold de subunidade (251 materiais)** e o **LR como curso reservado, sem gold de subunidade**
- `gera_sidecar_professor.py` (aquisicao deterministica) e `vocabulary_compile.py` (aquisicao por LLM), os dois rodaveis

## 8. O QUE EU QUERO DE VOCE

1. **A analise:** o enquadramento da §2 e da §4 esta certo? A aquisicao e um problema de **selecao de termo**, nao de
   fonte? Se sim, diga o que exatamente separa `perceptron` de `chiara` no corpus — e se esse separador e computavel
   sem LLM. Se nao for, **diga isso com todas as letras**, porque muda a meta do usuario.

2. **O desenho da aquisicao, executavel.** Fontes, criterio de selecao de termo, criterio de selecao de TOPICO (dado
   que curar demais piora e que o meu seletor nao seleciona), orcamento fixado ANTES, e onde o resultado e gravado.
   Diga o que **nao** fazer.

3. **O contrato minimo de LLM, se ele for necessario.** Quantas chamadas por curso, o que fica em cache, o que e
   auditavel, o que acontece num curso novo sem nenhum artefato — e se da para o curador humano substituir a chamada
   (o sidecar manual e o mesmo arquivo). Se a sua conclusao for "sem LLM nao chega a 90%", **diga o numero que da
   sem LLM** e o que ele exige.

4. **A dependencia de gold do prompt v2.** Como quebra-la, e qual e o teste que a mede sem inflacionar.

5. **O protocolo de validacao sem gold**, depois da licao do LOCO: os 7 cursos ja foram olhados; o LR nao tem gold de
   subunidade. Diga o que precisaria ser adjudicado no LR e **quanto** (n de materiais), ou um caminho que dispense
   isso. E contra quais baselines comparar — o "maior unidade" ja empata com o meu seletor.

6. **Os 25 que o produto tambem erra e os 14 de predicao vazia**: entram no alvo da aquisicao ou sao outro problema?

7. **A meta realista da subunidade no cru, em quantos passos** — dado que o vocabulario dirigido POR GOLD nos 36
   topicos chega a 222/251 = 88,4%, e que o usuario pede 90%.

8. **O eixo unidade:** os 10 materiais em que o produto acerta e o cru erra sao alcancaveis pela mesma aquisicao, ou
   precisam de peca propria? A unidade esta em 89,1% e a meta e 90% — faltam 3.
