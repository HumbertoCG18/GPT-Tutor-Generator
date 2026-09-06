---
name: decisions
description: Architectural choices and rationale for GPT-Tutor-Generator
triggers:
  - decision
  - why
  - rationale
  - architectural choice
edges:
  - target: context/architecture.md
    condition: when a decision affects system structure
  - target: context/stack.md
    condition: when a decision affects technology choice
last_updated: 2026-09-05
---

# Decisions

Append-only log. When a decision changes, mark the old entry as superseded and add the new decision above it.

---

### [backfill 03/09] Sete decisões duráveis que viviam só no tracker (junho–agosto/2026; span-cap refutado entrou junto com "2 aulas = 1 bloco")

Registradas originalmente em `docs/reports/pendencias.md` (hoje `docs/reports/_archive/pendencias-historico-ate-2026-09-02.md`);
movidas para cá em 2026-09-03 sem mudar o teor. Datas são as originais.

#### Dedup de materiais é por CONTEÚDO (md5), nunca por basename ou id
**Date:** 2026-06-23 · **Status:** Active
**Decision:** Duplicata só existe com hash igual; nome de arquivo ou id iguais/diferentes não decidem nada.
**Reasoning:** Causa confirmada no IA: o stash migrou de uma pasta nomeada pelo TÍTULO do PDF para a pasta do Moodle (nomes reais + semanas); o manifest acumulou os dois e ninguém podou o velho. Dedup por nome não pega (nomes diferem); só md5.
**Consequences:** Toda migração de stash exige poda por conteúdo; duplicata sem hash é palpite e não entra.

#### Regra "2 aulas = 1 bloco" aposentada: bloco = unidade pedagógica, sessão = átomo do render
**Date:** 2026-06-22 · **Status:** Active
**Decision:** A granularidade fina vive em `sessions[]` (por semana ISO), não em mais blocos. Junto: span-cap de over-merge REFUTADO por evidência (IA bloco-05 de 28 dias é unidade COESA de ML supervisionado; span não separa coeso-longo de qualquer-longo sem quebrar o coeso).
**Reasoning:** Nenhum limiar temporal distingue bloco coeso de mis-merge; a cauda errada do bloco-05 é caso de conteúdo, não de duração.
**Consequences:** Não reintroduzir cap de span nem contagem de aulas como critério de corte de bloco.

#### Bibliografia é caso à parte, fora do motor temporal
**Date:** 2026-07-22 (brainstorm F5) · **Status:** Active
**Decision:** Bibliografia/references/cronograma ficam fora do provider de janela-de-prazo e do motor de bloco. O tutor deve passar a CONSUMIR bibliografias sem estourar o limite do Project, com brainstorm/spec próprios.
**Reasoning:** Referência não tem "quando"; forçar bloco gera o residual conhecido (MF eth2 → bloco-12, aws → bloco-01). Ver spec `docs/superpowers/specs/2026-07-22-janela-de-prazo-tier2-design.md` §7.
**Consequences:** Régua de cobertura das referências é separada (campanha própria); eth2/aws são exceção documentada, não bug do motor.

#### `covered_units` é LISTA por avaliação/entrega, regra do plano de cada curso
**Date:** 2026-08-08 · **Status:** Active
**Decision:** Cobertura de prova/entrega é um conjunto de unidades vindo do plano (due-window + `<repo-tutor>/course/.assessment_context.json` + notas do gold como verdade inicial). Regra IA: P1 = u01+u05; P2 CUMULATIVA = u01+u05+u02+u03; PS = tudo. MF/TCC não-cumulativo.
**Reasoning:** Uma prova cobre várias unidades; campo único mentiria.
**Consequences:** Consumidores (EXAM_INDEX, "o que cai na P2") leem a lista; cumulatividade é por curso, nunca global.

#### PS e G2 têm tratamento estrutural, sem unidade
**Date:** 2026-08-08 (regra institucional) · **Status:** Active
**Decision:** Provas opcionais não recebem unidade: PS = semestre inteiro; G2 condicional (G1 < 7 e (G1+G2)/2 ≥ 5).
**Reasoning:** São instrumentos institucionais, não avaliações de conteúdo delimitado.
**Consequences:** `_NOT_MAIN_EXAM` e a fórmula do G1 devem tratá-las como não-principais (pendência aberta: FR contaria 4 principais; a fórmula diz 2).

#### Modo não-monotônico por curso: descartado
**Date:** 2026-08-11 (ruling T11, opção C) · **Status:** Active (reavaliar só se a família de cursos crescer)
**Decision:** Não implementar inversão de ordem por curso no caminho bloco→unidade.
**Reasoning:** 1 em 5 cursos inverte; o scorer puro erra sob co-ocorrência; o caminho já empilha ~8 camadas (DP global, fallbacks, heranças, curadoria, demote) — overengineering confirmado no código.
**Consequences:** Curso que inverter é caso de curadoria/pino, não de modo novo.

---

### Motor de Atribuição (AnchorEngine + LlmVoter) Roda Por Curso Atrás de Flags Próprias

**Date:** 2026-08-06 (fases 0-5a entregues 07/07..08/05; rollout MF/SO 08/04)
**Status:** Active
**Decision:** A atribuição temporal nova vive em `src/builder/routing/motor/` (WindowProviders por curso, Disambiguator, gate D4, voter LLM TIER 3 bounded à janela, TIER 2 janela-de-prazo) e roda por curso atrás de `use_anchor_engine`/`use_llm_voter` em `SubjectProfile.feature_flags`, com precedência sobre o legado `use_anchor_placement`. Escreve SÓ campos `temporal_*` (+ sidecar `<repo-tutor>/material_curation.json` de votos, keyed por md5); `computed_*` e pino manual intocados. Funil legado vive até o cutover F5 (deleção por lista nomeada de símbolos).
**Reasoning:** Cutover exige gold-gated por curso; flags por curso limitam blast-radius e permitem rollback barato (provado 2×: TCC 2026-08-04 e 2026-08-06).
**Consequences:** Toda medição passa por `audit_gold_freshness` (pré-gate hard=0) + probes fase0-5 byte-idênticos; FAIL de gate = rollback + investigação, NUNCA re-tuning pós-hoc (spec §12); rollback de reprocess DEVE cobrir artefatos gitignored (índice/sidecars) — snapshot só de tracked é rede furada. Supersede na prática o "Anchor Placement Is Additive and Feature-Flagged" abaixo (o campo temporal aditivo e o princípio flag-off-byte-idêntico permanecem; o produtor mudou).

---

### Stable Timeline Block Identity Uses UUID Ledger

**Date:** 2026-06-21
**Status:** Active
**Decision:** Timeline blocks get durable `block_uuid` values from the generated course block-identity ledger, reattached across rebuilds by date overlap and topic-token tie-breaking; human and generated block references migrate toward UUIDs while positional block ids remain compatibility fallbacks.
**Reasoning:** Positional `bloco-NN` ids change when schedule blocks split, merge, or move, which can orphan manual truth, curation, eval fixtures, and card maps. A ledger preserves identity across rebuilds without hashing content that intentionally changes during timeline cleanup.
**Consequences:** Timeline rebuild code must respect the `persist` gate, avoid writing ledgers during dry-run/eval paths, and fail clearly when UUID references exist but the ledger is missing.

---

### Anchor Placement Is Additive and Feature-Flagged

**Date:** 2026-06-21
**Status:** Superseded per-course (2026-08-06) — ver "Motor de Atribuição" acima; `use_anchor_engine` precede `use_anchor_placement` (IA ainda roda o legado até o flip)
**Decision:** The anchor placement layer can write `temporal_block_id` and `temporal_block_method` only behind per-subject `use_anchor_placement`; it does not overwrite `computed_block_id`, and manual block truth still wins.
**Reasoning:** Card/source-section dates are strong temporal evidence, but cutover needs gold-backed evaluation. Additive temporal fields allow canary comparison without changing the default knowledge-base routing surface.
**Consequences:** Builder options inject only explicit `SubjectProfile.feature_flags`; anchor placement tests must prove flag-off behavior is byte-compatible and no resolver call happens when disabled.

---

### Moodle/SARC Signals Are Preserved as Separate Routing Evidence

