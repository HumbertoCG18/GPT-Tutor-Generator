# Clareza de config na UI — Design

date: 2026-06-11
roadmap: seção 5 item 3 + seção 7 (config) do relatório
status: aprovado para plano

## Objetivo

Comunicar na UI duas verdades hoje implícitas:
1. As opções de **vision** (`vision_backend`, `vision_model_quantization`) afetam
   **apenas o Image Curator** (descrição manual de imagens), **não o build** (que
   usa descrições do Datalab).
2. Os **padrões** (modo / OCR) exibidos na janela principal vêm da **matéria
   ativa** quando há uma, senão da **config global** — hoje sem nenhuma indicação
   de fonte.

Sem tocar o pipeline de build. Apenas tooltips, um hint e um label de fonte.

## Fatos verificados (file:line)

- `get_vision_client()` só é chamado em `src/ui/image_curator.py`
  (940, 943, 1366, 1431, 1497) — nunca no builder. `vision_client.py:17` já
  comenta "Ollama-only, mantido por compat".
- SettingsDialog: combo `vision_backend` (`dialogs.py:370`, label "Backend Vision"),
  combo `vision_model_quantization` (`dialogs.py:372`, label "Quantização").
  `add_tooltip(widget, text, delay=600)` definido em `dialogs.py:105-107`; padrão
  de hint muted em `dialogs.py:404` (`ttk.Label(..., font=("Segoe UI", 8), wraplength=320)`).
- Padrões na janela principal: `var_default_mode` init `app.py:249`,
  `var_default_ocr_language` init `app.py:250`; sobrescritos em
  `_on_subject_selected` (`app.py:1393-1395`). Labels read-only em `app.py:322`
  (modo) e `app.py:326` (OCR), dentro do LabelFrame "Dados da Disciplina".
- Sentinela de "sem matéria": `name == "(nenhuma)"` (usado em `_save_current_queue`).
- Estilo muted disponível: `Muted.TLabel` (`theme.py:210`).

## Componente A — Vision settings (só Image Curator)

Arquivo: `src/ui/dialogs.py` (SettingsDialog).

Texto único reutilizado (constante local no método que monta a seção vision):
> "Afeta apenas o Image Curator (descrição manual de imagens). O build usa as descrições geradas pelo Datalab."

Ações:
1. `add_tooltip(<combo vision_backend>, VISION_SCOPE_NOTE)` — no widget criado em ~`dialogs.py:370`.
2. Um `ttk.Label` muted (mesmo padrão de `dialogs.py:404`: `font=("Segoe UI", 8)`,
   `wraplength=320`) logo abaixo dos combos vision, com `VISION_SCOPE_NOTE`, para
   quem não usa o mouse. Cobre ambos os combos (backend + quantização) num só
   aviso visível, sem depender de hover.

Não adicionar tooltip separado no combo de quantização (já há o tooltip do
"modelo vision" em `dialogs.py:386` na mesma área; o label de seção do passo 2 já
comunica o escopo para os dois combos).

Sem mudança de comportamento; só texto.

## Componente B — Indicador de fonte dos padrões

### B1 — Helper puro (testável)

Arquivo novo: `src/ui/ui_text.py`.

```python
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

### B2 — Ligação na UI

Arquivo: `src/ui/app.py`.

1. Criar `self.var_default_source = tk.StringVar()` junto da init dos defaults
   (~`app.py:249-251`), inicializada com
   `default_source_label(self._var_active_subject.get())`.
   (Importar `from src.ui.ui_text import default_source_label`.)
2. Adicionar um `ttk.Label(course, textvariable=self.var_default_source, style="Muted.TLabel")`
   no LabelFrame "Dados da Disciplina", abaixo dos labels de modo/OCR
   (~`app.py:326`).
3. Em `_on_subject_selected` (~`app.py:1393-1396`), após setar os vars de
   modo/OCR/backend, atualizar:
   `self.var_default_source.set(default_source_label(self._var_active_subject.get()))`.

Observação: o nome da matéria ativa já está em `self._var_active_subject`. Se a
troca de matéria usar `sp.name`, usar a mesma fonte que os outros sets já usam
para consistência.

## Não-objetivos

- Não tocar `default_backend` (não é exibido na janela hoje; só modo+OCR).
- Não alterar precedência nem comportamento de config.
- Não mexer no pipeline de build, vision_client, ou Image Curator.
- Não persistir nada novo.

## Testes

`tests/test_ui_text.py`:
- `default_source_label("Cálculo I")` → `"Padrões da matéria «Cálculo I»"`.
- `default_source_label("(nenhuma)")` → `"Padrões globais (Configurações)"`.
- `default_source_label("")` e `default_source_label(None)` → global.
- `default_source_label("  Física  ")` (espaços) → `"Padrões da matéria «Física»"`.

Widgets tkinter (tooltips, labels) não são unit-testados — texto estático e
ligação trivial; validação por revisão de código.
