# Close Processing Queue and Dashboard Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar a rodada da fila persistente de repositórios e do dashboard operacional, removendo o caminho legado de `Importação rápida`, alinhando a ajuda/README com a UX atual e concluindo a responsividade pendente dos curators.

**Architecture:** O que já existe de queue/dashboard permanece como base. Este plano trata apenas do fechamento da UX e da documentação: remover o fluxo paralelo de `Importação rápida`, consolidar a fila persistente como caminho oficial, refletir isso na ajuda/README e ajustar os curators para larguras menores sem mexer na lógica pedagógica. A limpeza ampla de código morto do app inteiro fica explicitamente fora de escopo e deve virar um plano separado depois.

**Tech Stack:** Python 3.11, tkinter/ttk, JSON persistence, pathlib, threading, pytest.

---

## Scope Boundary

Este plano **não** cobre:

- limpeza ampla e sistemática do app inteiro
- refatoração arquitetural do builder
- mudanças novas no matcher pedagógico

Este plano **cobre apenas**:

- remoção completa de `Importação rápida`
- fechamento funcional e textual do fluxo queue/dashboard
- ajustes responsivos dos curators
- regressão final da rodada

---

## File Structure

### Arquivos a modificar

- `src/ui/app.py`
  Remover o toggle e os ramos de `Importação rápida`, consolidar a fila persistente como fluxo principal e ajustar os textos da tela principal.

- `src/ui/dialogs.py`
  Atualizar a Central de Ajuda para refletir o fluxo atual, remover menções legadas a `Importação rápida` e documentar a fila/dashboard.

- `src/ui/image_curator.py`
  Tornar o layout mais resiliente em larguras menores, redistribuindo painéis sem quebrar o fluxo existente.

- `src/ui/curator_studio.py`
  Tornar o layout mais resiliente em larguras menores, redistribuindo painéis sem quebrar o fluxo existente.

- `README.md`
  Atualizar a documentação principal do app para incluir `Tasks de Repositório`, `Dashboard` e o fluxo de desligamento ao final da fila, removendo a narrativa de `Importação rápida`.

### Novos arquivos

- `tests/test_ui_queue_dashboard.py`
  Testes focados em helpers/textos/estados da UI ligados ao fechamento da queue/dashboard.

### Arquivos já existentes para regressão

- `tests/test_task_queue.py`
- `tests/test_repo_dashboard.py`
- `tests/test_core.py`
- `tests/test_image_curation.py`

---

## Task 1: Remover completamente o fluxo de `Importação rápida`

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Escrever o teste de ajuda sem menção a `Importação rápida`**

```python
from src.ui.dialogs import HELP_SECTIONS


def test_help_sections_do_not_reference_quick_import():
    joined = "\n".join(body for _title, body in HELP_SECTIONS)
    assert "Importação rápida" not in joined
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_ui_queue_dashboard.py::test_help_sections_do_not_reference_quick_import -v`

Expected: FAIL porque a ajuda ainda menciona `Importação rápida`.

- [ ] **Step 3: Escrever o teste para garantir que o toggle foi removido do shell principal**

```python
from pathlib import Path


def test_app_no_longer_declares_quick_import_toggle():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "_quick_import" not in text
    assert "Importação rápida" not in text
```

- [ ] **Step 4: Rodar o teste para garantir que falha**

Run: `pytest tests/test_ui_queue_dashboard.py::test_app_no_longer_declares_quick_import_toggle -v`

Expected: FAIL porque `src/ui/app.py` ainda declara o toggle e os ramos condicionais.

- [ ] **Step 5: Remover o estado e os ramos de `Importação rápida` em `app.py`**

```python
class App(tk.Tk):
    def __init__(self):
        ...
        self.entries: List[FileEntry] = []
        self._shutdown_after_build = tk.BooleanVar(value=False)
```

Remover:

```python
self._quick_import = tk.BooleanVar(value=False)
cb_quick = ttk.Checkbutton(...)
if self._quick_import.get():
    ...
```

