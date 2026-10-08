# Auditoria-Enxame — Relatório Final

> Proveniência: workflow `auditoria-enxame` (run `wf_48318b37-7b8`), 2026-08-14, branch
> `feat/motor-atribuicao`. 45 agentes (7 finders em paralelo + 37 verificadores adversariais
> + 1 sintetizador), ~2.03M tokens, 468 tool calls, 0 erros. Mix de modelos: varredura e
> verificação em Sonnet (verify com effort high), síntese em Fable.

Branch `feat/motor-atribuicao` · 2026-08-14 · 7 dimensões varridas · **32 achados confirmados** por verificação adversarial · **5 refutados**. Ranqueado por severidade × esforço-inverso dentro de cada grupo.

> **DESEMPATE MANUAL (2026-08-14, pós-relatório):** o journal do workflow continha vereditos
> duplicados (pause/resume rodou alguns verificadores 2x) e 3 deles contradiziam itens
> confirmados. Verificação manual com evidência primária (leitura das linhas citadas + grep +
> git blame) decidiu os 3 — TODOS a favor do contra-veredito: **2.5 REBAIXADO** (sem corrupção
> cross-entry; deepcopy desnecessário — fica só 3.2), **2.2 FUNDIDO no 2.1** (write-per-entry é
> design deliberado de resiliência a crash, commits `10bec352`/`79b6f98` — nunca deletar a
> linha 83 isolada), **1.5(b) REESCOPADO** (test_block_scorer_signals.py tem 3 testes S4b que
> são a ÚNICA cobertura de extensão→ferramenta — mover antes de apagar). Itens marcados abaixo.

---

## 1. Pré-cutover (bloqueia/facilita campanha 3)

**1.1 [BLOQUEANTE] Campos de unidade são 100% produzidos pelo motor legado** — `src/builder/routing/resolver_apply.py:101-105` + `src/builder/extraction/content_taxonomy.py:1397,1424-1429`
Evidência: motor novo calcula `Assignment.unit_slug` (concept_resolver.py:178) e o descarta de propósito (resolver_apply.py:132-137 só lê block_id/confidence/band/method); UI real depende dos campos (navigation.py:643, dialogs.py:2487/3336, timeline_dashboard.py:828) com fallback silencioso para vazio.
Ação: Fase 4 (unit/subunit no motor novo) é pré-requisito duro; `resolve_unit_block_tags` não pode ser desligado antes dela. Sequência atual (legado incondicional → novo sobrepõe) também não pode ser reordenada.

**1.2 Gap de reconciliação unidade×bloco com `use_concept_resolver=True`** — `content_taxonomy.py:1354-1363` vs `resolver_apply.py:132-146`
Evidência: apply_concept_resolver sobrescreve `computed_block_id` sem re-rodar `reconcile_unit_with_block`; `unit_match_reasons`/`unit_block_conflict` passam a descrever o bloco antigo (lidos por dialogs.py:3348, 4113-4114). Hoje dormente (flag OFF em produção), ativa no instante do cutover.
Ação: re-rodar a reconciliação depois de apply_concept_resolver, ou movê-la para dentro de resolver_apply.py.

**1.3 Espelho `auto_tags` já tem drift real em produção (flag legada)** — `file_map.py:560-583` (espelho documentado) + `pedagogical_regeneration.py:242` (writer que quebra o invariante)
Evidência: attach_block_summary_fields troca `computed_block_id` (override Gemini, band baixa, code/zip) DEPOIS de resolve_unit_block_tags sem resincronizar a tag `bloco:`; nenhum teste cobre (test_attach_block_consensus.py não asserta auto_tags).
Ação: teste de invariante `computed_*` ↔ espelho em auto_tags + resync no attach_block_summary_fields.

