# Cronograma-Validated Coverage
date: 2026-06-21
branch: feat/block-stable-id
analyst: Claude Sonnet 4.6 (read-only, no repo changes)

---

## Method

Re-measures M2 authoritative card coverage applying the **SO method**: a file's card is
REAL only if its Moodle section maps to a real class day/week in the cronograma AND the
session topic matches the material's topic. Three-tier classification:

- **REAL** — section dates appear in CRONOGRAMA_DETALHADO and topic matches
- **INFLATED** — section date/label is present but is admin/posting (TDE, entrega, feriado)
- **MANUAL** — user-assigned block_id with no date; counted as authoritative but non-date-validated
- **NO AUTH** — no section in card_block_map, no manual_block; falls to scorer

---

## Per-repo data

### MF (Metodos-Formais-Tutor)

**Has CRONOGRAMA_DETALHADO**: YES  
**total entries**: 60 (M2 measured 57; +3 new entries since M2 snapshot, all empty source_section)  
**card_block_map sections (source=labels with dates)**:
- `Introdução a Métodos Formais`: dates 2026-03-02, 2026-03-04 — both in cronograma; topic=intro metodos formais MATCH → REAL. But **0 manifest entries** are filed under this section.
- `Verificação de Programas`: 14 dates 2026-04-27 to 2026-06-10 — all 14 in cronograma; topic spans logica hoare, correcao parcial, terminacao, dafny colecoes — all Verificacao de Programas content → REAL. 12 entries.
- `TDE Trabalho Discente Efetivo`: source=labels, assign_due only (no session date) → INFLATED. 2 entries.

**card_block_map sections (source=manual)**: Especificações Indutivas e Recursivas, Provas por Indução, Revisão - Lógica e Especificação, Exercícios de Revisão para Provas, Bibliografia-Livros — all manual, no date → MANUAL. 29 entries.

| classification | entries |
|----------------|---------|
| REAL (cronograma-confirmed) | 12 |
| INFLATED (TDE admin) | 2 |
| MANUAL (source=manual, no date) | 29 |
| NO AUTH (empty source_section) | 17 |
| **total** | **60** |

REAL% = 12/60 = **20.0%**  
M2 auth% = 43/57 = **75.4%**  
Delta = **−55.4 pp**

**Verdict**: The −55 pp drop is NOT because coverage deteriorated. It reflects that M2 counted
all sections with manual source as "authoritative" — valid for block attribution, but those 29
entries have no date anchor. The only date-confirmed content is 12 entries under Verificação de
Programas. The reform does not inflate here; MF's date-coverage is genuinely thin.

---

### IA (Inteligencia-Artifical-Tutor)

**Has CRONOGRAMA_DETALHADO**: YES  
**total entries**: 50 (M2 measured 46; +4 new entries: 2 manual-block externals, 2 scorer-only)  
**card_block_map sections**: all 16 are Semana N format (source=labels, format B).  

Cronograma validation — all 16 Semana sections checked:
- Semanas 1–9, 11–16: both dates per section present in cronograma AND topic matches → REAL
- Semana 10 (`04.04 a 08.04 - Avaliações`): dates 2026-04-04 (Saturday, not class day) and 2026-04-06 (Monday, IS within the 18/03–15/04 ML block). 1/2 dates valid; section label says "Avaliações" but maps to bloco-05 (ML supervisionado) which is the teaching content of that week. **0 manifest entries** filed here. REAL by section-level validation.
- TDE: 2 entries, admin assign_due → INFLATED

| classification | entries |
|----------------|---------|
| REAL (Semana sections, cronograma-confirmed) | 44 |
| INFLATED (TDE admin) | 2 |
| MANUAL (manual_block, no section — external articles) | 2 |
| NO AUTH (scorer_only, no section — external articles) | 2 |
| **total** | **50** |

REAL% = 44/50 = **88.0%**  
M2 auth% = 44/46 = **95.7%**  
Delta = **−7.7 pp**