E consolidar os fluxos de importação para sempre passarem por:

```python
dialog = self._entry_dialog(defaults)
```

sem bifurcação por toggle.

- [ ] **Step 6: Atualizar a Central de Ajuda em `dialogs.py`**

Trocar o bloco antigo:

```text
⚡ Importação rápida
  Adiciona arquivos sem abrir o diálogo detalhado.
  Usa auto-detecção + defaults da matéria ativa.
```

por:

```text
IMPORTAÇÃO
  Ao adicionar arquivos, o app abre o diálogo de entrada para revisar
  categoria, modo, perfil, backend e sinais pedagógicos antes de salvar.
```

- [ ] **Step 7: Rodar os testes da task**

Run: `pytest tests/test_ui_queue_dashboard.py -q`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/ui/app.py src/ui/dialogs.py tests/test_ui_queue_dashboard.py
git commit -m "refactor: remove quick import and keep explicit import flow"
```

---

## Task 2: Fechar a documentação e a ajuda do fluxo queue/dashboard

**Files:**
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Escrever o teste de README mencionando queue/dashboard**

```python
from pathlib import Path


def test_readme_mentions_repo_tasks_and_dashboard():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "Tasks de Repositório" in text
    assert "Dashboard" in text
    assert "Desligar ao concluir build/fila" in text or "desligamento ao final da fila" in text
```

- [ ] **Step 2: Rodar o teste para garantir que falha ou captura a lacuna**

Run: `pytest tests/test_ui_queue_dashboard.py::test_readme_mentions_repo_tasks_and_dashboard -v`

Expected: FAIL ou cobertura insuficiente do fluxo novo.

- [ ] **Step 3: Atualizar o README na seção de fluxo do app**

Adicionar algo neste formato em `README.md`:

```markdown
### Fila persistente de repositórios

Além da fila de arquivos da matéria, o app agora possui a aba **Tasks de Repositório**.

Ela permite:

- enfileirar build do repositório atual
- enfileirar reprocessamento estrutural
- enfileirar o processamento do item selecionado
- executar, pausar e cancelar a fila
- usar desligamento automático ao final da fila

### Dashboard operacional

A aba **Dashboard** resume, por matéria:

- status do repositório
- quantidade de itens na fila da matéria
- número de entries no manifest
- quantidade de arquivos em `manual-review/`
- tasks pendentes e última task executada
```

- [ ] **Step 4: Atualizar a ajuda interna para refletir o fluxo oficial**

No bloco “Estrutura Mental do App” em `src/ui/dialogs.py`, manter:

```text
• Fila a Processar: itens ainda não processados.
• Tasks de Repositório: fila persistente de builds, reprocessamentos e processamentos individuais.
• Backlog: itens já processados, lidos do manifest do repositório.
• Dashboard: visão operacional dos repositórios, manifest e manual-review.
• Log: saída detalhada das operações.
```

E ajustar o bloco de toolbar para citar o checkbox:

```text
⏻ Desligar ao concluir build/fila
  Agenda o desligamento automático ao final da operação atual ou da fila persistente.
```

- [ ] **Step 5: Rodar os testes da task**

Run: `pytest tests/test_ui_queue_dashboard.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add README.md src/ui/dialogs.py tests/test_ui_queue_dashboard.py
git commit -m "docs: align help and readme with queue and dashboard workflow"
```

---

## Task 3: Fechar a integração fina entre fila, backlog e dashboard

**Files:**
- Modify: `src/ui/app.py`
- Test: `tests/test_task_queue.py`
- Test: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Escrever o teste de snapshot para `process_selected`**

```python
from src.models.task_queue import RepoTask


def test_repo_task_can_snapshot_single_selected_entry():
    task = RepoTask(
        task_id="task-001",
        subject_name="Métodos Formais",
        repo_root="C:/Repos/metodos-formais",
        action="process_selected",
        entry_payloads=[{"source_path": "raw/pdfs/a.pdf", "title": "A"}],
    )

    assert task.action == "process_selected"
    assert task.entry_payloads[0]["source_path"] == "raw/pdfs/a.pdf"