**Date:** 2026-06-18
**Status:** Active
**Decision:** Persist source signals such as `source_section`, `moodle_label`, `posting_date`, `posting_date_created`, `turma`, `schedule_url`, the generated card-block map, and the generated lessons index as explicit metadata instead of overwriting titles or relying only on filenames.
**Reasoning:** Attribution accuracy depends on the original course card, Moodle resource label, posting date, and SARC schedule identity. Keeping those signals separate lets routing, eval harnesses, and manual review reason about provenance without corrupting user-visible titles.
**Consequences:** Import and migration paths must distinguish additive signals from consumed signals that can change attribution. Backfills that alter `source_section` or card maps need eval-gated review.

---

### Concept Resolver Cutover Is Feature-Flagged

**Date:** 2026-06-18
**Status:** Active
**Decision:** The concept resolver is wired through `use_concept_resolver` and, when enabled, overwrites only block fields (`computed_block_id`, confidence, band, method, and mirrored `bloco:` tag).
**Reasoning:** The resolver unifies several attribution signals, but routing cutover needs gold coverage and regression gates before becoming default behavior.
**Consequences:** Production-default behavior remains the existing routing funnel. Resolver work should be tested with the comparison/gold scripts and should not silently change unit fields.

---

### Generated Tutor Artifacts Carry Timeline Health and Temporal Context

**Date:** 2026-06-17
**Status:** Active
**Decision:** Regeneration writes cronograma health and temporal context artifacts alongside COURSE_MAP and FILE_MAP.
**Reasoning:** Timeline-aware tutoring needs both a compact current-schedule context and a visible audit surface for timeline/unit conflicts, stale overrides, and allocation health.
**Consequences:** Generated-output documentation and artifact tests must include both files. Tutor instructions may refer to the temporal context artifact, while operational diagnostics should use the cronograma health artifact.

---

### References Are First-Class Tutor Context

**Date:** 2026-06-17
**Status:** Active
**Decision:** Entries in reference/bibliography categories are fetched lightly, optionally summarized with Gemini, deterministically mapped to units/topics, cached in generated reference curation, surfaced in BIBLIOGRAPHY, and linked from COURSE_MAP support lines.
**Reasoning:** A tutor that only sees reference links and titles cannot use bibliography as grounding context. The cache keeps enrichment incremental, and the deterministic mapping still works when Gemini is unavailable.
**Consequences:** Reference changes must preserve no-key degradation, cache-by-hash behavior, COURSE_MAP support-line limits, and BIBLIOGRAPHY as the deep-reference target.

---

### Timeline Block Unit Assignment Uses Positional Matching

**Date:** 2026-06-17
**Status:** Active
**Decision:** Timeline blocks receive `auto_unit_slug` through the positional matcher in `src/builder/timeline/unit_matcher.py`, with authoritative non-class kinds excluded from unit assignment and manual overrides remaining dominant.
**Reasoning:** The previous keyword-only block-to-unit path produced confident but wrong unit inheritance. Monotonic positional assignment better matches course chronology and reduces fragile vocabulary coupling.
**Consequences:** Timeline/unit changes should be verified with unit matcher tests and rebuild-diff/eval harnesses where possible. Conflict reporting should compare manual overrides against the positional auto suggestion.

---

### Code Summarization Uses Gemini at Build Time (Optional Layer)

**Date:** 2026-06-02
**Status:** Active
**Decision:** Code entries can be summarized at build time through `google-genai`'s structured-output mode (`response_schema=CodeSummary`) with a content-hash cache in the generated repo's course/code_curation.json. Timeline block assignment is done locally via concept overlap, not via a second LLM call.
**Reasoning:** Code bundles benefit from semantic enrichment (inferred title, role, concepts) for richer downstream artifacts (CODE_INDEX, CRONOGRAMA_DETALHADO, CODE_HEALTH) and tutor grounding. Structured output prevents JSON parsing failures; the local matcher keeps the per-build cost bounded to one LLM call per changed entry. Without an API key the entire layer is bypassed via lazy import.
**Consequences:** Build pipeline must keep the no-key path identical to current behavior. New artifacts must be tolerant of empty code_curation.json. Future material types (PDF, exercises) follow the same hash-cache + local-link pattern.

---

### Generated Repositories Are Markdown-First

**Date:** 2026-05-04
**Status:** Active
**Decision:** The application consolidates imported academic materials into a structured Markdown repository.
**Reasoning:** Markdown is portable, reviewable, and directly usable as knowledge-base content for LLM tutors.
**Consequences:** Build and reprocess flows must preserve navigable Markdown output and tutor instruction artifacts.

---

### Desktop Application Instead of Web Service

**Date:** 2026-05-04
**Status:** Active
**Decision:** The product is a Python desktop application using Tkinter, with `app.py` as the main entry point.
**Reasoning:** The README describes a local academic-material processing workflow with UI-driven subject setup, file import, review, image curation, repository tasks, and dashboard monitoring.
**Consequences:** Setup and operational documentation should prioritize local Python execution rather than server deployment.

---

### Queue-Based Processing Persists Across Sessions

**Date:** 2026-05-04
**Status:** Active
**Decision:** Builds, reprocessing, and individual material processing run through a repository task queue that persists between app sessions.
**Reasoning:** The README states that the queue is persistent, which protects long-running repository work from app restarts.
**Consequences:** Task state is part of the product architecture and must be considered when changing build, reprocess, dashboard, or processing behavior.

---

### Manual Review Is an Explicit Stage

**Date:** 2026-05-04
**Status:** Active
**Decision:** Problematic processing outputs are routed to the generated repository's manual review area instead of being silently accepted.
**Reasoning:** Academic materials can contain difficult PDFs, images, links, and code. A manual correction point prevents low-quality generated repositories from being treated as complete.
**Consequences:** Processing changes should preserve a failure or uncertainty path into manual review.

---

### Image Understanding Is a Separate Curator Flow

**Date:** 2026-05-04
**Status:** Active
**Decision:** Images extracted from PDFs or imported as photos are handled through an Image Curator workflow with description extraction.
**Reasoning:** Academic images often carry pedagogical content that text-only processing misses.
**Consequences:** PDF processing and image curation should stay coordinated, but image review remains a distinct workflow.

---

### Multi-LLM Instruction Output

**Date:** 2026-05-04
**Status:** Active
**Decision:** The repository builder generates instructions/artifacts for Claude, GPT, and Gemini.
**Reasoning:** The README states that generated repositories are prepared for multiple LLM tutor targets.
**Consequences:** Changes to generated instructions must account for all supported LLM outputs.

---

### Fila de revisao `revisar` como campo derivado do manifest

**Date:** 2026-09-02
**Status:** Active
**Decision:** `revisar` ∈ {duvida, llm, ok} e calculado por `src/builder/routing/revisar.py` (funcao pura sobre o entry gravado) e persistido em todo material a cada reprocess. `duvida` = sem bloco em escopo | `temporal_block_flag` | `unit_block_conflict` | subunidade ambiguous/empate; `llm` = voto do LLM na janela; `ok` = resto. A UI (secao de revisao) le o campo, nao recalcula.
**Reasoning:** Metrica de produto "revisar por 100 materiais" (decisao B do plano fechar-o-motor). Calibrado no gold do motor puro: sem-bloco 100%, flag:disamb 63%, sub-empate 57%, conflito 56% de precisao; janela-1 27% e sub-ambigua 22% sao fracos e se decidem com a run real do FR. Sem-sinal e revisao-sem-assunto NAO sao duvida (nem todo material tem subunidade).
**Consequences:** Novo gatilho ou remocao exige remedir com `docs/reports/_harness-2026-09-02/calibra_revisar.py`; a sentinela vigia o campo; `scripts/censo_motor_llm.py` e a regua do numero.

---

### Estrutura do Moodle e sinal gravado no manifest, nao decisao (Fase 3a)

