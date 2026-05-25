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


class TimelineDashboardView(tk.Frame):
    """Embeddable timeline dashboard. Pass a callable that returns the active subject."""

    def __init__(
        self,
        parent: tk.Widget,
        get_subject_fn: Callable[[], Optional[SubjectProfile]],
        enqueue_reprocess_fn: Callable[[], None],
    ):
        super().__init__(parent)
        self._get_subject_fn = get_subject_fn
        self._enqueue_reprocess_fn = enqueue_reprocess_fn
        self._subject: Optional[SubjectProfile] = None
        self._repo_root: Optional[Path] = None
        self._dirty = False

        p = apply_theme_to_toplevel(self, parent)
        self._p = p
        self.configure(bg=p["bg"])

        self._build_toolbar(p)
        self._build_scroll_area(p)
        self.refresh()

    def refresh(self) -> None:
        """Re-read active subject and reload UI. Safe to call after subject change."""
        self._subject = self._get_subject_fn()
        self._repo_root = (
            Path(self._subject.repo_root)
            if self._subject and getattr(self._subject, "repo_root", "")
            else None
        )
        self._dirty = False
        if hasattr(self, "_btn_reprocess"):
            self._btn_reprocess.pack_forget()
        self._reload()

    # ------------------------------------------------------------------ toolbar

    def _build_toolbar(self, p: dict) -> None:
        bar = tk.Frame(self, bg=p["header_bg"], pady=4)
        bar.pack(fill="x", side="top")

        self._repo_label_var = tk.StringVar(value="Repositório: —")
        tk.Label(
            bar,
            textvariable=self._repo_label_var,
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

        ttk.Button(bar, text="↺ Recarregar", command=self.refresh).pack(side="right", padx=4)

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
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

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

        self._repo_label_var.set(f"Repositório: {self._repo_root or '—'}")

        if not self._repo_root:
            self._show_error("Selecione uma matéria com repositório gerado.")
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

    def _build_unmapped_section(self) -> None:
        p = self._p
        unmapped = self._unmapped or []
        n = len(unmapped)
        if n == 0:
            return

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
            self._build_unmapped_entry_row(content, entry)

    def _build_unmapped_entry_row(
        self, parent: tk.Widget, entry: dict
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