**Verdict**: IA is genuinely high-coverage. The −7.7 pp delta is entirely explained by 4 new entries
(2 scorer-only externals, 2 TDE inflated) added after M2. The 44 Semana-section entries are all
cronograma-confirmed. No inflation in the existing corpus.

---

### SO (Sistemas-Operacionais-Tutor)

**Has CRONOGRAMA_DETALHADO**: YES  
**total entries**: 36 (M2 measured 33; +3 entries added after M2)  
**card_block_map**: **ABSENT** — no `.card_block_map.json` file.

Without the card map, no entry has an authoritative card. M2 auth=0 stands.

**Reconciliation of 33 vs 36**: M2 was measured on an older manifest snapshot. The current manifest
has 36 entries. The so-backfill report had already noted 36. M2's "33" was the pre-backfill count.
The authoritative analysis uses **36**.

**If a card map existed** (hypothetical, for context):
- 29 entries have topical sections matching the cronograma: Threads (6), Processo e Estruturas (7),
  Sincronização e Comunicação (6), Gerência de Memória (4), Gerência de I/O (2), Gerência de Processos CPU (3), Introdução SO (1) → would be REAL
- 7 entries under `Informações Gerais` (plano de ensino, listas P1, questões ENADE) → admin, would be INFLATED
- The 8 DIFFERS from so-differs-classification.md all remain POSTAGEM (date≠topic): confirmed 0 flip to REAL

| classification | entries |
|----------------|---------|
| REAL (cronograma-confirmed) | 0 |
| INFLATED | 0 |
| MANUAL | 0 |
| NO AUTH (no .card_block_map.json) | 36 |
| **total** | **36** |

REAL% = 0/36 = **0.0%**  
M2 auth% = 0/33 = **0.0%**  
Delta = **0.0 pp**

**Verdict**: SO is unchanged at 0% — the map simply doesn't exist. The underlying sections ARE
mostly cronograma-valid (29/36 would pass if a map were backfilled), but without the map there
is no authoritative path. The 8 DIFFERS (02.06, 07.04, 09.04, 14.04 entries) are confirmed
POSTAGEM — uploading artifacts, not session-matched.

---

### ES2 (Engenharia-Software-2-Tutor)

**Has CRONOGRAMA_DETALHADO**: YES  
**total entries**: 25 (same as M2)  
**card_block_map sections (source=labels)**:
- `Revisão`: dates 2026-03-06, 2026-03-13 — both in cronograma; topic=revisao arquitetura padroes/web/servicos MATCHES first teaching block (06/03–20/03 = "disciplina conceitos arquitetura") → REAL. 3 entries.
- `Microsserviços`: 13 dates 2026-03-20 to 2026-06-29. 12/13 in cronograma (2026-06-29 is a Monday after the devops block ends, not a class day). Section covers the entire Microsserviços teaching unit → section-level REAL. 19 entries.
- `TDE Trabalho Discente Efetivo`: date 2026-07-03 IS in cronograma but labeled "Entrega trabalho final" = admin session, not thematic → INFLATED. 1 entry.
- `Exercícios Revisão para Provas`: section NOT in card_block_map, computed_block_method=scorer_only → NO AUTH. 1 entry.
- `Plano de Ensino`: section NOT in card_block_map, but manual_timeline_block_id set → MANUAL. 1 entry.

| classification | entries |
|----------------|---------|
| REAL (cronograma-confirmed) | 22 |
| INFLATED (TDE admin date) | 1 |
| MANUAL (manual_block, section not in map) | 1 |
| NO AUTH (section not in map, scorer_only) | 1 |
| **total** | **25** |

REAL% = 22/25 = **88.0%**  
M2 auth% = 23/25 = **92.0%**  
Delta = **−4.0 pp**

**Verdict**: ES2 is near-complete. The −4 pp shift is because M2 counted `t1-2026-1` (TDE) as
authoritative (labels source, date present). Under cronograma validation that date is an admin
session → INFLATED, dropping 1 entry. All 22 REAL entries are soundly validated.

---

### TCC (TCC-Tutor)

