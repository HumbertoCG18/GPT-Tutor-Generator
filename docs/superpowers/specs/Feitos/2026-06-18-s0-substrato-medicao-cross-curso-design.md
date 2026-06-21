# Design — S0: Substrato de medição cross-curso

date: 2026-06-18
branch base: `feat/reconciliar-unit-bloco`
status: design aprovado (brainstorming) — pré-plano

## Context

Objetivo do usuário: levar a atribuição (arquivo→bloco→unidade→subunidade; e código)
a ~100% de precisão de forma **modular** — funcionar em qualquer cadeira, não um fix
isolado de Métodos Formais (MF) — aproveitando recursos hoje sub-usados (Moodle API +
tokens, Microsoft Graph/M365, OpenSARC/ASP.NET). Restrição forte: **evitar loop de
refatoração**.

A investigação profunda (workflow `auditoria-atribuicao` + leitura direta do código de
precedência, 2026-06-17/18) concluiu que a arquitetura de scoring é sólida e **não merece
rewrite**. O resíduo de erro não está no código do scorer — está em (1) **sinais limpos que
existem mas são dropados** na ingestão e (2) **deploy**: produção roda o funil legado (~41%
no gold de código) enquanto o `concept_resolver` (~70%) fica atrás da flag
`use_concept_resolver` (default OFF). O caminho é **extensão** do fusor (adicionar
sinal+peso) + **cutover** (flip da flag + delete do funil legado), não reescrita.

Decompôs-se o objetivo numa fila de sub-projetos, cada um com spec→plano→eval-gate próprio:

- **S0 — Substrato de medição cross-curso (ESTE spec, primeiro).**
- S0b — Refresh de sinais já-consumidos (source_section, card_block_map). Eval-gated; ver abaixo.
- A1 — consumir `lessons[].text` (resumo-da-semana) no fusor.
- A2 — `posting_date` real no scorer de data (guarda auto-calibrante).
- A3 — âncora de ferramenta data-driven (mata o hardcode `TOOL_TOKENS` MF).
- A5 — `sec.summary`/`mod.description` enriquece blocos de `topic_text` pobre.
- A4 — cutover: flip da flag `use_concept_resolver` ON + **delete** do funil legado.
- A6 — confiança = margem → probabilidade (raiz do `confident_wrong`); só se persistir.
- A7 — limpeza (dead code + artefatos), DEPOIS do cutover.

**Por que S0 primeiro:** sem substrato de medição, nenhuma alavanca é *provável-modular* —
só "funciona em MF", o risco exato a cortar. S0 captura os sinais que faltam **na fonte**,
mede empiricamente o valor de cada um, e produz gold cross-curso que torna A1..A6
eval-gated em qualquer cadeira.

S0 é **estritamente não-mutante para atribuição**: só captura sinais que NENHUM caminho de
produção consome hoje (ou consome só atrás de flag OFF). Nenhuma constante de scoring/fusor
muda; a flag fica OFF; os invariantes GOLDEN ficam intocados. (Os sinais que JÁ afetam
atribuição — source_section, card_block_map — saem do S0 para o S0b, eval-gated.)

## Precedência de atribuição (mapa verificado por leitura)

Há vários sistemas de atribuição, mas eles formam uma **pilha determinística de
precedência** (maior vence), não concorrência aleatória. O risco a gerenciar: mexer no
INPUT de uma camada de cima muda o resultado silenciosamente.

**BLOCO** (`resolve_unit_block_tags`, content_taxonomy.py:1137-1236):
1. `manual` — `manual_timeline_block_id` → conf 1.0 (cap 1.0). Absoluto.
2. `review_rule` — nome casa "revisão"+P1/P2/PS/G2 → 0.95 (cap 0.95). "vence card/score"
   (content_taxonomy.py:1180).
3. `card` / `card+scorer` — `source_section` → `lookup_card_blocks` (card_block.py:130:
   card_map OU, sem map, `resolve_card_to_block` heurística 4-fases data/título/tópico/
   tokens) → 0.85 / 0.80.
4. `scorer_only` — `score_entry_against_timeline_block` (gate best≥0.95, senão fallback
   "pega o melhor") → 0.70.
- \+ janela S5 `assign_due` (card_block.py:137) restringe candidatos do scorer p/
  trabalho/código.
- \+ **[resolver, flag ON]** `apply_concept_resolver` (resolver_apply.py:111) pós-processa e
  SOBREPÕE `computed_block_id`. **OFF em produção.**

