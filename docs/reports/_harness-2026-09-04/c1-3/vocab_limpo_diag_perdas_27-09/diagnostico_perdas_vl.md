# Diagnóstico das 13 perdas da subunidade primária do VOCAB_LIMPO (27/09/2026)

**Pesquisa pós-gold.** O gold da rodada foi visto na avaliação de 26/09. Este diagnóstico explica mecanismos; não
propõe nem aplica ajuste. Qualquer mudança derivada daqui está contaminada pelos mesmos sete cursos e exige Gate próprio.

- **Autorização:** decisão do usuário de 27/09 ("fazer as 3 decisões"; diagnóstico das perdas recorrentes como pesquisa).
- **Nada alterado:** `src/`, sidecars, capturas, régua, avaliador. Sem LLM e sem rede.
- **Artefatos:** `diag_perdas_vl.py` → `diag_perdas_vl.json`; `saldo_mecanismos_vl.py` → `saldo_mecanismos_vl.json`; logs.

## 1. Método e fidelidade

- A fase real do braço VOCAB_LIMPO foi reexecutada em memória pelo mesmo caminho da captura: helpers congelados,
  taxonomia e índice dos snapshots, palco do braço e `captura.instrumenta` no pontuador do produto.
- Pré-condições conferidas: `src/` = árvore congelada, helpers = hashes congelados, módulos `src` carregados = fonte
  congelada, snapshots e palcos = congelamento, capturas = manifesto. O `.env` foi bloqueado no processo.
- **Fidelidade exigida e obtida:** pontuações da 1ª passada, chamadas posteriores e subunidade final idênticas à captura
  congelada em todos os materiais dos seis cursos afetados (MF 70, SO 42, IA 63, ES2 35, TCC 27, CG 93; 0 divergências).
- **Ablação:** para cada perda na 1ª passada, os aliases que o vocabulário acrescentou (ausentes no mesmo tópico do
  CRU_LIMPO) foram retirados um por vez e todos juntos, no tópico vencedor e no tópico certo, com os mesmos sinais e o
  mesmo pontuador.
- "Tópico certo" = a predição do CRU_LIMPO, que estava certa em todas as 13.

## 2. As 13 perdas por mecanismo

| mecanismo | onde | perdas | recorrentes da Fase 1 |
|---|---|---:|---:|
| A. Migalha de token preempta a regra de seção | 1ª passada | 4 (ES2 `roteiro5/6/7`, `roteiro7-history-service`) | 4 |
| B. Aliases acumulados no tópico vizinho, com diluição do tópico certo | 1ª passada | 4 (MF `exerciciosespecificacao` e `-respostas`, MF `verificacaomodelos`, IA `introducao-a-ml`) | 0 |
| C. Termo específico forte no título | 1ª passada | 1 (CG `slab`) | 1 |
| D. Propagação por headings na 2ª passada | 2ª passada | 3 (CG `pagina-com-videos-…`, MF `exerciciosisabelle`, TCC `aula-07-…`) | 2 |
| E. Ambiguidade nova dispara a regra de seção | 2ª passada | 1 (SO `2403-escalonamento-de-processos`) | 0 |

### A. Migalha de token preempta a regra de seção (ES2, 4)

- No CRU_LIMPO a 1ª passada não tem sinal (score 0). A regra "seção nomeia subtópico" decide então o tópico certo.
- No VOCAB_LIMPO o alias `Infraestrutura como código`, acrescentado a `conceito-de-devops`, dá score 0,1077 = 0,25 ×
  0,72 × 0,68 × 0,88. É um único token em comum, sem frase exata. Isso basta para a 1ª passada decidir, e a regra de
  seção não roda.
- Sem esse alias, os sete tópicos da unidade empatam em 0 e a 1ª passada volta a ficar sem sinal.
- Na Fase 1 o mesmo aconteceu com outro tópico (`gerenciamento-da-configuracao`): a recorrência é do mecanismo, não do
  termo.

### B. Aliases acumulados no tópico vizinho, com diluição do tópico certo (MF 3, IA 1)

O bônus de cobertura do pontuador depende da fração dos tokens do tópico presentes no material. Cada alias novo aumenta
esse denominador. Por isso o vocabulário pode baixar o score do tópico certo.

