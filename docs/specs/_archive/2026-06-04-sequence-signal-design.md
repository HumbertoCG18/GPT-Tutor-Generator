# Sinal de Sequência (ordinal de aula) — Design

last_updated: 2026-06-04
status: aprovado (aguardando revisão do spec escrito)

## Objetivo

Melhorar a precisão da atribuição arquivo→bloco quando o material tem um ordinal de aula explícito no nome ("Aula 03") e o cronograma tem blocos de aula adjacentes com texto parecido e sem data — o caso que hoje cai no fallback "pega o melhor" com band baixa (chute). O ordinal vira um sinal de desempate moderado.

Métrica de sucesso: o harness `scripts/eval_assignments.py` mede ganho de acurácia em casos com ordinal, sem regressão nos casos existentes (gate `tests/test_eval_assignments.py`).

## Escopo

Dentro do v1:
- Extração de ordinal de aula do título/nome do material (marcadores `aula`, `encontro`).
- Numeração dos blocos `kind=class` em ordem cronológica.
- Boost de desempate `SEQUENCE_BOOST=0.20` quando o ordinal do material casa a posição do bloco de aula.

Fora do v1 (YAGNI / v2):
- Ordem de import como sinal (descartado: tipicamente arbitrária — alfabética/lote).
- Marcador `semana N` (semana ≠ aula; uma semana pode ter 2 aulas).
- Ordinais romanos (`Aula III`).
- Mapeamento por categoria do material (`Lista 02` contra blocos de lista).

## Como funciona (fluxo)

Cronograma exemplo:

```
bloco-01  11/03  kind=class      "Lógica de predicados"   -> aula nº 1
bloco-02  18/03  kind=class      "indução estrutural"     -> aula nº 2
bloco-03  25/03  kind=holiday    "Carnaval"               (pulado)
bloco-05  08/04  kind=class      "Recursão"               -> aula nº 3
```

Material `Aula 03 - slides.pdf` (sem data, texto fraco):

1. **Extração:** `"aula 03 slides"` → marcador `aula` + número `03` → ordinal = 3.
2. **Numeração:** blocos `kind=class` em ordem cronológica recebem `class_ordinal` 1, 2, 3 (holiday/review/assessment não contam).
3. **Match:** ordinal 3 → 3ª aula = bloco-05. Ao pontuar bloco-05, soma `+0.20`.
4. **Desempate:** antes os três blocos de aula empatavam ~0.05 (texto fraco). bloco-05 vira 0.25, vence limpo. Band sobe de baixa para média.

Sinais fortes preservam prioridade: um match de data (`+0.30`) ou tópico (`+0.48`) ainda vence o `+0.20`, então um ordinal mal-extraído não rouba uma atribuição genuína.

## Arquitetura

### Novo módulo: `src/builder/routing/sequence.py`

Três funções puras, sem estado, testáveis isoladamente:

**`extract_lecture_ordinal(text: str) -> Optional[int]`**
- Entrada: texto JÁ normalizado (como chega nos `signals`, ex.: `title_text`, `raw_text`). Normalização existente colapsa pontuação em espaços ("Aula 03" → "aula 03").
- Procura o padrão: marcador de aula (`aula` ou `encontro`) seguido imediatamente (mesma adjacência tokenizada) de um inteiro arábico.
- Retorna o inteiro (ex.: 3) ou `None`.
- Regras anti-falso-positivo:
  - Só dispara com marcador de aula. `lista 2`, `prova 1`, `capitulo 5 12`, `2024` → `None`.
  - Pega o número adjacente ao marcador. `aula 03 2024` → 3 (não 2024).
  - Número arábico apenas. `aula iii` → `None` no v1.
  - Se houver mais de um marcador de aula com números diferentes (raro), usa o primeiro.

**`annotate_class_ordinals(blocks: list) -> list`**
- Percorre `blocks` em ordem cronológica (a lista já chega ordenada pelos call sites; ordenação por período é responsabilidade do upstream, não deste helper).
- Atribui `block["class_ordinal"] = 1, 2, 3, ...` apenas a blocos com `kind == "class"`.
- Blocos de outro `kind` (holiday/review/assessment) ou sem `kind` recebem `block["class_ordinal"] = None`.
- Idempotente: recomputa os mesmos valores se chamado de novo.
- Retorna a mesma lista (mutação in-place dos dicts de bloco, consistente com como `rows`/`scores` já são carimbados em `score_entry_against_timeline_block`).

**`score_sequence_match(signals: dict, block: dict, *, boost: float) -> float`**
- Extrai o ordinal via `extract_lecture_ordinal` a partir de fontes dos signals (`title_text` primeiro, depois `raw_text`; NÃO usa markdown completo para evitar "aula 3" solto no corpo de outro material).
- Se o ordinal existe E `block.get("class_ordinal")` é igual → retorna `boost`.
- Caso contrário → `0.0`.

### Constante: `src/builder/routing/thresholds.py`

Adicionar ao dataclass `_Thresholds`:
```
SEQUENCE_BOOST: float = 0.20
```
Justificativa do valor no comentário: menor que `DATE_STRONG_BOOST=0.30` e que o boost de tópico (`+0.48`), de modo que o ordinal desempata blocos de aula adjacentes sem sobrepor um match forte de data/tópico. Não rebalanceia thresholds existentes — apenas adiciona.

### Integração: `src/builder/routing/file_map.py`

Dentro de `score_entry_against_timeline_block`, somar o sinal junto dos demais boosts (após o boost de data em `file_map.py:838`):

