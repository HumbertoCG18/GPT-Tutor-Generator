# Inventário do que JÁ EXISTE no motor para os 5 passos do plano "teto do puro" (07/09, read-only)

Pedido do user: "o que já existe no código? não quero band-aid". Levantamento por leitura (subagente Explore), sem execução, sem edição.
Caminhos relativos a `src/builder/`. Eixo: BLOCO / UNIDADE / SUBUNIDADE.

## TEMA 1 — token genérico / boilerplate (toda noção de "token que pesa menos")

Fonte compartilhada: `text/stopwords.py` — `TIMELINE_GENERIC_TOKENS` (:12, bloco), `TIMELINE_UNIT_NEUTRAL_TOKENS` (:23, unidade),
`UNIT_GENERIC_TOKENS` (:35, unidade+sub+bloco), `UNIT_STRUCTURAL_TOKENS` (:51), `unit_generic_tokens_from_units` (:55, df >= 0,4 por curso),
`resolve_unit_generic_tokens` (:89, modo df|lista|ambos + nome do curso), `UNIT_MATCHER_STOPWORDS` (:108), `CARD_BLOCK_STOP` (:115),
`SHORT_FUNCTION_WORDS_PT` + `short_vocab_from_topic_labels` (:124/:131, allowlist inversa de siglas).
Definições INDEPENDENTES: `timeline/unit_matcher.py:21 _UNIT_GENERIC` · `routing/motor/disambiguator.py:26 _GENERIC_STEMS` (26 stems; usado por
motor, cobertura, subunidade) · `routing/anchor_placement.py:60 _GENERIC_STEMS` (8 stems, cópia, caminho legado) · `extraction/content_taxonomy.py:51
_UNIT_TITLE_GENERIC` + `:57 _STEMS` + `:61 _unit_title_core_tokens` · `content_taxonomy.py:214 _topic_support_tokens` (stem-5) · `:156/:598
generic_slugs` (perfil `tag_generic_slugs`) · `:599 course_norm` · `core/semantic_config.py:30 _SEMANTIC_TOKEN_STOPWORDS` (27, paralela) ·
`timeline/index.py:1771 _LABEL_STOP` + `:1791 _specific_tokens` · `index.py:403 _timeline_specific_tokens` · `index.py:1984 _TOPIC_FALLBACK_STOPWORDS` ·
`routing/file_map.py:127` e `:132` (inline, hardcoded) · `file_map.py:299 matched_specific_tokens` (x0,55 / x0,45) · `file_map.py:367 weight *= 0.2`
(neutros) · `routing/concept_resolver.py:28 FORMAT_TOKENS` · `motor/window_provider.py:119 _course_stems` · `disambiguator.py:126 drop = _toks(course_name)` ·
`text/tokens.py:16 motor_tokens` (declarado "tokenizador único"; só `disambiguator._toks` migrou).
df / raridade: `routing/thresholds.py:194 SUBUNIT_PROPAG_DF_MAX=0.25` (`resolver_apply.py:295/:213`) · `file_map.py:137-162 token_weights=1/df` (IDF entre
unidades) + `distinctive_tokens` (df==1) · `concept_resolver.py:149 rarity=1/freq` (IDF_WEIGHT) · `disambiguator.py:117 DATE_DF_MAX` · `stopwords.py:80`.
Exclusivo: `unit_matcher.py:169 exclusive` + `:175 so_dela` + `:187 sexcl` (unidade do bloco) · `resolver_apply.py:302` (subtópico) ·
`resolver_apply.py:205-212` (parte de rótulo) · `file_map.py:158 distinctive_tokens` (unidade da entry).

## TEMA 2 — unidade da ENTRY e conflito com o bloco