**Date:** 2026-09-03
**Status:** Active
**Decision:** Os 5 cursos encerrados nao se rebuildam (regua de regressao); a posicao do professor (secao, modulo, label datado) entra por backfill de `<repo-tutor>/raw/moodle/contents.json` a cada regeneracao (`backfill_moodle_structure_repo`, hook `_run_moodle_structure_backfill` antes do motor), em campos proprios do entry (`moodle_section_index`, `moodle_module_index`, `moodle_week_label`), consumidos pelo motor so a partir da Fase 3b. Casamento por secao (savename/filename -> `moodle_label` unico -> stem), nada fuzzy: entry sem match fica sem estrutura e e contada, nunca remendada. `description` do label manda sobre `name` (cache stale: ES2 2025 x 2026); label sem data nao ancora; ano != ano do cronograma e ruido.
**Reasoning:** Decisao C (02/09): a verdade estrutural esta no Moodle pela API e o export a apaga; para os encerrados a unica forma de importa-la sem invalidar golds e o backfill. Campos separados (e nao `moodle_label`/`source_section`) porque a semana do label nao existe em lugar nenhum do manifest; `data no nome` e `secao` ja estao em `moodle_label`/`source_section`, nao se duplicam.
**Consequences:** Gate do item 2 (03/09): sentinela 0 fora dos 3 campos e TODAS as reguas identicas (estrutura sozinha nao muda decisao). Casamento nos encerrados 217/221 entries com card (4 sem match = arquivo renomeado no Moodle depois do stash). Quem consumir os campos (3b) age so em decisao flagada (lei "estrutura nunca sobrepoe decisao confiante").

---

### Card como documento ordenado age so onde nem o texto nem o LLM decidiram (Fase 3b)

**Date:** 2026-09-03
**Status:** Active
**Decision:** O card do Moodle lido em ordem (semana do label / modulo datado + posicao dos materiais, `card_stream.card_windows`) e um provider FORA da cascata: o `anchor_engine` o consulta (a) sem janela, depois de prep-prova e antes do llm-funil; (b) em decisao ainda FLAGADA **depois** do voter. Janela-1 do card e gateada como data/topic; decisao do card sem flag sai com banda "media"; card que repete bloco e duvida nao renomeia o provider.
**Reasoning:** Medido 03/09 nos 5 golds: so-flagados +16/-5 (motor puro 161 -> 173, AULA 152 -> 163); a tudo, +13/-10 (02/09). Card ANTES do voter estreitava para 1 bloco e o LLM (que acertava) nao votava: curada 199 -> 187. Janela-1 incondicional: conf-err 3 -> 15; precisao das decisoes do card sem flag = 8/11, longe da banda "alta" (~98%).
**Consequences:** Com o voter ligado o card nao muda a curada (o LLM ja decide o que ele decide); o ganho e do motor sem voter e do custo futuro (item 7 mede votos/100 em outro eixo). 5 erros do card escapam da fila com banda "media" sem flag — insumo da calibracao do `revisar` (item 7). Lei reafirmada: estrutura estreita, texto (e o LLM) decide, estrutura nunca sobrepoe decisao confiante.

---

### Secao 0 do Moodle e a area geral do curso: material sem sinal temporal mora na apresentacao (Fase 3b, item 4)

**Date:** 2026-09-03
**Status:** Active
**Decision:** `resolve_general_section` (anchor_engine): entry com `moodle_section_index == 0` que chegou sem janela de provider nenhum (nem card) vai ao bloco de apresentacao (overview/1a aula), method `secao-geral`, banda media — irma de meta/ref-generica. So no caminho lexical (materiais), depois de prep-prova e antes do llm-funil. O sinal e ESTRUTURAL (a secao 0 e, por definicao do Moodle, a area geral do curso), nunca o nome do card.
**Reasoning:** Medido 03/09 (SO, 3 golds): +3/0 no motor puro; no curado tira 3 materiais do llm-funil (50% de precisao, o degrau mais caro). O regex de nome do harness (`informa|geral|aviso`) casava "Semana 12 ... Busca com Informacao" no IA (9 entries) — regra por nome e remendo. Ordem das secoes como prior (H7, +7/-1 em 02/09) foi remedida depois do card ordenado: 0 efeito — nao entrou (nada sem numero).
**Consequences:** Cursos cujo professor usa a secao 0 como card de conteudo teriam materiais na apresentacao — so quando NENHUM outro sinal existe (data, label, topico, card); nos 8 tutores hoje so o SO tem material na secao 0. A regua vigia `secao-geral` em separado.

---

### Tokens curtos consagrados pelo cronograma so onde o lexico padrao ficou em duvida; tokenizador unico nasce no disambiguator (Fase 3c)

**Date:** 2026-09-03
**Status:** Active
**Decision:** `src/builder/text/tokens.py` expõe `motor_tokens`, o tokenizador UNICO do motor; `disambiguator._toks` delega (byte-identico) e os demais 12 tokenizadores migram para ele em C4, um por vez, com sentinela 0. Tokens de 2-3 chars so contam quando o CRONOGRAMA do curso os consagra (`course_short_vocab`: topic_text + labels de sessao) e so no RETRY: `disambiguate` decide com tokens padrao; se flagado, refaz com o vocab curto nos dois lados e adota se muda o bloco ou tira a flag (`disamb-curto`).
**Reasoning:** Medido 03/09: +4/0 nos 5 (IA k-NN x4) e +3/0 no holdout CG ("2d" das sessoes de recorte/instanciamento). Vocab curto global seria ruido (MF nao tem "tcp"); aplicar em toda decisao mexeria em confiantes sem gold que prove. No curado o retry preempta 3 votos de LLM no IA com o mesmo bloco — primeiro item que reduz votos/100 sem regredir a curada.
**Consequences:** Nenhum outro tokenizador muda ate C4. Holdout CG vira regua fixa (`holdout_cg.py`, baseline 30/35).

---

### Sincronizar e a operacao; rebuild e o caso particular do delta total (campanha SYNC)

**Date:** 2026-09-03
**Status:** Active
**Decision:** `sync <curso>` = pull incremental (`moodle_pull`, ja pula o que existe) -> diff estrutural do `<repo-tutor>/raw/moodle/contents.json` contra o `<repo-tutor>/manifest.json` (novo / alterado por `timemodified` > `posting_date` / sumido) -> import so do delta -> `incremental_build` (extrai o novo, motor em tudo) -> diff de decisoes entry a entry + `<repo-tutor>/course/SYNC_REPORT.md` -> fila `revisar`. Rulings do user: modulo removido no Moodle SOME do tutor (flag por curso `sync_prune_removed`, default ligada; desligada = marcado e fora dos indices); decisao antiga que se moveu por material novo entra como "mudou, confira"; arquivo alterado re-extrai automatico com contagem e cap; links/videos entram como entries de referencia (atribuicao e C2); CG = primeira sync como rebuild limpo (ids novos, gold re-chaveado por `true_block_uuid`).
**Reasoning:** Dry-runs de 03/09: FR tem os mesmos 20 arquivos (so o nome de gravacao mudou), LR esta sem o Lab 4 desde 31/08, CG veio do export. Sem uma operacao de sync o tutor de curso em andamento envelhece a cada semana; "rebuild pela API" nao e uma cerimonia, e o delta total.
**Consequences:** Item 8 do C0 vira a campanha SYNC (S1-S6, handoff 2026-09-03). Sync sem delta tem que ser byte-identico (determinismo). Ids nao mudam por renome de gravacao: o casamento estrutural (basename/savename -> stem -> label) e o que liga entry a modulo.

---

### HTML salvo e material, nao codigo nem PDF impresso: texto pelo conversor, so as imagens vao ao Datalab (SYNC S6a/S6b)

