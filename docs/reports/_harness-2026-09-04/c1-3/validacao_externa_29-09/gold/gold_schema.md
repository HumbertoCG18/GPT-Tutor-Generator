# Schema do gold da validação externa (versão `gold-externo-1`, 29/09/2026)

Um arquivo por curso: `gold_<SIGLA>.csv`, UTF-8 sem BOM, fim de linha LF, separador vírgula, aspas duplas quando
necessário. Parte do `gold_modelo.csv` do pacote cego, que já traz uma linha por `material_id` na ordem do pacote.
Validação automática: `generico/gold_externo.py` (`valida_gold`). JSON Schema equivalente: `gold_schema.json`.

## Colunas

| coluna | obrigatória | valores |
|---|---|---|
| `material_id` | sim | exatamente os ids de `materiais.json` com `adjudicavel = true`; nenhum a mais, nenhum a menos, sem repetição |
| `status` | sim | `avaliado`, `meta` ou `excluido` |
| `unidade` | se `status` ≠ `excluido` | um ou mais ids de unidade de `rotulos.json` separados por `\|`, ou `-` (nenhuma unidade é a resposta certa) |
| `sub_primaria` | se `status` = `avaliado` | um ou mais ids de tópico separados por `\|`, ou `-` (nenhum tópico é a resposta certa) |
| `sub_aceita` | se `status` = `avaliado` | ids de tópico separados por `\|`, contendo todos os de `sub_primaria`; `-` só se `sub_primaria` = `-` |
| `observacao` | não | texto livre; nunca entra na avaliação |

Célula vazia = campo não preenchido (erro de validação se obrigatório). `-` = "vazio é a resposta certa".

## Regras de consistência (validação reprova o arquivo inteiro)

1. Todo id de tópico pertence a uma das unidades da linha. Com `unidade` = `-`, `sub_primaria` e `sub_aceita` são `-`.
2. `sub_primaria` ⊆ `sub_aceita`.
3. `meta` e `excluido` deixam `sub_primaria` e `sub_aceita` vazios; `excluido` deixa `unidade` vazia.
4. Sem ids desconhecidos, sem duplicata dentro de uma célula, sem espaço em volta dos ids.
5. O arquivo é congelado por sha256 e blob git ANTES de qualquer build, replay ou captura dos cursos novos.

## Tradução para a régua do avaliador (contrato da rodada VOCAB_LIMPO)

| gold | régua interna (`{"gold_id", "eid", "bloco", "unidade", "sub_primaria", "sub_aceita"}`) |
|---|---|
| `material_id` | `gold_id`; `eid` = entry do build ligada pelo mapeamento pré-registrado; sem entry = `None` (material ausente, conta como erro) |
| bloco | sempre `None`: bloco não é rotulado nos cursos novos (pré-registro, §6.3) |
| `unidade` = ids | conjunto dos slugs de unidade congelados em `rotulos.json` |
| `unidade` = `-` | `{""}` (vazio é a resposta certa) |
| `sub_*` = ids | conjunto dos slugs de tópico congelados em `rotulos.json` |
| `sub_*` = `-` | `{""}` |
| `meta` | `unidade` como acima; `sub_primaria` = `sub_aceita` = `None` (fora do denominador da subunidade) |
| `excluido` | linha fora de todos os eixos (contada e relatada; não entra em denominador) |

Os denominadores por curso e eixo saem do gold congelado e são gravados no congelamento do gold, antes de qualquer
replay. Não podem mudar depois.
