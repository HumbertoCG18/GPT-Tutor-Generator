# Motor de Atribuição — Log de Decisões

date: 2026-06-28
status: EM DISCUSSÃO (decisões sendo travadas uma a uma; reler no fim pra ver o sistema)
contexto: continua de `_archive/2026-06-28-handoff-roteiro-como-base.md`. Branch `feat/block-stable-id`.

> Documento vivo. Cada decisão é numerada (D0, D1, ...). Forks abertos ao fim.
> Quando tudo travado → reler este arquivo e descrever o sistema completo.

---

## Problema (1 parágrafo)

Atribuir material → bloco da timeline, em 5 cursos com **sinais organizadores
heterogêneos**: IA tem data-de-seção; MF/ES2 têm roteiro (`lessons_index`); TCC
tem "Semana N" sem data; SO só tópico. O motor que resolve o IA hoje
(`anchor_placement`, parse de data-de-seção) é **IA-only** — não generaliza. Os
outros 4 cursos caem inteiros no funil-chute (`computed`, scorer). Só o IA tem
gold/régua.

---

## D0 — Direção do motor  [DECIDIDO]

Motor = **anchor plugável, mode-aware**. Forma:

```
WindowProvider(seção) → conjunto-de-blocos candidato   [o "container"]
   ├─ IA:  parse datas da seção → blocos cujas sessões caem na janela
   ├─ MF:  card_block_map[seção]  (manual=verdade, labels=candidato)
   ├─ TCC: ordinal "Semana N" → bloco            (futuro)
   └─ SO:  tópico-da-seção → bloco(s)             (futuro)

Disambiguator(janela, sinais)  [COMPARTILHADO; só roda se |janela|>1]
   → ranqueia blocos DENTRO da janela por roteiro/tópico, BOUNDED
   → conteúdo NUNCA escapa a janela (mata o ruído genérico, ex.: "introdução"→bloco-03)

ANCHOR-ONLY: escreve temporal_block_id só se resolve 1 bloco. Senão → scorer/flag.
```

- IA e MF viram o **mesmo motor**, mudando só o `WindowProvider`.
- Refatorar o `anchor_placement` de "anchor que cospe bloco" para
  **`WindowProvider + Disambiguator`** (mais fiel e seguro: o container sempre limita).
- **Prototipar o modo MF primeiro** (tem roteiro + `card_block_map` manual + golden de referência).
- **Provar read-only** (função pura medida contra o golden MF) ANTES de ligar no
  pipeline vivo. Ligar (escrever temporal) = reprocess = ação do USER na GUI.

---

## D1 — Grão do "manual" (escotilha de correção)  [DECIDIDO]

Manual = **escape hatch raro**, não entrada de rotina. Métrica de sucesso do
motor = **quão POUCOS** manuais são precisos.

Existem **dois grãos**, complementares (não competem), numa escada de precedência
(mais-específico vence):

```
1. pino por-material (manual_timeline_block_id) → bloco final     [cirúrgico]
2. card-window MANUAL (card_block_map source=manual)
       |1 bloco|  → coloca direto
       |>1 bloco| → Disambiguator escolhe dentro (janela = verdade humana)
3. card-window LABELS (derivado) → Disambiguator escolhe dentro   [conf menor]
4. SEM janela → scorer (chute) → FLAG (cross-check) → humano cura
```

**Princípio:** corrige no grão mais **COARSE** que resolve o erro.
- Erro de seção inteira (janela errada/grande) → **card-window** (1 toque conserta N materiais).
- Exceção de 1 material dentro de janela certa, ou resíduo **sem-card** (ex.: aula-29) → **pino-material**.
- Nunca pina N materiais quando 1 card-window conserta os N.

**Cada grão conserta um erro distinto:**
- card-window conserta a **JANELA** (container errado).
- pino-material conserta a **DESAMBIGUAÇÃO** dentro de janela certa, ou o **sem-janela**.

**Durabilidade:** ambos `source=manual` → sobrevivem reprocess (nunca sobrescritos).

**Ciclo de correção:** motor auto-coloca → cross-check **flaga** suspeitos → humano
revisa só os flags → cura no grão certo (card-window de preferência, pino se exceção).
Não varre N materiais à mão; revisa os poucos que o detector levanta.

---

## Achado I1 — derivação dos `labels` (INCÓGNITA RESOLVIDA)

`derive_card_block_map` (`moodle_labels.py:152`): janela = blocos cujo período
contém alguma **data-de-lição** do card. As datas vêm de `parse_card_dates`
(formatos A-C) que parseiam o **texto dos labels datados** dentro do card, ou
formato D ("Semana N"→range).

**Janela-labels e roteiro compartilham a fonte.** `build_lesson_topic_index:253`
reusa `parse_card_dates` — mesmas `lessons[{date,text}]`. Não é circular:
janela = UNIÃO dos blocos tocados; roteiro = SELEÇÃO de qual bloco. A janela
limita, o conteúdo escolhe.

**Dois vazamentos no dado real do MF:**
- `Verificação de Programas` → {10–15}: janela GENUÍNA (unidade Hoare/Dafny, 5
  blocos de conteúdo distinto) + 1 vazamento admin (`bloco-14 "evento academico"`).
- `Especificação e Verificação de Modelos` → {16–21}: FRÁGIL. Só `bloco-16` tem
  conteúdo; os outros 5 são admin/placeholder (`substituicao`, `devolucao`,
  `"Conteúdo: unidade-XX"`). A derivação inchou pro fim-de-curso.

## D2 — Higiene de janela: kind SOFT (não hard-filter)  [DECIDIDO — revisado]

**Tentativa inicial (descartada):** filtrar a janela para `kind == "class"`. **Furou.**
A prova de paridade do IA (47/47 temporal dentro da janela) revelou **9 materiais de
aula/código legítimos em blocos NÃO-class**: `bloco-01` kind=`overview` (intro do
curso) e `bloco-06` kind=`suspended` (8 materiais de clustering reais — gold confirma).

**Por quê:** o `kind` do BLOCO é AGREGADO (`_aggregate_source_kind`: o não-class de
maior prioridade vence). Uma sessão suspensa sobrepondo um bloco de ensino contamina
o kind inteiro. `kind==class` hard dropparia conteúdo real.

