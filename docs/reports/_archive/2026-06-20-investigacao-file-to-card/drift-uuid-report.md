# Drift UUID Re-confirmation — feat/block-stable-id

Generated: 2026-06-20

## Method

- **Stale side**: on-disk `computed_block_id` is `bloco-NN`. Resolved to UUID via ledger `display_id_last`.
- **Fresh side**: fresh scorer (persist=False) returns UUID directly.
- **Compare**: stale_uuid == fresh_uuid → renumber (DISAPPEARS). stale_uuid != fresh_uuid → real reassignment (SURVIVES).
- **Stale resolution source**: `course/.block_identity.json` (`display_id_last`). `course/.timeline_index.json` has no `block_uuid` field (only `bloco-NN` ids), so cannot improve over ledger.

## Caveat — stale resolution reliability

| repo | rebuild_diff blocks_changed | stale→uuid via ledger |
|------|----------------------------|-----------------------|
| MF   | 1 block changed            | **FLAG**: 1 block moved, stale bloco-NN resolution may be off for that block |
| IA   | 1 block changed            | **FLAG**: same caveat |
| SO   | 0                          | Safe |
| ES2  | 0                          | Safe |
| TCC  | 0                          | Safe |

## MF

| entry | stale bloco | stale→uuid (disp) | fresh uuid (disp) | survives? | gold uuid (disp) | fresh==gold |
|-------|-------------|-------------------|-------------------|-----------|-----------------|-------------|
| exemplos-zip | bloco-12 | e3bc8a61... (bloco-12) | 1e73625a... (bloco-02) | YES — real reassignment | a6ac04f2... (bloco-16) | False |
| exercicios-conjuntos | bloco-13 | de7d1b70... (bloco-13) | 2edd762f... (bloco-03) | YES — real reassignment | de7d1b70... (bloco-13) | False |
| logicadehoare2 | bloco-10 | 171a1a09... (bloco-10) | c9f5f7cf... (bloco-11) | YES — real reassignment | (no gold) | — |
| revisao-p1 | bloco-06 | 5599d015... (bloco-06) | 1dd6f143... (bloco-07) | YES — real reassignment | (no gold) | — |
| tiposindutivos | bloco-04 | 7ccdaf5e... (bloco-04) | a6ac04f2... (bloco-16) | YES — real reassignment | de7d1b70... (bloco-13) | False |

## IA

| entry | stale bloco | stale→uuid (disp) | fresh uuid (disp) | survives? |
|-------|-------------|-------------------|-------------------|-----------|
| aprendizadosupervisionado-arvoresdedecisao-duncan | bloco-04 | af22fe17... (bloco-04) | 2fdbf4f5... (bloco-05) | YES — real reassignment |
| inteligencia-artificial-aula-29-aprendizagem-de-maquina-medidas-de-avaliacao | bloco-04 | af22fe17... (bloco-04) | 2fdbf4f5... (bloco-05) | YES — real reassignment |
| p1-2024-02-ia | bloco-08 | 5256ec08... (bloco-08) | 55691241... (bloco-02) | YES — real reassignment |
| prova-1-2024-02 | bloco-04 | af22fe17... (bloco-04) | 2fdbf4f5... (bloco-05) | YES — real reassignment |

## SO

_No drifts to resolve._

## ES2

| entry | stale bloco | stale→uuid (disp) | fresh uuid (disp) | survives? |
|-------|-------------|-------------------|-------------------|-----------|
| roteiro1 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |
| roteiro2 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |
| roteiro3 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |
| roteiro5 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |
| roteiro6 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |
| roteiro7 | bloco-04 | 8a2e86f0... (bloco-04) | c47823dc... (bloco-01) | YES — real reassignment |

## TCC

| entry | stale bloco | stale→uuid (disp) | fresh uuid (disp) | survives? |
|-------|-------------|-------------------|-------------------|-----------|
| aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade | bloco-01 | 667491f1... (bloco-01) | 18a1092a... (bloco-02) | YES — real reassignment |

## Specific Confirmations

### 1. MF `exercicios-conjuntos`: fresh uuid vs gold uuid

- Gold `true_block_id`: `de7d1b70-fb58-4a18-ad49-d1a64c6c7684` (display: bloco-13)
- Fresh computed uuid: `2edd762f-2dc8-4437-90c7-c207b796434a` (display: bloco-03)
- Stale uuid: `de7d1b70-fb58-4a18-ad49-d1a64c6c7684` (display: bloco-13)
- **fresh == gold? False** → regression is REAL in uuid space (renumber-proof)
- Stale was correct (stale==gold): True

### 2. ES2 `roteiro1..7` (bloco-04→bloco-01): real reassignment or renumber?

- Stale `bloco-04` → uuid `8a2e86f0-fb4a-4487-86ec-07e74c73d88a` (display: bloco-04)
- Fresh uuid for all 6 roteiros: `c47823dc-111f-4854-b46e-08acb7063909` (display: bloco-01)
- **UUIDs different? True** → REAL REASSIGNMENT — survives in uuid space

All 6 entries:
  - roteiro1: stale=8a2e86f0 fresh=c47823dc survives=True
  - roteiro2: stale=8a2e86f0 fresh=c47823dc survives=True
  - roteiro3: stale=8a2e86f0 fresh=c47823dc survives=True
  - roteiro5: stale=8a2e86f0 fresh=c47823dc survives=True
  - roteiro6: stale=8a2e86f0 fresh=c47823dc survives=True
  - roteiro7: stale=8a2e86f0 fresh=c47823dc survives=True

## Read-Only Proof

| repo | manifest | ledger | result |
|------|----------|--------|--------|
| MF | unchanged | unchanged | OK |
| IA | unchanged | unchanged | OK |
| SO | unchanged | unchanged | OK |
| ES2 | unchanged | unchanged | OK |
| TCC | unchanged | unchanged | OK |

_All repos clean. persist=False gate held. No file written in any tutor repo._