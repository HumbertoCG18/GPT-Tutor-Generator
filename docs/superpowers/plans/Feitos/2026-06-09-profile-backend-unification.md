# Profile-Backend Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derivar o mapa de auto-roteamento `document_profile → backend` dos perfis nomeados, removendo o config duplicado `profile_backends` e a chave morta `default_profile`.

**Architecture:** Um helper puro `derive_profile_backends(config_obj)` calcula o dict a partir de `load_processing_profiles`. Os dois sites que liam `config.get("profile_backends")` passam a chamar o helper. `BackendSelector`/`resolve_profile_backend` ficam intactos (recebem o dict via options). Remove-se `profile_backends` e `default_profile` do `AppConfig.DEFAULTS` e os widgets correspondentes do `SettingsDialog`. Migração é automática (o loader já filtra chaves fora de DEFAULTS).

**Tech Stack:** Python 3.13, pytest, tkinter.

Spec: `docs/superpowers/specs/2026-06-09-profile-backend-unification-design.md`

---

### Task 1: Helper `derive_profile_backends`

**Files:**
- Modify: `src/utils/helpers.py` (adicionar função após `save_processing_profiles`, ~linha 699+; garantir `import logging` + logger de módulo no topo)
- Test: `tests/test_core.py` (adicionar no fim do arquivo)

- [ ] **Step 1: Write the failing tests**

Adicionar ao fim de `tests/test_core.py`:

```python
class _ProfCfg:
    """Config stub: só expõe processing_profiles para load_processing_profiles."""
    def __init__(self, profiles):
        self._p = profiles
    def get(self, key, default=None):
        return self._p if key == "processing_profiles" else default


def test_derive_profile_backends_builtins():
    from src.utils.helpers import derive_profile_backends, BUILTIN_PROCESSING_PROFILES
    cfg = _ProfCfg([dict(b) for b in BUILTIN_PROCESSING_PROFILES])
    assert derive_profile_backends(cfg) == {
        "auto": "auto",
        "math_heavy": "datalab",
        "diagram_heavy": "docling",
        "scanned": "auto",
    }


def test_derive_profile_backends_first_wins_on_conflict():
    from src.utils.helpers import derive_profile_backends
    cfg = _ProfCfg([
        {"name": "a", "document_profile": "math_heavy", "preferred_backend": "datalab"},
        {"name": "b", "document_profile": "math_heavy", "preferred_backend": "marker"},
    ])
    assert derive_profile_backends(cfg)["math_heavy"] == "datalab"


def test_derive_profile_backends_skips_empty_document_profile():
    from src.utils.helpers import derive_profile_backends
    cfg = _ProfCfg([
        {"name": "x", "document_profile": "", "preferred_backend": "datalab"},
    ])
    assert derive_profile_backends(cfg) == {}


def test_derive_profile_backends_empty_and_none():
    from src.utils.helpers import derive_profile_backends
    assert derive_profile_backends(_ProfCfg([])) == {}
    assert derive_profile_backends(None) == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core.py -q -k derive_profile_backends`
Expected: FAIL — `ImportError: cannot import name 'derive_profile_backends'`.

- [ ] **Step 3: Implement the helper**

No topo de `src/utils/helpers.py`, garantir (se ainda não existir):

```python
import logging

log = logging.getLogger("helpers")
```

Adicionar após `save_processing_profiles` (~linha 699+):

```python
def derive_profile_backends(config_obj) -> dict:
    """Mapa {document_profile: preferred_backend} derivado dos perfis nomeados.

    Fonte única do auto-roteamento (substitui o antigo config `profile_backends`).
    Primeiro perfil por ordem da lista vence; conflito (mesmo document_profile com
    backend diferente) -> log.warning e ignora. `config_obj` None -> {}.
    """
    if config_obj is None:
        return {}
    mapping: dict = {}
    for prof in load_processing_profiles(config_obj):
        dp = (prof.document_profile or "").strip()
        if not dp:
            continue
        backend = (prof.preferred_backend or "").strip() or "auto"
        if dp in mapping:
            if mapping[dp] != backend:
                log.warning(
                    "perfil '%s' redefine document_profile '%s' (%s -> %s); mantendo o primeiro",
                    prof.name, dp, mapping[dp], backend,
                )
            continue
        mapping[dp] = backend
    return mapping
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k derive_profile_backends`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/utils/helpers.py tests/test_core.py
git commit -m "feat(profile): derive_profile_backends helper (map from named profiles)"
```

---

### Task 2: Ligar o helper nos dois sites de leitura (app.py)

**Files:**
- Modify: `src/ui/app.py` (import; linha 107; linha ~1794)

- [ ] **Step 1: Importar o helper**

Em `src/ui/app.py`, localizar a linha `from src.utils.helpers import ...` (a que já traz helpers de perfil) e acrescentar `derive_profile_backends` à lista importada. Se não houver import de helpers conveniente, adicionar:

```python
from src.utils.helpers import derive_profile_backends
```

- [ ] **Step 2: Substituir o site do build (linha 107)**

Trocar:

```python
        "profile_backends": config_obj.get("profile_backends") or {},
