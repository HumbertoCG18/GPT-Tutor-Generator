# Clareza de config na UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Comunicar na UI que as opções de vision só afetam o Image Curator (não o build) e indicar de qual fonte (matéria ativa vs global) vêm os padrões exibidos.

**Architecture:** Um helper puro testável (`default_source_label`) num módulo novo `src/ui/ui_text.py`, ligado a um label muted na janela principal (`app.py`); e tooltips/hint estáticos no SettingsDialog (`dialogs.py`). Sem tocar pipeline, comportamento de config ou vision_client.

**Tech Stack:** Python 3.13, tkinter, pytest.

**Spec:** `docs/superpowers/specs/2026-06-11-clareza-config-ui-design.md`

---

## Contexto de codebase (leia antes de começar)

- `src/ui/app.py`:
  - Vars de padrões init em `app.py:249-253` (`var_default_mode`, `var_default_ocr_language`, etc.).
  - Labels read-only dos padrões renderizados em `app.py:319-329` (LabelFrame `course`, "Modo padrão"/"OCR padrão", grid row 4).
  - Troca de matéria: `_on_subject_selected`, que seta os vars em `app.py:1388-1398` a partir de `sp` (SubjectProfile).
  - A var da matéria ativa é `self._var_active_subject` (já existe quando os labels são renderizados; o seletor de matéria é montado no header antes do LabelFrame `course`).
- `src/ui/dialogs.py` (SettingsDialog):
  - Combos vision montados num loop em `dialogs.py:369-379` (lista `vision_fields`; variável compartilhada `vcb`). Campo "Backend Vision" é o primeiro (`vision_fields[0]`).
  - `add_tooltip(widget, text, delay=600)` definido em `dialogs.py:105-107`. Já há um tooltip em `dialogs.py:386` (anexado ao último `vcb`).
  - Estilo muted disponível: `"Muted.TLabel"` (theme.py:210). Hint pequeno usa `font=("Segoe UI", 8/9)`, `wraplength`.
- Estilo de hint muted em dialogs já usado em `dialogs.py:404` como referência.
- Hook pre-commit `code-review-graph` imprime `UnicodeEncodeError` inofensivo; o commit conclui — verificar com `git log -1 --oneline`.
- Suíte ~1196 testes verde. Não quebrar.

## File Structure

- **Create** `src/ui/ui_text.py` — helper puro `default_source_label`. Responsabilidade única: gerar o texto de fonte dos padrões. Sem dependência de tkinter.
- **Create** `tests/test_ui_text.py` — testes do helper.
- **Modify** `src/ui/app.py` — importar + criar var + label muted + atualizar na troca de matéria.
- **Modify** `src/ui/dialogs.py` — tooltip no combo de backend vision + hint muted na seção vision.

---

### Task 1: Helper `default_source_label`

**Files:**
- Create: `src/ui/ui_text.py`
- Test: `tests/test_ui_text.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ui_text.py
from src.ui.ui_text import default_source_label


def test_default_source_label_with_subject():
    assert default_source_label("Cálculo I") == "Padrões da matéria «Cálculo I»"


def test_default_source_label_no_subject_sentinel():
    assert default_source_label("(nenhuma)") == "Padrões globais (Configurações)"


def test_default_source_label_empty_and_none():
    assert default_source_label("") == "Padrões globais (Configurações)"
    assert default_source_label(None) == "Padrões globais (Configurações)"


def test_default_source_label_strips_whitespace():
    assert default_source_label("  Física  ") == "Padrões da matéria «Física»"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ui_text.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.ui.ui_text'`

- [ ] **Step 3: Write the implementation**

```python
# src/ui/ui_text.py
from __future__ import annotations

NO_SUBJECT_SENTINEL = "(nenhuma)"


def default_source_label(active_subject_name: str | None) -> str:
    """Texto curto indicando de onde vêm os padrões (modo/OCR) exibidos.
    Matéria ativa → 'Padrões da matéria «<nome>»'; sem matéria → global."""
    name = (active_subject_name or "").strip()
    if not name or name == NO_SUBJECT_SENTINEL:
        return "Padrões globais (Configurações)"
    return f"Padrões da matéria «{name}»"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ui_text.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/ui/ui_text.py tests/test_ui_text.py
git commit -m "feat(ui): default_source_label helper para indicar fonte dos padroes"
```
Verifique `git log -1 --oneline` (hook UnicodeEncodeError inofensivo).

---

### Task 2: Indicador de fonte dos padrões na janela principal

