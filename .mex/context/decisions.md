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

Registradas originalmente em `docs/reports/pendencias.md` (hoje `_archive/pendencias-historico-ate-2026-09-02.md`);
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
**Decision:** Cobertura de prova/entrega é um conjunto de unidades vindo do plano (due-window + `.assessment_context.json` + notas do gold como verdade inicial). Regra IA: P1 = u01+u05; P2 CUMULATIVA = u01+u05+u02+u03; PS = tudo. MF/TCC não-cumulativo.
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
**Decision:** A atribuição temporal nova vive em `src/builder/routing/motor/` (WindowProviders por curso, Disambiguator, gate D4, voter LLM TIER 3 bounded à janela, TIER 2 janela-de-prazo) e roda por curso atrás de `use_anchor_engine`/`use_llm_voter` em `SubjectProfile.feature_flags`, com precedência sobre o legado `use_anchor_placement`. Escreve SÓ campos `temporal_*` (+ sidecar `material_curation.json` de votos, keyed por md5); `computed_*` e pino manual intocados. Funil legado vive até o cutover F5 (deleção por lista nomeada de símbolos).
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