**Decisão (soft):** NÃO pré-filtra a janela por kind. O **Disambiguator (content↔topic)
evita admin/placeholder naturalmente** — material de clustering casa o tópico de
clustering (score alto) e casa "evento academico"/"devolucao"/"Conteúdo: unidade-XX"
em ~0. O bloco admin **perde sozinho**.
- `kind` = desempate SOFT só no caso silencioso/fraco (penaliza event/results/holiday).
- Hard-drop SÓ o inequívoco: topic_text = placeholder ("Conteúdo: unidade-") ou
  frase-admin pura (evento/devolução/recesso) — nunca seguram aula.

**Provado no trace (`scripts/trace_motor.py`):** janela 6-blocos "Especificação"
→ "verificacaomodelos" vence `bloco-16=4` vs admin `≤1` (margem 3, ALTA). Os 5 admin
perdem no conteúdo, SEM filtro. E `bloco-06 suspended-com-conteúdo` seria mantido.

→ F5 RESOLVIDO (kind do SARC é o sinal, mas SOFT). Dependência SARC: SO/TCC verificar.

## D5 — Window-source único = `card_block_map` (F3)  [DECIDIDO]

**Paridade provada:** 47/47 placements temporais do IA caem DENTRO da janela
`card_block_map[source_section]`, zero miss. Logo `card_block_map` **contém** toda
escolha do `anchor_placement` → é o WindowProvider universal.

**Decisão:** aposenta o monolito `anchor_placement` (que parseava data-de-seção e
escolhia bloco junto). O motor passa a `card_block_map` (janela) + Disambiguator (D3),
mantendo o esqueleto de tiers. A variação por-curso vive na DERIVAÇÃO do card_block_map
(`parse_card_dates` formatos A-D + manual), não em motores separados.

**Contrato:**
```
WindowProvider(entry, ctx) -> [block_uuid...]            # card_block_map[source_section]
Disambiguator(entry, window, ctx) -> (block, conf, band, flag)   # cadeia D3, kind soft
AnchorEngine.resolve(entry, blocks, ctx) -> AnchorResult|None
   tier1 pino manual (D1)        -> bloco final
   tier2 window = WindowProvider; se window: Disambiguator -> temporal (ANCHOR-ONLY)
   tier3 sem window              -> None -> scorer/flag
```

**Migração segura:** construir o motor novo, provar paridade read-only contra o
`temporal` atual do IA (deve reproduzir 47/47), SÓ ENTÃO trocar. Não quebra IA.

**Incógnita herdada:** cursos sem datas (SO: seções só-tópico) podem ter
`card_block_map` VAZIO → sem janela. Precisa de derivação de janela por TÓPICO
(seção-tópico ↔ bloco-tópico) pra SO. Sub-investigação na vez do SO.

---

## D3 — Disambiguator = cadeia de sinais por DISPONIBILIDADE  [DECIDIDO]

**Roteiro NÃO é assumido** — depende do professor (IA/MF/ES2 têm; SO/TCC não).
O disambiguator escolhe o bloco DENTRO da janela pelo melhor sinal **disponível**.

Chave: mesmo sem `lessons_index`, o **`block.topic_text` vem do SARC** (coluna
Atividade) — ex.: bloco-10="logica hoare". Logo content↔topic funciona sem roteiro;
o roteiro só **enriquece** onde existe.

```
janela = blocos kind==class do card           [cards + SARC montam a janela]
dentro da janela, em prioridade (usa o que TIVER):
  0. DATA-no-nome do arquivo (limpa, ≠ posting_date) cai na janela? → bloco   [determinístico]
  1. CONTENT↔TOPIC: conteúdo-limpo (title+moodle_label) ∩ block.topic_text (SARC)
        + lessons_index (roteiro) se houver                                    [sinal principal]
  2. PLANO DE ENSINO (talvez) → tópico→semana→bloco                            [sub-investigação]
  3. scorer-BOUNDED na janela (reusa máquina, limitado à janela)               [resíduo]
  4. bloco class mais cedo da janela + FLAG                                     [último]
```

**Invariantes:**
- NUNCA sai da janela. Material COM janela nunca cai no scorer desbounded (o que
  errou o aula-29 colocando fora). Janela = piso.
- IA é o caso DEGENERADO (seção≈1 bloco → desambigua no nível-seção, todos os
  materiais → mesmo bloco). MF/SO/TCC são o GERAL: seção = unidade multi-bloco →
  desambiguação POR-MATERIAL (conteúdo do material → sua sessão/bloco).
- roteiro apontando FORA da janela = cross-check `card!=roteiro` = possível arquivo
  mal-filed → FLAG (fica na janela, não segue o roteiro pra fora).

Reusa `roteiro_block_for` (já construído no cross-check), bounded à janela, com
`block.topic_text` como fonte de tópico quando não há roteiro.

### D3-ajuste — teto do determinístico ~65%; LLM é o lever (falsificação F-MF)  [DECIDIDO]

Investigação iterativa (3 correções minhas, cada uma artefato de probe parcial):
1. "ordinal load-bearing" → ERRADO: o markdown do material discrimina (Dafny5
   markdown="Classes/objetos" → bloco-15). Não é ordinal-posicional (Dafny5 ≠ 5ª sessão).
2. "só adicionar markdown" → INSUFICIENTE: token-count + markdown troca silêncio por
   ruído (silêncio 9→2 mas erro 11→16).
3. IDF (concept_resolver, dentro da janela) ajuda (multi 47→63%) mas **plateia**.

**Fusão COMPLETA bounded à janela (concept-IDF+seq+date+lesson, SEM LLM): 57% multi,
30/46 global.** E o breakdown mostra: `seq=0`/`date=0` em TODO Dafny → o
`score_sequence_match` **NÃO extrai** o ordinal do nome ("Dafny5") — sinal ausente.
Obstáculo real = **vocab de tema compartilhado**: todo exercício Dafny fala
"verificação/correção" → casa o bloco-tema (11); as poucas palavras discriminantes
(objetos/coleções) afogam.

