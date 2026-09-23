# Named Processing Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create/edit reusable named processing profiles (e.g. "Math" = high_fidelity + datalab + math_heavy) and apply them via a selector that fills processing defaults; each subject remembers its profile.

**Architecture:** A `ProcessingProfile` dataclass stored as a list in `settings.json` (`processing_profiles`). Pure load/get/save helpers. A manager dialog (CRUD). The per-subject editor gains a profile dropdown that auto-fills the existing `default_*` combos. The main processing area gets a "Perfil" selector that fills `app.py`'s default vars (incl. a new `var_default_profile` for `document_profile`) and persists the choice on the active subject.

**Tech Stack:** Python 3.8+, tkinter, existing `AppConfig` (settings.json), dataclasses. Reuses `PROCESSING_MODES`, `PREFERRED_BACKENDS`, `DOCUMENT_PROFILES`.

---

## File Structure

- **Modify** `src/models/core.py` — add `ProcessingProfile` dataclass + `SubjectProfile.processing_profile`.
- **Modify** `src/ui/theme.py` — `AppConfig.DEFAULTS["processing_profiles"]`.
- **Modify** `src/utils/helpers.py` — `load_processing_profiles` / `get_processing_profile` / `save_processing_profiles`.
- **Modify** `src/builder/core/stash_import.py` — propagate `document_profile` (pdf/image only).
- **Modify** `src/ui/dialogs.py` — `ProcessingProfileManagerDialog` (new) + subject-editor profile dropdown.
- **Modify** `src/ui/app.py` — `var_default_profile`, "Perfil" selector, apply/persist, FileEntry + FileEntryDialog propagation.
- **Tests** `tests/test_core.py`, `tests/test_stash_import.py`.

---

## Task 1: ProcessingProfile dataclass

**Files:**
- Modify: `src/models/core.py` (add after the `SubjectProfile` class, before `StudentProfile`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_processing_profile_roundtrip():
    from src.models.core import ProcessingProfile
    p = ProcessingProfile(name="Math", processing_mode="high_fidelity",
                          preferred_backend="datalab", datalab_mode="accurate",
                          document_profile="math_heavy")
    d = p.to_dict()
    assert d["name"] == "Math" and d["preferred_backend"] == "datalab"
    p2 = ProcessingProfile.from_dict(d)
    assert p2.document_profile == "math_heavy" and p2.processing_mode == "high_fidelity"

def test_processing_profile_from_dict_ignores_unknown_keys():
    from src.models.core import ProcessingProfile
    p = ProcessingProfile.from_dict({"name": "X", "bogus": 1})
    assert p.name == "X" and p.preferred_backend == "auto"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k processing_profile_roundtrip`
Expected: FAIL (`ImportError: cannot import name 'ProcessingProfile'`)

- [ ] **Step 3: Add the dataclass**

In `src/models/core.py`, immediately after the `SubjectProfile` class definition (before `class StudentProfile`), add:

```python
@dataclass
class ProcessingProfile:
    """Preset reutilizável de processamento (referenciado por nome pela matéria)."""
    name: str = ""
    processing_mode: str = "auto"
    preferred_backend: str = "auto"
    datalab_mode: str = "accurate"
    document_profile: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessingProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (d or {}).items() if k in valid})
```

(`asdict`, `fields`, `dataclass`, `Dict`, `Any` are already imported in this module.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k processing_profile`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_core.py
git commit -m "feat(profile): ProcessingProfile dataclass"
```

---

## Task 2: SubjectProfile.processing_profile field

**Files:**
- Modify: `src/models/core.py` (in `SubjectProfile`, after `default_datalab_mode`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_subject_profile_processing_profile_roundtrip():
    from src.models.core import SubjectProfile
    sp = SubjectProfile(name="MF", slug="mf", processing_profile="Math")
    d = sp.to_dict()
    assert d["processing_profile"] == "Math"
    assert SubjectProfile.from_dict(d).processing_profile == "Math"

def test_subject_profile_processing_profile_defaults_empty():
    from src.models.core import SubjectProfile
    assert SubjectProfile.from_dict({"name": "x", "slug": "x"}).processing_profile == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k subject_profile_processing_profile`