**1.4 Scripts chamam o funil condenado direto, ignorando as flags** — `scripts/retag_manifest.py:44,54-67` · `scripts/eval_assignments.py:22,86-99`
Evidência: injetam `select_probable_period_for_entry` (símbolo na lista CONDENADOS do guard test); já marcado LEGADO-NÃO-USAR em pendencias.md:304-306 desde 2026-07-03.
Ação: portar para apply_concept_resolver ou aposentar no mesmo commit da deleção do funil.

**1.5 Mapa de deleção de testes para o cutover** — 3 lotes:
(a) `tests/test_temporal_block_wire.py`: cortar linhas 68-197 (8 testes, apply_anchor_placement + _course_year_from_blocks, legado-only), **manter 198-285** (`temporal_block_id` é contrato dos dois motores — lido por repo.py:927, cronograma_health.py:39, timeline_dashboard.py:225).
(b) **[REESCOPADO no desempate]** Apagar em bloco os 4 puros (911 linhas): `test_resolve_unit_block_tags.py`, `test_funil_gate_ambiguidade.py`, `test_resolve_unit_block_band.py`, `test_card_block_assignment.py`. `test_block_scorer_signals.py` NÃO é puro: os 3 testes S4b (linhas 273-301, `test_ferramenta_por_extensao_*`/`test_ferramenta_extensao_uniao_*`) chamam SÓ `collect_entry_unit_signals` (sobrevivente) e são a ÚNICA cobertura do sinal extensão→ferramenta (verificado: `test_entry_signals_materials.py` cobre image_description/moodle_label/notes, NÃO tool_tags) — **mover esses 3 pra `test_entry_signals_materials.py` (~30 linhas), aí apagar o arquivo em bloco**.
(c) `tests/test_file_map_unit_mapping.py` (2032 linhas): misto (símbolos condenados + sobreviventes) — auditoria função-a-função obrigatória antes de tocar.

**1.6 cronograma_health usa o scorer condenado como fallback** — `src/builder/artifacts/cronograma_health.py:114-181`
Evidência: `_candidate_refs` já prefere `temporal_block_window` (motor novo, apply.py:50) e só cai no S2 condenado para entries que não passaram pelo motor — dualidade documentada no próprio código.
Ação: na F4/5, portar o ranking para o scoring do concept_resolver ou aposentar quando 100% das entries tiverem janela.

---

## 2. Quick wins (baixo esforço, ganho real)

**2.1+2.2 [FUNDIDOS no desempate] Loop incremental: manifest inteiro reescrito + `_compact_manifest` O(N×M) a cada entry** — `src/builder/ops/incremental_build.py:77-78,83-84` → `src/utils/helpers.py:277-292` + `repo.py:587-604, 181-204, 518-584`
Evidência: 2 I/Os completos + ~10-13 `Path.exists()` × M entries, por entry processada (medido: write 32x mais lento; ~0.84s de puro stat para M=300/N=30).
Desempate (git blame verificado): o par compact+write por-entry é **design deliberado** de resiliência — `10bec352` ("logs and manifest timestamps are updated and written out immediately"; crash no meio → rerun pula concluídas via `existing_sources`) e `79b6f98` (write atômico anti-corrupção). Deletar só a linha 83 regride o saneamento por checkpoint e deixa `manifest["logs"]` crescer sem cap dentro do loop.
Ação (única): **checkpoint a cada N entries com compact+write JUNTOS** (N configurável; crash perde no máximo N-1 entries de trabalho — knob explícito da troca velocidade×resiliência). Nunca deletar a linha 83 isolada.

**2.3 Suíte de testes quase 2x mais rápida com 5 mocks** — `tests/test_core.py:2362,2376,2389,2403,2424` (classe TestBackendSelector) *(derivado de refutado corrigido)*
Evidência: import real de docling (~19-25s) em qualquer teste da classe sem mock de `available_backends`; mockar só o de 2362 apenas migra o custo pro próximo (cache global de processo).
Ação: replicar o `mock.patch.object(BackendSelector, 'available_backends', ...)` dos vizinhos 2326/2344 nos 5 testes não-mockados.