**Conclusão:** matching por token (sem LLM) **plateia ~57-65%** no multi-bloco. Subir
o teto exige **voto LLM por-material** (entende sub-tópico semanticamente) — ver D8.
Ordinal-no-nome ajuda séries posicionais (não as de conteúdo-stage); extrair é gap
menor, não a solução principal.

## D4 — Gate de margem do Disambiguator  [DECIDIDO (valor a calibrar)]

- Confiante = best supera runner-up por **≥1 token discriminante** (≥0.5 no
  roteiro-score, que é 0.5/1.0/1.5 = 1/2/3 tokens). → band alta, ancora.
- Empate (margem 0) → ancora no melhor MAS band baixa + **FLAG**.
- Sinais que **concordam** (data-no-nome + topic) → band alta; **discordam** → FLAG.
- Valor exato do gate **calibrado contra o golden do MF** (measure-as-you-build, TDD).

## D6 — Motor é CATEGORY-AWARE (contexto universidade)  [DECIDIDO]

O tipo do material escolhe a lógica de JANELA (não é one-size). Três modos:

1. **material/exercício regular / código** → card-window + Disambiguator (content↔topic
   + ordinal/data → sessão). [core novo] — confirma: a MAIORIA dos exercícios segue a
   sessão que cobre → ordinal/data load-bearing (D3-ajuste válido).
2. **trabalho** (dura várias sessões, tem prazo) → NÃO mapeia 1 sessão → **janela-de-
   prazo**: blocos com `period_start < assign_due`. Reusa `lookup_card_assign_due` +
   `ASSIGN_WINDOW_CATEGORIES` (S5, JÁ existe no funil). O due NUNCA decide sozinho.
3. **exercício de revisão p/ prova** → bloco de revisão antes da prova. Reusa
   `review_list_block_for_entry` / `review_rule` (JÁ existe).

→ o motor unifica esses 3 sob o esqueleto de tiers; reusa as regras de categoria que
já existem no funil, agora dentro do AnchorEngine.

## D7 — Estilo de postagem é POR-PROFESSOR; modelar  [DECIDIDO — investigar]

Convenção de card varia por professor:
- **week-card** (1 semana = 1 card) → janela TIGHT (≈1 bloco) → pouca desambiguação. (IA)
- **unit-card** (1 unidade = 1 card, todos os arquivos da subunidade dentro) → janela
  LOOSE (multi-bloco) → desambiguação PESADA. (MF "Verificação de Programas" = 6 blocos)

A `card_block_map` captura ambos (tight=1 bloco, loose=N), mas a carga do Disambiguator
difere radicalmente. **Próximo: PERFILAR cada curso (week vs unit) e criar um "modelo de
postagem" por professor** — define quanto a janela bound já resolve vs quanto sobra pro
Disambiguator.

## D8 — Disambiguator é ESCALADA por custo (resolve fork A/B + parte do F6)  [DECIDIDO]

Não é "determinístico OU LLM" — é escalada em 3 tiers, cada um pega o que o anterior
não resolveu:

```
1. DETERMINÍSTICO (window + concept-IDF + seq + date + lesson)   GRÁTIS  → ~65% confiante
2. Se FLAGGED (margem baixa / série mesmo-tema): VOTO LLM (Gemini)  BARATO  → resolve semântica
3. Ainda incerto: REVISÃO HUMANA (pino)                            RARO
```

**O voto LLM JÁ EXISTE como mecanismo** (não é capacidade nova):
- Código: `code_curation` (Gemini) → `block_match_confidence`/`primary_block_id`,
  **bundled no resumo de código** (grátis — já roda).
- Material: `run_material_residual` → `summarize_residual_materials` → `primary_block_id`.

**Hoje o material só pega o voto quando é ÓRFÃO** (sem bloco) + opt-in
(`enable_material_residual`) + cap=20. Os Dafny que erraram NÃO são órfãos → não pegam.

**Wiring:** mudar o escopo do voto-material de "órfão" → "órfão OU flagged". Custo
**bounded** (LLM só no resíduo ~35%, não em todo material; cap=20 já é o orçamento).

**O FLAG (gate de margem, D4) é o gatilho que escala** — fecha o F6: flag → voto LLM
→ (se ainda incerto) humano. Os dois grãos do manual (D1) continuam: pino-material
no resíduo, card-window no erro de janela.

**Custo bounded long-term (user OK com pagar API, mas princípio = reduzir carga):**
- voto **cacheado** em `code_curation.json` (artefato persistido; prune stale + write
  atomic). Re-reprocess **reusa** o voto, NÃO re-chama Gemini — só material novo/alterado.
- determinístico é o piso (LLM nunca roda no caso fácil) → maioria nunca toca a API.

**Validação pendente:** rodar Gemini no conjunto flagged do MF pra PROVAR que o voto
conserta same-theme (Dafny OO→15). Mecanismo desenhado pra isso; teto real no protótipo.

**Validação EXECUTADA (2026-07-01 — MARCO 0/1, `scripts/marco0_prova_deterministica.py`
+ `scripts/marco1_voto_llm.py`, régua = ground_truth_MF.csv 66 unidades):**
- **MARCO 0 (sem LLM):** ordinal-no-nome MORREU por medição — prior linear = lift zero;
  DP-monotone = lift NEGATIVO (importa erro do vizinho: quebrou Dafny1 que o content
  acertava). Confirma o "gap menor" do design, agora com número. Achado colateral:
  **len-norm da assinatura (+6.5pp grátis)** — o sumidouro bloco-11 era assinatura
  gorda, não semântica. Piso determinístico do probe (tokenizer cru): 59.7% no escopo.
- **MARCO 1 (Gemini 2.5-flash, 18 flagged, ≤cap):** determinístico 3/18 → **LLM 8/18
  (+5)**. Global escopo-disamb: 58.1% → **66.1% (empata com o funil)**. O LLM converte
  a classe CONFUSÃO-SEMÂNTICA (sintaxe/semântica proposicional↔predicados: 4/4;
  isabelle2; plano→bloco-01), mas NÃO converte grão-de-semana same-theme (Dafny1,
  indução 05↔06, tiposindutivos) nem bibliografia/apoio (0/3 — classe fora de escopo,
  refatoração de ingestão). Confiança do voto = "alta" em 18/18 → inútil como sinal;
  não usar como gate.
