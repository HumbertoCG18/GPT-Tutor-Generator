# Propagar method/confiança do match de código — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Propagar `block_match_method`/`block_match_confidence` do code_curation pro manifest (FileEntry) e exibir no editor de backlog.

**Architecture:** Dois campos novos no FileEntry; o helper único de propagação (`attach_block_rationale`, no ponto de convergência `regenerate_pedagogical_files`) é renomeado `attach_block_summary_fields` e passa a copiar os 3 campos com o mesmo anti-stale (`pop`); o editor lê do entry e mostra um campo read-only "Match do bloco". Escopo espelha o #4 (manifest + editor, não tutor).

**Tech Stack:** Python (dataclass FileEntry), tkinter (dialogs), pytest.

Spec: `docs/superpowers/specs/2026-06-11-propagar-block-match-design.md`

---

### Task 1: Campos novos no FileEntry

**Files:**
- Modify: `src/models/core.py:90` (após `computed_block_rationale`)
- Test: `tests/test_block_rationale.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar em `tests/test_block_rationale.py` (após `test_fileentry_default_rationale_not_emitted`, ~linha 22):

```python
def test_fileentry_roundtrip_preserves_match_fields():
    e = _entry(computed_block_method="consensus", computed_block_match_confidence=0.87)
    d = e.to_dict()
    assert d["computed_block_method"] == "consensus"
    assert d["computed_block_match_confidence"] == 0.87
    back = FileEntry.from_dict(d)
    assert back.computed_block_method == "consensus"
    assert back.computed_block_match_confidence == 0.87


def test_fileentry_default_match_fields_not_emitted():
    d = _entry().to_dict()
    assert "computed_block_method" not in d  # default "" não incha o manifest
    assert "computed_block_match_confidence" not in d  # default 0.0 idem
    back = FileEntry.from_dict(d)
    assert back.computed_block_method == ""
    assert back.computed_block_match_confidence == 0.0
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_block_rationale.py::test_fileentry_roundtrip_preserves_match_fields tests/test_block_rationale.py::test_fileentry_default_match_fields_not_emitted -v`
Expected: FAIL (`TypeError: __init__() got an unexpected keyword argument 'computed_block_method'`)

- [ ] **Step 3: Adicionar os campos**

Em `src/models/core.py`, após a linha 90 (`computed_block_rationale: str = ""`):

```python
    # Método e confiança do match code->bloco, do code summarizer (Gemini +
    # matcher local). Copiados de code_curation.json (summary.block_match_method
    # / block_match_confidence) na regeneração pedagógica; default vazio/0.0 para
    # entries sem summary (não-código). Distinto de computed_block_confidence
    # (acima), que é a confiança do routing determinístico.
    computed_block_method: str = ""
    computed_block_match_confidence: float = 0.0
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_block_rationale.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_block_rationale.py
git commit -m "feat(model): FileEntry computed_block_method/match_confidence"
```

---

### Task 2: Renomear e estender `attach_block_summary_fields`

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py:115-127` (função) e `:305-307` (call site)
- Test: `tests/test_block_rationale.py`

- [ ] **Step 1: Atualizar os testes (renomear import + novos casos)**

Em `tests/test_block_rationale.py`:

1. Trocar o import na linha 25 e todas as 4 chamadas `attach_block_rationale(...)` por `attach_block_summary_fields(...)`.
2. Estender o `CURATION` (linha 28) para incluir os campos de match:

```python
CURATION = {
    "entries": {
        "id-1": {"summary": {
            "match_rationale": "Demonstra recursão do bloco 3",
            "block_match_method": "consensus",
            "block_match_confidence": 0.91,
        }},
        "id-2": {"summary": {"match_rationale": "   "}},  # whitespace -> ignora
        "id-3": {},  # sem summary
    }
}
```

3. Adicionar novos testes ao final do arquivo:

```python
def test_attach_copies_match_fields_for_matching_entry():
    entries = [{"id": "id-1", "title": "a"}]
    out = attach_block_summary_fields(entries, CURATION)
    assert out[0]["computed_block_method"] == "consensus"
    assert out[0]["computed_block_match_confidence"] == 0.91


def test_attach_skips_match_fields_when_missing_summary():
    entries = [{"id": "id-2"}, {"id": "id-3"}, {"id": "id-9"}]
    out = attach_block_summary_fields(entries, CURATION)
    for e in out:
        assert "computed_block_method" not in e
        assert "computed_block_match_confidence" not in e


def test_attach_removes_stale_match_fields():
    entries = [{"id": "id-9", "computed_block_method": "orphan",
                "computed_block_match_confidence": 0.4}]
    out = attach_block_summary_fields(entries, CURATION)
    assert "computed_block_method" not in out[0]
    assert "computed_block_match_confidence" not in out[0]


def test_attach_drops_nonnumeric_match_confidence():
    curation = {"entries": {"id-1": {"summary": {"block_match_confidence": "abc"}}}}
    entries = [{"id": "id-1", "computed_block_match_confidence": 0.5}]
    out = attach_block_summary_fields(entries, curation)
    assert "computed_block_match_confidence" not in out[0]
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_block_rationale.py -v`
Expected: FAIL (`ImportError: cannot import name 'attach_block_summary_fields'`)

- [ ] **Step 3: Renomear e estender a função**