```

- [ ] **Step 2: Rodar o teste para garantir baseline**

Run: `pytest tests/test_task_queue.py::test_repo_task_can_snapshot_single_selected_entry -v`

Expected: PASS ou FAIL pequeno caso o teste ainda não exista.

- [ ] **Step 3: Escrever o teste de métricas usando tasks concluídas e pendentes**

```python
from src.models.core import SubjectProfile
from src.models.task_queue import RepoTask
from src.ui.repo_dashboard import collect_repo_metrics


def test_collect_repo_metrics_reports_pending_tasks_count():
    subject = SubjectProfile(name="IA", repo_root="", queue=[])
    tasks = [
        RepoTask(task_id="t1", subject_name="IA", repo_root="", action="build_repo", status="pending"),
        RepoTask(task_id="t2", subject_name="IA", repo_root="", action="refresh_repo", status="completed"),
    ]

    row = collect_repo_metrics([subject], tasks)[0]

    assert row.pending_repo_tasks == 1
```

- [ ] **Step 4: Rodar os testes focados**

Run: `pytest tests/test_task_queue.py tests/test_repo_dashboard.py -q`

Expected: PASS

- [ ] **Step 5: Ajustar a integração cruzada em `app.py`**

Garantir que estes métodos chamem o refresh cruzado:

```python
def _refresh_repo_task_views(self):
    self._save_repo_tasks()
    self._refresh_repo_tasks_tree()
    self._refresh_repo_dashboard()
```

e que também sejam chamados ao final de:

```python
def _on_repo_task_queue_finished(self):
    ...
    self._refresh_repo_task_views()
    self._refresh_backlog()
```

e em mudanças relevantes do SubjectManager / seleção de matéria:

```python
self._refresh_repo_dashboard()
```

- [ ] **Step 6: Rodar a regressão da integração**

Run: `pytest tests/test_task_queue.py tests/test_repo_dashboard.py tests/test_core.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/ui/app.py tests/test_task_queue.py tests/test_repo_dashboard.py
git commit -m "fix: finalize queue and dashboard cross-refresh behavior"
```

---

## Task 4: Tornar `Image Curator` responsivo para larguras menores

**Files:**
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Escrever o teste do helper de layout responsivo**

```python
from src.ui.image_curator import _image_curator_layout_mode


def test_image_curator_layout_mode_changes_by_width():
    assert _image_curator_layout_mode(1500) == "wide"
    assert _image_curator_layout_mode(1100) == "medium"
    assert _image_curator_layout_mode(820) == "stacked"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_image_curation.py::test_image_curator_layout_mode_changes_by_width -v`

Expected: FAIL porque o helper ainda não existe.

- [ ] **Step 3: Implementar um helper simples de modo de layout**

Em `src/ui/image_curator.py`:

```python
def _image_curator_layout_mode(width: int) -> str:
    if width >= 1400:
        return "wide"
    if width >= 980:
        return "medium"
    return "stacked"
```

- [ ] **Step 4: Aplicar o helper ao layout existente**

Usar `<Configure>` para trocar pesos/orientação sem reescrever a tela inteira:

```python
self.bind("<Configure>", self._on_layout_change)

def _on_layout_change(self, event=None):
    mode = _image_curator_layout_mode(self.winfo_width())
    ...
```

Objetivo:

- `wide`: viewer + lista + painel lateral
- `medium`: viewer maior e lateral mais estreita
- `stacked`: empilhar painel lateral abaixo

- [ ] **Step 5: Rodar a suíte do arquivo**

Run: `pytest tests/test_image_curation.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ui/image_curator.py tests/test_image_curation.py
git commit -m "feat: make image curator responsive across widths"
```

---

## Task 5: Tornar `Curator Studio` responsivo para larguras menores

**Files:**
- Modify: `src/ui/curator_studio.py`
- Test: `tests/test_ui_queue_dashboard.py`

- [ ] **Step 1: Escrever o teste do helper de layout do Curator Studio**

```python
from src.ui.curator_studio import _curator_studio_layout_mode