**2.4 `_load_timeline_blocks` engole qualquer exceção sem log e finge curso sem cronograma** — `src/builder/engine.py:1831-1840` (7 call-sites) + cópia idêntica em `src/builder/core/code_summarization.py:343-354`
Evidência: `except Exception: return []` sem nem debug; JSON truncado/permissão faz temporal_context, resolução de bloco e bootstrap rodarem como se o curso não tivesse blocos; motor novo já loga (motor/context.py:24).
Ação: logar warning com path+exceção antes do `return []` nos dois lugares; considerar abortar quando o arquivo existe mas falha ao parsear.

**2.5 [REBAIXADO no desempate — mover para "Registrar e ignorar"] `annotate_class_ordinals` sobre subconjuntos** — `content_taxonomy.py:920` (via `scoped`, linha 984) · `file_map.py:1300,1307`
Desempate (verificado nas linhas): NÃO há corrupção cross-entry — os 2 consumidores re-anotam a lista exata que vão pontuar IMEDIATAMENTE antes de ler (`file_map.py:1307` anota a lista completa antes do scoring 1329+; `content_taxonomy.py:920` anota e pontua a mesma lista em 932-949); grep prova que `class_ordinal` não é persistido nem tem outro leitor (só `score_sequence_match`, sempre pós-anotação). Deepcopy é desnecessário; o `resolver_apply.py:110` do motor novo é defensivo, não evidência de bug no legado.
Bug real residual = **3.2** (numeração 1,2,3 relativa ao subconjunto do card no caminho `card+scorer` — auto-contido a 1 entry, tie-break "Aula N" ocasionalmente errado dentro do próprio card). Fix certo lá, não deepcopy aqui.

**2.6 Loaders de artefatos-fonte silenciosos degradam o tier `card` sem rastro** — `src/builder/timeline/card_block.py:149-156` + causa-raiz também em `src/models/tag_profile.py:70-74` e `code_summarization.py:332-335` (o try/except externo em `content_taxonomy.py:1111-1133` é quase inalcançável — os loaders já engolem antes)
Evidência: `.card_block_map.json` corrompido vira "sem overrides de card" para todo o manifesto (shift em massa para `scorer_only`), sem log. Afeta só o legado — motor novo lê via load_repo_artifact, já corrigido (T2b).
Ação: logar path+tipo de exceção nos 3 loaders antes do default.

**2.7 `signal_token_set` reimplementado ~17x em file_map.py + 2 módulos, com fonte única já existente** — `file_map.py` vs `text/normalize.py:54-67`
Evidência: file_map.py importa `normalize_match_text` do módulo canônico mas nunca `signal_token_set`; padrão `{tok ... if len(tok)>=4}` inline.
Ação: troca mecânica segura APENAS nos sites de pertinência: file_map.py:226-234, 776, 785, 927-928 e `concept_resolver.py:100-104` (`signal_token_set(text, normalize=...) - _STOPWORDS`). **NÃO tocar** 707/992/1194 — são listas alimentando `score_text_against_row`, cujo scoring depende de multiplicidade (dedupe mudaria pontuação). anchor_placement.py:91-94 é legado condenado — pular.

**2.8 `score_card_evidence_against_entry` renormaliza texto já normalizado em toda combinação entry×bloco** — `file_map.py:749-809` (linha 782), usado pelos dois motores
Evidência: `item["normalized_title"]` já sai normalizado da extração (card_evidence.py:23, mesmos defaults) — a chamada é um no-op idempotente pago O(entries × blocos × cards); legado ainda multiplica por sessão (file_map.py:1228).
Ação: usar `normalized_title` direto, sem renormalizar.

