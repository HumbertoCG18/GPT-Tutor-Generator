# Tarefa (leitura e classificacao; nao invente dado): quantos erros de subunidade sao "o PAI vencendo o proprio FILHO"?

Voce vai ler DOIS arquivos CSV e classificar 109 linhas. Nao ha nada a pesquisar alem deles.

## Arquivos (caminhos ABSOLUTOS)

1. **Erros:** `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/erros_subunidade_cru_honesto_13-09.csv`
   - 109 linhas. Colunas que importam: `curso`, `entry_id`, `gold` (slug do topico certo), `extras` (slugs aceitos
     alternativos, separados por `;`), `cru` (slug que o motor escolheu; vazio = nao escolheu nada).
2. **Topicos:** `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/pai_filho_topicos_13-09.csv`
   - Colunas: `curso`, `unit_slug`, `slug`, `code`, `kind`, `label`. O `slug` so e unico DENTRO do curso: sempre procure
     pelo par (`curso`, `slug`).

## Definicoes (use exatamente estas)

- **ancestral:** o topico A e ancestral do topico B se `B.code` comeca com `A.code + "."`. Ex.: `2.2` e ancestral de
  `2.2.1` e de `2.2.1.4`. `2.2` NAO e ancestral de `2.21` (sem o ponto).
- **irmaos de subtopico:** os dois codes tem o mesmo prefixo ate o ultimo ponto e esse prefixo tem pelo menos um ponto.
  Ex.: `7.1.1.1` e `7.1.1.4` sao irmaos (prefixo `7.1.1`). `2.1` e `2.3` NAO contam aqui (sao topicos de primeiro nivel).

## Classificacao de cada linha, NESTA ORDEM (pare na primeira que se aplica)

1. `gold` vazio -> **gold_vazio**
2. `cru` vazio -> **predicao_vazia**
3. o (`curso`, `gold`) ou o (`curso`, `cru`) nao existe na tabela de topicos -> **slug_ausente**
4. o `code` do gold OU o `code` do cru esta vazio (acontece no curso IA inteiro) -> **sem_codigo**
5. `unit_slug` do cru diferente do `unit_slug` do gold -> **unidade_diferente**
6. cru e ancestral do gold -> **pai_vence_filho**
7. gold e ancestral do cru -> **filho_vence_pai**
8. cru e gold sao irmaos de subtopico -> **irmaos_subtopico**
9. qualquer outro caso -> **mesma_unidade_sem_parentesco**

Em TODAS as linhas, preencha tambem `cru_e_ancestral_de_extra`: true se o `cru` for ancestral de algum slug da coluna
`extras` (mesma regra de code). Isso detecta o pai vencendo um filho que era resposta aceita alternativa.

## Anomalia conhecida (nao corrija, so registre em `observacoes` se afetar alguma linha)

No curso FR existe o topico de code `3.21` (`controle-de-congestionamento-tcp`) marcado `kind=topic`. Pela regra do
ponto, ele NAO e filho de `3.2`. Aplique a regra literal.

## Saida

JSON no schema fornecido. **Os 109 erros, um por linha, na ordem do CSV.** Os `totais` devem somar 109. Na
`justificativa`, cite os dois codes (ex.: "cru 2.2 e ancestral do gold 2.2.1").