**Date:** 2026-09-03
**Status:** Active
**Decision:** Arquivos HTML (.htm e .html) no stash sao tipo `html` (antes de `code`: a extensao HTML estava em CODE_EXTENSIONS e virava `codigo-professor` sem texto; HTM era ignorado; por isso o pull imprimia pagina em PDF). `process_html` em `src/builder/core/html_material.py` (fachada `RepoBuilder._process_html`, 2 linhas no engine): HTML -> `html_to_structured_markdown` sem teto (`truncate_markdown_blocks(max_chars=None)`) e sem cabecalho web (documento local nao tem URL/dominio/hora) -> cada `![alt](src)` da pagina: `src` relativo ao dir do HTML, `data:image/...;base64` decodificado para arquivo, http externo = `![x — não capturada](url)`; imagem copiada para `content/images/<id>-<arquivo>` (ref raiz-relativa; `resolve_content_images` deixa em paz e `unprocess` limpa por prefixo); Datalab CRU por imagem (GIF direto) com cache por md5 em `<repo-tutor>/course/.image_transcriptions.json` (versionado, como o glossario LLM) e cap por build (400); bloco `$$...$$` na resposta = formula -> bloco + `<sub>fonte: [x](content/images/...)</sub>` + `manual-review/formulas/<id>-<img>.md` ("conferir com o professor", fonte NAO corrigida); `![caption](...)` = legenda -> Gemini PT-BR (`GeminiClient.generate_text`, texto) -> `![Figura: ...]`; vazia -> Gemini descreve (texto + imagem inline); sem Gemini a legenda fica em ingles e a vazia vira nao capturada; falha do Datalab nao entra no cache (tenta de novo no proximo build). Clientes injetados (`datalab_image_fn`, `gemini_text_fn`); testes com os falsos e o gold do piloto Curvas.
**Reasoning:** Dado antes de codigo (03/09, 51 paginas reais do CG: 20 do site + 31 do Moodle): 0/51 paginas passam de 15 000 chars (Vis3d 14 183, a 94% do teto) — o teto vira parametro so para nao cortar material em silencio; 4 paginas vazavam VML condicional do Word porque `inline_html_to_markdown` devolvia `str(node)` para Comment/Declaration (Curvas: ~3 200 dos 11 179 chars do piloto eram lixo; limpa tem 7 917); 3 paginas do Moodle ("resolucao de prova") trazem 20 PNGs em `data:` inline (0,6 a 2 MB de markdown se nao decodificar); 139 imagens no mirror, 0 duplicadas por md5, 0 logos sobrevivem ao conversor (todos em `<td>`) — a regra "logos deduplicados por md5 e descartados" nao tem dado e NAO entrou (md5 e so cache/idempotencia); `resolve_content_images` mataria as formulas (GIFs de 511-918 B < `_MIN_IMG_BYTES` 2000, 2 cores = `is_noise_image`) — por isso a copia e propria e a ref e raiz-relativa; no gold do Datalab 12/12 formulas tem `$$` e 0/9 legendas tem (legendas trazem `$C_1$` inline na prosa e caption + paragrafo descrevendo a MESMA figura: a caption basta). 0 entries HTML nos 8 tutores e 0 dentro de zips: tratar html como material nao regride nada.
**Consequences:** S6a `6111b46`, S6b `0a8ae2e`, fix de determinismo das referencias url `a10a6ca` (o cabecalho web entrava no hash de `references_curation` e re-sumarizava toda referencia url a cada regeneracao). Curvas na copia do CG: 24 imagens -> 12 formulas + 9 legendas + 3 descritas, 0 nao capturadas, 24 copias, 12 reviews; segunda rodada 0 chamadas e byte-identica. Custo real do CG: ~160 imagens (139 + 20 data-URI) ≈ US$ 1,60, nao ~250. S6d decide se a snapshot mapeia http do mesmo host para o mirror (hoje = nao capturada, 12 refs em 20 paginas); nao copiar `.orig` do snapshot para o stash. Divida do conversor fora do escopo: `**P(****0)` (bold aninhado do Word) — caixa de ideias.

---

### Pagina do Moodle e do site do professor entram no stash como .html (bundle na subarvore), nunca impressas; PDF ja impresso fica (SYNC S6d)

**Date:** 2026-09-03
**Status:** Active
**Decision:** `moodle_pull` grava resource `.htm(l)` e `mod_page` como `stash/<card>/<nome>.html` normalizado UTF-8 (acao `html`); a pagina do site do professor (acao `snapshot`) vira bundle `stash/<card>/<Stem>/` = pagina + imagens do mesmo host (do dir da pagina no caminho relativo, de fora pelo basename), sem `.orig`; o snapshot segue links so na SUBARVORE da pagina (`in_subtree` = mesmo host + caminho sob o diretorio da pagina). Regra (a) do user: onde ja existe `<stem>.pdf` impresso o PDF fica e o HTML nao entra (`pdf-existente`); migracao so na fronteira. `scan_stash_cards` trata o bundle como 1 item html. Nenhuma pagina e mais impressa em PDF (print_all/find_browser saem do pull).
**Reasoning:** Dado: LR tem 4 labs `.htm` impressos em PDF (entries `lab-N-*`) e `match_module_entries` casa por basename E por stem — com HTML e `.pdf` no mesmo card um readd viraria 2 entries; FR 0; CG e rebuild limpo (sem transicao). `same_site` seguia links para as subarvores URL "Aulas/", "CGII/", "~manssour/" e "CG-PPGCC/" (mirror real do CG); so o que um card do Moodle aponta e o que vive abaixo dele e material. 4 refs de imagem http do mesmo host sobrevivem ao conversor no CG (3 em ExercicioDuasCores sao do proprio diretorio escritas como URL absoluta "~pinho/"). Dry-run real do CG: 15 paginas -> html, 15 snapshot, 23 referencia, 40 download.
**Consequences:** S6d `5799035`. Tipo `html` (S6b) e o consumidor. LR: sync futura nao muda os 4 labs ate o user decidir a migracao (readd dos 4, decisoes podem se mover). `--pdf` do pull passa a significar so "baixa tudo".

---

### SYNC segurada com o rebuild do CG medido na copia: o criterio 34/35 nao se ajusta ao numero, o motor se ajusta ao criterio

**Date:** 2026-09-04
**Status:** Superseded em 04/09 (entrada seguinte: o user aceitou 33/35 com causa e promoveu o rebuild)
**Decision:** O rebuild limpo do CG pela API (S6f) fica na copia `.ablacao/CG-rebuild` ate o C0 item 11 calibrar a regra `exclusivo` do disambiguator; a SYNC so fecha com holdout curado >= 34/35 SEM ruido. O CG original, o perfil e o gold versionado nao mudam ate la.
**Reasoning:** O 34/35 do baseline dependia de um token de boilerplate ("imagens") que criava competicao falsa e flagava `transformacoesgl`; o motor honesto da 33/35 porque `exclusivo` (s2=0) da banda alta a UM token generico ("geometrica" -> bloco-15). Medido nos 6 golds: 22 decisoes alta por 1 token, 5 erradas (77%), contra 94% dos outros baldes. Aceitar 33 rebaixaria o criterio para caber no motor; segurar mantem "gold nao e oraculo, mas regua nao se dobra".
**Consequences:** C0 vira o trabalho em execucao (ordem proposta 11 -> 10 -> 9 -> 12). Quando a SYNC voltar: rerodar `docs/reports/_harness-2026-09-03/s6f/holdout_cg_rebuild.py` com o gerador novo, revisar `revisar_queue.md` e `formulas_index.md`, promover a copia, apontar `stash_folder` para `C:/Users/Humberto/Desktop/Moodle/computacao-grafica/stash`, trocar `ground_truth_CG.csv` pelo re-chaveado.

---

### SYNC fechada com o rebuild do CG promovido: 33/35 aceito porque o 34 do criterio era ruido, nao regua

**Date:** 2026-09-04
**Status:** Active
**Decision:** O rebuild limpo do CG pela API vira o original (`Computacao-Grafica-Tutor` `a16051b`, 66 entries); o perfil aponta para o stash novo; `ground_truth_CG.csv` passa a ser o re-chaveado (35 scorable). O criterio "holdout curado 34/35" e aceito em 33/35 COM a causa medida e registrada (regra `exclusivo` do disamb por 1 token, C0 item 11a), sem rebaixar o criterio para lotes futuros: o 34 volta a valer quando o item 11a entrar.
**Reasoning:** O user reverteu "segurar ate o C0" porque manter o CG no export antigo nao faz sentido: o stash novo e o material real (paginas como html, formulas transcritas, 0 impressao em PDF) e o 34/35 anterior dependia de um token de boilerplate ("imagens") que criava competicao falsa. Aceitar o numero honesto com a causa documentada e diferente de dobrar a regua ao numero. Holdout puro 31/35 (conf-err 2, flagados 9) e curado 33/35 (conf-err 2, flagados 1) no CG novo; curada dos 5, sentinela e determinismo intactos.
**Consequences:** SYNC 6/6 fechada; C0 aberta com o 11a primeiro; export antigo em `.ablacao/CG-export-backup`; revisao humana das 45 duvidas e 37 formulas fica aberta sem travar campanha.

