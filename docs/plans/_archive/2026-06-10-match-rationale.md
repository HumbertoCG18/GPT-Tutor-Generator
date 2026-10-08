# Propagar match_rationale (#4) + limpeza de mortos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Propagar a justificativa do Gemini (`match_rationale`) do `.code_curation.json` para o `manifest.json` e exibi-la read-only no editor de backlog; aproveitar para remover código morto confirmado e deduplicar `_normalized_source_key`.

**Architecture:** Campo novo `computed_block_rationale` no FileEntry; helper puro `attach_block_rationale` roda no único ponto de convergência dos dois caminhos de build (`regenerate_pedagogical_files`); UI lê do entry do manifest (padrão "Seção de origem").

**Tech Stack:** Python 3, pytest, tkinter. Sem libs novas.

**Spec:** `docs/superpowers/specs/2026-06-10-match-rationale-design.md`

---

### Task 1: Campo `computed_block_rationale` no FileEntry

**Files:**
- Modify: `src/models/core.py:86` (após `computed_block_band`)
- Test: `tests/test_block_rationale.py` (novo)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_block_rationale.py`:

```python
"""Propagação do match_rationale (Gemini) pro manifest + FileEntry."""

from src.models.core import FileEntry


def _entry(**kw):
    base = dict(source_path="C:/x/a.py", file_type="code", category="codigo-professor")
    base.update(kw)
    return FileEntry(**base)


def test_fileentry_roundtrip_preserves_rationale():
    e = _entry(computed_block_rationale="Usa listas e loops do bloco 5")
    d = e.to_dict()
    assert d["computed_block_rationale"] == "Usa listas e loops do bloco 5"
    assert FileEntry.from_dict(d).computed_block_rationale == "Usa listas e loops do bloco 5"


def test_fileentry_default_rationale_not_emitted():
    d = _entry().to_dict()
    assert "computed_block_rationale" not in d  # default "" não incha o manifest
    assert FileEntry.from_dict(d).computed_block_rationale == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_block_rationale.py -q`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'computed_block_rationale'`

- [ ] **Step 3: Add the field**

In `src/models/core.py`, after `computed_block_band: str = ""` (line 86) and before the `source_section` comment block (line ~87), add:

```python
    # Justificativa do Gemini (code summarizer) para a escolha de bloco.
    # Copiada de .code_curation.json (summary.match_rationale) na regeneração
    # pedagógica; "" para entries sem summary (não-código).
    computed_block_rationale: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_block_rationale.py -q`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_block_rationale.py
git commit -m "feat(models): campo computed_block_rationale no FileEntry"
```

---

### Task 2: `attach_block_rationale` + chamada na regeneração

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (função nova module-level + chamada ~linha 288-290)
- Test: `tests/test_block_rationale.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_block_rationale.py`:

```python
from src.builder.ops.pedagogical_regeneration import attach_block_rationale


CURATION = {
    "entries": {
        "id-1": {"summary": {"match_rationale": "Demonstra recursão do bloco 3"}},
        "id-2": {"summary": {"match_rationale": "   "}},  # whitespace -> ignora
        "id-3": {},  # sem summary
    }
}


def test_attach_copies_rationale_for_matching_entry():
    entries = [{"id": "id-1", "title": "a"}]
    out = attach_block_rationale(entries, CURATION)
    assert out[0]["computed_block_rationale"] == "Demonstra recursão do bloco 3"


def test_attach_skips_blank_rationale_and_missing_summary():
    entries = [{"id": "id-2"}, {"id": "id-3"}, {"id": "id-9"}, {"title": "sem id"}]
    out = attach_block_rationale(entries, CURATION)
    for e in out:
        assert "computed_block_rationale" not in e


def test_attach_tolerates_empty_curation():
    entries = [{"id": "id-1"}]
    assert attach_block_rationale(entries, {}) == [{"id": "id-1"}]
    assert attach_block_rationale(entries, None) == [{"id": "id-1"}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_block_rationale.py -q`
Expected: FAIL with `ImportError: cannot import name 'attach_block_rationale'`

- [ ] **Step 3: Implement the helper**

In `src/builder/ops/pedagogical_regeneration.py`, add at module level (after `run_material_residual`, before `def regenerate_pedagogical_files`):

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

- [ ] **Step 4: Wire the call**

In `regenerate_pedagogical_files`, between `live_manifest_entries = run_material_residual(builder, live_manifest_entries)` (~line 288) and `manifest["entries"] = live_manifest_entries` (~line 290), add:

```python
    live_manifest_entries = attach_block_rationale(
        live_manifest_entries, builder._load_code_curation()
    )
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_block_rationale.py "tests/test_core.py" -k "rationale or incremental" -q`
Expected: PASS (5 rationale tests + incremental integration still green)

- [ ] **Step 6: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py tests/test_block_rationale.py
git commit -m "feat(build): attach_block_rationale copia match_rationale pro manifest"
```

---

### Task 3: Campo read-only no BacklogEntryEditDialog

**Files:**
- Modify: `src/ui/dialogs.py:2254-2268`

- [ ] **Step 1: Insert the field**

In `src/ui/dialogs.py`, the "Seção de origem" block ends at line 2266 (the `add_tooltip(lbl_origem, ...)` call) and line 2268 currently reads `row_unit = row_origem + 1`. Insert BETWEEN them:

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

And change line 2268 from `row_unit = row_origem + 1` to:

```python
        row_unit = row_rationale + 1
```

(Rows are chained relative — `row_unit`, and everything after it, shifts automatically.)

- [ ] **Step 2: Verify the file parses and the UI suite passes**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py', encoding='utf-8').read())"`
Expected: no output (parses).

Run: `python -m pytest -q`
Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): campo read-only 'Por que este bloco?' no editor de backlog"
```

---

### Task 4: Limpeza — código morto confirmado + dedup `_normalized_source_key`

**Files:**
- Modify: `src/utils/helpers.py` (remove `file_size_mb:355`; add `normalized_source_key`)
- Modify: `src/builder/timeline/card_block.py:130-136` (remove `save_card_block_map`)
- Modify: `src/builder/timeline/unit_matcher.py:58-60` (remove `score_block_unit_affinity`)
- Modify: `src/ui/theme.py:102` (remove `"font_size": 10,` from DEFAULTS)
- Modify: `src/ui/app.py:43-...` e `src/ui/repo_dashboard.py:13-23` (import from helpers)
- Modify: `tests/test_core.py` (remove `file_size_mb` import line 80 + test class ~2102-2112)
- Modify: `tests/test_card_block.py` (remove `save_card_block_map` import/test ~40-48)
- Modify: `tests/test_unit_matcher.py` (remove `score_block_unit_affinity` import/tests, lines 6, 26, 31, 36, 42 — keep `assign_units_positional` tests)

Todos os 3 mortos foram confirmados por busca de referências (única referência fora da definição = testes). `font_size` nunca é lido. `_normalized_source_key` é **idêntica** em app.py e repo_dashboard.py.

- [ ] **Step 1: Add the shared helper (TDD)**

Append test to `tests/test_block_rationale.py`? NO — separate concern. Create `tests/test_normalized_source_key.py`:

```python
"""normalized_source_key: chave canônica de source_path (dedup de UI)."""

