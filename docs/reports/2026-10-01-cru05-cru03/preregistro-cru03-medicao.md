# CRU-03: pré-registro da medição de sinal nos blocos de afinidade zero (01/10/2026)

Escrito e selado por sha256 **antes** de qualquer execução. É só medição e não muda decisão de produção.

- **Gold:** não é lido.
- **Gate:** do usuário em 01/10, "faça a opção 2 e depois a medição do CRU-03", no desenho da revisão do GPT Pro, item 6.

## Base

`src` em `bf46d51f`, **sem** a correção do CRU-05: a worktree da noite de 30/09, com `src`/`tests` idênticos ao HEAD.
Os dados são os mesmos do replay da base (`replay_base.json`, `e024d396…`, 223/249/86) e são lidos da árvore
principal, só leitura.

## Definições (fixadas antes)

- **Candidato:** bloco do `course/.timeline_index.json` com `auto_unit_slug` não vazio, na ordem do índice. É o que o DP
  posicional recebe (`wz2_diagnostico_causal_23-09.py`, `decompor_dp`).
- **Afinidade de um bloco a uma unidade:** `|tokens do bloco ∩ tokens da unidade|`, pelas funções do próprio
  `unit_matcher` (`_block_tokens`, `_unit_tokens`).
- **Afinidade zero (universo):** um candidato cuja afinidade máxima, entre todas as unidades, é 0 (classe `sem_sinal`
  do W-Z2). A unidade dele vem da ordem e da janela (DP).
- **Posição**, pela unidade que o DP atribui ao bloco anterior e ao seguinte:
  - **borda:** primeiro ou último candidato;
  - **interior:** o anterior e o seguinte têm a mesma unidade que o bloco;
  - **fronteira:** qualquer outro caso.
- **Fidelidade do DP:** a recomputação de `assign_units_positional` é igual ao `auto_unit_slug` gravado, bloco a bloco.
  Blocos não fiéis são registrados e entram no inventário, mas não no resumo do sinal.
- **Materiais do bloco:** os IDs cujo bloco, no `replay_base.json`, é o ID do bloco. A decisão de bloco é do eixo de
  bloco, independente da unidade do bloco.

## Sinais medidos

1. **Seção do Moodle**, sinal independente da atribuição: a organização é do professor no Moodle.
   - Para cada material: a unidade implicada pela seção, que o `auto_unit` já calcula (`section_slug`, #47; campo
     `unidade_bruta.secao` do rastro da base, `diag_rastro_base.json`), e o nome cru da seção no manifest.
   - **Unidades compatíveis com o bloco:** o conjunto de `section_slug` não vazios dos seus materiais.
2. **Aliases EN/PT:** **não medido.** Não há fonte bilíngue verificável e independente dos erros conhecidos, e os aliases
   da taxonomia já entram na afinidade (`_unit_tokens`). Fica registrado como lacuna; não se cria léxico novo.

## Saída

Uma tabela lateral por bloco do universo:

- curso, ordem, posição e período;
- rótulo das sessões;
- unidade do DP e mecanismo (puro, desvio, âncora);
- número de materiais e os que têm seção;
- multiconjunto de `section_slug`;
- cardinalidade das unidades compatíveis (0, 1, mais de 1);
- **concordância** da compatível única com a unidade do DP (concorda, conflita, ausente).

Resumos por curso e por posição. A saída inclui também o inventário de **todos** os candidatos, para controle, e a
reconciliação com os 50/125 do W-Z2. A contagem nova não precisa ser idêntica.

"Uma compatível que conflita com o DP" **não** quer dizer erro do DP, e "concorda" não quer dizer acerto. Sem gold não
há placar.

## Selo e parada

- A tabela é selada por sha256 ao ser gravada.
- **Uma passagem pelo universo, e fim.** Sinal ausente, conflitante ou não discriminante é resultado válido.
- Não há grade de combinações, não se reabre R1–R4 e não se faz proposta de regra: ela exigiria Gate próprio, com gold
  só para pontuar uma proposta congelada.
