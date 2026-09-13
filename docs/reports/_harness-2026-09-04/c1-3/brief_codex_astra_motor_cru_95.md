# Brief 8 para o astra (read-only): A CAUSA REAL, E UM MOTOR CRU COM ≥95% NOS 3 EIXOS — 2026-09-13

## 0. A ordem do usuário, literal

> *"Eu imagino que estamos fazendo fixes específicos, e não atacando a causa real do problema. A ideia é que o motor
> fique preciso o suficiente (3 eixos e primário > 95%), mas de maneira crua — ou seja, que o aluno consiga apenas
> processar o arquivo, e com base nas informações que o sistema coleta quando é criada uma matéria (SARC, Plano de
> Ensino, Cards moodle etc.) consiga categorizar tudo; e quando o repo sofre um resync, a mesma coisa acontece com o
> arquivo novo. O uso de LLM ou APIs externas tem que ser totalmente opcional, nenhum eixo ou precisão pode se
> sustentar com LLM ou APIs... E também as informações e eixos não podem se sustentar nos gold... Outra coisa, o motor
> tem que ser modular, pois cada professor tem uma maneira de rotular os arquivos. Busco tanto o bloco, unidade e
> subunidade >= 95%, depois disso é apenas polimento."*

**Ele suspeita que o trabalho está em remendo, não em causa.** Eu concordo com a suspeita e por isso este brief não
pede validação do que fizemos: pede **arquitetura**.

## 1. A PRIMEIRA COISA QUE VOCÊ TEM QUE ENFRENTAR: o alvo está acima do teto já medido

| eixo | base | 95% exige | cru honesto | cru + vocabulário dirigido | **PRODUTO (APIs pagas, voter ON)** |
|---|---|---|---|---|---|
| bloco | 237 | 226 | 222 | 222 | **235** ✅ |
| unidade | 284 | 270 | 253 | 253 | **263** ❌ faltam 7 |
| **subunidade PRIMÁRIO** | 251 | 239 | 100 | 134 | **186** ❌ **faltam 53** |

**A configuração com APIs pagas — o melhor número que este projeto já mediu — não alcança 95% primário em dois dos
três eixos.** Então o pedido não é "tirar o LLM e manter o número". É **superar o melhor número já medido, sem LLM**.

Se a sua resposta for que isso não é alcançável com a informação disponível, **diga isso na primeira linha e mostre
onde a informação acaba.** O usuário prefere um limite medido a um plano otimista — ele já derrubou quatro
conclusões otimistas minhas hoje.

Note a diferença entre **aceito** (a predição está no conjunto {gold primário} ∪ extras) e **primário** (bate o gold
primário exato). Todo o trabalho de ontem foi cobrado em *aceito*; o usuário agora cobra **primário**, que é mais
duro. No cru: aceito 56,6%, primário 39,8%.

## 2. O motor hoje, em uma página

**Entrada por curso** (é isto que o sistema coleta quando a matéria é criada — nenhum destes é gold):
- **Plano de Ensino** → vira `course/.content_taxonomy.json`: unidades → tópicos → subtópicos, cada um com `label`,
  `code` e `aliases`.
- **SARC** (sistema acadêmico): calendário com data e rótulo de cada aula.
- **Moodle**: seções (com nome), cards por seção, label por material, data de entrega.
- **Acervo**: os arquivos em si (pdf, zip, url, vídeo...), convertidos a markdown.

**Três eixos, três mecanismos diferentes — e é aqui que a modularidade existe ou não:**

| eixo | como é decidido hoje | modular? |
|---|---|---|
| **bloco** | cascata nomeada de 12 métodos, e o manifest grava qual decidiu | **sim** |
| **unidade** | precedência fixa em `routing/file_map.py:802-807`: a unidade do BLOCO vence o texto | **não** |
| **subunidade** | scorer lexical sobre a taxonomia, 3 rotas (`1a-passada` 78, `propagado-headings` 26, `rotulo-decomposto` 5) | parcialmente |

Distribuição real dos 12 métodos de bloco nos 7 cursos (341 entries): `janela-1` 147, `disamb` 100, `titulo-topico`
24, vazio 23, `prep-prova` 12, `irmao-card` 10, `meta-generica` 7, `disamb-curto` 7, `ref-generica` 5, `secao-geral`
3, `due-contain` 2, `due-straddle` 1.

