# TimelineDashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar janela `TimelineDashboard` (Toplevel Tkinter) que exibe blocos do cronograma em accordion, arquivos mapeados por bloco, dropdown para atribuição manual de `manual_timeline_block_id`, e botão de reprocessamento.

**Architecture:** Leitura direta de `manifest.json` e `course/.timeline_index.json` via duas funções puras (`load_timeline_data`, `save_block_assignment`) extraídas no topo do módulo para permitir testes sem instanciar Tkinter. A janela consome essas funções. Entrada via item `📅 Timeline` no menu `🗂 Repo` do backlog toolbar em `app.py`.

**Tech Stack:** Python 3.11+, Tkinter/ttk, pathlib, json. Pytest para testes de dados.

---

## Estrutura de Arquivos

| Arquivo | Tipo | Responsabilidade |
|---|---|---|
| `src/ui/timeline_dashboard.py` | Novo | Funções puras de dados + classe `TimelineDashboard` |
| `src/ui/app.py` | Modificar | Import + menu item + `_open_timeline_dashboard()` |
| `tests/test_timeline_dashboard_data.py` | Novo | 3 testes das funções puras (sem Tkinter) |

---

## Referência de Dados

**`manifest.json`** (em `repo_root/manifest.json`):
```json
{
  "entries": [
    {
      "id": "abc123",
      "title": "Processos",
      "source_path": "12.03 Processos.pdf",
      "auto_tags": ["bloco:blk-01", "unit:unidade-01"],
      "manual_timeline_block_id": "",
      "unit_match_confidence": 0.92
    }
  ]
}
```

**`course/.timeline_index.json`** (em `repo_root/course/.timeline_index.json`):
```json
{
  "version": 3,
  "blocks": [
    {
      "id": "blk-01",
      "period_label": "Semana 01",
      "unit_slug": "unidade-01",
      "primary_topic_label": "Processos"
    }
  ]
}
```

**Regra de mapeamento entry→bloco:**
1. `manual_timeline_block_id` não vazio → usa esse block_id
2. Senão: procura `bloco:<block_id>` em `auto_tags`
3. Sem nenhum dos dois → entry vai para "sem bloco"

**Badge DD.MM:** detectado na UI via `re.match(r"^(\d{1,2})\.(\d{2})\s+", Path(source_path).stem)`

---

## Task 1: Funções puras de dados

**Arquivo:** `src/ui/timeline_dashboard.py` (apenas as funções — TDD antes do Toplevel)
**Teste:** `tests/test_timeline_dashboard_data.py`

- [ ] **Step 1.1: Escrever os 3 testes — verificar que falham**

Criar `tests/test_timeline_dashboard_data.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.timeline_dashboard import load_timeline_data, save_block_assignment


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_data_separates_mapped_and_unmapped(tmp_path):
    manifest = {
        "entries": [
            {"id": "e1", "auto_tags": ["bloco:blk-01"], "unit_match_confidence": 0.9},
            {"id": "e2", "manual_timeline_block_id": "blk-01", "auto_tags": []},
            {"id": "e3", "auto_tags": []},
        ]
    }
    timeline = {
        "version": 3,
        "blocks": [{"id": "blk-01", "period_label": "Semana 01", "unit_slug": "u1"}],
    }
    _write(tmp_path / "manifest.json", manifest)
    _write(tmp_path / "course" / ".timeline_index.json", timeline)

    blocks, by_block, unmapped = load_timeline_data(
        tmp_path / "manifest.json",
        tmp_path / "course" / ".timeline_index.json",
    )

    assert len(blocks) == 1
    assert len(by_block["blk-01"]) == 2  # e1 (auto_tags) + e2 (manual)
    assert len(unmapped) == 1
    assert unmapped[0]["id"] == "e3"


def test_save_block_assignment_writes_manifest(tmp_path):
    manifest = {"entries": [{"id": "e1"}]}
    mp = tmp_path / "manifest.json"
    _write(mp, manifest)

    save_block_assignment(mp, "e1", "blk-01")

    data = json.loads(mp.read_text(encoding="utf-8"))
    assert data["entries"][0]["manual_timeline_block_id"] == "blk-01"


def test_save_block_assignment_none_removes_field(tmp_path):
    manifest = {"entries": [{"id": "e1", "manual_timeline_block_id": "blk-01"}]}
    mp = tmp_path / "manifest.json"
    _write(mp, manifest)

    save_block_assignment(mp, "e1", None)

    data = json.loads(mp.read_text(encoding="utf-8"))
    assert "manual_timeline_block_id" not in data["entries"][0]
```

