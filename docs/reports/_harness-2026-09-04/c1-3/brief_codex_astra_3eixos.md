# Brief 5 para o astra (read-only): REVISAR A MEDICAO DOS 3 EIXOS COM O MOTOR COMPLETO — 2026-09-12, noite

Voce pediu, no brief anterior: *"Medir o motor completo nos tres eixos em copias novas, separadas da `.ablacao/`
congelada"* (passo 2 do seu plano). **Feito.** Este brief traz o resultado e pede revisao antes de eu agir sobre ele.
O usuario ja decidiu o proximo trabalho a partir desses numeros, entao um erro aqui custa caro.

Regras de sempre: MEDIDO x HIPOTESE, evidencia com arquivo:linha, diga quando o dado nao sustenta. Read-only.

---

## 1. METODOLOGIA E GUARDAS

O motor rodou INTEIRO (`reprocess_assignments.reprocess`, a mesma rota do botao "Reprocessar" da UI) em copia, uma
configuracao por vez. Instrumento: `c1-3/motor_3eixos_12-09.py` (driver) + `c1-3/mede_3eixos_12-09.py` (medidor).

  - Copia em `.motor3eixos/` (novo no .gitignore), **nunca** em `.ablacao/` — a regua congelada foi verificada
    intacta depois (manifest da copia identico ao produto no CG e no MF).
  - `use_llm_voter=False` nas tres configuracoes, pelo mesmo monkeypatch que o `scripts/motor_puro.py` usa.
  - **REDE BLOQUEADA no processo**: `socket.socket.connect` e `socket.create_connection` levantam RuntimeError.
    As tres rodaram sem excecao -> **0 chamadas**. E o voter foi confirmado off pelo manifest: nenhuma entry com
    `temporal_block_method == "llm"` nas copias, contra 1 no produto do TCC.
  - `TUTOR_NO_VOCAB_COMPILE=1` nas configuracoes sem vocabulario.
  - **Esconder o sidecar do LLM nao basta** (os sinonimos ja estao FUNDIDOS em `course/.content_taxonomy.json`), entao o
    driver tambem VETA na taxonomia compilada da copia os aliases cujo `_norm` esta no sidecar — o mesmo veto que o
    `sem_llm` do replay faz em memoria, so que persistido antes do reprocess (85 a 98 aliases por curso).
  - **Validacao do medidor:** rodado contra o PRODUTO, reproduz 99,2% / 92,6% / 89,2% / 74,1% exatos, os mesmos do
    `calibra_fila_como_regua_12-09b.log`.

**Erro meu que ja aconteceu e que voce deve considerar ao revisar:** a copia guarda UMA configuracao por vez, e a
seguinte sobrescreve. Eu li a copia achando que estava em `regua` quando ja estava em `vocab`, e a primeira lista de
erros de unidade saiu da configuracao errada. Acrescentei um marcador `_CONFIG_ATUAL.txt` e refiz. Os numeros deste
brief sao da rodada refeita.

## 2. O RESULTADO (acuracia TOTAL: todo material avaliavel no denominador; abster nao tira ninguem)

```
NU    (sem curadoria manual, sem vocab LLM)
eixo                n     ACURACIA TOTAL    precisao do confiante   cobertura  erros conf
bloco             237    221/237    93.2%       135/138     97.8%      58.2%           3
unidade           284    244/284    85.9%       147/154     95.5%      54.2%           7
subunidade        251    123/251    49.0%        68/136     50.0%      54.2%          68
subunid(prim)     251     84/251    33.5%        50/136     36.8%      54.2%          86

REGUA (curadoria humana, sem vocab LLM)  <- o que a regua chama de "cru"
eixo                n     ACURACIA TOTAL    precisao do confiante   cobertura  erros conf
bloco             237    222/237    93.7%       143/147     97.3%      62.0%           4
unidade           284    253/284    89.1%       159/162     98.1%      57.0%           3
subunidade        251    145/251    57.8%        83/141     58.9%      56.2%          58
subunid(prim)     251    103/251    41.0%        65/141     46.1%      56.2%          76

VOCAB (+ vocab LLM, voter ainda OFF)
eixo                n     ACURACIA TOTAL    precisao do confiante   cobertura  erros conf
bloco             237    221/237    93.2%       158/162     97.5%      68.4%           4
unidade           284    255/284    89.8%       166/173     96.0%      60.9%           7
subunidade        251    220/251    87.6%       136/146     93.2%      58.2%          10
subunid(prim)     251    184/251    73.3%       121/146     82.9%      58.2%          25
```

