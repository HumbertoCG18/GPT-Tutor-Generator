# Remendo dos golds antigos (arquivo→bloco) — 32 fixes mecânicos, hard=0 em 5/5

as-of: 2026-08-12 · item 2 da fila pós-campanha-2 · dossiê: `remendo_golds/remendo_<C>.csv`

## Método

3 tiers de correção; TODOS os 32 remendos saíram no Tier A (mecânico): `true_block_uuid`
do gold VIVO no índice atual → `true_block_id` posicional remapeado pro display id de
hoje. Zero arbitragem humana necessária (Tiers B/C vazios). Aplicados em
`docs/reports/ground_truth_{SO,TCC,IA}.csv`: SO 25 · TCC 6 · IA 1. ES2/MF: 0 drift
posicional.

## Resultado

| Métrica | Antes | Depois |
|---|---|---|
| audit hard (SO/TCC/IA/ES2/MF) | 13/0/1/0/0 | **0/0/0/0/0** |
| suspeitas SO | 32 | 19 (só ZERO_OVERLAP/ADMIN_TRUE — sinal fraco, não drift) |
| fase2/4/5 · suite | PASS · 1930/0/4 | PASS · 1930/0/4 (inalterados) |
| eval MF | 50/57=87.7 | 50/57=87.7 (drift MF é SEMÂNTICO — ver pendência) |
| eval SO | (nunca medido honesto) | **17/38 = 44.7% — BASELINE HONESTO novo** |

## Leituras

1. **SO 44.7% é achado, não regressão**: o gold antigo apontava blocos que não existiam
   mais (hard=13 mascarava); remendado, a régua mede de verdade — e o motor no SO é
   fraco em materiais "Lâminas" (19 ZERO_OVERLAP: título curto, sem md). É O insumo
   pro cutover/campanha 3 julgar o motor novo no SO.
2. **Pendência [USER] restante (arbitragem opcional, sem urgência)**: ~102 suspeitas
   soft nos 5 cursos (sinal fraco material×bloco, rótulo pode estar certo) + 7 drifts
   SEMÂNTICOS do MF (datas de entrega remarcadas; eval 87.7 documenta) — re-decisão de
   conteúdo, caso a caso, com os CSVs do dossiê como material.
3. uuid no gold provou o valor (lição 2026-07-08 do tracker): keying por uuid tornou o
   remendo 100% mecânico onde o bloco sobreviveu.
