# Brief 6 para o astra (read-only): ATACAR A SUBUNIDADE — 2026-09-12, noite

Ordem do usuario: *"vamos atacar a subunidade, pois 58% e bem ruim, delegue o astra para atacar a subunidade"*.
Ele tambem definiu que os outros eixos serao polidos depois, ate perto de 100%.

**O que eu quero de voce neste brief: o PLANO DE ATAQUE da subunidade no regime cru.** Nao uma revisao — um plano, com
ordem, com o que descartar, e com o criterio de parada de cada passo. Tudo que ja foi medido (e refutado) esta aqui.

Regras de sempre: MEDIDO x HIPOTESE, evidencia com arquivo:linha, e diga quando o dado nao sustenta. Read-only.

---

## 1. ONDE A SUBUNIDADE ESTA (motor COMPLETO, nao mais o replay)

O experimento foi consertado hoje nos 3 pontos que voce apontou (gold de bloco do CG validado por data — 35/35 batem;
veto por proveniencia medido e inocuo; 4o braco com voter ligado reproduz o produto digito a digito, com contador de
rede em 0). Os numeros sao do motor rodando inteiro em copia, `use_llm_voter=False`, rede bloqueada e contada.

| eixo | NU | **REGUA (cru)** | VOCAB | PRODUTO |
|---|---|---|---|---|
| bloco (237) | 93,2% | **93,7%** | 93,2% | 99,2% |
| unidade (284) | 85,9% | **89,1%** | 89,8% | 92,6% |
| **subunidade aceito (251)** | 49,8% | **58,2%** | 87,6% | **89,2%** |
| subunidade primario | 33,9% | 41,0% | 73,3% | 74,1% |
| cobertura | 54,2% | 56,2% | 58,2% | 76,9% |

**O vocabulario sozinho vale +29,4 pontos na subunidade** (e +0,7 na unidade, -0,4 no bloco). O voter vale mais +1,6.

## 2. OS 105 ERROS, ANATOMIA (MEDIDO, `c1-3/erros_subunidade_motor_12-09.{py,log,csv}`)

```
ERROS DE SUBUNIDADE no motor completo, regime cru: 105 de 251
  o PRODUTO acerta 80 e tambem erra 25
  na FILA (o motor avisou): 47 · confiantes e errados: 58
  com predicao VAZIA: 14
  DENTRO da unidade certa (dano contido): 83 · com a unidade TAMBEM errada (dano grande): 9 · sem regua de unidade: 13

por rota que decidiu:
  1a-passada                  77  (produto acerta  56)
  propagado-headings          23  (produto acerta  21)
  rotulo-decomposto            5  (produto acerta   3)

por curso:
  MF     12  (produto acerta   9 · na fila   3)
  SO      6  (produto acerta   6 · na fila   3)
  IA     34  (produto acerta  31 · na fila   6)
  ES2    10  (produto acerta   8 · na fila   5)
  TCC     3  (produto acerta   2 · na fila   1)
  CG     29  (produto acerta  13 · na fila  23)
  FR     11  (produto acerta  11 · na fila   6)

CONCENTRACAO por (curso, topico do gold) — decide se a alavanca e dirigida ou difusa:
   1. IA   modelos-preditivos                                    25   (acumulado  25 de 105 = 24%)
   2. IA   modelos-descritivos                                    8   (acumulado  33 de 105 = 31%)
   3. MF   provadores-de-teoremas                                 6   (acumulado  39 de 105 = 37%)
   4. SO   conceitos-basicos                                      5   (acumulado  44 de 105 = 42%)
   5. ES2  estudo-de-caso-arquitetura-orientada-a-microsservicos   5   (acumulado  49 de 105 = 47%)
   6. CG                                                          5   (acumulado  54 de 105 = 51%)
   7. CG   sistema-de-coordenadas-cartesianas                     5   (acumulado  59 de 105 = 56%)
   8. FR   implementacao-de-sockets                               5   (acumulado  64 de 105 = 61%)
   9. CG   conceito-de-camera-sintetica                           4   (acumulado  68 de 105 = 65%)
  10. CG   tecnicas-de-modelagem-3d                               3   (acumulado  71 de 105 = 68%)
  11. CG   segmentacao                                            3   (acumulado  74 de 105 = 70%)
  12. MF   linguagens-de-especificacao-e-logicas                  2   (acumulado  76 de 105 = 72%)
  13. ES2  estudo-de-caso-integracao-e-implantacao-de-microsservicos   2   (acumulado  78 de 105 = 74%)
  14. CG   operacoes-com-vetores                                  2   (acumulado  80 de 105 = 76%)
  15. FR   protocolos-de-aplicacao-para-o-usuario-http-https-smtp-pop3-imap   2   (acumulado  82 de 105 = 78%)
  ... 38 pares no total

```