| eixo | (1) NU<br>sem curadoria, sem vocab | (2) REGUA<br>curadoria humana, sem vocab | (3) VOCAB<br>+vocab LLM, voter off | (4) PRODUTO<br>+voter |
|---|---|---|---|---|
| bloco (237) | 221 = **93,2%** | 222 = **93,7%** | 221 = 93,2% | 235 = **99,2%** |
| unidade (284) | 244 = 85,9% | 253 = **89,1%** | 255 = 89,8% | 263 = **92,6%** |
| subunidade aceito (251) | 123 = 49,0% | 145 = 57,8% | 220 = 87,6% | 224 = **89,2%** |
| subunidade primario | 84 = 33,5% | 103 = 41,0% | 184 = 73,3% | 186 = 74,1% |
| cobertura | 54,2% | 56,2-62,0% | 58,2-68,4% | 76,9-79,7% |

**O que cada camada compra, em pontos de acuracia total:**

| camada | bloco | unidade | subunidade |
|---|---|---|---|
| curadoria humana (1 -> 2) | +0,5 | **+3,2** | +8,8 |
| vocabulario do LLM (2 -> 3) | **-0,5** | +0,7 | **+29,8** |
| voter do LLM (3 -> 4) | **+6,0** | +2,8 | +1,6 |

**A leitura que eu tirei, e que quero que voce ataque:** contra a meta de 90% do usuario, **o BLOCO ja esta batido no
motor cru** (93,7%), a **UNIDADE fica a menos de 1 ponto** (89,1%, faltam 3 materiais de 284) e a **SUBUNIDADE e o unico
eixo longe** (57,8%). Ou seja, "aumentar o cru" seria uma frente de UM eixo so.

## 3. POR CURSO, configuracao REGUA (acuracia total)

| curso | bloco | unidade | subunidade |
|---|---|---|---|
| MF | 89,4% | 92,4% | 79,3% |
| SO | 92,3% | **73,0%** | 60,0% |
| IA | 97,6% | **100,0%** | **12,8%** |
| ES2 | 96,4% | 85,7% | 64,3% |
| TCC | 96,3% | 100,0% | 72,7% |
| CG | 94,3% | 87,1% | 63,4% |
| FR | — | — | 38,9% |

## 4. OS 31 ERROS DE UNIDADE NO REGIME CRU, com o recorte que decide se ha alavanca

```
ERROS DE UNIDADE no regime cru (configuracao 'regua'): 31
  o PRODUTO acerta 10 deles e tambem erra 21
  na fila do cru (o motor avisou): 28 · confiantes e errados: 3
  com conflito unidade x bloco marcado: 17

por curso:
  MF      5  (produto acerta  0 · na fila  4)
  SO     10  (produto acerta  2 · na fila  9)
  ES2     4  (produto acerta  0 · na fila  3)
  CG     12  (produto acerta  8 · na fila 12)

============================================================================================================================================
```

**Os 10 em que o CRU erra e o PRODUTO acerta** (a unica alavanca possivel do eixo unidade sem API nova):