Expected: FAIL (`TypeError: unexpected keyword argument 'processing_profile'`)

- [ ] **Step 3: Add the field**

In `src/models/core.py`, `class SubjectProfile`, after the line `default_datalab_mode: str = "accurate"`, add:

```python
    processing_profile: str = ""   # nome do preset ProcessingProfile (referência)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k subject_profile_processing_profile`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_core.py
git commit -m "feat(profile): SubjectProfile.processing_profile reference"
```

---

## Task 3: Config seed + profile helpers

**Files:**
- Modify: `src/ui/theme.py` (`AppConfig.DEFAULTS`)
- Modify: `src/utils/helpers.py` (add helpers at end of file)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_appconfig_seeds_processing_profiles():
    from src.ui.theme import AppConfig
    names = [p["name"] for p in AppConfig.DEFAULTS["processing_profiles"]]
    assert "Math" in names and "Padrão" in names

def test_processing_profile_helpers_load_get_save():
    from src.utils.helpers import (load_processing_profiles, get_processing_profile,
                                    save_processing_profiles)
    class _Cfg:
        def __init__(self): self.d = {"processing_profiles": [
            {"name": "Math", "processing_mode": "high_fidelity", "preferred_backend": "datalab",
             "datalab_mode": "accurate", "document_profile": "math_heavy"}]}
        def get(self, k, default=None): return self.d.get(k, default)
        def set(self, k, v): self.d[k] = v
    cfg = _Cfg()
    profs = load_processing_profiles(cfg)
    assert profs[0].name == "Math" and profs[0].preferred_backend == "datalab"
    assert get_processing_profile(cfg, "Math").document_profile == "math_heavy"
    assert get_processing_profile(cfg, "missing") is None
    save_processing_profiles(cfg, profs + [type(profs[0])(name="Fast")])
    assert "Fast" in [p["name"] for p in cfg.get("processing_profiles")]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py -q -k "seeds_processing_profiles or profile_helpers"`
Expected: FAIL (`KeyError`/`ImportError`)

- [ ] **Step 3: Seed config + add helpers**

In `src/ui/theme.py`, `AppConfig.DEFAULTS`, after the `"profile_backends": {...}` entry, add:

```python
        "processing_profiles": [
            {"name": "Padrão", "processing_mode": "auto", "preferred_backend": "auto",
             "datalab_mode": "accurate", "document_profile": "auto"},
            {"name": "Math", "processing_mode": "high_fidelity", "preferred_backend": "datalab",
             "datalab_mode": "accurate", "document_profile": "math_heavy"},
        ],
```

In `src/utils/helpers.py`, append at end of file:

```python
def load_processing_profiles(config_obj):
    """Lista de ProcessingProfile salva no config (vazia se ausente)."""
    from src.models.core import ProcessingProfile
    raw = config_obj.get("processing_profiles") or []
    return [ProcessingProfile.from_dict(d) for d in raw]


def get_processing_profile(config_obj, name):
    """ProcessingProfile pelo nome, ou None."""
    for p in load_processing_profiles(config_obj):
        if p.name == name:
            return p
    return None


def save_processing_profiles(config_obj, profiles):
    """Grava a lista de ProcessingProfile no config."""
    config_obj.set("processing_profiles", [p.to_dict() for p in profiles])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k "seeds_processing_profiles or profile_helpers"`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/ui/theme.py src/utils/helpers.py tests/test_core.py
