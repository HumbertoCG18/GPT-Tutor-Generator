# Fase 0: pré-registro da medição descritiva do pontuador da subunidade (01/10/2026)

Gate do usuário: "autorizo a Fase 0", sobre `proposta-pontuador-termos-pouco-discriminantes.md`. É medição
descritiva:

- sem regra, sem gold e sem placar;
- instrumentação só em memória;
- selado por sha256 antes da execução.

## Universo

- **Cursos:** MF, SO, IA, ES2 e TCC (desenvolvimento). **CG e FR não são executados.**
- **Base:** `src` em `bf46d51f`, sem a correção do CRU-05 (worktree da noite de 30/09). Dados da árvore principal, só
  leitura.
- **Materiais:** os que passam pela **1ª passada** da subunidade (`auto_map_entry_subtopic` fora da propagação). Quando
  o mesmo material tem mais de uma chamada, vale a última; o número de chamadas fica registrado.

## Fidelidade (qualquer falha torna a execução inconclusiva; sem ajuste nem repetição)

1. **Decisões:** as finais (bloco, unidade, subunidade) dos 5 cursos são idênticas às de `replay_base.json` (sha256
   `e024d396…`) em todos os IDs.
2. **Captura:** para cada chamada capturada, o vencedor recalculado com o pontuador real sobre os tópicos da unidade
   vencedora é igual ao `topic_slug` devolvido. Vale quando a decisão não é vazia.
3. **Decomposição:** a soma das componentes reproduz `_score_entry_against_taxonomy_topic(sinais, tópico)` em todos os
   pares (material, tópico) avaliados, com |dif| < 1e-9.

## Decomposição da pontuação (mesmas funções do módulo)

score = (Σ acertos de frase + bônus de sobreposição + extras) × multiplicador de penalidade.

- **acerto de frase:** (campo, frase normalizada, peso do campo × fator: rótulo 1,0, alias 0,82, slug 0,65). O
  casamento usa o `_matches_normalized_phrase` real.
- **bônus de sobreposição:** `topic_tokens` ∩ `signal_tokens`, pelas regras do pontuador (`generic_tokens`,
  `short_vocab`, fusões do slug).
- **extras:** categoria 0,08 e subtópico 0,04.
- **penalidades:** quando `exact_hits == 0`.

## Frequências (do plano e do corpus; sem gold)

- **F_top(x, u)** de uma **frase** *x*: número de tópicos da unidade *u* (o mesmo índice que o seletor usa) com
  alguma frase (rótulo, alias, slug) que casa *x* pelo matcher real. Inclui o próprio tópico.
- **F_top(k, u)** de um **token** *k*: número de tópicos de *u* cujos `topic_tokens` contêm *k*.
- **F_mat(x, c, campo)** de uma frase: fração dos materiais da 1ª passada do curso *c* em que *x* casa no campo.
- **F_mat(k, c)** de um token: fração dos materiais de *c* cujos `signal_tokens` (mesma regra do pontuador) contêm *k*.
- **Pouco discriminante:**
  - entre tópicos: **F_top ≥ 2**;
  - entre materiais: **F_mat > 0,25**. O limiar é herdado de `df_max` da propagação, fixo, sem grade.

## Saídas

Por curso e no total dos 5:

1. **Composição do vencedor da 1ª passada**, só entre materiais com vencedor > 0:
   - fração da pontuação de **frases** que vem de frases com F_top ≥ 2, F_mat > 0,25 ou ambos (componente aditiva
     exata);
   - mediana e quartis.
2. **Sensibilidade (contrafactual, não placar).** A pontuação de todos os tópicos da unidade é recalculada pelas mesmas
   regras em três versões:
   - **R_top:** sem as frases e tokens com F_top ≥ 2;
   - **R_mat:** sem as frases com F_mat > 0,25 no campo do acerto e sem os tokens com F_mat > 0,25;
   - **R_both:** sem os dois.

   Para cada versão são contados os materiais em que:
   - (a) o argmax muda;
   - (b) o estado muda entre decidido, ambíguo (margem relativa < 0,12) e vazio (sem sinal ou empate exato).

   Sem gold, nenhuma dessas mudanças é "acerto" ou "erro".
3. **Inventário:** frases e tokens pouco discriminantes por curso, com F_top e F_mat, e quantas decisões eles tocam.

## Critério indicativo (informa, não decide; a decisão é do usuário)

- **A hipótese perde força** se, no total dos 5 cursos, a mediana do item 1 (ambos os critérios) for < 10 % **e** as
  mudanças de argmax em R_both atingirem < 5 % dos materiais com vencedor.
- **Ganha força** se uma das duas medidas passar de 25 %.
- Entre os dois, o resultado é inconclusivo.

## Parada

Uma execução, sem repetição e sem variação de limiar. Depois, só o relatório. A Fase 1 exige Gate próprio.
