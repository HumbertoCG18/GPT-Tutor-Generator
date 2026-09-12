# Drift Map Report — feat/block-stable-id

Generated: 2026-06-20

## Summary Table

| repo | funil stale | funil fresco | drifted | total |
|------|-------------|--------------|---------|-------|
| MF | 7/17 cw5 | 6/17 cw4 | 5 | 60 |
| IA | n/a | n/a | 4 | 50 |
| SO | n/a | n/a | 0 | 36 |
| ES2 | n/a | n/a | 6 | 25 |
| TCC | n/a | n/a | 1 | 39 |

## Per-repo Drift Details

### MF — 5 drifted / 60 total

**Format note:** on-disk `computed_block_id` uses `bloco-NN` format (manifest not yet migrated to uuid)

| entry | bloco stale | bloco fresco | gold | verdict |
|-------|-------------|--------------|------|---------|
| exemplos-zip | bloco-12 | bloco-02 | bloco-16 | nenhum |
| exercicios-conjuntos | bloco-13 | bloco-03 | bloco-13 | REGRESSAO **(REGRESSAO)** |
| logicadehoare2 | bloco-10 | bloco-11 | (sem gold) | — |
| revisao-p1 | bloco-06 | bloco-07 | (sem gold) | — |
| tiposindutivos | bloco-04 | bloco-16 | bloco-13 | nenhum |

### IA — 4 drifted / 50 total

**Format note:** on-disk `computed_block_id` uses `bloco-NN` format (manifest not yet migrated to uuid)

| entry | bloco stale | bloco fresco |
|-------|-------------|--------------|
| aprendizadosupervisionado-arvoresdedecisao-duncan | bloco-04 | bloco-05 |
| inteligencia-artificial-aula-29-aprendizagem-de-maquina-medidas-de-avaliacao | bloco-04 | bloco-05 |
| p1-2024-02-ia | bloco-08 | bloco-02 |
| prova-1-2024-02 | bloco-04 | bloco-05 |

### SO — 0 drifted / 36 total

**Format note:** on-disk `computed_block_id` uses `bloco-NN` format (manifest not yet migrated to uuid)

_No drift — STALE = FRESH for all entries._

### ES2 — 6 drifted / 25 total

**Format note:** on-disk `computed_block_id` uses `bloco-NN` format (manifest not yet migrated to uuid)

| entry | bloco stale | bloco fresco |
|-------|-------------|--------------|
| roteiro1 | bloco-04 | bloco-01 |
| roteiro2 | bloco-04 | bloco-01 |
| roteiro3 | bloco-04 | bloco-01 |
| roteiro5 | bloco-04 | bloco-01 |
| roteiro6 | bloco-04 | bloco-01 |
| roteiro7 | bloco-04 | bloco-01 |

### TCC — 1 drifted / 39 total

**Format note:** on-disk `computed_block_id` uses `bloco-NN` format (manifest not yet migrated to uuid)

| entry | bloco stale | bloco fresco |
|-------|-------------|--------------|
| aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade | bloco-01 | bloco-02 |

## Read-Only Proof

| repo | manifest | ledger | result |
|------|----------|--------|--------|
| MF | unchanged | unchanged | OK |
| IA | unchanged | unchanged | OK |
| SO | unchanged | unchanged | OK |
| ES2 | unchanged | unchanged | OK |
| TCC | unchanged | unchanged | OK |