git commit -m "feat(profile): config seed + load/get/save processing profile helpers"
```

---

## Task 4: Propagate document_profile through stash import

**Files:**
- Modify: `src/builder/core/stash_import.py` (`build_stash_entries`, the `FileEntry(...)` block)
- Test: `tests/test_stash_import.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_stash_import.py`:

```python
def test_build_stash_entries_propagates_document_profile_pdf_only(tmp_path):
    card = tmp_path / "Aulas"
    card.mkdir()
    (card / "a.pdf").write_bytes(b"%PDF-1.7 x")
    (card / "x.dfy").write_text("method M(){}", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    entries = {Path(e.source_path).name: e for e in build_stash_entries(
        res, existing_source_paths=set(), defaults={"document_profile": "math_heavy"})}
    assert entries["a.pdf"].document_profile == "math_heavy"   # pdf herda
    assert entries["x.dfy"].document_profile == "auto"          # código não
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stash_import.py -q -k document_profile`
Expected: FAIL (assertion: `a.pdf` profile is "auto", not "math_heavy")

- [ ] **Step 3: Add document_profile to the entry build**

In `src/builder/core/stash_import.py`, in `build_stash_entries`, the `entries.append(FileEntry(...))` call already gates `preferred_backend`/`datalab_mode` by `item.file_type`. Add a `document_profile` line with the same pdf/image gate. Locate:

```python
            preferred_backend=(defaults.get("preferred_backend", "auto")
                               if item.file_type in ("pdf", "image") else "auto"),
            datalab_mode=(defaults.get("datalab_mode", "accurate")
                          if item.file_type == "pdf" else "accurate"),
        ))
```

Replace with:

```python
            preferred_backend=(defaults.get("preferred_backend", "auto")
                               if item.file_type in ("pdf", "image") else "auto"),
            datalab_mode=(defaults.get("datalab_mode", "accurate")
                          if item.file_type == "pdf" else "accurate"),
            document_profile=(defaults.get("document_profile", "auto")
                              if item.file_type in ("pdf", "image") else "auto"),
        ))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_stash_import.py -q`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/stash_import.py tests/test_stash_import.py
git commit -m "feat(profile): propagate document_profile through stash import (pdf/image)"
```

---

## Task 5: ProcessingProfileManagerDialog (CRUD)

**Files:**
- Modify: `src/ui/dialogs.py` (add a new dialog class near the other dialogs, e.g. after `SettingsDialog`)

UI task — verified manually. Use exact code.

- [ ] **Step 1: Add the dialog class**

In `src/ui/dialogs.py`, add this class (place it after the `SettingsDialog` class definition). It uses `ttk`, `tk`, `messagebox`, `add_tooltip`, `PROCESSING_MODES`, `PREFERRED_BACKENDS`, `DOCUMENT_PROFILES` (all already imported), and the helpers from Task 3.

```python
class ProcessingProfileManagerDialog(tk.Toplevel):
    """CRUD de perfis de processamento nomeados (settings.json)."""

    def __init__(self, parent, config_obj, theme_mgr=None):
        super().__init__(parent)
        self.config_obj = config_obj
        self.title("Perfis de processamento")
        self.geometry("620x420")
        self.transient(parent)
        self.grab_set()

        from src.utils.helpers import load_processing_profiles, save_processing_profiles
        self._load_all = load_processing_profiles
        self._save_all = save_processing_profiles
        self._current = None

        pw = ttk.Panedwindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(pw)
        pw.add(left, weight=1)
        self._listbox = tk.Listbox(left, exportselection=False)
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        bf = ttk.Frame(left)
        bf.pack(fill="x", pady=(8, 0))
        ttk.Button(bf, text="➕ Novo", command=self._new).pack(side="left")
        ttk.Button(bf, text="✖ Excluir", command=self._delete).pack(side="right")

        right = ttk.Frame(pw)
        pw.add(right, weight=2)
        form = ttk.LabelFrame(right, text="  Perfil", padding=12)
        form.pack(fill="both", expand=True)
        self._vars = {
            "name": tk.StringVar(),
            "processing_mode": tk.StringVar(value="auto"),
            "preferred_backend": tk.StringVar(value="auto"),
            "datalab_mode": tk.StringVar(value="accurate"),
            "document_profile": tk.StringVar(value="auto"),
        }
        rows = [
            ("name", "Nome", None),
            ("processing_mode", "Modo", PROCESSING_MODES),
            ("preferred_backend", "Backend preferido", PREFERRED_BACKENDS),
            ("datalab_mode", "Datalab mode", ["fast", "balanced", "accurate"]),
            ("document_profile", "Perfil de documento", DOCUMENT_PROFILES),
        ]
        for i, (key, label, vals) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
            if vals is None:
                ttk.Entry(form, textvariable=self._vars[key], width=28).grid(row=i, column=1, sticky="ew", padx=(8, 0))
            else:
                ttk.Combobox(form, textvariable=self._vars[key], values=vals,
                             state="readonly", width=24).grid(row=i, column=1, sticky="ew", padx=(8, 0))
        form.columnconfigure(1, weight=1)
        ttk.Button(right, text="💾 Salvar perfil", command=self._save).pack(fill="x", pady=(8, 0))

        self._refresh_list()

    def _profiles(self):
        return self._load_all(self.config_obj)

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        for p in self._profiles():
            self._listbox.insert("end", p.name)

    def _on_select(self, _e=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        name = self._listbox.get(sel[0])
        for p in self._profiles():
            if p.name == name:
                self._current = name
                for k, var in self._vars.items():
                    var.set(getattr(p, k, ""))
                break

    def _new(self):
        self._current = None
        self._vars["name"].set("")
        self._vars["processing_mode"].set("auto")
        self._vars["preferred_backend"].set("auto")
        self._vars["datalab_mode"].set("accurate")
        self._vars["document_profile"].set("auto")

    def _save(self):
        from src.models.core import ProcessingProfile
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Perfil", "Preencha o nome.", parent=self)
            return
        prof = ProcessingProfile(
            name=name,
            processing_mode=self._vars["processing_mode"].get(),
            preferred_backend=self._vars["preferred_backend"].get(),
            datalab_mode=self._vars["datalab_mode"].get(),
            document_profile=self._vars["document_profile"].get(),
        )
        profiles = [p for p in self._profiles() if p.name != name]   # upsert por nome
        profiles.append(prof)
        self._save_all(self.config_obj, profiles)
        self._current = name
        self._refresh_list()
        messagebox.showinfo("Perfil", f"Perfil '{name}' salvo.", parent=self)

    def _delete(self):
        if not self._current:
            return
        profiles = [p for p in self._profiles() if p.name != self._current]
        self._save_all(self.config_obj, profiles)
        self._current = None
        self._new()
        self._refresh_list()
```

