# Regression Diagnosis — Block Attribution
Date: 2026-06-20

## Read-only Verification
All three repos had only pre-existing untracked/modified files before and after this session.
No source file was written. Scratch path is `.git/sdd/` (git-ignored).

---

## MF / exercicios-conjuntos

### Entry fields (from manifest.json)
- `id`: `exercicios-conjuntos`
- `category`: `codigo-professor`
- `source_path`: `.../Verificação de Programas/exercicios_conjuntos.zip`
- `source_section`: **ABSENT** (field not present in entry)
- `moodle_label`: `Respostas`
- `posting_date`: `2026-06-08`
- `manual_timeline_block_id`: `""` (empty)
- `computed_block_id`: `bloco-13`
- `computed_block_method`: `llm_only`
- `computed_block_confidence`: `0.6`
- `computed_block_band`: `alta`
- `computed_unit_slug`: `unidade-01-metodos-formais`
- `auto_tags`: `["tipo:codigo", "unit:unidade-01-metodos-formais", "bloco:bloco-03"]`
- `unit_match_reasons`: `["winner_score=1.79", "topic_score=0.60", "tag_boost=1.50", "herdada_do_bloco=bloco-03"]`

### Block period data
| Block    | UUID prefix | period_start | period_end | unit                              | topic_tokens                                                                    |
|----------|-------------|--------------|------------|-----------------------------------|---------------------------------------------------------------------------------|
| bloco-03 | 2edd762f    | 2026-03-09   | 2026-03-09 | unidade-01-metodos-formais        | logica, predicados                                                              |
| bloco-13 | de7d1b70    | 2026-05-13   | 2026-05-25 | unidade-02-verificacao-de-programas | arrays, colecoes, conjuntos, dafny, logica, programas, sequencias             |

### .card_block_map.json — key lookup result
The card map has 8 section-level keys. The entry's `source_section` field is **absent**.
The lookup in `lookup_card_blocks()` uses `norm_ascii_lower(entry.get("source_section"))`.
Since `source_section` is missing → lookup key = `""` → **no hit** in card map.

Had `source_section` been present as `"Verificação de Programas"`, the card map entry
`"Verificação de Programas" -> block_ids: ['bloco-10','bloco-11','bloco-12','bloco-13','bloco-14','bloco-15']`
would have been found, narrowing candidates to those 6 blocks and making bloco-13 the correct winner.

### Root cause — Question 4 answer
**Specific lever: `computed_block_method = "llm_only"` — this entry was attributed by the legacy LLM pathway, not the current funnel.**

The funnel (card → card+scorer → scorer_only) was bypassed entirely. The legacy LLM path ran independently and wrote `computed_block_id = "bloco-13"` (correct!), but the `auto_tags` reflect an older run where `bloco:bloco-03` was written — possibly from a prior scorer_only run or a unit-inheritance cascade. The `unit_match_reasons` field contains `herdada_do_bloco=bloco-03`, confirming the unit `unidade-01-metodos-formais` was *inherited from bloco-03*, not resolved independently.

**Regression summary:**
- The `auto_tag bloco:bloco-03` is stale — from a prior pipeline run
- The `computed_block_id = bloco-13` is the LLM's answer (correct block by content)
- The `source_section` field is absent, which means the card_block_map funnel stage produces zero hits
- The funnel stage that *would* have been authoritative (card lookup on `"Verificação de Programas"`) was bypassed because `source_section` is not populated for this zip-type entry
- The winning signal was NOT a date-in-range match, NOT a lexical overlap on card topics, NOT a unit-title match — it was raw `llm_only` attribution
- The bloco-03 in auto_tags is a **stale tag from a previous run** that was never cleared when the llm_only path ran and wrote bloco-13 to `computed_block_id`

**Why bloco-03 appeared:** The scorer (when it ran previously) found `unidade-01-metodos-formais` for this entry. bloco-03 belongs to that unit. The unit→block inheritance (`herdada_do_bloco=bloco-03`) then wrote `bloco:bloco-03` into auto_tags. The LLM later overwrote `computed_block_id` to `bloco-13` (which belongs to `unidade-02-verificacao-de-programas` — the correct unit for Verificação de Programas material), creating a cross-unit conflict that shows as a mismatch between `computed_block_id` and `auto_tags`.

---

## ES2 / roteiro1..roteiro7