def test_curator_studio_layout_mode_changes_by_width():
    assert _curator_studio_layout_mode(1500) == "wide"
    assert _curator_studio_layout_mode(1100) == "medium"
    assert _curator_studio_layout_mode(820) == "stacked"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_ui_queue_dashboard.py::test_curator_studio_layout_mode_changes_by_width -v`

Expected: FAIL porque o helper ainda não existe.

- [ ] **Step 3: Implementar o helper mínimo no Curator Studio**

```python
def _curator_studio_layout_mode(width: int) -> str:
    if width >= 1400:
        return "wide"
    if width >= 980:
        return "medium"
    return "stacked"
```

- [ ] **Step 4: Aplicar o helper ao layout existente**

Usar reconfiguração de painéis/weights em vez de reescrever a tela:

```python
self.bind("<Configure>", self._on_layout_change)
```

Com metas:

- manter a lista principal legível
- evitar painéis espremidos
- empilhar detalhes quando a largura cair

- [ ] **Step 5: Rodar o teste e a regressão da UI**

Run: `pytest tests/test_ui_queue_dashboard.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ui/curator_studio.py tests/test_ui_queue_dashboard.py
git commit -m "feat: make curator studio responsive across widths"
```

---

## Task 6: Regressão final e smoke test da rodada

**Files:**
- Modify: `README.md`
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/image_curator.py`
- Modify: `src/ui/curator_studio.py`
- Test: `tests/test_task_queue.py`
- Test: `tests/test_repo_dashboard.py`
- Test: `tests/test_ui_queue_dashboard.py`
- Test: `tests/test_image_curation.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Rodar a suíte focada da rodada**

Run: `pytest tests/test_task_queue.py tests/test_repo_dashboard.py tests/test_ui_queue_dashboard.py tests/test_image_curation.py tests/test_core.py -q`

Expected: todos PASS

- [ ] **Step 2: Fazer o smoke test manual mínimo**

Checklist manual:

```text
1. Abrir o app.
2. Confirmar que não existe mais checkbox de Importação rápida.
3. Enfileirar build e reprocessamento do repositório atual.
4. Abrir a aba Tasks de Repositório e executar a fila.
5. Verificar Dashboard atualizando métricas da matéria.
6. Abrir Image Curator e Curator Studio em largura menor e confirmar que os painéis não ficam inutilizáveis.
7. Abrir Ajuda e confirmar o texto novo.
```

- [ ] **Step 3: Fazer uma revisão rápida de resíduos**

Run:

```bash
rg -n "Importação rápida|_quick_import|Todos → Auto" src README.md
```

Expected:

- nenhuma ocorrência de `_quick_import`
- nenhuma menção residual que contradiga a UX nova

- [ ] **Step 4: Commit**

```bash
git add README.md src/ui/app.py src/ui/dialogs.py src/ui/image_curator.py src/ui/curator_studio.py tests/test_task_queue.py tests/test_repo_dashboard.py tests/test_ui_queue_dashboard.py tests/test_image_curation.py tests/test_core.py
git commit -m "feat: close queue dashboard workflow and responsive curation round"
```

---

## Self-Review

- Remoção de `Importação rápida`: coberta na Task 1.
- Fechamento textual de help/README: coberto na Task 2.
- Integração fina entre fila, backlog e dashboard: coberta na Task 3.
- Responsividade pendente dos curators: coberta nas Tasks 4 e 5.
- Regressão final e smoke test: cobertos na Task 6.

Nada neste plano depende da futura limpeza ampla do app. Essa limpeza continua como etapa seguinte e deve virar um plano separado depois desta rodada.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-07-close-processing-queue-dashboard-workflow.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
