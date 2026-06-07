---
name: router
description: Session bootstrap. Read this before any task. Contains project state, routing table, and behavioural contract.
last_updated: 2026-06-03
---

# ROUTER.md - Session Bootstrap

Read this file before starting any task.

---

## Current Project State

### Working

- Python desktop app with Tkinter UI, launched through `app.py`.
- Manifest is `pyproject.toml` with package name `academic-tutor-repo-builder` and version `3.0.0`.
- Academic-material import flow supports files and links.
- Processing flow handles PDFs, links, images, and code.
- Problematic processing outputs are reviewed through the generated repository's manual review area.
- Image Curator supports images extracted from PDFs and imported photos.
- Repository builder consolidates content into Markdown.
- Generated tutor artifacts target Claude, GPT, and Gemini.
- Repository task queue supports builds, reprocessing, and individual material processing.
- Queue state persists between app sessions.
- Dashboard monitors operational repository state.
- Reprocess Repository reapplies the current architecture to existing generated repositories.
- Test runner is `pytest`; brief lists 28 files under `tests/`.
- Auto-tags de unidade/subunidade/bloco geradas em `resolve_unit_block_tags()`:
  tags `unit:`, `subunit:`, `bloco:` persistidas em `auto_tags` do manifest após
  cada regeneração pedagógica.
- Sinal DD.MM: arquivo `12.03 Processos.pdf` recebe boost +0.30 no bloco do
  cronograma correspondente em `score_entry_against_timeline_block()`.
- Code summarization via Gemini API (`gemini-2.5-flash`): bundle each code entry, persist summary + concept-based timeline block assignment in the generated repo's course/code_curation.json. Lazy: without `gemini_api_key` in config the pipeline is a no-op.
- Generated artifacts add course/CODE_HEALTH.md (coverage report) and course/CRONOGRAMA_DETALHADO.md (block-by-block render) to the generated repo.
- Harness de avaliacao de atribuicao bloco em `scripts/eval_assignments.py`:
  roda o gold set `tests/fixtures/eval/assignments_gold.json` pelo scorer real
  (resolve_unit_block_tags) e reporta acuracia/confusao/calibracao de band.
  Gate de regressao em `tests/test_eval_assignments.py` (baseline no fixture).
- Sinal de sequencia (ordinal de aula) em `src/builder/routing/sequence.py`:
  "Aula 03" recebe boost de desempate `SEQUENCE_BOOST=0.20` no 3o bloco
  `kind=class` (numerado por `annotate_class_ordinals`), somado em
  `score_entry_against_timeline_block`. So marcadores `aula`/`encontro`.
- Referencias como contexto do tutor (`src/builder/core/reference_*.py`):
  entries `category in {referencias, bibliografia}` buscam conteudo leve sem
  clone (README via API GitHub / texto de pagina via `url_markdown`), resumo
  Gemini lazy (`ReferenceSummary`), e mapeamento determinístico a
  unidade/topico (`assign_concepts_to_unit`). Surfaceado na BIBLIOGRAPHY.md
  (resumo + mapa de relevancia). Cache por hash em `references_curation.json`.
  Wiring em `build_workflow._run_auto_code_summarization` (referencias mapeiam
  mesmo sem chave Gemini; reload do manifest pos-enriquecimento).
- Clone de repo GitHub (`process_github_repo`, `source_importers.py`) detecta o
  branch default via `git ls-remote --symref HEAD` (`_detect_default_branch`;
  tags pinam branch explicito, fallback `main`) e clona com
  `git -c core.longpaths=true`. Conserta repos com default `master`/outro
  (`Remote branch main not found`) e long-path no Windows (`Filename too long`).
- Chave Gemini (`gemini_client._resolve_gemini_key`) com precedencia config (UI)
  > `GEMINI_API_KEY` do `.env`/ambiente. Vale para code summary E referencias
  (client compartilhado). `.env` carrega em os.environ no import de helpers.
- Pipeline de referencias validada end-to-end com Gemini real
  (`scripts/validate_references_e2e.py`): fetch real (README GitHub + doc HTML),
  resumo+conceitos Gemini, mapeamento determinístico, persistencia em
  `references_curation.json`. Requer `google-genai` instalado (declarado em
  pyproject; degrada silencioso para resumo vazio se ausente).
- Approach C: referencias mapeadas viram linhas `📖 Apoio:` sob unidade/topico no
  `COURSE_MAP.md` (material complementar). Helper `core/reference_navigation.py`
  (`build_unit_topic_reference_index`, chave de topico canonica `_topic_key` =
  `normalize_match_text(strip_outline_prefix(...))`), injetado via
  `course_meta["_reference_nav_index"]` em `pedagogical_regeneration`, emitido em
  `render_low_token_course_map_md` (cap 2/ancora + overflow, dedup topico vs
  unidade). Tabela de relevancia redundante da BIBLIOGRAPHY virou ponteiro.
  Modo degradado byte-identico sem curation.
