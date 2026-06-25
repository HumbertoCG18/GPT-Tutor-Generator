# Estado da atribuição material→bloco (foco: IA)

as-of: IA reprocess `7561f5c` · código `feat/block-stable-id` HEAD `d5d61f0` · 2026-06-22
modo: READ-ONLY. Nenhum repo tutor tocado. Toda afirmação cita `arquivo:linha` ou artefato de dado.
nota de path: o produtor é `src/builder/extraction/content_taxonomy.py` (NÃO `routing/`).

---

## 1. Fluxo de atribuição (trace vivo)

Dois produtores rodam em sequência. **Ambos pontuam UM arquivo por vez** contra o conjunto de blocos.

### Produtor A — seed lexical (`extraction/content_taxonomy.py`, `resolve_unit_block_tags`)
```
entry + markdown + timeline_index.blocks
 → pin manual?            file_map.py:517 resolve_entry_manual_timeline_block → content_taxonomy.py:1143  (method=manual, conf=1.0, CURTO-CIRCUITA)
 → filtro instrucional    content_taxonomy.py:1156   (dropa administrative_only)
 → clamp janela-entrega   content_taxonomy.py:1172   (period_start < assign_due)
 → regra de revisão       content_taxonomy.py:1185   (conf 0.95)
 → bloco por CARD         content_taxonomy.py:1193   (_card_scoped_block @879, usa source_section)
 → scorer primário ≥0.95  content_taxonomy.py:1208   (select_probable_period_for_entry @file_map.py:1266)
 → fallback "pega o melhor" content_taxonomy.py:1235  (_best_instructional_block_fallback @811 — FORÇA vencedor)
 = computed_block_id      content_taxonomy.py:1260 → escrito :1344
```

### Produtor B — re-pass conceitual (flag `use_concept_resolver`, `concept_resolver.py:256`)
```
entry signals + blocks + units + llm_curation + lessons_index
 → tier manual            concept_resolver.py:270
 → score fundido por bloco concept_resolver.py:336   = W_CONCEPT·overlap + W_LLM·voto + data + seq + card + lesson
 = Assignment.block_id    concept_resolver.py:426 → escrito resolver_apply.py:134
```

### Consumo
- campo: `core.py:87` (`computed_block_id`). Escritores: `content_taxonomy.py:1344`, `resolver_apply.py:134`, `pedagogical_regeneration.py:176` (override Gemini só quando band=baixa).
- leitores: `file_map.py:559 _entry_computed_block_id` → `resolve_effective_block` (:595); `repo.py:838/927/1026`; `navigation.py:658`; `dialogs.py:4222`.

### Cadeia conteúdo → bloco → unidade — EXISTE
A unidade é **herdada do bloco vencedor**: `reconcile_unit_with_block` `file_map.py:639-681` (auto sem unidade → herda do bloco `:671`), chamado em `content_taxonomy.py:1277-1286`.

### Precedência de leitura (efetivo)
```
temporal_block_id (âncora, flag) > manual_timeline_block_id > computed_block_id > auto_tags["bloco:"]
       resolve_temporal_block file_map.py:633   |   resolve_effective_block file_map.py:594-614
```

### PASSO FRÁGIL (sintoma vs causa)
- **Sintoma:** um arquivo cai na semana errada enquanto os irmãos acertam; arquivos de baixa confiança são **forçados** a um bloco (nunca ficam órfãos).
- **Causa-raiz:** **argmax por-arquivo independente** — `_best_instructional_block_fallback` (`content_taxonomy.py:811`) / `select_probable_period_for_entry` (`file_map.py:1266`) rankeiam CADA arquivo sozinho contra todos os blocos; o fallback "pega o melhor" (`content_taxonomy.py:1235`) garante vencedor mesmo quando o gate ≥0.95 recusa (`file_map.py:1427`). **Não há agrupamento por sessão/semana.**
- **Propagação:** a unidade é herdada desse bloco possivelmente errado (`file_map.py:671`) → 1 arquivo mal-pontuado leva junto a unidade errada.

---

## 2. Inventário de sinais

| sinal | lido p/ placement? | onde |
|---|---|---|
| conteúdo (título+markdown, overlap léxico + IDF) | SIM (principal) | `file_map.py:926-1057 score_entry_against_timeline_block` |
| unidade (boost ±) | SIM (boost dentro do scorer) | `file_map.py:961-965` |
| datas | SIM | `file_map.py:1078-1102` |
| léxico prova/exercício | SIM | `file_map.py` (scorer) |
| card-evidence | SIM | `file_map.py:737-797` |
| `source_section` (nome da seção/Semana) | SIM | ver Roteiro abaixo |
| pin manual (`manual_timeline_block_id`) | SIM (vence, conf 1.0) | `content_taxonomy.py:1143`, `concept_resolver.py:270` |
| Roteiro dia-a-dia (corpo) | parcial, via lessons_index | `concept_resolver.py:106-133` |