**Files:**
- Modify: `src/ui/app.py` (import no topo; label em ~319-329; update em ~1388-1398)

Esta task é de UI (tkinter), validada por revisão de código; a lógica do texto já é testada na Task 1. Não há teste novo.

- [ ] **Step 1: Adicionar o import no topo de `src/ui/app.py`**

Localize o bloco de imports `from src.ui...` no topo e acrescente:
```python
from src.ui.ui_text import default_source_label
```

- [ ] **Step 2: Adicionar o label muted de fonte abaixo dos padrões**

Em `src/ui/app.py`, o bloco atual (linhas ~319-329) é:
```python
        # Row 4: Default mode + OCR
        lbl_dm = ttk.Label(course, text="Modo padrão")
        lbl_dm.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_default_mode, font=("Segoe UI", 10, "bold")).grid(row=4, column=1, sticky="w", padx=(8, 16))

        lbl_ocr = ttk.Label(course, text="OCR padrão")
        lbl_ocr.grid(row=4, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_default_ocr_language, font=("Segoe UI", 10, "bold")).grid(row=4, column=3, sticky="w", padx=(8, 0))

        course.columnconfigure(1, weight=1)
        course.columnconfigure(3, weight=1)
```
Insira, logo após o label de OCR (antes das linhas `course.columnconfigure`), o indicador de fonte:
```python
        # Row 4: Default mode + OCR
        lbl_dm = ttk.Label(course, text="Modo padrão")
        lbl_dm.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_default_mode, font=("Segoe UI", 10, "bold")).grid(row=4, column=1, sticky="w", padx=(8, 16))

        lbl_ocr = ttk.Label(course, text="OCR padrão")
        lbl_ocr.grid(row=4, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_default_ocr_language, font=("Segoe UI", 10, "bold")).grid(row=4, column=3, sticky="w", padx=(8, 0))

        # Row 5: fonte dos padrões (matéria ativa vs global)
        self.var_default_source = tk.StringVar(
            value=default_source_label(self._var_active_subject.get())
        )
        ttk.Label(course, textvariable=self.var_default_source, style="Muted.TLabel").grid(
            row=5, column=0, columnspan=4, sticky="w", pady=(2, 4))

        course.columnconfigure(1, weight=1)
        course.columnconfigure(3, weight=1)
```

- [ ] **Step 3: Atualizar o indicador na troca de matéria**

Em `src/ui/app.py`, no método `_on_subject_selected`, o bloco atual (linhas ~1393-1398) é:
```python
        self.var_default_mode.set(sp.default_mode)
        self.var_default_ocr_language.set(sp.default_ocr_lang)
        self.var_default_backend.set(getattr(sp, "default_backend", "auto") or "auto")
        self.var_default_datalab_mode.set(getattr(sp, "default_datalab_mode", "accurate") or "accurate")
```
Adicione, logo após essas linhas, a atualização do indicador:
```python
        self.var_default_mode.set(sp.default_mode)
        self.var_default_ocr_language.set(sp.default_ocr_lang)
        self.var_default_backend.set(getattr(sp, "default_backend", "auto") or "auto")
        self.var_default_datalab_mode.set(getattr(sp, "default_datalab_mode", "accurate") or "accurate")
        self.var_default_source.set(default_source_label(self._var_active_subject.get()))
```

- [ ] **Step 4: Verificar import + sem regressão**

Run: `python -c "import src.ui.app"`
Expected: importa sem erro (sem ImportError/SyntaxError).

Run: `pytest -q`
Expected: todos passam (sem regressão).

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py
git commit -m "feat(ui): indicador de fonte (materia vs global) dos padroes exibidos"
```
Verifique `git log -1 --oneline`.

---

### Task 3: Aviso de escopo das opções de vision no SettingsDialog

**Files:**
- Modify: `src/ui/dialogs.py` (~369-388)

UI estática; validada por revisão. Sem teste novo.

- [ ] **Step 1: Definir a nota de escopo e anexá-la ao combo de backend + hint visível**

Em `src/ui/dialogs.py`, o bloco atual (linhas ~369-388) é:
```python
        vision_fields = [
            ("Backend Vision", self._var_vision_backend, VISION_BACKENDS),
            ("Modelo Vision", self._var_vision_model, VISION_MODELS),
            ("Quantização", self._var_vision_quant, QUANTIZATIONS),
        ]
        for i, (label, var, vals) in enumerate(vision_fields):
            r = sep_row + 2 + i
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            state = "readonly" if label != "Modelo Vision" else "normal"
            vcb = ttk.Combobox(tab_proc, textvariable=var, values=vals, state=state, width=28)
            vcb.grid(row=r, column=1, sticky="ew")

        url_row = sep_row + 2 + len(vision_fields)
        ttk.Label(tab_proc, text="URL do Ollama").grid(
            row=url_row, column=0, sticky="w", pady=6, padx=(0, 16))
        ttk.Entry(tab_proc, textvariable=self._var_ollama_url, width=28).grid(
            row=url_row, column=1, sticky="ew")
        add_tooltip(vcb, "Para Ollama, use nomes como qwen3-vl:235b-cloud ou qwen3-vl:8b.\n"
                         "qwen3-vl:235b-cloud é o padrão para máxima qualidade visual.\n"
                         "qwen3-vl:8b é o fallback local recomendado.")
