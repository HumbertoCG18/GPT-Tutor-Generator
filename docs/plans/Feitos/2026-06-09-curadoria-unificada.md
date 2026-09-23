# Curadoria Unificada Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the separate `Image Curator` and `Curator Studio` entry points with one `Curadoria` window that opens on `Revisao Manual` and lazy-loads `Imagens`.

**Architecture:** Extract each existing `tk.Toplevel` curator into an embeddable `ttk.Frame` panel, keep thin standalone wrappers for compatibility, and add `CurationWorkspace(tk.Toplevel)` as the new composed window. The workspace instantiates the manual-review panel immediately and only creates the image panel after the `Imagens` tab is selected.

**Tech Stack:** Python, Tkinter/ttk, existing `src/ui` modules, pytest static/helper tests.

---

## File Structure

- Create `src/ui/curation_workspace.py`: owns the new top-level curation window and lazy image-tab loading.
- Modify `src/ui/curator_studio.py`: extract `CuratorStudioPanel(ttk.Frame)` and keep `CuratorStudio(tk.Toplevel)` as a thin wrapper.
- Modify `src/ui/image_curator.py`: extract `ImageCuratorPanel(ttk.Frame)` and keep `ImageCurator(tk.Toplevel)` as a thin wrapper.
- Modify `src/ui/app.py`: replace the two toolbar buttons and open methods with `open_curation_workspace`.
- Modify `src/ui/dialogs.py`: update help text that tells users to open `Curator Studio`.
- Modify `tests/test_ui_queue_dashboard.py`: add static tests for the single toolbar entry and workspace lazy markers.
- Run existing `tests/test_image_curation.py` to catch helper regressions.

---

### Task 1: Add Static Tests for the New UI Contract

**Files:**
- Modify: `tests/test_ui_queue_dashboard.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Add failing source-level tests**

Append these tests near the existing source-text cleanup tests:

```python
def test_app_declares_single_curation_workspace_entry():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "open_curation_workspace" in text
    assert "open_image_curator" not in text
    assert "open_curator_studio" not in text
    assert 'text="🧰 Curadoria"' in text
    assert 'text="🖼 Image Curator"' not in text
    assert 'text="🖌 Curator Studio"' not in text


def test_curation_workspace_lazy_load_contract_is_declared():
    text = Path("src/ui/curation_workspace.py").read_text(encoding="utf-8")
    assert "class CurationWorkspace" in text
    assert "self._image_panel = None" in text
    assert "def _ensure_image_panel" in text
    assert "ImageCuratorPanel" in text
    assert "CuratorStudioPanel" in text


def test_help_text_points_to_unified_curation_workspace():
    joined = "\n".join(body for _title, body in HELP_SECTIONS)
    assert "Curadoria > Revisão Manual" in joined
    assert 'Clique em "🖌 Curator Studio"' not in joined
```

- [ ] **Step 2: Run the failing tests**

Run:

```powershell
python -m pytest tests/test_ui_queue_dashboard.py -q
```

Expected: failure because `src/ui/curation_workspace.py` does not exist and `app.py` still declares the two old buttons/methods.

- [ ] **Step 3: Commit only if this task is executed separately**

This task can be committed with the implementation task if the red phase is not committed in this repository.

---

### Task 2: Extract `CuratorStudioPanel`

**Files:**
- Modify: `src/ui/curator_studio.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Convert the existing class body into a panel**

Change the class declaration and constructor shape:

```python
class CuratorStudioPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        repo_dir: str,
        theme_mgr,
        *,
        app_parent=None,
        bind_target=None,
        apply_theme: bool = True,
        title_text: str = "🖌 Curator Studio",
    ):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._app_parent = app_parent if app_parent is not None else parent
        self._bind_target = bind_target if bind_target is not None else self
        self._title_text = title_text
        self._theme_name = (
            self._app_parent.config_obj.get("theme")
            if hasattr(self._app_parent, "config_obj")
            else "dark"
        )
        if apply_theme:
            self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_files()
        self.bind("<Configure>", self._on_layout_change)
        self.after_idle(self._apply_responsive_layout)
```

Keep the existing migration call and state initialization inside this constructor before `_build_ui()`.

- [ ] **Step 2: Replace window-only dependencies**

