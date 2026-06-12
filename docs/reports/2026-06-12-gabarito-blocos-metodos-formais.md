# Gabarito de revisão — blocos × datas × casos do golden (Metodos-Formais)

date: 2026-06-12
fonte: `Metodos-Formais-Tutor/course/.timeline_index.json` +
`tests/fixtures/eval/metodos_formais_golden.json` (golden v1, decisões assistidas)

Como revisar: confira se cada caso está no bloco da AULA em que o material foi
usado. Pra corrigir: edite `expected_block_id` no golden e rode
`python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`.
O gerador preserva tuas mudanças em re-runs (merge por id+categoria).

## Blocos da timeline

| Bloco | Datas | Tópico | Casos do golden apontando pra ele |
|---|---|---|---|
| bloco-01 | 02/03 | Disciplina (apresentação) | — |
| bloco-02 | 04/03 | Sistemas Formais (introdução a MF) | introducao |
| bloco-03 | 09/03 | Lógica predicados (revisão) | exerciciosespecificacao, exerciciosespecificacao-respostas, logicapredicados-semantica, logicapredicados-sintaxe, logicaproposicional-semantica, logicaproposicional-sintaxe, revisao |
| bloco-04 | 11/03 a 25/03 | Especificação de Conjuntos Indutivos | conjuntosindutivos, exerciciosconjuntosindutivos, exerciciosformalizacaoalgoritmosrecursao(+2, +respostas), formalizacaoalgoritmos-recursao(+2) |
| bloco-05 | 30/03 a 01/04 | Indução (listas/árvores) | exercicioscorrecaoinducaomatematica, provasindutivas-especificacoesrecursivas (+arvores, +listas) |
| bloco-06 | 06/04 a 13/04 | Prova interativa de teoremas — Isabelle | arvores, exemplos, intro, listas, provas, revisao-p1-gabarito |
| bloco-07 | 15/04 | Conteúdo u01 (provável P1) | — |
| bloco-08 | 20/04 | Suspensão | — |
| bloco-09 | 22/04 | Conteúdo u01 | — |
| bloco-10 | 27/04 a 04/05 | Lógica de Hoare | hoare, logicadehoare, logicadehoare2 |
| bloco-11 | 06/05 | Correção Parcial e Total | correcaoterminacao, exercicioscorrecaoterminacao, exerciciosformalizacaoalgoritmosinvariantes, formalizacaoalgoritmos-invarianteslaco, invariantes |
| bloco-12 | 11/05 | Terminação + introdução a Dafny | exerciciosdafny1, introducao (código), terminacao |
| bloco-13 | 13/05 a 25/05 | Dafny: arrays, sequências, conjuntos | colecoes-arrays, colecoes-conjuntos, colecoes-sequences, exercicios-conjuntos, exerciciosdafny2, exerciciosdafny3, exerciciosdafny4 |
| bloco-14 | 27/05 | Evento acadêmico | — |
| bloco-15 | 01/06 a 10/06 | Dafny: OO, classes, ghosts | classes-parte1, exerciciosdafny5, tiposindutivos |
| bloco-16 | 15/06 a 29/06 | Verificação de modelos / lógica temporal | — |
| bloco-17 a 21 | 01/07 a 15/07 | revisões/substituição/devolução/exame | — |

## Pontos quentes pra tua revisão (onde a decisão assistida pode estar errada)

1. **Cluster Revisão → bloco-03 (7 casos)**: decidi pela semana do label do card
   ("Semana 09/03"); o scorer prevê bloco-02 (04/03). Se a lógica proposicional
   foi dada em 04/03, troca os 7 pra bloco-02 (mexe 7 pontos no baseline).
2. **Os 5 `.thy` → bloco-06** (arvores, exemplos, intro, listas, provas): âncora
   = ferramenta Isabelle (semana 06-13/04); scorer prevê bloco-05 (provas por
   indução, 30/03). Os exemplos podem ter sido usados já em 30/03.
3. **Marcados "ALTERNATIVA" na note**: `hoare`→10 (alt 12), `invariantes`→11
   (alt 12), `terminacao`→12 (alt 11), `exerciciosdafny1`→12 (alt 13).
4. **`t1-2026-1` ×2 = null (pendente)**: TDE — bloco do deadline (bloco-11,
   06/05) ou do conteúdo (blocos 04-06, Isabelle/recursão)? Tua chamada.
5. **`revisao-p1-gabarito` → bloco-06**: veio do card_block_map antigo
   ("Exercícios de Revisão para Provas" → bloco-06); o scorer prevê bloco-07
   (15/04, dia provável da P1). Se preferir o bloco da prova, muda pra bloco-07
   E corrige o card_block_map.