---

### C7 IMAGENS: campanha propria para duplicatas e logos, estacionada (nao entra na C0)

**Date:** 2026-09-04
**Status:** Active
**Decision:** Imagens saem da caixa de ideias e do escopo da C3 e viram campanha C7 (estacionada, posicao decidida na fronteira). Objetivo do user: nenhuma imagem captada 2 ou mais vezes e logos/templates fora do tutor, via galeria curada por ele (`<repo-tutor>/content/images/logos/`, parcial) com dHash<=8 — nao regra automatica.
**Reasoning:** Medido no CG (977 imagens): 299 logos em `<repo-tutor>/content/images`, 0 citados em markdown, chegam pelo bloco de `resolve_content_images` que copia toda imagem extraida para o Image Curator; 3 familias de extracao por PDF (pymupdf, Datalab, `.pdf-NNNN-NN`) deixam 359 orfas. Cluster dHash automatico sem galeria flagaria 84 imagens citadas (GIFs de formula) -> refutado; md5 exato pega so 203/296; a galeria do user com dHash<=8 deu 0 falso positivo nos 8 tutores (CG 3, TCC 25, SO 2, IA 1, conferidos na imagem).
**Consequences:** C0 segue aberta com o 11a; C3 perde "imagens"; a galeria e dado em `<repo-tutor>/content/images/logos/`, que o user amplia; gate da C7 no handoff 2026-09-04 (fila, item 8).

---

### C0 11a: exclusividade lexical com um so token deixa de ser confianca

**Date:** 2026-09-04
**Status:** Active
**Decision:** No disambiguator, `exclusivo` (s1>0, s2=0) so e banda alta com 2+ tokens discriminantes; com 1 token o best fica, mas sai em banda media e flagado (voter e card decidem). Entrou no gerador (`728c0f1`) e nos 8 tutores por reprocess registrado.
**Reasoning:** Medido antes do codigo: 22 decisoes alta em 1 token nos 6 golds, 5 erradas (77%) contra 94% com 2+ tokens ou margem. Depois, na mesma base: conf-err 3 -> 2 (motor puro), holdout CG puro conf-err 2 -> 0 e curado 33 -> 35/35, bloco/AULA/REF/curada iguais, unidade +1. Custo medido: 23 votos de LLM a mais (votos/100 29,9 -> 36,5; revisar/100 54,0 -> 58,3). determinismo 8/8 (0 arquivos nao deterministicos).
**Consequences:** C0 segue com 11b (LLM so nos flagados, contado). FR `udp-example-c` e `java` separados pelo voter sem gold — observar na C1. Divida: `tests/test_unit_matcher.py` grava o ledger do MF real a cada suite (corrigir em C4 ou antes).

---

### C0 11b: a via 'serie confiante' do voter fica; votos contados no CRONOGRAMA_HEALTH

**Date:** 2026-09-04
**Status:** Active
**Decision:** O voter continua votando em decisao flagada, membro de serie same-theme (mesmo confiante), prova/trabalho sem due e funil; nenhuma mudanca no motor. O CRONOGRAMA_HEALTH ganha a secao 'Votos de LLM' (decisoes por llm/llm-funil e flagados, por 100 entries) na mesma regua do censo (`86dab7e`).
**Reasoning:** Medido nos 8 originais recomputando o motor sem voter: dos 22 votos de serie, 17 caem onde o motor ja decidia sem flag, mas em 1 deles (MF exerciciosdafny2) o motor confiante erra e o voto acerta. Cortar poupa 17 votos (13%) e cria 1 conf-err na curada — regride, nao entra. O residual flagado em AULA no produto e 7,9/100 (15/189, todos sem 2o candidato), abaixo do gate de 8. determinismo 8/8 (0 arquivos nao deterministicos).
**Consequences:** Item 11 fechado (11a+11b); C0 segue com o 10 (medir os 12 erros de unidade antes de codigo). Regua por item (com vocab + curada + holdout, ablacao so em gate) continua decisao aberta do user.

---

### C0 10: ancora lexical exclusiva vence a ordem do plano no mapa bloco->unidade

**Date:** 2026-09-04
**Status:** Active
**Decision:** Em `assign_units_positional`, depois da DP monotonica, um bloco com >= 2 tokens na unidade argmax, margem >= 1 e um token que so essa unidade tem no plano recebe essa unidade (so ele). Um token continua indicio; token exclusivo de duas unidades e ambiguo e fica com o otimo global. Entrou no gerador (`4a14d8b`) e nos 8 tutores.
**Reasoning:** Dos 12 erros de unidade do motor puro, 10 eram o mapa bloco->unidade errado onde o professor sai da ordem do plano (SO Arquivos depois de E/S) e a curada corrigia com pino manual. A DP segmentada por ancoras muda 12-14 blocos e perde pino; a ancora so no proprio bloco muda 3 blocos nos 8 tutores, todos confirmados por pino ou secao do Moodle, unidade 179 -> 183/191 e nenhuma outra regua se move. determinismo 8/8 (0 arquivos nao deterministicos).
**Consequences:** C0 em 8/11; proximo item 9 (refactor corte 1, byte-identico). Sem alavanca estrutural: SO bloco-06 (deadlock e juizo humano), IA blocos 01-02, SO sockets.

---

### C0 9: scripts/ cortado por grafo de dependencias medido, nao por lista de gosto

**Date:** 2026-09-04
**Status:** Active
**Decision:** `scripts/` fica com 37 (handoff §Ferramentas + dependencias + utilitarios e ferramental de gold com teste vivo); 44 + `docs/reports/_archive/scripts-2026-09-04/artefato_razao/` vao para `docs/reports/_archive/scripts-2026-09-04/` por `git mv` com README; testes que so testavam scripts arquivados vao junto. A regua AULA perde a escada (H1/H7 refutados, H8/H9 ja producao) e fica so com o numero do motor puro.
**Reasoning:** O grafo completo (import, `from scripts.X import`, subprocess por caminho) achou 5 dependencias que o scan simples nao via; arquivar por lista quebraria `moodle_pull`, a ablacao e 2 ferramentas de gold. O alvo ~25 do plano era estimativa; o dado deu 37. `src/` intocado, logo tutores byte-identicos; suite 2312 verde; sentinela 0/8.
**Consequences:** C0 em 9/11; falta o item 12 (travessia "depois", medicao). Licao registrada: a suite do gate roda depois do reprocess registrado (o baseline de caracterizacao do CG ficou stale no item 10 e foi regenerado em `599ff10`).

---

### C0 MOTOR fechada 11/11; travessia 'depois' mostra que o limite agora e o indice, nao a atribuicao

**Date:** 2026-09-05
**Status:** Active
**Decision:** C0 fecha com o item 12 (medicao). C1 TRAVESSIA vira a campanha aberta com entrada numerada: FILE_MAP completo (clamp 12 KB -> 80 KB), linha do FILE_MAP com `moodle_label`, label de bloco duplicado no cronograma. C3 e a proxima pela ordem registrada; a posicao da C7 IMAGENS e decisao do user.
**Reasoning:** Travessia rerodada nos 3 cursos x 3 modos com a mesma regua de 03/09: IA identico (0 chamadas novas, indices iguais), FR material 15/15, CG com LLM 7/15 onde os 7 acertos tem alvo dentro do FILE_MAP e os 8 erros tem alvo fora do corte (26/93 citados). O motor (C0) melhorou o 'quando' (CG bloco 8 -> 10/11 sem-llm, 7 -> 8/11 LLM) e nada regrediu por ele. O piso sem-llm do CG caiu 10 -> 5 porque o rebuild grava `title` = nome do arquivo.
**Consequences:** Reguas finais da C0 (motor puro +vocab): bloco 183/200 conf-err 2 · unidade 183/191 · cobertura 53/57 · subunidade 82/93 · AULA 174/189 · holdout CG puro 31/35 conf-err 0 / curado 35/35 · curada 199/200 · 191/191 · 55/57 · censo revisar/100 58,0 · votos/100 36,5. Handoff 2026-09-04 segue vivo com C1 aberta.

