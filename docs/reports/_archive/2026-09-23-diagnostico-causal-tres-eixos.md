# Diagnóstico causal dos três eixos a partir do W-Z (W-Z2), 23/09/2026

Pedido literal: `_harness-2026-09-04/c1-3/wz2_pedido_usuario_23-09.md`. Estado e registro pré-medição (Q1–Q6: pergunta,
por que os artefatos não bastavam, decisão que muda): `.workflow/local/wz2-diagnostico-causal-20260923.md`.
Nada foi alterado em `src/`, testes, régua ou declarações congeladas; nenhuma regra nova; sem commit.

**Base.** A mesma do W-Z: régua v2 final + 13 materiais presentes (MF/IA/CG em `.frzero/wv_importacao_22-09`), cadeia real
`replay_bloco_21-09` → `replay_unidade_21-09`. Placar de partida 223/237 bloco, 248/284 unidade, 86/251 subunidade primária,
109/251 aceita. As 25 variantes do W-Z não foram relançadas.

**Artefatos desta entrega** (todos em `docs/reports/_harness-2026-09-04/c1-3/`):

| artefato | conteúdo | versão |
|---|---|---|
| `wz2_diagnostico_causal_23-09.py` | medição (docstring = definições pré-declaradas) | declaração sha256 `2a448326…` |
| `wz2_diagnostico_causal_23-09.json` | anexo de dados completo (por ID) | sha256 `0a7fbdee…` |
| `wz2_diagnostico_causal_23-09_anexo.md` | tabelas geradas A1–A7 | sha256 `959ac794…` |
| `.frzero/wz2_captura_base_23-09.json` | decisões base instrumentadas, congeladas antes do gold | conteúdo `f941ac33…` (arquivo `204a1ca1…`) |
| `.frzero/wz2_captura_oraculos_23-09.json` | replays dos dois oráculos | arquivo `75c6f158…` |

**Fidelidade conferida antes de qualquer conclusão:** a base instrumentada decide igual ao congelamento do W-Z em todos os
IDs (bloco, unidade, subunidade); o DP posicional recomputado reproduz o `auto_unit_slug` gravado em 125/125 blocos; o laço do
índice documental reproduz o sha do W-U (`c17786ef…`, 11.663 relações) antes de ser apontado para a base v2 (15.517 relações).

**O que foi medido de novo (e por quê):** (1) decomposição do DP posicional na população inteira e avaliação contra o gold
POR BLOCO (`tests/fixtures/eval/gold_units_<C>.csv`, que casa com os blocos dos builds por data exata; MF, SO, IA, ES2, TCC);
(2) proveniência do gold de unidade por material; (3) replay instrumentado guardando a 1ª passada da subunidade, a pontuação
de todos os tópicos e a seção do Moodle; (4) oráculo de unidade e oráculo de unidade do bloco, com o resolver real e a 2ª
passada recomputados; (5) índice documental do W-U recomputado na base v2. Nenhum desses dados existia nos artefatos do W-Z.

---

## Respostas

**1. O que o W-Z já demonstrou?** As regras de texto examinadas perdem na base v2: R2 (219/284), R1 com τ por LOCO (241, +3/−10)
e as variantes de cobertura R3/R4 (237, +1/−12). Todas derrubam a subunidade. A precedência bloco > texto sustenta acertos:
51 materiais passam pela reconciliação; 37 acertam, e em 36 deles o texto vencedor estava errado. **Novo:** 27 desses 37
acertos são julgados por gold POR MATERIAL (adjudicação ou seção), não pelo bloco — a compensação não é artefato da régua.

**2. Onde os erros nascem?**
- *Bloco* (14 erros, todos os cursos acima de 90 %, MF no limite 60/66): em 12 o bloco-gold nem entra na janela de candidatos
  do motor temporal; é falha de geração da janela, não de desempate.
- *Unidade do bloco*: o DP posicional acerta 51 de 56 blocos com gold por bloco. Os 5 erros: 2 preenchimentos sem sinal em
  fronteira de unidade (ES2 bloco-07, TCC bloco-10), 2 na janela de desvio do IA (bloco-01, bloco-02), 1 decidido pelo
  cabeçalho "Gerência do processador" (SO bloco-06).
- *Unidade do material* (36 erros): nos 5 cursos com gold por bloco os 16 erros se dividem em material de outra unidade num
  bloco certo (9), bloco com unidade errada (5) e os dois ao mesmo tempo (2). No CG (20 erros, sem gold por bloco): 9 de bloco
  temporal (4 deles herdados do resolvedor antigo quando o motor D9 se abstém), 6 de heterogeneidade não verificável, 5 em que
  texto e bloco concordam no erro ou o texto vence o vizinho errado.

**3. O que explica a maior parte dos erros de subunidade?** Dos 165 erros: **não geração 76 (46 %)** — o tópico-gold tem
pontuação zero na unidade prevista (65 com relação em outra fonte do pacote, porém ambígua; 11 sem relação no alcance
inspecionado); **seleção 67 (41 %)** — o gold é candidato ou é um assunto aceito (escolha errada 33, vários assuntos 23,
abstenção 8, alterada pela 2ª passada 3); **unidade 17 (10 %)**; **identidade 5 (3 %)**. Dar a unidade correta como oráculo
recupera só +6 líquidos (86 → 92).