**UNIDADE** (content_taxonomy.py:1079-1095, 1257-1272):
1. `manual_unit_slug` → 1.0.
2. auto scorer (`auto_map_entry_unit_fn` + `build_learned_unit_boosts` do `tag_profile`).
3. `reconcile_unit_with_block` (file_map.py:598): bloco define unidade se
   `block_confidence >= unit_confidence`; senão mantém unidade forte + flag conflito.

**SUBUNIDADE** (content_taxonomy.py:1097-1121):
1. `manual_subunit_slug` → 1.0.
2. auto subtopic scorer, gated `SUBUNIT_TAG`; **input enriquecido com o resumo Gemini de
   código** (`code_curation`, content_taxonomy.py:1070) — consumidor de produção à parte.

Implicação direta para S0: backfillar/regenerar um input de camada 1-3 (source_section,
card_block_map) **muda atribuição** → não pode estar num passo dito "inerte". Daí o split
S0 (inerte) × S0b (eval-gated).

## Achado empírico (probe read-only, 2026-06-18)

`scripts/moodle_probe` + inspeção de `core_course_get_contents` nas 5 cadeiras 2026/1
(234 arquivos): `timecreated`/`timemodified` reais.

| Curso | arquivos | stale (ano<2026) | timemodified por mês |
|---|---|---|---|
| MF (92717) | 75 | 0 | Fev=55, Abr=2, Mai=9, Jun=9 |
| IA (93156) | 68 | 0 | Fev=54, Mar=2, Abr=8, Mai=1, Jun=3 |
| SO (92854) | 36 | 0 | Mar=32, Mai=4 |
| ES2 (92714) | 30 | 0 | Fev=21, Abr=1, Jun=8 |
| TCC (93728) | 25 | 0 | Fev=4, Mar=5, Abr=8, Mai=5, Jun=3 |

Conclusões que orientam o design:

1. **0/234 stale.** Nenhum material usado em 2026 tem `timemodified` de ano anterior. O
   medo "restore carrega data antiga" não se materializa neste Moodle; o PUCRS reseta o
   timestamp no upload. `timemodified ≈ timecreated` (data de upload real). `posting_date`
   é **seguro de capturar**.
2. **Padrão varia por professor (insight de modularidade):**
   - *Batch-dominado* (MF/IA/SO/ES2): lump grande no início do semestre + filete. ~70–85%
     empilhado no começo → a data não discrimina a semana da maioria; só os uploads do meio
     do semestre carregam sinal por-semana.
   - *Bem distribuído* (TCC): quase semanal → `posting_date` é âncora forte.
3. Implicação p/ A2 (consumo, fora deste spec): valor real mas **parcial e por-curso**. A
   guarda tem que ser **auto-calibrante** — detectar o cluster de início-de-semestre por
   curso e só confiar em datas fora dele. S0 entrega o dado + a métrica; A2 decide.

## Goals

- Capturar `posting_date` (`timemodified` + `timecreated`) **na fonte**, um caminho só
  (import futuro e migração de repos antigos convergem). Campo NÃO consumido por atribuição.
- Capturar a **chave de turma** (Turma NNN do Moodle + GUID/ano/sem do SARC) como registro
  no perfil/manifest. Sem atribuição turma-scoped (decisão: 1 turma por repo).
- Migrador **estritamente aditivo** que aplica só as capturas não-consumidas aos repos já
  gerados (rebuild_diff=0 verdadeiro).
- Probe que mede empiricamente a utilidade do `posting_date` por curso (cluster de início,
  fração off-batch, stale).
- Gold **full file→bloco** cross-curso (ES2/IA/SO + MF) + eval-gate de regressão por curso.

## Non-Goals (anti-loop — explícito)

- **Zero mudança de atribuição no S0.** Só captura campos que nenhum caminho de produção
  consome: `posting_date`/`turma` (novos, ninguém lê), `moodle_label` (consumido só no
  resolver/flag OFF; fill-if-empty), `lessons_index` (consumo revertido; ninguém lê).
- **`source_section` e `card_block_map` ficam de fora do S0** → S0b (eval-gated), porque
  alimentam a rota de card (precedência 3, acima do scorer).