- **Gargalo REAL medido = recall do gate D4:** 11 confiante-e-ERRADO ficaram CEGOS pro
  LLM (gate proxy τ=0.25 pegou 15/26 erros). O lever do teto não é o LLM nem o ordinal:
  é o gate pegar mais erro (ou escopo do voto ampliar p/ séries same-theme inteiras).
- **Caveats:** probe é PISO (sem concept-IDF real do `concept_resolver`, sem split
  avançado); flagged set muda quando o disambiguator real entrar. MARCO 1 prova o
  MECANISMO (lift existe e é barato), não o teto.
- **D8 REFINADO pela evidência:** TIER 3 fica, mas o wiring deve (a) ampliar escopo do
  voto pra "flagged OU membro de série same-theme", (b) ignorar a autoconfiança do LLM,
  (c) priorizar calibração do gate D4 como fase com número próprio (era "fase 2";
  agora é o lever dominante).

## Nota — Frequência de aula = UPSTREAM, não core  [DECIDIDO escopo]

"Card = semana inteira" (IA, 2 aulas/sem) JÁ é tratado genericamente: o range de
datas do card → blocos na janela (`derive_card_block_map`), seja 1 dia/semana/unidade.
Sem caso especial, sem fallback. Logo **frequência de aula (dias/horário) = YAGNI pro
motor** — duplica o sinal de data que o range já dá; a desambiguação é por conteúdo/
data/ordinal, não por dia-da-semana. Frequência tem valor só no UPSTREAM (corte de
bloco — onde nasceu o mega-bloco de 28 dias) e em QA (validar data-no-nome contra dia
de aula). Fora do core de atribuição.

## Nota — granularidade de bloco = UPSTREAM  [risco registrado]

O motor é tão fino quanto os blocos que recebe. `Semana 10` IA → `bloco-05` (28 dias,
9 sessões fundidas pela suspensão). Atribuição correta mas grossa. Problema é do
block-splitting, não do motor — mas o motor herda a grossura.

## Nota — SARC/Cronograma SEMPRE existem  [CONFIRMADO pela universidade]

Mata a dependência aberta: kind/higiene (D2) e tópico-de-bloco (D3) valem nos 5 cursos.
Cores geralmente consistentes; mapa cor→kind é **extensível** (cor nova, mesmo kind →
adiciona ao set). Sub-investigação: verificar consistência de cor entre professores.

---

## Falsificação F-MF — motor vs gold MF (48 casos, read-only)

Prova read-only do motor proposto contra `tests/fixtures/eval/metodos_formais_golden.json`
(disambiguator = content↔topic + roteiro, com split camelCase).

| Claim | Resultado | Veredito |
|-------|-----------|----------|
| **C1** verdade DENTRO da card-window | **46/46 = 100%** | CONFIRMA D5 (motor bounded alcança a verdade) |
| **C2** bloco admin venceu material real | **0** | CONFIRMA D2-soft (conteúdo evita admin) |
| **C4** content↔topic resolve multi-bloco | 18/38 confiante (47%); 9 silêncio; 11 errado/empate | **QUEBRA** "tópico basta" |

- janela=1 bloco: 8/8 trivial.
- Erros genuínos = **séries de mesmo-tema** (ExerciciosDafny1-5 → 12,13,13,13,15;
  indução defs/proofs). Vocab compartilhado afoga a palavra discriminante.

**Progressão do disambiguator (multi-bloco, mesmos 38 casos):**
| Config | multi CERTO | global |
|--------|-------------|--------|
| título só (count) | 18/38 (47%) | 26/46 |
| título+markdown (count) | 20/38 (52%, +ruído) | 28/46 |
| IDF + markdown | 24/38 (63%) | 32/46 |
| **fusão completa SEM LLM** (concept-IDF+seq+date+lesson) | 22/38 (57%) | 30/46 |

`seq=0`/`date=0` em todo Dafny → ordinal-do-nome NÃO é extraído. Teto determinístico
~57-65%. → D3-ajuste (teto) + D8 (LLM no flagged sobe o teto).

---

## D9 — Integração & migração (fronteira #3)  [DECIDIDO]