**Recortes que decidem o ataque:**
- **83 dos 105 estao DENTRO da unidade certa** — dano contido (o material esta na pasta certa, no subtopico
  errado). So 9 vem com a unidade tambem errada.
- **58 sao CONFIANTES** (o motor entrega errado sem avisar) e 47 estao na fila.
- **25 o produto TAMBEM erra** — nesses o vocabulario do LLM nao e a resposta.
- **77 nascem na 1a passada; 23 na propagacao por headings; 5 no rotulo decomposto.**

## 3. A CAUSA, MEDIDA — e por que as alavancas obvias ja foram fechadas

**(a) Em 71% dos erros o texto do material NAO NOMEIA o topico.** Medido sobre os 104 erros da regua do replay: o label
do gold aparece inteiro em 3, por alias cru em 1, so por token em 26, e **em 74 nao aparece nada**. (Sua correcao:
6 tem gold vazio, entao entre os 98 com topico esperado sao 68/98 = 69,4%. E meu instrumento mediu frases dos aliases
mas tokens so do label primario — "nada" e ausencia segundo aquele instrumento.)

**O padrao e sempre o mesmo: o plano usa a CATEGORIA e o material usa a TECNICA.** O plano do IA diz "Modelos
Preditivos" e os slides dizem perceptron, k-NN, MLP, arvore de decisao. Li o plano do IA inteiro (3.569 chars): a ementa
diz "Introducao ao Aprendizado de Maquina" e **nao menciona nenhuma dessas tecnicas uma unica vez**.

**(b) As fontes posicionais do professor estao inventariadas e medidas.** Teto das 5 fontes cruas (plano, SARC, secao,
titulo, headings) na taxonomia do regime cru: **100/227 = 44% primario** (e nao os 64% que eu publiquei por engano —
a flag `--cru` nao chegava ao detector). Sua correcao, que aceito: 44% **nao e teto do motor**, e alcance de detector —
na mesma base, teto 100 e motor cru 99 tem so **79 materiais em comum**, o motor acerta 20 que nenhuma fonte nomeia e
erra 21 que uma fonte ja nomeia. Dos 11 desses no eixo aceito, **5 vem de SECAO/TITULO/HEADINGS e nunca foram testados
como regra de motor**: ES2 `microsservicos6`, ES2 `roteiro8-autenticacao-autorizacao`, ES2 `devops`,
TCC `aula-10-linguagens-reconheciveis...`, CG `introducaoprocimg`. Sao 2,0 pp.

**(c) SARC posicional: NEGATIVO MEDIDO, frente fechada.** A regra literal do seu §12.4 perde nos dois regimes (cru
147 -> 141 aceito, produto 224 -> 209), e o negativo sobrevive a desligar a abstencao "so o pai" e a nao deixar a regra
se autodeclarar confiante. Sua correcao: a regra perde onde DECIDE (MF -6, SO -2), nao onde abstem.

**(d) A abstencao NAO aumenta o cru.** Fronteira completa varrida (~200 regras, com holdout leave-one-course-out): a
zona gratis (`cobertura do topico entregue < 0,2 E peso do campo doador <= 1,1`) tira 20 erros confiantes por 1 entrega
e no produto sai de graca, **mas a entrega nao sobe** (113 -> 112). O teto de toda a fronteira sem regredir o produto e
precisao 66,3% com entrega 44,6%. Fechados: margem 1o-2o (Spearman 0,948 com o proprio score — piso global com outro
nome, 5a refutacao), razao s2/s1, cobertura de tokens, riqueza de alias, "sem competicao".