- Nenhuma constante de `file_map.py`/`concept_resolver.py`/`thresholds.py` muda.
- A flag `use_concept_resolver` continua OFF. Nenhum cutover.
- Sem rewrite. Invariantes GOLDEN intocados: `assign_units_positional` (unit_matcher.py:52),
  `_build_timeline_index` (timeline/index.py:2026), `finalize_block` (index.py:42), review
  rule, golden PDF 5/5 (`eval_assignments.py`).

## Componentes

### C1 — Captura de `posting_date` na fonte

- `SectionFile` (src/builder/sources/moodle.py:97, frozen dataclass): adicionar
  `timemodified: int = 0` e `timecreated: int = 0` (epoch). Defaults mantêm compat com os
  construtores posicionais (moodle.py:132).
- `iter_section_files` (moodle.py:122): ler `f.get("timemodified")` / `f.get("timecreated")`
  por content-file → SectionFile.
- Novo `backfill_posting_date_from_api(manifest_entries, contents)` espelhando
  `backfill_moodle_label_from_api` (moodle.py:137): match por basename **único**
  (colisão = pulado), retorna `{id: {"timemodified": int, "timecreated": int}}`.
- `FileEntry` (src/models/core.py): adicionar `posting_date: str = ""` (ISO `YYYY-MM-DD`
  derivado de `timemodified`) e `posting_date_created: str = ""` (de `timecreated`).
  `from_dict` filtra por `fields(cls)` → campo novo no dataclass persiste; adicionar teste
  round-trip. Guardar ISO (não epoch) por legibilidade no manifest e estabilidade de diff.
  HTML resources com `timecreated=None` → campo vazio (degrada honesto).

### C2 — Captura da chave de turma na fonte

- `parse_moodle_course` (moodle.py:32): capturar `turma` (ex.: "031") do "Turma NNN" já
  localizado por `m_turma`. Robusto a "Turmas 010 - 011 - 012" (multi-turma no fullname →
  guardar a string inteira; não quebrar).
- `SubjectProfile` (src/models/core.py:206): adicionar `turma: str = ""` e
  `schedule_url: str = ""` (a URL do SARC `Export.aspx`, hoje descartada após o import —
  dialogs.py:1168 usa transitoriamente).
- Import dialog do SARC (src/ui/dialogs.py:1168, `HTMLImportDialog`): ao importar com
  sucesso, persistir a URL em `profile.schedule_url`. Helper **puro** novo (ex.:
  `parse_sarc_turma_key(url) -> {"guid","ano","sem"}`) extraindo `id`/`ano`/`sem` da query.
- `import_moodle_courses` (moodle.py:342): setar `sp.turma` a partir do curso parseado.
- Chave de turma é **registro** (perfil + meta do manifest). Nenhuma lógica de atribuição
  consome ela neste spec.

### C3 — Migrador aditivo (orquestrador fino, anti-duplicação)

- **Refactor DRY com split de responsabilidade:** fatorar o backfill in-place de
  `import_moodle_courses` (moodle.py:392–454) em DUAS funções:
  - `backfill_repo_signals_additive(repo_root, contents, info)` — **não muda atribuição**:
    `moodle_label` (fill-if-empty), `lessons_index` (regrava `.lessons_index.json`),
    `posting_date` (C1), turma (C2).
  - `backfill_repo_signals_consumed(repo_root, contents, info)` — **muda atribuição**:
    `source_section` (overwrite — moodle.py:399) + `derive_card_block_map`/`assign_due`
    (regrava `.card_block_map.json`). Usada só pelo S0b e pelo import normal.
  - `import_moodle_courses` chama as DUAS (comportamento atual preservado). O migrador do S0
    chama **só a additive**.
- `scripts/migrate_signals.py <repo_root> --course <id> [--write]`: padrão de
  `scripts/moodle_backfill_sections.py` (dry-run default, backup `.apibak`, `--write`).
  Idempotente (re-run = no-op). Roda **só** `backfill_repo_signals_additive`. Reporta o que
  mudaria por campo.

### C4 — Probe empírico do `posting_date`

- `scripts/posting_date_probe.py <repo_root> --course <id>` (read-only, sem `--write`):
  por curso, computa o **cluster de início-de-semestre** (moda/mês dominante de
  `timemodified`), a **fração off-batch** (materiais com data fora do cluster = sinal
  informativo), e a contagem **stale** (ano < ano do semestre). Imprime tabela.
