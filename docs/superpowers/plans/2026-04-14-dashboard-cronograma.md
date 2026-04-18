# Dashboard Cronograma Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar ao Dashboard um botão para abrir uma visão de cronograma da matéria selecionada, mostrando a data atual, o bloco temporal atual e os arquivos relacionados a esse bloco.

**Architecture:** A feature deve ser dividida em uma camada pura de leitura/modelagem do cronograma do repositório e uma camada de UI em `tkinter` que apenas renderiza esse read-model. O cálculo do bloco atual deve consumir o artefato estrutural já existente em `course/.timeline_index.json` e cruzá-lo com `course/FILE_MAP.md` para montar os arquivos por bloco, sem introduzir nova heurística pedagógica no dashboard.

**Tech Stack:** Python 3.11, tkinter/ttk, pathlib, JSON, dataclasses, pytest.

---

## Scope Boundary

Este plano cobre apenas:

- ação explícita no Dashboard para abrir o cronograma da matéria selecionada
- leitura do cronograma atual a partir do repositório existente
- destaque da data de hoje
- destaque do bloco atual
- listagem dos arquivos relacionados ao bloco
- estados vazios e mensagens de erro legíveis

Este plano não cobre:

- edição manual de blocos pela nova janela
- reprocessamento do repositório a partir dessa janela
- calendário mensal/visualização em grade
- sincronização com Google Calendar ou qualquer fonte externa

---

## File Structure

### Arquivos a criar

- `src/ui/course_timeline_view.py`
  Read-model puro da feature. Responsável por carregar `course/.timeline_index.json`, ler `course/FILE_MAP.md`, resolver o bloco atual pela data de hoje, normalizar os períodos e montar a lista de arquivos por bloco.

- `src/ui/course_timeline_dialog.py`
  Janela `tk.Toplevel` da feature. Responsável apenas por renderizar o resumo do cronograma, a linha do tempo dos blocos e os arquivos associados ao bloco selecionado.

- `tests/test_course_timeline_view.py`
  Testes do read-model e das regras de seleção do bloco atual, arquivos relacionados e estados vazios.

### Arquivos a modificar

- `src/ui/repo_dashboard.py`
  Expor seleção atual do dashboard e suportar uma ação de “Abrir Cronograma” sem embutir regra de leitura de arquivos.

- `src/ui/app.py`
  Integrar o callback do dashboard, abrir a nova janela, validar seleção e repassar o `repo_root` da matéria escolhida.

- `tests/test_repo_dashboard.py`
  Cobrir o comportamento novo do dashboard: seleção, callback e estado habilitado/desabilitado da ação.

### Arquivos existentes a consultar, mas não usar como home da feature

- `src/ui/dialogs.py`
  Já contém helpers de timeline e backlog. Deve servir como referência de formatação e matching, mas a nova feature não deve ser implementada dentro desse arquivo grande.

- `src/builder/timeline_index.py`
  Fonte do formato do `course/.timeline_index.json`.

---

## Data Contract

O read-model novo deve expor algo neste formato:

```python
@dataclass
class TimelineRelatedFile:
    title: str
    category: str
    markdown_path: str
    unit_slug: str
    period_label: str


@dataclass
class TimelineBlockView:
    block_id: str
    period_label: str
    period_start: str
    period_end: str
    unit_slug: str
    topics: list[str]
    aliases: list[str]
    is_current: bool
    contains_today: bool
    related_files: list[TimelineRelatedFile]


@dataclass
class CourseTimelineView:
    repo_root: str
    today_iso: str
    today_label: str
    has_timeline: bool
    current_block_id: str
    current_block_label: str
    blocks: list[TimelineBlockView]
    warning: str
```

Regras:

- `contains_today` usa a data real do sistema contra `period_start`/`period_end`, com fallback para `period_label`.
- `is_current` deve ficar `True` só em um bloco por vez, preferindo o bloco que realmente contém a data de hoje.
- `related_files` deve ser derivado principalmente do `Período` do `FILE_MAP.md`, com suporte a `manual_timeline_block_id` quando isso estiver refletido no `FILE_MAP`.
- se não houver `course/.timeline_index.json`, a janela abre com mensagem clara e sem stack trace.