```

por:

```python
        "profile_backends": derive_profile_backends(config_obj),
```

- [ ] **Step 3: Substituir o site do preview da tree (linha ~1794)**

Trocar:

```python
                pb = self.config_obj.get("profile_backends") or {}
                backend_disp = pb.get(entry.document_profile, "auto")
```

por:

```python
                pb = derive_profile_backends(self.config_obj)
                backend_disp = pb.get(entry.document_profile, "auto")
```

- [ ] **Step 4: Verificar import e ausência de referência a config profile_backends em app.py**

Run: `python -c "import ast; ast.parse(open(r'src/ui/app.py', encoding='utf-8').read())"`
Expected: sem erro.

Run: `python -m pytest -q -k "app or build" 2>&1 | tail -5`
Expected: PASS (sem novas falhas).

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py
git commit -m "refactor(profile): app reads auto-routing via derive_profile_backends"
```

---

### Task 3: Remover config morto/duplicado + widgets do Settings

**Files:**
- Modify: `src/ui/theme.py` (AppConfig.DEFAULTS, linhas 91, 93-98)
- Modify: `src/ui/dialogs.py` (SettingsDialog: linhas 211, 219, 421-444, 466, 468-469)

- [ ] **Step 1: Remover chaves de `AppConfig.DEFAULTS` (theme.py)**

Apagar estas linhas de `DEFAULTS`:

```python
        "default_profile": "auto",
```

e o bloco:

```python
        "profile_backends": {
            "auto": "auto",
            "math_heavy": "datalab",
            "diagram_heavy": "docling",
            "scanned": "auto",
        },
```

Manter `default_mode` e `default_backend`.

- [ ] **Step 2: Remover a var e o campo `default_profile` no SettingsDialog (dialogs.py)**

Apagar a linha 211:

```python
        self._var_profile = tk.StringVar(value=normalize_document_profile(self.config.get("default_profile")))
```

E remover do `fields` (linha 219) a entrada:

```python
            ("Perfil de documento padrão", self._var_profile, DOCUMENT_PROFILES),
```

- [ ] **Step 3: Remover o editor inline de profile_backends (dialogs.py, linhas 421-444)**

Apagar todo o bloco que começa em `# ── Perfis de documento → Backend ───` (linha 421) e vai até o label de `código / zip` inclusive (linha 444):

```python
        # ── Perfis de documento → Backend ────────────────────────────
        pb_sep = sep_row + 14
        ttk.Separator(tab_proc, orient="horizontal").grid(
            row=pb_sep, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(tab_proc, text="Perfis de documento → Backend",
                  style="Accent.TLabel").grid(
            row=pb_sep + 1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        _pb_cfg = self.config.get("profile_backends") or {}
        _PB_CHOICES = ["auto", "datalab", "marker", "docling", "docling_python", "pymupdf4llm", "pymupdf"]
        self._var_profile_backends = {}
        for _j, _prof in enumerate(["auto", "math_heavy", "diagram_heavy", "scanned"]):
            _r = pb_sep + 2 + _j
            ttk.Label(tab_proc, text=_prof).grid(row=_r, column=0, sticky="w", pady=4, padx=(0, 16))
            _v = tk.StringVar(value=str(_pb_cfg.get(_prof, "auto")))
            self._var_profile_backends[_prof] = _v
            _cb = ttk.Combobox(tab_proc, textvariable=_v, values=_PB_CHOICES,
                               state="readonly", width=22)
            _cb.grid(row=_r, column=1, sticky="w")
            add_tooltip(_cb, "Backend p/ este perfil. 'auto' = ordem automática.\n"
                             "Se o backend escolhido estiver indisponível, cai no automático.")
        _code_row = pb_sep + 6
        ttk.Label(tab_proc, text="código / zip").grid(row=_code_row, column=0, sticky="w", pady=4, padx=(0, 16))
        ttk.Label(tab_proc, text="gemini (fixo — código não passa por datalab)",
                  font=("Segoe UI", 9, "italic")).grid(row=_code_row, column=1, sticky="w")
```