### Entry survey
| ID                          | computed_block_id | computed_block_method | source_section  |
|-----------------------------|-------------------|-----------------------|-----------------|
| roteiro1-introducao         | bloco-02          | card+scorer           | Microsserviços  |
| roteiro2-nameserver         | bloco-04          | card+scorer           | Microsserviços  |
| roteiro1                    | bloco-04          | llm_only              | Microsserviços  |
| roteiro2                    | bloco-04          | consensus             | Microsserviços  |
| roteiro3                    | bloco-04          | llm_only              | Microsserviços  |
| roteiro4-circuitbreaker     | bloco-07          | card+scorer           | Microsserviços  |
| roteiro5                    | bloco-04          | llm_only              | Microsserviços  |
| roteiro5-conteiners         | bloco-04          | card+scorer           | Microsserviços  |
| roteiro6                    | bloco-04          | consensus             | Microsserviços  |
| roteiro6-conteiners-composicao | bloco-02       | card+scorer           | Microsserviços  |
| roteiro7                    | bloco-04          | llm_only              | Microsserviços  |
| roteiro7-filas              | bloco-07          | card+scorer           | Microsserviços  |
| roteiro7-history-service    | bloco-01          | llm_only              | Microsserviços  |
| roteiro8-autenticacao-autorizacao | bloco-04   | card+scorer           | Microsserviços  |

### Block period data
| Block    | UUID prefix | period_start | period_end | unit                               | primary_topic_label                          |
|----------|-------------|--------------|------------|------------------------------------|----------------------------------------------|
| bloco-01 | c47823dc    | 2026-03-06   | 2026-03-20 | unidade-01-arquitetura-de-software | Disciplina conceitos arquitetura baseada servicos monolitica |
| bloco-04 | 8a2e86f0    | 2026-04-10   | 2026-04-24 | unidade-01-arquitetura-de-software | Microservicos spring discovery gateway       |

### .card_block_map.json
- `"Microsserviços"` → `block_ids: ['bloco-01','bloco-02','bloco-03','bloco-04','bloco-05','bloco-06','bloco-07','bloco-08','bloco-09','bloco-10']`

### Question answers
**Q1 — Which `computed_block_method` won?**
Mixed: `llm_only` for the plain `roteiro[1-7]` zip entries, `card+scorer` or `consensus` for the named entries like `roteiro2-nameserver`, `roteiro4-circuitbreaker`, etc.

**Q2 — What moved the group to bloco-04?**
For the `llm_only` entries (roteiro1..7 plain zips): the LLM independently assigned bloco-04 with confidence `0.5567500000000001` (identical for all 5 entries — likely a batch LLM call with the same response). The card map section `"Microsserviços"` returns 10 blocks — too wide to be a useful signal; the scorer narrows within that set, and the `card+scorer` entries with richer text (like roteiro2-nameserver with spring/gateway content) also converge on bloco-04 because bloco-04's primary_topic is `"Microservicos spring discovery gateway"`.

**Q3 — Same lever as MF?**
**DIFFERENT.** In ES2, the dominant entries (plain roteiro zips) are `llm_only` like MF's exercicios-conjuntos, but the underlying cause differs: ES2 entries DO have `source_section = "Microsserviços"`, so the card map lookup hits (returns 10 blocks). The scorer then runs within those 10 candidates. The `llm_only` entries bypass the scorer entirely and use LLM batch attribution. The problem in ES2 is that `source_section` IS present but the card map returns a 10-block set — too coarse to avoid ambiguity — and the `llm_only` entries bypass the current funnel.

The shared symptom is `llm_only` method bypassing the funnel, but the triggering cause differs:
- MF: `source_section` absent → card map miss → fell to scorer → then LLM overrode
- ES2: `source_section` present → card map hit (10 blocks) → scorer, but plain zips have no text → scorer weak → LLM overrides with uniform 0.5567 confidence

---

## IA / arvoresdedecisao-duncan, aula-29-medidas, prova-1-2024

### Entry survey
| ID                                    | computed_block_id | computed_block_method | source_section          |
|---------------------------------------|-------------------|-----------------------|-------------------------|
| aprendizadosupervisionado-arvoresdedecisao-duncan | bloco-04 | scorer_only      | N/A (absent)            |
| inteligencia-artificial-aula-29-...   | bloco-04          | scorer_only           | N/A (absent)            |
| prova-1-2024-02                       | bloco-04          | scorer_only           | TDE Trabalho Discente Efetivo |