- [ ] **Step 1.2: Rodar — confirmar que falham com ImportError**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× `ImportError: cannot import name 'load_timeline_data'`

- [ ] **Step 1.3: Criar `src/ui/timeline_dashboard.py` com as funções puras**

```python
from __future__ import annotations

import json
import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.models.core import SubjectProfile
from src.ui.theme import apply_theme_to_toplevel

logger = logging.getLogger(__name__)

_DATE_PREFIX_RE = re.compile(r"^(\d{1,2})\.(\d{2})\s+")


def load_timeline_data(
    manifest_path: Path,
    timeline_index_path: Path,
) -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    """Returns (blocks, entries_by_block_id, unmapped_entries)."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_index_path.read_text(encoding="utf-8"))

    blocks: list[dict] = list(timeline.get("blocks") or [])
    entries: list[dict] = list(manifest.get("entries") or [])

    block_ids = {b["id"] for b in blocks if b.get("id")}
    entries_by_block_id: dict[str, list[dict]] = {b["id"]: [] for b in blocks if b.get("id")}
    unmapped: list[dict] = []

    for entry in entries:
        manual_id = str(entry.get("manual_timeline_block_id") or "").strip()
        auto_tags = list(entry.get("auto_tags") or [])
        auto_block_id = next(
            (t[len("bloco:"):] for t in auto_tags if t.startswith("bloco:")),
            "",
        )
        assigned_id = manual_id or auto_block_id
        if assigned_id and assigned_id in block_ids:
            entries_by_block_id[assigned_id].append(entry)
        else:
            unmapped.append(entry)

    return blocks, entries_by_block_id, unmapped


def save_block_assignment(
    manifest_path: Path,
    entry_id: str,
    block_id: Optional[str],
) -> None:
    """Persiste manual_timeline_block_id no manifest. block_id=None remove o campo."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("entries") or []:
        if entry.get("id") == entry_id:
            if block_id:
                entry["manual_timeline_block_id"] = block_id
            else:
                entry.pop("manual_timeline_block_id", None)
            break
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- [ ] **Step 1.4: Rodar testes — confirmar que passam**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 1.5: Commit**

```bash
git add tests/test_timeline_dashboard_data.py src/ui/timeline_dashboard.py
git commit -m "feat(ui): add load_timeline_data and save_block_assignment pure functions"
```

---

## Task 2: Skeleton do TimelineDashboard (Toplevel + toolbar + canvas scrollável)

**Arquivo:** `src/ui/timeline_dashboard.py` (continua)

- [ ] **Step 2.1: Adicionar a classe `TimelineDashboard` ao final do arquivo**

Acrescentar após as funções puras:

```python
class TimelineDashboard(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        subject: SubjectProfile,
        enqueue_reprocess_fn: Callable[[], None],
    ):
        super().__init__(parent)
        self.title(f"📅 Cronograma — {subject.name or 'Repositório'}")
        self.geometry("900x620")
        self.minsize(700, 480)

        self._subject = subject
        self._enqueue_reprocess_fn = enqueue_reprocess_fn
        self._repo_root = Path(subject.repo_root) if getattr(subject, "repo_root", "") else None
        self._dirty = False

        p = apply_theme_to_toplevel(self, parent)
        self._p = p
        self.configure(bg=p["bg"])

        self._build_toolbar(p)
        self._build_scroll_area(p)
        self._reload()

    # ------------------------------------------------------------------ toolbar

    def _build_toolbar(self, p: dict) -> None:
        bar = tk.Frame(self, bg=p["header_bg"], pady=4)
        bar.pack(fill="x", side="top")

        repo_label = str(self._repo_root or "—")
        tk.Label(
            bar,
            text=f"Repositório: {repo_label}",
            bg=p["header_bg"],
            fg=p["muted"],
            font=("", 10),
        ).pack(side="left", padx=10)

        self._btn_reprocess = ttk.Button(
            bar,
            text="🔄 Reprocessar",
            command=self._on_reprocess,
        )
        self._btn_reprocess.pack(side="right", padx=6)
        self._btn_reprocess.pack_forget()  # oculto até primeira atribuição

        ttk.Button(bar, text="↺ Recarregar", command=self._reload).pack(side="right", padx=4)

    # ---------------------------------------------------------------- scroll area

    def _build_scroll_area(self, p: dict) -> None:
        container = tk.Frame(self, bg=p["bg"])
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=p["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._scroll_frame = tk.Frame(self._canvas, bg=p["bg"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw"
        )

        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ----------------------------------------------------------------- load/reload

    def _reload(self) -> None:
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        if not self._repo_root:
            self._show_error("Selecione um repositório com build gerado.")
            return

        manifest_path = self._repo_root / "manifest.json"
        timeline_path = self._repo_root / "course" / ".timeline_index.json"

        if not manifest_path.exists():
            self._show_error("Build não encontrado — gere o repositório primeiro.")
            return
        if not timeline_path.exists():
            self._show_error("Nenhum cronograma detectado — o SYLLABUS foi carregado?")
            return

        try:
            blocks, entries_by_block_id, unmapped = load_timeline_data(
                manifest_path, timeline_path
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.exception("Erro ao ler artefatos do TimelineDashboard")
            self._show_error("Erro ao ler artefatos — veja o log.")
            return

        self._blocks = blocks
        self._entries_by_block_id = entries_by_block_id
        self._unmapped = unmapped
        self._manifest_path = manifest_path
        self._build_accordion()

    def _show_error(self, msg: str) -> None:
        tk.Label(
            self._scroll_frame,
            text=msg,
            bg=self._p["bg"],
            fg=self._p["warning"],
            font=("", 11),
            wraplength=600,
        ).pack(expand=True, pady=60)

    # ------------------------------------------------------------------ reprocess

    def _on_reprocess(self) -> None:
        self._enqueue_reprocess_fn()
        self._btn_reprocess.pack_forget()
        self._dirty = False

    def _reveal_reprocess_btn(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._btn_reprocess.pack(side="right", padx=6)

    # ------------------------------------------------------------------ accordion placeholder

    def _build_accordion(self) -> None:
        pass  # implementado na Task 3
```

- [ ] **Step 2.2: Rodar testes — confirmar que continuam passando**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 2.3: Commit**

```bash
git add src/ui/timeline_dashboard.py
git commit -m "feat(ui): add TimelineDashboard Toplevel skeleton with toolbar and scroll area"
```

---

## Task 3: Accordion — linhas de bloco

**Arquivo:** `src/ui/timeline_dashboard.py`

- [ ] **Step 3.1: Substituir `_build_accordion` pelo código real**

Substituir o método `_build_accordion` placeholder pelo código abaixo. Adicionar também `_build_block_row` e `_build_block_content`:

```python
    def _build_accordion(self) -> None:
        p = self._p
        blocks = self._blocks or []
        block_ids = [b["id"] for b in blocks if b.get("id")]

        for block in blocks:
            self._build_block_row(block, block_ids)

        # seção sem bloco no rodapé
        tk.Frame(self._scroll_frame, bg=p["border"], height=2).pack(fill="x", pady=(8, 0))
        self._build_unmapped_section()

    def _build_block_row(self, block: dict, all_block_ids: list[str]) -> None:
        p = self._p
        block_id = str(block.get("id") or "")
        period_label = str(block.get("period_label") or block_id)
        unit_slug = str(block.get("unit_slug") or "")
        topic_label = str(block.get("primary_topic_label") or "")

        entries = list(self._entries_by_block_id.get(block_id) or [])
        n_entries = len(entries)
        has_gap = n_entries == 0

        # header frame
        header = tk.Frame(self._scroll_frame, bg=p["frame_bg"], cursor="hand2")
        header.pack(fill="x", padx=0, pady=(0, 1))

        arrow_var = tk.StringVar(value="▶")
        arrow_lbl = tk.Label(header, textvariable=arrow_var, bg=p["frame_bg"], fg=p["muted"], width=2)
        arrow_lbl.pack(side="left", padx=(8, 2), pady=6)

        title_color = p["warning"] if has_gap else p["fg"]
        title_text = period_label
        if topic_label:
            title_text += f" — {topic_label}"
        tk.Label(header, text=title_text, bg=p["frame_bg"], fg=title_color, font=("", 10, "bold"), anchor="w").pack(
            side="left", pady=6
        )

        if unit_slug:
            tk.Label(
                header,
                text=f"  {unit_slug}",
                bg=p["frame_bg"],
                fg=p["muted"],
                font=("", 9),
            ).pack(side="left", padx=(4, 0), pady=6)

        badge_text = f"⚠ {n_entries} arquivo(s)" if has_gap else f"{n_entries} arquivo(s)"
        badge_color = p["warning"] if has_gap else p["success"]
        tk.Label(header, text=badge_text, bg=p["frame_bg"], fg=badge_color, font=("", 9)).pack(
            side="right", padx=12, pady=6
        )

        # content frame (colapsável)
        content = tk.Frame(self._scroll_frame, bg=p["bg"])

        def toggle(_event=None):
            if content.winfo_ismapped():
                content.pack_forget()
                arrow_var.set("▶")
            else:
                content.pack(fill="x", padx=0, pady=(0, 2))
                arrow_var.set("▼")

        header.bind("<Button-1>", toggle)
        for child in header.winfo_children():
            child.bind("<Button-1>", toggle)

        if entries:
            for entry in entries:
                self._build_entry_row(content, entry, block_id, all_block_ids)
```

- [ ] **Step 3.2: Rodar testes**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 3.3: Commit**

```bash
git add src/ui/timeline_dashboard.py
git commit -m "feat(ui): add accordion block rows to TimelineDashboard"
```

---

## Task 4: Linhas de arquivo com dropdown de atribuição

**Arquivo:** `src/ui/timeline_dashboard.py`

- [ ] **Step 4.1: Adicionar `_build_entry_row` à classe**

Adicionar o método após `_build_block_row`:

```python
    def _build_entry_row(
        self,
        parent: tk.Widget,
        entry: dict,
        current_block_id: str,
        all_block_ids: list[str],
    ) -> None:
        p = self._p
        entry_id = str(entry.get("id") or "")
        title = str(entry.get("title") or entry.get("source_path") or "—")
        source_path = str(entry.get("source_path") or "")
        confidence = float(entry.get("unit_match_confidence") or 0.0)
        is_manual = bool(str(entry.get("manual_timeline_block_id") or "").strip())

        row = tk.Frame(parent, bg=p["input_bg"])
        row.pack(fill="x", padx=24, pady=2)

        # ícone por tipo
        file_type = str(entry.get("file_type") or "")
        icon = "🔗" if file_type in {"url", "github-repo"} else "📄"
        tk.Label(row, text=icon, bg=p["input_bg"], fg=p["fg"]).pack(side="left", padx=(6, 2), pady=4)

        tk.Label(
            row,
            text=title,
            bg=p["input_bg"],
            fg=p["fg"],
            font=("", 9),
            anchor="w",
        ).pack(side="left", padx=(0, 8), pady=4, fill="x", expand=True)

        # badge de confiança
        if confidence >= 0.80:
            conf_color = p["success"]
        elif confidence >= 0.50:
            conf_color = p["accent"]
        else:
            conf_color = p["warning"]
        tk.Label(
            row,
            text=f"conf {confidence:.2f}",
            bg=p["input_bg"],
            fg=conf_color,
            font=("", 8),
        ).pack(side="left", padx=4, pady=4)

        # badge DD.MM
        stem = Path(source_path).stem
        if _DATE_PREFIX_RE.match(stem):
            tk.Label(
                row,
                text="🗓 DD.MM",
                bg=p["input_bg"],
                fg=p["accent"],
                font=("", 8),
            ).pack(side="left", padx=4, pady=4)

        # badge manual override
        if is_manual:
            tk.Label(row, text="✎", bg=p["input_bg"], fg=p["accent2"], font=("", 8)).pack(
                side="left", padx=2, pady=4
            )

        # dropdown
        block_labels = ["— remover atribuição"] + [
            self._block_label(b)
            for b in (self._blocks or [])
            if b.get("id")
        ]
        block_values = [""] + [b["id"] for b in (self._blocks or []) if b.get("id")]

        current_idx = (block_values.index(current_block_id) if current_block_id in block_values else 0)
        var = tk.StringVar(value=block_labels[current_idx])

        combo = ttk.Combobox(row, textvariable=var, values=block_labels, state="readonly", width=28, font=("", 8))
        combo.pack(side="right", padx=(4, 6), pady=4)

        def on_select(_event=None):
            selected_label = var.get()
            idx = block_labels.index(selected_label) if selected_label in block_labels else 0
            new_block_id: Optional[str] = block_values[idx] if idx < len(block_values) else None
            if not new_block_id:
                new_block_id = None
            try:
                save_block_assignment(self._manifest_path, entry_id, new_block_id)
                self._reveal_reprocess_btn()
            except Exception:
                logger.exception("Erro ao salvar atribuição de bloco para entry %s", entry_id)

        combo.bind("<<ComboboxSelected>>", on_select)

    def _block_label(self, block: dict) -> str:
        period = str(block.get("period_label") or block.get("id") or "")
        topic = str(block.get("primary_topic_label") or "")
        return f"{period} — {topic}" if topic else period
```

- [ ] **Step 4.2: Rodar testes**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 4.3: Commit**

```bash
git add src/ui/timeline_dashboard.py
git commit -m "feat(ui): add entry rows with confidence badge and block assignment dropdown"
```

---

## Task 5: Seção "Sem bloco atribuído" no rodapé

**Arquivo:** `src/ui/timeline_dashboard.py`

- [ ] **Step 5.1: Adicionar `_build_unmapped_section` e `_build_unmapped_entry_row`**

Adicionar os dois métodos à classe:

```python
    def _build_unmapped_section(self) -> None:
        p = self._p
        unmapped = self._unmapped or []
        n = len(unmapped)
        if n == 0:
            return

        block_ids = [b["id"] for b in (self._blocks or []) if b.get("id")]

        header = tk.Frame(self._scroll_frame, bg=p["frame_bg"], cursor="hand2")
        header.pack(fill="x", padx=0, pady=(0, 1))

        arrow_var = tk.StringVar(value="▶")
        tk.Label(header, textvariable=arrow_var, bg=p["frame_bg"], fg=p["warning"], width=2).pack(
            side="left", padx=(8, 2), pady=6
        )
        tk.Label(
            header,
            text="⚠ Sem bloco atribuído",
            bg=p["frame_bg"],
            fg=p["warning"],
            font=("", 10, "bold"),
        ).pack(side="left", pady=6)
        tk.Label(
            header,
            text=f"{n} arquivo(s)",
            bg=p["frame_bg"],
            fg=p["warning"],
            font=("", 9),
        ).pack(side="right", padx=12, pady=6)

        content = tk.Frame(self._scroll_frame, bg=p["bg"])

        def toggle(_event=None):
            if content.winfo_ismapped():
                content.pack_forget()
                arrow_var.set("▶")
            else:
                content.pack(fill="x", padx=0, pady=(0, 2))
                arrow_var.set("▼")

        header.bind("<Button-1>", toggle)
        for child in header.winfo_children():
            child.bind("<Button-1>", toggle)

        for entry in unmapped:
            self._build_unmapped_entry_row(content, entry, block_ids)

    def _build_unmapped_entry_row(
        self, parent: tk.Widget, entry: dict, all_block_ids: list[str]
    ) -> None:
        p = self._p
        entry_id = str(entry.get("id") or "")
        title = str(entry.get("title") or entry.get("source_path") or "—")
        source_path = str(entry.get("source_path") or "")

        row = tk.Frame(parent, bg=p["input_bg"])
        row.pack(fill="x", padx=24, pady=2)

        file_type = str(entry.get("file_type") or "")
        icon = "🔗" if file_type in {"url", "github-repo"} else "📄"
        tk.Label(row, text=icon, bg=p["input_bg"], fg=p["fg"]).pack(side="left", padx=(6, 2), pady=4)

        stem = Path(source_path).stem
        has_date = bool(_DATE_PREFIX_RE.match(stem))

        tk.Label(row, text=title, bg=p["input_bg"], fg=p["fg"], font=("", 9), anchor="w").pack(
            side="left", padx=(0, 8), pady=4, fill="x", expand=True
        )

        if has_date:
            tk.Label(row, text="🗓 DD.MM", bg=p["input_bg"], fg=p["accent"], font=("", 8)).pack(
                side="left", padx=4, pady=4
            )

        block_labels = ["— sem bloco —"] + [self._block_label(b) for b in (self._blocks or []) if b.get("id")]
        block_values = [""] + [b["id"] for b in (self._blocks or []) if b.get("id")]

        var = tk.StringVar(value=block_labels[0])
        combo = ttk.Combobox(row, textvariable=var, values=block_labels, state="readonly", width=28, font=("", 8))
        combo.pack(side="right", padx=(4, 6), pady=4)

        def on_select(_event=None):
            selected_label = var.get()
            idx = block_labels.index(selected_label) if selected_label in block_labels else 0
            new_block_id: Optional[str] = block_values[idx] if idx > 0 and idx < len(block_values) else None
            if not new_block_id:
                return
            try:
                save_block_assignment(self._manifest_path, entry_id, new_block_id)
                self._reveal_reprocess_btn()
                self._reload()
            except Exception:
                logger.exception("Erro ao salvar atribuição de bloco para entry %s", entry_id)

        combo.bind("<<ComboboxSelected>>", on_select)
```

- [ ] **Step 5.2: Rodar testes**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 5.3: Commit**

```bash
git add src/ui/timeline_dashboard.py
git commit -m "feat(ui): add unmapped entries section at bottom of TimelineDashboard"
```

---

## Task 6: Wiring em app.py

**Arquivo:** `src/ui/app.py`

- [ ] **Step 6.1: Adicionar import no topo de `app.py`**

Localizar o bloco de imports de UI (linha ~34) e adicionar após `from src.ui.repo_dashboard import RepoDashboard, collect_repo_metrics`:

```python
from src.ui.timeline_dashboard import TimelineDashboard
```

- [ ] **Step 6.2: Adicionar item de menu ao `backlog_repo_menu`**

Localizar (linha ~494):
```python
backlog_repo_menu.add_command(label="📦 Consolidar Unidade...", command=self._open_consolidate_dialog)
```

Adicionar logo após essa linha:
```python
backlog_repo_menu.add_command(label="📅 Timeline", command=self._open_timeline_dashboard)
```

- [ ] **Step 6.3: Adicionar o método `_open_timeline_dashboard`**

Localizar o método `_open_consolidate_dialog` (linha ~2297) e adicionar logo antes dele:

```python
def _open_timeline_dashboard(self) -> None:
    repo_dir = self._repo_dir_from_active_subject()
    if not repo_dir:
        messagebox.showinfo(APP_NAME, "Selecione uma matéria com repositório configurado.")
        return
    active_name = self._var_active_subject.get()
    subject = self.subject_store.get(active_name) if active_name != "(nenhuma)" else None
    if not subject:
        messagebox.showinfo(APP_NAME, "Selecione uma matéria com repositório configurado.")
        return
    TimelineDashboard(
        self,
        subject=subject,
        enqueue_reprocess_fn=self.enqueue_current_repo_refresh,
    )
```

- [ ] **Step 6.4: Rodar todos os testes**

```
pytest tests/test_timeline_dashboard_data.py -v
```
Esperado: 3× PASSED

- [ ] **Step 6.5: Commit final**

```bash
git add src/ui/app.py
git commit -m "feat(ui): wire TimelineDashboard into Repo menu in app.py"
```

---

## Self-Review

**Spec coverage:**
- ✅ Accordion layout — Task 3
- ✅ Dropdown por arquivo — Task 4
- ✅ Janela Toplevel — Task 2
- ✅ Seção sem bloco no rodapé — Task 5
- ✅ Entrada via `🗂 Repo → 📅 Timeline` — Task 6
- ✅ Botão Reprocessar oculto, aparece após atribuição — Task 2 (`_reveal_reprocess_btn`)
- ✅ Tratamento de erros (manifest ausente, timeline ausente, JSON inválido) — Task 2 (`_reload`)
- ✅ Badge DD.MM — Tasks 4 e 5
- ✅ Badge de confiança — Task 4
- ✅ 3 testes de dados — Task 1
- ✅ `apply_theme_to_toplevel` — Task 2

**Tipo consistency:**
- `load_timeline_data` retorna `tuple[list[dict], dict[str, list[dict]], list[dict]]` — consistente em Task 1 (definição) e Task 2 (`_reload`)
- `save_block_assignment(manifest_path, entry_id, block_id)` — assinatura consistente em Task 1 (definição), Task 4 e Task 5 (uso)
- `_block_label(block)` definido em Task 4, usado em Tasks 4 e 5

**Placeholders:** nenhum
