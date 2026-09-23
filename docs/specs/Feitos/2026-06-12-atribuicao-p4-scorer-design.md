# Spec — P4: limpeza do subsistema + 5 sinais novos no scorer de bloco

date: 2026-06-12
status: aprovada (brainstorm 12/06; escopo "4 sinais completos" + ferramenta + limpeza pedida pelo usuário)
base: plano-mestre (P4 aprovado pelos números: 8-10 dos 12 erros do golden têm mecanismo aqui)
rede: golden v1 (36/48 = 75.0%, confiante-e-errado 0) + suíte 1294 + inventário de
código morto (sessão 12/06, 5 mortos / 9 duplicados / 6 suspeitos)

## Metas

| Métrica (golden, 48 casos) | Hoje | Meta |
|---|---|---|
| Acurácia | 36/48 (75.0%) | **≥ 43/48 (~90%)** |
| Confiante-e-errado | 0 | 0 (manter) |
| Regressão em casos hoje certos | — | 0 |
| Suíte | 1294 | verde, sem afrouxar teste |

Caso emblemático que TEM que sarar: `logicadehoare` (hoje bloco-11 conf 0.03;
anatomia provada: 27.4/26.5/26.1/23.9 com o certo em 4º) → bloco-10 com margem.

## Fase 0 — Limpeza (pré-requisito dos sinais)

Razão: os sinais novos mexem em tokenização e pesos; com helpers duplicados o
sinal muda num caminho e não no outro (mesma doença do B1/match_card/FILE_MAP).

### 0.A Deletar (mortos confirmados, zero call sites de produção)

- `extract_date_prefix_signal` (entry_signals.py:119) + tests/test_date_prefix_signal.py
- `scripts/backfill_source_section.py` (superado pelo backfill via API)
- `scripts/eval_cards.py` + tests/test_eval_cards.py (superado pelo eval_assignments)
- `T.MATERIAL_COVERAGE_MIN` (thresholds.py:111) + assert correspondente no teste
- Flag `processing_profiles_seeded_v2` (helpers.py:706-712 + theme.py:94) — no-op de migração já consumida

### 0.B Unificar (duplicados que ameaçam o P4)

1. **`normalize_match_text` — 4 redefinições além da fonte única** (text/normalize.py):
   content_taxonomy.py:26 (DIVERGENTE: preserva `+-./`), vision/card_evidence.py:12,
   image_markdown.py:45, timeline/signals.py:36. Unificação: todas re-importam da
   fonte única. A divergência da taxonomy precisa de investigação de 1 nível
   (por que preserva `+-./`? se houver razão real — ex. versões "1.2", "c++" —
   vira PARÂMETRO da fonte única, não cópia). Golden + suíte são a rede; medir
   antes/depois da unificação ISOLADAMENTE (é mudança de comportamento potencial).
2. `_NO_TIMELINE_CATEGORIES` — navigation.py:614 importa da taxonomy (matar o literal).
3. `_signal_token_set` (content_taxonomy:582 ≡ index:93) e `_extract_markdown_headings`
   (content_taxonomy:42 ≡ entry_signals:43) — uma definição, re-importada.
4. Fórmula de margem inline em index.py:1973 → `margin_confidence(..., k=T.MARGIN_K_TOPIC)`
   (a constante existe e nunca foi usada).
5. Literais que ignoram thresholds: content_taxonomy.py:1158 (`0.65`→`T.UNIT_TAG`),
   :1040 (`0.60`→`T.SUBUNIT_TAG`); `_vote_unit_from_topic_candidates` recebe
   `T.VOTE_MIN_SCORE`/`T.VOTE_DOMINANCE`; `DATE_STRONG_BOOST`/`DATE_WEAK_BOOST`
   migram pra thresholds.py.
6. `CARD_SINGLE_CONF` (content_taxonomy:848) passa a LER `METHOD_CAPS["card"]`
   (acoplamento manual de 0.85 em 2 módulos morre).

### 0.C Fica como está (suspeitos que são decisão, não lixo)

`margin_confidence`×`relative_margin_confidence` (coexistência documentada),
`score_sequence_match(boost=)` (parâmetro de calibração), `eval_ground_truth.py`
(decisão de harness canônico fica pro fim do P4), números mágicos de index.py:1979/2079
(unidade — fora do escopo bloco).

