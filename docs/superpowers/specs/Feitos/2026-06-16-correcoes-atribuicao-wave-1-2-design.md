# Spec — Correções do sistema de atribuição (auditoria wave 1+2 + D1)

date: 2026-06-16
base: `docs/reports/2026-06-11-plano-mestre-atribuicao.md` (seção "Auditoria completa
do sistema de atribuição (16/06, wave 1+2)") e aba 6 de `docs/Overview-Sistema.html`.
objetivo: corrigir os defeitos estruturais achados na auditoria read-only do subsistema
de atribuição (arquivo→bloco→unidade/subunidade), mantendo o golden de bloco.

## Contexto

A auditoria (9 clusters, subagentes paralelos em 2 ondas) achou 21 problemas em 4
categorias: conflito (um passo desfaz outro), duplicação, código morto, ruído. Este spec
cobre TODOS eles + a decisão de arquitetura D1, organizados num plano faseado.

O subsistema está em reforma desde o plano-mestre (P0-P4 fechados, golden de bloco
**41/48, confiante-errado 0**). Estas correções são a continuação: matam os "segundos
cérebros" e contratos mortos que sobreviveram às fases anteriores.

## Decisões tomadas (brainstorming 16/06)

- **Estrutura:** spec único + plano de implementação **faseado** (P0 → P1 → P2 → P3),
  executado incrementalmente, cada fase atrás do golden. Merges pequenos.
- **D1 (Gemini código→bloco) = A:** fonte única `computed_block_id`; Gemini vira **voto**
  (consensus/llm_only), não decisor rival. Alinha com o alvo do plano-mestre (linha 43).
- **D2 (`administrative_only`) = A uniforme:** trocar o key-lookup morto
  `block.get("administrative_only")` pelo predicado real
  `_timeline_block_is_administrative_only(block)` nos 4 sites. Verificado: no caminho
  normal de build/retag o `timeline_index` vem do **runtime** (`_build_timeline_index`,
  index.py:1450), que NÃO remove admin nem grava a chave — logo o filtro atual é no-op e
  blocos administrativos (feriado/prova) vazam como candidatos do scorer material→bloco.
  O predicado funciona em blocos runtime (lê `rows`) e é inofensivo em blocos serializados
  (sem `rows` → False, e ali admin já foi removido no `_serialize`). Sem mudança de
  serialização.

## Princípios e constraints (toda fase)

1. **Rede de medição:** golden de bloco **41/48, confiante-errado 0** + suíte (~1332)
   verde após cada fase. `scripts/eval_*` + golden já existem e são rodáveis.
2. **Eval-gate:** qualquer mudança que altere candidate set ou atribuição real → rodar
   `scripts/eval_*` + golden + **censo de bands de subunit no repo real** antes de mergear.
3. **Fonte única + precedência explícita:** cada fix elimina um "segundo cérebro" ou uma
   leitura divergente. Um dado de atribuição = um campo canônico, lido na mesma ordem por
   todos os consumidores.
4. **Modularidade:** fixes gerais, zero hardcode de cadeira.
5. **Branch:** nova branch por fase a partir da atual (`feat/reconciliar-unit-bloco`),
   merges pequenos e frequentes.

---

## Fase P0 — estrutural (causas-raiz)

Ordem: **P0.4 → (P0.1 + P0.2) → P0.3.**

### P0.4 — Dedup de id no batch (fix c)
Barato, independente, sem eval.

- **Defeito:** `_dedup_entry_id` só roda no caminho single-entry
  (`lifecycle_ops.process_single_impl:101-108`); os builds batch (`build_workflow.py:64`,
  `incremental_build.py:48`) chamam `_process_entry` direto, sem dedup → ids duplicados
  (`introducao`×2, `t1-2026-1`×2 — pdf trabalhos + zip codigo-professor compartilham id,
  reintroduz B5: dirs de assets compartilhados).
- **Fix (implementado P0.4):** extrair helper `assign_dedup_id(entry, existing_ids)`
  (base_id=`entry.id()`; se colide → `entry.id_override = _dedup_entry_id(...)`; registra o
  id final no set). Chamar nos 2 laços batch **antes** de `_process_entry`: `build_workflow`
  semeia `existing_ids` vazio e acumula; `incremental_build` semeia com os ids do manifest
  existente e acumula os novos.
- **Atualização 16/06 — fix c v2 (sufixo por EXTENSÃO, não categoria):** a 1ª versão
  (mergeada) sufixava por **categoria**, o que (a) gera ids que parecem categoria
  (`exemplos-codigo-professor`) e (b) NÃO desambigua quando a colisão é mesma-categoria
  (`exemplos.thy` vs `exemplos.zip`, ambos `codigo-professor`; caso real do MF). Decisão:
  `_dedup_entry_id` passa a usar **cascata extensão → token da pasta → contador**
  (`introducao-zip`, `exemplos-zip`). Determinístico, no import, sem Gemini; o id vira
  significativo; só entries colididas mudam (sem churn nas demais). **Gemini NÃO define o id**
  (id nasce antes do Gemini, que é opt-in; precisa ser determinístico/estável — título de LLM
  mudaria o id entre runs → assets/curation órfãos). Gemini fica só no TÍTULO de display (P0.5).
- **Teste:** build batch com `introducao.pdf` + `introducao.zip` → ids distintos
  (`introducao`, `introducao-zip`). Sem impacto no scorer.

### P0.5 — Aba códigos: rótulo = `inferred_title` (display, opcional)
- **Defeito:** a aba códigos (`codes_panel.py`) usa `eid[:8]` como rótulo da linha → dois ids
  com prefixo igual (`exemplos.thy` e `exemplos.zip` → ambos "exemplos") parecem duplicados ou
  somem.
- **Fix:** rótulo da linha = `summary.inferred_title` (Gemini) com fallback pro id. Só display;
  não toca atribuição. O Gemini já gera `inferred_title` coerente do conteúdo (usado também em
  CODE_INDEX/CRONOGRAMA).

### P0.1 — Subunidade fonte-única (8º "segundo cérebro")
Eval leve (muda a exibição do FILE_MAP).

- **Defeito:** `computed_subunit_slug` gravado SEMPRE/ungated (content_taxonomy.py:1316);
  tag `subunit:` gravada só após gate (≥`SUBUNIT_TAG`=0.60, não-ambíguo;
  content_taxonomy.py:1278-1279). Leitores divergem: `navigation.py:623-625` (FILE_MAP)
  usa o ungated e ignora a tag; `dialogs.py:4154-4166` (editor) prefere a tag gated. Pior:
  `computed_subunit_slug` NÃO é campo declarado de `FileEntry` (core.py:75-76 só tem
  `subunit_match_confidence`/`reasons`) → round-trip `from_dict→to_dict`
  (fila/SubjectProfile/PendingOperation) descarta o slug e mantém a confiança (órfã).
- **Fix:**
  - Declarar `computed_subunit_slug` como campo de `FileEntry` (core.py), simétrico a
    `computed_unit_slug`/`computed_block_id` → sobrevive ao round-trip.
  - Unificar a ordem de leitura em `navigation.py` (FILE_MAP) E `dialogs.py` (editor):
    `manual_subunit_slug` > tag `subunit:` (gated) > `computed_subunit_slug` (best-effort).
    FILE_MAP passa a espelhar a tag gated; o computed best-effort não é mais exibido como
    atribuição no FILE_MAP (só "sugestão baixa confiança" no editor).
  - Escrita inalterada (mantém computed + tag); só alinha a LEITURA + declara o campo.
- **Eval:** censo de bands de subunit no repo real (a exibição do FILE_MAP muda; é a
  correção). Golden de bloco intacto (não toca bloco).

### P0.2 — `winning_unit_slug`: subunit restrita à unidade do bloco
Eval (muda subunit real).

- **Defeito:** `auto_map_entry_subtopic` (file_map.py:173-174) tem o parâmetro
  `winning_unit_slug` que filtraria os tópicos à unidade vencedora, mas **nenhum caller o
  passa** → a subunidade é escolhida sobre TODOS os tópicos de TODAS as unidades. Causa-raiz
  do desalinhamento subunit↛unit (hoje só avisado em dialogs.py:4143, nunca corrigido).
- **Fix:** ligar o parâmetro — o orquestrador (`content_taxonomy.py:1087`) passa a unidade
  resolvida da entry/bloco ao `auto_map_entry_subtopic`, restringindo os tópicos candidatos
  àquela unidade. A subunidade só pode vir da unidade do bloco. Entry sem unidade resolvida
  (órfã) → sem restrição (comportamento atual), confiança honesta. Reconciliação
  subunit↔unidade-do-bloco fica desnecessária pra novos computes; manter só como guarda
  opcional p/ legado.
- **Eval:** censo de bands de subunit no repo real (atribuições de subunit mudam). Golden de
  bloco intacto.

### P0.3 — D1: fonte única de bloco pra código (Gemini vira voto)
Eval (diff dos 3 .md de código no repo real).

- **Defeito:** bloco de entry de código decidido por dois sistemas que nunca reconciliam:
  `primary_block_id` (Gemini, `code_summarization.py:_consolidate_assignment`) governa
  CODE_INDEX.md / CRONOGRAMA_DETALHADO.md / contagem CODE_HEALTH (repo.py:837/913/994);
  `computed_block_id` (funil determinístico) governa todo o resto (`resolve_effective_block`,
  file_map.py:613). Mesma entry, bloco diferente conforme o .md.
- **Fix (decisão A):**
  - Artefatos (CODE_INDEX/CRONOGRAMA/CODE_HEALTH) passam a ler `resolve_effective_block`
    (`computed_block_id`).
  - `_consolidate_assignment` deixa de DECIDIR bloco. Gemini vira voto: **consensus**
    (bloco do Gemini == `computed_block_id` → method=consensus, sobe confiança); **llm_only**
    (funil órfão → grava o bloco do Gemini EM `computed_block_id`, method=llm_only). Tudo lê
    um campo só.
  - Mantém a extração de SINAL do Gemini (`inferred_title`/`concepts`/`summary`/`language`)
    — alimenta o scorer de subunit e `code_curation_signal_text` (intactos).
  - Subsume os mortos P1.6: `consensus` branch B e o method `auto_concept`/tooltip são
    revisitados aqui (a lógica de método de código é reescrita).
  - Resolver na implementação: `source_importers.py:75-81` (onde escreve o bloco do Gemini?
    se em `computed_block_id`, é um 4º ponto de escrita a unificar).
- **Eval:** diff do agrupamento de código nos 3 .md no repo real (Metodos-Formais);
  golden de bloco do funil intacto; medir entries de código órfãs afetadas pelo llm_only.

---

## Fase P1 — morto/contrato (barato; maioria não toca o scorer)

- **P1.1 — `administrative_only` (D2=A uniforme):** trocar `block.get("administrative_only")`
  por `_timeline_block_is_administrative_only(block)` nos 4 sites (`content_taxonomy.py:1144`
  crítico; `file_map.py:537`, `cronograma_health.py:124`, `moodle_labels.py:131`).
  *Eval-gate* (candidate set encolhe; pode melhorar atribuição).
- **P1.2 — `BLOCO_TAG` morto (thresholds.py:139): DELETAR** (constante + refs de teste). A
  band já carrega a honestidade; gatear a tag `bloco:` esconderia o bloco de quem agrupa por
  ela (FILE_MAP). "Emite sempre, band diz a confiança" é o comportamento correto. Sem impacto
  no output.
- **P1.3 — piso 0.72 (file_map.py:1354): REMOVER o piso.** O cap `scorer_only=0.70` é
  principiado (plano-mestre P2). O piso já está morto (sempre rebaixado pelo cap) → remover é
  no-op no output → golden idêntico garantido.
- **P1.4 — fallback keyword ~600 linhas (index.py:2205-2213):** substituir por default
  trivial (unidade vazia, confiança honesta) + **deletar** `_assign_timeline_block_to_unit`,
  `_vote_unit_from_topic_candidates`, `_score_timeline_row_against_unit`. Só é alcançável
  quando `assign_units_positional` retorna [] (<2 unidades / 0 blocos / afinidade-zero
  global). *Eval-gate forte*: guard test confirmando que `assign_units_positional` nunca
  retorna [] nos cursos do golden ANTES de remover. Maior item do P1.
- **P1.5 — `auto_suggested_unit` gate obsoleto (conflicts.py:31-44):** ler `auto_unit_slug`
  direto, deletar o ramo topic-derive morto (gate 0.65 inalcançável porque
  `assign_units_positional` sempre grava `auto_unit_slug`) + corrigir docstring. Baixo risco.
- **P1.6 — mortos menores:** `process_reference_entry` (reference_summary.py:56) — confirmar
  0 callers em `tests/`, então deletar. `consensus` B e `auto_concept`/tooltip → tratados no
  P0.3 (D1 reescreve `_consolidate_assignment`).

---

## Fase P2 — duplicação (eval-gated; golden idêntico obrigatório)

- **P2.1 — família de 6 scorers:** unificar núcleo. Começar pelos 3 leves
  (`assign_code_to_block`, `assign_concepts_to_unit`, `assign_concepts_to_block`) →
  `overlap_score(bag_entry, bag_target, *, conf_fn)` parametrizado por bag/pesos/fórmula de
  confiança. Depois avaliar os 3 ponderados (index.py:1618, file_map.py:236, index.py:1730) —
  pesos afinados em P2/P4, golden-idêntico obrigatório. Coordena com P0.3 (D1 muda o papel de
  `assign_code_to_block`).
- **P2.2 — 3× basename→source_section:** helper `match_basenames_to_sections(entries,
  name_to_section)` (núcleo: Counter/casefold/ambiguidade/grava `source_section`); cada fonte
  (stash_backfill.py:16, moodle.py:156, m365.py:271) só monta o dict `name_to_section`.
- **P2.3 — 2 rotas card→bloco:** restringir `lookup_card_blocks` ao map persistido
  (`derive_card_block_map`, datas, autoritativo); card-sem-map cai no scorer de conteúdo como
  qualquer arquivo — não alimentar o palpite léxico só-nome (`resolve_card_to_block`,
  card_block.py:62) como autoritativo @0.80. *Eval-gate.*
- **P2.4 — predicados de kind index vs classifier:** unificar sobre `classify_block`/
  `BlockKind` (vocabulário único; hoje index aceita "prova 1/2"/"teste", classifier exige
  "prova N"). *Eval-gate* (muda elegibilidade).
- **P2.5 — menores:** constante única para `is_exercise_entry` (lista de 6 termos hoje
  repetida 3-4×); helper para `entry_norm`; helper `significant_tokens` (filtro len≥4, ~5
  sites); unificar os 3 tokenizadores (unit_matcher/file_map/index). Mecânico, golden-idêntico.

---

## Fase P3 — ruído (eval-gated; cada um isolado atrás do golden)

- **P3.1 — auto_tags self-confirmation:** excluir os prefixos gerenciados (`unit:`/`subunit:`/
  `bloco:`) do `auto_tags_text` antes de pontuar (index.py:1755,1801). Mata o viés de
  auto-confirmação em retag.
- **P3.2 — `llm_only` conf 0.6:** rebaixar para <banda alta (ou derivar do voto). Coordena
  com P0.3.
- **P3.3 — precedência de source_section:** API Moodle autoritativa sobre m365 (resolvido
  junto com P2.2, ao centralizar o helper). Hoje m365 sobrescreve por ordem de execução.
- **P3.4 — "trabalho"→DELIVERABLE (classifier.py:77-82):** exigir frase, não token isolado
  (hoje zera a unidade de aula legítima que mencione "trabalho").
- **P3.5 — restante:** canal de data duplo (file_map.py:1297+1311); herança bidirecional em
  soft-continuation (index.py:2218 → preferir só `previous`, preservando a monotonicidade do
  DP); substring em fontes fracas (file_map.py:700 → exigir match de token nas fontes
  tags/category); pisos de confiança hardcoded → centralizar em thresholds.py.

---

## Testing (toda fase)

- Cada item: teste unitário + golden de bloco (`scripts/eval_*` / fixture) + (itens de
  subunit) censo de bands de subunit no repo real.
- P0.4: teste de colisão de id no build batch.
- P1.4: guard test (`assign_units_positional` nunca [] nos cursos do golden).
- Critério de aceite por fase: suíte verde + golden de bloco 41/48 não regride +
  confiante-errado segue 0.

## Não-problemas confirmados (fora de escopo — não mexer)

- Referências (Approach C) NÃO contaminam a atribuição principal (isolamento em 3 níveis).
- `margin_confidence` vs `relative_margin_confidence`: escopos disjuntos, intencional.
- METHOD_CAPS não tornam banda alta inalcançável.
- Os 3 "segundos cérebros" do FILE_MAP já mortos não ressurgiram.
- `image_resolution.py`, `semantic_config.py`: periféricos, não-core.

## Riscos

- **Golden de 1 cadeira (Metodos-Formais):** calibração pode enviesar. Itens eval-gated que
  mudam pesos/candidate set correm esse risco; mitigação = golden-idêntico onde possível e
  censo de subunit no repo real.
- **P0.3 (D1):** mudar a leitura dos artefatos de código pode reagrupar entries onde
  Gemini×funil divergiam — é a correção, mas precisa de diff revisado no repo real.
- **P1.4:** remoção de ~600 linhas só após o guard test provar o fallback inalcançável nos
  cursos reais.
