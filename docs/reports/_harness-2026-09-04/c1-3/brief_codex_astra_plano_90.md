# Brief 4 para o astra (read-only): REVISAR OS ACHADOS DO DIA E PROPOR O PLANO PARA 90/90/90 — 2026-09-12, noite

O usuario definiu a meta do produto e quer plano: **motor CRU com no minimo 90% de acuracia em UNIDADE, 90% em
SUBUNIDADE e 90% em BLOCO**. Hoje o cru esta em 58,6% de aceito na subunidade. Este brief traz tudo que foi medido hoje
(quatro rodadas, incluindo dois erros MEUS que precisei corrigir) e pede duas coisas:
(1) revisar os achados; (2) um plano — ou a demonstracao de que a meta nao e alcancavel como esta posta, e o que seria.

Regras de sempre: MEDIDO x HIPOTESE, evidencia com arquivo:linha, diga quando o dado nao sustenta. Voce esta read-only.

---

## 1. AVISO: DOIS ERROS MEUS FORAM ENCONTRADOS HOJE. Desconfie do resto na mesma medida.

**ERRO 1 — o teto do professor.** Publiquei "o teto cru e 64%, e o vocabulario do LLM estava SUPRIMINDO o teto".
Falso. `mede_fontes_do_professor.py` fazia `tops_ev = tops_limpos if LIMPO else tops`: a flag `--cru` que eu
acrescentei alimentava o conjunto de aliases vetados mas **nunca chegava ao detector**, entao `--cru` sozinho devolvia
byte a byte a linha da taxonomia do PRODUTO. Corrigido, com um modo novo `--so-llm` (sem o sidecar do LLM, curadoria
humana mantida = a taxonomia do regime cru da regua). Medido de novo, base 227, PRIMARIO:

| modo do detector | PROFESSOR | SARC | IA |
|---|---|---|---|
| taxonomia do produto (sem flag) | 146 = 64% | 85 = 37% | 37/39 = 95% |
| `--limpo` (sem sidecar manual, LLM dentro) | 138 = 61% | 80 = 35% | 37 = 95% |
| **`--so-llm` = a taxonomia do regime cru** | **100 = 44%** | **55 = 24%** | **2/39 = 5%** |
| `--cru` (sem os dois sidecares) | 85 = 37% | 44 = 19% | 0 = 0% |

**Consequencia:** o teto das fontes cruas do professor e **44% primario** e o cru esta em **41,8% primario** — a folga
e de ~2 pontos, nao 22, e ainda em base mais facil (227 exclui gold vazio e o FR). E o "bolsao do IA, cru de verdade a
87-95%", que orientou a frente inteira, era vocabulario de LLM.

**ERRO 2 — contagem de erros confiantes.** Publiquei 82; sao 77 (o bloco final do calibra contava por `motivos_de`, que
nao ve o gatilho "mudou" por `sync_changed`). 190 confiantes - 113 certos = 77.

**Ressalva de processo:** os 3 refutadores da ultima rodada morreram por limite de sessao. O que esta nas secoes 4 e 5
e **medido mas nao refutado**, exceto o que eu reproduzi com as proprias maos (marcado).

## 2. A REGUA CONGELADA (subunidade, base 251, 7 cursos; replay reproduz o produto em 251/251)

| regime | aceito | primario | confiantes | aceito do confiante | erros confiantes | entrega (confiantes certos / 251) |
|---|---|---|---|---|---|---|
| produto (vocab + LLM + curadoria) | 224 = 89,2% | 186 = 74,1% | 193 | **92,2%** | 15 | 178 = 70,9% |
| **cru** (sem sidecar LLM, curadoria humana mantida) | **147 = 58,6%** | **105 = 41,8%** | 190 | **59,5%** | **77** | 113 = 45,0% |
| so codigo de outline | 113 = 45,0% | 84 = 33,5% | 183 | 50,8% | 90 | 93 = 37,1% |

Precisao do confiante nos outros eixos, no PRODUTO (`calibra_fila_como_regua_12-09b.log`):
**bloco 188/189 = 99,5% · unidade 209/216 = 96,8% · subunidade 178/193 = 92,2% (154/193 = 79,8% pelo primario)**.

## 3. AS TRES CONFIGURACOES QUE O USUARIO PEDIU (MEDIDO hoje, `c1-3/tres_configuracoes_12-09.{py,log}`)