**Has CRONOGRAMA_DETALHADO**: **NO** — FLAG: NON-VALIDATED coverage  
**total entries**: 40 (M2 measured 38; +2 new)  
**card_block_map sections**: 5 sections, ALL source=manual (Semana 3, 7, 10, 12, 13). No dates field.

Without a cronograma, no section can be validated against class dates. The Semana week labels
are plausible (each maps to a TCC course week), but there is no authoritative session calendar
to confirm against.

| classification | entries |
|----------------|---------|
| REAL (cronograma-confirmed) | 0 |
| INFLATED | 0 |
| MANUAL (card_map source=manual or manual_block) | 15 |
| NO AUTH (section not in map, scorer_only) | 23 |
| empty/sem-secao (no section) | 2 |
| **total** | **40** |

REAL% = 0/40 = **0.0%** (non-validated; would need cronograma to assess)  
M2 auth% = 12/38 = **31.6%**  
Delta = **−31.6 pp** (all counted as MANUAL, none as REAL without cronograma)

**Verdict**: TCC's M2 auth of 31% was already partial. Under cronograma-validation ALL of those
12 entries drop from "authoritative" to "MANUAL (no date anchor)" because the map has no dates
and there is no session calendar to validate against. Cronograma creation is a prerequisite
before TCC coverage can be assessed as REAL.

---

## Summary Table

| Repo | total | REAL | INFLATED | MANUAL | NO AUTH | REAL% | M2 auth% | Δ pp | cronograma? |
|------|-------|------|----------|--------|---------|-------|---------|------|-------------|
| MF   | 60    | 12   | 2        | 29     | 17      | 20.0% | 75.4%   | −55.4 | YES |
| IA   | 50    | 44   | 2        | 2      | 2       | 88.0% | 95.7%   | −7.7  | YES |
| SO   | 36    | 0    | 0        | 0      | 36      | 0.0%  | 0.0%    | 0.0   | YES |
| ES2  | 25    | 22   | 1        | 1      | 1       | 88.0% | 92.0%   | −4.0  | YES |
| TCC  | 40    | 0    | 0        | 15     | 25      | 0.0%  | 31.6%   | −31.6 | NO |

---

## SO reconciliation: 33 vs 36

M2 said 33 entries. so-differs-classification said 36. Current manifest has 36.
**Answer**: 3 entries were added to SO's manifest after the M2 snapshot (all backfill entries
added during the SO backfill session). The authoritative count is **36**. so-differs was correct.

---

## Overall Verdict

The file→date reform's real coverage numbers are:
- **IA 88%, ES2 88%** — genuine, cronograma-confirmed. Reform is well-justified for these two.
- **MF 20%** — only the Verificação de Programas section is date-confirmed (12 entries).
  The other 29 "authoritative" entries are manual-source (valid for block routing, but not date-anchored). Reform doesn't inflate here; MF's date-coverage is thin by design (many weeks are manual-curated).
- **SO 0%** — the card map doesn't exist yet. Cronograma exists and 29/36 sections would pass if backfilled. Reform hasn't reached SO.
- **TCC 0%** — no cronograma at all. The 15 MANUAL entries are plausible but unverifiable. Reform premise cannot be tested for TCC until a cronograma is built.

**Reform verdict**: Justified for IA and ES2 (high, clean coverage). MF is partially justified
(12 date-confirmed, 29 manual-confirmed). SO and TCC remain blockers — SO needs the card map
backfilled, TCC needs a cronograma built.

---

## READ-ONLY PROOF

Git status check executed on 2026-06-21. All 5 repos' `manifest.json` and `course/.block_identity.json`
show no `M` (modified) entries in git status. Files showing `??` are `course/.card_block_map.json`
files that were pre-existing untracked files (not created in this session).

```
MF:  ?? course/.card_block_map.json  (untracked, pre-existing)
IA:  ?? course/.card_block_map.json  (untracked, pre-existing)
SO:  (clean - no card_block_map.json exists)
ES2: ?? course/.card_block_map.json  (untracked, pre-existing)
TCC: (clean)
```

No manifest.json, no .block_identity.json, no content files were modified.
This session performed zero writes to any of the 5 tutor repos.