---

### C1 item 1: FILE_MAP completo e magro — o roteador lista todos os materiais, a rastreabilidade vai para o TRACE

**Date:** 2026-09-05
**Status:** Active
**Decision:** Teto do FILE_MAP 12 KB -> 80 KB (aviso mantido); linha de rastreabilidade sai para course/FILE_MAP_TRACE.md (mesma numeracao, sem clamp); titulo = moodle_label com fallback title; Secoes <= 3 headers / 80 chars; '|' no titulo vira '/'. Entrou no gerador (`0ff832a`) e nos 8 tutores.
**Reasoning:** Medido: com 12 KB o FILE_MAP citava CG 26/93, IA 22/59, MF 31/66 e a travessia do CG errava exatamente os alvos fora do corte (8/8). Cada material custava ~480 chars por causa da linha de rastreabilidade; sem ela e com Secoes limitada, os 8 tutores completos cabem em 3,7-21,8 KB. Travessia depois: ver tracker §C1 ITEM 1. determinismo 8/8 (0 arquivos nao deterministicos).
**Consequences:** Medicoes que dependiam da linha '↳' (harness da travessia, watchdog do censo) passaram a ler o TRACE pelo numero e o label. Proximos da C1: label de bloco duplicado no cronograma; title do material html = label no manifest (piso sem-llm).

---

### C1 item 2: titulo de bloco qualificado so em colisao; CRONOGRAMA_DETALHADO nao depende de haver codigo

**Date:** 2026-09-05
**Status:** Active
**Decision:** No CRONOGRAMA_DETALHADO, blocos com o mesmo label no curso ganham um qualificador do proprio bloco (topic_text; senao a 1a sessao); o artefato passa a ser gravado sempre que ha blocos (estava dentro de `if code_entries`, TCC e LR nao o tinham). Sem LLM: o efeito no 'quando' da travessia espera a recarga. A raiz da colisao do FR (aliases de todas as camadas no topico 'Modelos OSI e TCP/IP') fica na caixa: exige gold de topico.
**Reasoning:** Medido nos 8: 7 labels repetidos, 16 blocos, 33 materiais; o flip 'osi tcp ip' do item 12 veio dai. Mudanca deterministica, byte-identica fora das colisoes.
**Consequences:** determinismo 8/8 (0 arquivos nao deterministicos); proximo C1 item 3 (title = label no manifest, medir antes). Ideia registrada na caixa: Datalab para imagens, Gemini so fallback (custo).

---

### Gold pelo oraculo: SARC e Moodle mandam; gold e humano e se corrige; curadoria e a camada humana, nao remendo no motor

**Date:** 2026-09-05
**Status:** Active
**Decision:** Quando gold e SARC/Moodle divergem, vale o professor: TCC aula-17 -> bloco-19, MF arvores/listas -> bloco-05, IA prova antiga fora do gold. A regua de bloco honra `scorable`. Onde o produto seguia o gold antigo, o alinhamento veio por curadoria registrada (pinos MF, card do TCC), nao por regra no motor.
**Reasoning:** 4 alavancas estruturais para os erros restantes do motor puro foram medidas e refutadas (label x2/x3; janela = secao em 2 formas; data de postagem). O que sobra e duvida legitima (voter) ou juizo humano (pino). Curadoria e desenho da arquitetura, e fixes especificos ali sao legitimos; fixes de raiz vao para o motor so com saldo medido.
**Consequences:** Reguas: motor puro 186/199 conf-err 1; curada 198/199 conf-err 0 (falta azure = imagens, C7). Caixa: capturar `duedate` na SYNC (trabalhos), janela do card so com dado novo.

---

### C1 item 3: o `title` do manifest fica o nome do arquivo; o label do Moodle e coluna, nao substituto

**Date:** 2026-09-05
**Status:** Active
**Decision:** Nao substituir `title` por `moodle_label` no manifest (nem em `build_stash_entries`, nem por reprocess). O label ja e a coluna Titulo do FILE_MAP (item 1); o motor soma title + label em conjunto. Item 3 da C1 fecha por medicao, sem codigo; entra em NAO fazer.
**Reasoning:** Medido antes de codigo (sessao 6): piso sem-llm da travessia com title := label em memoria, 0 flip em IA/FR/CG; motor puro +vocab nas copias, bloco 186 -> 184/199 (MF `exercicios-conjuntos`/`exercicios-arrays`: label "Respostas" apaga `conjuntos`/`arrays`), 2 decisoes confiantes viram flag; subunidade, unidade e holdout CG identicos (remedido limpo, 0 chamadas Gemini, apos o incidente de 60 resumos); 0 flip positivo. Nome de arquivo e label sao sinais complementares (103 entries tem token so no title; 7 labels sem token de conteudo). A queda do piso CG 10 -> 5 foi entre manifests diferentes, nao efeito do title.
**Consequences:** C1 so tem trabalho com LLM (travessia final; prompt do voter com label — 90/125 votados tem label != title; FILE_MAP "label · stem" so se a travessia errar). Sem Gemini, a proxima acao e decisao de fila do user.

---

### Subunidade do motor puro: IDF intra-unidade refutado; o teto e vocabulario (glossario manual = curadoria); medicao em copia roda com tripwire Gemini

**Date:** 2026-09-05
**Status:** Active
**Decision:** Nao entra IDF intra-unidade no scorer de subtopico. A subunidade do motor puro (82/93) fica como teto de vocabulario: os termos que decidem os 4 notebooks do IA (`perceptron`, `rede neural`, `MLP`, `kNN`) existem so no glossario MANUAL, camada humana que a ablacao remove por desenho. Toda medicao em copia `.ablacao` roda com o tripwire Gemini do `shim_b.py` e o pos-check `check_gemini_hoje.py`.
**Reasoning:** Simulado em memoria pela rota real (base reproduz 92/93): V1 tokens 0 flip; V2 frases +1/-5 (o token `Agrupamento` e compartilhado com aliases-sessao do topico de introducao e V2 tira o dono legitimo); V2s 0/0. Duas variantes de card ja tinham dado 0/+ 23/- e 0/+ 2/-. Incidente: o reprocess chama Gemini para re-resumir codigo quando o hash da entry muda (`gemini_auto_summarize` na UI); a medicao title := label custou 60 resumos nao autorizados e contaminou a 1a rodada (sub 81, CG 10 mudancas); refeita limpa, bloco 184/199 e 2 confiantes iguais, sub 82 = 82.
**Consequences:** §OS 32 ERROS e §C1 ITEM 3 (INCIDENTE) no tracker; NAO fazer do handoff ganha as duas refutacoes; decisao aberta do user: desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado. Sem LLM, bloco/unidade/subunidade do motor puro nao sobem: o que resta e voto ou pino.

---

### Propagacao de vocabulario por headings (sem LLM) fica na caixa: +5 no gold de subunidade, mas sem gold nos outros 4 cursos nao entra

**Date:** 2026-09-05
**Status:** Active
**Decision:** A 2a passada de subunidade (tokens exclusivos dos headings dos confiantes viram aliases; teto de df 25%; so onde a 1a passada nao decidiu) NAO entra no motor agora, apesar de 82 -> 87/93 no gold e curada intacta. Entra so depois de gold de subunidade do CG e do MF (proposto-claude, aprovado pelo user) e saldo medido nos 8.
**Reasoning:** No gold o ganho e real e estavel em conf >= 0,7 (min 2-3 entries), mas nos cursos sem gold a mesma regra muda MF 6 e CG 9 subunidades, varias visivelmente erradas (self-training amplifica o boilerplate de headings do OpenGL); sem o teto de df, (0,9;2) dava -20. "Saldo medido nos 8" e lei; 4 cursos sem regua nao contam como saldo.
**Consequences:** Caixa do handoff + decisao aberta do user (gold CG/MF, C5). Ate la, subunidade do motor puro = 82/93 por vocabulario. `gemini_auto_summarize` desligado na UI pelo user em 05/09 tarde.