---

## UX Contract

No Dashboard:

- botão novo: `🗓 Abrir Cronograma`
- botão começa desabilitado sem seleção
- habilita quando houver uma linha selecionada com `repo_root` válido
- duplo clique na linha continua livre para futuro uso; nesta feature o caminho oficial é o botão explícito

Na janela do cronograma:

- cabeçalho com matéria, repositório e data de hoje
- resumo curto do bloco atual: período, tópicos e unidade
- lista de blocos temporais à esquerda
- arquivos relacionados ao bloco selecionado à direita
- bloco atual marcado visualmente
- se a data atual não cair em nenhum bloco, a janela mostra “fora de bloco ativo” e ainda lista os blocos normalmente

---

## Task 1: Extrair um read-model puro para cronograma do curso

**Files:**
- Create: `src/ui/course_timeline_view.py`
- Test: `tests/test_course_timeline_view.py`

- [ ] **Step 1: Escrever o teste de bloco atual pela data do sistema**

```python
from pathlib import Path

from src.ui.course_timeline_view import build_course_timeline_view


def test_build_course_timeline_view_marks_block_that_contains_today(tmp_path: Path):
    repo = tmp_path / "repo"
    course = repo / "course"
    course.mkdir(parents=True)
    (course / ".timeline_index.json").write_text(
        """
        {
          "version": 1,
          "blocks": [
            {
              "id": "bloco-01",
              "period_label": "01/04/2026 a 05/04/2026",
              "period_start": "2026-04-01",
              "period_end": "2026-04-05",
              "unit_slug": "unidade-01",
              "topics": ["introducao"],
              "aliases": []
            },
            {
              "id": "bloco-02",
              "period_label": "10/04/2026 a 18/04/2026",
              "period_start": "2026-04-10",
              "period_end": "2026-04-18",
              "unit_slug": "unidade-02",
              "topics": ["recursao"],
              "aliases": ["inducao"]
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )
    (course / "FILE_MAP.md").write_text(
        """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Lista Recursão | listas | praticar | alta | `exercises/lists/lista-recursao.md` | Recursão | unidade-02 | Alta | 10/04/2026 a 18/04/2026 |
""",
        encoding="utf-8",
    )

    view = build_course_timeline_view(repo, today_iso="2026-04-14")

    assert view.has_timeline is True
    assert view.current_block_id == "bloco-02"
    assert any(block.is_current for block in view.blocks)
    current = next(block for block in view.blocks if block.is_current)
    assert current.related_files[0].markdown_path == "exercises/lists/lista-recursao.md"
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

Run: `pytest tests/test_course_timeline_view.py::test_build_course_timeline_view_marks_block_that_contains_today -v`

Expected: FAIL porque `build_course_timeline_view` ainda não existe.

- [ ] **Step 3: Implementar o carregador e os dataclasses mínimos**

Criar `src/ui/course_timeline_view.py` com uma API pública pequena:

```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re


@dataclass
class TimelineRelatedFile:
    title: str
    category: str
    markdown_path: str
    unit_slug: str
    period_label: str


@dataclass
class TimelineBlockView:
    block_id: str
    period_label: str
    period_start: str
    period_end: str
    unit_slug: str
    topics: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    is_current: bool = False
    contains_today: bool = False
    related_files: list[TimelineRelatedFile] = field(default_factory=list)


@dataclass
class CourseTimelineView:
    repo_root: str
    today_iso: str
    today_label: str
    has_timeline: bool
    current_block_id: str
    current_block_label: str
    blocks: list[TimelineBlockView] = field(default_factory=list)
    warning: str = ""
```

E expor:

```python
def build_course_timeline_view(repo_root: Path, today_iso: str | None = None) -> CourseTimelineView:
    ...
