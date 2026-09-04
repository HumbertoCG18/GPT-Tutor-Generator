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
last_updated: 2026-09-03
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
**Decision:** `.htm/.html` no stash e tipo `html` (antes de `code`: `.html` esta em CODE_EXTENSIONS e virava `codigo-professor` sem texto; `.htm` era ignorado; por isso o pull imprimia pagina em PDF). `core/html_material.process_html` (fachada `RepoBuilder._process_html`, 2 linhas no engine): HTML -> `html_to_structured_markdown` sem teto (`truncate_markdown_blocks(max_chars=None)`) e sem cabecalho web (documento local nao tem URL/dominio/hora) -> cada `![alt](src)` da pagina: `src` relativo ao dir do HTML, `data:image/...;base64` decodificado para arquivo, http externo = `![x — não capturada](url)`; imagem copiada para `content/images/<id>-<arquivo>` (ref raiz-relativa; `resolve_content_images` deixa em paz e `unprocess` limpa por prefixo); Datalab CRU por imagem (GIF direto) com cache por md5 em `course/.image_transcriptions.json` (versionado, como o glossario LLM) e cap por build (400); bloco `$$...$$` na resposta = formula -> bloco + `<sub>fonte: [x](content/images/...)</sub>` + `manual-review/formulas/<id>-<img>.md` ("conferir com o professor", fonte NAO corrigida); `![caption](...)` = legenda -> Gemini PT-BR (`GeminiClient.generate_text`, texto) -> `![Figura: ...]`; vazia -> Gemini descreve (texto + imagem inline); sem Gemini a legenda fica em ingles e a vazia vira nao capturada; falha do Datalab nao entra no cache (tenta de novo no proximo build). Clientes injetados (`datalab_image_fn`, `gemini_text_fn`); testes com os falsos e o gold do piloto Curvas.
**Reasoning:** Dado antes de codigo (03/09, 51 paginas reais do CG: 20 do site + 31 do Moodle): 0/51 paginas passam de 15 000 chars (Vis3d 14 183, a 94% do teto) — o teto vira parametro so para nao cortar material em silencio; 4 paginas vazavam VML condicional do Word porque `inline_html_to_markdown` devolvia `str(node)` para Comment/Declaration (Curvas: ~3 200 dos 11 179 chars do piloto eram lixo; limpa tem 7 917); 3 paginas do Moodle ("resolucao de prova") trazem 20 PNGs em `data:` inline (0,6 a 2 MB de markdown se nao decodificar); 139 imagens no mirror, 0 duplicadas por md5, 0 logos sobrevivem ao conversor (todos em `<td>`) — a regra "logos deduplicados por md5 e descartados" nao tem dado e NAO entrou (md5 e so cache/idempotencia); `resolve_content_images` mataria as formulas (GIFs de 511-918 B < `_MIN_IMG_BYTES` 2000, 2 cores = `is_noise_image`) — por isso a copia e propria e a ref e raiz-relativa; no gold do Datalab 12/12 formulas tem `$$` e 0/9 legendas tem (legendas trazem `$C_1$` inline na prosa e caption + paragrafo descrevendo a MESMA figura: a caption basta). 0 entries `.html` nos 8 tutores e 0 dentro de zips: tratar html como material nao regride nada.
**Consequences:** S6a `6111b46`, S6b `0a8ae2e`, fix de determinismo das referencias url `a10a6ca` (o cabecalho web entrava no hash de `references_curation` e re-sumarizava toda referencia url a cada regeneracao). Curvas na copia do CG: 24 imagens -> 12 formulas + 9 legendas + 3 descritas, 0 nao capturadas, 24 copias, 12 reviews; segunda rodada 0 chamadas e byte-identica. Custo real do CG: ~160 imagens (139 + 20 data-URI) ≈ US$ 1,60, nao ~250. S6d decide se a snapshot mapeia http do mesmo host para o mirror (hoje = nao capturada, 12 refs em 20 paginas); nao copiar `.orig` do snapshot para o stash. Divida do conversor fora do escopo: `**P(****0)` (bold aninhado do Word) — caixa de ideias.
