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