```python
from src.builder.routing.sequence import score_sequence_match
from src.builder.routing.thresholds import T
...
score += score_sequence_match(signals, block, boost=T.SEQUENCE_BOOST)
```

Import no topo do módulo se não criar ciclo; caso contrário, import tardio dentro da função (padrão já usado no codebase para quebrar ciclos — cf. `_best_instructional_block_fallback`).

### Carimbo dos ordinais (2 call sites)

`annotate_class_ordinals(blocks)` deve rodar antes de qualquer pontuação, nos dois pontos que possuem a lista completa de blocos:

1. `src/builder/routing/file_map.py` — `select_probable_period_for_entry`: logo após montar `blocks` (após `file_map.py:1064`), antes do loop de scoring. Cobre o scorer primário e o roteamento do FILE_MAP (navigation.py).
2. `src/builder/extraction/content_taxonomy.py` — `_best_instructional_block_fallback`: logo após o guard `if not instructional_blocks` (após `content_taxonomy.py:819`), antes do scoring. Cobre o caminho "pega o melhor".

Como o boost vive dentro de `score_entry_against_timeline_block` (chamado por ambos os caminhos), carimbar nos dois call sites garante cobertura total sem duplicar a lógica de boost.

## Edge cases (decididos)

| Caso | Comportamento |
|---|---|
| `Aula 09` mas só 3 aulas no cronograma | Nenhum bloco tem `class_ordinal == 9` → sem match, sem boost. Não crava na última aula. |
| `Aula 03 - 2024` | Extrai 3 (número adjacente ao marcador), ignora 2024. |
| Cronograma sem blocos `kind=class` | Todos `class_ordinal = None` → sinal inerte, `+0.0`. |
| `Aula III` (romano) | `None` no v1. |
| `Lista 02`, `Prova 1`, `Capitulo 5.12` | Sem marcador de aula → `None`, não dispara. |
| Dois materiais "Aula 03" | Cada um recebe o mesmo `+0.20` no bloco-3-de-aula; desempate entre eles fica a cargo dos outros sinais (comportamento atual preservado). |

## Estratégia de testes

### Testes unitários (`tests/test_sequence_signal.py`)
- `extract_lecture_ordinal`: positivos (`Aula 3`, `aula 03`, `Encontro 2`); negativos/armadilhas (`Lista 2`, `Prova 1`, `Capitulo 5 12`, `2024`, `aula iii`, texto sem ordinal); adjacência (`aula 03 2024` → 3).
- `annotate_class_ordinals`: numera só `kind=class` em ordem, pula holiday/review/assessment, idempotência, lista sem class → todos `None`.
- `score_sequence_match`: `+0.20` quando ordinal casa `class_ordinal`; `0.0` quando não casa, quando ordinal é `None`, ou quando `class_ordinal` é `None`.

### Teste de integração no scorer (`tests/test_sequence_signal.py` ou no arquivo de scoring existente)
- `score_entry_against_timeline_block` com material `Aula 03` e blocos anotados: o bloco da 3ª aula pontua acima dos demais; sem ordinal, scores iguais (prova que o delta vem do sinal).

### Harness (gold set)
- Adicionar caso(s) a `tests/fixtures/eval/assignments_gold.json`: timeline com ≥3 blocos `kind=class` (intercalando um holiday para provar o pulo), material `Aula 03` sem data/tópico forte cujo `expected_block_id` é a 3ª aula.
- Medir com `python scripts/eval_assignments.py` ANTES da integração (caso erra/baixa) e DEPOIS (acerta). Registrar o ganho.
- Re-travar `baseline.block_accuracy` no valor medido após a mudança.

### Gate de regressão
- `tests/test_eval_assignments.py` (já existe) garante que os 4 casos atuais não regridam e que nenhum vira órfão.
- Rodar a suite completa (`python -m pytest tests -q`) — zero novas falhas.

## Riscos e mitigação

- **Ordinal mal-extraído rouba atribuição:** mitigado pela força moderada (data/tópico vencem) + extração conservadora (só marcador de aula + número arábico adjacente) + cobertura de armadilhas nos testes.
- **Materiais de aula não-1:1 com blocos de aula** (ex.: 2 slides para a mesma aula): ambos recebem o boost no mesmo bloco; correto (mesmo bloco) — não é regressão.
- **Cronograma com numeração de aula inconsistente** (professor pula números): `class_ordinal` segue a ordem cronológica real, não os números do professor. Se divergir, o ordinal do material pode apontar para a aula errada. Aceito no v1: o sinal é desempate, e o harness mede se ajuda no agregado. Documentar como limitação conhecida.

## Arquivos tocados

| Arquivo | Mudança |
|---|---|
| `src/builder/routing/sequence.py` | NOVO: `extract_lecture_ordinal`, `annotate_class_ordinals`, `score_sequence_match` |
| `src/builder/routing/thresholds.py` | `SEQUENCE_BOOST = 0.20` no `_Thresholds` |
| `src/builder/routing/file_map.py` | `score_entry_against_timeline_block` soma o boost; `select_probable_period_for_entry` carimba ordinais |
| `src/builder/extraction/content_taxonomy.py` | `_best_instructional_block_fallback` carimba ordinais |
| `tests/test_sequence_signal.py` | NOVO: unitários + integração |
| `tests/fixtures/eval/assignments_gold.json` | caso(s) de ordinal + baseline re-travado |
```