| material | vencedor: score → sem aliases novos | certo: score → sem aliases novos | aliases que mais pontuam no vencedor |
|---|---|---|---|
| MF `exerciciosespecificacao` (e `-respostas`) | 5,84 → 0,16 | 0,14 → 0,42 | `Lógica de Predicados` +3,38; `Assinatura` +1,08 |
| MF `verificacaomodelos` | 39,32 → 1,48 | 19,35 → 5,38 | `Propriedades` +6,81; `Sistemas` +6,81; `Justiça`, `fortemente justa`, `fracamente justa`, `weak fa` +4,73 cada |
| IA `introducao-a-ml` | 19,34 → 6,76 | 18,71 → 13,66 | `Aprendizado indutivo` +6,99; `Aprendizado Supervisionado` +4,51 |

- No MF, nenhum alias sozinho desfaz a perda; o vencedor acumula vários. Em `exerciciosespecificacao`, tirar todos os
  aliases novos do vencedor ainda não devolve o acerto: o certo foi diluído de 0,42 para 0,14 e a unidade vira empate.
- `Propriedades` e `Sistemas` são termos de uma palavra, genéricos no curso, e também estavam no sidecar histórico.
- No IA, tirar qualquer um dos três aliases mais fortes devolve o acerto (margem de 0,63).

### C. Termo específico forte no título (CG `slab`)

- O alias `Slab`, acrescentado a `algoritmos-de-deteccao-e-calculo-de-interseccao`, aparece no título, headings, lead e
  corpo e vale +10,91.
- O gold marca o tópico mais amplo, `algoritmos-de-geometria-computacional`. É uma divergência de granularidade; este
  diagnóstico não adjudica o gold.
- Sem os aliases novos do vencedor, o vencedor passa a ser `entidades-geometricas` (3,45), também reforçado pelo
  vocabulário. O certo foi diluído de 1,32 para 0,91.

### D. Propagação por headings na 2ª passada (3)

- A 1ª passada do VOCAB_LIMPO acerta nos três. A 2ª passada (`propagar_vocabulario_por_headings`) troca o tópico com
  scores altos vindos da taxonomia enriquecida (22,94, 22,11 e 28,05).
- É o mesmo mecanismo da CRU-05 (propagação de vocabulário entre materiais). CG `pagina-com-videos-…` e MF
  `exerciciosisabelle` já perdiam assim na Fase 1.

### E. Ambiguidade nova dispara a regra de seção (SO, 1)

- No VOCAB_LIMPO a 1ª passada acerta `escalonamento`, mas marcada como ambígua (no CRU não era).
- A ambiguidade libera a regra "seção nomeia subtópico", que troca para `conceitos-basicos`.

## 3. Saldo por mecanismo, nas 114 transições da primária (101 correções, 13 perdas)

| origem da decisão final do VOCAB_LIMPO | correções | perdas | saldo |
|---|---:|---:|---:|
| 1ª passada | 84 | 9 | +75 |
| 1ª passada sem vencedor (vazio) | 1 | 0 | +1 |
| 2ª passada, propagação por headings | 16 | 3 | +13 |
| 2ª passada, seção nomeia subtópico | 0 | 1 | −1 |

Do lado do CRU_LIMPO, os 4 acertos que vinham da regra de seção foram todos perdidos (as perdas A). A propagação e a
1ª passada têm saldo positivo grande; as perdas são o custo concentrado de mecanismos que também produzem os ganhos.

## 4. Por que 7 das 7 perdas da Fase 1 reaparecem

- Os termos gerados diferem: `Infraestrutura como código` e `Slab` não estão no sidecar histórico.
- O que se repete são materiais frágeis: acertos do CRU que dependem da 1ª passada vazia (ES2), de um tópico certo com
  pouco vocabulário próprio (CG `slab`) ou que a propagação da 2ª passada alcança (CG, MF).
- Esses mecanismos estão no motor (pontuador, regra de seção, propagação), não na geração.

## 5. Hipóteses para decisão futura (não aplicadas, não medidas)

1. Um piso para a 1ª passada decidir contra a regra de seção. O score 0,1077 vem de um só token, sem frase exata.
2. Diluição do bônus de cobertura pelo número de aliases: normalizar por frase ou por fonte do termo.
3. Aliases de uma palavra genérica no curso (`Propriedades`, `Sistemas`) e o efeito da propagação (CRU-05).

Toda hipótese daqui foi formada vendo o gold dos sete cursos. Qualquer teste precisa de pré-registro e de avaliação em
cursos que não participaram desta análise.

## 6. Limitações

- **Gold visto:** diagnóstico explicativo, não evidência para ajuste.
- **Campos em que o alias aparece:** conferência por substring normalizada, indicativa. O score em si vem do pontuador do
  produto; a contribuição de cada alias é exata para os sinais reexecutados.
- **Ablação isolada por tópico:** não simula a 2ª passada depois da troca; os efeitos da seção D ficam descritos pelos
  motivos gravados na captura.