**4. O que continua sem comprovação?** (a) Que algum sinal sem gold separe o assunto principal nos 67 erros de seleção sem
derrubar os 86 acertos. (b) Que relações do pacote tenham precisão útil: em 103 dos 116 erros com relação ao gold, a mesma
fonte relaciona o material a 5 ou mais outros tópicos. (c) Que "preenchimento em fronteira" seja o padrão geral de erro do DP
(n = 2 com gold; CG e FR têm 9 blocos nessa condição sem gold por bloco). (d) A extensão real da heterogeneidade: a régua de
MF/SO/IA/ES2/TCC só registra material de outra unidade onde houve adjudicação. (e) Qualquer caminho para CG +11 e SO +4 na
unidade.

**5. Próxima frente recomendada:** Frente 1, seleção do assunto principal dentro da unidade (subunidade), começando por um
experimento de discriminabilidade, sem regra. É o maior conjunto em que a resposta já está entre os candidatos (67, dos quais
43 com evidência acima do resíduo), as fontes estruturais da 2ª passada já mediram +15/−0, não depende de conhecimento externo
e é disjunta de tudo o que foi reprovado (as regras reprovadas eram de unidade).

**6. Quanto da distância ela aborda e o que fica descoberto?** A subunidade precisa de +140 (+144 somando os mínimos por curso).
A Frente 1 tem teto diagnóstico de 67 materiais; o ganho executável não é estimável antes do experimento. Mesmo no limite
ideal de todas as frentes com insumos do pacote (unidade oráculo + toda candidata convertida + toda relação do pacote
convertida, sem perdas), o teto é 234/251 (93,2 %), mas o **CG não passa de 69/82 (84,1 %)** e o SO exige converter 100 % do
endereçável. Sem corrigir a unidade, o teto total cai para 218/251 (86,9 %). Na unidade, o oráculo de bloco (intervenção ideal)
dá +4 no total e **zero no CG e no SO**.

---

## 1. W-Z consolidado e ambiguidades fechadas

### 1.1 "origem 9, homogeneidade 6, empate 3" × "origem 9, homogeneidade 9"

A segunda frase do W-Z (§7 da conclusão) somou os 3 empates à homogeneidade sem nova evidência; foi erro de redação, não
reclassificação. Os vereditos do W-Z usavam o **voto do gold dos materiais** do bloco. Agora há evidência independente
desse voto: o gold POR BLOCO (unidade anotada por aula, casada por data exata). Reclassificação por ID
(`reconciliacao_18` no JSON; tabela A5 do anexo):

| curso | material | bloco | unidade do bloco (DP) | gold do bloco | gold do material | W-Z | pelo gold de bloco |
|---|---|---|---|---|---|---|---|
| SO | `3103-threads`, `biblioteca-em-c-pthread`, `exemplo-threads-em-c-exemplo1/2/3` | bloco-04 | u02 | u02 | u03 | origem | **homogeneidade** |
| SO | `0704-exemplo-threads-em-java` | bloco-06 | u02 | **u04** | u03 | origem | origem + heterogeneidade |
| IA | `visao-geral-introducao-e-historico` | bloco-02 | u05 | u01 | u01 | origem | origem |
| IA | `ia-responsável-7c4626` | bloco-01 (herda do bloco-02) | u05 | u01 | u01 | empate | **origem** |
| ES2 | `microsservicos4` | bloco-07 | u01 | u02 | u02 | origem | origem |
| TCC | `aula-11-…-halting-problem…` | bloco-10 | u02 | u03 | u03 | origem | origem |
| MF | `eth2` | bloco-01 | u01 | u01 | u02 | empate | **homogeneidade** |
| MF | `t1-2026-1-thy` | bloco-11 (herda do bloco-10) | u02 | u02 | u01 | empate | **homogeneidade** |
| CG | `animacao-v2`, `instanciamento`, `pagina-com-videos-sobre-instanciamento`, `transformacoesgeometricas`, `transformacoesgl`, `exemplodemanipulacaodeimagens` | bloco-06 / bloco-03 | u04 / u02 | — | u05 / u03 | homogeneidade | **indeterminado** (sem gold por bloco no CG) |

Resultado: **origem 5, homogeneidade 7, indeterminado 6**. As mudanças vêm de uma única evidência: a linha do
`gold_units_<C>.csv` com a mesma data do bloco. O caso SO bloco-04 mostra o limite do voto: os 4 votos u02 eram gold
derivado do próprio bloco e os 5 votos u03 eram adjudicações; a "maioria u03" não dizia nada sobre a aula.

### 1.2 Alcance das conclusões anteriores

- "Nenhuma regra de texto" vale só para as regras examinadas: R2, R1 (τ ∈ {0,50…0,90}), R3/R4 (grade 3×3 de cobertura), além
  das já registradas no tracker ("texto vence sempre", precedência pelo método do bloco, regra do título). Não é afirmação
  sobre toda regra possível.
- Os "+4 e +2" do W-Z eram hipóteses. Agora medidos como **efeito ideal**, alimentado por gold: corrigir a unidade de todos os
  blocos para o gold por bloco dá **+4** de unidade (ES2 `microsservicos4`, IA `visao-geral…`, IA `ia-responsável…`, TCC
  `aula-11…`) e +2 de subunidade (ES2), com 0 perda. Não é ganho implantável. O "+2 no SO bloco-06" está **refutado**: o gold
  do bloco-06 é u04 (deadlock), não u03; corrigi-lo não muda nenhum acerto.
- "Maioria dos materiais" no W-Z foi constatada pelo gold, não por evidência disponível ao motor. Evidência independente do
  gold está na §2.3.

---

## 2. Unidade

### 2.1 Origem da unidade do bloco (`assign_units_positional`, `unit_matcher.py:109`)

