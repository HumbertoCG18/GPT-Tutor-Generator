# Anchor Placement — Phase 1 Commit Report

Generated: 2026-06-21

## Status: COMMITTED

## Implementation

### Generic-stem filter added to `src/builder/routing/anchor_placement.py`

New module constant `_GENERIC_STEMS` (frozenset of 8-char prefixes):
```
"introduc", "continua", "exercici", "revisao",
"conteudo", "material", "aplicac", "apresent"
```

`_topic_overlap()` now subtracts generic stems from the shared stem set before counting.
Result: only *meaningful* stem overlap counts toward `_MIN_TOPIC_OVERLAP=1`.

### New test in `tests/test_anchor_placement.py`

`test_generic_stem_only_falls_to_scorer`: section "Introducao a IA e Introducao a ML"
vs block topic "introducao" — overlap is only "introduc" (generic) → method=="scorer".

## Test Results

```
1595 passed in 10.88s
```

6 anchor_placement tests + 1589 existing = zero regressions.

## IA Canary Breakdown (anchor=33, manual=5, scorer=12)

| Method | N |
|--------|---|
| anchor | 33 |
| manual |  5 |
| scorer | 12 |
| TOTAL  | 50 |

### Anchor sub-breakdown

| Stems | Count | Example stems |
|-------|-------|---------------|
| >=2 meaningful stems | 11 | ['algoritm','busca'], ['ensino','plano'], ['agente','busca'] |
|  1 meaningful stem   | 22 | ['supervis'] x16, ['dados'] x6 |
| Total                | 33 | |

**The 22 previously-STRONG 1-stem anchors (supervis/dados) still anchor.**
**The 11 >=2-stem anchors still anchor.**

### The 4 weak entries that now fall to scorer

These 4 were anchoring on "introduc" only (generic). They now go to scorer
for manual pin by user:

| entry_id | source_section |
|----------|----------------|
| `caracteristicasdosdados` | Semana 2 - 09.03 a 13.03 - Introdução a IA (continuação) e Introdução a ML |
| `introducaoml-atualizacao2025` | Semana 2 - 09.03 a 13.03 - Introdução a IA (continuação) e Introdução a ML |
| `caracteristicas-dos-dados` | Semana 2 - 09.03 a 13.03 - Introdução a IA (continuação) e Introdução a ML |
| `introducao-a-ml` | Semana 2 - 09.03 a 13.03 - Introdução a IA (continuação) e Introdução a ML |

Target block: the IA intro block for Semana 2 (week of 09.03-13.03).
These should be manually pinned via `manual_timeline_block_id` in the manifest.

### Existing scorer entries (unchanged from before)

- `aprendizadosupervisionado-arvoresdecisao-duncan` — no source_section
- `inteligencia-artificial-aula-29-...` — no source_section
- `prova-1-2024-02` — TDE admin section
- 5x Semana 12 algo-genético topic mismatch (block has "Introdução a Agentes" sessions)

## Read-Only Proof

- `manifest.json` mtime: UNCHANGED
- `.block_identity.json` mtime: UNCHANGED
- IA git status: CLEAN (canary runs only in memory)

## Files committed

- `src/builder/routing/anchor_placement.py` — generic-stem filter added
- `tests/test_anchor_placement.py` — test 6 (generic-stem falls to scorer)
