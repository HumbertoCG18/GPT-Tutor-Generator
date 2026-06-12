# Gabarito de revisão — aulas × blocos × casos do golden (Metodos-Formais)

date: 2026-06-12 (v2 — aula por aula, datas uniformes)
fonte: sessions do `Metodos-Formais-Tutor/course/.timeline_index.json` (derivado do
cronograma) + `tests/fixtures/eval/metodos_formais_golden.json` (golden v1)

Como revisar: ache a aula em que o material foi usado na tabela 1, confira o bloco;
depois veja na tabela 2 se o caso aponta pra esse bloco. Pra corrigir: edite
`expected_block_id` no golden e rode
`python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`.
Re-runs do gerador preservam tuas mudanças (merge por id+categoria).

## Tabela 1 — Aula por aula (cronograma)

| Data | Bloco | Aula |
|---|---|---|
| 02/03 | bloco-01 | apresentação da disciplina |
| 04/03 | bloco-02 | introdução a métodos formais |
| 09/03 | bloco-03 | revisão de lógica de predicados + exercícios |
| 11/03 | bloco-04 | conjuntos indutivos e equações recursivas |
| 16/03 | bloco-04 | exercícios |
| 18/03 | bloco-04 | estudo de caso: listas |
| 23/03 | bloco-04 | estudo de caso: árvores |
| 25/03 | bloco-04 | exercícios |
| 30/03 | bloco-05 | provas por indução |
| 01/04 | bloco-05 | provas por indução: listas e árvores |
| 06/04 | bloco-06 | prova interativa de teoremas — Isabelle |
| 08/04 | bloco-06 | prova interativa de teoremas — Isabelle |
| 13/04 | bloco-06 | exercícios |
| 15/04 | bloco-07 | exercícios de revisão |
| 20/04 | bloco-08 | suspensão de aulas |
| 22/04 | bloco-09 | PROVA P1 |
| 27/04 | bloco-10 | lógica de Hoare |
| 29/04 | bloco-10 | lógica de Hoare |
| 04/05 | bloco-10 | exercícios |
| 06/05 | bloco-11 | correção parcial/total, terminação, invariantes |
| 11/05 | bloco-12 | terminação + introdução ao Dafny |
| 13/05 | bloco-13 | lógica de programas — Dafny |
| 18/05 | bloco-13 | coleções Dafny: arrays |
| 20/05 | bloco-13 | coleções Dafny: sequências |
| 25/05 | bloco-13 | coleções Dafny: conjuntos |
| 27/05 | bloco-14 | SE Day (evento acadêmico) |
| 01/06 | bloco-15 | OO em Dafny: ghosts, autocontrato |
| 03/06 | bloco-15 | exercícios |
| 08/06 | bloco-15 | OO em Dafny: ghosts, autocontrato |
| 10/06 | bloco-15 | exercícios |
| 15/06 | bloco-16 | verificação de modelos: lógica temporal |
| 17/06 | bloco-16 | verificação de modelos: lógica temporal |
| 22/06 | bloco-16 | exercícios |
| 24/06 | bloco-16 | verificação de modelos: ferramenta |
| 29/06 | bloco-16 | exercícios |
| 01/07 | bloco-17 | exercícios de revisão |
| 06/07 | bloco-18 | PROVA P2 |
| 08/07 | bloco-19 | PROVA PS (substituição) |
| 13/07 | bloco-20 | devolução das provas |
| 15/07 | bloco-21 | PROVA G2 |

## Tabela 2 — Casos do golden por bloco (decisões atuais)

| Bloco | Casos apontando pra ele |
|---|---|
| bloco-02 | introducao (pdf) |
| bloco-03 | revisao, logicaproposicional-sintaxe/-semantica, logicapredicados-sintaxe/-semantica, exerciciosespecificacao (+respostas) |
| bloco-04 | conjuntosindutivos, exerciciosconjuntosindutivos, formalizacaoalgoritmos-recursao(+2), exerciciosformalizacaoalgoritmosrecursao(+2, +respostas) |
| bloco-05 | provasindutivas-especificacoesrecursivas (+listas, +arvores), exercicioscorrecaoinducaomatematica |
| bloco-06 | arvores, exemplos, intro, listas, provas (.thy), revisao-p1-gabarito |
| bloco-10 | logicadehoare, logicadehoare2, hoare (zip) |
| bloco-11 | formalizacaoalgoritmos-invarianteslaco, exerciciosformalizacaoalgoritmosinvariantes, correcaoterminacao, exercicioscorrecaoterminacao, invariantes (zip) |
| bloco-12 | introducao (zip Dafny), terminacao (zip), exerciciosdafny1 |
| bloco-13 | colecoes-arrays/-sequences/-conjuntos, exercicios-conjuntos, exerciciosdafny2/3/4 |
| bloco-15 | classes-parte1, tiposindutivos, exerciciosdafny5 |
| null (pendente) | t1-2026-1 (×2 — TDE) |

## Pontos quentes pra tua revisão

1. ~~`revisao-p1-gabarito` → bloco-06~~ — **RESOLVIDO (12/06)**: usuário confirmou
   que a aula de revisão da P1 é 15/04 (label no card Provas por Indução) =
   bloco-07. `card_block_map` corrigido na fonte ("Exercícios de Revisão para
   Provas" → bloco-07); golden regenerado; caso agora bloco-07 automático.
   PENDÊNCIA: `revisao-p1` tem bloco MANUAL = bloco-06 no manifest do app —
   corrigir lá (editor) pra bloco-07.
2. **Cluster Revisão → bloco-03 (7 casos)**: âncora = label do card ("Semana
   09/03", que na tabela 1 é "revisão de lógica de predicados" — consistente).
   Scorer prevê bloco-02. Mantive 03; confirma.
3. ~~Os 5 `.thy` → bloco-06~~ — **CONFIRMADO pelo usuário (12/06)**: card
   "Provas por Indução", semanas 06/04-13/04 (Isabelle). bloco-06 correto.
4. **"ALTERNATIVA" na note**: `hoare`→10 (alt 12), `invariantes`→11 (alt 12),
   `terminacao`→12 (alt 11), `exerciciosdafny1`→12 (alt 13). A tabela 1 ajuda:
   invariantes/terminação são a aula de 06/05 (bloco-11); Dafny começa 11/05.
5. **`t1-2026-1` ×2 = null**: TDE com deadline 06/05 (bloco-11) vs conteúdo
   Isabelle/recursão (blocos 04-06). Tua chamada.