- Higiene dos MDs do tutor (grupo tabelas mortas, `repo.py`): placeholders
  permanentes `[a preencher]` e secoes nunca preenchidas removidas de
  exam/assignment/code_index/whiteboard/exercise; comentario TODO que vazava
  por block no CRONOGRAMA removido; coluna `Status` morta do assignment
  dropada; labels de clamp corrigidos (EXAM/ASSIGNMENT/CODE_INDEX/WHITEBOARD
  usam o proprio nome). Branches vazios viram frase curta de estado. 887 testes
  verdes. Spec/plano `2026-06-05-tabelas-mortas-mds-tutor*`.
- Higiene dos MDs do tutor (grupo ambiguidade barata): `modes_md` "quatro
  modos" -> cinco; modo `assignment` referencia os dois indices (exercises +
  assignments); label de clamp do `glossary_md` corrigido p/ GLOSSARY; contrato
  estrutural de navegacao alinhado a COURSE_MAP->FILE_MAP (bate com as 3
  variantes); FILE_MAP perdeu o sufixo redundante `_(baixa confianca)_`
  (mantem `_(ambiguo)_`); `render_course_map_md` legado (0 callers) removido.
  893 testes verdes. Spec/plano `2026-06-05-ambiguidade-barata-mds-tutor*`.
  Fim de sessao (2 protocolos divergentes) adiado pro student_state.
- Higiene dos MDs do tutor (grupo duplicacoes): fonte unica em `pedagogy.py` -
  constante `PEDAGOGICAL_SEQUENCE` (ordem canonica Intuicao antes de Definicao,
  rotulos padronizados) + helpers `_pedagogical_sequence_*`/`_exam_scope_rule_lines`.
  `pedagogy_md`/`modes_md`/`output_templates_md` derivam dela; acaba a
  contradicao das 3 ordens e o hardcode 2x dos pesos de prova. Guard DRY
  `TestPedagogySingleSource`. 906 testes verdes. Spec/plano
  `2026-06-05-duplicacoes-mds-tutor*`. Aberto: 5 modos inline (rodada propria).
- Harness ground-truth (`scripts/eval_ground_truth.py` +
  `scripts/make_ground_truth_template.py`): mede correcao REAL file->bloco contra
  um repo gerado real + CSV de rotulos, sem re-rodar o scorer (le `manifest.json`
  + `course/.timeline_index.json`). Metrica-chave `confident_wrong` (band alta +
  bloco errado), alem de acuracia/confusao/orphans/missed/calibracao por band.
  Gerador de esqueleto pre-preenche `true_block_id` com a predicao. Falta o passo
  de dados: usuario aponta repo real + rotula (assistido). 913 testes verdes.
  Spec/plano `2026-06-05-medicao-ground-truth*`.
- Fix classificacao de prova no cronograma (`classifier.py`): bloco sem unidade
  era `class` mesmo com prova/revisao so no label da sessao (topico reduzido a
  stopword "para"). Passo extra le `sessions[].label`, gated em `not has_unit`,
  tokens fortes (P1-4/PF/"prova N") -> assessment, "revisao" -> review; guarda
  `correcao` (aula de correcao != prova) e "prova" isolado (= demonstracao). 5
  blocos corrigidos no corpus, 0 regressao; resolveu o gate TCC-Tutor.
- Tipo autoritativo do SARC -> kind do bloco (Parte A, backend). O cronograma
  SARC (ASP.NET `dgAulas`) marca tipo por coluna `Atividade` + cor da linha.
  Fluxo: `_aspnet_row_canonical_kind` (helpers) emite `{kind=<canonico>}` (cor de
  EXCLUSAO suspension/ps/g2/event vence; senao Atividade; senao cor positiva) ->
  validado contra BlockKind em `_build_timeline_candidate_rows` -> agregado em
  `block["source_kind"]` (`_aggregate_source_kind`) -> `classify_block` honra
  source_kind (abaixo do override manual) -> `finalize_block` limpa unidade de
  blocos nao-aula (preserva `block_manual_unit_slug`). Provas viram assessment e
  nao recebem unidade. 938 testes verdes. Spec `2026-06-06-cronograma-sarc-tipo-
  e-tab-design` (Parte A); plano `2026-06-06-cronograma-sarc-tipo-backend`.
  Aberto: Parte B (UI: tab do cronograma em tabela + legenda).
- Guard de conflito override-vs-auto (Parte A, backend). `timeline/conflicts.py`
  (puro): `auto_suggested_unit` (espelha gate de topic-derive: conf>=0.65,
  nao-ambiguo) + `detect_block_conflicts`/`detect_timeline_conflicts`. Sinaliza
  quando `block_manual_unit_slug` contradiz a unidade auto-confiante, ou
  `manual_kind_override` contradiz `source_kind` (SARC). Surfaceado no health
  report (`override_conflicts`, warning nao-bloqueante) e em CRONOGRAMA_HEALTH.md
  (secao "Conflitos de curadoria"). Override manual segue vencendo; o guard so
  torna visivel/reversivel. Achou e corrigiu o caso real TCC bloco-02 (override
  manual unidade-02 vs auto unidade-01 conf 1.0; removido de .timeline_curation).
  956 testes verdes. Spec `2026-06-06-guard-conflito-override-curadoria-design`;
  plano `2026-06-06-guard-conflito-override-backend`. Aberto: Parte B (UI: aviso
  no tab + botao reverter p/ auto).
