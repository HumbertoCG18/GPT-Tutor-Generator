# Design: Editor de perfil de processamento (por matéria)

last_updated: 2026-06-08
status: aprovado para planejamento

## Problema

Ao processar arquivos, modo/backend/datalab-mode são configurados por arquivo no
diálogo "Configurar" (`FileEntryDialog`), que abre com defaults hardcoded
(`preferred_backend="auto"`, `datalab_mode="accurate"`). Não há como definir esses
defaults por matéria — o setup é repetitivo. O `SubjectProfile` já guarda
`default_mode`, `default_ocr_lang`, `preferred_llm`, mas não backend nem datalab.

## Objetivo

Estender o **perfil por matéria** (editor existente) com **backend preferido** e
**datalab mode**, e propagar esses defaults pré-preenchendo o diálogo Configurar e
a criação de `FileEntry`. Acelera o setup do processamento.

## Decisões (do usuário)

1. Escopo: **por matéria** — estende o editor de perfil existente (onde já vivem
   `default_mode`/`preferred_llm`).
2. Campos: **modo + backend preferido + datalab mode** (sem OCR/extras nesta etapa).
3. Propagação: **pré-preenche** o diálogo "Configurar" (`FileEntryDialog`); o
   usuário ainda pode ajustar por arquivo.

## Constantes existentes (reuso)

- `PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]`
- `PREFERRED_BACKENDS = ["auto", "pymupdf4llm", "pymupdf", "datalab", "docling", "docling_python", "marker"]`
- Datalab mode: `["fast", "balanced", "accurate"]` (já no combobox do `FileEntryDialog`).

## Componentes

### Modelo (`src/models/core.py`)

`SubjectProfile`: adicionar
```python
default_backend: str = "auto"
default_datalab_mode: str = "accurate"
```
Retrocompatível (`from_dict` filtra por campos válidos; perfis antigos recebem default).

### Editor de perfil (`src/ui/dialogs.py`, form da ~linha 1185)

Adicionar duas linhas ao `labels`/form (combobox `state="readonly"`):
- `default_backend` → "Backend padrão", valores `PREFERRED_BACKENDS`.
- `default_datalab_mode` → "Datalab mode", valores `["fast", "balanced", "accurate"]`.

Carregar/salvar junto dos demais campos do `SubjectProfile` (load em `_on_select`,
save no handler que monta o `SubjectProfile`).

### Diálogo Configurar (`FileEntryDialog`, ~linha 3259)

- Assinatura: adicionar `default_backend: str = "auto"`, `default_datalab_mode: str = "accurate"`.
- No corpo (hoje linhas ~3352-3353), trocar o else hardcoded:
  - `var_backend` inicial: `self.initial.preferred_backend if self.initial else self.default_backend`.
  - `var_datalab_mode` inicial: `getattr(self.initial, "datalab_mode", ...) if self.initial else self.default_datalab_mode`.

### Propagação (`src/ui/app.py`)

- Novos `tk.StringVar`: `var_default_backend`, `var_default_datalab_mode`.
- Ao carregar perfil (junto de ~linhas 1379-1380): setar a partir de
  `sp.default_backend` / `sp.default_datalab_mode`.
- Ao instanciar `FileEntryDialog` (~linha 1464): passar
  `default_backend=self.var_default_backend.get()`,
  `default_datalab_mode=self.var_default_datalab_mode.get()`.
- Ao criar `FileEntry` em lote (~linhas 1543, 1567, 1610): preencher
  `preferred_backend` e `datalab_mode` a partir das vars do perfil (hoje usam
  default do dataclass). Mantém override por arquivo.

## Fluxo

Editar perfil da matéria → salva `default_backend`/`default_datalab_mode` no
`SubjectProfile` → ao selecionar a matéria, `app.py` carrega esses defaults →
"Configurar" e criação de `FileEntry` já vêm pré-preenchidos → menos cliques.

## Erros e bordas

- Perfil antigo sem os campos → defaults (`auto`/`accurate`). Sem migração.
- `datalab_mode` só é relevante quando backend = `datalab`; o `FileEntryDialog` já
  mostra/oculta esse campo conforme o backend (`_update_datalab_mode_visibility`).
  O valor fica salvo no perfil mesmo se oculto.
- Backend inválido (combobox readonly) impossível pela UI.

## Testes

- `SubjectProfile` round-trip com `default_backend`/`default_datalab_mode`
  (presente preserva; ausente → default).
- UI (editor, FileEntryDialog, app propagação): verificação manual — tkinter.

## Fora de escopo (YAGNI)

- Perfis nomeados reutilizáveis (múltiplos presets).
- Default global no SettingsDialog.
- OCR/force_ocr/formula_priority/extract_* no perfil (só modo+backend+datalab agora).
- Migração de perfis antigos.