Use `self._app_parent` instead of `self.master` in `_repo_course_meta()` and the rejection sync block. Use `self._bind_target.bind("<Control-s>", ...)` instead of `self.bind("<Control-s>", ...)`. Use `self._title_text` in the toolbar label instead of the hard-coded `🖌 Curator Studio`.

- [ ] **Step 3: Add the thin standalone wrapper**

Place this after `CuratorStudioPanel`:

```python
class CuratorStudio(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.title("Curator Studio")
        self.geometry("1600x900")
        self.minsize(1100, 650)
        panel = CuratorStudioPanel(
            self,
            repo_dir,
            theme_mgr,
            app_parent=parent,
            bind_target=self,
            apply_theme=True,
        )
        panel.pack(fill="both", expand=True)
        self.panel = panel
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/test_ui_queue_dashboard.py::test_curator_studio_layout_mode_changes_by_width tests/test_ui_queue_dashboard.py::test_curator_review_paths_excludes_code_manual_review tests/test_ui_queue_dashboard.py::test_curator_review_paths_excludes_legacy_url_fetcher_reviews_in_pdfs -q
```

Expected: PASS.

---

### Task 3: Extract `ImageCuratorPanel`

**Files:**
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Convert the existing class body into a panel**

Change the class declaration and constructor shape:

```python
class ImageCuratorPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        repo_dir: str,
        theme_mgr,
        *,
        app_parent=None,
        bind_target=None,
        apply_theme: bool = True,
        title_text: str = "Image Curator",
    ):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._app_parent = app_parent if app_parent is not None else parent
        self._bind_target = bind_target if bind_target is not None else self
        self._title_text = title_text
        self._theme_name = (
            self._app_parent.config_obj.get("theme")
            if hasattr(self._app_parent, "config_obj")
            else "dark"
        )
        self._parent = self._app_parent
        self._image_description_source = (
            self._app_parent.config_obj.get("image_description_source", "ollama")
            if hasattr(self._app_parent, "config_obj")
            else "ollama"
        )
        if apply_theme:
            self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_manifest()
        self._bind_target.bind("<Delete>", self._on_delete_key)
        self.bind("<Configure>", self._on_layout_change)
        self.after_idle(self._apply_responsive_layout)
```

Keep the existing state initialization between `_image_description_source` and `apply_theme`.

- [ ] **Step 2: Replace the toolbar title**

Use `self._title_text` in the top toolbar label instead of hard-coded `Image Curator`.

- [ ] **Step 3: Add the thin standalone wrapper**

Place this after `ImageCuratorPanel`:

```python
class ImageCurator(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.title("Image Curator")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        panel = ImageCuratorPanel(
            self,
            repo_dir,
            theme_mgr,
            app_parent=parent,
            bind_target=self,
            apply_theme=True,
        )
        panel.pack(fill="both", expand=True)
        self.panel = panel
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/test_image_curation.py::test_image_curator_layout_mode_changes_by_width tests/test_image_curation.py::test_image_types_include_latex_extraction -q
```

Expected: PASS.

---

### Task 4: Add `CurationWorkspace`

**Files:**
- Create: `src/ui/curation_workspace.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Create the workspace module**

Create:

```python
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.ui.curator_studio import CuratorStudioPanel
from src.ui.image_curator import ImageCuratorPanel


MANUAL_REVIEW_TAB = "Revisão Manual"
IMAGES_TAB = "Imagens"