- Precisao bloco->unidade (investigacao + Plano 1). Gargalo medido: arquivo->bloco
  e FORTE (bands quase todas "alta"), mas bloco->topico->unidade FALHA (~100% dos
  blocos ambiguo/topic_text_fallback, ~0 via taxonomia) -> unidade vem de
  scorer-keyword fragil que erra (ex.: recursivas->turing por "computavel"~
  "computabilidade"). Arquivo cai no bloco certo mas herda a unidade errada.
  Plano 1 entregue: `_build_timeline_candidate_rows` deriva kind da coluna
  Atividade do syllabus (sem `{kind=}`) via `ATIVIDADE_KIND_MAP` (promovido a
  publico em helpers) -> provas/trabalhos/feriados viram nao-aula e saem da
  atribuicao de unidade (TCC: P1/P2/PS/G2 agora source_kind=assessment). 965
  testes. Spec `2026-06-06-precisao-bloco-unidade-design`; plano
  `2026-06-06-atividade-kind-backend`. ABERTO: Plano 2 (matcher posicional:
  afinidade token-overlap bloco x titulo+topicos da unidade + anchor-fill
  monotonico, substitui o caminho fragil; rebuild-diff guard 5 cursos; guard de
  conflito usando a sugestao do posicional).
- Matcher posicional bloco->unidade (Plano 2 de C) ENTREGUE. Modulo novo
  `src/builder/timeline/unit_matcher.py`: `score_block_unit_affinity` (overlap de
  tokens bloco x titulo+topicos+aliases da unidade, stopwords PT) +
  `assign_units_positional` (DP monotonico global: maximiza afinidade total sob
  unidade nao-decrescente; robusto a ancora espuria). Wiring two-phase em
  `_build_timeline_index`: atribui unidade aos candidatos (sem source_kind
  nao-aula) ANTES da classificacao final de kind (preserva o gate do classificador
  de sessao); fallback estreito (curso sem unidades/ancora). `auto_unit_slug`
  persistido (serializer+schema); guard de conflito le ele. Substitui o caminho
  fragil (Bug A subsumido). Corpus real: turing->u2, conjuntos/recursivas->u1,
  hoare->verificacao-programas, modelos->verificacao-modelos, microservicos->
  integracao, gerencia->u2. 982 testes. Guard `scripts/rebuild_diff.py` (dry-run,
  diff unit/kind nos 5 cursos). NADA gravado nos repos reais (reprocess e decisao
  do usuario apos revisar deltas). Spec `2026-06-06-precisao-bloco-unidade-design`;
  plano `2026-06-06-matcher-posicional-unidade`. Aberto p/ futuro: separar blocos
  merged (feriado+prova etc.); plano de limpeza/dead-code (auditoria pronta:
  `_match_timeline_to_units_generic` morto ~180 linhas, contrato `administrative_only`
  quebrado, 3 scorers de unidade duplicados, vocab/normalizadores ×4).

### Not Declared In Brief

- Runtime dependencies are not declared in the manifest brief.
- Development dependencies are not declared in the manifest brief.
- Project scripts are not declared in the manifest brief.
- Build tool, linter, formatter, and package manager are not declared in the brief.
- Exact Datalab API/package version is not declared in the brief.
- Exact Ollama model/version is not declared in the brief.

### Current Design Focus

- ENTREGUE: Referencias como contexto base do tutor (8 tasks TDD + 2 fixes de
  wiring). Spec `docs/.../2026-06-04-referencias-contexto-tutor-design.md`,
  plano `docs/.../plans/2026-06-04-referencias-contexto-tutor.md`. Resolve
  "tutor so tem link/titulo da referencia". 841 testes verdes.
- Itens PARADOS (retomar): ver `docs/superpowers/BACKLOG.md` — verbosidade do
  manifest (`to_dict` serializa todos os defaults), #3 decay de data, #4 piso
  de band, Horario, conserto do clone github, token github, referencias
  Approach C, harness de referencias, medicao de correcao com ground-truth.

> Historico: o redesign do sistema de tags (unit/subunit/bloco) e a precisao de
> atribuicao bloco/unidade ja foram implementados (auto_tags, bandas de
> confianca Fase 1-4, harness de avaliacao, sinal de sequencia). Foco migrou de
> "precisao de bloco" (resolvida, ~98% band alta nos repos reais) para
> "referencias usaveis pelo tutor".

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `context/architecture.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.
