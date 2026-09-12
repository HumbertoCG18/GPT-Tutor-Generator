# Baseline congelado — pré Fase 1 (identidade estável de bloco)

date: 2026-06-20
branch: `feat/block-stable-id`
base: `8fb4bd2` (pós-degrau-3a)
proposito: ORÁCULO DE REGRESSÃO da Fase 1 (uuid). Estado dos 5 repos ANTES de
qualquer mudança. Read-only — nenhum comportamento alterado nesta captura.
Spec: `docs/superpowers/specs/2026-06-20-block-stable-id-design.md`.

## 1. eval_assignments (golden PDF sintético) — INVARIANTE SAGRADO
```
Acuracia de bloco: 5/5 (100.0%)   orfaos: 0
Confiante e ERRADO (band alta, bloco errado): 0
band alta 2 ok / 0 erro | media 1 ok / 0 erro | baixa 2 ok / 0 erro
```
**Portão:** 5/5 cw0. Pós-Fase-1 tem que dar IGUAL (T6 prova que migrar gold+eval
pra uuid é não-comportamental).

## 2. eval_code_block_gold (MF, `tests/fixtures/eval/code_block_gold.json`)
```
funil:    acc 7/17 (41%), confiante-errado 5
resolver: acc 12/17 (70%), confiante-errado 1
subset alta:  funil 7/14 (50%)  resolver 11/14 (78%)
subset media: funil 0/3 (0%)   resolver 1/3 (33%)
baseline travado: resolver_acc >= 70.6%, confiante-errado <= 1
```
Único cw do resolver = `hoare` (dá bloco-11, gold bloco-10; blocos adjacentes).
**Todos os `true_block_id` aqui estão em `bloco-NN`** → confirma a camada de
medição (§3.9): ao migrar `computed_block_id`→uuid, este gold tem que migrar junto
ou a igualdade `predicted==true` quebra.

## 3. rebuild_diff (5 cursos) — ESTADO REAL ATUAL
```
ES2 (14 blocos):  0 mudaram
IA  (25 blocos):  1 mudou  — bloco-03 unit unidade-de-aprendiza->- | kind class->overview (Introducao)
MF  (21 blocos):  1 mudou  — bloco-10 unit unidade-01->unidade-02 | kind class->class (Logica de Hoare)
SO  (21 blocos):  0 mudaram
TCC (31 blocos):  0 mudaram
```
**Baseline real congelado: ES2 0 / IA 1 / MF 1 / SO 0 / TCC 0.**

### ⚠️ Discrepância vs o número lembrado (7/20/13/1/0)
O baseline histórico documentado era `ES2 7 / IA 20 / SO 13 / MF 1 / TCC 0`. Esse
era o drift PRÉ-resync. O `migrate --write` (S0) + reprocess já baixaram pra
`ES2 0/IA1/MF1/SO0/TCC0` (o ledger do degrau 3a Task 2 já registrava esse set).
É exatamente por isso que PASSO 0 mede o estado REAL em vez de confiar no número
lembrado. **O portão da Fase 1 = "sem drift NOVO vs ES2 0/IA1/MF1/SO0/TCC0"**, não
vs 7/20/13/1/0. Os 2 deltas restantes (IA bloco-03, MF bloco-10) são dívida
pré-existente, não regressão da Fase 1.

## Como o portão usa este baseline
Pós-impl da Fase 1, re-rodar os 3 e comparar:
- eval_assignments == 5/5 cw0 (idêntico) ← T6.
- eval_code_block_gold: resolver_acc >= 70.6%, cw <= 1 (idêntico).
- rebuild_diff: sem delta NOVO vs ES2 0/IA1/MF1/SO0/TCC0.
Qualquer regressão = REVERT, nunca calibração.