### Block period data
| Block    | UUID prefix | period_start | period_end | unit                                   | primary_topic_label                    |
|----------|-------------|--------------|------------|----------------------------------------|----------------------------------------|
| bloco-04 | af22fe17    | 2026-03-11   | 2026-03-16 | unidade-de-aprendizagem-01-visao-geral-5 | Tipos dados preparacao               |
| bloco-05 | 2fdbf4f5    | 2026-03-18   | 2026-04-15 | unidade-de-aprendizagem-01-visao-geral-5 | Introdução a agentes em ambientes determinísticos |

The block_identity anchor for bloco-05 lists topic_tokens: `abordagem, analise, arvores, decisao, introducao, means, neural, perceptron, rede, resultados, supervisionada`.

### .card_block_map.json (relevant entries)
- `"TDE Trabalho Discente Efetivo"` → `block_ids: []` (empty!)
- `"Semana 4 - 23.03 a 27.03 - Machine Learning Aprendizado Supervisionado"` → `['bloco-05']`
- `"Semana 5 -30.03 a 01.04 ML - Aprendizado Supervisionado"` → `['bloco-05']`

### Question answers
**Q1 — Which `computed_block_method` won?**
`scorer_only` for all three.

**Q2 — What moved them to bloco-04?**
The question premise needs qualification: the manifest shows `bloco-04` (not bloco-05 as expected). The scorer ran without a card map hit (source_section absent or maps to empty block_ids for TDE). The scorer assigned bloco-04 with low confidence (0.11–0.18, band `baixa`). Unit-block conflicts are flagged for two entries (`unit: unidade-de-aprendizagem-05` vs `block_unit: unidade-de-aprendizagem-01`).

For `arvoresdedecisao-duncan`: bloco-05 anchor has `arvores, decisao, supervisionada` which should score higher than bloco-04 (`tipos, dados, preparacao`). The scorer_only result of bloco-04 at very low confidence (0.137) suggests either the scorer's lexical match on bloco-04's `tipos dados preparacao` beat bloco-05, OR the block period-weight favored bloco-04 (earlier period). This is the regression: the scorer produced the wrong block at low confidence.

**Q3 — Same lever as MF?**
**DIFFERENT from MF, but partially similar to ES2 zip case.** The method is `scorer_only` (not `llm_only`), meaning the LLM did NOT run for these entries. The funnel stage is the current scorer. The low confidence (band `baixa`) indicates the scorer is genuinely uncertain. The root cause is that `source_section` is absent or maps to empty, so the card map stage produces no candidates, and the scorer runs over ALL instructional blocks — a wide open search where the wrong block wins by a small margin.

---

## Verdict

**The MF cause is ISOLATED in its specific mechanism, but SHARES a class-level root cause with the other repos.**

### Shared root cause (class-level)
**`source_section` absent or card-map miss → scorer/LLM runs without card-scoped candidate restriction → wrong block wins.**

In all three repos, the regression originates from the card_block_map lookup failing to scope the scorer's candidate set:
- MF: `source_section` field absent → `lookup_card_blocks("")` → no hit → scorer+LLM unscoped
- ES2 (plain zips): `source_section` present (`"Microsserviços"`) but returns 10 blocks (entire course section) → too wide; `llm_only` entries bypass scorer and use LLM batch attribution with identical 0.5567 confidence
- IA: `source_section` absent or maps to `TDE` (empty block_ids) → scorer_only runs over all blocks; wrong block wins at low confidence

### Different levers per repo
| Repo | Method     | Specific lever                                                              |
|------|------------|-----------------------------------------------------------------------------|
| MF   | llm_only   | source_section absent → no card map hit → scorer produced bloco-03 (unit inheritance) → LLM overrode to bloco-13; auto_tags stale (bloco-03 residue from prior run) |
| ES2  | llm_only (zips), card+scorer (PDF/docs) | source_section present but 10-block section too wide; zip entries have no extractable text → LLM batch override with uniform confidence |
| IA   | scorer_only | source_section absent; scorer runs unscoped; bloco-04 beats bloco-05 by thin margin at very low confidence (0.11–0.18) |

### MF-specific additional issue
The MF `exercicios-conjuntos` entry has a **stale `auto_tag bloco:bloco-03`** that disagrees with `computed_block_id = bloco-13`. This is a tag-sync bug: the current funnel writes `computed_block_id` but the `auto_tags[bloco:]` field was last written by a prior run that resolved to bloco-03 (via unit inheritance from `unidade-01-metodos-formais`). The new LLM-only path updated `computed_block_id` without rebuilding `auto_tags`.