O DP alinha blocos-aula (ordem do cronograma) a unidades (ordem do plano) maximizando a sobreposição de tokens entre o rótulo
da linha do cronograma e título/tópicos/aliases da unidade, com monotonicidade, um desvio de janela pago (`DETOUR_COST`,
`unit_matcher.py:33`), âncora exclusiva (`:169`) e âncora por radical (`:188`). A confiança 0,4 é "preenchido por posição"
(`CONF_FILL`, `:38`). Classe de cada bloco pela unidade atribuída (tabela A3 do anexo):

| classe da evidência | blocos (7 cursos) | com gold por bloco | corretos |
|---|---:|---:|---:|
| sinal próprio, máximo único | 62 | 36 | 35 |
| sinal próprio, máximo empatado | 9 | 4 | 3 |
| sem sinal (afinidade 0 em todas; preenchido pela ordem) | 50 | 16 | 13 |
| contra o máximo (ordem ou janela forçou) | 4 | 0 | — |

Mecanismos: DP puro 114, desvio de janela 8 (IA 7, CG 1), âncora 3. Contra o gold: desvio 5 certos e 2 errados (os dois no
IA); âncora 1 certa; cabeçalho decisivo (o título da unidade decide e sem ele o bloco não seria máximo) 9 certos e 1 errado.

- **Quando funciona:** preenchimento sem sinal no interior de uma sequência (unidade anterior = seguinte) acerta 11 de 12;
  sinal próprio único acerta 35 de 36.
- **Quando falha:** preenchimento em fronteira de unidade, 0 de 2 (ES2 bloco-07 "microserviços no Spring, circuit breaker";
  TCC bloco-10 "halting problem"); a janela de desvio que leva o IA para u05 cedo demais (bloco-02 "visão geral da IA" e o
  bloco-01 de plano de ensino); o cabeçalho "Gerência do processador" no SO bloco-06, que vence "sincronização" (u03) e
  "deadlock" (u04, o gold).
- **Quantos acertos dependem do preenchimento:** 60 materiais com gold caem em bloco preenchido (ou herdam dele); 55 acertam.
  Em 35 o texto concorda e o bloco é irrelevante. **Dependem do bloco preenchido 25: 20 acertos** (ES2 10, IA 7, MF 2, TCC 1) e
  5 erros (IA 2 da janela, ES2 1 e TCC 1 de fronteira, MF `eth2` com bloco certo).
- **O que diferencia os erros:** posição (fronteira vs interior) e a janela de desvio. É indício, não demonstração: n = 2 em
  fronteira com gold; CG e FR têm 9 preenchimentos em fronteira sem gold por bloco. Afinidade zero sozinha não discrimina
  (13 de 16 acertam). O contexto institucional diz que "afinidade-zero é rara" (`.mex/context/institutional.md:80`); medido,
  são 50 de 125 blocos-candidatos (40 %). Contexto obsoleto a corrigir.

Por que a afinidade zera nos casos de erro (tokens do próprio `unit_matcher`):
IA bloco-02 "visão geral da IA" — "visão" e "geral" estão no filtro genérico e somem também do título da u01 (artefato do
filtro, não de idioma); ES2 bloco-07 — "microservicos" (grafia do cronograma) ≠ "microsservicos" (plano), e "circuit breaker"/
"spring" não têm frase no plano; TCC bloco-10 — "halting problem" (inglês) contra "problema da parada" (plano).

### 2.2 Herança e homogeneidade: o que `unit_slug` significa hoje

- **No código**, `unit_slug` do bloco é a unidade atribuída à aula pelo alinhamento posicional; blocos que não são aula ficam
  sem unidade (`timeline/index.py:79-80`) e o material herda do vizinho de conteúdo (`file_map.py:873`). Na
  reconciliação, quando o bloco tem unidade própria e o texto discorda sem exceção aplicável, **o bloco vence** (`file_map.py:856-868`).
  O comentário de 21/08 diz que "a verdade de unidade é, por construção, a unidade do bloco (ground_truth ⋈ gold_units)".
  O código trata `unit_slug` como unidade obrigatória de todos os materiais do bloco.
- **No contrato**, desde 12/09 a régua é curricular: "unidade = onde o plano põe o assunto, não quando a aula foi dada"
  (`scripts/eval_entry_unit.py:62-66`); o bloco é vínculo temporal (parecer do Astra, `pendencias.md:1932`). O contexto
  institucional de 17/06 (`institutional.md:218-226`) propunha o contrário ("o bloco/agendado vence") e está superado.
  Pelo contrato, `unit_slug` é **contexto usado como aproximação** da unidade curricular do material.
- **Custo medido da aproximação** (5 cursos, 189 materiais em blocos com gold por bloco, relativo ao bloco em que o material
  caiu): bloco certo e material da mesma unidade 167 (todos acertam); bloco certo e material de outra unidade 10 (1 acerta);
  bloco errado e material igual ao gold do bloco 7 (2 acertam); bloco errado e material de outra unidade 5 (3 acertam).
- **O que o modelo representa:** uma unidade por bloco; exceções por material só via pino manual, número explícito de unidade,
  seção corroborada (`resolver_apply.py:469-473`) e texto contra vizinho. Existe um eixo de cobertura 1:N (`coverage_units`),
  mas ele não alimenta a unidade 1:1 nem a subunidade. **O que perde:** blocos mistos (SO bloco-04: 4 materiais u02 e 5 u03;
  CG bloco-06: u04 hospedando 5 materiais que o usuário decidiu serem u05). Nesses casos a subunidade é restrita à unidade
  errada (família F2, §3).
- Não se presume reescrita nem campo novo: o oráculo de unidade mostra que acertar a unidade vale +6 de subunidade (§3.3), e a
  heterogeneidade observável nos 5 cursos são 15 materiais.