class CurationWorkspace(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._app_parent = parent
        self._theme_name = (
            parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"
        )
        self._image_panel = None

        self.title("Curadoria")
        self.geometry("1600x900")
        self.minsize(1100, 650)
        self.theme_mgr.apply(self, self._theme_name)

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)

        self._manual_tab = ttk.Frame(self._notebook)
        self._images_tab = ttk.Frame(self._notebook)
        self._notebook.add(self._manual_tab, text=MANUAL_REVIEW_TAB)
        self._notebook.add(self._images_tab, text=IMAGES_TAB)

        self._manual_panel = CuratorStudioPanel(
            self._manual_tab,
            str(self.repo_dir),
            self.theme_mgr,
            app_parent=self._app_parent,
            bind_target=self,
            apply_theme=False,
            title_text="Revisão Manual",
        )
        self._manual_panel.pack(fill="both", expand=True)

        self._build_images_placeholder()
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_images_placeholder(self) -> None:
        placeholder = ttk.Frame(self._images_tab)
        placeholder.pack(fill="both", expand=True)
        ttk.Label(
            placeholder,
            text="A curadoria de imagens será carregada quando esta aba for aberta.",
        ).pack(anchor="center", expand=True)
        self._images_placeholder = placeholder

    def _on_tab_changed(self, _event=None) -> None:
        selected = self._notebook.select()
        if selected and self._notebook.tab(selected, "text") == IMAGES_TAB:
            self._ensure_image_panel()

    def _ensure_image_panel(self):
        if self._image_panel is not None:
            return self._image_panel
        self._images_placeholder.destroy()
        self._image_panel = ImageCuratorPanel(
            self._images_tab,
            str(self.repo_dir),
            self.theme_mgr,
            app_parent=self._app_parent,
            bind_target=self,
            apply_theme=False,
            title_text="Imagens",
        )
        self._image_panel.pack(fill="both", expand=True)
        return self._image_panel
```

- [ ] **Step 2: Run the workspace source test**

Run:

```powershell
python -m pytest tests/test_ui_queue_dashboard.py::test_curation_workspace_lazy_load_contract_is_declared -q
```

Expected: PASS after Task 1 test exists.

---

### Task 5: Wire the App Toolbar and Clean Old Open Methods

**Files:**
- Modify: `src/ui/app.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Replace toolbar buttons**

Replace the two old tool buttons with:

```python
ttk.Button(tool_actions, text="🧰 Curadoria", command=self.open_curation_workspace).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
```

Keep `Configurações`, `Ajuda`, and the shutdown checkbox on their current rows.

- [ ] **Step 2: Replace open methods**

Remove `open_curator_studio()` and `open_image_curator()`. Add:

```python
def open_curation_workspace(self):
    repo_dir = self._repo_dir()
    if not repo_dir:
        messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para abrir a Curadoria.")
        return

    from src.ui.curation_workspace import CurationWorkspace
    CurationWorkspace(self, str(repo_dir), self.theme_mgr)
```

- [ ] **Step 3: Run app source contract test**

Run:

```powershell
python -m pytest tests/test_ui_queue_dashboard.py::test_app_declares_single_curation_workspace_entry -q
```

Expected: PASS.

---

### Task 6: Update Help Text and Cleanup References

**Files:**
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Update user-facing instructions**

Replace instructional references like `Clique em "🖌 Curator Studio"` with `Clique em "🧰 Curadoria" e abra a aba "Revisão Manual"`. Replace shortcut/help references to say `Ctrl+S salva na aba Revisão Manual da Curadoria`.

- [ ] **Step 2: Keep internal historical comments only if not user-facing**

Do not rewrite backend comments that merely explain generated artifacts from the old feature name unless they become misleading UI instructions.

- [ ] **Step 3: Run help text test**

Run:

```powershell
python -m pytest tests/test_ui_queue_dashboard.py::test_help_text_points_to_unified_curation_workspace -q
```

Expected: PASS.

---

### Task 7: Full Verification and Scaffold Growth

**Files:**
- Modify if needed: `.mex/ROUTER.md`
- Test: `tests/test_image_curation.py`, `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Run targeted verification**

Run:

```powershell
python -m pytest tests/test_image_curation.py tests/test_ui_queue_dashboard.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full tests if imports or initialization are unstable**

Run when targeted tests reveal import side effects or when the panel split touched shared startup paths:

```powershell
python -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 3: Update MEX current project state**

If implementation is complete, add one bullet to `.mex/ROUTER.md` Current Project State:

```markdown
- Curadoria unificada na UI: um botão `Curadoria` abre workspace com abas
  `Revisão Manual` e `Imagens`; revisão manual abre primeiro e o painel de
  imagens é lazy-loaded ao selecionar a aba.
```

- [ ] **Step 4: Commit implementation**

Run:

```powershell
git add src/ui/app.py src/ui/curation_workspace.py src/ui/curator_studio.py src/ui/image_curator.py src/ui/dialogs.py tests/test_ui_queue_dashboard.py .mex/ROUTER.md docs/superpowers/plans/2026-06-09-curadoria-unificada.md
git commit -m "Unify curation tools in tabbed workspace"
```