**O scorer de subunidade** (`timeline/index.py:1899-1907`) pontua estes campos e só estes:
```
markdown_headings_text · title_text · markdown_lead_text · manual_tags_text
markdown_text · auto_tags_text · legacy_tags_text · raw_text
```
**Não pontua o `moodle_label`.** E `index.py:1935` dá `+0.04` incondicional a todo subtópico, sem casamento de texto.

**A taxonomia doa headings dos próprios materiais como alias de tópico** (`extraction/content_taxonomy.py:603-646`) —
auto-envenenamento medido: no IA, 5 headings foram arquivados no tópico errado e `arvores-de-decisao` pontua 8,97 no
tópico errado casando a frase que é o H2 do próprio arquivo. **Isso não vem do LLM, então sobrevive ao regime cru.**

**Camada de vocabulário:** um sidecar por curso mapeia termo → tópico. Duas origens: `.glossary_curation.json`
(hoje gerado por script de fontes do professor, 66 termos nos 7 cursos, quase tudo ruído — `chiara`, `capitulo`,
`demo`) e `.glossary_curation.llm.json` (compilado por LLM, 560 termos, 1 chamada por unidade). **O regime "cru"
mantém o primeiro e remove o segundo.**

## 3. O placar completo, medido (motor completo, rede bloqueada e contada em 0)

| eixo | NU | **CRU honesto** | VOCAB | PRODUTO |
|---|---|---|---|---|
| bloco (237) | 93,2% | **93,7%** | 93,2% | 99,2% |
| unidade (284) | 85,9% | **89,1%** | 89,8% | 92,6% |
| subunidade aceito (251) | 49,8% | **56,6%** | 87,6% | 89,2% |
| subunidade primário (251) | 33,9% | **39,8%** | 73,3% | 74,1% |

Por curso no cru (bloco / unidade / subunidade aceito): MF 89,4 / 92,4 / 79,3 · SO 92,3 / **73,0** / 60,0 ·
IA 97,6 / 100,0 / **12,8** · ES2 96,4 / 85,7 / 57,1 · TCC 96,3 / 100,0 / 72,7 · CG 94,3 / 87,1 / 62,2 ·
FR — / — / 38,9.

## 4. O QUE JÁ ESTÁ FECHADO POR MEDIÇÃO — não reproponha nada disto

| frente | resultado medido |
|---|---|
| "texto vence o bloco" sempre | **−15 no cru, −7 no produto** contra a régua curricular |
| "texto vence quando o bloco veio de método fraco" (`janela-1`/`due-*`) | +38 dentro da amostra, **−3 FORA** (LOCO, 6 folds, conjunto estável em 5 deles) |
| regra do título nomeia a unidade | refutada (−9 cru, −14 produto) |
| SARC posicional como regra de subunidade | cru 147→141, produto 224→209 |
| abstenção / margem 1º-2º / razão s2/s1 / riqueza de alias / "sem competição" | a entrega não sobe (113 → 112); teto da fronteira 66,3% de precisão com 44,6% de entrega |
| limpar tokens de mídia da doação | −2 cru, −3 produto |
| Datalab como alavanca de atribuição | 21/31 nos dois braços |
| seletor de "tópicos carentes" sem gold | não seleciona: o baseline ingênuo "maior unidade" empata em K=5 e ganha em K=10 e K=20 |
| **engenharia de bundle** | **zero no cru**: o bundle de 24 headings é entrada do COMPILADOR de vocabulário, não do motor; o scorer já lê o corpo inteiro |

## 5. Os dois experimentos de hoje que mais informam a sua resposta

**(a) Braço V — vocabulário dirigido, medido no motor completo.** Devolvi ao regime cru os sinônimos de **2 tópicos
de 1 curso** (IA: `Modelos Preditivos`, `Modelos Descritivos`, 18 termos):

| eixo | antes | depois |
|---|---|---|
| bloco | 222 | **222** (zero regressão) |
| unidade | 253 | **253** (zero regressão) |
| subunidade aceito | 142 = 56,6% | **175 = 69,7%** (+33) |
| subunidade primário | 100 | **134** (+34) |

