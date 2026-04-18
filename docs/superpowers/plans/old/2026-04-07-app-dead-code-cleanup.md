# App Dead Code Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remover código morto, wrappers obsoletos e caminhos de UI sem uso confirmados após a refatoração pedagógica e da fila de repositórios, sem alterar comportamento funcional do app.

**Architecture:** A limpeza será conservadora e dirigida por evidência. Só entram símbolos sem chamadas no código atual, wrappers redundantes que apenas repassam para a implementação real e classes de UI sem nenhum ponto de entrada. Cada corte deve vir acompanhado de regressão focada para garantir que o comportamento ativo continua o mesmo.

**Tech Stack:** Python 3.11, Tkinter, pytest, ripgrep, Git

---

## File Map

- Modify: `src/builder/engine.py`
  - Remover wrappers de prompt obsoletos que apenas repassam para a implementação canônica atual.
- Modify: `src/ui/app.py`
  - Remover handlers de UI sem nenhum botão, binding ou chamada restante.
- Modify: `src/ui/dialogs.py`
  - Remover janelas auxiliares sem qualquer ponto de entrada no app atual.
- Create: `docs/superpowers/plans/2026-04-07-app-dead-code-cleanup.md`
  - Registrar o plano de limpeza e a estratégia conservadora adotada.
- Test: `tests/test_core.py`
  - Cobrir o caminho de prompt ativo sem depender de wrappers legados.
- Test: `tests/test_ui_queue_dashboard.py`
  - Validar que a UI principal não perdeu fluxos ativos após a limpeza.

## Task 1: Consolidar o caminho canônico de prompts

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste que prova que o caminho público usa a implementação canônica**

```python
def test_generate_claude_project_instructions_uses_canonical_low_token_body():
    text = generate_claude_project_instructions({"course_name": "Teste"})
    assert "course/FILE_MAP.md" in text
    assert "não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente" in text
```

- [ ] **Step 2: Rodar o teste para verificar o estado atual**

Run: `pytest tests/test_core.py::TestPromptArchitectureAlignment::test_generate_claude_project_instructions_uses_canonical_low_token_body -v`
Expected: PASS ou FAIL controlado; o objetivo é fixar o contrato antes de cortar o wrapper redundante.

- [ ] **Step 3: Remover o wrapper redundante em `engine.py`**

```python
def generate_claude_project_instructions(...):
    return _low_token_generate_claude_project_instructions(...)
```

Remover:

```python
def _low_token_generate_claude_project_instructions_v2(...):
    return _low_token_generate_claude_project_instructions(...)
```

- [ ] **Step 4: Rodar a suíte de prompts**

Run: `pytest tests/test_core.py -k "PromptArchitectureAlignment or SystemPromptFileReferences" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "refactor: remove redundant prompt wrapper"
```

## Task 2: Remover UI sem ponto de entrada

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Escrever o teste de ausência do fluxo morto**

```python
def test_app_source_no_longer_contains_dead_duplicate_action():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "def duplicate_selected(" not in text
```

```python
def test_dialogs_source_no_longer_contains_unused_markdown_preview_window():
    text = Path("src/ui/dialogs.py").read_text(encoding="utf-8")
    assert "class MarkdownPreviewWindow" not in text
```

- [ ] **Step 2: Rodar os testes e confirmar o baseline**

Run: `pytest tests/test_ui_queue_dashboard.py -k "dead_duplicate_action or markdown_preview_window" -v`
Expected: FAIL, porque o código morto ainda existe na base atual.

- [ ] **Step 3: Remover o handler morto e a janela sem uso**

Excluir em `src/ui/app.py`:

```python
def duplicate_selected(self):
    ...
```

Excluir em `src/ui/dialogs.py`:

```python
class MarkdownPreviewWindow(tk.Toplevel):
    ...
```

- [ ] **Step 4: Rodar os testes da UI**

Run: `pytest tests/test_ui_queue_dashboard.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py src/ui/dialogs.py tests/test_ui_queue_dashboard.py
git commit -m "refactor: remove dead ui entry points"
```

## Task 3: Regressão final da limpeza

**Files:**
- Modify: `docs/superpowers/plans/2026-04-07-app-dead-code-cleanup.md`
- Test: `tests/test_core.py`
- Test: `tests/test_ui_queue_dashboard.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: Rodar a regressão focada da rodada**

Run: `pytest tests/test_core.py tests/test_ui_queue_dashboard.py tests/test_task_queue.py -q`
Expected: PASS

- [ ] **Step 2: Verificar ausência dos símbolos mortos removidos**

Run: `rg -n "duplicate_selected|MarkdownPreviewWindow|_low_token_generate_claude_project_instructions_v2" src`
Expected: sem ocorrências

- [ ] **Step 3: Confirmar árvore limpa**

Run: `git status --short`
Expected: apenas os arquivos desta limpeza antes do commit final; após commit, árvore limpa.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-04-07-app-dead-code-cleanup.md tests/test_core.py tests/test_ui_queue_dashboard.py
git commit -m "chore: clean dead code after pedagogy and queue refactors"
```

## Self-Review

- Cobertura do escopo: o plano foca em código morto/obsoleto confirmado nas frentes tocadas recentemente e evita “limpeza” especulativa.
- Placeholders: não há `TODO`, `TBD` ou passos sem arquivos e comandos.
- Consistência: a limpeza preserva os caminhos públicos ativos e concentra os cortes em wrappers redundantes e símbolos sem chamada.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-07-app-dead-code-cleanup.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