`file_map.py:458 auto_map_entry_unit`: (1) `explicit_unit_number:443` curto-circuito 0,95; (2) `score_entry_against_unit:260` por unidade (+ boosts);
(3) melhor tópico da unidade (`_score_entry_against_taxonomy_topic`, x0,85 se >= 0,25); (4) `confidence = relative_margin_confidence`, `ambiguous` se
rel_margin < 0,15 ou winner < 0,5; (5) override por tópico forte. `score_entry_against_unit`: pesos por campo (headings 1,8 / lead 1,6 / card 1,5 /
markdown 1,1 / title 1,0; frase exata headings 3,0 ... card 2,5); **IDF SIM: `token_weights[token] = 1/df` (df = nº de unidades com o token)**;
alias sem peso próprio (vale como rótulo); penalidades x0,55 (nenhum token específico) e x0,45 (1 só).
`file_map.py:752 reconcile_unit_with_block`: manual > has_manual_unit > sem bloco > herda > iguais > `unit_is_explicit` (unidade vence, registra
conflict) > **bloco decide** (`reconciliada_do_bloco`, registra conflict). **`block_confidence` é parâmetro MORTO** (comentário :800-806: comparação
removida; chamador passa 1,0 fixo em `resolver_apply.py:511`). `revisar.py:46 motivos_de`: sem-bloco > flag:<metodo> (exceto janela-1, llm-funil) >
**`conflito` se `unit_block_conflict` truthy** > sub-empate/ambigua. `revisar_de`: motivo -> duvida; `sync_changed` -> mudou; senão ok.

## TEMA 3 — escopo de prova, marcos e prazos

Cadeia de unidade dos blocos (`index._build_timeline_index:2240`): `assign_units_by_work_milestones` (F5: entregas "parte N" formando 1..K == unidades,
CONF_STRONG) -> senão `assign_units_positional` (DP monotônico, desvio de janela DETOUR_COST=2, âncora exclusiva ANCHOR_MIN_AFF=2/MARGIN=1, fallback
stem-6, CONF 0,8/0,6/0,4) -> senão zera; depois herança soft-continuation; `_apply_curation_overrides` -> `assign_units_around_pins` ->
`_apply_timeline_post_transforms` (`_promote_preexam_reviews` -> `_demote_non_preexam_reviews` -> `apply_assessment_review_scope`).
Escopo: `index.py:1170 assessment_scope_by_date` (Pk = unidades das aulas em (P(k-1), Pk], sem repetir; PS/G2/PF = tudo) · `:1223 link_review_scope` ·
`:1357 apply_assessment_review_scope` grava `scope_unit_slugs` (lido só por `artifacts/temporal_context.py:71` e `ui/timeline_dashboard.py:300`) ·
**`:1135 _assessment_scope_unit_slugs(declared_unit_numbers, unit_index)` = escopo DECLARADO no plano (já parseado; usado em :1668)**.
Prazo: `motor/due_window.py:38 tier2_due_scope` (trabalhos/provas, código em TDE) · `:104 resolve_due_window` (`_match_due`: file_dues por basename >
assign_dues por stem tN; varre blocos **pulando `_NON_CONTENT_KINDS` = {assessment, review} ∪ NON_ACADEMIC_KINDS**; containment -> `due-contain`
alta/media; senão último bloco de conteúdo anterior -> `due-straddle` media + flag). Ordem em `motor/apply.py:77-121`: pino > due-window >
resolve_unscoped(lexical=False) > fora de escopo > referência genérica > cache > `engine.resolve` > `_inherit_from_numbered_sibling`.

## TEMA 4 — ORDEM dos módulos/seções do Moodle

Escrita (Fase 3a): `models/core.py:133-135` campos `moodle_section_index`, `moodle_module_index`, `moodle_week_label`; `sources/moodle.py:300
backfill_moodle_structure_from_api` (run de labels datados " || "). Leitura no motor: **só 2 pontos** — `motor/card_stream.py:114-123` (agrupa por seção,
ordena por módulo; `card_windows`: âncora datada = faixa da seção; grupos com o mesmo week_label -> `_align:80` = **DP monotônica por FLUXO (categoria),
tokens em comum − 0,001·j, empate -> semana mais cedo**) e `motor/anchor_engine.py:85 resolve_general_section` (seção 0 -> 1ª aula). `moodle_module_index`
não é lido em mais lugar nenhum. A ordem produz **JANELA** (`provider_card`, fora da cascata; consumido em `anchor_engine.py:239` sem janela e `:278-291`
só em decisão FLAGADA, nunca preempta o voto; band alta -> media), nunca desempate direto. Cascata `window_provider._CASCADE`: manual > labels > data >
ordinal > topic; `narrow_window_by_unit` depois. `routing/sequence.py:33/63` (ordinal de aula, boost 0,20) é o único desempate por ordem. `irmao-card`
(`apply.py:135`) usa chave (seção, radical, número) do id, não o índice. `card_evidence` (`vision/card_evidence.py`, `file_map.py:901`) = bônus <= 0,45.