Critério de aceite da Fase 0: suíte verde, golden IDÊNTICO (36/48, mesmos erros)
— limpeza não pode mudar resultado; se mudar, investigar antes de seguir.
Exceção: a unificação do normalize divergente (0.B.1) PODE mudar — medir isolada.

## Fase 1 — Sinais (um por task, MEDIR após cada)

### S1 — CamelCase na tokenização do título

`split_camel_case(text)` novo em text/normalize.py (aditivo; NÃO muda
`normalize_match_text`): insere espaço em fronteiras minúscula→Maiúscula e
letra→dígito ("LogicaDeHoare2"→"Logica De Hoare 2"). Aplicado aos TÍTULOS na
coleta de sinais da entry (entry_signals), antes da normalização. Medir efeito
em bloco E unidade (título alimenta ambos); se a unidade regredir no golden,
restringir ao caminho de bloco.

### S2 — IDF/raridade no scorer de bloco

No scoring temporal (`score_entry_against_timeline_block`/`score_timeline_block`):
peso do token ∝ 1/(nº de blocos candidatos cujo topic_text contém o token).
Computado UMA vez por chamada sobre o conjunto candidato (mesma mecânica do
`token_weights` do scorer de unidade, file_map.py:136-140). "hoare" (1 bloco)
≫ "logica" (3+).

### S3 — Normalização por tamanho do topic

Contribuição do `topic_text` dividida por `sqrt(nº de tokens do topic)` —
desinfla topics verbosos (blocos 13/15) que hoje vencem por superfície.
Constante de calibração em thresholds.py.

### S4 — Sinal de ferramenta

As entries JÁ têm `auto_tags ferramenta:` (hoare, isabelle, dafny...). Usar no
score de bloco: ferramenta da entry presente nos tokens do topic do bloco →
boost forte; entry com ferramenta X e bloco com ferramenta Y disjunta →
penalidade. Mapa de equivalência mínimo (`.thy`→isabelle; `.dfy`/dafny→dafny)
em thresholds/constante. Conserta `provas`.thy (05→06) e reforça dafny→13.

### S5 — Janela de assign (trabalhos)

Parser (moodle_labels ou módulo irmão): cascata de fontes do deadline —
(1) `assign.dates[duedate]` da API; (2) regex `\((\d{1,2}/\d{1,2})\)` no NOME de
módulo de entrega (forum/assign "Sala de Entrega (10/06)"); (3) data avulsa no
label do card (parser A já captura). Persistido junto do card map
(`.card_block_map.json` ganha campo opcional `assign_due` por card, ou arquivo
irmão — decidir no plano pelo que for menor).
Consumo no funil: entries de categoria trabalho (e código do mesmo card) ganham
RESTRIÇÃO — candidatos = blocos de aula com `period_start` < duedate — e o
scorer decide dentro (validado: T1 duedate 06/05 + conteúdo Isabelle → bloco-06).
Sem fonte de deadline → sem restrição (scorer puro, como sempre). NUNCA decide
sozinho (heurística "último bloco antes do prazo" foi REPROVADA em demo real).

## Sequência e medição

```
Fase 0 limpeza (golden idêntico) → S1 CamelCase → MEDIR → S2 IDF → MEDIR
→ S3 tamanho → MEDIR → S4 ferramenta → MEDIR → S5 assign → MEDIR final
→ retag no repo real de MF + atualizar placar do plano-mestre
```

Pesos/calibração: constantes nomeadas em thresholds.py, valores justificados
pelo golden (anotar no commit de cada sinal). Se um sinal REGREDIR o golden,
não avança — recalibra ou reverte (commit por sinal facilita bisect).

## Riscos

- Coração do matcher: mitigado por sinal-por-task + golden + commit por sinal.
- Unificação do normalize divergente pode mudar matches fora do bloco
  (unidade/tópico/cards): medir isolada na Fase 0, com a suíte como rede.
- Overfitting ao golden de 1 cadeira: pesos conservadores; segundo golden segue
  como dívida; o sinal de assign foi validado em 2 cadeiras (MF, exemplo do
  usuário).
- CamelCase em títulos que não são CamelCase reais (siglas "IHC", "P1"): o
  split só em fronteira minúscula→Maiúscula preserva siglas puras.