### Roteiro — VEREDITO: **READ-FOR-PLACEMENT (parcial)**
O **nome da seção** (`source_section`, ex. "Semana 16 - … - Algoritmos de Busca e Agentes") É lido p/ decidir o bloco, em 2 caminhos de produção:
1. **card scoping autoritativo** — `content_taxonomy.py:890` (`card = entry["source_section"]` → `lookup_card_blocks`; 1 bloco mapeado → retorna direto, conf 0.85, method `card`). Pode **decidir o bloco sozinho**.
2. **scorer conceitual fundido** — `concept_resolver.py:314-321` (tokens da seção entram no `entry_vec`, peso `SECTION_CONCEPT_FRAC=0.35`, movem o ranking).
3. âncora "Semana N" — `anchor_placement.py:295-308` — **NÃO wired em produção** (docstring :16, só canário IA).

**MAS** o **corpo dia-a-dia do Roteiro** ("15/06 - Busca; 17/06 - Agentes") **NÃO** é parseado linha-a-linha pelo placement. Só entra (se entrar) pelo `lessons_index` (`concept_resolver.py:106-133`), que chaveia por label+título do Moodle — e a alavanca de lessons está **dormente** (ver pendencias, alavanca 0). → o roteiro fino da professora é **subutilizado**.

### Confiança — EMITIDA e CONSUMIDA (NÃO é lacuna de existência)
- **emitida:** `relative_margin_confidence` `thresholds.py:20-31`; bands `alta`≥0.50 / `media`[0.20,0.50) / `baixa`<0.20 `thresholds.py:118-131`; tetos por método `METHOD_CAPS` (manual 1.0, card 0.85, scorer 0.70). Persistida `content_taxonomy.py:1345-1346` (`computed_block_confidence`/`_band`).
- **consumida:** `cronograma_health.py:205-233` lista "Materiais de baixa confiança (revisar)" (bands media/baixa, `_REVIEW_BANDS` :19), escrita em `course/CRONOGRAMA_HEALTH.md` (`pedagogical_regeneration.py:469-477`). Também gate de auto-remediação Gemini (band baixa) `pedagogical_regeneration.py:171-184`.
- **LACUNA REAL (não ausência, mas cobertura):** (a) é relatório MD estático, não fila interativa com estado resolvido/dispensado; (b) confiança = **margem léxica**, não probabilidade calibrada; (c) `_REVIEW_BANDS` **exclui `alta`** — e os erros do golden vieram justamente da band `alta` (`thresholds.py:43-49`). O ponto-cego está no que a revisão NÃO mostra.

---

## 3. Dump das atribuições atuais (IA) — DIAGNÓSTICO

Arquivo: `docs/reports/estado_atribuicao_IA.csv` (50 linhas).
Colunas: `arquivo | topico_cronograma | bloco_computado | pin_manual | bloco_temporal | datas_bloco`.
⚠️ **RETRATO DO SISTEMA — NÃO é o gold.** Vaza a predição (computed/pin/temporal). NÃO mesclar nem mostrar na planilha de rotulagem cega.

---

## 4. Merges espúrios — 4 blocos cobrem >1 seção do cronograma

| bloco | kind | datas | nº seções | seções absorvidas |
|---|---|---|---|---|
| **bloco-05** | class | 18/03→15/04 | **6** | Semanas **3,4,5,6,7,8** (kNN+perceptron+MLP+árvores+superv.+NÃO-superv.) |
| bloco-04 | class | 11/03→16/03 | 3 | Semana 2, Semana 3, TDE |
| bloco-06 | suspended | 20/04→27/04 | 2 | Semana 8, Semana 9 |
| bloco-15 | class | 01/06→08/06 | 2 | Semana 14, Semana 15 |

- **bloco-05 é o pior** — funde 6 semanas (18/03–15/04). Engole o supervisionado inteiro E parte do não-supervisionado (Semana 8). É por isso que kNN/perceptron/MLP/árvores caem todos no mesmo bloco — e o `artigo-agrupamento` (clustering, Semana 8) pinado em 05 está nessa zona de sobreposição com bloco-06.
- bloco-15 confirma S14+S15 (suspeito conhecido). bloco-06 sobrepõe S8 com bloco-05.

---

## 5. Checklist de problemas conhecidos (verificado vivo)