- [ ] **Step 2: Syntax check**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py',encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Smoke test the suite (no regressions)**

Run: `python -m pytest -q`
Expected: all passed

- [ ] **Step 4: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(profile): ProcessingProfileManagerDialog (CRUD)"
```

---

## Task 6: Subject-editor profile dropdown + manage button

**Files:**
- Modify: `src/ui/dialogs.py` (the subject editor: `labels` list ~line 1178, combo branches ~line 1199, `_new` ~line 1304, `_save` ~line 1324)

UI task — verified manually. The 3 `default_*` combos stay (legacy fallback); the new dropdown auto-fills them when a preset is chosen.

`SubjectManagerDialog.__init__` (line 1155) is `(self, parent, subject_store, theme_mgr)` — it has NO config. It must be threaded.

- [ ] **Step 0: Thread config into SubjectManagerDialog**

In `src/ui/dialogs.py`, change the signature (line 1155) to add a trailing optional param and store it:

```python
    def __init__(self, parent, subject_store: SubjectStore, theme_mgr: ThemeManager, config_obj=None):
        super().__init__(parent)
        self.title("📚  Gerenciador de Matérias")
        self.geometry("780x700")
        self.transient(parent)
        self.grab_set()
        self._store = subject_store
        self._theme_mgr = theme_mgr
        self._config = config_obj
```

In `src/ui/app.py`, `open_subject_manager` (the line `SubjectManagerDialog(self, self.subject_store, self.theme_mgr)`), change to:

```python
        SubjectManagerDialog(self, self.subject_store, self.theme_mgr, self.config_obj)
```

All subsequent references in this task use `self._config`.

- [ ] **Step 1: Add processing_profile to the editor form**

In the subject-editor `labels` list, add an entry right after `("preferred_llm", ...)`:

```python
            ("processing_profile", "Perfil de processamento", "Preset que preenche modo/backend/datalab"),
