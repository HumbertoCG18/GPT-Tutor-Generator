# Design: auto-roteamento derivado dos perfis nomeados

last_updated: 2026-06-09
status: aprovado

## Problema

Existem DOIS sistemas paralelos que codificam o mesmo mapeamento
`document_profile → backend`:

1. **`profile_backends`** — dict em `AppConfig.DEFAULTS` (theme.py), editado por um
   editor inline no `SettingsDialog`, lido em runtime pelo `BackendSelector`
   (engine.py) para o auto-roteamento quando `backend = auto`.
2. **Perfis nomeados** (`processing_profiles` / `BUILTIN_PROCESSING_PROFILES`) — cada
   `ProcessingProfile` já tem `document_profile` + `preferred_backend`.

Os dois duplicam a mesma informação (o comentário em helpers.py:655 admite
"alinhados ao profile_backends default"; os built-ins reproduzem o
profile_backends 1:1). Resultado: duas estruturas de config, dois editores no
Settings (editor de profile_backends + `ProcessingProfileManagerDialog`), e
confusão sobre qual manda.

Além disso, `default_profile` (AppConfig) é **morto / write-only**: o
`SettingsDialog` grava (dialogs.py:466), mas o app inicia
`var_default_profile = "auto"` hardcoded (app.py:264) e nunca lê o valor do
config.

## Decisões (do usuário)

- Níveis realmente usados: **por arquivo** e **por matéria**. As 4 camadas
  (global → matéria → arquivo) são layering intencional e **permanecem**.
- **Perfis nomeados ficam como estão** (manager + `processing_profiles` + BUILTIN
  intactos). São a fonte única.
- Auto-roteamento (`document_profile → backend`) passa a **derivar dos perfis
  nomeados**. Remove o `profile_backends` separado e seu editor.
- Abordagem **#1**: helper que deriva o dict sob demanda, mantendo a interface
  atual do `BackendSelector` (testes intactos).
- Conflito (mesmo `document_profile` em 2 perfis): **primeiro da lista vence +
  log**.

## Escopo

**Dentro:** remover `profile_backends` e `default_profile` do AppConfig; derivar o
mapa de roteamento dos perfis nomeados; remover os widgets correspondentes do
`SettingsDialog`.

**Fora (cleanups posteriores, não neste plano):** frame compartilhado dos 4
campos de processamento (B); helpers duplicados — `collapse_ws`, parse de data,
`_norm`/`norm_ascii_lower` (C); passe de código morto / cadeias de alias no
engine.py (D). O usuário sinalizou que há mais duplicatas/código morto a tratar
depois.

## Componentes

### 1. `derive_profile_backends(config_obj) -> Dict[str, str]` (novo, helpers.py)

- Itera `load_processing_profiles(config_obj)` na ordem da lista.
- Para cada perfil com `document_profile` não-vazio: registra
  `mapa[document_profile] = preferred_backend` **se ainda não presente** (primeiro
  vence).
- Se um perfil posterior repete um `document_profile` já mapeado com backend
  diferente: `log.warning(...)` e ignora (não sobrescreve).
- `config_obj is None` → retorna `{}`.
- Built-ins atuais produzem
  `{"auto": "auto", "math_heavy": "datalab", "diagram_heavy": "docling", "scanned": "auto"}`
  — idêntico ao `profile_backends` default de hoje.

Usa `log = logging.getLogger(__name__)` (ou o logger já existente em helpers.py).

### 2. Substituir as leituras de `profile_backends` (app.py)

- **app.py:107** (dict de options do build):
  `"profile_backends": config_obj.get("profile_backends") or {}`
  → `"profile_backends": derive_profile_backends(config_obj)`
- **app.py:1794** (preview do backend efetivo na tree):
  `pb = self.config_obj.get("profile_backends") or {}`
  → `pb = derive_profile_backends(self.config_obj)`

`BackendSelector`, `resolve_profile_backend` e a forma como `options` carrega
`profile_backends` para o selector **não mudam** — só a origem do dict.

### 3. Remover chaves mortas/duplicadas do `AppConfig.DEFAULTS` (theme.py)

- Remover `"default_profile": "auto"` (linha 91).
- Remover o bloco `"profile_backends": { ... }` (linhas 93-98).
- Manter `default_mode` e `default_backend` (defaults globais legítimos, fallback).

### 4. `SettingsDialog` (dialogs.py)

- Remover o editor inline de `profile_backends`: a construção
  (linhas ~428-435, incluindo `self._var_profile_backends`) e o save
  (linhas ~468-469).
- Remover `self._var_profile` (linha ~211) e o save de `default_profile`
  (linha ~466).
- Manter os controles de `default_mode` e `default_backend`.

## Fluxo de dados

Build / preview: `derive_profile_backends(config)` →
`options["profile_backends"]` → `BackendSelector(profile_backends=...)` →
`decide()` usa o mapa em `pick_advanced_for_profile` quando `backend = auto`.
Idêntico ao fluxo atual; muda só a fonte (perfis nomeados em vez de config
separada).

## Migração

Automática. `AppConfig._load` (theme.py:127) já filtra chaves fora de
`DEFAULTS` (`if k in self.DEFAULTS`). Removidas as chaves de `DEFAULTS`, os
valores antigos `profile_backends`/`default_profile` no
`~/.gpt_tutor_config.json` são ignorados na carga e desaparecem no próximo
`save()`. Sem código de migração.

**Risco aceito:** se alguém customizou `profile_backends` divergindo dos perfis
nomeados, essa customização se perde. Aceitável — os perfis nomeados passam a ser
a fonte única e os built-ins já reproduzem o default.

## Error handling

- `processing_profiles` vazio → mapa vazio → `resolve_profile_backend` retorna
  `None` → cai na ordem de fallback built-in (`pick_first`). Comportamento atual
  quando `profile_backends` estava vazio, preservado.
- `document_profile` duplicado → primeiro vence + `log.warning`.
- `config_obj is None` → `{}`.

## Testes

- `derive_profile_backends`:
  - built-ins → `{auto:auto, math_heavy:datalab, diagram_heavy:docling, scanned:auto}`.
  - conflito (2 perfis, mesmo `document_profile`, backends diferentes) → primeiro
    vence; segundo ignorado.
  - `processing_profiles` vazio → `{}`.
  - `config_obj is None` → `{}`.
- Integração: `BackendSelector(profile_backends=derive_profile_backends(cfg))`
  com perfil `math_heavy` no entry → `decide()` roteia para `datalab` (quando
  disponível) ou fallback.
- `AppConfig`: carregar um config legado com `profile_backends` e
  `default_profile` no JSON não levanta erro e essas chaves não aparecem em
  `config.data`.
- Smoke do `SettingsDialog`: instancia sem referências a `_var_profile` /
  `_var_profile_backends` (sem `AttributeError`); `_save` persiste sem as chaves
  removidas.

## Critérios de aceite

- Nenhuma referência a `profile_backends` ou `default_profile` como chave de
  config (grep limpo em src/, exceto o helper derivado e os testes).
- Editar um perfil nomeado (ex.: `math_heavy → marker`) muda o auto-roteamento no
  próximo build, sem tocar em outro lugar.
- Suíte completa verde.
