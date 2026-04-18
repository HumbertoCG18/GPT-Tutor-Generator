# Queue de Processamento, Dashboard de Repositórios e UX Responsiva Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir pipelines noturnas com múltiplos repositórios em fila, desligamento automático ao fim da fila, um dashboard operacional dos repositórios, dialogs/curators responsivos e documentação interna atualizada.

**Architecture:** A fila de processamento deixa de ser apenas a fila de arquivos da matéria e passa a existir também como fila persistida de tarefas de repositório em nível de aplicativo. O shell principal (`src/ui/app.py`) continua sendo o orquestrador da UI, mas a execução sequencial sai para um runner dedicado e o dashboard vira um componente separado que lê `subjects.json`, `manifest.json` e `manual-review/` para produzir métricas operacionais sem duplicar estado. O dialog de plataforma principal passa a ser um Toplevel temado, e os curators recebem layout adaptativo com panes reconfiguráveis conforme largura.

**Tech Stack:** Python 3.11, tkinter/ttk, JSON persistence, pathlib, threading, pytest.

---

## Estrutura de Arquivos

### Novos arquivos

- `src/models/task_queue.py`
  Responsável por definir `RepoTask`, `RepoTaskStore`, `RepoTaskStatus`, serialização JSON e helpers de migração.

- `src/builder/task_queue_runner.py`
  Responsável por executar tarefas de repositório em sequência, reportar progresso para a UI, lidar com cancelamento/pausa e disparar desligamento somente ao final da fila inteira.

- `src/ui/repo_dashboard.py`
  Responsável por montar a visão operacional dos repositórios: pendências na fila, último processamento, imagens curadas, arquivos em `manual-review`, status do manifest e resumo por matéria.

- `tests/test_task_queue.py`
  Testes unitários de persistência, ordenação, transições de estado e migração da fila de tasks.

- `tests/test_repo_dashboard.py`
  Testes unitários de coleta/agregação de métricas a partir de `SubjectProfile`, `manifest.json` e estrutura de diretórios.

### Arquivos a modificar

- `src/models/core.py`
  Ajustar interoperabilidade com o novo sistema de tasks e evitar misturar `queue` de arquivos com fila de repositórios.

- `src/ui/app.py`
  Integrar a nova fila de tasks, remover `Importação rápida`, adicionar controles de fila, execução em lote, desligamento ao concluir a fila e embutir o dashboard no shell principal.

- `src/ui/dialogs.py`
  Atualizar a Central de Ajuda, corrigir o dialog de plataforma principal e refletir a nova arquitetura de processamento.

- `src/ui/theme.py`
  Consolidar helpers de tema para Toplevels/dropsowns, especialmente no dialog de plataforma principal e em layouts responsivos com `PanedWindow`.

- `src/ui/image_curator.py`
  Tornar a tela flexível e responsiva com redistribuição dos painéis, cards e viewer PDF.

- `src/ui/curator_studio.py`
  Tornar a tela flexível e responsiva com redistribuição dos painéis e melhor comportamento em larguras menores.

- `README.md`
  Atualizar o fluxo do app, a nova fila de processamento, o dashboard e a remoção da importação rápida.

---

### Task 1: Modelar a fila persistida de tarefas de repositório

**Files:**
- Create: `src/models/task_queue.py`
- Modify: `src/models/core.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: Escrever o teste de persistência básica da fila**

```python
from pathlib import Path

from src.models.task_queue import RepoTask, RepoTaskStore


def test_task_queue_store_roundtrip(tmp_path: Path):
    store = RepoTaskStore(tmp_path / "repo_tasks.json")
    task = RepoTask(
        task_id="task-001",
        subject_name="Métodos Formais",
        repo_root="C:/Repos/metodos-formais",
        action="build_repo",
        status="pending",
    )

    store.save_all([task])
    loaded = store.load_all()

    assert len(loaded) == 1
    assert loaded[0].task_id == "task-001"
    assert loaded[0].subject_name == "Métodos Formais"
    assert loaded[0].action == "build_repo"
    assert loaded[0].status == "pending"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_task_queue.py::test_task_queue_store_roundtrip -v`

Expected: FAIL com `ModuleNotFoundError` ou ausência de `RepoTaskStore`.

- [ ] **Step 3: Implementar o modelo mínimo da fila**

```python
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

RepoTaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
RepoTaskAction = Literal["build_repo", "process_selected", "refresh_repo"]


@dataclass
class RepoTask:
    task_id: str
    subject_name: str
    repo_root: str
    action: RepoTaskAction
    status: RepoTaskStatus = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    shutdown_after_completion: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RepoTask":
        return cls(**data)


class RepoTaskStore:
    def __init__(self, path: Path):
        self._path = path

    def load_all(self) -> List[RepoTask]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [RepoTask.from_dict(item) for item in raw]

    def save_all(self, tasks: List[RepoTask]) -> None:
        self._path.write_text(
            json.dumps([task.to_dict() for task in tasks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Rodar o teste para garantir que passa**

Run: `pytest tests/test_task_queue.py::test_task_queue_store_roundtrip -v`

Expected: PASS

- [ ] **Step 5: Cobrir transições e ordenação**

```python
def test_repo_task_status_transition_updates_timestamps(tmp_path: Path):
    store = RepoTaskStore(tmp_path / "repo_tasks.json")
    task = RepoTask(
        task_id="task-002",
        subject_name="EDA",
        repo_root="C:/Repos/eda",
        action="build_repo",
    )
    task.status = "running"
    task.started_at = "2026-03-31T01:00:00"
    task.status = "completed"
    task.finished_at = "2026-03-31T01:10:00"

    store.save_all([task])
    loaded = store.load_all()[0]

    assert loaded.status == "completed"
    assert loaded.started_at == "2026-03-31T01:00:00"
    assert loaded.finished_at == "2026-03-31T01:10:00"
```

- [ ] **Step 6: Separar o conceito de fila de arquivos da fila de repositórios**

```python
@dataclass
class SubjectProfile:
    ...
    queue: List[FileEntry] = field(default_factory=list)
```

Manter `queue` em `SubjectProfile` apenas para arquivos da matéria. Não adicionar tasks de repositório em `core.py`; apenas importar o novo store no shell principal.

- [ ] **Step 7: Rodar a suíte da camada de modelo**

Run: `pytest tests/test_task_queue.py tests/test_core.py -q`

Expected: todos PASS

- [ ] **Step 8: Commit**

```bash
git add src/models/task_queue.py src/models/core.py tests/test_task_queue.py tests/test_core.py
git commit -m "feat: add persisted repository task queue models"
```

### Task 2: Implementar o runner sequencial da fila com desligamento ao final

**Files:**
- Create: `src/builder/task_queue_runner.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: Escrever o teste do runner processando duas tasks em ordem**

```python
from src.builder.task_queue_runner import TaskQueueRunner
from src.models.task_queue import RepoTask


def test_runner_executes_tasks_in_fifo_order():
    executed = []

    def fake_executor(task):
        executed.append(task.task_id)

    runner = TaskQueueRunner(fake_executor)
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo"),
    ]

    runner.run_pending(tasks)

    assert executed == ["task-a", "task-b"]
    assert tasks[0].status == "completed"
    assert tasks[1].status == "completed"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_task_queue.py::test_runner_executes_tasks_in_fifo_order -v`

Expected: FAIL porque `TaskQueueRunner` ainda não existe.

- [ ] **Step 3: Implementar o runner mínimo**

```python
from datetime import datetime
from typing import Callable, Iterable, Optional

from src.models.task_queue import RepoTask


class TaskQueueRunner:
    def __init__(self, executor: Callable[[RepoTask], None], on_event: Optional[Callable[[str, RepoTask], None]] = None):
        self._executor = executor
        self._on_event = on_event

    def run_pending(self, tasks: Iterable[RepoTask]) -> None:
        for task in tasks:
            if task.status != "pending":
                continue
            task.status = "running"
            task.started_at = datetime.now().isoformat(timespec="seconds")
            if self._on_event:
                self._on_event("started", task)
            try:
                self._executor(task)
                task.status = "completed"
            except Exception:
                task.status = "failed"
                raise
            finally:
                task.finished_at = datetime.now().isoformat(timespec="seconds")
                if self._on_event:
                    self._on_event("finished", task)
```

- [ ] **Step 4: Adicionar teste do desligamento apenas no fim da fila**

```python
def test_shutdown_is_requested_only_after_last_completed_task():
    events = []

    def fake_executor(task):
        events.append(("exec", task.task_id))

    def fake_shutdown(tasks):
        events.append(("shutdown", len(tasks)))

    runner = TaskQueueRunner(fake_executor)
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo", shutdown_after_completion=True),
    ]

    runner.run_pending(tasks)
    fake_shutdown(tasks)

    assert events[-1] == ("shutdown", 2)
```

- [ ] **Step 5: Integrar o runner no `App` sem duplicar a lógica de build**

```python
def _execute_repo_task(self, task: RepoTask) -> None:
    if task.action == "build_repo":
        self._run_task_build_repo(task)
    elif task.action == "process_selected":
        self._run_task_process_selected(task)
```

O `App` continua sendo dono do `RepoBuilder`; o runner apenas controla ordem, estado e callbacks.

- [ ] **Step 6: Mover o desligamento do modo “após build” para “após a fila”**

```python
def _schedule_shutdown_after_queue(self):
    subprocess.run(
        ["shutdown", "/s", "/t", "60", "/c", "Fila de processamento concluída."],
        check=False,
    )
```

Substituir o uso isolado de `_schedule_shutdown_after_build()` por uma verificação no final da fila inteira. Se houver execução manual unitária fora da fila, manter a opção local só quando essa operação não estiver dentro do runner.

- [ ] **Step 7: Rodar testes do runner e regressões**

Run: `pytest tests/test_task_queue.py tests/test_core.py -q`

Expected: todos PASS

- [ ] **Step 8: Commit**

```bash
git add src/builder/task_queue_runner.py src/ui/app.py tests/test_task_queue.py
git commit -m "feat: add sequential repository task runner"
```

### Task 3: Refatorar a tela principal para suportar Tasks e remover Importação Rápida

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: Remover o estado e o check de Importação Rápida**

```python
class App(tk.Tk):
    def __init__(self):
        ...
        self._shutdown_after_build = tk.BooleanVar(value=False)
```

Excluir:

```python
self._quick_import = tk.BooleanVar(value=False)
cb_quick = ttk.Checkbutton(subj_frame, text="⚡ Importação rápida", variable=self._quick_import)
```

E refatorar `add_pdfs`, `add_images`, `add_code_files` e fluxos similares para sempre abrir o dialog de edição ou usar um único caminho explícito de importação.

- [ ] **Step 2: Adicionar uma nova aba de Tasks**

```python
tab_tasks = ttk.Frame(self.notebook)
self.notebook.add(tab_tasks, text="  🧱 Tasks de Repositório  ")
```

Adicionar uma `Treeview` com colunas:

```python
columns = ("status", "subject", "repo", "action", "created_at", "finished_at")
```

- [ ] **Step 3: Criar os botões operacionais da fila**

```python
ttk.Button(task_toolbar, text="➕ Enfileirar Repositório Atual", command=self.enqueue_current_repo_task)
ttk.Button(task_toolbar, text="▶ Executar Fila", command=self.run_repo_task_queue)
ttk.Button(task_toolbar, text="⏸ Pausar Fila", command=self.pause_repo_task_queue)
ttk.Button(task_toolbar, text="🗑 Remover Task", command=self.remove_selected_repo_task)
```

- [ ] **Step 4: Enfileirar o build atual em vez de executar imediatamente quando solicitado**

```python
def enqueue_current_repo_task(self):
    meta = self._course_meta()
    repo_dir = self._repo_dir()
    task = RepoTask(
        task_id=self._new_task_id(),
        subject_name=meta["course_name"],
        repo_root=str(repo_dir),
        action="build_repo",
        shutdown_after_completion=self._shutdown_after_build.get(),
    )
    self._repo_tasks.append(task)
    self._task_store.save_all(self._repo_tasks)
    self._refresh_repo_tasks_tree()
```

O botão `🚀 Criar Repositório` deve ganhar duas opções claras:
- executar imediatamente o repositório atual
- enfileirar como task

Se preferir minimizar mudança de UX, usar menu contextual no próprio botão.

- [ ] **Step 5: Preservar o uso noturno**

```python
add_tooltip(
    queue_button,
    "Adiciona o repositório atual à fila de processamento.\n"
    "Use junto com 'Desligar ao concluir a fila' para rodar pipelines noturnas.",
)
```

O texto do checkbox deve mudar para:

```python
"⏻ Desligar ao concluir a fila"
```

- [ ] **Step 6: Cobrir a remoção da importação rápida na ajuda**

```python
assert "Importação rápida" not in HELP_SECTIONS[1][1]
```

- [ ] **Step 7: Rodar regressão da UI lógica**

Run: `pytest tests/test_task_queue.py tests/test_image_curation.py -q`

Expected: todos PASS

- [ ] **Step 8: Commit**

```bash
git add src/ui/app.py src/ui/dialogs.py tests/test_task_queue.py tests/test_image_curation.py
git commit -m "feat: add repository tasks tab and remove quick import"
```

### Task 4: Criar o dashboard operacional dos repositórios

**Files:**
- Create: `src/ui/repo_dashboard.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Escrever o teste de agregação de métricas**

```python
from pathlib import Path

from src.ui.repo_dashboard import collect_repo_metrics
from src.models.core import SubjectProfile, FileEntry


def test_collect_repo_metrics_counts_queue_and_manual_review(tmp_path: Path):
    repo_root = tmp_path / "repo"
    (repo_root / "manual-review" / "pdfs").mkdir(parents=True)
    (repo_root / "manual-review" / "pdfs" / "item-a.md").write_text("# review", encoding="utf-8")
    (repo_root / "manifest.json").write_text(
        '{"updated_at":"2026-03-31T00:30:00","entries":[{"id":"a","image_curation":{"status":"curated","pages":{"1":{"images":{"img.png":{"description":"ok","include":true}}}}}}]}',
        encoding="utf-8",
    )

    subject = SubjectProfile(
        name="Métodos Formais",
        repo_root=str(repo_root),
        queue=[FileEntry(source_path="a.pdf", file_type="pdf", category="material-de-aula", title="Aula 1")],
    )

    metrics = collect_repo_metrics(subject)

    assert metrics.pending_queue_count == 1
    assert metrics.manual_review_count == 1
    assert metrics.curated_images_count == 1
    assert metrics.last_manifest_update == "2026-03-31T00:30:00"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_repo_dashboard.py::test_collect_repo_metrics_counts_queue_and_manual_review -v`

Expected: FAIL porque `repo_dashboard.py` ainda não existe.

- [ ] **Step 3: Implementar os coletores puros primeiro**

```python
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional

from src.models.core import SubjectProfile


@dataclass
class RepoMetrics:
    subject_name: str
    repo_root: str
    pending_queue_count: int
    processed_entries_count: int
    manual_review_count: int
    curated_images_count: int
    described_images_count: int
    last_manifest_update: str


def collect_repo_metrics(subject: SubjectProfile) -> RepoMetrics:
    repo_root = Path(subject.repo_root) if subject.repo_root else None
    manifest = {}
    if repo_root and (repo_root / "manifest.json").exists():
        manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))

    entries = manifest.get("entries", [])
    manual_review_count = 0
    if repo_root and (repo_root / "manual-review").exists():
        manual_review_count = sum(1 for _ in (repo_root / "manual-review").rglob("*.md"))

    described = 0
    curated = 0
    for entry in entries:
        curation = entry.get("image_curation", {})
        for page_data in curation.get("pages", {}).values():
            for image_data in page_data.get("images", {}).values():
                if image_data.get("description"):
                    described += 1
                if image_data.get("include") and image_data.get("description"):
                    curated += 1

    return RepoMetrics(
        subject_name=subject.name,
        repo_root=subject.repo_root,
        pending_queue_count=len(subject.queue),
        processed_entries_count=len(entries),
        manual_review_count=manual_review_count,
        curated_images_count=curated,
        described_images_count=described,
        last_manifest_update=manifest.get("updated_at") or manifest.get("generated_at") or "",
    )
```

- [ ] **Step 4: Montar o painel visual em forma de dashboard/terminal**

```python
class RepoDashboard(ttk.Frame):
    def __init__(self, parent, theme_mgr, on_open_repo=None):
        ...
```

Adicionar:
- cards por matéria/repositório
- resumo superior com `tasks pendentes`, `repositórios com pendência`, `última execução`
- tabela inferior de “últimos arquivos processados” baseada em `manifest["entries"][-10:]`

- [ ] **Step 5: Embutir o dashboard na janela principal**

```python
tab_dashboard = ttk.Frame(self.notebook)
self.notebook.add(tab_dashboard, text="  🖥 Dashboard  ")
self._repo_dashboard = RepoDashboard(tab_dashboard, self.theme_mgr, on_open_repo=self.open_repo_folder)
self._repo_dashboard.pack(fill="both", expand=True)
```

Atualizar o dashboard:
- ao trocar de matéria
- ao concluir tasks
- ao salvar curadoria de imagens
- ao abrir backlog

- [ ] **Step 6: Rodar testes do dashboard**

Run: `pytest tests/test_repo_dashboard.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/ui/repo_dashboard.py src/ui/app.py tests/test_repo_dashboard.py
git commit -m "feat: add repository operations dashboard"
```

### Task 5: Corrigir o dialog de Plataforma Principal com tema consistente

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/theme.py`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: Extrair o dialog inline para uma função/classe temada**

```python
class LLMPlatformDialog(tk.Toplevel):
    def __init__(self, parent, default_value: str):
        super().__init__(parent)
        self.result = None
        self._p = apply_theme_to_toplevel(self, parent)
```

- [ ] **Step 2: Aplicar o tema explicitamente aos widgets Tk e ttk do dialog**

```python
hdr = tk.Frame(self, bg=self._p["header_bg"])
tk.Label(hdr, text="Plataforma principal", bg=self._p["header_bg"], fg=self._p["header_fg"])
body = ttk.Frame(self, padding=16)
```

Evitar `foreground="gray"` hardcoded. Usar `self._p["muted"]`.

- [ ] **Step 3: Substituir `_select_llm_platform()` pela nova classe**

```python
def _select_llm_platform(self):
    dialog = LLMPlatformDialog(self, default)
    self.wait_window(dialog)
    return dialog.result
```

- [ ] **Step 4: Cobrir manualmente o caso que gerava branco**

Checklist manual:
- abrir o dialog em tema dark
- abrir o dialog em tema light
- abrir e fechar o combobox/listbox da seleção
- confirmar que não há fundo branco não temado

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py src/ui/theme.py src/ui/dialogs.py
git commit -m "fix: theme the primary llm selection dialog"
```

### Task 6: Tornar o Image Curator flexível e responsivo

**Files:**
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Adicionar teste para helper de layout responsivo**

```python
from src.ui.image_curator import compute_image_grid_columns


def test_compute_image_grid_columns_scales_with_width():
    assert compute_image_grid_columns(700) == 1
    assert compute_image_grid_columns(1100) == 2
    assert compute_image_grid_columns(1500) == 3
```

- [ ] **Step 2: Extrair helpers puros de responsividade**

```python
def compute_image_grid_columns(width: int) -> int:
    if width < 900:
        return 1
    if width < 1350:
        return 2
    return 3
```

- [ ] **Step 3: Trocar o layout fixo dos cards por grid recalculável**

```python
cols = compute_image_grid_columns(self._cards_frame.winfo_width() or self.winfo_width())
card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
```

Deixar de depender de `pack(side="left")` por linha manual.

- [ ] **Step 4: Adaptar o `PanedWindow` para larguras menores**

```python
def _apply_responsive_layout(self, width: int) -> None:
    if width < 1200:
        self._main_paned.configure(orient="vertical")
    else:
        self._main_paned.configure(orient="horizontal")
```

Em largura pequena:
- árvore e lista acima
- imagens no meio
- PDF abaixo

- [ ] **Step 5: Garantir atualização do layout ao redimensionar**

```python
self.bind("<Configure>", self._on_window_resize)
```

- [ ] **Step 6: Rodar testes e validação manual**

Run: `pytest tests/test_image_curation.py -q`

Expected: PASS

Checklist manual:
- abrir com 1400px
- reduzir para 1100px
- reduzir para 900px
- verificar que cards, árvore e PDF continuam utilizáveis

- [ ] **Step 7: Commit**

```bash
git add src/ui/image_curator.py tests/test_image_curation.py
git commit -m "feat: make image curator responsive"
```

### Task 7: Tornar o Curator Studio flexível e responsivo

**Files:**
- Modify: `src/ui/curator_studio.py`
- Test: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Extrair um helper de modo compacto**

```python
def compute_curator_layout_mode(width: int) -> str:
    return "stacked" if width < 1250 else "wide"
```

- [ ] **Step 2: Trocar pesos fixos por relayout adaptativo**

```python
def _apply_layout_mode(self, mode: str) -> None:
    if mode == "stacked":
        self.paned.configure(orient="vertical")
    else:
        self.paned.configure(orient="horizontal")
```

No modo `stacked`:
- lista de arquivos no topo
- preview no meio
- editor abaixo

- [ ] **Step 3: Melhorar a experiência do editor em telas menores**

```python
self.info_label.configure(wraplength=max(360, self.winfo_width() - 420))
```

E reduzir largura fixa de combos/listbox quando o espaço cair.

- [ ] **Step 4: Fazer QA manual**

Checklist manual:
- abrir Curator Studio em 1600px
- abrir em 1280px
- abrir em 1024px
- validar que lista, preview e editor continuam acessíveis sem áreas mortas

- [ ] **Step 5: Commit**

```bash
git add src/ui/curator_studio.py
git commit -m "feat: make curator studio responsive"
```

### Task 8: Atualizar a Central de Ajuda, README e handoff para a nova arquitetura

**Files:**
- Modify: `src/ui/dialogs.py`
- Modify: `README.md`
- Modify: `docs/CHATGPT_HANDOFF_PROMPT.md`

- [ ] **Step 1: Atualizar as seções da ajuda**

Substituir trechos que ainda refletem a UI antiga:

```python
("Tela Principal", """...
  🧱 Tasks de Repositório
    Permite enfileirar builds e execuções em sequência.

  🖥 Dashboard
    Mostra estado operacional dos repositórios, pendências, curadoria e backlog.
""")
```

Remover qualquer menção a:

```text
⚡ Importação rápida
```

Adicionar:
- fila de tasks
- desligamento ao concluir a fila
- dashboard dos repositórios
- Image Curator/Curator Studio responsivos
- arquitetura de vision atual com `qwen3-vl:235b-cloud` e fallback `qwen3-vl:8b`

- [ ] **Step 2: Atualizar o README**

Adicionar seções ou ajustar:
- fluxo recomendado com tasks
- “Pipeline noturna”
- “Dashboard de repositórios”
- “Curadoria visual responsiva”
- remoção da importação rápida

- [ ] **Step 3: Atualizar o handoff técnico**

No `docs/CHATGPT_HANDOFF_PROMPT.md`, atualizar:
- toolbar atual
- abas atuais
- nova fila de tasks
- dashboard operacional
- estratégia de desligamento ao final da fila

- [ ] **Step 4: Verificação textual**

Run: `rg -n "Importação rápida|Desligar ao concluir build|LLaVA local|transformers" README.md docs src/ui/dialogs.py`

Expected:
- nenhuma menção residual a `Importação rápida`
- nenhuma ajuda descrevendo a arquitetura antiga errada

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py README.md docs/CHATGPT_HANDOFF_PROMPT.md
git commit -m "docs: update help center and architecture docs for task queue workflow"
```

### Task 9: Integração final e regressão end-to-end

**Files:**
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/image_curator.py`
- Modify: `src/ui/curator_studio.py`
- Test: `tests/test_task_queue.py`
- Test: `tests/test_repo_dashboard.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Amarrar refresh cruzado entre fila, dashboard e curadoria**

```python
def _refresh_operational_views(self):
    self._refresh_repo_tasks_tree()
    self._refresh_backlog()
    if hasattr(self, "_repo_dashboard"):
        self._repo_dashboard.refresh(self.subject_store.names(), self.subject_store)
```

- [ ] **Step 2: Garantir que ações relevantes chamem o refresh**

Chamar `_refresh_operational_views()` após:
- build concluído
- task concluída/falhou
- abrir matéria
- salvar curadoria
- aprovar/reprovar item no Curator Studio

- [ ] **Step 3: Rodar a suíte alvo**

Run: `pytest tests/test_task_queue.py tests/test_repo_dashboard.py tests/test_image_curation.py tests/test_core.py -q`

Expected: todos PASS

- [ ] **Step 4: QA manual do fluxo principal**

Checklist manual:
1. Enfileirar dois repositórios.
2. Marcar “Desligar ao concluir a fila”.
3. Executar a fila.
4. Verificar mudança de status `pending -> running -> completed`.
5. Verificar dashboard refletindo pendências e último processamento.
6. Abrir o dialog de plataforma principal e validar tema.
7. Abrir Image Curator e Curator Studio em largura reduzida.
8. Abrir a Central de Ajuda e verificar o conteúdo novo.

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py src/ui/dialogs.py src/ui/image_curator.py src/ui/curator_studio.py tests/test_task_queue.py tests/test_repo_dashboard.py tests/test_image_curation.py README.md docs/CHATGPT_HANDOFF_PROMPT.md
git commit -m "feat: ship repository task queue dashboard and responsive curation ux"
```

## Self-Review

### Spec coverage

- Fila de processamento tipo playlist de repositórios: coberta nas Tasks 1, 2 e 3.
- Desligar o computador ao fim da fila: coberto nas Tasks 2 e 3.
- Dashboard estilo Git/terminal para repositórios: coberto na Task 4.
- Corrigir tema do dialog de plataforma principal: coberto na Task 5.
- Tornar Image Curator e Curator Studio flexíveis e responsivos: coberto nas Tasks 6 e 7.
- Atualizar central de ajuda e arquitetura documentada: coberto na Task 8.
- Remover `Importação Rápida`: coberto na Task 3 e validado na Task 8.

### Placeholder scan

- Não há `TODO`, `TBD` ou “similar à task anterior”.
- Cada task aponta arquivos concretos, comandos e critérios de teste.
- As novas peças arquiteturais têm nomes concretos (`RepoTask`, `RepoTaskStore`, `TaskQueueRunner`, `RepoDashboard`).

### Type consistency

- `SubjectProfile.queue` continua sendo `List[FileEntry]`.
- A fila nova usa `RepoTask`.
- O runner consome `RepoTask`.
- O dashboard agrega dados de `SubjectProfile` + `manifest.json`.

## Execução Recomendada

A melhor ordem de implementação é:
1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Tasks 5, 6 e 7 em paralelo
6. Task 8
7. Task 9

Isso reduz risco porque primeiro fecha o núcleo de persistência e orquestração, depois a UI, depois os refinamentos visuais e documentação.
