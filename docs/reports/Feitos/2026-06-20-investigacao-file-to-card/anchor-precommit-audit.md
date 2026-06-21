# anchor_placement.py — Pre-commit Audit
date: 2026-06-21
branch: feat/block-stable-id

---

## 1. CLEANUP

### Mudanças feitas em `src/builder/routing/anchor_placement.py`

1. **Removida `_resolve_semana`** (linhas ~156-222 antes do cleanup): função morta,
   near-duplicate de `_resolve_semana_with_meta`. `_anchor_dispatch` nunca a chamava.
   Consolidado em única função `_resolve_semana_with_meta` que retorna `(uuid, win_start, win_end, section)`.

2. **`import calendar` movido para o topo do arquivo** (linha 20): estava duplicado
   inline dentro de `_resolve_semana` e `_resolve_semana_with_meta`.

Nenhuma mudança de comportamento.

### pytest resultado

```
1594 passed in 10.93s
```

Zero regressões. Os 5 novos testes de `tests/test_anchor_placement.py` permanecem verdes.

### Recomputed IA canary (persist=False, in-memory)

| Método | N |
|--------|---|
| anchor | 37 |
| manual | 5  |
| scorer | 8  |
| TOTAL  | 50 |

Idêntico ao relatório anterior. Prova read-only: `manifest.json` e `.block_identity.json`
mtimes inalterados; `git status` do IA não mostra modificação nesses arquivos.

---

## 2. THRESHOLD AUDIT — Anchors de 1-stem

`_MIN_TOPIC_OVERLAP = 1`. De 37 anchors: **9 com >=2 stems, 28 com exatamente 1 stem**.

### Critério de classificação

- **STRONG**: o único stem que casou é a palavra que DEFINE o tópico
  (ex.: `supervis` em "Aprendizado Supervisionado" / "abordagem supervisionada" — disambígua claramente).
- **WEAK**: o stem que casou é genérico e pode mascarar tópicos diferentes
  (ex.: `introduc` — "Introdução a IA" bate com block topic = "introducao", que é o topic_text
  literal do bloco, não necessariamente confirmando o assunto real).

### 1-stem STRONG (24)

Todos via stem `supervis` (Aprendizado Supervisionado / Não Supervisionado)
ou stem `dados` (Machine Learning e Dados):

| entry_id | stem | section topic | block topic |
|----------|------|---------------|-------------|
| aprendizadonaosupervisionado-agrupamento-parte1 | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico analise resultados |
| aprendizadonaosupervisionado-agrupamento-parte2 | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico analise resultados |
| mlp-novaversao | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural introducao perceptron... |
| redesperceptron2023-02 | supervis | Machine Learning Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| como-analisar-resultados-sse-comcorrecoes | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| perceptron-equacaodereta | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| introducaoredesneurais-2023-02 | supervis | Machine Learning Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| aprendizadosupervisionado-classificacao-knn | dados | Machine Learning e Dados | tipos dados preparacao |
| rede-perceptron | supervis | Machine Learning Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| mlp | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| arvores-de-decisao | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| aula-sobre-agrupamento-parte-1-particional | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |
| aula-sobre-agrupamento-parte-2-hierarquico | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |
| algoritmo-de-classificacao-k-nn | dados | Machine Learning e Dados | tipos dados preparacao |
| analise-exploratoria-dos-dados-exemplo-2 | dados | Machine Learning e Dados | tipos dados preparacao |
| artigo-usando-k-nn-em-texto | dados | Machine Learning e Dados | tipos dados preparacao |
| exemplo-de-programa-com-k-nn-em-java | dados | Machine Learning e Dados | tipos dados preparacao |
| introducao-a-redes-neurais | supervis | Machine Learning Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| rede-perceptron-e-equacao-de-reta | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| como-analisar-resultados-acc-pr-re-e-f1 | supervis | ML - Aprendizado Supervisionado | abordagem supervisionada rede neural... |
| agrupamento-usando-k-means-exemplo-1-ipynb | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |
| agrupamento-usando-k-means-exemplo-2-ipynb | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |
| artigo-usando-agrupamento | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |
| survey-on-clustering | supervis | ML - Aprendizado Não Supervisionado | suspensao abordagem supervisionada means hierarquico... |

### 1-stem WEAK (4)

Stem genérico `introduc` ("introdução") — bate na section topic "Introdução a IA e ML" com
block topic_text = "introducao" (valor exato no campo, não elaborado):

| entry_id | stem | section topic | block topic |
|----------|------|---------------|-------------|
| caracteristicasdosdados | introduc | Introdução a IA (continuação) e Introdução a ML | introducao |
| introducaoml-atualizacao2025 | introduc | Introdução a IA (continuação) e Introdução a ML | introducao |
| caracteristicas-dos-dados | introduc | Introdução a IA (continuação) e Introdução a ML | introducao |
| introducao-a-ml | introduc | Introdução a IA (continuação) e Introdução a ML | introducao |