```
Substitua por (adiciona `VISION_SCOPE_NOTE`, captura o combo de backend para tooltip, e insere um hint muted abaixo da URL):
```python
        VISION_SCOPE_NOTE = (
            "Afeta apenas o Image Curator (descrição manual de imagens). "
            "O build usa as descrições geradas pelo Datalab."
        )

        vision_fields = [
            ("Backend Vision", self._var_vision_backend, VISION_BACKENDS),
            ("Modelo Vision", self._var_vision_model, VISION_MODELS),
            ("Quantização", self._var_vision_quant, QUANTIZATIONS),
        ]
        vision_backend_combo = None
        for i, (label, var, vals) in enumerate(vision_fields):
            r = sep_row + 2 + i
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            state = "readonly" if label != "Modelo Vision" else "normal"
            vcb = ttk.Combobox(tab_proc, textvariable=var, values=vals, state=state, width=28)
            vcb.grid(row=r, column=1, sticky="ew")
            if label == "Backend Vision":
                vision_backend_combo = vcb

        url_row = sep_row + 2 + len(vision_fields)
        ttk.Label(tab_proc, text="URL do Ollama").grid(
            row=url_row, column=0, sticky="w", pady=6, padx=(0, 16))
        ttk.Entry(tab_proc, textvariable=self._var_ollama_url, width=28).grid(
            row=url_row, column=1, sticky="ew")
        add_tooltip(vcb, "Para Ollama, use nomes como qwen3-vl:235b-cloud ou qwen3-vl:8b.\n"
                         "qwen3-vl:235b-cloud é o padrão para máxima qualidade visual.\n"
                         "qwen3-vl:8b é o fallback local recomendado.")
        if vision_backend_combo is not None:
            add_tooltip(vision_backend_combo, VISION_SCOPE_NOTE)
        ttk.Label(
            tab_proc,
            text=VISION_SCOPE_NOTE,
            font=("Segoe UI", 8),
            wraplength=320,
            foreground="#8aa0b8",
        ).grid(row=url_row + 1, column=0, columnspan=2, sticky="w", pady=(0, 8))
```

- [ ] **Step 2: Verificar import + sem regressão**

Run: `python -c "import src.ui.dialogs"`
Expected: importa sem erro.

Run: `pytest -q`
Expected: todos passam.

- [ ] **Step 3: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): aviso que opcoes de vision so afetam o Image Curator"
```
Verifique `git log -1 --oneline`.

---

## Pós-implementação

Após as 3 tasks + review final:
- `pytest -q` verde.
- Atualizar relatório `docs/reports/2026-06-09-relatorio-sistema.html`:
  - Seção 5: marcar item 2 (custos Datalab) e item 4 (% scaneados) como resolvidos pelo #5; marcar item 3 (vision) como resolvido aqui.
  - Seção 7 (config): atualizar linhas `vision_model_quantization`/`vision_backend` (agora comunicado na UI) e `default_mode/backend/ocr_language` (fonte agora exibida).

## Self-Review (autor do plano)

1. **Spec coverage:** Componente A (vision tooltip + hint) → Task 3. Componente B1 (helper puro) → Task 1. Componente B2 (var + label + update na troca) → Task 2. Testes do helper → Task 1. ✔
2. **Placeholder scan:** Sem TBD/TODO; cada step tem o trecho exato antes/depois e comando com saída esperada. Números de linha com "~" porque o arquivo é grande; o trecho de código citado é a âncora exata. ✔
3. **Type consistency:** `default_source_label(name)` idêntico entre Task 1 (def + testes) e Task 2 (chamadas em init e _on_subject_selected). `self.var_default_source` consistente entre Step 2 e Step 3 da Task 2. `VISION_SCOPE_NOTE` definido e usado no mesmo escopo (Task 3). ✔
