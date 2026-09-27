# Rodada VOCAB_LIMPO — preflight sem gold (26/09)

Congelamento comum: `6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81`.
Resultado: **APROVADO**

## Condições

- ✅ P0 processo: ambiente declarado, -B, pycache isolado, sys.path
- ✅ P0 comandos git sem erro
- ✅ P0 src/tests idênticos à base pretendida
- ✅ P0 inventário congelado = 350 sem duplicatas
- ✅ P1 nenhum manual em nenhum palco (mapa declarado)
- ✅ P0 descritor da avaliação sem pendências (blob IDs; gold não aberto)
- ✅ P2 A (sem sidecar == congelada) nos 7
- ✅ P2 delta não vazio no VOCAB_LIMPO
- ✅ P2 B: diferenças só de ordem de aliases (inspeção integral)
- ✅ P4 CRU = referência por ID (conjuntos completos)
- ✅ P3 C: identidade == VOCAB_LIMPO (taxonomia ordenada e índice)
- ✅ P3 CTRL_MAIOR_LIMPO: pares, estrutura e remoções
- ✅ P3 aleatórios: pares, contagem, multiconjunto, multiplicidade, sem duplicata/remoção
- ✅ P3 nenhum aleatório bloqueado por orçamento
- ✅ P5 manual efetivamente carregado = mapa esperado
- ✅ P5 artefatos temporais idênticos entre braços
- ✅ P5 braços não-CRU não leem a taxonomia congelada
- ✅ P5 unidades do motor iguais entre braços
- ✅ P5 taxonomia e índice = snapshots congelados
- ✅ P5 entradas comuns iguais antes/depois
- ✅ P5 entradas externas iguais antes/depois
- ✅ P5 código do harness, helpers e src/ iguais antes/depois
- ✅ P5 distribuições iguais à assinatura congelada
- ✅ principal sem violações

## P2 por curso

| curso | A | B LIMPO só ordem | +LIMPO | -LIMPO |
|---|---|---|---:|---:|
| MF | True | True | 64 | 0 |
| SO | True | True | 96 | 0 |
| IA | True | True | 80 | 0 |
| ES2 | True | True | 56 | 0 |
| TCC | True | True | 129 | 0 |
| CG | True | True | 103 | 0 |
| FR | True | True | 77 | 0 |

## P3 por curso

| curso | C taxonomia | C índice | MAIOR | ALEAT 1/2/3 | estados das unidades (3 sementes) |
|---|---|---|---|---|---|
| MF | True | True | True | True/True/True | {'pareado': 9} |
| SO | True | True | True | True/True/True | {'pareado': 12, 'estruturalmente_nao_informativa': 3} |
| IA | True | True | True | True/True/True | {'pareado': 6, 'estruturalmente_nao_informativa': 3} |
| ES2 | True | True | True | True/True/True | {'pareado': 6} |
| TCC | True | True | True | True/True/True | {'pareado': 12} |
| CG | True | True | True | True/True/True | {'pareado': 20, 'identidade_sorteada': 1} |
| FR | True | True | True | True/True/True | {'pareado': 6} |

## P4

- CRU_LIMPO (nova): problemas de estrutura 0, divergências 0, chamados 341, não chamados por motivo {'nao_identificado': 9}.

Não chamados do CRU (motivo do harness; `nao_identificado` = sem evidência suficiente para outro motivo):

- CG/cronograma2026-2: nao_identificado; final unidade='unidade-01-introducao-ao-processamento-grafico', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=14.06', 'topic_score=8.94', 'herdada_do_bloco=bloco-01']
- CG/planodeensino-4645z-04-fundamentos-de-computacao-grafica: nao_identificado; final unidade='unidade-01-introducao-ao-processamento-grafico', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=69.40', 'topic_score=9.16', 'ambiguous', 'herdada_do_bloco=bloco-01']
- ES2/plano: nao_identificado; final unidade='unidade-01-arquitetura-de-software', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=83.02', 'topic_score=9.38', 'herdada_do_bloco=bloco-01']
- FR/plano-de-ensino-20262: nao_identificado; final unidade='unidade-01-introducao-a-redes-de-computadores', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=84.39', 'topic_score=9.16', 'herdada_do_bloco=bloco-01']
- MF/plano: nao_identificado; final unidade='unidade-01-metodos-formais', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=107.22', 'topic_score=12.14', 'herdada_do_bloco=bloco-01']
- SO/apresentacao-da-disciplina: nao_identificado; final unidade='unidade-01-introducao-ao-estudo-de-sistemas-operacionais', sub='', motivos_sub=['meta-material:meta-por-conteudo'], motivos_unidade=['winner_score=52.01', 'topic_score=9.38', 'herdada_do_bloco=bloco-01', 'herdada_do_vizinho=bloco-03']
- SO/plano-de-ensino: nao_identificado; final unidade='unidade-01-introducao-ao-estudo-de-sistemas-operacionais', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=52.40', 'topic_score=15.11', 'ambiguous', 'herdada_do_bloco=bloco-01', 'herdada_do_vizinho=bloco-03']
- SO/programa: nao_identificado; final unidade='unidade-01-introducao-ao-estudo-de-sistemas-operacionais', sub='', motivos_sub=['meta-material:meta-por-conteudo'], motivos_unidade=['winner_score=52.40', 'topic_score=15.11', 'ambiguous', 'herdada_do_bloco=bloco-01', 'herdada_do_vizinho=bloco-03']
- TCC/plano-de-ensino: nao_identificado; final unidade='unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas', sub='', motivos_sub=['meta-material:meta'], motivos_unidade=['winner_score=99.03', 'topic_score=17.35', 'herdada_do_bloco=bloco-01']