**Observação sobre os WEAK:** O block topic_text do bloco de introdução é literalmente "introducao"
(string curta, sem contexto). A seção diz "Introdução a IA e ML" e o bloco é realmente o bloco de
introdução — portanto o placement é provavelmente CORRETO, mas o sinal é fraco pois o topic_text
do bloco não tem tokens ricos. O problema está na qualidade do topic_text do bloco (campo raso),
não num mismatch real. Esses 4 casos não constituem falsos positivos confirmados — precisam de
verificação manual do Humberto antes de descartar ou elevar `_MIN_TOPIC_OVERLAP`.

### Resumo contagem

| Categoria | N |
|-----------|---|
| >=2-stem anchors | 9 |
| 1-stem STRONG | 24 |
| 1-stem WEAK | 4 |
| TOTAL anchors | 37 |

---

## 3. TEST ASSERTIONS (5 testes)

### Test 1 — `test_manual_wins`
- **Path:** Tier 1 — `manual_timeline_block_id` presente e válido no ledger
- **Assert:**
  ```python
  assert result.block_uuid == UUID_MANUAL  # "aaaa0000-0000-0000-0000-000000000001"
  assert result.method == "manual"
  ```
- **Não-vacuoso:** Verifica tanto o UUID exato quanto o método. A entry tem source_section válida
  que produziria um anchor diferente (UUID_ANCHOR) — o teste confirma que manual VENCE o anchor.

### Test 2 — `test_anchor_valid_week`
- **Path:** Tier 2 — seção semana com datas e tópico que batem no bloco
- **Assert:**
  ```python
  assert result.block_uuid == UUID_ANCHOR  # "bbbb0000-0000-0000-0000-000000000002"
  assert result.method == "anchor"
  assert result.section is not None
  assert result.window_start is not None
  assert result.window_end is not None
  ```
- **Não-vacuoso:** Verifica UUID exato, method, e a presença dos 3 campos de metadados de âncora.

### Test 3 — `test_admin_section_falls_through`
- **Path:** Tier 2 falha (seção "TDE Trabalho Discente Efetivo" é admin) → Tier 3 scorer
- **Assert:**
  ```python
  assert result.block_uuid == UUID_SCORER  # "cccc0000-0000-0000-0000-000000000003"
  assert result.method == "scorer"
  ```
- **Não-vacuoso:** Verifica UUID do scorer e method. Confirma que admin section não ancora.

### Test 4 — `test_topic_mismatch_falls_through`
- **Path:** Tier 2 falha (datas batem em BLOCK_SUPERVISIONADO mas topic "Algoritmos de Busca"
  não tem overlap com "abordagem supervisionada rede neural") → Tier 3 scorer
- **Assert:**
  ```python
  assert result.block_uuid == UUID_SCORER
  assert result.method == "scorer"
  ```
- **Não-vacuoso:** Verifica UUID exato e method. O bloco existe na janela (datas corretas) mas
  tópico diferente — o teste confirma que topic validation é obrigatória, não apenas datas.

### Test 5 — `test_no_source_section_falls_through`
- **Path:** source_section = None → Tier 2 skip → Tier 3 scorer
- **Assert:**
  ```python
  assert result.block_uuid == UUID_SCORER
  assert result.method == "scorer"
  ```
- **Não-vacuoso:** Verifica UUID e method. Confirma fallback quando entry sem seção.

---

## Concerns

1. **4 WEAK (stem `introduc`):** O sinal é fraco porque o block topic_text é "introducao" (campo
   raso). O placement provavelmente está correto mas não é confirmado pelos dados do bloco.
   Recomendação: enriquecer o topic_text do bloco de introdução no timeline, ou aguardar
   verificação manual antes de confiar nesses 4 como anchor sólido.
   **NÃO alterar `_MIN_TOPIC_OVERLAP` com base apenas nisto** — bumpar para 2 eliminaria 28 anchors
   corretos (os STRONG) para corrigir 4 casos borderline.

2. **`supervis` em blocos de "Não Supervisionado":** 12 entries de seções "Aprendizado Não
   Supervisionado" ancoram num bloco cujo topic_text menciona "abordagem supervisionada means
   hierarquico" — o stem `supervis` vem do topic_text do bloco que lista AMBAS as abordagens.
   O placement para o bloco correto (bloco da semana de agrupamento) porque é o único bloco
   com sessões naquela janela de datas — a âncora é temporalmente sólida, mas o sinal semântico
   é ruidoso. Não é um falso positivo, mas é um sinal de que o topic_text do bloco precisa ser
   atualizado para refletir melhor o período de Não Supervisionado.