```

- [ ] **Step 4: Implementar os helpers de período e o parser de `FILE_MAP.md`**

Usar helpers pequenos e locais:

```python
def _parse_date(raw: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_period_bounds(text: str) -> tuple[datetime | None, datetime | None]:
    found = re.findall(r"\\d{4}-\\d{2}-\\d{2}|\\d{2}/\\d{2}/\\d{4}|\\d{2}-\\d{2}-\\d{4}", text or "")
    ...


def _load_file_map_rows(repo_root: Path) -> list[dict[str, str]]:
    ...
```

O parser do `FILE_MAP.md` deve suportar o layout atual com cabeçalhos `Título`, `Categoria`, `Markdown`, `Unidade` e `Período`.

- [ ] **Step 5: Ligar arquivos aos blocos sem nova heurística pedagógica**

Regra inicial de vínculo:

```python
if normalized_file_period == normalized_block_period:
    attach()
elif periods_overlap(file_period, block_period):
    attach()
```

Se o `FILE_MAP` não trouxer período válido, o arquivo fica fora da lista do bloco. Não inventar match por tópico nesta primeira versão.

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_course_timeline_view.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/ui/course_timeline_view.py tests/test_course_timeline_view.py
git commit -m "feat: add course timeline read model"
```

---

## Task 2: Cobrir estados vazios e bloco fora da data atual

**Files:**
- Modify: `src/ui/course_timeline_view.py`
- Test: `tests/test_course_timeline_view.py`

- [ ] **Step 1: Escrever o teste sem `.timeline_index.json`**

```python
from src.ui.course_timeline_view import build_course_timeline_view


def test_build_course_timeline_view_handles_missing_timeline_index(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)

    view = build_course_timeline_view(repo, today_iso="2026-04-14")

    assert view.has_timeline is False
    assert "timeline" in view.warning.lower()
    assert view.blocks == []
```

- [ ] **Step 2: Escrever o teste quando hoje não cai em nenhum bloco**

```python
def test_build_course_timeline_view_keeps_schedule_without_current_block(tmp_path):
    repo = tmp_path / "repo"
    course = repo / "course"
    course.mkdir(parents=True)
    (course / ".timeline_index.json").write_text(
        '{"version": 1, "blocks": [{"id": "bloco-01", "period_label": "01/03/2026 a 05/03/2026", "period_start": "2026-03-01", "period_end": "2026-03-05", "unit_slug": "unidade-01", "topics": ["introducao"], "aliases": []}]}',
        encoding="utf-8",
    )
    (course / "FILE_MAP.md").write_text("# FILE_MAP\n", encoding="utf-8")

    view = build_course_timeline_view(repo, today_iso="2026-04-14")

    assert view.has_timeline is True
    assert view.current_block_id == ""
    assert all(block.is_current is False for block in view.blocks)
```

- [ ] **Step 3: Rodar os testes para garantir que falham onde houver lacuna**

Run: `pytest tests/test_course_timeline_view.py -q`

Expected: FAIL em pelo menos um cenário de borda antes do ajuste final.

- [ ] **Step 4: Implementar warnings e fallback explícito**

Em `build_course_timeline_view(...)`, retornar:

```python
return CourseTimelineView(
    repo_root=str(repo_root),
    today_iso=today_iso_value,
    today_label=today_label,
    has_timeline=False,
    current_block_id="",
    current_block_label="",
    blocks=[],
    warning="O arquivo `course/.timeline_index.json` ainda não existe para este repositório.",
)
```

E quando não houver bloco ativo:

```python
warning = "A data de hoje não cai em nenhum bloco do cronograma atual."
```

- [ ] **Step 5: Rodar a suíte da task**

Run: `pytest tests/test_course_timeline_view.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ui/course_timeline_view.py tests/test_course_timeline_view.py
git commit -m "test: cover empty and out-of-range course timeline states"
```

---

## Task 3: Adicionar a janela de cronograma e integrá-la ao Dashboard

**Files:**
- Create: `src/ui/course_timeline_dialog.py`
- Modify: `src/ui/repo_dashboard.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Escrever o teste do callback do dashboard**

```python
from tkinter import Tk

from src.ui.repo_dashboard import RepoDashboard, RepoDashboardRow


def test_repo_dashboard_emits_open_timeline_for_selected_row():
    root = Tk()
    opened = []
    widget = RepoDashboard(root, on_open_timeline=opened.append)
    widget.set_rows([
        RepoDashboardRow(
            subject_name="Métodos Formais",
            repo_root="C:/repo",
            repo_status="Manifest pronto",
            queued_files=0,
            manifest_entries=10,
            manual_review_items=0,
            pending_repo_tasks=0,
            last_task_status="completed",
        )
    ])

    item_id = widget.tree.get_children()[0]
    widget.tree.selection_set(item_id)
    widget._handle_open_timeline()

    assert opened == ["C:/repo"]
    root.destroy()
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

Run: `pytest tests/test_repo_dashboard.py::test_repo_dashboard_emits_open_timeline_for_selected_row -v`

Expected: FAIL porque o callback e o botão ainda não existem.

- [ ] **Step 3: Expandir `RepoDashboard` com ação explícita**

Em `src/ui/repo_dashboard.py`, ajustar a assinatura:

```python
class RepoDashboard(ttk.Frame):
    def __init__(
        self,
        parent,
        on_refresh: Optional[Callable[[], None]] = None,
        on_open_timeline: Optional[Callable[[str], None]] = None,
    ):
        ...
```

Adicionar botão:

```python
ttk.Button(toolbar, text="🗓 Abrir Cronograma", command=self._handle_open_timeline)
```

E helper:

```python
def _selected_repo_root(self) -> str:
    ...


def _handle_open_timeline(self) -> None:
    repo_root = self._selected_repo_root()
    if repo_root and self._on_open_timeline:
        self._on_open_timeline(repo_root)
```

- [ ] **Step 4: Criar a janela `CourseTimelineDialog`**

Em `src/ui/course_timeline_dialog.py`, implementar:

```python
class CourseTimelineDialog(tk.Toplevel):
    def __init__(self, parent, repo_root: Path):
        super().__init__(parent)
        self._view = build_course_timeline_view(repo_root)
        ...
```

Estrutura mínima:

```python
self.title("Cronograma da Matéria")
header = ttk.Frame(self)
summary = ttk.LabelFrame(self, text="Bloco Atual")
body = ttk.PanedWindow(self, orient="horizontal")
```

Painel esquerdo: `Treeview` dos blocos.

Painel direito: `Treeview` ou `Listbox` com `Título`, `Categoria` e `Markdown`.

- [ ] **Step 5: Integrar a abertura no `App`**

Em `src/ui/app.py`:

```python
from src.ui.course_timeline_dialog import CourseTimelineDialog
```

Na criação do dashboard:

```python
self._repo_dashboard = RepoDashboard(
    tab_dashboard,
    on_refresh=self._refresh_repo_dashboard,
    on_open_timeline=self._open_dashboard_timeline,
)
```

Adicionar:

```python
def _open_dashboard_timeline(self, repo_root: str) -> None:
    repo_dir = Path(str(repo_root or "").strip())
    if not repo_dir.exists():
        messagebox.showwarning(APP_NAME, "O repositório selecionado não foi encontrado.")
        return
    CourseTimelineDialog(self, repo_dir)
```

- [ ] **Step 6: Rodar os testes da task**

Run: `pytest tests/test_repo_dashboard.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/ui/repo_dashboard.py src/ui/app.py src/ui/course_timeline_dialog.py tests/test_repo_dashboard.py
git commit -m "feat: open course timeline from dashboard"
```

---

## Task 4: Refinar a UI para destacar hoje, bloco atual e arquivos do bloco

**Files:**
- Modify: `src/ui/course_timeline_dialog.py`
- Modify: `src/ui/course_timeline_view.py`
- Test: `tests/test_course_timeline_view.py`

- [ ] **Step 1: Escrever o teste dos arquivos ligados ao bloco atual**

```python
from src.ui.course_timeline_view import build_course_timeline_view


def test_build_course_timeline_view_lists_only_files_for_selected_block(tmp_path):
    repo = tmp_path / "repo"
    course = repo / "course"
    course.mkdir(parents=True)
    (course / ".timeline_index.json").write_text(
        '{"version": 1, "blocks": [{"id": "bloco-a", "period_label": "01/04/2026 a 05/04/2026", "period_start": "2026-04-01", "period_end": "2026-04-05", "unit_slug": "u1", "topics": ["intro"], "aliases": []}, {"id": "bloco-b", "period_label": "10/04/2026 a 18/04/2026", "period_start": "2026-04-10", "period_end": "2026-04-18", "unit_slug": "u2", "topics": ["recursao"], "aliases": []}]}',
        encoding="utf-8",
    )
    (course / "FILE_MAP.md").write_text(
        '''# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Lista A | listas | praticar | alta | `exercises/lists/a.md` | Intro | u1 | Alta | 01/04/2026 a 05/04/2026 |
| 2 | Lista B | listas | praticar | alta | `exercises/lists/b.md` | Recursão | u2 | Alta | 10/04/2026 a 18/04/2026 |
''',
        encoding="utf-8",
    )

    view = build_course_timeline_view(repo, today_iso="2026-04-14")
    current = next(block for block in view.blocks if block.is_current)

    assert current.block_id == "bloco-b"
    assert [item.title for item in current.related_files] == ["Lista B"]
```

- [ ] **Step 2: Rodar o teste para verificar que falha onde a UI/data ainda não estiverem alinhadas**

Run: `pytest tests/test_course_timeline_view.py::test_build_course_timeline_view_lists_only_files_for_selected_block -v`

Expected: FAIL se ainda houver mistura de arquivos entre blocos.

- [ ] **Step 3: Ajustar a renderização visual do bloco atual**

Na janela:

```python
current_text = self._view.current_block_label or "Hoje fora de bloco ativo"
self._current_block_var.set(current_text)
self._today_var.set(self._view.today_label)
```

Ao popular a árvore dos blocos:

```python
tags = ("current",) if block.is_current else ()
self._blocks_tree.insert("", "end", iid=block.block_id, values=(block.period_label, ", ".join(block.topics[:2])), tags=tags)
```

E configurar:

```python
self._blocks_tree.tag_configure("current", background="#d9f2d9")
```

- [ ] **Step 4: Popular o painel direito a partir do bloco selecionado**

Adicionar:

```python
def _render_related_files(self, block_id: str) -> None:
    ...


def _on_block_selected(self, _event=None) -> None:
    selected = self._blocks_tree.selection()
    if selected:
        self._render_related_files(selected[0])
```

O painel direito deve mostrar:

- título
- categoria
- markdown

Sem abrir arquivo ainda nesta fase.

- [ ] **Step 5: Rodar a suíte da task**

Run: `pytest tests/test_course_timeline_view.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ui/course_timeline_view.py src/ui/course_timeline_dialog.py tests/test_course_timeline_view.py
git commit -m "feat: highlight current schedule block and related files"
```

---

## Task 5: Regressão final da feature

**Files:**
- Test: `tests/test_course_timeline_view.py`
- Test: `tests/test_repo_dashboard.py`

- [ ] **Step 1: Rodar os testes focados**

Run: `pytest tests/test_course_timeline_view.py tests/test_repo_dashboard.py -q`

Expected: PASS

- [ ] **Step 2: Rodar regressão do core da timeline já existente**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 3: Rodar uma regressão curta do núcleo da aplicação**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 4: Commit final**

```bash
git add tests/test_course_timeline_view.py tests/test_repo_dashboard.py
git commit -m "test: cover dashboard course timeline integration"
```

---

## Implementation Notes

- A nova feature deve tratar `course/.timeline_index.json` como fonte primária de blocos.
- `course/FILE_MAP.md` continua sendo a fonte primária de arquivos por período.
- Não puxar lógica nova do builder para dentro da UI.
- Não expandir `src/ui/dialogs.py` para acomodar a nova janela.
- Se surgir necessidade de abrir markdown pelo clique em arquivo relacionado, isso deve virar uma task separada.

## Self-Review

Cobertura do pedido:

- botão no dashboard: coberto na Task 3
- mostrar cronograma atual da matéria: coberto nas Tasks 1 e 3
- sinalizar a data atual: coberto nas Tasks 1, 2 e 4
- sinalizar em qual bloco está: coberto nas Tasks 1 e 4
- mostrar arquivos relacionados ao bloco: coberto nas Tasks 1 e 4
- fazer com calma e de forma precisa: decomposição em read-model, UI e regressão

Checklist de consistência:

- o plano mantém a regra pedagógica onde ela já existe
- a UI nova consome artefatos existentes do repositório
- os testes focam primeiro no read-model, depois na integração visual