**2.9 `auto_map_entry_unit` reconstrói o índice IDF de unidades a cada entry** — `file_map.py:367-382` (linha 382), chamado por entry em `content_taxonomy.py:1172`
Evidência: `unit_index` já vem pré-indexado de content_taxonomy.py:1091 (build_file_map_unit_index_from_course retorna o índice completo), mas a linha 382 reindexa do zero — 1.25ms/chamada × entries sem unit manual, resultado idêntico sempre.
Ação: reusar o índice já calculado (ou memoizar por `id(units)` no wrapper de facade/file_map.py:110).

**2.10 6 símbolos mortos de UI — deletar** —
`src/ui/image_curator.py:1650-1665` (classe ImageCurator, wrapper Toplevel morto; manter ImageCuratorPanel:256) · `src/ui/curator_studio.py:1464-1479` (CuratorStudio idem; manter Panel:225) · `src/ui/app.py:1084-1087` (open_repo_dashboard_tab, zero callers, aba já clicável nativamente) · `src/ui/app.py:2750-2765` (open_file_map — botão removido no commit 1df7035e; deletar ou re-wire, decisão de produto) · `src/ui/image_curator.py:1262-1283` (_preclassify + import órfão de classify_image na linha 17) · `src/ui/image_curator.py:1426-1489` (_extract_latex_single, superado por _describe_single_image).

**2.11 3 campos escritos e nunca lidos no approve-flow** — `src/ui/curator_studio.py:936-938,957,1176-1177`
Evidência: `approved_source_markdown`, `approved_at`, `review_status` — zero leitores no repo (whitelists de repo.py e _get_pending_entries não os incluem); nem participam do roundtrip FileEntry.
Ação: remover as escritas (ou criar o consumidor de auditoria, se essa era a intenção).

**2.12 Strip de acento (NFKD+combining) reescrito 6x fora da fonte única** — `normalize.py:31`, `helpers.py:252,445`, `semantic_config.py:76`, `timeline/signals.py:35`, `sanitization.py:363` (code_summarization.py:141-143 é variante diferente, excluir)
Evidência: core byte-a-byte idêntico nas 6; timeline/signals.py já importa normalize_match_text e MESMO ASSIM reescreve o core — uso real imediato para a extração.
Ação: extrair `strip_accents()` — **em `utils/helpers.py`** (camada baixa), não em builder/text, para não inverter a direção builder→utils; fazer os call-sites (incluindo normalize.py) chamarem.

**2.13 Redes de segurança de artefatos/golds sem asserção** —
(a) `write_deeptutor_export` (deeptutor.py:253, chamado em incremental_build.py:118 e build_workflow.py:128): há cobertura incidental anti-crash em test_core.py, mas zero asserts sobre `.deeptutor/` → teste smoke validando estrutura.
(b) 5 CSVs gold (`tests/fixtures/eval/gold_units_*.csv`): só consumidos pelo CLI manual scripts/eval_units.py:81; nenhum pytest → smoke gate rodando score_course contra os 5 com limiar mínimo, ou documentar como fora do escopo do pytest.

**2.14 Docstrings cruzados entre os dois normalizadores** — `text/normalize.py:8-38` ↔ `utils/helpers.py:441-446`
Evidência: propósitos genuinamente distintos (tokenização fuzzy vs chave exata com pontuação preservada — design deliberado, window_provider.py usa os dois); único cross-ref existente está enterrado em unit_matcher.py:30-33.
Ação: 2 linhas de docstring apontando um pro outro ("precisa remover pontuação → X; precisa preservar → Y"). Não fundir.

---

## 3. Estrutural (campanha própria)

**3.1 Cache de tokenização no concept_resolver (hot path pós-cutover)** — `concept_resolver.py:148-150,171,297,337-338` via `resolver_apply.py:113-127`
Evidência: corpus de blocos tokenizado 2x por chamada (weights + vector) e re-tokenizado do zero a cada entry material (~800x o mesmo texto); 0.61ms/chamada medido.
Ação: cachear a **lista de tokens** por bloco (não o vetor de pesos final — `tool_tokens` varia por entry e afeta o piso FORMAT_TOKENS) e eliminar a dupla passada dentro da chamada.