```

In the combo-branch `for` loop (where `key == "default_mode"` etc. are handled), add a branch for `processing_profile` that lists preset names and, on selection, fills the 3 default combos. Add after the `elif key == "preferred_llm":` branch:

```python
            elif key == "processing_profile":
                from src.utils.helpers import load_processing_profiles, get_processing_profile
                names = [""] + [p.name for p in load_processing_profiles(self._config)]
                fr = ttk.Frame(form)
                fr.grid(row=i, column=1, sticky="ew", padx=(8, 0))
                cb = ttk.Combobox(fr, textvariable=var, values=names, state="readonly", width=18)
                cb.pack(side="left", fill="x", expand=True)

                def _apply_preset(_e=None):
                    p = get_processing_profile(self._config, var.get())
                    if p:
                        self._vars["default_mode"].set(p.processing_mode)
                        self._vars["default_backend"].set(p.preferred_backend)
                        self._vars["default_datalab_mode"].set(p.datalab_mode)
                cb.bind("<<ComboboxSelected>>", _apply_preset)

                def _manage():
                    ProcessingProfileManagerDialog(self, self._config)
                    cb["values"] = [""] + [pp.name for pp in load_processing_profiles(self._config)]
                ttk.Button(fr, text="⚙", width=3, command=_manage).pack(side="right", padx=(4, 0))
```

NOTE: `self._config` is set by Step 0 above. If it is `None` (dialog opened without config), the combo simply shows an empty list — guard with `(self._config and load_processing_profiles(self._config)) or []` if desired.

- [ ] **Step 2: Default in `_new`**

In the subject-editor `_new`, after `self._vars["preferred_llm"].set("claude")`, add:

```python
        self._vars["processing_profile"].set("")
```

- [ ] **Step 3: Persist in `_save`**

In the subject-editor `_save`, in the `SubjectProfile(...)` constructor call, add the argument:

```python
            processing_profile=self._vars["processing_profile"].get(),
```

- [ ] **Step 4: Syntax check + suite**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py',encoding='utf-8').read()); print('OK')"` then `python -m pytest -q`
Expected: `OK` and all passed

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py src/ui/app.py
git commit -m "feat(profile): subject-editor preset dropdown + manage button"
```

---

## Task 7: Main-area selector + apply/persist + document_profile propagation

**Files:**
- Modify: `src/ui/app.py` (vars ~line 257, subject-select ~line 1379, FileEntry creation ~1547/1571, stash defaults ~1614, `_entry_dialog` ~1466, the import toolbar area ~line 350)
- Modify: `src/ui/dialogs.py` (`FileEntryDialog.__init__` + `var_profile` init)

UI task — verified manually.

- [ ] **Step 1: Add var_default_profile in app.py**

In `src/ui/app.py`, after `self.var_default_datalab_mode = tk.StringVar(value="accurate")`, add:

```python
        self.var_default_profile = tk.StringVar(value="auto")
        self.var_active_profile = tk.StringVar(value="")
```

- [ ] **Step 2: Add the "Perfil" selector to the import toolbar**

In `src/ui/app.py`, near the import action buttons (around line 350, the `import_actions` frame), add a labeled combobox. Insert after the import buttons grid:

```python
        ttk.Label(import_actions, text="Perfil:").grid(row=3, column=0, sticky="w", padx=4, pady=(6, 0))
        from src.utils.helpers import load_processing_profiles
        self._profile_combo = ttk.Combobox(
            import_actions, textvariable=self.var_active_profile, state="readonly",
            values=[""] + [p.name for p in load_processing_profiles(self.config_obj)], width=18)
        self._profile_combo.grid(row=3, column=1, sticky="ew", padx=4, pady=(6, 0))
        self._profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_active_profile())
```

- [ ] **Step 3: Add the apply method**

In `src/ui/app.py`, add a method to the App class:

```python
    def _apply_active_profile(self):
        from src.utils.helpers import get_processing_profile
        p = get_processing_profile(self.config_obj, self.var_active_profile.get())
        if not p:
            return
        self.var_default_mode.set(p.processing_mode)
        self.var_default_backend.set(p.preferred_backend)
        self.var_default_datalab_mode.set(p.datalab_mode)
        self.var_default_profile.set(p.document_profile)
        # Matéria ativa "lembra" o perfil
        name = self._var_active_subject.get()
        if name and name != "(nenhuma)":
            sp = self.subject_store.get(name)
            if sp is not None:
                sp.processing_profile = p.name
                self.subject_store.add(sp)