```
SUBUNIDADE, as tres configuracoes — REGUA INTEIRA (251 materiais, 7 cursos)
configuracao          n         aceito       primario  confiantes   aceito do confiante        entrega
(a) CRU             251    147   58.6%    105   41.8%         190    113/190    59.5%    113/251  45.0%
(b) CRU+DATALAB     251    147   58.6%    104   41.4%         190    113/190    59.5%    113/251  45.0%
(c) PRODUTO         251    224   89.2%    186   74.1%         193    178/193    92.2%    178/251  70.9%

SUBUNIDADE, so a FATIA COM DATALAB (a unica comparacao honesta de (b))
  materiais com Datalab por curso: MF 0 · SO 0 · IA 0 · ES2 0 · TCC 0 · CG 17 · FR 14  = 31 de 251
configuracao          n         aceito       primario  confiantes   aceito do confiante
(a) CRU              31     21   67.7%     16   51.6%          24     17/24     70.8%
(b) CRU+DATALAB      31     21   67.7%     15   48.4%          24     17/24     70.8%
(c) PRODUTO          31     30   96.8%     26   83.9%          23     23/23    100.0%

O QUE O DATALAB MUDA, material a material (so onde ele existe):
  CG   colisao                                        PERDE  cru=algoritmos-de-deteccao-e-calculo-de-interseccao datalab=(vazio)
  CG   instanciamento                                 troca  cru=sistema-de-coordenadas-cartesianas     datalab=recorte
  FR   08-desenvolvimento-de-aplicacoes               GANHA  cru=(vazio)                                datalab=paradigmas-clienteservidor-e-p2p
  (3 de 31 materiais com Datalab mudam de predicao)
```

**Achado que limita a coluna do Datalab: so 31 dos 251 materiais da regua tem `advanced_markdown` em disco** (CG 17,
FR 14; MF, SO, IA, ES2 e TCC tem ZERO). O handoff registrava "163 materiais nos 8 tem Datalab que o motor nunca leu" —
nos 7 cursos da regua sao 36 no manifest inteiro e 31 dentro do gold. **E onde ele existe, nao muda nada:** 3 de 31
materiais mudam de predicao, saldo zero (1 ganha, 1 perde, 1 troca).

**O que NAO consegui medir e por que:** unidade e bloco nas configuracoes (a) e (b). O replay so recomputa
`computed_subunit_slug`; `computed_unit_slug`, `temporal_block_id` e `unit_block_conflict` vem congelados do manifest do
PRODUTO. Medir os 3 eixos em regime cru exige rodar o motor inteiro (`reprocess_assignments`) em copia por configuracao.
`scripts/motor_puro.py` faz isso, mas ele sincroniza e ABLA as copias `.ablacao/`, o que destruiria a regua congelada —
nao rodei. **Entao hoje NAO existe medida de unidade nem de bloco no regime cru.** Isso e material para a pergunta 2.

## 4. POR QUE O CRU E BAIXO — a causa, medida (reproduzi a mao a secao 4.1)

### 4.1 O rotulo certo quase nunca esta escrito no material

Para cada um dos 104 erros de aceito do cru, o label do topico do gold (e seus aliases que sobrevivem ao corte) aparece
como frase no texto que o motor pontuou?

| | n | leitura |
|---|---|---|
| label inteiro presente | 3 (2,9%) | competicao: o motor viu e escolheu outro |
| alias cru presente | 1 (1,0%) | idem |
| so um token do label | 26 (25,0%) | parcial |
| **nada do rotulo** | **74 (71,2%)** | **o texto nao nomeia o topico** |

Nos 77 erros CONFIANTES: 54 sao "nada". Dos 80 que o produto acerta: 53 sao "nada".

**O padrao e sempre o mesmo: o plano usa a CATEGORIA e o material usa a TECNICA.** Amostra literal dos 74 casos
"nada" (curso, material, o que o gold queria):

