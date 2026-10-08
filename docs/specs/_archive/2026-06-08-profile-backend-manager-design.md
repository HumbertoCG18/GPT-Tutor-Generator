# Design: Gerenciador de perfil→backend (global)

last_updated: 2026-06-08
status: aprovado para planejamento

## Problema

O mapeamento perfil-de-documento → backend é hardcoded em `BackendSelector.decide`
(`engine.py:1674`): `math_heavy → pick_first([datalab, marker, docling])`. O usuário
não controla isso. Além disso a lista de processamento mostra o `preferred_backend`
estático (não o backend efetivo), então parece "apontar pra Marker" mesmo quando o
datalab seria usado. Código vai pro Gemini por `file_type` (correto), mas não tem
representação clara de "perfil".

## Decisões (do usuário)

1. **Gerenciador de perfis editável** (não só defaults por matéria).
2. **Global** em `settings.json` (AppConfig) — regras por tipo de documento.
3. **Um backend por perfil + fallback auto**: cada perfil aponta 1 backend; se
   indisponível, cai na ordem automática atual.
4. Código permanece roteado por `file_type` (Gemini, fixo) — entra como linha
   informativa não-editável.

## Precedência de backend (extração PDF)

1. `entry.preferred_backend` manual (≠ "auto" e disponível) — vence (já existe).
2. **Mapa do perfil** `profile_backends[effective_profile]` (concreto e disponível).
3. Ordem automática built-in (`pick_advanced_for_profile`) — fallback atual.

## Componentes

### Config (`src/ui/theme.py`, `AppConfig.DEFAULTS`)

Adicionar:
```python
"profile_backends": {
    "auto": "auto",
    "math_heavy": "datalab",
    "diagram_heavy": "docling",
    "scanned": "auto",
},
```
Valor `"auto"` = usar a ordem built-in. `_load` já preserva chaves de `DEFAULTS`
(o dict é substituído pelo armazenado). Nenhuma migração.

### Resolver (`src/builder/engine.py`)

- Helper puro:
  ```python
  def resolve_profile_backend(profile, profile_backends, available) -> Optional[str]:
      b = (profile_backends or {}).get(profile)
      if b and b != "auto" and available.get(b):
          return b
      return None
  ```
- `BackendSelector.__init__(self, profile_backends=None)`: `self.profile_backends = profile_backends or {}`.
- Em `decide`, `pick_advanced_for_profile(profile)` tenta primeiro
  `resolve_profile_backend(profile, self.profile_backends, available)`; se `None`,
  mantém o `pick_first(...)` atual. Acrescenta reason quando o mapa decide.
- `RepoBuilder.__init__` (`engine.py:1765`):
  `self.selector = BackendSelector(profile_backends=self.options.get("profile_backends") or {})`.

### Threading das options (`src/ui/app.py`)

Onde as `options` do builder são montadas a partir do config (ver
`_build_options_from_config` / criação do `RepoBuilder`), incluir
`"profile_backends": config_obj.get("profile_backends")`.

### UI — SettingsDialog aba Processing (`src/ui/dialogs.py`)

Nova seção "Perfis → Backend":
- Uma linha por perfil editável: `auto`, `math_heavy`, `diagram_heavy`, `scanned`
  → `ttk.Combobox` readonly, valores `["auto", "datalab", "marker", "docling", "docling_python", "pymupdf4llm", "pymupdf"]`.
- Linha fixa informativa (desabilitada): `código/zip → gemini`.
- Carrega de `config.get("profile_backends")`; salva no handler de save
  (`config.set("profile_backends", {...})`).

### Lista de processamento (`src/ui/app.py`, `refresh_tree`)

Backend efetivo exibido (corrige a "lista que mente"):
- código/zip → `"gemini"` (já feito).
- senão: `entry.preferred_backend` se ≠ "auto"; senão
  `profile_backends.get(entry.document_profile)` se concreto; senão `"auto"`.
Coluna "Perfil" segue mostrando `document_profile` (e "código" p/ code/zip).

## Erros e bordas

- Backend mapeado mas indisponível em runtime → fallback à ordem built-in (sem erro).
- Perfil ausente no mapa → tratado como "auto".
- `preferred_backend` manual por arquivo continua tendo prioridade máxima.
- Combobox readonly impede valor inválido.

## Testes

- `resolve_profile_backend`: concreto+disponível → backend; indisponível → None;
  "auto"/ausente → None.
- `decide`: com `profile_backends={"math_heavy":"docling"}` e docling disponível →
  advanced_backend == "docling"; com mapeado indisponível → cai no built-in.
- Config: `profile_backends` presente no DEFAULTS e round-trip de save/load.
- UI (SettingsDialog, refresh_tree): verificação manual — tkinter.

## Fora de escopo (YAGNI)

- Mapa por matéria (é global).
- Lista de prioridade por perfil (um backend + fallback).
- Editar o roteamento de código (fixo: Gemini).
- Resolver o backend efetivo via `decide()` completo na lista (preview leve pelo
  mapa basta; evita rodar análise por linha).