### 2.3 Seções, corpus e circularidade

- **Proveniência do gold de unidade** (284): 134 vêm do bloco-gold (ground_truth ⋈ gold_units, MF/SO/IA/ES2/TCC); 150 são por
  material (CG 93, ES2 19, SO 19, MF 13, IA 3, TCC 3), dos quais 62 por decisão do usuário, 60 propostos a partir da seção do
  Moodle (CG), 23 propostos por leitura, 5 por conteúdo. Consequência: **nos 5 cursos, a régua só vê heterogeneidade onde houve
  adjudicação**; nos demais materiais "material = bloco" vale por construção.
- **Evidência independente do gold**, por bloco, só com sinais pré-reconciliação (não leem o bloco): maioria do texto bruto
  acima do gate e maioria da seção do Moodle. Nos blocos em que o DP acerta, a maioria do texto coincide com o gold do bloco em
  29, diverge em 8, empata em 2, não existe em 5; a da seção coincide em 13 e não existe em 31. Nos 5 blocos em que o DP erra,
  o texto aponta o gold em 2 (IA bloco-02 e TCC bloco-10, blocos de **um** material, em que "maioria" é o próprio texto — a
  família "texto vence" já reprovada) e diverge em 3 (SO bloco-06 aponta u03, a unidade dos materiais, não u04). Estimar a
  unidade do bloco pelo voto dos materiais consertaria 2 e arriscaria 8: não há sinal de bloco sem gold que discrimine.
- **Circularidade:** usar a unidade final dos materiais para inferir a do bloco é circular (ela vem do bloco). Só sinais
  anteriores à reconciliação são admissíveis. No CG, 60 golds de unidade foram propostos a partir da seção do Moodle: qualquer
  frente baseada em seção pontua bem no CG por construção da régua e precisa ser validada nos outros cursos.