Coerente com o sistema existente (`anchor_placement` JÁ é "feature-flagged, additive,
writes temporal without changing computed" — o motor é a EVOLUÇÃO dele).

1. **`AnchorEngine` SUBSTITUI `apply_anchor_placement`** (passo 5 do
   `pedagogical_regeneration`), escreve `temporal_block_id` ANCHOR-ONLY. **Funil
   (`computed`) INTACTO** como piso pra material sem-janela. Cascata
   `temporal>manual>computed` preservada. → raio de explosão mínimo.
2. **Vive em `src/builder/routing/`** (subpackage), NUNCA `engine.py` (facade —
   não-negociável). Reusa o SCORING do `concept_resolver` (`concept_token_weights`/
   `concept_vector`/`score_lesson_match`) bounded à janela; escreve temporal (não a
   aplicação-overwrite do `resolver_apply`).
3. **Escalada LLM (D8)** dentro do disambiguator, gated por flag, **background-thread**,
   **`google-genai` lazy** (não-negociável). Voto cacheado em `code_curation.json`.
4. **Feature-flag por-curso** (`SubjectProfile.feature_flags`). IA/MF primeiro.
5. **Migração:** build → mede vs gold (IA `ground_truth` + MF `golden`), critério =
   **SEM REGRESSÃO** (NÃO byte-paridade com anchor velho — o disambiguator pode
   MELHORAR). Troca → re-baseline consciente de `test_caracterizacao`. Os testes
   `test_anchor_placement`/`test_temporal_block_wire` são substituídos pelos do motor
   novo (TDD).
6. **UI de revisão = Timeline Dashboard/Cronograma EXISTENTE** (override de bloco +
   badges de confiança). Sem UI nova.
7. **Reprocess re-renderiza** os artefatos (CRONOGRAMA_DETALHADO/FILE_MAP). Atualizar
   `docs/Overview-Sistema.html` (overview vivo) + `pendencias.md` como parte do trabalho.

---

## D10 — Escopo do rollout + SO WindowProvider  [DECIDIDO]

**SO não cabe no card-window** (card_block_map vazio — seções de tópico, sem data).
Precisa de WindowProvider DIFERENTE (mesmo motor, 2º provider):
```
SO WindowProvider:
  1. data-no-nome → bloco(s) cobrindo a data   [determinístico; cobertura alta nas
                                                 seções "Gerência de X": 4/4, 2/2]
  2. seção-tópico ↔ bloco-tópico → janela       [fallback, PARCIAL/ruidoso: I/O→nada,
                                                 Threads fraco, empata c/ placeholder]
  3. resíduo (Informações Gerais, sem-data)     → LLM/humano
```
SO tem SARC kind (overview/class/holiday/deliverable/...) — muito admin → D2-soft essencial.

**Ordem de rollout:**
1. **IA + MF** (card-window + gold) — provam o core.
2. **TCC/ES2** (card-window, sem gold → cross-check de rede).
3. **SO** por último — precisa do WindowProvider filename-date+tópico E de gold.

SO faseado, não excluído — a arquitetura (WindowProvider plugável, D5) o acomoda.

---

## D11 — F6-resíduo: cross-check = detector de ANOMALIA-DE-DADO  [DECIDIDO]

Teste MF (read-only): auditar janela com "roteiro-unbounded ∉ janela" = **11 disparos,
11/11 FALSO ALARME, 0 real**. Janela confiável (C1=100%) → auditá-la é 100% ruído.

Decisão:
- O cross-check **NÃO audita material windowed** (ruído provado).
- Papel = **detector read-only de ANOMALIA-DE-DADO**: material SEM-janela cujo placement
  (scorer) discorda de sinal independente (roteiro/conteúdo) = classe **aula-29**
  (duplicata / mis-file / nome corrompido).
- Roda como **QA report separado** (`scripts/crosscheck_IA.py`), alimenta correção de
  DADO do humano (dedup/rename/re-import), NÃO flag de atribuição de rotina.
- **Flag de atribuição de rotina ≠ cross-check:** rotina = flag intrínseco do motor (D4)
  → LLM (D8) → pino. O cross-check é a outra coisa (dado, não atribuição).
- Valor é LIMITADO (anomalia de dado é rara — aula-29 aconteceu 1× no IA). Mantém leve.

---

## D12 — Estratégia de gold/validação  [DECIDIDO]

**Gold = régua de DEV/validação, não artefato de produção.**
- Construído **AGORA** (fim de semestre = dados completos), **1×/curso**. NÃO se preenche
  por reprocess nem por arquivo novo.
- **Produção** (próximo semestre, poucos arquivos crescendo): o motor PRONTO atribui
  **incremental** — usa a ESTRUTURA do curso (SARC + cards + blocos, que existem cedo;
  IDF é sobre BLOCOS, não materiais). Rede = pino no resíduo + cross-check de anomalia.
  **Gold não entra em produção.**
- Preferir gold **DERIVADO-POR-SCRIPT** (do oráculo independente — crosswalk SARC
  subtópico): auto-estende com Moodle iterativo, só straddle precisa humano. Melhor que
  fixture-à-mão (IA é script; MF é fixture).

**Rollout de gold:**
- **IA/MF:** gold obrigatório (provar o motor + CI de regressão).
- **SO:** gold antes de confiar (WindowProvider NOVO).
- **TCC/ES2:** deferido — card-window PROVADO → flag + funil-piso + revisão Cronograma +
  cross-check é rede reversível. Gold só se a revisão achar problema.

**Grãos legítimos de risco (não imaginários):**
- janela depende do cronograma SARC publicado (sai cedo; onde falta → scorer+pino).
- convenção NOVA de professor → perfilar (D7) + talvez novo WindowProvider (bounded).

**Linha do tempo:** constrói+prova+ship AGORA (gold disponível) → semestre novo = motor
roda sozinho no incremental. Não fica refém de preencher gold em curso vazio.

---

## SÍNTESE — Como o sistema funciona (D0-D12 integradas)

```
ENTRADA: material (source_section, title, markdown, category)

TIER 1 — Pino manual (D1)
  manual_timeline_block_id válido? → bloco final. FIM.   (escape hatch raro, durável)

TIER 2 — Roteamento por categoria (D6) + Window + Disambiguator
  trabalho (prazo)?  → janela-de-prazo (blocos antes do assign_due; S5 EXISTE)
  revisão p/ prova?  → bloco de revisão (review_rule EXISTE)
  senão →
    WindowProvider (D5): card_block_map[source_section]   (IA/MF/ES2/TCC)
                         filename-date / section-topic     (SO; provider novo, D10)
       → janela (conjunto de blocos). NÃO filtra kind (D2-soft).
    Disambiguator (D3) DENTRO da janela:
       |janela|=1 → coloca
       senão: 0.data-no-nome  1.content↔topic (IDF+markdown + block.topic_text SARC + roteiro)
              admin perde sozinho no conteúdo (D2-soft); kind = desempate fraco
       gate de margem (D4): confiante→ALTA ancora; empate/silêncio→FLAG

TIER 3 — Escalada por custo (D8), se FLAGGED:
    voto LLM (Gemini, reusa summarize_residual/code_curation, CACHEADO) → semântica
    ainda incerto → FLAG humano

SAÍDA: escreve temporal_block_id (ANCHOR-ONLY, D0/D9). Funil (computed) = piso intacto.
       Cascata efetiva: temporal > manual > computed.
```

**Dois loops humanos (raros, no Cronograma Dashboard existente):**
- Atribuição: flag → (LLM) → **pino-material** no resíduo (D1/D8).
- Dado: cross-check (anomalia duplicata/mis-file no sem-janela) → dedup/rename (D11).

**Integração (D9):** AnchorEngine em `src/builder/routing/` substitui `apply_anchor_placement`;
reusa scoring do `concept_resolver`; flag por-curso; funil intacto; LLM background+lazy+cache;
migração = sem-regressão vs gold → re-baseline caracterização.

**Rollout (D10/D12):** IA+MF (gold, provar) → TCC/ES2 (flag+rede) → SO (provider novo+gold).

**O que sobrevive empiricamente:** C1 card-window contém verdade 100% · C2 admin nunca vence
· teto determinístico ~65% multi-bloco, LLM sobe · cross-check audita DADO não janela (11/11
falso-alarme).

**Prontidão:** decisões fechadas (D0-D12). Resta só calibração no TDD (gate/threshold/pesos),
detalhe do SO provider (fase SO), e sub-investigações não-bloqueantes (plano de ensino, cor).
→ pronto pra **spec → writing-plans**.

---

## Achado F-TCC — week_anchor ordinal-linear DRIFTA; TCC = provider por TÓPICO  [2026-06-29]

Probe read-only no repo `TCC-Tutor`. Cards = "Semana N - Tópico" (N 1-14, **sem data**),
arquivos = "Aula NN - Tópico" (**sem data**), blocos COM datas reais (`.timeline_index.json`,
31 blocos). `card_block_map` popula só por **5 pinos MANUAIS** (`source=manual`); derivação
por labels = **VAZIA** (sem label datado → formatos A-C de `parse_card_dates` falham; formato
D pula porque `week_anchor` nunca é suprido).

Formato D (`_parse_format_d`, `src/builder/sources/moodle_labels.py:138`) existe mas
**DORMENTE**: `start = week_anchor + (N-1) semanas`, range 5 dias, intersecta
`period_start/end`. Call-sites de produção (`src/builder/sources/moodle.py:448` e `:488`)
NUNCA passam `week_anchor` → default `""` → formato D pula. `SubjectProfile`
(`src/models/core.py:218`) não tem `course_start`. Wiring mecânico = ~1 linha.

**FALSIFICAÇÃO** (simulação linear `week_anchor=2026-03-04` cruzada contra os 5 pinos reais):

| Card | Linear (sim) | Pino manual (verdade) | |
|---|---|---|---|
| Semana 3 | bloco-03,04 | bloco-03,04 | ✓ |
| Semana 7 | bloco-10,11 | bloco-10,11 | ✓ |
| Semana 10 | bloco-16,17 | bloco-16 | ~ over |
| Semana 12 | bloco-19 | bloco-21,22 | ✗ drift 2-3 |
| Semana 13 | bloco-20,21 | bloco-23 | ✗ drift |

Semanas cedo casam; semanas tarde **driftam 2-3 blocos**. Causa: feriado/recesso/prova
quebram a cadência fixa de 7 dias. Ligar `week_anchor` naive = janela ERRADA nas semanas
finais = **confident-wrong** (PIOR que vazio, que cairia no funil seguro).

**DECISÃO/IMPLICAÇÃO:** TCC `WindowProvider` = por **TÓPICO** (card "Semana N - TÓPICO" →
`block.topic_text`), reusa o Disambiguator content↔topic, imune a drift de calendário. TCC é
**SO-like** (provider por tópico), NÃO ordinal-like. Confirma D10/D12 ("TCC precisa de
cuidado") com a razão exata: **ordinal-de-semana é ARMADILHA (drift), tópico é o sinal real**.
Ordinal "Aula NN" fica como sinal SOFT dentro da semana.

**Topic-bridge confirmado (probe vs 5 pinos): 4/5 determinístico, 1 = resíduo-LLM.**

| Card | topic_text do bloco-pino | casa? |
|---|---|---|
| Semana 3 (Minimização/T1) | bloco-03 "…minimizacao…"; bloco-04 "trabalho" | ✓ |
| Semana 7 (Halte/Entscheidung) | bloco-10 "halting problem"; bloco-11 "entscheidungsproblem" | ✓ exato |
| Semana 10 (Revisão P1) | bloco-16 topic="para" (genérico) MAS session-label "revisao para prova p1 aula" | ✓ via SESSÃO |
| Semana 12 (NP-completude) | bloco-21 "theorema cook levin"; bloco-22 "…pspace complete" | ✗ lexical (NP ausente) |
| Semana 13 (Trabalho T2) | bloco-23 "trabalho" | ✓ |

Dois aprendizados NOVOS:
1. **Sinal de SESSÃO** (`sessions[].label`/descrição) rescata onde `block.topic_text` é
   genérico (S10). O Disambiguator deve minerar texto de SESSÃO, não só `topic_text` do bloco.
   (Schema: `sessions` carrega mais que `{date}` — há label/descrição. Corrige a leitura
   anterior que via só `{date}`.)
2. **S12 NP-completude = caso D8 canônico do TCC:** "NP-completude" ≠ "Cook-Levin"/"PSPACE"
   lexicalmente, mas Cook-Levin É a base de NP-completude → ponte **SEMÂNTICA = LLM** (TIER 3).
   Mesma estrutura da série same-theme do Dafny (MF): vocab-de-tema afoga o discriminante.
   (Nota: o linear pôs S12→bloco-19="classes complexidade", que é o tópico da **Semana 11** →
   drift "1 semana atrás", consistente com feriado/recesso.)

**Síntese TCC:** melhor determinístico = TÓPICO (`block.topic_text` + texto de sessão) = 4/5;
resíduo (NP-completude) = D8 LLM. Ordinal = soft. Confirma a arquitetura de 3 tiers **sem caso
especial pro TCC** — só muda o WindowProvider (tópico, não ordinal-linear).

> Nota de método: o agent de probe declarou "TRIVIAL, 14/14 casam" porque só checou
> intersecção NÃO-VAZIA, não BLOCO-CERTO. O cruzamento adversarial contra os pinos reais
> pegou o confident-wrong. Lição: validar contra verdade, não contra "não-vazio".

---

## Restrições de PLATAFORMA & faculdade  [confirmado pelo usuário, 2026-06-29]

- **SARC = data POR AULA** (1 linha = 1 data + tópico + `kind`). "Semana" NÃO é do SARC — é
  agrupamento do professor no Moodle. SARC é a VERDADE de data/tópico/kind.
- **SARC completo desde o início do semestre** (todas as sessões). O **Moodle é INCREMENTAL**
  (arquivos postados ao longo do tempo). → confirma D12: o backbone (blocos/datas/tópicos)
  existe cedo; material chega aos poucos; motor coloca incremental. Exceção: arquivos do
  semestre passado (stale) ou upload-total raro = **ANOMALIA-DE-DADO** (D11).
- **Fonte do arquivo varia: Moodle vs M365.** MF e ES2 = **todos os arquivos vêm do M365**
  (professor upa no M365; API do Moodle não pega). → `moodle_label`/instancename pode FALTAR;
  `source_section` vem da estrutura de PASTAS (M365/stash), não da seção Moodle. Sinais
  disponíveis mudam por curso (impacta o Disambiguator e o gerador de gold-scaffold).
- **OpenSarc** = reserva de sala/lab (aparece horas antes da aula). IGNORAR por hora (futuro).
- **Convenção de card por curso (D7):**
  - IA = week-card (2x/sem, range seg-sex).
  - MF = **unit-card + roteiro interno** (linhas data→tópico, ex.: "(09/03): revisão lógica;
    (11/03): conjuntos indutivos; (assíncrona): exercícios"). Range seg-sex mesmo com aula seg/qua.
  - TCC = week-card ORDINAL (sem data no card → topic-bridge; ver F-TCC).
  - ES2 = week-card 1x/sem (M365). Risco = **conteúdo repetido entre blocos** (same-theme →
    D8 LLM), NÃO drift de ordinal. Ordinal ≈ semana 1:1 (1 aula/sem).
  - SO = **unit-card, SEM roteiro, MAS data no instancename E no nome do arquivo** →
    **data-no-nome FORTE** (step 0 do Disambiguator); topic-window fraco (ver memória 2078).
- **Roteiro NÃO é universal** — depende do professor (IA/MF têm; SO não; ES2 a confirmar). O
  Disambiguator usa o sinal que TIVER (D3).

---

## Mapa de WindowProvider dos 5 cursos  [probes read-only, 2026-06-29]

| Curso | Fonte | source_section | card_block_map | Sinal PRIMÁRIO | Resíduo (→ D8 LLM) |
|---|---|---|---|---|---|
| IA | Moodle | seção Moodle | popula (labels, datado) | data-de-seção (week-card, range) | degenerado (seção≈1 bloco) |
| MF | M365 | pasta/stash | popula (manual + labels) | unit-card + **roteiro** (data→tópico) | série same-theme (Dafny) |
| TCC | Moodle | seção Moodle | só 5 pinos manuais; labels VAZIA | **TÓPICO** (card ↔ block topic_text + sessão) | NP-completude (Cook-Levin) |
| ES2 | M365 | pasta (Desktop dump) | popula labels MAS GROSSO (1 card "Microsserviços" = 10 blocos) | **session-label** data→tópico (fino) | same-theme microsserviços espiral (5 blocos) |
| SO | Moodle | seção Moodle | VAZIA (unit-card, sem label datado) | **DATA-NO-NOME** (title+label+path, 45%, 1:1 determinístico, 0 colisão) | undated 55%: trabalho/revisão→categoria D6; resto = topic fraco (81% blocos 1-2 palavras) |

**Achados transversais (load-bearing pro spec):**

1. **card_block_map NÃO é provider universal suficiente.** Vazio (SO), grosso-inútil
   (ES2: 1 card = 10 blocos ≈ semestre todo), só-manual (TCC labels vazia). Só IA (e MF)
   populam útil. → o **WindowProvider é uma CASCATA/UNIÃO de providers por sinal disponível**,
   não só `card_block_map`. **AJUSTA o Contrato 1 do spec** (que assumia card_block_map universal).
2. **session-label do SARC (`sessions[].label` = data→tópico) é o sinal UNIVERSAL
   subutilizado.** Existe em TODOS (vem do SARC, completo desde o início). Rescatou TCC-S10 e é o
   lever fino do ES2. Disambiguator deve tratá-lo como PRIMEIRA-CLASSE, não só `block.topic_text`
   (agregado/grosso).
3. **Cada curso tem sinal PRIMÁRIO diferente** → confirma D0/D5 (motor plugável mode-aware) como
   NECESSÁRIO, não over-engineering. Matriz de disponibilidade: data-de-seção=IA · roteiro-no-card=MF ·
   data-no-nome=SO(forte)/IA(parcial) · tópico-do-card=TCC · ordinal=TCC/ES2(soft) ·
   **session-label-SARC=TODOS**.
4. **Resíduo é SEMPRE same-theme** (Dafny / NP-completude / microsserviços) → mesma cura **D8 LLM**.
   Um único tier LLM serve os 4 cursos não-triviais. Reforça D8.
5. **Categoria (D6) corta o resíduo do SO:** parte dos 55% undated são trabalho (→assign-due),
   revisão (→review_rule) e plano-de-ensino (→overview/excluído), não falhas de disambiguação.

---

## D13 — Gold: modo de gabarito por curso (ergonomia vs cobertura) + resolução de straddle  [DECIDIDO — 2026-06-30; premissa corrigida 2026-07-01]

Refina D12 pelo lado da FERRAMENTA (`build_gold_xlsx` → `build_ground_truth` →
`eval_ground_truth`). O gold-scaffold tem **dois modos de gabarito**, auto-detectados
pelo NOME DA ABA do xlsx:

- **MODO SUBTÓPICO** (aba `Gabarito Subtopicos`): humano rotula por **subtópico#**
  (semântico, datado); a máquina deriva o bloco pelas datas SARC sob a borda
  `[início, fim)` (esq-inclusiva, dir-exclusiva; `data==início` cai NAQUELE bloco).
  Sobrevive a renumeração de bloco. Precisa de `sarc_subtopics_<curso>.csv`.
- **MODO BLOCO** (aba `Gabarito dos Blocos`): humano escolhe `bloco-NN` direto no
  dropdown; `true_block = bloco_correto`, sem crosswalk de data.

**STRADDLE** = subtópico-semana cujas 2 datas caem em blocos diferentes. A máquina não
escolhe um → `scorable=no`, A MENOS que o humano desambigue por-material via `obs -> DD/MM`
(aponta a sessão exata). Straddle NÃO mata o material — é trabalho extra de resolução.

**CORREÇÃO de premissa (2026-07-01):** a 1ª versão desta D13 dizia que o critério de modo
era o "straddle rate" (straddle alto → bloco). ERRADO, falsificado na medição:
- IA straddla **14/20** subtópicos — MAIS que o MF (**10/18**). Não é o menos-straddle.
- IA funciona em subtópico porque os straddles foram **resolvidos** via `obs -> DD/MM`
  (29→44 scorable; 6 discriminantes após resolução). Straddle é resolvível, não bloqueio.

**Critério REAL do modo = ergonomia+robustez vs cobertura+simplicidade:**

| | Subtópico | Bloco |
|---|---|---|
| Rotula por | tópico (fácil; não precisa saber fronteiras) | `bloco-NN` (mapeia material→bloco) |
| Straddle | resolve por-material via `obs` (custo) | não existe (escolhe 1 direto) |
| Cobertura | perde o que não resolver | cheia |
| Renumeração | robusto | rótulo quebra |

**Resultado empírico por curso:**

| Curso | Fonte roteiro | Straddle | Modo | Motivo |
|---|---|---|---|---|
| IA | Moodle `lessons_index` | 14/20 (resolvidos via obs) | subtópico | estabelecido; obs resolve |
| ES2 | Moodle `lessons_index` (15 datas, 1x/sem) | **0/13** | subtópico | encaixe mais limpo (sem obs) |
| MF | Moodle `lessons_index` (39 datas, 2x/sem) | 10/18 | **bloco** (FORCE_BLOCK) | conveniência: cobertura cheia dos 67 sem resolver ~10 straddles à mão. NÃO por straddle-rate |
| SO | **sem `lessons_index`** | — | bloco | sem roteiro datado extraído |
| TCC | **sem `lessons_index`** | — | bloco | sem roteiro datado (topic-provider, F-TCC) |

MF em bloco é escolha de **conveniência** (cobertura cheia sem resolver straddles à mão),
não porque straddla mais — straddla MENOS que o IA. Poderia ser subtópico+obs, como o IA.
SO/TCC sem `lessons_index` = topic-provider (D10/F-TCC), não date-provider.

**Resolução de straddle: PRECEDÊNCIA de sinal (aprendido 2026-07-01):** ao decidir qual
sessão um material straddle é, checar nesta ordem — **pino manual (`manual_timeline_block_id`)
> pasta de origem (`source_path`) > conteúdo↔tópico-da-sessão (`lessons_index`)**.
Falsificação no IA: dos 24 straddles resolvidos por conteúdo, **4 estavam errados** contra
sinal mais forte (3 contra pino manual, 1 contra pasta `Semana 15 - Busca`) — geraram
discriminantes FALSOS. Corrigidos → **10→6** discriminantes reais. Melhoria futura: o
`run_subtopic` podia honrar o pino manual como verdade de maior precedência (hoje só lê
`obs`/crosswalk) — mas cuidado com circularidade (pino é dado de produção; ver D12).

**`clean_subtopics` (denominador do modo subtópico) = DERIVADO do csv:** `letivo=yes` e
fonte sem "Card" → clean; "Card" → eco (baixa confiança, carimbado-excluído). Reproduz o
IA byte-a-byte (`1-11,16-20` clean; `12-15` eco). ACOPLADO à ordem das linhas do csv →
reordenar/fundir exige re-derivar (o gerador imprime o set). Inerte em modo-bloco
(`run_block` ignora — só `run_subtopic` lê).

**Grão do gold subtópico = semana ISO** (unidade de ensino real: MF 2 sessões/sem, ES2
1/sem), com merge de semanas adjacentes de rótulo IDÊNTICO (evita 2 opções indistinguíveis
no dropdown). Gerado de `lessons_index` por `scripts/draft_subtopics.py` (rascunho
revisável); `fonte_data=Roteiro (Moodle)` marca NÃO-reconciliado com SARC (datas planejadas,
não reais — reconciliar onde houve feriado/aula-deslocada).

**FIREWALL do menu (mantido):** subtópico `letivo=no` (feriado/suspensão) NUNCA entra no
dropdown (assert em runtime); aparece só cinza como contexto. Material não pode ser rotulado
a feriado → crosswalk nunca faz data-math em feriado.

**Ferramenta:** `build_gold_xlsx.py` (scaffold; `FORCE_BLOCK={"MF"}`; reader `utf-8-sig`
p/ Excel), `build_ground_truth.py` (crosswalk; `COURSE_CONFIG` por-curso; modo auto por
aba), `eval_ground_truth.py` (já genérico). CSV com BOM (Excel lê UTF-8 direto). Gold =
régua de dev, não entra em produção (D12).

---

## Forks ABERTOS (próximos)

- ~~F2 política de janela~~ → RESOLVIDO por D3/D4.
- ~~F4 gate do Disambiguator~~ → RESOLVIDO por D4.
- ~~F5 definição de não-instrucional~~ → RESOLVIDO por D2 (`kind` do SARC).
- ~~F3 contrato/window-source~~ → RESOLVIDO por D5.
- **F6 — wiring do FLAG / cross-check** [PARCIAL — D8 fechou a escalada flag→LLM→humano].
  Resta: o cross-check independente (card-window vs roteiro-UNBOUNDED) — a falsificação
  mostrou que roteiro-unbounded é ruidoso (falso-alarme quando a janela já está certa).
  Definir se o cross-check audita a janela (e como, sem ruído) ou só vale no sem-janela.
- **SUB-INVESTIGAÇÃO — plano de ensino:** existe (page module Moodle); parseia pra
  tópico→semana? Enriquece D3 passo 2. Não bloqueia o core.
- **SUB-INVESTIGAÇÃO — SARC/kind em SO/TCC:** têm SARC importado? Sem ele, higiene (D2)
  e topic-de-bloco (D3) degradam. Verificar na vez deles.
- **SUB-INVESTIGAÇÃO — janela por TÓPICO p/ SO** (D5): seção-tópico ↔ bloco-tópico
  quando não há datas pra derivar card_block_map.
