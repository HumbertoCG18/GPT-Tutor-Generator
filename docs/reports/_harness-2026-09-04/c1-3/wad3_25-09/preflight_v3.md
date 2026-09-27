# W-AD3 — preflight v3 sem gold (25/09)

Congelamento comum: `05dc9cf1e3f35c09c79104fb1cfc953c8ee49660e56c045679ca4200366ad8f7`.
Resultado: **APROVADO**

## Condições

- ✅ P0 comandos git sem erro
- ✅ P0 src/tests idênticos à base pretendida
- ✅ P0 inventário congelado = 350 sem duplicatas
- ✅ P1 inventário de manuais = referência declarada
- ✅ P2 A (sem sidecar == congelada) nos 7
- ✅ P2 delta não vazio nos braços históricos
- ✅ P2 B: diferenças só de ordem de aliases (inspeção integral)
- ✅ P4 CRU = referência por ID (conjuntos completos)
- ✅ P3 C: identidade == VOCAB_LLM (taxonomia ordenada e índice)
- ✅ P3 CTRL_MAIOR: pares, estrutura e remoções
- ✅ P3 aleatórios: pares, contagem, multiconjunto, multiplicidade, sem duplicata/remoção
- ✅ P3 nenhum aleatório bloqueado por orçamento
- ✅ P5 manual efetivamente carregado = mapa esperado
- ✅ P5 artefatos temporais idênticos entre braços
- ✅ P5 braços não-CRU não leem a taxonomia congelada
- ✅ P5 unidades do motor iguais entre braços
- ✅ P5 taxonomia e índice = snapshots congelados
- ✅ P5 entradas comuns iguais antes/depois
- ✅ P5 entradas externas iguais antes/depois
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

## P3 por curso

| curso | C taxonomia | C índice | MAIOR | ALEAT 1/2/3 | estados das unidades (3 sementes) |
|---|---|---|---|---|---|
| MF | True | True | True | True/True/True | {'pareado': 9} |
| SO | True | True | True | True/True/True | {'pareado': 15} |
| IA | True | True | True | True/True/True | {'pareado': 9, 'estruturalmente_nao_informativa': 3} |
| ES2 | True | True | True | True/True/True | {'pareado': 6} |
| TCC | True | True | True | True/True/True | {'pareado': 12} |
| CG | True | True | True | True/True/True | {'estruturalmente_nao_informativa': 3, 'pareado': 12} |
| FR | True | True | True | True/True/True | {'pareado': 6} |

## P4

- CRU (nova): problemas de estrutura 0, divergências 0, chamados 341, não chamados por motivo {'nao_identificado': 9}.