```
  MF   archive-of-formal-proofs-355fb8                gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   logicaproposicional-sintaxe                    gold=linguagens-de-especificacao-e-logicas        label='Linguagens de Especificação e Lógicas'
  MF   logicaproposicional-semantica                  gold=linguagens-de-especificacao-e-logicas        label='Linguagens de Especificação e Lógicas'
  MF   arvores                                        gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   exemplos                                       gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   intro                                          gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   listas                                         gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   provas                                         gold=provadores-de-teoremas                       label='Provadores de Teoremas'
  MF   terminacao                                     gold=correcao-parcial-e-total                     label='Correção Parcial e Total'
  MF   tiposindutivos                                 gold=softwares-de-suporte-a-verificacao-formal-de-programas label='Softwares de Suporte à Verificação Formal de Programas'
  SO   1903-estruturas-de-controle                    gold=conceitos-basicos                            label='Conceitos básicos'
  SO   3103-threads                                   gold=conceitos-basicos                            label='Conceitos básicos'
  SO   exercicios                                     gold=algoritmos-de-escalonamento                  label='Algoritmos de escalonamento'
  SO   exemplo-threads-em-c-exemplo1                  gold=conceitos-basicos                            label='Conceitos básicos'
  SO   exemplo-threads-em-c-exemplo2                  gold=conceitos-basicos                            label='Conceitos básicos'
  SO   exemplo-threads-em-c-exemplo3                  gold=conceitos-basicos                            label='Conceitos básicos'
  IA   algoritmo-de-classificacao-k-nn                gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   exemplo-com-k-nn                               gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   exemplo-2-k-nn-com-iriscsv-mais-completo       gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   exemplo-de-programa-com-k-nn-em-java           gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   k-nn-para-classificacao-exemplo-cardio         gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   k-nn-para-regressao-exemplo-imc                gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   introducao-a-redes-neurais                     gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron                                gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-classificacao-de-cliente       gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-classificacao-planta-iris      gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-exemplo-atualizado             gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-or-em-python                   gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-reconhecendo-letras            gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   exercicio-2-solucao-com-rede-perceptron-atualizado gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   mlp-xoripynb                                   gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   mlp-classificacao-iris-atualizado              gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   mlp-regressao-cardio                           gold=modelos-preditivos                           label='Modelos Preditivos'
  IA   rede-perceptron-e-equacao-de-reta              gold=modelos-preditivos                           label='Modelos Preditivos'
```

**E a relacao instancia -> categoria nao esta em documento nenhum do professor:** li o plano de ensino do IA inteiro
(3.569 chars). A ementa diz "Introducao ao Aprendizado de Maquina" e **nao menciona perceptron, k-NN, MLP, k-means nem
arvore de decisao uma unica vez**.

### 4.2 As fontes posicionais do professor estao esgotadas

Inventario erro a erro, 8 fontes (plano, SARC, secao, titulo, headings, CORPO inteiro, week_label, nome original do
arquivo): **nenhuma alcanca o gold em 72 dos 104 erros (69%)**; a uniao cobre 32, e pelo criterio estrito do motor, 25.
E **alcance de fonte nao e ganho de motor**: dos 32 alcancados, so 10 teriam o topico do gold como argmax.
**Em 51 dos 98 erros testaveis o topico do gold tem score ZERO na 1a passada** — nao ha o que reordenar.

### 4.3 SARC posicional: NEGATIVO MEDIDO (o experimento que voce desenhou no §12.4)

| braco | cru: aceito / entrega / erros conf. | produto: aceito / entrega / erros conf. |
|---|---|---|
| controle | 147 / 113 / 77 | 224 / 178 / 15 |
| **SARC-A (sobrepoe quando identifica)** | **141 / 110 / 85** | **209 / 165 / 34** |
| SARC-B (so preenche predicao vazia) | 149 / 115 / 78 | 225 / 179 / 16 |

Com a **fila congelada** o sinal e o mesmo (cru 113/77 -> 109/81), entao nao e artefato de cobertura. Eixos bloco e
unidade: efeito zero por construcao (assert em 251x2x2 entries). **Causa do negativo:** no regime cru o SARC do IA
abstem em **39 de 39** por "nao nomeia nada" — as sessoes sao ricas em texto (`ml abordagem supervisionada k nn`,
`ml abordagem nao supervisionada k means`), mas nenhum rotulo do plano casa com elas sem os sinonimos do LLM.
A variante B vale +2 entregas e **so generaliza em 1 de 7 folds** do leave-one-course-out.

### 4.4 A abstencao nao aumenta o cru (fronteira medida, ~200 regras, com holdout)

**Zona gratis** (reproduzida por mim): `cobertura do topico entregue < 0,2 E peso do campo doador <= 1,1` tira 20 dos 77
erros confiantes custando 1 entrega, e no PRODUTO custa 0 e ainda tira 1 erro (92,2% -> 92,7%). Escolhida em 6 dos 7
folds. **Mas a entrega nao sobe: 113 -> 112.** O teto de toda a fronteira sem regredir o produto e precisao 66,3% com
entrega 44,6%. **A abstencao so torna a falta de vocabulario visivel.**

