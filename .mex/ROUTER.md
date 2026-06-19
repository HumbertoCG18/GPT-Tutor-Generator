---
name: router
description: Session bootstrap. Read this before any task. Contains project state, routing table, and behavioural contract.
last_updated: 2026-06-19
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
- Curadoria unificada na UI: um botão `Curadoria` abre workspace com abas
  `Revisão Manual` e `Imagens`; revisão manual abre primeiro e o painel de
  imagens é lazy-loaded ao selecionar a aba.
- Image Curator supports images extracted from PDFs and imported photos inside
  the unified curation workspace.
- Repository builder consolidates content into Markdown.
- Generated tutor artifacts target Claude, GPT, and Gemini.
- Repository task queue supports builds, reprocessing, and individual material processing.
- Queue state persists between app sessions.
- Dashboard monitors operational repository state.
- Reprocess Repository reapplies the current architecture to existing generated repositories.
- Test runner is `pytest`; the tracked test suite has 122 files under `tests/`.
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
- Referencias como contexto do tutor (`src/builder/core/reference_content.py`,
  `src/builder/core/reference_summary.py`, `src/builder/core/reference_topic.py`):
  entries `category in {referencias, bibliografia}` buscam conteudo leve sem
  clone (README via API GitHub / texto de pagina via `url_markdown`), resumo
  Gemini lazy (`ReferenceSummary`), e mapeamento determinístico a
  unidade/topico (`assign_concepts_to_unit`). Surfaceado na BIBLIOGRAPHY.md
  (resumo + mapa de relevancia). Cache por hash no arquivo de curation gerado.
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
  resumo+conceitos Gemini, mapeamento determinístico, persistencia no cache de
  referencias gerado. Requer `google-genai` instalado (declarado em
  pyproject; degrada silencioso para resumo vazio se ausente).