---

### CG: unidade pela camada humana (pinos de bloco pelo oraculo) + higiene generica do vocab compilado; sinonimo manual nunca renomeia bloco

**Date:** 2026-09-05
**Status:** Active
**Decision:** As 22/93 unidades erradas do CG se resolvem com (a) higiene generica no loader do glossario — sinonimo compilado por LLM igual a nome de secao do Moodle nao vira alias (`e0c433c`) — e (b) pinos de unidade nos blocos 06 (u04), 08 (u03) e 15 (u07), derivados do SARC/Moodle, o mesmo mecanismo dos outros 7 tutores. Nenhuma regra nova no mapa bloco->unidade. Sinonimo manual e vocabulario de SUBtopico e nunca pode renomear um bloco.
**Reasoning:** Raiz medida: o compilador de vocabulario pendurou nomes de secao ('Morfologia Matematica', 'Manipulacao de Imagens', 'Mapeamento de Texturas') nos topicos genericos de u01 e o mapa, o scorer e o rotulo do bloco-08 seguiam a secao errada; a ordem do professor (u04 -> u07 -> u03 -> u07 -> u06) inverte o plano e a DP monotonica so aceita um desvio. Cinco alavancas genericas medidas nos 8 e refutadas: sem aliases 183 -> 136/191; radicais saldo 0; vizinho ancorado 183 -> 163; exclusividade relaxada 179; higiene sozinha neutra. O sinonimo 'Morfologia' em '3.5 Segmentacao' rotulou o bloco-08 e moveu 4 materiais do bloco certo: revertido.
**Consequences:** CG `2c5e01e`: unidade 22 -> 1 errada (+2 por erro de bloco flagado); todas as reguas iguais (motor puro 186/199, holdout 31/35, curada 198/199); 0 chamadas Gemini (tripwire de produto). Dividas de dados novas (C5): GLOSSARY.md do CG para em 7.1.2 (u08 sem termo); zips do MF colidem nomes; gold de unidade do CG.

---

### Regua oficial e a AUTOMATICA (motor + voter cacheado, sem pino, sem glossario manual); gold so mede; curadoria por curso e andaime

**Date:** 2026-09-05
**Status:** Active
**Decision:** A meta de precisao e medida no pipeline automatico, nao no motor puro (diagnostico) nem na curada (produto de hoje). Golds existem para medir; nao se cria curadoria por curso como caminho para a precisao. Pino e glossario manual sao andaime: cada um precisa de regra generica ou voto de LLM que o substitua, medido nos 8, ou fica registrado como residuo humano com nome.
**Reasoning:** Medido em 05/09 tarde (`motor_auto.py`, 0 chamadas, 0 votos pulados): bloco 192/199 (96,5%, conf-err 0), unidade 185/191 (96,9%), holdout CG 35/35, subunidade 82/93 (88%). O automatico ja passa de 95% onde o aluno pergunta quando e em que unidade; abaixo de 95% so a subunidade, cujo bloqueio e vocabulario (o plano nomeia categorias, o material nomeia algoritmos). Dos 3 pinos do CG: bloco-06 ja nao precisa (higiene), bloco-15 e coberto por radical-fallback (generico, 0 colateral), bloco-08 nao tem sinal lexical possivel (plano nao menciona morfologia) — residuo para voto de LLM de unidade.
**Consequences:** Handoff 2026-09-05b registra a regua automatica como oficial; motor puro e curada continuam medidos como diagnostico e produto. Proximos genericos: radical-fallback (caixa), voto de LLM de unidade para bloco sem evidencia (Gemini), vocab compilado que emita nomes de algoritmos, propagacao por headings validada com o gold CG/MF.

---

### Radical so como fallback no mapa bloco->unidade; pinos do CG 06 e 15 removidos (regra generica cobre); bloco-08 e residuo nomeado

**Date:** 2026-09-05
**Status:** Active
**Decision:** `assign_units_positional` ganha ancora por radical de 6 chars SO para bloco sem ancora exata possivel (aff < 2), com as mesmas exigencias da ancora exata (`ff21cab`). Os pinos de unidade dos blocos 06 e 15 do CG saem (a higiene e o radical-fallback os cobrem; produto identico); o pino do bloco-08 fica como residuo com nome ate existir voto de LLM de unidade para bloco sem evidencia lexical.
**Reasoning:** Medido nos 8 antes do codigo: RF muda 1 bloco (CG 15 -> u07 = pino), 0 colateral, unidade 183 = 183/191; radical em tudo, generico por radical entre unidades (183 -> 172), heranca por afinidade zero, alias boilerplate, bloco flagado sem imposicao e gate por confianca do texto (saldo -17 a -2) foram refutados. Regua automatica remedida com vocab e cache do produto: CG unidade 22 -> 6 erradas (morfologia x3, texturas x3), holdout 35/35, 5 cursos bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · sub 82/93 (0 votos pulados; era 192 com o cache antigo da copia); determinismo 8/8, 0 arquivos nao deterministicos.
**Consequences:** CG `0d2020a` com 1 pino; motor puro/curada/holdout iguais; suite 2326. Caixa: voto de LLM de unidade para bloco sem evidencia (Gemini).

---

### Subunidade: propagacao de vocabulario por headings entra no motor como 2a passada (so onde a 1a nao decidiu); glossario manual deixa de ser necessario no IA

**Date:** 2026-09-05
**Status:** Active
**Decision:** `apply_unit_subunit_fields` ganha uma 2a passada: tokens exclusivos dos headings/titulo dos materiais confiantes (>= 0,7) de um subtopico viram aliases dele e so os materiais vazios/ambiguos/fracos sao repontuados (`4a239d9`, limiares em `thresholds.T`). Decisao confiante nunca e sobreposta. Reason gravada `propagado-headings`.
**Reasoning:** Pedido do user: subunidade automatica sem LLM, gold so mede. Medido em memoria pela rota real nos 6 golds (233): +5 -0 (IA perceptron x3 + mlp-xor, SO exemplo3), FR/LR 0 mudancas; grade de 8 pontos estavel em conf 0,7; cada salvaguarda tem a perda que evita medida (stems genericos, df 25%, minimo 2 confiantes, exclusividade, so nao-confiantes). Gates: motor puro sub 82 -> 87/93 com bloco/unidade iguais; automatica bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · **sub 87/93 (93,5%)**; holdout 35/35; curada igual; produto x 6 golds 193/233 igual; determinismo 8/8.
**Consequences:** Reprocess registrado dos 8 (MF/IA/ES2/TCC commitados; 4 tutores so `updated_at`, sem commit). Residuo da subunidade no puro: SO fork/exec x4 (regra humana do gold que o IA contradiz) e ES2 quase-empates x2.

---

### Camada 3 (resumos de codigo por LLM) medida para a regra 'no maximo duas camadas LLM': so a subunidade a sente; substituto deterministico pela mesma rota

**Date:** 2026-09-06
**Status:** Proposed (decisao do user: qual camada cortar)
**Decision:** Medido em copias com tripwire (0 chamadas), motor puro + vocab + propagacao: sem resumos de codigo a subunidade cai 87 -> 71/93; com `code_curation.json` produzido deterministicamente a partir dos `.md` que o motor ja gera (mesmo bundle que o Gemini recebe, mesma rota `code_curation_signal_text`) 78-79/93; bloco 186, unidade 183, cobertura 53 e holdout CG 31/35 iguais nos 4 regimes.
**Reasoning:** Pedido do user: motor o mais automatico possivel, no maximo duas camadas LLM, sem rotas novas. Peso no produto (8 tutores): 1 compilacao de vocab por curso, 85 resumos (1 por arquivo, cache por hash), 205 votos. Ganho por camada: vocab +57 sub/+10 unidade; voter +7 bloco/+4 holdout/conf-err 0; resumos +8 sub e 0 no resto. Os 8 que so o Gemini acerta (SO threads x3, IA perceptron x5, ES2 roteiro1) dependem de vocabulario de categoria que o codigo nao contem ('classificacao', 'chamadas de sistema', 'microsservicos') — o resumo e um remendo da camada 2. "% de similaridade vocab x nome do material" tambem medido: e o que o scorer ja faz; Jaccard >= 0,5 acerta 27/0 mas deixa 66 sem atribuicao; label do plano sem LLM 9/0/84.
**Consequences:** Se o user cortar a camada 3: trocar o produtor de `code_curation.json` (`c1-3/shim_codigo.py` v2 como base), manter a rota; custo -8/93 na subunidade. Alternativa que mantem duas camadas sem perder os 8: compilacao do vocab ver o bundle de codigo (exige Gemini para remedir). Nenhuma rota nova.