Fechados por medicao: margem 1o-2o (Spearman **0,948** com o proprio `winner_score` — e o piso global com outro nome,
5a refutacao), razao s2/s1, cobertura de tokens, riqueza de alias, "sem competicao".

## 5. A UNICA ALAVANCA QUE FUNCIONA, MEDIDA — e o que a impede de virar plano

Os 104 erros se concentram em 38 pares (curso, topico). **10 pares concentram 71 deles** e 62 dos 72 que nenhuma fonte
alcanca. O IA sozinho sao 2 topicos: `modelos-preditivos` (25) e `modelos-descritivos` (8).

Devolvendo vocabulario de dominio **so nesses 10 topicos**: cru **147 -> 201 aceito**, 105 -> **163 primario**, aceito do
confiante 59,5% -> **81,3%** (ganho nominal 61, perda 7). Com os **36 topicos** do gold dos erros (17% dos 217 topicos
dos 7 cursos): **222/251 aceito, 180 primario, 90,3% de aceito do confiante** — praticamente o produto (224/186, 92,2%).

**O que impede isso de ser plano: os topicos foram escolhidos OLHANDO O GOLD.** Num curso novo nao ha gold. Preciso de um
**seletor de topicos carentes que nao use a resposta** — uma regra que, olhando so o plano e os materiais, aponte quais
topicos vao ficar sem vocabulario. Os dois que testei falharam por marcar demais: "topico sem alias textual no cru"
marca 144 dos 217 topicos (66%) e "topico que nunca vence no cru" marca 137 (63%); a uniao cobre 8 dos 10 alvos mas com
171 topicos (79% do total).

## 5-bis. OS 3 REFUTADORES RODARAM (depois que eu montei as secoes acima). VEREDITO: 1 confirmado, 2 refutados.

**SARC posicional: CONFIRMADO no nucleo.** O refutador reproduziu digito a digito com script proprio, usando o
`_secao_nomeia_subtopico` do motor em vez da reimplementacao do agente original, e o negativo sobrevive a dois testes de
robustez novos: desligar a abstencao "so o pai" (cru 141/100, entrega 110) e nao deixar a regra se autodeclarar
confiante (braco A0, cobertura intacta em 190/193: cru 141/102, entrega 109).
**MAS ele corrigiu a CAUSA que eu dei, e eu estava errado:** a regra perde onde **DECIDE**, nao onde abstem. No cru o IA
e inerte nos tres numeros (aceito 5/5/5, erros confiantes 34/34/34, entrega 5/5/5); a perda inteira e **MF (-6 aceito,
-5 entrega, +5 erros), SO (-2, -1, +2) e FR (+1 erro)**, contra ES2 (+1, +2) e CG (+1, +1). No produto o IA e o SEGUNDO
MELHOR curso do braco A (entrega 36 -> 38) e a perda e ES2 -7, FR -4, SO -3, MF -2. A abstencao do IA em 39/39 explica
por que a regra nao AJUDA o alvo declarado; nao explica por que ela PERDE.

**A "folga de ~2 pontos" contra o teto: REFUTADA.** E subtracao entre conjuntos que nao se contem. Medido na mesma base
227 e na mesma taxonomia: teto PROFESSOR **100**, motor cru primario **99**, **mas so 79 sao os mesmos materiais** — o
motor acerta **20 que nenhuma das 5 fontes nomeia** e erra **21 que uma fonte do professor ja nomeia** (11 no eixo
aceito). A folga aritmetica de 1 e saldo de dois fluxos opostos de ~20. **44% nao e teto do motor em direcao nenhuma; e
alcance de detector.**
**E existe um recorte residual que minha frase negava:** dos 11 materiais em que uma fonte alcanca e o motor erra o
ACEITO, 3 ja sao colhidos pelo SARC-B, 3 vem da coluna PLANO (o rotulo esta no texto que o motor ja pontua: e scorer,
nao fonte nova) e **5 vem de SECAO/TITULO/HEADINGS, inventariados por alcance e NUNCA testados como regra de motor**:
ES2 `microsservicos6`, ES2 `roteiro8-autenticacao-autorizacao`, ES2 `devops`, TCC `aula-10-linguagens-reconheciveis...`,
CG `introducaoprocimg`. Sao 5/251 = 2,0 pp — pequeno demais para reabrir a frente, mas e esse o argumento honesto para
nao reabrir, nao a "folga de 2 pontos".