**(e) A 2a passada e quase neutra no cru** (aceito do confiante 59,1% -> 59,5%) e `propagado-headings` e a rota mais
fragil (51,4% de precisao contra 59,5% da media). No produto ela e a maior alavanca. **E ela AUTO-ENVENENA:**
`content_taxonomy.py:603-646` doa headings DOS PROPRIOS MATERIAIS como alias de topico — no IA, 5 headings de slides
foram arquivados no topico errado e **nao vem do LLM, entao sobrevivem ao corte do regime cru**; `arvores-de-decisao`
pontua 8,97 no topico errado casando a frase que e o H2 do proprio arquivo.

**(f) Limpar tokens de midia da doacao: REFUTADO** (custa -2 no cru e -3 no produto).

## 4. A UNICA ALAVANCA QUE FUNCIONA — e o que a impede de virar plano

Os erros se concentram: **10 pares (curso, topico do gold) concentram 71 dos 105 (68%)**, e o IA sozinho sao 2 topicos
(`modelos-preditivos` 25, `modelos-descritivos` 8).

Devolvendo vocabulario de dominio **so nos 10 topicos**: cru 147 -> **201 aceito**, 105 -> 163 primario, aceito do
confiante 59,5% -> **81,3%** (ganho 61, perda 7). Com os **36 topicos**: **222/251 e 90,3%** de aceito do confiante —
praticamente o produto.

**MAS os topicos foram escolhidos OLHANDO O GOLD.** Num curso novo nao ha gold. E os dois seletores sem gold que testei
falharam por marcar demais: "topico sem alias textual no cru" marca 144 dos 217 topicos (66%) e "topico que nunca vence"
marca 137 (63%); a uniao cobre 8 dos 10 alvos mas com 171 topicos (79% do total).

**Voce ja deixou um desenho para isso (§18.3)**, e e o ponto de partida: priorizar topicos **sem suporte nos componentes
reais do scorer e ausentes do top-2 com score positivo**, com concentracao entre irmaos como sinal auxiliar e numero de
materiais como desempate; top-K com orcamento fixado ANTES; e a regra de ouro — *o gold entra na avaliacao, nunca na
selecao, curadoria ou ajuste do curso testado*.

## 5. O QUE EU TENHO EM MAOS PARA EXECUTAR

- `erros_subunidade_motor_12-09.csv` (105 erros com rota, fila, unidade, confianca, produto)
- `fronteira_sinais_12-09.csv` (47 colunas de sinal por material x regime: cobertura do topico entregue, peso do campo
  doador, exact_hits, share na unidade, n de candidatos com score > 0, rota, tamanho da frase que casou...)
- `congela_regua_cru_12-09.csv` (251 materiais nos 3 regimes) · `onde_esta_o_rotulo_12-09.csv` (onde o rotulo aparece)
- o motor rodando em copia por configuracao, com rede bloqueada e contada (`motor_3eixos_12-09.py`), 4 braços
- 7 cursos com gold de subunidade (251 materiais) e o LR sem gold, disponivel como curso reservado

## 6. O QUE EU QUERO: O PLANO

1. **A ordem de ataque da subunidade**, passo a passo, com criterio de parada por passo (o que faz seguir, o que faz
   abandonar). Diga explicitamente o que NAO fazer.
2. **O seletor de topicos carentes: o desenho executavel.** Quais sinais exatamente, como combina-los, qual o K, e
   **como validar sem usar o gold do curso testado**. Se a validacao honesta exigir o LR (que nao tem gold de
   subunidade), diga o que precisaria ser adjudicado e quanto — e se ha um caminho que dispensa isso.
3. **O que fazer com os 25 que o produto tambem erra** e com os 14 de predicao vazia: entram no alvo ou saem do
   denominador?
4. **Os 5 materiais de SECAO/TITULO/HEADINGS nunca testados como regra** valem um experimento, ou sao ruido a 2 pp?
5. **A 1a passada concentra 77 dos 105 erros.** Vale atacar o scorer em si (pesos por campo, degrau de 1 para 2 tokens,
   o rotulo-aspirador), ou isso ja esta esgotado pelo que foi refutado?
6. **Qual e a meta realista da subunidade no cru**, e em quantos passos — dado que o usuario quer 90% e que o
   vocabulario dirigido com gold chega a 88,4% sobre 251.