NÃO apagar a linha seguinte `tab_proc.columnconfigure(1, weight=1)` (linha 446) nem a seção de botões.

- [ ] **Step 4: Remover os saves correspondentes em `_save` (dialogs.py, linhas 466, 468-469)**

Apagar:

```python
        self.config.set("default_profile", self._var_profile.get())
```

e:

```python
        self.config.set("profile_backends",
                        {p: v.get() for p, v in self._var_profile_backends.items()})
```

Manter os sets de `theme`, `default_mode`, `default_ocr_language`, `default_backend` e demais.

- [ ] **Step 5: Verificar parse e que `sep_row` não ficou órfão**

Run: `python -c "import ast; ast.parse(open(r'src/ui/dialogs.py', encoding='utf-8').read())"`
Expected: sem erro.

Nota: `sep_row` ainda é usado por outras seções acima; só removemos `pb_sep` (que dependia dele). Confirmar via grep que `pb_sep` e `_var_profile_backends` não têm mais referências:

Run: `python -m pytest -q -k "settings or config or theme" 2>&1 | tail -5`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ui/theme.py src/ui/dialogs.py
git commit -m "refactor(profile): remove duplicate profile_backends + dead default_profile from config/Settings"
```

---

### Task 4: Regressão — migração de config legado + suíte + grep limpo

**Files:**
- Test: `tests/test_core.py` (adicionar 1 teste de migração)

- [ ] **Step 1: Write the migration test**

Adicionar ao fim de `tests/test_core.py`:

```python
def test_appconfig_drops_removed_legacy_keys(tmp_path, monkeypatch):
    """Config legado com profile_backends/default_profile carrega sem erro e as
    chaves removidas não entram em config.data (filtradas por DEFAULTS)."""
    import json as _json
    import src.ui.theme as theme_mod
    legacy = tmp_path / ".gpt_tutor_config.json"
    legacy.write_text(_json.dumps({
        "theme": "light",
        "default_profile": "math_heavy",
        "profile_backends": {"math_heavy": "marker"},
    }), encoding="utf-8")
    monkeypatch.setattr(theme_mod, "CONFIG_PATH", legacy)
    cfg = theme_mod.AppConfig()
    assert cfg.get("theme") == "light"          # chave válida preservada
    assert "default_profile" not in cfg.data    # chave removida ignorada
    assert "profile_backends" not in cfg.data
```

- [ ] **Step 2: Run the migration test**

Run: `python -m pytest tests/test_core.py -q -k appconfig_drops_removed_legacy_keys`
Expected: PASS.

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -q 2>&1 | tail -5`
Expected: PASS (todos verdes).

- [ ] **Step 4: Grep de limpeza — nenhuma referência residual à config removida**

Run (PowerShell/ripgrep via Grep tool ou):
`python -c "import pathlib,re; hits=[f'{p}:{i+1}' for p in pathlib.Path('src').rglob('*.py') for i,l in enumerate(p.read_text(encoding='utf-8').splitlines()) if re.search(r'profile_backends|default_profile', l)]; print('\n'.join(hits))"`

Expected: apenas a definição/uso de `derive_profile_backends` (helper) e nada referente à CHAVE de config `profile_backends`/`default_profile`. Se aparecer qualquer `config.get("profile_backends")`, `config.set("default_profile"...)` ou `DEFAULTS` com essas chaves, corrigir antes de prosseguir.

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py
git commit -m "test(profile): legacy config drops removed profile_backends/default_profile keys"
```

---

## Notas finais

- `BackendSelector`, `resolve_profile_backend`, `processing_profiles`,
  `BUILTIN_PROCESSING_PROFILES`, `ProcessingProfileManagerDialog` e os campos
  per-matéria/per-arquivo **permanecem intactos** (decisão do usuário).
- Cleanups separados (fora deste plano): frame compartilhado dos 4 campos de
  processamento; helpers duplicados (`collapse_ws`, parse de data,
  `_norm`/`norm_ascii_lower`); passe de código morto + cadeias de alias no
  `engine.py`.
