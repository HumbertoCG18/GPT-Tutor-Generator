# W-AD4 — preflight v4 sem gold (25/09)

Congelamento comum: `d6edda44a2cfb8f578b56ff0666868ac4bfe00b2cb8f035159aa152f91f5d3cd`.
Resultado: **REPROVADO** — interrompido: Falha: worker CRU/capturar saiu 2: {"falha": "Falha: pr\u00e9-execu\u00e7\u00e3o n\u00e3o confere com o congelamento: ['vari\u00e1vel n\u00e3o declarada no ambiente: TESSDATA_PREFIX']", "violacoes": 0}
 

## Condições

- ✅ P0 processo: ambiente declarado, -B, pycache isolado, sys.path
- ✅ P0 comandos git sem erro
- ✅ P0 src/tests idênticos à base pretendida
- ✅ P0 inventário congelado = 350 sem duplicatas
- ✅ P1 inventário de manuais = referência declarada
- ✅ P0 descritor da avaliação sem pendências (blob IDs; gold não aberto)
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