- Reusa `MoodleClient.get_course_contents` + `load_block_period_map` (de
  `scripts/eval_ground_truth.py`) p/ comparar `timemodified` ao período do bloco atribuído
  (quando o repo tem timeline). Objetivo: quantificar, por cadeira, quanto A2 ganharia.

### C5 — Gold cross-curso + eval-gate

- Gerar templates full file→bloco: `python scripts/make_ground_truth_template.py <repo>
  <out.csv>` para ES2/IA/SO (e re-confirmar MF). `true_block_id` vem pré-preenchido com a
  predição → usuário corrige só os errados. (Gold = verdade; independe da predição atual,
  logo NÃO depende do S0b ter rodado.)
- Persistir os golds rotulados em `tests/fixtures/eval/ground_truth_<curso>.json` (formato
  consumido por `scripts/eval_ground_truth.py`).
- Wire de gate de regressão cross-curso: teste espelhando
  `tests/test_eval_code_block_gold.py`, com baseline (accuracy + `confident_wrong`) por
  curso travado no fixture. Sobe exit≠0 em regressão.
- Métrica autoritativa: `confident_wrong` (band alta + bloco errado) ≤ baseline E accuracy
  ≥ baseline, **por curso**.

### S0b — Refresh de sinais já-consumidos (passo separado, eval-gated)

Fora do S0 inerte. Aplica `backfill_repo_signals_consumed` (source_section overwrite +
card_block_map/assign_due regen) aos repos antigos. **Muda atribuição** → tratado como
melhoria medida, não como inerte:
- `scripts/migrate_signals.py ... --refresh-consumed` (ou flag dedicada), dry-run default.
- **Gate de pré-condição:** só roda com `.timeline_index.json` fresco (resolve FLAW 3 — não
  regenerar card_block_map sobre blocos stale; reprocessar o timeline antes se necessário).
- **Eval-gate:** `rebuild_diff` mostra os deltas de unit/kind/bloco → usuário revisa →
  `eval_ground_truth` por curso não regride (accuracy ≥, confident_wrong ≤) → só então
  `--write` (com `.apibak`).
- Pode ser executado por curso, após o gold daquele curso existir (medível).

## Data Flow

```
core_course_get_contents (Moodle API, token mobile)
 └─ iter_section_files → SectionFile{...,timemodified,timecreated}     (C1)
 └─ backfill_repo_signals_additive(repo, contents, info)              (C3, S0 — INERTE)
     ├─ backfill_moodle_label_from_api  → entry.moodle_label (fill-if-empty)  [resolver/OFF]
     ├─ backfill_posting_date_from_api  → entry.posting_date(+_created)        [não consumido]
     ├─ build_lesson_topic_index        → .lessons_index.json                 [não consumido]
     └─ turma key → SubjectProfile.turma/schedule_url + manifest meta         [não consumido]
 └─ manifest.json (campos novos = aditivos; atribuição inalterada → rebuild_diff=0)

 └─ backfill_repo_signals_consumed(repo, contents, info)             (S0b — EVAL-GATED)
     ├─ backfill_source_section_from_api → entry.source_section (overwrite)   [rota card]
     └─ derive_card_block_map/assign_due → .card_block_map.json               [rota card + janela S5]
   (gate: timeline fresco + rebuild_diff revisado + gold não regride)

import_moodle_courses → chama additive + consumed (comportamento atual preservado)
parse_moodle_course(course) → {..., turma}                          (C2)
HTMLImportDialog (SARC) → SubjectProfile.schedule_url               (C2)
posting_date_probe.py → métrica por curso (cluster/off-batch/stale)  (C4)
make_ground_truth_template.py → CSV → label → ground_truth_<curso>.json → eval gate  (C5)
```

## Testing (TDD)

- `SectionFile` carrega `timemodified`/`timecreated`; `iter_section_files` lê os campos do
  payload (fixture com content-file contendo timemodified/timecreated).
- `backfill_posting_date_from_api`: match único, colisão de basename pulada, ISO correto,
  `timecreated=None` → vazio.
- `FileEntry` round-trip: `to_dict`/`from_dict` preserva `posting_date(_created)`.
- `parse_moodle_course`: turma de "Turma 031", "Turmas 010 - 011 - 012", e sem turma.
- `parse_sarc_turma_key`: GUID/ano/sem da URL do `Export.aspx`; URL malformada → vazio.
- **Split DRY:** `backfill_repo_signals_additive` NÃO toca `source_section` nem
  `.card_block_map.json` (teste de não-efeito); `backfill_repo_signals_consumed` reproduz o
  comportamento atual de source_section/card_block_map; `import_moodle_courses` = additive +
  consumed (paridade com o atual).
