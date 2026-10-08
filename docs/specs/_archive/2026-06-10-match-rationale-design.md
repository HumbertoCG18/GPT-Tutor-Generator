# Propagar match_rationale — Design

> Roadmap #4: levar a justificativa do Gemini ("por que este código foi
> atribuído a este bloco") do cache `.code_curation.json` até o curador.

**Data:** 2026-06-10
**Branch:** new-features

## Objetivo

Hoje o `match_rationale` (campo do schema `CodeSummary`, gerado pelo Gemini
em `src/builder/core/code_summarization.py:51-54`) morre em
`.code_curation.json` — nunca chega ao `manifest.json` nem à UI. O curador
não tem como saber POR QUE um código foi atribuído a um bloco.

**Escopo desta entrega:** manifest + editor de backlog (read-only).
**Fora de escopo (YAGNI):** coluna no CODE_INDEX.md (token budget do tutor;
o índice já agrupa por bloco), FILE_MAP, cronograma detalhado, e reconciliar
`computed_block_id` × `primary_block_id` (concern separado).

## Arquitetura e fluxo

```
code_summarization (Gemini) → .code_curation.json
    entries[<id>].summary.match_rationale  ("1 frase: por que este bloco")
                          │
                          ▼
regenerate_pedagogical_files  (ÚNICO ponto: build completo E incremental
                               passam aqui — build_workflow.py:122)
    após resolve_unit_block_tags (linha ~285), antes de
    manifest["entries"] = live_manifest_entries (linha ~290):
    attach_block_rationale(entries, builder._load_code_curation())
       → entry["computed_block_rationale"] = summary["match_rationale"]
                          │
                          ▼
manifest.json (FileEntry.computed_block_rationale)
                          │
                          ▼
BacklogEntryEditDialog → campo read-only "Por que este bloco? (Gemini)"
```

Decisões:

- **Um único ponto de cópia.** Os dois caminhos de build convergem em
  `regenerate_pedagogical_files`. O helper roda DEPOIS do
  `resolve_unit_block_tags_fn` (que reconstrói os entries) — assim o campo
  não é perdido pelo enriquecimento.
- **Sem acoplamento novo:** `content_taxonomy` não passa a conhecer
  `code_curation`. O helper é função separada que recebe ambos como dados.
- O rationale explica a sugestão de bloco do *code-summarizer* Gemini
  (par do `primary_block_id` no summary). O label da UI deixa isso explícito.
- Entries não-código não têm summary no curation → campo fica `""`
  (default do dataclass; `to_dict` nem o emite — manifest não incha).

## Componentes

### 1. `src/models/core.py` — campo novo no FileEntry

Após `computed_block_band` (~linha 86):

```python
    # Justificativa do Gemini (code summarizer) para a escolha de bloco.
    # Copiada de .code_curation.json (summary.match_rationale) na regeneração
    # pedagógica; "" para entries sem summary (não-código).
    computed_block_rationale: str = ""
```

Round-trip já coberto: `to_dict` só emite não-default; `from_dict` filtra
por campos do dataclass.

### 2. Helper `attach_block_rationale(entries, code_curation) -> list`

Em `src/builder/ops/pedagogical_regeneration.py` (módulo já orquestra a
regeneração; função pura no nível do módulo):

```python
def attach_block_rationale(entries: list, code_curation: dict) -> list:
    """Copia summary.match_rationale do code_curation pro entry dict
    (computed_block_rationale). Entries sem summary/rationale ficam intactos."""
    curation_entries = (code_curation or {}).get("entries", {})
    for e in entries:
        rec = curation_entries.get(str(e.get("id") or "")) or {}
        rationale = str(((rec.get("summary") or {}).get("match_rationale")) or "").strip()
        if rationale:
            e["computed_block_rationale"] = rationale
    return entries
```

Mutação in-place + retorno da lista (mesmo padrão de `run_material_residual`).

### 3. Chamada em `regenerate_pedagogical_files`

Entre `run_material_residual` (linha ~288) e `manifest["entries"] = ...`
(linha ~290):

```python
    live_manifest_entries = attach_block_rationale(
        live_manifest_entries, builder._load_code_curation()
    )
```

`builder._load_code_curation()` já existe (engine) e retorna `{}` defensivo.

### 4. `src/ui/dialogs.py` — BacklogEntryEditDialog

Logo após o bloco "Seção de origem" (~linha 2266), mesmo padrão visual
(label coluna 0 + valor read-only coluna 1 + tooltip):

```python
        row_rationale = row_origem + 1
        _rationale = str(self._data.get("computed_block_rationale") or "").strip() or "—"
        lbl_rationale = tk.Label(tab_edit, text="Por que este bloco?", bg=p["bg"], fg=p["fg"],
                                 font=("Segoe UI", 10))
        lbl_rationale.grid(row=row_rationale, column=0, sticky="w", padx=(0, 12), pady=6)
        tk.Label(tab_edit, text=_rationale, bg=p["bg"], fg=p["muted"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(
            row=row_rationale, column=1, sticky="w", pady=6)
        add_tooltip(lbl_rationale,
            "Justificativa automática do Gemini (resumo de código) para a\n"
            "atribuição deste arquivo a um bloco do cronograma.\n"
            "'—' quando não há resumo (arquivo não-código ou sem Gemini).",
        )
```

Layout do grid: rows são relativos encadeados (`row_origem = row_tags + 1`,
`row_unit = row_origem + 1`, ...). Inserir o bloco novo com
`row_rationale = row_origem + 1` e mudar a linha seguinte (dialogs.py:2268)
de `row_unit = row_origem + 1` para `row_unit = row_rationale + 1` — os rows
subsequentes encadeiam sozinhos.

## Tratamento de erros / bordas

- `code_curation` vazio/None → helper no-op.
- Entry sem id ou id não presente no curation → intacto.
- `match_rationale` vazio/whitespace → não grava (fica default `""`).
- Manifests antigos (sem o campo) → `from_dict` aplica default `""`; dialog
  mostra "—".

## Testes

Em `tests/test_core.py` (ou arquivo novo `tests/test_block_rationale.py`):

- **Round-trip FileEntry:** `FileEntry(computed_block_rationale="x").to_dict()`
  contém o campo; `from_dict` o restaura; default `""` não é emitido por
  `to_dict`.
- **attach_block_rationale:**
  - copia quando summary tem `match_rationale` não-vazio;
  - entry sem registro no curation fica sem o campo;
  - rationale vazio/whitespace → não grava;
  - `code_curation=None`/`{}` → lista retorna inalterada.

Dialog: sem teste unitário (UI tkinter); verificação manual.