from src.utils.helpers import normalized_source_key


def test_url_passthrough_casefolded():
    assert normalized_source_key("HTTPS://Ex.com/A") == "https://ex.com/a"


def test_empty():
    assert normalized_source_key("") == ""
    assert normalized_source_key(None) == ""


def test_path_normalized_forward_slashes_casefold():
    out = normalized_source_key("C:\\Foo\\..\\Foo\\Bar.PDF")
    assert "\\" not in out
    assert out == out.casefold()
    assert out.endswith("foo/bar.pdf")
```

Run: `python -m pytest tests/test_normalized_source_key.py -q` → FAIL (ImportError).

- [ ] **Step 2: Move the function to helpers**

In `src/utils/helpers.py`, add (public name, same body as the UI copies):

```python
def normalized_source_key(raw_path: str) -> str:
    """Chave canônica de um source_path para dedup: URLs casefold;
    paths locais resolvidos, barras normalizadas, casefold."""
    value = str(raw_path or "").strip()
    if not value:
        return ""
    if "://" in value:
        return value.casefold()
    try:
        normalized = Path(value).expanduser().resolve()
    except Exception:
        normalized = Path(value).expanduser()
    return str(normalized).replace("\\", "/").casefold()
```

Run: `python -m pytest tests/test_normalized_source_key.py -q` → PASS (3 tests).

- [ ] **Step 3: Point the two UI copies at the helper**

In `src/ui/app.py`: delete the local `def _normalized_source_key(...)` (lines 43-...; same body as above) and add to the existing `from src.utils.helpers import ...` import (or a new import line):

```python
from src.utils.helpers import normalized_source_key as _normalized_source_key
```

In `src/ui/repo_dashboard.py`: delete the local def (lines 13-23) and add:

```python
from src.utils.helpers import normalized_source_key as _normalized_source_key
```

(All call sites keep using `_normalized_source_key` — no other edits.)

- [ ] **Step 4: Remove the dead functions and their test-only references**

1. `src/utils/helpers.py`: delete `def file_size_mb(...)` (line ~355, whole function).
   `tests/test_core.py`: remove `file_size_mb,` from the import list (line 80) and delete the test block around lines 2102-2112 (comment `# file_size_mb` + the test(s) asserting it).
2. `src/builder/timeline/card_block.py`: delete `def save_card_block_map(...)` (lines 130-136).
   `tests/test_card_block.py`: remove `save_card_block_map` from the import (line 40) and delete the test that calls it (line ~48 — read the test and remove the whole test function, keeping tests for `load_card_block_map`/`lookup_card_blocks`).
3. `src/builder/timeline/unit_matcher.py`: delete `def score_block_unit_affinity(...)` (lines 58-60). The private `_block_tokens`/`_unit_tokens` STAY (used by `assign_units_positional`).
   `tests/test_unit_matcher.py`: remove the import (line 6) and the test functions that call it (asserts at lines 26, 31, 36, 42 — delete those whole test functions). Keep all `assign_units_positional` tests.
4. `src/ui/theme.py`: delete the line `"font_size": 10,` (line 102). Config loading merges saved JSON over DEFAULTS, so stale `font_size` keys in `~/.gpt_tutor_config.json` are harmless extras — verify by reading how AppConfig loads (search `DEFAULTS` usage in theme.py); if loading does strict key validation against DEFAULTS, leave `font_size` in place and report DONE_WITH_CONCERNS instead.

- [ ] **Step 5: Full suite**

Run: `python -m pytest -q`
Expected: all PASS (count drops slightly — removed dead-API tests).

Also: `python -c "import ast,glob; [ast.parse(open(f,encoding='utf-8').read()) for f in ['src/ui/app.py','src/ui/repo_dashboard.py','src/ui/theme.py']]"` → parses.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove código morto (file_size_mb, save_card_block_map, score_block_unit_affinity, font_size) e deduplica normalized_source_key"
```

---

## Final verification

- [ ] `python -m pytest -q` — all green.
- [ ] Atualizar `docs/reports/2026-06-09-relatorio-sistema.html`: #4 feito; #3 parcialmente feito (mortos removidos); seção 4 (código morto/duplicatas) — marcar itens resolvidos; quick-win `_normalized_source_key` resolvido.