**3.2 Semântica de `class_ordinal` em subconjuntos (complemento do 2.5)** — `content_taxonomy.py:920,984` · `file_map.py:1300-1307` · consumidor sem re-anotação em `cronograma_health.py:158-159`
Evidência: mesmo com deepcopy, o ordinal fica relativo ao subconjunto card-scoped/due-windowed (1,2,3… do recorte ≠ posição real no curso), corrompendo `score_sequence_match` dentro da própria chamada.
Ação: anotar sobre a lista global ordenada e projetar no subconjunto — exige validação contra golds; escopo de campanha, não de patch.

**3.3 Unificação final de tokenização com multiplicidade** — `file_map.py:707,992,1194` + `entry_signals.py:17-42`
Evidência: scoring depende de listas não-deduplicadas (design pareado nos dois lados do duplo loop); só unificável com variante de `signal_token_set` que preserve multiplicidade + golds para provar não-regressão.
Ação: só dentro da campanha de consolidação de tokenizadores, nunca como troca mecânica.

---

## 4. Registrar e ignorar

**4.1 Stemming com 3 profundidades (5/6/8)** — `content_taxonomy.py:223-229` · `disambiguator.py:25-42` (calibrado: 84.2%/78.9% medidos) · `window_provider.py:90` · `anchor_placement.py:54` (legado, morre na FASE 5 — ROI negativo tocar). Não fundir; extrair `prefix_stem(token, n)` só se mexer nesses arquivos por outro motivo.

**4.2 22 testes dependem de repos reais com fallback hardcoded pro home do Humberto** — `test_timeline_kinds.py:189` · `test_timeline_schema.py:109` · `test_unit_matcher.py:153,175`. Skip gracioso; CI já assume e documenta (validate-timeline.yml:8-9, fixtures determinísticos); existe 4º mecanismo sem hardcode (test_caracterizacao_blocos_atual.py). Ação mínima: nota no README de testes de que 22 testes só rodam com TUTOR_COURSES_DIR.

**4.3 Leads NÃO verificados adversarialmente (dos resumos por dimensão — investigar antes de agir):** `posting_date_created` só roundtrip; `approved_markdown`/`curated_markdown` escritos idênticos com heal duplicado em repo.py; fixture JSON órfã em tests/; `split_camel_case` reimplementado no motor novo; test_core.py monólito de 5630 linhas/59 classes.

---

## Refutados na verificação

- **card_block._tokens quebra o motor novo**: o bug de pontuação é real, mas `resolve_block_ref` (única função de card_block.py importada pelo motor novo) não usa `_tokens` — confinado ao legado; o fix de 1 linha segue válido como correção do legado.
- **Miolo de scoring 1215-1326 é "trabalho descartado" com a flag ON**: falso — `computed_block_id` do legado é gate de entrada do resolver_apply.py:116-117 e `computed_block_band` alimenta attach_block_summary_fields (incondicional); remover quebraria os dois caminhos.
- **backend_runtime.py sem nenhum teste**: falso — testado via aliases `_*` de engine.py em test_core.py (grep whole-word não atravessa o prefixo `_`); kernel residual real: família `marker_model_*` e `run_cli_with_timeout` (sempre mockado) sem cobertura.
- **url_markdown.py com zero cobertura**: falso — as 8 funções são exercitadas transitivamente via `_html_to_structured_markdown` (test_core.py:2106-2172), inclusive a heurística de escolha de nó do DOM que o finder disse não testada.
- **Teste lento = 44% da suíte, fix de 1 linha**: mecanismo confirmado, ação refutada — mockar só test_core.py:2362 migra o custo pro próximo teste não-mockado da classe (cache global do import de docling); a correção real é mockar os 5 (promovida ao quick win 2.3).
