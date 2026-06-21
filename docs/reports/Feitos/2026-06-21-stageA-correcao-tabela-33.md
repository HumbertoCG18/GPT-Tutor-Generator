# Stage A corrigido (Opção A) + tabela dos 33 anchors — para revisão

date: 2026-06-21
plano-fonte: `.git/sdd/wire-stageA-plan.md` (rev2)
canário: `.git/sdd/ia_canary_table33.py` (read-only, manifest vivo)

> **Atualização Stage B (implementado, gate verde, aguarda OK p/ commit):** decidido
> **anchor-only** (produtor grava temporal só p/ method=anchor). Gate flag-ON IA = exatamente
> **2 movers**. Os 5 manual ficam no fallback inalterado. Achado: 4/5 manual estão HOJE em
> branco por bug latente uuid da Fase 1 — ver `2026-06-21-bug-manual-uuid-leitores.md` (fase
> própria, não tocada no commit da âncora).

## As 4 correções aplicadas

1. **Opção A no corpo do plano (§2/§3/§5/§6):** campo aditivo `temporal_block_id`, escrito
   flag-gated (method anchor; manual redundante-mas-ok). `computed_block_id` **nunca tocado** →
   "KB inalterado" do §5 agora bate com o mecanismo. A cópia em `.git/sdd/` PRECISAVA da correção
   (a rev1 escrevia computed_block_id — re-conflacionava temporal+KB).
2. **1 helper `resolve_temporal_block(entry, blocks)`** — T1/T3/T4/T5/T6 chamam. T2 e
   `_entry_block_source` NÃO (leem `.source`/manual-ness, ortogonal). `resolve_effective_block`
   (KB) intocado. **Correção do helper que você ditou:** fallback = `resolve_effective_block`,
   não `computed_block_id` cru (senão flag-OFF perde o honra-manual → quebra byte-idêntico).
3. **Tabela completa dos 33** abaixo.
4. **`year` determinístico** = ano modal das datas de sessão dos blocos = **2026** (`{2026: 40}`),
   não chute. Função `_course_year_from_blocks`. Limitação ano-cruzado documentada (degrada seguro).

## ACHADO que muda o gate: 2 movers reais, não 33

`computed_block_id` do IA está em legacy `bloco-NN` (nunca reprocessado pós-Fase-1). O "33
changed=True" anterior era artefato de comparar uuid (anchor) × string `bloco-NN` (scorer).
Normalizado pra display: **só 2 dos 33 mudam de bloco**. Os 31 confirmam o scorer (ganham só
proveniência `method=anchor`). KB byte-idêntico nos 50.

**Os 2 movers (correção legítima):** Semana 9, agrupamento hierárquico. Scorer → bloco-07
(sessão única 29/04 "dúvidas para t1"). Âncora → bloco-06 (aula real de hierárquico 27/04).

## Tabela dos 33 anchors (scorer-hoje → anchor, display bloco-NN)

| # | entry_id | scorer | → anchor | mudou | semana |
|---|----------|--------|----------|-------|--------|
| 1 | ag-feito-em-aula-pelo-luca | bloco-13 | bloco-13 | não | S13 |
| 2 | agrupamento-usando-k-means-exemplo-1-ipynb | bloco-06 | bloco-06 | não | S8 |
| 3 | agrupamento-usando-k-means-exemplo-2-ipynb | bloco-06 | bloco-06 | não | S8 |
| 4 | algoritmo-de-classificacao-k-nn | bloco-04 | bloco-04 | não | S3 |
| 5 | algoritmo-dijkstra | bloco-15 | bloco-15 | não | S14 |
| 6 | analise-exploratoria-dos-dados-exemplo-2 | bloco-04 | bloco-04 | não | S3 |
| 7 | aprendizadonaosupervisionado-agrupamento-particional (S8) | bloco-06 | bloco-06 | não | S8 |
| 8 | **aprendizadonaosupervisionado-agrupamento-particional (S9)** | **bloco-07** | **bloco-06** | **SIM** | **S9** |
| 9 | aprendizadosupervisionado-classificacao-knn | bloco-04 | bloco-04 | não | S3 |
| 10 | arvores-de-decisao | bloco-05 | bloco-05 | não | S7 |
| 11 | aula-sobre-agrupamento-parte-1-particional | bloco-06 | bloco-06 | não | S8 |
| 12 | **aula-sobre-agrupamento-parte-2-hierarquico** | **bloco-07** | **bloco-06** | **SIM** | **S9** |
| 13 | aula01-introducao-ia | bloco-01 | bloco-01 | não | S1 |
| 14 | como-analisar-resultados-acc-pr-re-e-f1 | bloco-05 | bloco-05 | não | S6 |
| 15 | como-analisar-resultados-sse-comcorrecoes | bloco-05 | bloco-05 | não | S6 |
| 16 | exemplo-de-programa-com-k-nn-em-java | bloco-04 | bloco-04 | não | S3 |
| 17 | hill-climbing-e-simulated-annealing | bloco-15 | bloco-15 | não | S14 |
| 18 | implementacaominimax | bloco-15 | bloco-15 | não | S15 |
| 19 | introducao-a-redes-neurais | bloco-05 | bloco-05 | não | S4 |
| 20 | introducaoredesneurais-2023-02 | bloco-05 | bloco-05 | não | S4 |
| 21 | lista-de-exercicios-i | bloco-15 | bloco-15 | não | S15 |
| 22 | lista1 | bloco-15 | bloco-15 | não | S15 |
| 23 | minimax | bloco-15 | bloco-15 | não | S15 |
| 24 | minimax-teoria | bloco-15 | bloco-15 | não | S15 |
| 25 | mlp | bloco-05 | bloco-05 | não | S5 |
| 26 | mlp-novaversao | bloco-05 | bloco-05 | não | S5 |
| 27 | perceptron-equacaodereta | bloco-05 | bloco-05 | não | S5 |
| 28 | programas-exemplo-hc-sa-versao-para-nrainhas | bloco-15 | bloco-15 | não | S14 |
| 29 | rede-perceptron | bloco-05 | bloco-05 | não | S4 |
| 30 | rede-perceptron-e-equacao-de-reta | bloco-05 | bloco-05 | não | S5 |
| 31 | redesperceptron2023-02 | bloco-05 | bloco-05 | não | S4 |
| 32 | survey-on-clustering | bloco-06 | bloco-06 | não | S8 |
| 33 | visao-geral-introducao-e-historico | bloco-01 | bloco-01 | não | S1 |

Destino: bloco-01×2 · bloco-04×4 · bloco-05×11 · bloco-06×7 · bloco-13×1 · bloco-15×8.

## Ponto de decisão pra você
A tabela tem 2 suspeitos pra olhar: **#5 algoritmo-dijkstra** e **#28 programas-hc-sa** caem em
**bloco-15** pela Semana **14** (01–05/06), enquanto minimax (#18,23,24) cai em bloco-15 pela
Semana **15** (08–12/06). bloco-15 absorve 2 semanas (busca + minimax) — confere se é over-merge
de bloco ou se está certo. O resto bate com a intuição (perceptron/MLP→05, k-NN→04, k-means→06).
