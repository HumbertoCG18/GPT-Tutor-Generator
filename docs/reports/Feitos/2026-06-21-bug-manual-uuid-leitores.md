# Bug latente: leitores de verdade-humana não casam uuid migrado (Fase 1)

date: 2026-06-21
achado: durante o gate do wire anchor (Stage B). NÃO corrigido no commit da âncora.
escopo: fase própria, eval-gated.

## Sintoma confirmado (IA)
4 materiais pinados à mão pelo humano aparecem **sem período** no dashboard e na coluna
Período do FILE_MAP:

| entry_id | manual_timeline_block_id | computed_block_id | resolve_effective_block |
|----------|--------------------------|-------------------|-------------------------|
| `o-que-é-inteligência-artificial-ia-oracle-brasil` | `43b6f936…` (=bloco-01, válido) | None | **""** |
| `ia-responsável-7c4626` | `43b6f936…` (=bloco-01) | None | **""** |
| `artigo-usando-k-nn-em-texto` | `2fdbf4f5…` (válido) | None | **""** |
| `artigo-usando-agrupamento` | `2fdbf4f5…` (válido) | None | **""** |

O uuid ESTÁ presente nos blocks (`block_uuid`). Mesmo assim `resolve_effective_block` →
`resolve_entry_manual_timeline_block` retorna None → cai no computed (None) → `""`.

## Causa-raiz
Gap da migração uuid da Fase 1: o **escritor** migrou `manual_timeline_block_id` para uuid
(Task 3), mas o **leitor** `resolve_entry_manual_timeline_block` casa por id exato (bloco-NN) +
fallback ordinal "bloco-N" — **não casa uuid**. Verdade-humana gravada, mas invisível na leitura.

Contraste: `resolve_placement` (anchor layer) Tier-1 manual casa `manual in {block_uuid|id}` →
resolve. Por isso o wire, se gravasse temporal p/ manual, surfaciaria as 4 (branco→bloco). Foi o
que delatou o bug — e por isso o produtor ficou **anchor-only** (não conserta de carona).

## AUDIT DA CLASSE — COMPLETO (WO2, 2026-06-21)
Helper único `_block_by_migrated_ref` (uuid-first + fallback bloco-NN, file_map.py) + verdito por leitor:

- [x] `manual_timeline_block_id` — `resolve_entry_manual_timeline_block`: **QUEBRADO → CONSERTADO**
      (roteado pelo helper antes do fallback ordinal).
- [x] gold `true_block_id`/`expected_block_id` — evals (eval_assignments:152, eval_code_block_gold:30,
      eval_ground_truth:48): **uuid-safe** (Task 4 migrou gold pra uuid + canonicaliza predicted;
      compara string uuid, não resolve-to-block).
- [x] `.timeline_curation.json` — `apply_block_curation` (curation.py:125): **uuid-safe**
      (`curation.get(block_uuid) or curation.get(id)`, Task 3). Único leitor de chave de curation.
- [x] `manual_unit_slug` — dialogs/_resolve_backlog_unit_status: **N/A** (slug de unidade, não block-ref).
- [x] `manual_scope_unit_slugs` — valor=slugs de unidade; chave=curation (uuid-first acima): **N/A**.
- [x] `block_identity._has_human_ref`: **N/A** (presença booleana, não resolve).

## ALCANCE REAL — cross-repo, 23 pins (não só os 4 do IA)
Gate `.git/sdd/wo2_crossrepo_gate.py` (read-only, OLD id-only vs NEW uuid-first):
ES2 1 · IA 5 · MF 9 · SO 4 · TCC 4 = **23 verdades-humanas invisíveis** (período em branco) recuperadas.
`outras mudanças: 0` (nenhum bloco-NN/ordinal/não-pinado muda). Gate verde: rebuild_diff baseline
(ES2 0/IA1/MF1/SO0/TCC0), golden 5/5, eval_code funil 7/17 resolver 12/17 cw1, pytest 1620.

## Por que NÃO neste commit
O commit da âncora é UMA fase (seam temporal + flag + IA on). Misturar o fix de leitura-manual
(a) quebra o gate dos 2 movers, (b) funde duas preocupações, (c) precisa do próprio eval-gate
cross-superfície. Logado aqui; intocado no wire.