Em `src/builder/ops/pedagogical_regeneration.py`, substituir a função `attach_block_rationale` (linhas 115-127) por:

```python
def attach_block_summary_fields(entries: list, code_curation: dict) -> list:
    """Sincroniza campos do code_curation (summary.*) com o entry dict:
    match_rationale -> computed_block_rationale,
    block_match_method -> computed_block_method,
    block_match_confidence -> computed_block_match_confidence.
    Sem valor na curation, remove o campo — evita dado stale após
    prune/reatribuição."""
    curation_entries = (code_curation or {}).get("entries", {})
    for e in entries:
        rec = curation_entries.get(str(e.get("id") or "")) or {}
        summary = rec.get("summary") or {}

        rationale = str(summary.get("match_rationale") or "").strip()
        if rationale:
            e["computed_block_rationale"] = rationale
        else:
            e.pop("computed_block_rationale", None)

        method = str(summary.get("block_match_method") or "").strip()
        if method:
            e["computed_block_method"] = method
        else:
            e.pop("computed_block_method", None)

        conf = summary.get("block_match_confidence")
        if conf is not None:
            try:
                e["computed_block_match_confidence"] = float(conf)
            except (TypeError, ValueError):
                e.pop("computed_block_match_confidence", None)
        else:
            e.pop("computed_block_match_confidence", None)

    return entries
```

- [ ] **Step 4: Atualizar o call site**

Em `src/builder/ops/pedagogical_regeneration.py:305`, trocar:

```python
    live_manifest_entries = attach_block_rationale(
        live_manifest_entries, builder._load_code_curation()
    )
```

por:

```python
    live_manifest_entries = attach_block_summary_fields(
        live_manifest_entries, builder._load_code_curation()
    )
```

- [ ] **Step 5: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_block_rationale.py -v`
Expected: PASS (todos)

- [ ] **Step 6: Confirmar nenhuma referência órfã ao nome antigo**

Run: `python -m pytest -q && git grep -n "attach_block_rationale" -- "*.py"`
Expected: pytest PASS; grep não retorna nada em `.py` (só specs/plans antigos em docs).

- [ ] **Step 7: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py tests/test_block_rationale.py
git commit -m "feat(build): attach_block_summary_fields propaga method/confiança do match"
```

---

### Task 3: Campo "Match do bloco" no editor de backlog

**Files:**
- Modify: `src/ui/dialogs.py:2299` (inserir antes de `row_unit = row_rationale + 1`)

- [ ] **Step 1: Inserir o campo read-only**

Em `src/ui/dialogs.py`, logo após o bloco do "Por que este bloco?" (que termina na linha 2297 com o `add_tooltip(lbl_rationale, ...)`) e ANTES de `row_unit = row_rationale + 1` (linha 2299), inserir:

```python
        row_match = row_rationale + 1
        _bm_method = str(self._data.get("computed_block_method") or "").strip()
        if _bm_method:
            _bm_conf = self._data.get("computed_block_match_confidence") or 0.0
            try:
                _bm_text = f"método: {_bm_method} · confiança: {float(_bm_conf):.2f}"
            except (TypeError, ValueError):
                _bm_text = f"método: {_bm_method}"
        else:
            _bm_text = "—"
        lbl_match = tk.Label(tab_edit, text="Match do bloco", bg=p["bg"], fg=p["fg"],
                             font=("Segoe UI", 10))
        lbl_match.grid(row=row_match, column=0, sticky="w", padx=(0, 12), pady=6)
        tk.Label(tab_edit, text=_bm_text, bg=p["bg"], fg=p["muted"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(
            row=row_match, column=1, sticky="w", pady=6)
        add_tooltip(lbl_match,
            "Como o bloco do cronograma foi escolhido para este código:\n"
            "consensus = Gemini e matcher local concordam; llm_only = só o Gemini;\n"
            "auto_concept = fallback por conceito; orphan = sem bloco.\n"
            "'—' quando não há summary (arquivo não-código).",
        )

```

- [ ] **Step 2: Ajustar a linha do `row_unit` para encadear relativo**

Logo abaixo do bloco inserido, a linha existente:

```python
        row_unit = row_rationale + 1
```

passa a:

```python
        row_unit = row_match + 1
```

- [ ] **Step 3: Verificar grid sem colisão e import compila**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py', encoding='utf-8').read())"`
Expected: sem erro (sintaxe ok).

Verificação manual: `row_origem` < `row_rationale` < `row_match` < `row_unit` < `row_unit_status` < `row_subunit` — cada um = anterior + 1, sem (row,column) duplicado.

- [ ] **Step 4: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS (sem regressão; widgets tkinter não são unit-testados).

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): campo read-only 'Match do bloco' no editor de backlog"
```

---

## Self-Review

- **Spec coverage:** Task 1 = §1 (FileEntry); Task 2 = §2 (rename+extend+call site) + §Testes; Task 3 = §3 (editor). Escopo §"espelha o #4" respeitado (sem tutor/FILE_MAP/CODE_INDEX). Não-objetivos respeitados (produtor intocado).
- **Placeholder scan:** sem TBD/TODO; todo código completo.
- **Type consistency:** `computed_block_method: str`, `computed_block_match_confidence: float` consistentes nas 3 tasks; função `attach_block_summary_fields` mesma assinatura `(entries, code_curation)` do antigo. `.2f` formato consistente com a spec.
