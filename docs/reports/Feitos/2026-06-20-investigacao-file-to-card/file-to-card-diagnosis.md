# File-to-Card Attribution Diagnosis
date: 2026-06-21
branch: feat/block-stable-id
author: measurement session (read-only)

---

## CIRCULARITY GATE

**Result: NOT circular. Card_match can be measured independently.**

The `.card_block_map.json` block_ids come from two authoritative sources:
- `source="labels"`: `derive_card_block_map` in `moodle_labels.py` — date-membership
  of Moodle section session dates ∈ block `period_start..period_end`. Pure date-based.
- `source="manual"`: user-manually assigned block_ids (authoritative by inspection, no scorer).

The scorer path (`resolve_card_to_block` token-overlap) is called ONLY by `lookup_card_blocks`
at runtime when a card has NO entry in the persisted map. It does NOT produce the map's content.

---

## MEASUREMENT 1 — Card-level vs Block-level accuracy on MF gold (17 entries)

**Source used for card(block):** `.card_block_map.json` (authoritative, date/manual-based).
Block uuid resolved via `.block_identity.json` slug→uuid map.

| Entry              | Computed slug | Gold uuid (true)                     | BM   | CM   | card_computed                       | card_true                              |
|--------------------|---------------|--------------------------------------|------|------|-------------------------------------|----------------------------------------|
| arvores            | bloco-06      | 7a5e29db (bloco-05)                  | FAIL | OK   | provas por inducao                  | provas por inducao                     |
| exemplos           | bloco-06      | 7ccdaf5e (bloco-04)                  | FAIL | FAIL | provas por inducao                  | especificacoes indutivas e recursivas  |
| intro              | bloco-06      | 7ccdaf5e (bloco-04)                  | FAIL | FAIL | provas por inducao                  | especificacoes indutivas e recursivas  |
| listas             | bloco-06      | 7a5e29db (bloco-05)                  | FAIL | OK   | provas por inducao                  | provas por inducao                     |
| provas             | bloco-05      | 5599d015 (bloco-06)                  | FAIL | OK   | provas por inducao                  | provas por inducao                     |
| t1-2026-1-thy      | bloco-05      | 7ccdaf5e (bloco-04)                  | FAIL | FAIL | provas por inducao                  | especificacoes indutivas e recursivas  |
| introducao-zip     | bloco-12      | e3bc8a61 (bloco-12)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| tiposindutivos     | bloco-04      | de7d1b70 (bloco-13)                  | FAIL | FAIL | especificacoes indutivas e recursivas | verificacao de programas             |
| terminacao         | bloco-11      | e3bc8a61 (bloco-12)                  | FAIL | OK   | verificacao de programas            | verificacao de programas               |
| hoare              | bloco-10      | 171a1a09 (bloco-10)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| invariantes        | bloco-11      | c9f5f7cf (bloco-11)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| colecoes-arrays    | bloco-13      | de7d1b70 (bloco-13)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| colecoes-conjuntos | bloco-13      | de7d1b70 (bloco-13)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| colecoes-sequences | bloco-13      | de7d1b70 (bloco-13)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| exercicios-conjuntos| bloco-13     | de7d1b70 (bloco-13)                  | OK   | OK   | verificacao de programas            | verificacao de programas               |
| classes-parte1     | bloco-16      | 95d7c9fb (bloco-15)                  | FAIL | FAIL | None (bloco-16 not in any card)     | verificacao de programas               |
| exemplos-zip       | bloco-12      | a6ac04f2 (bloco-16)                  | FAIL | FAIL | verificacao de programas            | None (bloco-16 NuSMV not mapped)       |

**block_accuracy = 7/17 (41%)**
**card_accuracy  = 11/17 (65%)**
**block WRONG but card RIGHT = 4**

### Edge cases
- `classes-parte1`: computed=bloco-16 (NuSMV card absent from map); true=bloco-15 (in Verificacao de Programas). card_match FAIL because computed block not in any card.
- `exemplos-zip`: computed=bloco-12 (in Verificacao de Programas); true=bloco-16 (NuSMV, card "Especificacao e Verificacao de Modelos" absent from map). card_match FAIL because true card not in map.

### Verdict
card_accuracy (11/17=65%) >> block_accuracy (7/17=41%). 4 errors are contained within the card boundary.
Reform is worth it for the majority of block errors. However 6/10 block-wrong cases also fail card_match —
these are cross-card errors where file→card alone won't rescue the attribution.

---

## MEASUREMENT 2 — Authoritative card coverage (5 repos)

Definition: a file has an authoritative card if `source_section` is non-empty AND maps to a
`.card_block_map.json` entry with `source in {manual, labels}`.

| Repo | total entries | w/ authoritative card | needs inference | auth% | notes                                     |
|------|--------------|----------------------|-----------------|-------|-------------------------------------------|
| MF   | 57           | 43                   | 14              | 75%   | 12 code entries have empty source_section |
| IA   | 46           | 44                   | 2               | 95%   | near-complete coverage                    |
| SO   | 33           | 0                    | 33              | 0%    | NO .card_block_map.json file              |
| ES2  | 25           | 23                   | 2               | 92%   | near-complete coverage                    |
| TCC  | 38           | 12                   | 26              | 31%   | only 5/14 Moodle sections in card map     |

### Verdict
Mixed: IA (95%) and ES2 (92%) already have near-complete authoritative card coverage — reform premise
holds for them. MF (75%) is partial (code entries pre-date source_section wiring). SO (0%) and
TCC (31%) are blockers — SO has no card map at all, TCC is only partially backfilled. Reform moves
the problem for SO/TCC rather than solving it without further backfill.

---

## SANITY 3 — card.dates granularity

| Repo | dates pattern                                                  |
|------|----------------------------------------------------------------|
| MF   | manual-cards: no dates; labels-cards: 2 session days per card (1 card) or 14 days (Verificacao de Programas spans 7 weeks) |
| IA   | every card = exactly 2 session days (Mon+Wed per week) — session-precision |
| SO   | no card_block_map, cannot assess                               |
| ES2  | mixed: 1 day (TDE), 2 days (Revisao), 13 days (Microservicos spanning 7 weeks) |
| TCC  | manual-only, no dates field — week-name labels only            |

### Pattern
IA: session-precision (each card = exactly 1 week = 2 days). MF/ES2: mixed — some cards span
multiple weeks (multi-topic units). TCC: block-name only, no date granularity. File→card gives
session-precision only for IA; for MF/ES2 the card covers several blocks (coarser than session).

---

## READ-ONLY PROOF

All 5 repos' `manifest.json` and `course/.block_identity.json` mtimes match pre-session timestamps.
This session performed no writes to any of these files.

Git status: none of the 5 repos show manifest.json or .block_identity.json as modified (`M`).
All changes visible in git status are pre-existing (content curated files, .bak files, student state).

**CLEAN. This session wrote nothing to any generated repo.**