IA: **12,8% → 97,4%**. Os outros 6 cursos, idênticos ao material. **Quando o tópico certo é curado, a conversão é
quase total: 33 de 34.** O problema nunca foi a eficácia do vocabulário — é **saber onde aplicá-lo sem o gabarito**.

**A lição de método que veio junto:** antes eu havia classificado os 109 erros por leitura e concluído que o teto da
aquisição era 32 materiais, com os erros de "competição" fechados ao vocabulário. **Medido, o vocabulário corrigiu
também os de competição.** Contagem de classe por leitura não mede teto.

**(b) O sidecar do cru tem proveniência misturada.** Congelei os 628 pares (tópico, termo) por proveniência: 60 de
script automático, **6 escolhidos MEDINDO contra a régua**, 2 vetos, 560 do LLM, **0 sem origem identificável**.
Os 6 escolhidos pelo placar valiam **+4 de subunidade e +5 de unidade** — foram removidos, e é por isso que o cru
honesto é 142 e não 146.

## 6. As restrições duras do usuário (o desenho tem que caber nelas)

1. **Nenhum eixo pode se sustentar em LLM ou API externa.** LLM é opcional; sem ele, os números têm que valer.
   (Ideia posterior dele, fora do escopo agora: OAuth da conta do próprio usuário em vez de chave de API.)
2. **Nenhum eixo pode se sustentar no gold.** O motor nunca lê arquivo de gold — isso está verificado. **Mas a
   seleção de curadoria já foi escolhida olhando a régua mais de uma vez**, e é esse vício que precisa morrer no
   desenho, não só na execução.
3. **Modular por professor.** Cada professor rotula de um jeito. Hoje só o eixo bloco tem cascata de métodos nomeados.
4. **Resync:** arquivo novo entra depois e tem que ser categorizado pelo mesmo caminho, sem recompilar nada que exija
   rede.
5. **O aluno só processa o arquivo.** Nada de curadoria manual no caminho feliz.

## 7. O QUE EU QUERO DE VOCÊ

1. **A causa real.** O usuário suspeita que estamos remendando. Concorda? **Qual é o defeito estrutural** que produz
   os erros de subunidade — e ele é um só, ou são três problemas diferentes por eixo? Use os dados das §3 e §5.
   Se a causa for a que eu já nomeei (o plano usa a CATEGORIA, o material usa a TÉCNICA), diga por que as alavancas
   de estrutura falharam todas e o vocabulário não — e o que isso implica.

2. **O alvo é alcançável sem LLM?** Responda com número, não com opinião. Se **não**, diga **qual é o teto
   determinístico** e **que informação teria que existir** (não "seria bom ter": qual campo, de qual fonte do
   professor) para que 95% fosse possível. Se **sim**, diga por onde.

3. **A arquitetura modular.** Como deveria ser o motor para acomodar "cada professor rotula de um jeito"? O eixo
   bloco já tem 12 métodos nomeados com registro de qual decidiu; os outros dois não têm. Isso é o modelo a
   generalizar, ou é ele próprio parte do problema? Como um método novo entra sem regredir os 7 cursos?

4. **Onde o vocabulário entra num desenho sem LLM e sem gold.** O braço V prova que a curadoria certa converte quase
   tudo. A pergunta que sobra é a seleção. **Existe um sinal, disponível no ato da criação da matéria, que diga quais
   tópicos vão precisar de vocabulário — antes de haver qualquer erro para olhar?** Se não existir, diga isso e diga
   o que resta (interface de curadoria? curadoria incremental guiada pelo próprio uso? outra coisa?).

5. **O primário.** Aceito 56,6% × primário 39,8% é uma distância de 17 pontos — 42 materiais em que o motor acerta
   *um* dos tópicos aceitáveis mas não o principal. **O que essa distância diz?** É desempate, é granularidade da
   taxonomia, ou é o gold que admite ambiguidade que o motor não tem como resolver?

6. **A ordem.** Dado tudo, qual a sequência de trabalho com maior ganho por risco — e **qual é o critério de parada
   de cada passo**? Diga explicitamente o que NÃO fazer.

7. **O que você não consegue avaliar** com o que está aqui, e qual medição eu deveria rodar para te dar isso.

**Regras de sempre:** MEDIDO × HIPÓTESE, evidência com `arquivo:linha`, e diga quando o dado não sustenta a conclusão.
Read-only, sem rede.