- Gate cross-curso: teste de baseline por curso (mirror de `test_eval_code_block_gold.py`).

## Verification (end-to-end)

**S0 (inerte):**
1. Suíte: `python -m pytest tests -q` — verde (≥1456, sem regressão).
2. Golden PDF: `python scripts/eval_assignments.py` — 5/5, confiante-errado 0 (inalterado).
3. `python scripts/rebuild_diff.py` — **0 diffs** de unit/kind nos 5 cursos (prova a
   inércia do S0; só campos novos não-consumidos no manifest).
4. Migrador additive dry-run em 1 repo real → confirmar que só toca campos aditivos →
   `--write` (com `.apibak`).
5. Probe nas 5 cadeiras → tabela cluster/off-batch/stale.
6. Gerar + rotular gold de ≥1 cadeira nova (ES2 ou IA) → gate cross-curso passa.
7. Atualizar `docs/Overview-Sistema.html` (AGENTS non-negotiable): marcar `posting_date` e
   chave de turma como CAPTURADOS (não consumidos); §5/§0 sinais.

**S0b (eval-gated, separado):**
8. `--refresh-consumed` dry-run → `rebuild_diff` lista deltas → revisão do usuário →
   `eval_ground_truth` por curso (accuracy ≥ baseline, confident_wrong ≤ baseline) → só
   então `--write`. Pré-condição: `.timeline_index.json` fresco.

## Riscos / Gotchas

- **source_section é overwrite, não fill** (moodle.py:399) → por isso fica no S0b, não no
  S0. `moodle_label` é fill-if-empty (moodle.py:405) → seguro no additive.
- `SectionFile` é `frozen` — adicionar campos com default mantém compat; checar todos os
  construtores posicionais (moodle.py:132).
- `from_dict` de `FileEntry`/`SubjectProfile` filtra por `fields(cls)` → campo novo no
  dataclass basta; manifests antigos sem o campo carregam default (sem crash).
- HTML resources (ex.: IA `index.html`) podem ter `timecreated=None` → tratar como ausente.
- O migrador toca o manifest in-place → SEMPRE `.apibak` + dry-run default.
- S0b depende de `.timeline_index.json` fresco (FLAW 3): 4/5 cursos têm índice stale →
  regenerar card_block_map sobre stale produziria mapa errado. Gate de pré-condição.
- `import_moodle_courses` só backfilla quando `sp.repo_root`/`manifest.json` existem
  (moodle.py:392) — o migrador aceita `<repo_root>` direto (não depende do store).
- Não commitar CSVs de template gerados.

## Roadmap pós-S0 (contexto, fora de escopo)

S0b → A1 → A2 (com guarda auto-calibrante do achado empírico) → A3 → A5 → A4 (cutover) → A6
(só se `confident_wrong` persistir) → A7 (limpeza). Cada um: spec→plano→eval-gate
cross-curso usando o substrato deste S0.

### A7 — Limpeza (DEPOIS do cutover A4, nunca antes)

O funil legado ainda LÊ parte dos artefatos até ser deletado no A4; limpar antes =
regressão silenciosa. Duas frentes, cada uma eval-gated (golden 5/5 + suíte + rebuild_diff
5 cursos):

- **Dead code (no A4 e logo após):** delete do funil legado — `score_entry_against_timeline_block`
  S2/S4 (`block_token_weights`, `TOOL_BOOST/PENALTY/TOOL_TOKENS`),
  `select_probable_period_for_entry`, `_best_instructional_block_fallback`, fallback keyword
  de unidade (~600 linhas, index.py:2205), 3 scorers de unidade duplicados,
  `_derive_unit_specs_from_repo` (latente). Guard test antes de cada deleção.
- **Artefatos de dados em disco:** auditar quem LÊ cada `.json` por curso (load points) →
  marcar morto/vivo/redundante → fundir na raiz. Suspeitas: `tag_profile`×`tag_catalog`;
  sobreposição de mapa data→bloco entre `card_block_map`×`lessons_index`×`timeline_index`;
  curations dispersas. Também: **regravar os `.timeline_index.json` stale** (4/5 cursos,
  drift unit/kind pré-existente). Correção na RAIZ, não por curso.