```
  SO   laminas-cs-4244-internet-programming-sockets-programming cru=unidade-04-deadlock                          produto=unidade-03-programacao-concorrente           [fila]
  SO   laminas-sockets-material-alternativo-em-pt   cru=unidade-04-deadlock                          produto=unidade-03-programacao-concorrente           [fila] [conflito]
  CG   basico3d-cpp                                 cru=unidade-02-fundamentos-matematicos           produto=unidade-07-representacao-e-modelagem-de-objetos [fila]
  CG   basico3d-py-zip                              cru=unidade-02-fundamentos-matematicos           produto=unidade-07-representacao-e-modelagem-de-objetos [fila]
  CG   resolucao-de-prova-de-computacao-grafica-2d  cru=unidade-08-sintese-de-imagens-realisticas    produto=unidade-04-processo-de-visualizacao-2d       [fila]
  CG   resolucao-de-prova-de-computacao-grafica-2d-html cru=unidade-08-sintese-de-imagens-realisticas    produto=unidade-04-processo-de-visualizacao-2d       [fila]
  CG   exercicios-sobre-curvas-html                 cru=unidade-02-fundamentos-matematicos           produto=unidade-07-representacao-e-modelagem-de-objetos [fila] [conflito]
  CG   atividade                                    cru=unidade-04-processo-de-visualizacao-2d       produto=unidade-06-processo-de-visualizacao-3d       [fila]
  CG   video-sobre-prechimento-de-areas-duracao-330-defae7 cru=unidade-01-introducao-ao-processamento-grafico produto=unidade-03-processamento-de-imagens-e-visao-computacional [fila]
  CG   resolucao-de-prova-de-computacao-grafica-3d  cru=unidade-04-processo-de-visualizacao-2d       produto=unidade-08-sintese-de-imagens-realisticas    [fila]
```

## 5. RESSALVAS QUE EU MESMO VEJO

- **A cobertura cai muito no cru** (54-62% contra 77-80%): mais material vai para a fila. A acuracia total ja conta
  isso (o que a fila acerta entra no numerador), mas o custo de revisao sobe, e o preco da fila so esta medido para o
  produto (58 materiais revisados por 12 erros pegos = 4,8 por correcao, 79% de alarme falso).
- **`nu` nao e "sem LLM nenhum"**: `code_curation.json` (resumo de codigo do Gemini) continua na copia, e o markdown do
  acervo ja foi gerado pelos pipelines de sempre. E ablacao de curadoria e de vocabulario, nao um gerador virgem.
- As bases dos 3 eixos sao diferentes (237 / 284 / 251) e **isto nao mede acerto simultaneo nos tres**.
- O bloco do `nu` (93,2%) e quase igual ao do `vocab` (93,2%) e ao do `regua` (93,7%): o vocabulario nao ajuda o bloco, e
  chega a custar 0,5 ponto. Isso bate com o achado antigo de que "o vocab compilado mexe no bloco".

## 6. PERGUNTAS

1. **A medicao se sustenta?** Em particular: (a) o veto de aliases na taxonomia compilada da copia e equivalente ao
   `sem_llm` do replay, ou introduz diferenca (o replay veta em memoria DEPOIS de carregar; aqui o arquivo e reescrito
   ANTES do reprocess, e o reprocess pode regenerar a taxonomia); (b) `use_llm_voter=False` cobre todos os caminhos de
   LLM do reprocess, ou existe outro (residuo, descricao de imagem, resumo de codigo) que continua ligado e que eu nao
   notei porque ja havia cache; (c) a acuracia total esta bem calculada, dado que a fila entra no numerador.
2. **"O bloco ja bate a meta" se sustenta?** 93,2% no `nu` com cobertura de 54% me parece bom demais para um motor sem
   curadoria. O que pode estar inflando — o gold de bloco ser mais facil, a fila absorver os dificeis, ou a base 237
   excluir justamente os casos duros?
3. **"Faltam 3 materiais na unidade" e uma leitura honesta?** Os 31 erros tem um recorte duro: **o produto tambem erra
   21**, e **28 dos 31 estao na fila**. Entao a alavanca real seriam os 10 em que o produto acerta e o cru
   erra — 8 deles no CG. Perseguir exatamente 3 desses seria ajuste ao gold? Qual o criterio honesto para trabalhar esse
   eixo?
4. **A subunidade e o unico eixo que precisa de LLM** (+29,8 pontos, contra +0,7 na unidade e -0,5 no bloco). Isso muda
   o que voce recomendaria? Vale a pena um produto que roda cru em bloco e unidade e so chama LLM para subunidade — e,
   se sim, o que isso significa para o custo por curso?
5. **O que descartar agora**, a luz destes numeros.