## TEMA 5 — subunidade: ordem das regras (`resolver_apply.py:533-577`)

1 manual · 2 meta -> vazio · 3 **1ª passada** `file_map.py:171 auto_map_entry_subtopic` restrito à unidade reconciliada (recusas: sem-sinal, empate-exato,
revisão sem assunto < 7,0, ambíguo rel_margin < 0,12) · 4 **2ª passada** `propagar_vocabulario_por_headings`: alias por token exclusivo (conf >= 0,7,
df <= 0,25, dono único, >= 2 confiantes) -> `_partes_de_rotulo` -> `_subtopico_nomeado_no_titulo` (**única que sobrepõe confiante**) -> re-scoring só
onde indeciso -> `_secao_nomeia_subtopico` (último recurso, só indeciso). **O tópico do BLOCO (`primary_topic_slug`, `topic_candidates`) NÃO é usado na
subunidade**; `file_map.py:1033 timeline_block_matches_preferred_topic` existe e está **sem chamador vivo** (embrulhado em `facade/teaching_timeline.py:82`,
chave não desempacotada em `engine.py:2332-2340`); `preferred_topic_slug` é só gate da tag.

## DUPLICAÇÕES (o band-aid que já existe)

1. Três filtros de "stem genérico" (disambiguator 26, anchor_placement 8, stopwords TIMELINE_GENERIC_TOKENS 40) sem código comum.
2. Cinco+ conjuntos de "genérico de unidade" (stopwords x3, unit_matcher `_UNIT_GENERIC`, content_taxonomy `_UNIT_TITLE_GENERIC`, file_map inline x2).
3. Duas stopwords "semânticas" paralelas (semantic_config 27 vs stopwords 40, ~60% sobreposição).
4. `_tokens` duplicado byte a byte: `timeline/card_block.py:34` e `timeline/block_identity.py:41`.
5. Oito tokenizadores paralelos (`text/tokens.py motor_tokens` "único"; unit_matcher; content_taxonomy stem-5; anchor_placement stem-8; index x2;
   resolver_apply x2; concept_resolver).
6. Três "df/raridade" (file_map 1/df, concept_resolver 1/freq, stopwords df>=0,4) + dois tetos (resolver_apply 0,25, disambiguator DATE_DF_MAX).
7. Três "token exclusivo de um dono" (unit_matcher exato+stem, file_map distinctive, resolver_apply subtópico).
8. Duas "a seção do Moodle nomeia X" (window_provider `unit_named_by_section`, resolver_apply `_secao_nomeia_subtopico`) com regex de prefixo próprias.
9. Duas regex de número explícito de unidade (file_map `_UNIT_NUM_*`, window_provider cópia).
10. Cinco leitores de `moodle_label` reimplementados (disambiguator, window_provider, moodle, resolver_apply, vocabulary_compile).
11. Duas extrações de data-no-nome (window_provider, moodle + card_stream).
12. Quatro "nome do curso é boilerplate" (window_provider, disambiguator, content_taxonomy, stopwords).
13. Duas heranças de unidade por vizinho (file_map `unit_of_block_or_neighbor`, index soft-continuation + demote).
14. Código sem chamador vivo: `file_map.timeline_block_matches_preferred_topic`; parâmetro `block_confidence` de `reconcile_unit_with_block`;
    `routing/anchor_placement.py` inteiro (só pela flag legada `use_anchor_placement`).