```

- [ ] **Step 4: Apply the subject's profile on subject select**

In `src/ui/app.py`, in `_on_subject_selected`, after the existing
`self.var_default_datalab_mode.set(...)` line, add:

```python
        prof_name = getattr(sp, "processing_profile", "") or ""
        self.var_active_profile.set(prof_name)
        if prof_name:
            self._apply_active_profile()
```

- [ ] **Step 5: Propagate document_profile into FileEntry creation + stash + dialog**

In `src/ui/app.py` `add_pdfs` FileEntry block (the one with `preferred_backend=self.var_default_backend.get()`), add:

```python
                document_profile=self.var_default_profile.get(),
```

In `add_images` FileEntry block likewise add:

```python
                document_profile=self.var_default_profile.get(),
```

In `import_from_stash` defaults dict (where `"preferred_backend"` / `"datalab_mode"` are set), add:

```python
                "document_profile": self.var_default_profile.get(),
```

In `_entry_dialog`, pass the profile to the dialog:

```python
            default_profile=self.var_default_profile.get(),
```

In `src/ui/dialogs.py` `FileEntryDialog.__init__`, add a param `default_profile: str = "auto"` and store `self.default_profile = default_profile`. Then change the `var_profile` init line:

```python
        self.var_profile = tk.StringVar(
            value=normalize_document_profile(self.initial.document_profile if self.initial else self.default_profile)
        )
```

- [ ] **Step 6: Syntax check + suite**

Run: `python -c "import ast; ast.parse(open('src/ui/app.py',encoding='utf-8').read()); ast.parse(open('src/ui/dialogs.py',encoding='utf-8').read()); print('OK')"` then `python -m pytest -q`
Expected: `OK` and all passed

- [ ] **Step 7: Manual verification (document the result)**

Launch `python app.py`. Create a "Math" preset (or use the seed) via "Gerenciar perfis". Select a subject → set its profile dropdown to "Math". Pick "Math" in the main "Perfil" selector → confirm mode/backend/datalab/profile fill; add a PDF and a .dfy → PDF shows the preset's backend/profile, code shows gemini/código. Re-select the subject → confirm it remembers "Math".

- [ ] **Step 8: Commit**

```bash
git add src/ui/app.py src/ui/dialogs.py
git commit -m "feat(profile): main-area profile selector, apply/persist, document_profile propagation"
```

---

## Task 8: Full suite + spec status

- [ ] **Step 1: Run the whole suite**

Run: `python -m pytest -q`
Expected: all passed (baseline 1074 + new model/helper/stash tests).

- [ ] **Step 2: Mark spec implemented**

In `docs/superpowers/specs/2026-06-08-named-processing-profiles-design.md`, set `status:` to `implementado (verificação manual da UI pendente)`.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-06-08-named-processing-profiles-design.md
git commit -m "docs(profile): mark named-profiles spec implemented"
```

---

## Self-Review (completed by plan author)

**Spec coverage:** ProcessingProfile → Task 1. SubjectProfile.processing_profile → Task 2. Config seed + helpers → Task 3. document_profile propagation (stash) → Task 4; (FileEntry/dialog) → Task 7. Manager CRUD → Task 5. Subject editor dropdown + manage → Task 6. Selector + apply + subject-remembers → Task 7. Precedence unchanged (no task needed; preset feeds preferred_backend/document_profile which existing decide() already consumes).

**Placeholder scan:** none — full code in every code step. Task 6 Step 1 contains a conditional ("if attribute named differently") because the subject-editor's config attribute name must be verified against the actual `__init__`; the engineer is told exactly how to resolve both cases.

**Type consistency:** `ProcessingProfile(name, processing_mode, preferred_backend, datalab_mode, document_profile)`, `load_processing_profiles(config_obj)`, `get_processing_profile(config_obj, name)`, `save_processing_profiles(config_obj, profiles)`, `SubjectProfile.processing_profile`, `var_default_profile`, `var_active_profile`, `_apply_active_profile`, `FileEntryDialog(default_profile=...)` — consistent across tasks.

**Resolved integration point (Task 6):** `SubjectManagerDialog.__init__` had no config; Task 6 Step 0 threads `config_obj` into it and updates the `open_subject_manager` caller. Verified against the live signature at dialogs.py:1155.
