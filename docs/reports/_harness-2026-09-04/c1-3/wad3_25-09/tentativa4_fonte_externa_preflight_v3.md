# W-AD3 — preflight v3 sem gold (25/09)

Congelamento comum: `f975f9a2927f814303556cddc482b3c8b719bde2f910d9ec18e3849d39c53057`.
Resultado: **REPROVADO** — interrompido: Falha: worker CRU/capturar saiu 2: {"falha": "Violacao: acesso fora da lista permitida", "violacoes": 1}
 

## Condições

- ✅ P0 comandos git sem erro
- ✅ P0 src/tests idênticos à base pretendida
- ✅ P0 inventário congelado = 350 sem duplicatas
- ✅ P1 inventário de manuais = referência declarada
- ✅ P2 A (sem sidecar == congelada) nos 7
- ✅ P2 delta não vazio nos braços históricos
- ✅ P2 B: diferenças só de ordem de aliases (inspeção integral)
- ✅ principal sem violações

## P2 por curso

| curso | A | B ATUAL só ordem | B LLM só ordem | +LLM | +ATUAL |
|---|---|---|---|---:|---:|
| MF | True | True | True | 80 | 80 |
| SO | True | True | True | 98 | 107 |
| IA | True | True | True | 79 | 100 |
| ES2 | True | True | True | 58 | 80 |
| TCC | True | True | True | 96 | 103 |
| CG | True | True | True | 80 | 85 |
| FR | True | True | True | 55 | 55 |