| item | veredito | evidência |
|---|---|---|
| **5 pins do IA** | **VÁLIDO** | `manual_timeline_block_id` live: bloco-01 `oracle`+`ia-responsavel` (refs); bloco-05 `artigo-usando-k-nn-em-texto`+`artigo-usando-agrupamento`; bloco-08 `p1-2024-02-ia`. (campo é `manual_timeline_block_id`, não `manual_block_id`.) |
| **artigo-agrupamento@05 deveria ser bloco-06?** | **VÁLIDO (suspeito), agravado** | clustering=bloco-06; mas bloco-06 está `suspended` (alvo inválido) E bloco-05 absorveu a Semana 8 (não-superv.). Pin humano — adjudicar no gold. |
| **bloco-06 suspended por 1 sessão** | **VÁLIDO** | causa-raiz = **heurística de texto** no token "suspensao" (`classifier.py:60`), NÃO source_kind. A linha 20/04 é tipada "Aula" no SARC (`ATIVIDADE_KIND_MAP` sem "suspens", `helpers.py:425`); `_aggregate_source_kind` retorna "" (`index.py:258-264`); o classifier cai no keyword e casa SUSPENDED. **Só bloco-06 mistura suspensão+aula no IA (1 bloco).** |
| **Staleness `.timeline_index` ≠ SYLLABUS/KB** | **VÁLIDO** | janela 24–29/06: SYLLABUS/KB têm 24/06=Feriado + 29/06=T2; timeline tem 24/06=T2 (bloco-19) + 29/06=aula (bloco-20). Mesmo reprocess, curation vazia → 2 caminhos de SARC divergem. |
| **eval lê CRU ou resolve?** | **HEAD=CRU; patch preparado não commitado** | HEAD `eval_ground_truth.py:27` = `str(e.get("computed_block_id",""))`. Working-tree (M, não commitado): `:72` `resolve_temporal_block` + `_canon` uuid↔bloco-NN, labels canon `:203`. |

---

## 6. Prontidão do eval

- **harness roda?** SIM — `python scripts/eval_ground_truth.py <repo_root> <labels.csv> [--json]` (uso impresso).
- **falta p/ rodar o gold do IA:**
  1. `tests/fixtures/eval/ground_truth_IA.csv` — **AUSENTE** (só existe `ground_truth_MF.csv`). Rotular (dump cego pronto).
  2. **decidir** commitar o patch eval (resolve+canon) OU rodar CRU. Sem o patch: pins/temporal não creditados + uuid↔bloco-NN dá falso-miss.
  3. rodar `eval_ground_truth.py <IA> ground_truth_IA.csv --json`.

---

## LISTA DE CORREÇÃO RANKEADA

| # | sintoma | causa-raiz (`arquivo:linha`) | raio | bloqueia gold? | esforço |
|---|---|---|---|---|---|
| **1** | eval credita computed cru — ignora âncora/pins, uuid↔bloco-NN dá falso-miss | `eval_ground_truth.py:27` (HEAD); patch pronto no working-tree (`:72,:203`) | só eval | **SIM** | **P** (commitar patch já escrito) |
| **2** | bloco-05 funde 6 semanas; bloco-04/06/15 também → semana indeterminada p/ cada material | segmentação só quebra bloco em **mudança de kind** (`_row_is_standalone_kind` `index.py:659-663`); rows class de tópicos distintos NÃO quebram (sem split por fronteira de tópico) | **alto** (todo material em bloco merge) | não | **G** |
| **3** | arquivo isolado cai na semana errada e leva unidade errada junto | argmax por-arquivo: `content_taxonomy.py:811` / `file_map.py:1266`; vencedor forçado `:1235`; unidade herdada `file_map.py:671` | **alto** (todo material) | não | **G** |
| **4** | bloco-06 (clustering, 7 materiais) tipado não-acadêmico → some da vista do gabarito | heurística texto "suspensao" `classifier.py:60` + `ATIVIDADE_KIND_MAP` sem "suspens" `helpers.py:425` (sem precond. de row-feriado nem guarda de aula-presente) | médio (1 bloco IA; **código compartilhado→todos repos**) | não¹ | **M** |
| **5** | revisão de confiança não pega os erros reais (band `alta`) | `_REVIEW_BANDS` exclui alta `cronograma_health.py:19`; confiança = margem léxica não-calibrada `thresholds.py:20-49` | médio (cobertura de revisão) | não | **M** |
| **6** | timeline em snapshot SARC antigo (24/06↔29/06 trocados) | 2 caminhos de ingestão SARC divergem (SYLLABUS≠timeline, mesmo reprocess); linha exata a rastrear | baixo (0 material na janela) | não | **M** |
| **7** | artigo-agrupamento pinado em bloco-05 (supervisionado), clustering=06 | pin humano (`manual_timeline_block_id`) + downstream de #2/#4 | baixo (1 entry) | não | **P** (re-pin curation ou rótulo no gold) |

¹ #4 não bloqueia o gold **porque o dump cego sai do manifest cru** (50 entries, bypassa o filtro de kind). Mas é necessário p/ correção da vista/resolver.

### Leitura da lista
- **Único bloqueador duro do gold = #1** (commitar o patch eval, esforço P). Tudo mais é qualidade de atribuição, não cria-gold.
- **Maior ganho de acurácia = #2 + #3** (merges + argmax por-arquivo). São a mesma família: falta de **agrupamento por sessão/semana** como unidade de atribuição. Atacar juntos.
- #4 tem atalho durável já-existente (curation `manual_kind_override`, gateado pós-gold) e fix-de-código separado (guarda no classifier).
- #2 precisa de 1 trace adicional da função exata de segmentação (`index.py ~640-700`) antes de mexer.

— fim do mapa. Nenhuma correção aplicada.