- **Aliases EN/PT:** o par "halting problem" ↔ "problema da parada" está no próprio pacote (título do material "O Problema da
  Parada (Halting Problem, Halteproblem)"), com proveniência — relação lexical admissível, que não depende da unidade do
  material. "Circuit breaker"/"Spring" → implantação (u02) não aparece em nenhum insumo inspecionado: exigiria conhecimento
  externo. "microservicos"/"microsservicos" é variação de grafia, não de idioma.

### 2.4 Os 36 erros de unidade e as metas por curso

| classe (anatomia v2) | n | mecanismo reclassificado |
|---|---:|---|
| bloco certo, gold diverge | 18 | pelo gold de bloco: origem 5, homogeneidade 7, indeterminado 6 (CG) |
| bloco errado | 11 | bloco temporal errado com gold 4 (CG `basico3d-cpp`/`-py-zip`, SO `laminas-sockets…`, ES2 `azure`); **fallback do resolvedor antigo** 4 (CG 3 `resolucao-de-prova-…` e `exercicios-sobre-curvas-html`: o D9 não deu bloco temporal e a unidade herdou o `computed_block_id`); material sem bloco no gold que recebeu bloco 3 (CG) |
| texto vence errado | 7 | texto e bloco concordam no erro 4 (CG `morfologiamatematicapptx`, página de morfologia, vídeo de preenchimento; MF `aws-encryption-sdk`); texto vence o vizinho errado 3 (CG `openglbasico`, `texturas-v3`; IA `…oracle…`) |

O fallback do resolvedor antigo alcança 13 materiais no laço (9 com gold: 5 acertos, 4 erros), via
`resolve_temporal_block` → `resolve_effective_block` (`file_map.py:745`). Nos 9, o texto sozinho acima do gate acertaria 3
(CG `exercicios-teoricos-sobre-processo-de-visualizacao`, `exerciciosfundamentosmatematicos`, `exercicios-sobre-curvas-html`) e
se absteria nos outros 6. Hoje o fallback rende 5 acertos contra 3 do texto. É estimativa direta, sem replay; a subunidade e a
2ª passada também mudariam.

**Metas.** Total +8 (256): o único efeito medido é o ideal do oráculo de bloco, +4. **SO +4** (30 → 34): dos 7 erros, 5 são a
família threads no bloco-04 (homogeneidade; o texto bruto acerta 2, os 3 `exemplo-threads-em-c-*` têm vencedor bruto u07), 1 é
origem + heterogeneidade no bloco-06 (corrigir o bloco para u04 não ajuda) e 1 é bloco temporal errado. Nenhum caminho
demonstrado. **CG +11** (73 → 84): 20 erros, sem gold por bloco, 9 dependentes de bloco temporal ou do fallback; nenhum caminho
demonstrado.

### 2.5 Eixo bloco

14 erros (MF 6, SO 3, CG 2, IA 1, ES2 1, TCC 1; tabela A2). Métodos: desempate 9, janela única 3, sem decisão temporal 2 (SO
`definicao-e-historico`, TCC `t1-enunciado`). O bloco-gold está dentro da janela considerada só em 2 (CG `basico3d-*`): nos
outros 12 o erro é de geração da janela. Todos os cursos passam de 90 %; MF está exatamente no mínimo (60/66), então qualquer
frente precisa preservar o bloco do MF. Não proponho frente de bloco.

---

## 3. Subunidade (prioridade)

### 3.1 O que é "subunidade primária" operacionalmente

É o tópico do plano sobre o qual o material principalmente trata, anotado por material: 197 dos 251 por conteúdo (título,
headings, maioria das questões), 19 pelo título, 15 pelo card, 8 pelo label do Moodle, 7 por oráculo, 5 por decisão do usuário.
As notas da régua explicitam o critério: "primário = nomeado no título e tópico próprio", "tópico guarda-chuva", "maioria das
questões". 112 dos 251 (45 %) têm assuntos extras aceitos: material com vários assuntos é a regra, e o primário precisa ser
distinguido. Sinais disponíveis ao motor: título e nome do arquivo, headings e primeiro parágrafo (pesos 3,8/4,4/2,8 contra 1,1
do corpo, `timeline/index.py:1859`), partes do rótulo do plano e seção do Moodle (só na 2ª passada). O label/seção do Moodle não
entra no pontuador da 1ª passada.

### 3.2 Anatomia dos 165 erros (base v2, famílias pré-declaradas; cada material conta uma vez)

| curso (acertos/n; mínimo >90 %) | F1 identidade | F2 unidade | F5 alterada depois | F8 vários assuntos | F4a abstenção | F4b escolha errada | F6 relação fora do índice | F7 relação não encontrada |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MF (25/58; 53) | 0 | 0 | 0 | 4 | 2 | 10 | 14 | 3 |
| SO (7/15; 14) | 0 | 4 | 0 | 1 | 0 | 0 | 2 | 1 |
| IA (4/39; 36) | 0 | 0 | 0 | 1 | 0 | 4 | 30 | 0 |
| ES2 (7/28; 26) | 0 | 3 | 0 | 1 | 0 | 7 | 10 | 0 |
| TCC (7/11; 10) | 0 | 0 | 1 | 2 | 1 | 0 | 0 | 0 |
| CG (30/82; 74) | 5 | 10 | 0 | 13 | 3 | 6 | 8 | 7 |
| FR (6/18; 17) | 0 | 0 | 2 | 1 | 2 | 6 | 1 | 0 |
| **total** | **5** | **17** | **3** | **23** | **8** | **33** | **65** | **11** |

Sobreposições registradas como marcas, sem recontar: 8 dos 23 F8 têm o gold com pontuação zero (também "não gerados"); 16 dos
67 de seleção têm o gold só com pontuação residual (< 0,05, o 0,0172 de token solto), ou seja, candidatos só no nome; slug
duplicado 1; "vários assuntos competitivos" (≥ 2 candidatos com pontuação ≥ 50 % do vencedor) em 56 erros e 22 acertos.
Indeterminados e fora da fase: 0.

- **F1 (5)** são todos do CG e são uma **incoerência da régua**: `animacao-v2`, `instanciamento`,
  `pagina-com-videos-sobre-instanciamento`, `transformacoesgeometricas` e `transformacoesgl` têm subunidade-gold vazia anotada
  em 06/09 sob a u04 ("u04 não tem subtópico → vazio"), mas a régua v2 (22/09) passou a unidade deles para u05, que tem
  "transformações geométricas". Não alterei a régua; é decisão sua.
- **F2 (17)**: a unidade prevista exclui o gold (SO 4 threads, ES2 3 microsserviços, CG 10). Em 4 o texto bruto de unidade
  apontava a unidade certa e foi descartado pela reconciliação; em 7 o eixo de cobertura já continha a unidade do gold.
- **F6 (65)** por fonte de alcance: só o índice documental 33 (IA 22), documental + radical 8 (IA), seção 6, bloco + seção 11
  (MF), documental + seção 5 (ES2), outros 2. **F7 (11)**: MF 3, SO 1, CG 7 (OpenGL/câmera sintética, mapeamento).

### 3.3 Quanto a unidade explica (oráculo)

O oráculo de unidade cobriu 294 materiais com gold coerente (245 pela subunidade, 49 só pela unidade; 13 sem oráculo). Com a
unidade certa, o resolver real e a 2ª passada recomputados:

| modo | unidade | sub primária | sub aceita | mudanças de sub primária |
|---|---:|---:|---:|---|
| base | 248 | 86 | 109 | — |
| oráculo de unidade (por material) | 283 | **92** | 116 | +8 (CG 6, ES2 2) / −2 (CG `bezier-py`, `bezier-python`, efeito colateral da 2ª passada) |
| oráculo de bloco (unidade do bloco = gold por bloco) | 252 | 88 | 110 | +2 (ES2 `microsservicos4`, `roteiro4`) / 0 |

**Persistem 159 erros com a unidade certa** (F6 70, F4b 35, F8 24, F7 13, F4a 10, F1 4, F5 3). O SO não ganha nada: os 4 de
threads, já em u03, continuam sem pontuação para `programas-multithreads` (viram F6/F4b). São efeitos diagnósticos de
intervenção ideal: não são regra, não são teto universal e não se somam.

### 3.4 A resposta certa já está entre os candidatos?

Nos 165 erros, o gold tem pontuação > 0 entre os tópicos da unidade prevista em **59** (em 16 só com resíduo < 0,05; **43 com
evidência real**), em qualquer unidade em 64, e por radical em 73. Posição do gold entre os candidatos: 2º lugar 23, 3º 8, 4º–6º
21, pior 4, 1º 3 (perdido depois); não candidato 106. Nos 86 acertos, o gold é o 1º colocado entre os candidatos em 61; nos
outros 25 ele chega pela 2ª passada ou pela seção, ou o acerto é uma abstenção correta (1). Com a unidade oráculo, 64 dos 159 erros têm o gold entre os candidatos.

### 3.5 Segunda passada: efeito direto × dependência entre materiais

A 1ª passada acerta 64; a 2ª mantém 60, perde 4 e ganha 26: **resultado líquido +22** (86 = 64 − 4 + 26).

| fonte da 2ª passada (`resolver_apply.py:262-360`) | ganhos | perdas | proveniência |
|---|---:|---:|---|
| partes do rótulo do plano (`_partes_de_rotulo`, `:183`) | 10 | 0 | plano de ensino |
| seção do Moodle nomeia um tópico (`_secao_nomeia_subtopico`, `:239`, último recurso) | 5 | 0 | estrutura do professor |
| propagação de vocabulário de materiais confiantes (`:262`) | 11 | 4 | outros materiais do curso |

A propagação é dependência **legítima** quando os doadores estão certos (MF especificação recursiva: 4 de 5 doadores com gold
certos → 7 ganhos, 1 perda; SO chamadas de sistema: 2 de 2 → 3 ganhos). É **propagação sem suporte** quando a 1ª passada é
confiante e errada: IA "introdução ao aprendizado de máquina" tem 30 doadores, 27 com gold e só 3 certos (11 materiais movidos,
0 ganho); FR "paradigmas cliente-servidor", 0 de 4 certos (2 perdas: `04-protocolo-http`, `unidade2-exercicios-http`); ES2 0 de
2 (4 movidos sem ganho).

### 3.6 Evidências disponíveis descartadas antes da seleção

| evidência | uso atual | aponta o gold nos erros | aponta o gold nos acertos | ambiguidade |
|---|---|---:|---:|---|
| texto bruto de unidade acima do gate | descartado quando o bloco tem unidade (`file_map.py:856-868`) | 4 dos 17 F2 | — | ver R1–R4 |
| eixo de cobertura (`coverage_units`, 1:N) | não alimenta a subunidade | 7 dos 17 F2 | — | lista várias unidades |
| radical (stem6) | só na rota de unidade (`file_map.py:536-543`) | 73 | 77 | resgata 8 não gerados, todos também documentais |
| seção do Moodle | só último recurso da 2ª passada | 38 | 25 | quando nomeia um único tópico: gold em 3/22 erros e 14/22 acertos |
| tópicos do bloco no cronograma (`topic_candidates`) | não usados | 44 | 59 | nos erros, sempre entre ≥ 5 candidatos |
| índice documental (W-U, P1–P4) | não usado | 116 | 72 | 103 dos 116 com ≥ 5 tópicos concorrentes |

A evidência existe para a maior parte dos erros, mas quase sempre aponta também para muitos outros tópicos: é recall sem
precisão, o mesmo achado do W-U, agora na base v2.

### 3.7 Teto estrutural por curso (limite ideal, não previsão)

Sem caminho demonstrado com insumos do pacote: F1 (régua) e F7 (relação ausente); na base, também F2.

| curso | mínimo | teto na base | teto com unidade oráculo |
|---|---:|---:|---:|
| MF | 53 | 55 | 55 |
| SO | 14 | **10** | 14 (exige 100 % do endereçável) |
| IA | 36 | 39 | 39 (exige converter 30 de 30 F6) |
| ES2 | 26 | **25** | 28 |
| TCC | 10 | 11 | 11 |
| CG | 74 | **60** | **69 (84,1 %)** |
| FR | 17 | 18 | 18 |
| total | 226 | **218 (86,9 %)** | 234 (93,2 %) |

---

## 4. Mapa de dependências, exemplos e controles

```
Cronograma SARC (linha: data, atividade, descrição) ─► blocos (kind, topic_text, sessões)
Plano de ensino ─► taxonomia (unidades → tópicos, aliases) ─┐
blocos × taxonomia ─► DP posicional (unit_matcher.py:109) ─► unit_slug do bloco (0,4 preenchido | 0,6/0,8 sinal)
Manifest (data, seção, título) + blocos ─► motor D9 (janela → desempate) ─► bloco temporal do material
                                         └─ D9 se abstém ─► computed_block_id do resolvedor antigo (file_map.py:745)
Texto do material ─► vencedor bruto de unidade (gate 0,50) ─┐
reconcile (file_map.py:779): bloco manual > unidade manual > seção corroborada > texto vazio herda > número explícito
                             > vizinho → texto > BLOCO VENCE
unidade final ─► tópicos só dessa unidade (file_map.py:186) ─► 1ª passada (pontuação exata; título/heading/lead ≫ corpo)
1ª passada confiante (≥ 0,7) ─► vocabulário doado + partes de rótulo ─► 2ª passada (só indecisos) + título + seção
```

**Exemplos completos** (fonte → decisão → erro → propagação):

1. SO `3103-threads`. Cronograma 19–31/03 "Gerência do processador: processos, chamadas de sistema, escalonamento…" → DP u02
   (afinidade 3 contra 1; gold do bloco u02, certo) → texto bruto u03 (0,58, acima do gate) → reconciliação: o bloco vence → u02,
   errado (gold do material u03, adjudicado) → subunidade restrita a u02 exclui `programas-multithreads` (F2) → com a unidade
   oráculo u03, `programas-multithreads` segue com pontuação zero (F6). Heterogeneidade + não geração.
2. TCC `aula-11-o-problema-da-parada…`. Cronograma "halting problem aula" → afinidade zero (o plano diz "problema da parada")
   → DP preenche pela ordem na fronteira u02|u03 → u02 (gold do bloco u03) → texto bruto u03 (0,60) perde para o bloco →
   unidade errada. O oráculo de bloco corrige (+1). A relação EN↔PT está no título do próprio material.
3. IA `artigo-usando-k-nn-em-texto` (subunidade). Unidade u05 certa (bloco preenchido no interior, controle de unidade
   correto) → tópicos da u05 são categorias ("modelos preditivos") e o material fala de k-NN → gold com pontuação 0,12, 3º
   lugar → 1ª passada confiante em "introdução ao aprendizado de máquina" → 2ª passada propaga com 27 doadores, 3 certos (F4b,
   propagação sem suporte).
4. CG `resolucao-de-prova-de-computacao-grafica-2d`. O D9 não dá bloco temporal → a unidade cai no `computed_block_id` do
   resolvedor antigo (bloco-01, u01) → herdada, errada (gold u04).

**Controles hoje corretos:**
- Preenchimento no interior: IA `exemplo-de-programa-com-k-nn-em-java`, `introducao-a-redes-neurais` (bloco-05, u05) e MF `plano`
  (bloco-01) herdam de bloco sem sinal e acertam.
- Compensação com gold por material: ES2 `microsservicos7` (texto u01 → bloco u02, decisão do usuário u02) e SO
  `exemplo-criacao-de-processos-no-unix-linux-teste01/02/03` (texto u03 → bloco u01, decisão do usuário u01).
- Subunidade no 1º lugar pelo título/headings: MF `formalizacaoalgoritmos-recursao2`, `logicapredicados-sintaxe`.
- 2ª passada legítima: MF `provasindutivas-especificacoesrecursivas` (propagação com 4 de 5 doadores certos).

---

## 5. Frentes (até três, por evidência, alcance e risco)

### Frente 1 — Subunidade: seleção do assunto principal entre candidatos gerados (recomendada)

- **Causa:** o gold é candidato ou assunto aceito e perde a seleção (F4 41, F8 23, F5 3 = 67; 43 com evidência acima do resíduo).
- **A favor:** acertos concentrados no 1º lugar (61/86); gold em 2º lugar em 23 erros; fontes estruturais da 2ª passada mediram
  +15/−0 (rótulo do plano, seção); o pontuador já dá peso maior a título e headings.
- **Contra:** 16 dos 67 só têm pontuação residual (não são candidatos de fato); pai × filho foi fechado por medição em 13–14/09
  (nenhuma regra de parentesco separa erros de controles); "vários assuntos competitivos" também marca 22 acertos; seção com um
  único tópico tem 39 % de precisão.
- **Mecanismo geral:** decidir o primário pelo papel estrutural da evidência (frase completa em título/heading/lead contra
  menção no corpo) e só propagar vocabulário na 2ª passada a partir de doadores cuja própria decisão tenha evidência estrutural.
  Sem gold, sem lista, sem parâmetro por curso.
- **Diferença do reprovado:** R1–R4 mexiam na unidade; W-P2/W-S eram perguntas ao professor (descartado); pai × filho testou
  parentesco. Ordenação por papel do trecho nunca foi medida.
- **Atingidos:** MF 16, CG 22, FR 11, ES2 8, IA 5, TCC 4, SO 1 (sobreposição: 8 dos F8 também são não gerados).
- **Alcance:** bloco 0, unidade 0; subunidade com teto diagnóstico de 67; ganho executável **não estimável ainda**.
- **Ameaçados:** os 86 acertos, sobretudo os 26 que só existem pela 2ª passada.
- **Custo:** seletor da subunidade (`file_map.py:174-262`) e 2ª passada (`resolver_apply.py:262-360`); nenhum dado novo.
- **Menor experimento:** medição 0 src (proposta de Gate 1, §7).
- **Aprovação:** critério com precisão > 50 % nos 86 acertos e saldo positivo nos 67, depois replay integral com 0 perda, nenhum
  curso regredindo e bloco/unidade idênticos. **Refutação/encerramento:** nenhum critério pré-declarado atinge a precisão ou o
  saldo em LOCO é ≤ 0 → a família "seleção por papel estrutural" fecha.

### Frente 2 — Subunidade: relação tópico ↔ vocabulário do material a partir do pacote, com proveniência

- **Causa:** o gold tem pontuação zero, mas outra fonte do pacote liga uma expressão do material ao tópico (F6 65: IA 30, MF 14,
  ES2 10, CG 8, SO 2, FR 1).
- **A favor:** 65 dos 76 não gerados têm relação no alcance inspecionado; quando a relação é fornecida a conversão é alta (braço V
  de 13/09: 2 tópicos do IA, +33 — mas dirigido por gold).
- **Contra:** a relação é ambígua: 103 dos 116 erros com relação ao gold também ligam a 5 ou mais outros tópicos; tópicos do
  bloco sempre entre ≥ 5; W-U já mostrou 177/179 conflitantes. Mexer em aliases muda a pontuação de todos os materiais.
- **Mecanismo:** aceitar só relações exclusivas e ponderadas por proveniência (linha do plano/syllabus sob o heading do tópico >
  hierarquia de headings de outro material > mesma linha), entrando pelo canal de aliases da 2ª passada.
- **Diferença:** o W-U mediu só a existência de relação; o critério de seleção nunca foi medido. É o portão já registrado no
  tracker: precisão > 50 % nos acertos antes de qualquer Gate 1 de mecanismo.
- **Alcance:** subunidade com teto diagnóstico de 65; bloco e unidade 0. **Ameaçados:** os 86 acertos.
- **Menor experimento:** sobre o índice v2 já congelado neste JSON (`sha256_indice_documental`), pré-declarar exclusividade + peso
  por padrão; medir precisão nos 86 e recall nos 65, com LOCO; parar se a precisão ficar ≤ 50 %.
- **Fica fora:** F7 (11) e o elo categoria ↔ algoritmo do IA, se a precisão falhar → regime de conhecimento externo (§6).

### Frente 3 — Unidade: origem do bloco nas fronteiras, na janela de desvio e no cabeçalho

- **Causa:** 5 blocos com unidade errada pelo gold por bloco (2 fronteiras sem sinal, 2 na janela de desvio do IA, 1 cabeçalho).
- **A favor:** efeito ideal medido +4 unidade e +2 subunidade, 0 perda; preenchimento no interior acerta 11/12; cabeçalho
  acerta 9/10.
- **Contra:** n minúsculo (2 fronteiras com gold); CG e FR sem gold por bloco (9 fronteiras sem verdade); não alcança SO nem CG;
  afinidade zero sozinha não discrimina; o voto dos materiais não serve de estimador (§2.3).
- **Mecanismo:** nas fronteiras e na janela, usar só evidência pré-reconciliação e com proveniência do pacote (pares de termos
  que o próprio pacote justapõe, como "problema da parada (halting problem)"; revisar o filtro genérico que apaga o título da
  unidade, como "visão geral").
- **Alcance:** unidade teto ideal +4 (ES2 1, IA 2, TCC 1); subunidade +2 (ES2); bloco 0. **Ameaçados:** 20 acertos que dependem
  de preenchimento (ES2 10, IA 7).
- **Menor experimento:** listar todas as fronteiras preenchidas (7 cursos), medir quantas têm par de termos no pacote e se
  isso aponta a unidade do gold por bloco nos 5 cursos com gold, sem tocar nos blocos de interior.
- **Aprovação:** replay com 0 perda. **Encerramento:** sem par de termos com proveniência nas fronteiras ou com perda em LOCO.

---

## 6. Lacuna restante e conhecimento externo

- **Subunidade:** faltam +140 (+144 por curso). As Frentes 1 e 2 têm tetos diagnósticos de 67 e 65, que não se somam como
  previsão e exigiriam conversão quase integral sem perdas. Mesmo no limite ideal, o CG fica em 84,1 % e o SO exige 100 %
  do endereçável. **Parcela sem caminho demonstrado:** F7 (11; 13 com unidade oráculo), F1 (5, dependente de decisão da régua) e,
  sem correção de unidade, F2 (17).
- **Unidade:** faltam +8 no total, +11 no CG e +4 no SO. Só +4 medido como ideal, nenhum no CG ou no SO.
- **Bloco:** meta cumprida em todos os cursos; MF no limite.

**Regime separado (não autorizado; só para decisão):** falta a relação entre o vocabulário do material (algoritmos, termos em
inglês, ferramentas: k-NN, perceptron, circuit breaker, OpenGL, câmera sintética) e os rótulos-categoria do plano. O pacote não
a fornece porque os documentos do professor param antes do rótulo do plano (tracker, 14/09) e, quando a relação existe, ela é
ambígua. Fornecê-la sem professor custaria um tesauro por área, versionado e auditável, ou uma etapa de compilação de
vocabulário por LLM, que já existe (`compile_vocabulary` está ligado nos seus cursos) mas viola o contrato do cru. Risco comum:
ajuste ao benchmark, como no braço V.

---

## 7. Proposta de Gate 1 (medição, 0 src, sem commit)

**W-AA — discriminabilidade do assunto principal (Frente 1).**

1. **Pergunta:** existe critério sem gold que separe o primário do vencedor atual nos 67 erros de seleção sem derrubar os 86
   acertos? Artefatos atuais não bastam: não guardam **em que campo** cada frase de tópico pontuou.
2. **Insumo:** as capturas congeladas do W-Z2 mais uma instrumentação da 1ª passada que registra, por candidato, a pontuação por
   campo (título, arquivo, heading, lead, corpo, tags), com o mesmo coletor de sinais.
3. **Critérios pré-declarados, no máximo dois, sem grade:** C1 "o primário é o candidato com frase completa em título ou heading;
   empate → maior pontuação atual"; C2 = C1 + a 2ª passada só propaga a partir de doadores que satisfazem C1.
4. **Medida:** precisão nos 86 acertos, ganhos e perdas por ID nos 67, LOCO se surgir parâmetro, e replay integral dos 3 eixos
   para o critério que passar.
5. **Decisão:** abrir Gate 1 de implementação só com saldo > 0, 0 perda, nenhum curso regredindo e bloco/unidade idênticos;
   caso contrário a frente fecha e a próxima medição é a da Frente 2 (precisão do índice documental).

Estimativa: um replay instrumentado (~7 min por modo) e a avaliação. Executor: Opus, conforme `routing.md` (T2); sem Astra, pois
é medição.

**Decisões suas, independentes do Gate 1:** (i) coerência da régua no CG (5 subunidades-gold vazias contra a unidade v2 u05);
(ii) Gate 2 documental dos artefatos `wz_*`/`wz2_*` junto com os de 22/09; (iii) registrar que o padrão do código roda o
resolvedor antigo e só liga o D9 por flag (os 8 cursos têm a flag), e que o fallback dele gera 4 erros de unidade no CG.

## Limites desta entrega

- Oráculos usam gold por definição; são efeito de intervenção ideal, não ganho.
- A heterogeneidade medida é limitada ao que foi adjudicado; o CG não tem gold por bloco.
- "Relação" usa o índice do W-U (menção contígua por radical de 6 letras) e as fontes listadas; fora disso é "não
  encontrada no alcance inspecionado", não "inexistente".
- Cursos já estudados; nenhum resultado aqui é holdout novo.
- Execução pelo agente ativo (claude-opus-5-5, effort xhigh escolhido pelo usuário), sem worker separado. A 1ª rodada foi
  interrompida por mim, antes do gold, para desligar a pontuação por tópico no oráculo de bloco (docstring atualizada;
  declaração `40d59afd…` → `2a448326…`). Depois do gold, corrigi só a avaliação (precedência da proveniência "decisão do
  usuário" sobre "seção", e a origem do bloco usado) e reavaliei as capturas congeladas com `--reavaliar`; as decisões não mudam.