**"O vocabulario e reconstruivel": REFUTADO na conclusao.** Os numeros reproduzem byte a byte; a conclusao nao. Alcance
de fonte foi confundido com ganho de motor, e o ganho publicado so existe com ORACULO: a restauracao devolve exatamente
os aliases que a ablacao ja provou decisivos, filtrados por onde a palavra existe — um colhedor real traria tambem os
termos que atrapalham, e isso esta medido no proprio item (o braco "+corpo", com 124 aliases, DERRUBA o IA de 35 para 32
e o CG de 64 para 62). **O que sobrevive e o negativo:** o TERMO esta no acervo, mas a RELACAO termo -> topico do plano
nao esta em lugar nenhum.

**"Onde esta a informacao": REFUTADO num numero-manchete.** O agente publicou "teto cru real = 85/227 = 37%", que e o
modo `--cru` (tira os DOIS sidecares, curadoria humana inclusive). O regime cru da regua MANTEM a curadoria humana e o
numero dele e **44%** (`--so-llm`) — que e o que esta na secao 1 deste brief. A alavanca de vocabulario (147 -> 201
aceito, 81,3% de aceito do confiante) reproduz byte a byte.


## 6. AS PERGUNTAS

1. **Revise os achados das secoes 4 e 5.** Os 3 refutadores desta rodada morreram por limite de sessao; voce e a
   verificacao que sobrou. O que nao se sustenta? Em particular: o "71% dos erros o texto nao nomeia o topico" (medido
   por casamento de FRASE do label e dos aliases crus — o scorer tambem tem bonus por TOKEN, que eu nao usei no criterio);
   e a conclusao "as fontes do professor estao esgotadas" a partir de um teto de 44% medido em base diferente da regua.

2. **A META: cru com >= 90% em unidade, >= 90% em subunidade e >= 90% em bloco.** Com o que esta medido, ela e
   alcancavel sem LLM em runtime? Responda com numero, nao com opiniao: a subunidade cru esta em 58,6% aceito / 41,8%
   primario, o teto das fontes do professor e 44% primario, e a unica alavanca medida (vocabulario dirigido) chega a
   90,3% de aceito do confiante mas foi calibrada com o gold. **E qual e a metrica em que "90%" deve ser cobrado** —
   aceito, primario, ou precisao do confiante? Elas diferem em 30 pontos no mesmo motor. Diga tambem o que fazer com o
   fato de que unidade e bloco NUNCA foram medidos em regime cru (secao 3).

3. **O SELETOR DE TOPICOS CARENTES.** Esta e a peca que falta e eu quero seu desenho. A ideia: sem gold, apontar os
   topicos do plano que vao ficar orfaos de vocabulario, para pedir curadoria (humana, ou uma unica passada de LLM
   offline) SO neles. Sinais candidatos que eu consigo computar sem gold: (a) o rotulo do topico nao aparece em NENHUM
   material do curso; (b) o topico nunca vence e nunca fica em 2o lugar; (c) DESEQUILIBRIO de reparticao — numa unidade
   com N materiais, um topico leva quase todos e os irmaos ficam com zero (o colapso do IA e observavel assim, sem
   gold); (d) o rotulo e generico/categorico (poucas palavras especificas, muito "modelos", "conceitos", "tecnicas");
   (e) razao entre o n de materiais da unidade e o n de topicos da unidade. **Qual desenho voce faria, e como se valida
   um seletor desses sem usar o gold do proprio curso?** (a validacao obvia — medir se ele acerta os topicos-alvo —
   usa o gold; tem saida?)

4. **O PLANO.** Dada a meta do usuario e tudo acima, qual e a sequencia de trabalho? Inclua o que descartar. Se a
   conclusao for "90/90/90 no cru nao e alcancavel, mas 90/90/90 com uma passada offline de LLM por curso e", diga isso
   com todas as letras e diga qual e o custo por curso — o usuario esta decidindo entre motor cru e motor com API paga,
   e a secao 3 mostra que o Datalab (uma das APIs) nao compra nada.

5. **O que muda se o alvo for o PRODUTO e nao o cru?** O produto ja esta em 92,2% de aceito do confiante na subunidade,
   99,5% no bloco e 96,8% na unidade. A meta 90/90/90 ja esta batida la. **A pergunta real do usuario pode ser "quanto
   custa manter isso sem API paga"** — e nesse enquadramento, qual e a resposta medida?
