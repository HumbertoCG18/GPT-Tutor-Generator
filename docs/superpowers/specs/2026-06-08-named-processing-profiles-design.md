# Design: Perfis de processamento nomeados (presets reutilizáveis)

last_updated: 2026-06-08
status: aprovado para planejamento

## Problema

Hoje os defaults de processamento vivem soltos: 3 campos no `SubjectProfile`
(`default_mode`, `default_backend`, `default_datalab_mode`) editados num form. Não
há presets reutilizáveis. O usuário quer criar/editar perfis nomeados (ex.: "math"
= high_fidelity + datalab + math_heavy) e aplicá-los rápido.

## Decisões (do usuário)

1. **Campos do preset**: `name`, `processing_mode`, `preferred_backend`,
   `datalab_mode`, `document_profile`.
2. **Aplicação**: um **seletor** ("Perfil") que preenche os defaults (modo/backend/
   datalab/perfil-doc) usados em novos arquivos e import de stash.
3. **Matéria guarda o perfil**: `SubjectProfile.processing_profile` (nome). Ao
   selecionar a matéria, aplica o preset. Substitui o uso dos 3 `default_*` por
   referência ao preset.
4. Storage: **global** em `settings.json` (lista de presets), como `profile_backends`.

## Modelo (`src/models/core.py`)

Nova dataclass:
```python
@dataclass
class ProcessingProfile:
    name: str = ""
    processing_mode: str = "auto"
    preferred_backend: str = "auto"
    datalab_mode: str = "accurate"
    document_profile: str = "auto"
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d) -> "ProcessingProfile": ...   # filtra por campos válidos
```

`SubjectProfile`: adicionar `processing_profile: str = ""` (nome do preset). Os
campos `default_mode`/`default_backend`/`default_datalab_mode` permanecem como
**fallback legado** (retrocompat): usados só quando `processing_profile` vazio.

## Config (`src/ui/theme.py`)

`AppConfig.DEFAULTS["processing_profiles"]` = lista de dicts, semeada:
```python
[
  {"name": "Padrão",  "processing_mode": "auto",          "preferred_backend": "auto",    "datalab_mode": "accurate", "document_profile": "auto"},
  {"name": "Math",    "processing_mode": "high_fidelity", "preferred_backend": "datalab", "datalab_mode": "accurate", "document_profile": "math_heavy"},
]
```

## Helpers puros (`src/models/core.py` ou `src/utils/helpers.py`)

- `load_processing_profiles(config) -> list[ProcessingProfile]`
- `get_processing_profile(config, name) -> Optional[ProcessingProfile]`
- `save_processing_profiles(config, profiles)` — grava a lista no config.

## UI

### Gerenciador de presets (`src/ui/dialogs.py`, novo dialog)

`ProcessingProfileManagerDialog`: painel-lista (nomes) à esquerda + form à direita
(`name`, combos: `processing_mode`=PROCESSING_MODES, `preferred_backend`=
PREFERRED_BACKENDS, `datalab_mode`=[fast,balanced,accurate], `document_profile`=
DOCUMENT_PROFILES). Botões Nova/Salvar/Excluir. Persiste via `save_processing_profiles`.

### Editor de matéria (`src/ui/dialogs.py`, form ~linha 1185)

Substituir os combos `default_mode`/`default_backend`/`default_datalab_mode` por:
- Combo **"Perfil de processamento"** (nomes dos presets + vazio) → grava
  `SubjectProfile.processing_profile`.
- Botão **"Gerenciar perfis…"** → abre `ProcessingProfileManagerDialog`.
Mantém `default_ocr_lang` (fora do preset).

### Seletor + aplicação (`src/ui/app.py`)

- Combobox **"Perfil"** na área de processamento, valores = nomes dos presets.
- Ao mudar: carrega o preset → seta `var_default_mode`, `var_default_backend`,
  `var_default_datalab_mode`, e novo `var_default_profile` (document_profile). Se
  há matéria ativa, grava `sp.processing_profile` e salva (matéria "lembra").
- Ao selecionar matéria (`_on_subject_selected`): seta o combobox para
  `sp.processing_profile` e aplica o preset (fallback aos `default_*` legados se vazio).

## Propagação do document_profile (novo)

- `app.py`: novo `var_default_profile`. Incluir em:
  - criação de `FileEntry` (add PDF/imagem): `document_profile=self.var_default_profile.get()`.
  - `FileEntryDialog`: novo param `default_profile`; `var_profile` inicial usa-o
    quando não há `initial`.
  - import de stash: `build_stash_entries` aceita `document_profile` nos defaults
    (gate: só pdf/imagem, como backend).

## Precedência (inalterada)

`preferred_backend` manual do preset/arquivo → mapa perfil→backend → ordem built-in.
O preset alimenta `preferred_backend` e `document_profile`; o mapa
(`profile_backends`) continua resolvendo quando `preferred_backend="auto"`.

## Erros e bordas

- `processing_profile` aponta pra preset inexistente (renomeado/excluído) →
  fallback aos `default_*` legados; sem erro.
- Lista de presets vazia → seletor mostra só vazio; defaults legados valem.
- Nome duplicado no manager → sobrescreve o existente (upsert por nome).
- Excluir preset em uso → matérias caem no fallback legado.

## Testes

- `ProcessingProfile` round-trip; `SubjectProfile.processing_profile` round-trip.
- `load/get/save_processing_profiles` (config seed + upsert + get-by-name + missing→None).
- `build_stash_entries` propaga `document_profile` (pdf/imagem) e ignora p/ código/zip.
- Config: `processing_profiles` no DEFAULTS com "Math".
- UI (manager, seletor, editor): verificação manual — tkinter.

## Fora de escopo (YAGNI)

- Aplicar preset por arquivo no Configurar (só seletor global de defaults).
- Campos extras no preset (OCR/formula/force_ocr) — só os 5 decididos.
- Migrar automaticamente os `default_*` existentes pra um preset (ficam como fallback).
- Import/export de presets.