---

### Golds de subunidade CG e MF aprovados: a regua de subunidade passa a 233 e o numero de referencia vira o da automatica nos 6 (80,3%), nao 87/93

**Date:** 2026-09-06
**Status:** Active
**Decision:** User aprovou os golds propostos (com os 4 rulings). `subunit_gt_MF.csv` entra em `scripts/motor_puro.py` e `subunit_gt_CG.csv` no `holdout_cg.py`, ambos pelo scorer compartilhado `ablacao_rapida.score_subunit`. Remedido com tripwire: automatica x 233 = 187 (80,3%; SO 11/15, IA 39/39, ES2 26/28, TCC 11/11, MF 51/58, CG 49/82); produto 193 (83%); CG puro sem vocab 39/82.
**Reasoning:** Os 87/93 eram in-sample (golds nascidos com a curadoria dos 4 cursos; regras e prompt afinados neles). O CG, unico curso nao usado para afinar, da 60%. Gold so mede: o motor nao o le; sem gold nao ha numero, so os sinais de duvida do motor, que apontam o curso (revisar/100) mas acertam so metade dos erros (20/40) e erram confiantes nos outros 20.
**Consequences:** Alvo da subunidade passa a ser o CG (33 erros: 11 vazias, 10 confiantes, 9 gold-vazio-preenchido, 2 ambiguas, 1 fraca) e o MF (7). Bloco e unidade seguem >= 96,9% na automatica. Um curso 100% novo deve esperar o numero do CG, nao o dos 93.

---

### Subunidade: partes do rotulo composto do plano viram aliases na 2a passada (teto de df, exclusividade no curso); fila de revisao sem a camada llm

**Date:** 2026-09-06
**Status:** Active
**Decision:** (1) `resolver_apply._partes_de_rotulo` alimenta a 2a passada (`propagar_vocabulario_por_headings`) com as partes dos rotulos compostos ('Bezier e Algoritmo de Casteljau' -> 'Bezier', 'Algoritmo de Casteljau'; 'Algoritmos de X' -> 'X' quando a cabeca e generica no curso), sob as salvaguardas da propagacao (df <= 25%, exclusividade no curso inteiro incluindo titulos de unidade, nunca sobre decisao confiante). Reason `rotulo-decomposto`. `ff3eda7`. (2) `revisar_de` deixa de classificar voto de LLM na janela como pendencia (`0673150`).
**Reasoning:** Diagnostico dos 33 erros do CG pela rota real: o plano nomeia por frase composta e o material pela parte (bezier x4 valiam 0,12). Simulado na 1a passada: +9 -1 nos 6 golds; na taxonomia (1a passada, sem df) custava 1 cobertura no SO ('saida' = titulo da unidade) e o teste do holdout FR ('Internet'): por isso a rota e a 2a passada com df. Gates: bloco/unidade/cobertura iguais em todas as reguas; CG automatica 49 -> 54/82; automatica x 233 187 -> 192; produto 193 -> 197 (ES2 devops 28 -> 27: parte "Integracao continua" de "Integracao continua (CI)" esta na aula de DevOps; gold diz conceito). Fila: camada llm era 79/200 itens por 2 erros (voto 75/76 no gold): 57,5 -> 33,0 por 100 sem perder bloco/unidade/subunidade. Determinismo 8/8, 0 arquivos nao deterministicos.
**Consequences:** Reprocess registrado dos 8 duas vezes (fila; decomposicao): HEADs MF ed31d99, SO f513ba0, IA 74fec68, ES2 0fe0f53, TCC 082b728, LR d139547, FR 4c64ed6, CG 929cdc3. Residuo do CG (28/82): 9 gold-vazio (alias 'OpenGL' do vocab LLM em `conceitos`), 3 morfologia (unidade a montante), 5 paginas de login (dado), confiantes errados (a 2a passada nao os toca por desenho). Higiene estendida contra nomes de secao REFUTADA (+0 -2).

---

### Subunidade: titulo que nomeia outro subtopico (parte do rotulo) vence decisao confiante que o titulo nao nomeia

**Date:** 2026-09-06
**Status:** Active
**Decision:** Na 2a passada, decisao confiante da 1a cai quando o titulo + label do Moodle contem uma parte de rotulo de outro subtopico Y da unidade (unico) e nenhuma frase do vencedor esta no titulo (`34d8b19`, reason `titulo-nomeia-subtopico`). Unica excecao ao principio "decisao confiante nunca e sobreposta" — e o professor nomeando o assunto no titulo.
**Reasoning:** Simulado pela rota real nos 6 golds (base reproduz o gravado): +2 -0; variante por margem 0/0 (a margem nao separa 7,74 x 0,96). Gates: bloco/unidade/cobertura iguais; 5 cursos 138 = 138; CG 54 -> 56/82; automatica x 233 194 (83,3%); determinismo 8/8, 0 arquivos nao deterministicos.
**Consequences:** Reprocess registrado: subunidade mudou 2 (CG: exercicios-de-geometria-computacional, domina), bloco 0, unidade 0, revisar 0; CG HEAD e598a3c, demais so updated_at. Produto x 6 golds 199/233 (85,4%), primario 166; CG 56/82, ES2 27/28, MF 51/58. Resta no CG (26/82): 9 gold-vazio (alias 'OpenGL' do vocab LLM), 5 login (dado), 3 morfologia (unidade), 5 confiantes entre dois assuntos presentes, 4 vazias/empate sem alias. Teto sem LLM e sem dado novo ~56-58/82.

---

### Subunidade: secao do Moodle que nomeia exatamente um subtopico decide onde nem a 1a nem a 2a passada decidiram (S1b); Moodle e o oraculo tambem para o gold de subunidade

**Date:** 2026-09-06
**Status:** Active
**Decision:** No fim da 2a passada, material ainda vazio ou empatado recebe o subtopico que a SECAO do Moodle nomeia, se for exatamente um da unidade (`4d649c4`, reason `secao-nomeia-subtopico`). Gold do CG `intro` corrigido pelo oraculo (secao "Origens" -> primario `origens`; conceitos/areas-relacionadas extras).
**Reasoning:** Pedido do user: comparar o gold de subunidade do CG com o Moodle, que e o oraculo. Onde a secao nomeia um subtopico, gold = secao em 27/29; as 2 divergencias sao o `intro` (gold errado) e `exemplozbuffer` (gold mais especifico que a secao). Regra simulada pela rota real nos 6 golds: S1b +3 -0; S1 (sobrepoe a 2a passada) +5 -3; S2 (sobrepoe confiante) +5 -13 — a secao nomeia o pai quando o gold e o filho. Gates: bloco/unidade/cobertura iguais; CG 56 -> 58/82; automatica x 233 194 -> 196; determinismo 8/8, 0 arquivos nao deterministicos.
**Consequences:** Reprocess registrado: subunidade mudou 7 (SO 1: laminas-sockets -> comunicacao-e-sincronizacao; IA 3: outros-operadores, programa-exemplo-ag, lista-de-exercicios-i -> algoritmos-de-busca-com-informacao; CG 3: intro -> origens, curvasparametricas -> representacao-de-curvas-parametricas, slab -> algoritmos-de-geometria-computacional), bloco 0, unidade 0, fila 115 -> 110; HEADs SO db71737, IA d88cc53, CG 73ab72e, demais so updated_at. Produto x 6 golds 201/233 (86,3%), primario 169; CG 58/82, SO 15/15, IA 39/39, ES2 27/28, TCC 11/11, MF 51/58. Fila 31,6 (110/348)/100. A secao do Moodle e sinal de subunidade so como ultimo recurso; como override e refutada.
