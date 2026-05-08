# Design: Campo de Subunidade Manual no Editor do Backlog

**Data:** 2026-05-08  
**Branch:** new-features  
**Escopo:** `src/builder/extraction/content_taxonomy.py`, `src/ui/dialogs.py`

---

## Contexto

A subunidade de cada arquivo é inferida automaticamente por `resolve_unit_block_tags()` via `auto_map_entry_subtopic_fn`. O resultado é gravado em `auto_tags` como `subunit:<slug>`. Não existe campo de override manual: arquivos com `topic_confidence < 0.60` ficam permanentemente sem tag de subunidade, sem que o usuário possa intervir.

O padrão de `manual_unit_slug` (campo no manifest + combobox no editor + precedência no engine) já resolve esse tipo de problema para unidades. Esta feature aplica o mesmo padrão à subunidade.

---

## Objetivo

1. Adicionar `manual_subunit_slug` como campo editável no editor do backlog.
2. Garantir que `manual_subunit_slug`, quando preenchido, tenha precedência absoluta sobre o matcher automático em `resolve_unit_block_tags`.
3. Exibir a confiança do matcher automático no painel de status da subunidade, para que o usuário entenda por que um arquivo ficou sem tag.

---

## Arquitetura

### 1. Manifest (dados da entrada)

Novo campo opcional `manual_subunit_slug: str` em cada entrada do manifest. Semântica:
- `""` ou ausente → usar matcher automático.
- Qualquer slug não-vazio → sobrescrever o resultado do matcher com confidence=1.0.

Não há migração necessária: o campo é simplesmente ignorado quando ausente.

### 2. Engine — `content_taxonomy.py` / `resolve_unit_block_tags`

No início do loop por entry, antes de chamar `auto_map_entry_subtopic_fn`:

```python
manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
if manual_subunit:
    preferred_topic_slug = manual_subunit
    topic_confidence = 1.0
    topic_ambiguous = False
else:
    topic_match = auto_map_entry_subtopic_fn(entry, content_taxonomy, markdown_text)
    topic_confidence = topic_match.confidence
    topic_ambiguous = topic_match.ambiguous
    preferred_topic_slug = (
        topic_match.topic_slug
        if topic_match.topic_slug and not topic_match.ambiguous and topic_match.confidence >= 0.60
        else ""
    )
```

A variável `topic_confidence` e `topic_ambiguous` são usadas só internamente para montar o status no editor — não precisam ser persistidas.

### 3. UI — `dialogs.py`

#### 3a. Helper `_load_subunit_options(repo_dir)`

Nova função análoga a `_load_file_map_unit_options`. Lê o COURSE_MAP ou `subject.teaching_plan` e extrai os tópicos de todas as unidades, retornando `List[Tuple[str, str]]` com `(label_display, slug)`.

Fonte primária: `course/COURSE_MAP.md` — linhas `| Subtópico ...` ou seção de tópicos.  
Fonte secundária: `subject.teaching_plan` via `_parse_units_from_teaching_plan`.

#### 3b. Helper `_resolve_backlog_subunit_status(entry_data, repo_dir, label_by_slug)`

Análoga a `_resolve_backlog_unit_status`. Retorna dict com:
- `assigned`: label da subunidade atribuída (manual ou auto), ou "Não atribuída"
- `source`: "Manual" | "Automático (confidence X%)" | "Automático (abaixo do threshold, confidence X%)"
- `note`: observação textual sobre o estado

#### 3c. Bloco no `_build_ui`

Inserido após o `unit_frame` e antes do `timeline_frame`. Estrutura idêntica ao bloco de unidade:

```
[Label "Subunidade manual"]  [Combobox: "Automático" | tópico1 | tópico2 ...]

┌─ subunit_frame ────────────────────────────────────┐
│ Subunidade atribuída  │ <valor>                     │
│ Origem                │ <fonte>                     │
│ Observação            │ <nota>                      │
│                       │ [Aplicar subunidade] [Voltar para automático] │
│                       │ <pendência>                 │
└─────────────────────────────────────────────────────┘
```

Vars Tkinter:
- `self._manual_subunit_var`: StringVar do combobox
- `self._subunit_assigned_var`, `self._subunit_source_var`, `self._subunit_note_var`, `self._subunit_pending_var`
- `self._manual_subunit_committed`: valor salvo no momento de abertura

Callbacks:
- `_on_manual_subunit_selection_changed`: atualiza `_subunit_pending_var`
- `_apply_manual_subunit_selection`: persiste o slug, atualiza painel, limpa pendência
- `_clear_manual_subunit`: volta para automático

#### 3d. Serialização em `_on_save`

```python
result["manual_subunit_slug"] = self._manual_subunit_committed or ""
```

### 4. Numeração de rows no `_build_ui`

Inserir `row_subunit = row_unit_status + 1` e deslocar `row_timeline` para `row_subunit + 1` (atualmente `row_unit_status + 1`).

---

## Fluxo de dados

```
Usuário abre editor
  → _load_subunit_options(repo_dir) → lista de tópicos
  → _resolve_backlog_subunit_status(entry_data) → status atual

Usuário seleciona subunidade + clica "Aplicar"
  → _manual_subunit_committed = slug
  → result_data["manual_subunit_slug"] = slug (no save)

Reprocessar Repositório
  → pedagogical_regeneration → resolve_unit_block_tags
  → manual_subunit_slug presente → preferred_topic_slug = slug (confidence=1.0)
  → auto_tags recebe "subunit:<slug>"
```

---

## Casos de borda

- **Sem COURSE_MAP e sem teaching_plan**: combobox mostra só "Automático" + mensagem "Nenhum tópico disponível ainda."
- **Slug manual não existe mais no course map**: painel mostra "Subunidade atribuída: <slug> (não encontrado no catálogo atual)" em `note`.
- **Categoria excluída (cronograma/bibliografia)**: `resolve_unit_block_tags` já pula essas entradas; o campo manual é salvo mas não tem efeito, o que é aceitável.

---

## O que não muda

- `manual_tags`, `auto_tags`, `manual_unit_slug`, `manual_timeline_block_id`: sem alterações.
- Thresholds do matcher automático: sem alterações.
- Qualquer outra aba ou tela além do `BacklogEntryEditDialog`.