- Approach C: referencias mapeadas viram linhas `📖 Apoio:` sob unidade/topico no
  course map gerado (material complementar). Helper `src/builder/core/reference_navigation.py`
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
  um repo gerado real + CSV de rotulos, sem re-rodar o scorer (le o manifest
  gerado + o timeline index gerado). Metrica-chave `confident_wrong` (band alta +
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
- Guard de conflito override-vs-auto (Parte A, backend). `src/builder/timeline/conflicts.py`
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
  `src/builder/timeline/unit_matcher.py`: afinidade por overlap de tokens
  (bloco x titulo+topicos+aliases da unidade, stopwords PT — interno, via
  `_block_tokens`/`_unit_tokens`) +
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
- Blocos merged resolvidos: `_rows_belong_to_same_thematic_block` separa por
  `kind` autoritativo da linha (helper `_row_is_standalone_kind`) — prova/feriado/
  etc. viram bloco proprio (nao escondem prova em bloco de feriado/atendimento).
  985->978 testes (apos limpeza). 
- Limpeza matcher/timeline (plano `2026-06-07-limpeza-matcher-timeline`) PARCIAL:
  Task A feita (deletado `_match_timeline_to_units_generic` + helpers + wiring +
  testes do caminho morto, ~178 linhas); Task C feita (dedup `_normalize_unit_slug`
  index->teaching_plan, `UNIT_GENERIC_TOKENS` unificado, `_collapse_ws`->
  `helpers.collapse_ws`). ADIADO: Task B (`administrative_only` precisa decisao de
  produto: persistir vs deletar filtros mortos), Tasks D/E (unificar scorers/
  predicados, eval-gated). 978 testes.
- D2 (`administrative_only`) RESOLVIDO (`085a725`, P1 Lote B; subsume a Task B acima):
  a chave nunca e gravada em producao (`_build_timeline_index` runtime nao escreve nem
  remove admin; `_serialize` ja remove) -> `block.get("administrative_only")` era no-op
  nos 4 sites, e `content_taxonomy`/`file_map` (leem o indice runtime) deixavam blocos
  admin (feriado/prova) vazarem como candidatos do scorer material->bloco e do ordinal
  `bloco-N`. D2=A uniforme: troca pelo predicado real
  `timeline_block_is_administrative_only` (promovido a publico; le `rows`) nos 4 sites.
  Correto no runtime, inocuo no serializado. Suite 1366 verde; golden de bloco 5/5.
- P1.5 `auto_suggested_unit` (conflicts.py) investigado (`8392450`): o ramo topic-derive
  e VIVO, nao morto. A premissa da spec (inalcancavel pq posicional sempre grava
  `auto_unit_slug`) e FALSA — posicional so grava p/ class_candidates com slug; blocos
  nao-aula, herdados (soft-continuation seta `unit_slug` sem `auto_unit_slug`) e
  posicional-vazio serializam SEM `auto_unit_slug` mas COM `topic_candidates`. MANTIDO
  (conflict-detection/health, golden-safe); so o comentario stale ("espelha topic-derive
  do build" -> hoje build deriva via posicional) foi corrigido. Sem mudanca de comportamento.
- P1.3 piso 0.72 REMOVIDO (`6f24fc7`): o `max(confidence,0.72)` no session-first
  single-block era polegar-na-balanca invisivel. A band usa a conf CAPADA
  (scorer_only=0.70); o piso so afetava o `block_confidence` RAW passado a
  `reconcile_unit_with_block` (bloco define unidade se block_confidence >=
  unit_confidence). Como `unit_confidence` tambem e `relative_margin_confidence`
  (idea 1), a comparacao e simetrica por design — o piso quebrava isso so na janela
  unit_conf in (0.70,0.72]. Removido: discordancia marginal vira conflito flagado, conf
  honesta. Rejeitada a opcao de reconciliar com a conf capada (method-cap = teto de
  display, nao evidencia). Suite 1366 verde; golden 5/5. P1 restante: so o fallback
  keyword ~600 linhas (index.py:2205, eval-gate forte, guard test antes de deletar).
- P1.4 fallback keyword INVESTIGADO (17/06): NAO e dead-code degenerado. So dispara quando
  `assign_units_positional` retorna [] = m<2 / n==0 / afinidade-zero. Contexto institucional
  (`.mex/context/institutional.md`): plano de ensino SEMPRE presente + NUNCA cadeira de 1
  unidade -> m>=2 garantido -> m<2 inalcancavel; resta afinidade-zero (rara, Descricao do
  SARC traz topico) e n==0 (no-op). DECISAO = Alternativa C (ADIAR pro P2): nao causa bug
  hoje; deletar errado = regressao silenciosa em curso degenerado. Tratar o delete junto da
  unificacao de scorers do P2 (fold no posicional dos sinais que o fragil tem e o posicional
  nao: nº explicito "Unidade N", frases/ancoras) + guard test (posicional nunca [] no golden).
- LATENTE (item proprio, investigar antes de mexer no fallback — interdependentes): sem
  teaching_plan, `unit_index` cai em `_derive_unit_specs_from_repo` mas `content_taxonomy
  ["units"]=[]` -> as 2 fontes de unidade divergem e o fallback vira load-bearing. Nao
  exercitado (plano sempre presente). Ou remover `_derive_unit_specs_from_repo` (se nunca-hit)
  ou dar a content_taxonomy o mesmo fallback. Outros gaps mapeados: "Evento Academico" fora
  do ATIVIDADE_KIND_MAP; divergencia nome-unidade x nome-card Moodle (match fuzzy).
- P3.4 `trabalho`->DELIVERABLE unit-aware FEITO (17/06): o token nu `"trabalho"`/`"parte
  trabalho"` saiu de `KIND_KEYWORDS[DELIVERABLE]` (classifier.py) e virou regra gated 3c em
  `classify_block` -> so vira DELIVERABLE quando o bloco NAO tem evidencia de unidade
  (`_has_unit_evidence`: unit_slug/auto_unit_slug/topic_candidates). Aula "Trabalho sobre X"
  com unidade mantem a unidade (CLASS). Bundle: `_STRONG_EXAM_RE` ganhou `\bg2\b|\bps\b`
  (no-op no corpus atual — PS/G2 ja vem por source_kind; rede de seguranca sem source_kind).
  DESCOBERTA: a premissa do handoff (FP frequente) NAO bate no corpus — os unicos blocos com
  "trabalho" nu nos 5 cursos sao apresentacoes de TP/T (sem unidade), p/ os quais DELIVERABLE
  estava certo; 2 deles (IA bloco-16, SO bloco-08) sao MERGED (apresentacao + prova P1/P2) e
  agora caem em ASSESSMENT via session-exam (reforca a divida "separar blocos merged"). Suite
  1370 verde; golden 5/5 confiante-errado 0.
- Normalizacao/tokenizacao consolidada (P2 Fase 1): `src/builder/text/normalize.py` e
  `src/builder/text/stopwords.py` viraram fontes unicas para normalizadores/stopwords,
  com delegadores byte-identicos preservando comportamento legado.
- Concept resolver (P2/Fase 2-3) existe em `src/builder/routing/concept_resolver.py` +
  `resolver_apply.py`, com harness `scripts/compare_resolver.py` e gold de codigo em
  `tests/fixtures/eval/code_block_gold.json`. Wiring de producao fica atras da flag
  `use_concept_resolver` e sobrescreve apenas campos de bloco (`computed_block_id`,
  confidence/band/method + tag `bloco:`), nao unidade.
- Signal registry/Moodle S0: `FileEntry` preserva `source_section`, `moodle_label`,
  `posting_date`, `posting_date_created`; `SubjectProfile` preserva `turma` e
  `schedule_url`. `backfill_repo_signals_additive` grava labels/datas/lessons index
  sem mudar atribuicao; `backfill_repo_signals_consumed` pode atualizar `source_section`
  e card-block map e por isso precisa de eval-gate. Scripts atuais:
  `migrate_signals.py`, `posting_date_probe.py`, `propose_gold.py`, `gold_by_card.py`,
  `expand_card_gold.py`, `make_code_gold_template.py`, `eval_code_block_gold.py`.
- SARC/Moodle metadata: `parse_sarc_turma_key` resolve GUID/ano/sem da URL; a UI persiste
  `schedule_url` no perfil da materia. `Evento Academico` ja esta mapeado para `event`
  em `ATIVIDADE_KIND_MAP`; o gap antigo foi fechado.
- Docs/reports: `docs/reports/gold_templates/` contem templates/gabaritos CSV por curso
  para medicao cross-curso e rotulagem por card.
- Cronograma sessao-atomo (Specs A+B, design revisado 19/06 via workflow adversarial):
  a CHAVE de join da atribuicao passa a ser a DATA por membership (`session.date in
  card.dates`, conjunto discreto + fallback span logado); slug vira projecao de display.
  Specs `docs/superpowers/specs/2026-06-19-cronograma-sessao-atomo-design.md` (consumidor)
  + `...-ingestao-stash-download-automap-design.md` (produtor). Roteiro em degraus:
  1 render+normalizacao (FEITO), 2 over-merge temporal (ADIADO — block_id posicional
  cascateia, funde no 3), 3 atribuicao = signal-registry (em curso), 4 ingestao, 5 inversao
  sessao-atomo. Handoff `docs/reports/2026-06-19-handoff-cronograma-degraus.md`; progresso
  duravel em `.git/sdd/progress.md`.
- Degrau 1 FEITO (merge-ready, nao mergeado): `cronograma_detalhado_md` (`repo.py`) lista
  `### Sessoes` por bloco (data+dia-semana+label+marcador de prova) lendo `blocks[].sessions[]`;
  `lookup_card_blocks`/`lookup_card_assign_due` (`card_block.py`) casam a chave do card por
  `norm_ascii_lower` (caixa/acento). Nao-regressivo, atras de nenhuma flag (render/normalizacao
  sao seguros). Sem material por dia ainda (depende do degrau 3/5).
- Degrau 3 = signal-registry do `concept_resolver`: alavancas 2 (source_section) e 1
  (moodle_label) JA no fusor; alavanca 0 (lessons[].text data->topico) e a unica aberta,
  PLANEJADA (`docs/superpowers/plans/2026-06-19-degrau3a-alavanca0-lesson-signal.md`) — termo
  lesson capado casando o sinal LIMPO (moodle_label+titulo), atras da flag, eval-gate decisivo.

### Not Declared In Brief

- Project scripts are not declared in the manifest brief.
- No `[build-system]` table, linter, formatter, or project scripts are declared in the manifest.
- Exact Datalab API/package version is not declared in the brief.
- Exact Ollama model/version is not declared in the brief.

### Current Design Focus

- Foco atual: refactor do cronograma sessao-atomo em DEGRAUS, atribuicao por DATA
  (membership) eval-gated. Degrau 1 (render dia-a-dia + fix de normalizacao) FEITO. Proximo =
  degrau 3a / alavanca 0 (sinal lessons[].text data->topico no `concept_resolver`, atras da
  flag, casando o moodle_label limpo) — plano escrito, aguarda execucao em sessao fresca.
- Resolver por conceito permanece atras de flag ate cutover com gold suficiente; degrau 3
  o estende como signal-registry (alavancas 2/1 ja no fusor; alavanca 0 = proxima). O
  over-merge de blocos foi adiado pro degrau 3 (block_id posicional cascateia se cortado antes).
- Dependencia user-side: gold cross-curso (ground_truth_<curso>.csv IA/SO/ES2/TCC) + re-sync
  por fonte destravam a medicao dos 4 cursos; MF ja mede.

> Historico: referencias como contexto base do tutor, redesign de tags
> (unit/subunit/bloco), precisao bloco/unidade, guard de conflitos e higiene dos
> MDs ja foram entregues. O foco atual migrou para medicao/gold cross-curso e
> unificacao da atribuicao por conceito com gates de regressao.

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `context/architecture.md` |
| Understanding the faculty/source platforms (Moodle, SARC, Plano de Ensino) | `context/institutional.md` |
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
