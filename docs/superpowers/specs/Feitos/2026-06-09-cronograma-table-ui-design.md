# Design: aba Cronograma como tabela editável

last_updated: 2026-06-09
status: aprovado

## Problema

A aba Cronograma (`src/ui/timeline_dashboard.py`, 722 linhas) é um accordion
vertical de blocos construído à mão (grid de frames tk). O usuário acha a leitura
confusa, quer uma **tabela densa** (estilo planilha) para revisar/corrigir o
cronograma de relance, com ordenação por coluna e um override manual de escopo de
prova que hoje não existe.

## Decisões (do usuário)

1. Direção visual: **tabela editável** (rejeitou accordion polido e linha do tempo).
2. Colunas: **✓(incluir) · # · Data · Bloco/tópico · Tipo · Unidade · Escopo · Arq.**
3. Edição inline de **Tipo** e **Unidade** (mantém o que já existe). **Escopo**
   editável em prova/revisão (capacidade nova).
4. Capacidades novas: **ordenar por coluna** + **editar escopo da prova**
   (override manual de `scope_unit_slugs`).
5. Fora de escopo: busca por texto; editar data do bloco.

## Arquitetura

Reescrever a view sobre **`ttk.Treeview`** (tabela nativa do tk):

- **Linhas-pai** = blocos; **linhas-filhas** = arquivos do bloco (expandir/recolher
  nativo do Treeview, substitui o accordion manual).
- Colunas configuradas via `Treeview(columns=..., show="tree headings")`. A coluna
  da árvore (`#0`) guarda Data + título do bloco; as demais como `columns`.
- **Ordenação nativa**: bind no cabeçalho (`heading(..., command=...)`) reordena as
  linhas-pai (arquivos seguem o bloco). Pura UI, sem persistência.
- Mantém a **barra de filtro por tipo** (checkboxes) no topo e os botões
  **Recarregar** / **Reprocessar** (revela ao haver alteração suja, como hoje).
- **Arquivos não mapeados**: segunda `Treeview` (ou seção) abaixo, com ação
  "atribuir a bloco".

A view fica mais enxuta que as 722 linhas atuais; lógica pura (carga, saves, chave
de ordenação, merge de escopo) sai para funções testáveis fora da classe.

## Componentes

### 1. View `TimelineDashboardView` (reescrita, `src/ui/timeline_dashboard.py`)

- `_build_table()`: cria a `ttk.Treeview` com as 8 colunas + scrollbar.
- `_populate()`: insere blocos (pai) e arquivos (filhos) a partir do cache
  (`self._blocks`, `self._entries_by_block_id`).
- `_sort_by(column)`: reordena linhas-pai pela chave da coluna; redesenha.
- Edição inline (Tipo/Unidade): clique na célula → `ttk.Combobox` sobreposto
  (overlay posicionado via `bbox`); ao escolher, salva e re-renderiza.
- Edição de Escopo: clique na célula Escopo de um bloco prova/revisão → popup
  `ScopeEditDialog` (checkboxes das unidades do curso) → salva override.
- Mantém `refresh()`, `_reload()`, `_on_reprocess()`, filtro por kind, estados de
  erro (sem repo / sem build / sem cronograma).

### 2. Helpers puros (testáveis)

- `timeline_sort_key(block, column) -> tuple`: chave de ordenação por coluna
  (`Data` → datetime parseada; `#` → int da sequência; `Tipo`/`Unidade` → str;
  `Arq.` → int). Blocos sem valor vão para o fim de forma estável.
- `save_block_scope_override(course_dir, block_id, slugs)`: persiste/limpa o
  override manual de escopo via `set_block_override` (curation). `slugs` vazio/None
  remove o override.

### 3. Persistência do override de escopo (curation)

- Novo campo de override: `manual_scope_unit_slugs` (lista de slugs).
  - `src/builder/timeline/curation.py`: incluir `manual_scope_unit_slugs` em
    `_OVERRIDE_FIELDS` e mapear em `_BLOCK_FIELD_RENAMES` para
    `block_manual_scope_slugs` (evita colisão com o campo derivado
    `scope_unit_slugs`, mesma convenção de `manual_unit_slug → block_manual_unit_slug`).
  - `_apply_curation_overrides` (em `index.py`) já chama `apply_block_curation`;
    nenhuma derivação extra é necessária ali além do merge do campo.
- `apply_assessment_review_scope(blocks)` (em `index.py`) passa a **respeitar o
  escopo manual**: se o bloco tem `block_manual_scope_slugs` não-vazio, usa-o como
  `scope_unit_slugs` e o label "Conteúdo: …" derivado dele; **não** sobrescreve com
  o derivado por data. Manual vence derivado (mesma precedência do label manual).

### 4. Fluxo de dados

- Carga: `load_timeline_data(manifest, timeline_index)` (já existe) → blocos +
  arquivos por bloco + não-mapeados.
- Edição inline kind/unit → `save_block_kind_override` / `save_block_unit_override`
  (já existem) → marca sujo → revela Reprocessar.
- Edição de escopo → `save_block_scope_override` → marca sujo → Reprocessar.
- No próximo build, `_apply_curation_overrides` + `apply_assessment_review_scope`
  aplicam os overrides (escopo manual incluso).

## Error handling

- Bloco prova/revisão sem unidades disponíveis no curso → popup de escopo mostra
  lista vazia + aviso; salvar com seleção vazia remove o override (volta ao
  derivado).
- Override de escopo só é oferecido para `kind ∈ {assessment, review}`; nas demais
  linhas a célula Escopo é read-only ("—").
- Ordenar coluna com valores ausentes (data vazia) → vão para o fim, ordem estável.
- Estados de erro de repo/build/cronograma preservados (mensagens atuais).

## Testes

- `timeline_sort_key`: ordena por data cronologicamente; `#` numérico (10 depois de
  9, não lexical); valores ausentes ao fim.
- `save_block_scope_override`: grava `manual_scope_unit_slugs` no curation; vazio/None
  remove; round-trip via `load_block_curation`.
- `curation`: `manual_scope_unit_slugs` é aceito por `set_block_override` e renomeado
  para `block_manual_scope_slugs` em `apply_block_curation`.
- `apply_assessment_review_scope` honra manual: bloco com `block_manual_scope_slugs`
  mantém esse escopo (não o derivado por data) + label "Conteúdo: …"; sem manual,
  cai no derivado (regressão dos testes atuais permanece verde).
- A view `ttk.Treeview` não roda headless → verificação manual do usuário (abrir o
  app, aba Cronograma de Métodos-Formais: ordenar colunas, editar tipo/unidade,
  editar escopo de uma prova, reprocessar).

## Fora de escopo (YAGNI)

- Busca por texto.
- Edição manual de data do bloco.
- Mesclar/dividir/reordenar blocos persistidos.
- Linha do tempo gráfica (direção rejeitada).
