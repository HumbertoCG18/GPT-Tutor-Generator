"""Image Curator — UI for curating and describing images from PDFs."""

import hashlib
import json
import logging
import re
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from PIL import Image, ImageTk

from src.builder.image_classifier import (
    classify_image,
    extract_page_number,
    group_images_by_page,
)
from src.builder.image_markdown import (
    _IMAGE_DESC_BLOCK_RE,
    _image_curation_heading as _image_curation_heading_label,
    _low_token_inject_image_descriptions,
)

logger = logging.getLogger(__name__)

IMAGE_TYPES = ["diagrama", "tabela", "fórmula", "código", "genérico", "decorativa", "extração-latex"]


def _image_curator_layout_mode(width: int) -> str:
    if width >= 1400:
        return "wide"
    if width >= 980:
        return "medium"
    return "stacked"


def _page_sort_key(page_num: Optional[int]) -> int:
    return page_num if page_num is not None else 9999


def _remove_images_from_curation(curation: dict, page_key: str, filenames: List[str]) -> dict:
    """Remove image records from a page and prune empty page state."""
    page_data = curation.get("pages", {}).get(page_key, {})
    images_data = page_data.get("images", {})
    for fname in filenames:
        images_data.pop(fname, None)

    if not images_data and page_key in curation.get("pages", {}):
        curation["pages"].pop(page_key, None)

    if not curation.get("pages"):
        curation["status"] = "pending"
        curation["curated_at"] = None

    return curation


def _selected_image_names(image_widgets: Dict[str, dict]) -> List[str]:
    """Return filenames currently marked for bulk selection."""
    return [
        fname
        for fname, widgets in image_widgets.items()
        if widgets.get("selected_var") is not None and widgets["selected_var"].get()
    ]


def _uses_zero_based_page_pattern(images: List[Path]) -> bool:
    return any("_page_" in img.name.lower() for img in images)


def _resolve_curation_page_key(curation: dict, page_num: Optional[int], images: List[Path]) -> str:
    """Resolve the manifest page key, tolerating legacy zero-based keys."""
    page_key = str(page_num) if page_num is not None else "none"
    if page_key in curation.get("pages", {}):
        return page_key
    if page_num is not None and _uses_zero_based_page_pattern(images):
        legacy_key = str(page_num - 1)
        if legacy_key in curation.get("pages", {}):
            return legacy_key
    return page_key


def _migrate_curation_page_key(curation: dict, page_num: Optional[int], images: List[Path]) -> str:
    """Migrate legacy zero-based page keys to the normalized one-based key."""
    page_key = str(page_num) if page_num is not None else "none"
    resolved_key = _resolve_curation_page_key(curation, page_num, images)
    if resolved_key != page_key and resolved_key in curation.get("pages", {}):
        curation.setdefault("pages", {})[page_key] = curation["pages"].pop(resolved_key)
    return page_key


def _file_sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _build_duplicate_index(groups: Dict[Optional[int], List[Path]]) -> Dict[str, dict]:
    """Index exact duplicate images across pages of the same entry."""
    by_hash: Dict[str, List[tuple[Optional[int], Path]]] = {}
    for page_num, images in groups.items():
        for img in images:
            try:
                digest = _file_sha1(img)
            except Exception:
                continue
            by_hash.setdefault(digest, []).append((page_num, img))

    duplicate_info: Dict[str, dict] = {}
    for digest, occurrences in by_hash.items():
        if len(occurrences) < 2:
            continue
        pages = sorted({page for page, _ in occurrences}, key=_page_sort_key)
        for page_num, img in occurrences:
            other_pages = [p for p in pages if p != page_num]
            duplicate_info[img.name] = {
                "hash": digest,
                "pages": pages,
                "other_pages": other_pages,
                "count": len(occurrences),
            }
    return duplicate_info


def _resolve_entry_pdf_path(repo_dir: Path, entry_data: dict) -> Optional[Path]:
    """Resolve the exact PDF for an entry using manifest-backed paths."""
    for raw_value in (
        entry_data.get("raw_target"),
        entry_data.get("source_path"),
    ):
        candidate_text = str(raw_value or "").strip()
        if not candidate_text:
            continue
        candidate = Path(candidate_text)
        if not candidate.is_absolute():
            candidate = repo_dir / candidate
        if candidate.exists() and candidate.suffix.lower() == ".pdf":
            return candidate
    return None


def _inject_all_image_descriptions_from_manifest(repo_dir: Path, manifest: dict) -> None:
    """Reinject curated image descriptions into the preferred markdown targets."""
    entries = manifest.get("entries", []) or []
    for entry_data in entries:
        curation = entry_data.get("image_curation")
        if not curation:
            continue

        status = (curation.get("status") or "").strip().lower()
        if status not in {"described", "curated"} and not curation.get("pages"):
            continue

        candidate_paths = []
        for key in ("approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"):
            rel_path = str(entry_data.get(key) or "").strip()
            if not rel_path:
                continue
            path = repo_dir / rel_path
            if path.exists():
                candidate_paths.append(path)

        if not candidate_paths:
            entry_id = str(entry_data.get("id") or "").strip()
            if entry_id:
                for path in repo_dir.rglob("*.md"):
                    try:
                        snippet = path.read_text(encoding="utf-8", errors="replace")[:4096]
                    except Exception:
                        continue
                    if f'entry_id: "{entry_id}"' in snippet or f"entry_id: '{entry_id}'" in snippet:
                        candidate_paths.append(path)
                        break

        seen_targets = set()
        for path in candidate_paths:
            if path in seen_targets or not path.exists():
                continue
            seen_targets.add(path)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                new_text = _low_token_inject_image_descriptions(
                    text,
                    curation,
                    desc_block_re=_IMAGE_DESC_BLOCK_RE,
                    image_heading=_image_curation_heading_label,
                )
                if new_text != text:
                    path.write_text(new_text, encoding="utf-8")
            except Exception as exc:
                logger.warning("Could not inject image descriptions into %s: %s", path, exc)


class ImageCurator(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._theme_name = (
            parent.config_obj.get("theme")
            if hasattr(parent, "config_obj")
            else "dark"
        )
        self._parent = parent

        self.title("Image Curator")
        self.geometry("1400x800")
        self.minsize(1000, 600)

        # State
        self._manifest_path = self.repo_dir / "manifest.json"
        self._images_dir = self.repo_dir / "content" / "images"
        self._manifest: dict = {}
        self._entries_with_images: List[dict] = []
        self._current_entry: Optional[dict] = None
        self._current_page: Optional[int] = None
        self._thumbnail_refs: List[ImageTk.PhotoImage] = []  # prevent GC
        self._image_widgets: Dict[str, dict] = {}  # fname -> {type_var, include_var, selected_var, path}
        self._vision_client = None  # persistent client for both prompts
        self._vision_busy = False   # prevent concurrent requests
        self._layout_mode = ""

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_manifest()
        self.bind("<Delete>", self._on_delete_key)
        self.bind("<Configure>", self._on_layout_change)
        self.after_idle(self._apply_responsive_layout)

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)

        # Toolbar
        toolbar = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        toolbar.pack(fill="x", side="top")
        tk.Label(
            toolbar,
            text="Image Curator",
            bg=p["header_bg"],
            fg=p["header_fg"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        ttk.Button(
            toolbar, text="Gerar Descrições", command=self._generate_descriptions
        ).pack(side="right", padx=5)
        ttk.Button(
            toolbar, text="Pré-classificar", command=self._preclassify
        ).pack(side="right", padx=5)
        ttk.Button(toolbar, text="Salvar", command=self._save_curation).pack(
            side="right", padx=5
        )

        # Status bar
        self.status_var = tk.StringVar(
            value="Selecione um entry para curar imagens"
        )
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            bg=p["header_bg"],
            fg=p["header_fg"],
            anchor="w",
            padx=12,
            pady=4,
            font=("Segoe UI", 9),
        )
        status_bar.pack(fill="x", side="bottom")

        # PanedWindow
        self._main_paned = ttk.PanedWindow(self, orient="horizontal")
        self._main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel: entry + page tree
        left_frame = ttk.Frame(self._main_paned)
        self._main_paned.add(left_frame, weight=1)

        ttk.Label(
            left_frame, text="Entries / Páginas", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self._tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(
            left_frame, orient="vertical", command=self._tree.yview
        )
        self._tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Right side: vertical paned — images top, PDF bottom
        self._right_paned = ttk.PanedWindow(self._main_paned, orient="vertical")
        self._main_paned.add(self._right_paned, weight=3)

        # Top: image cards
        images_frame = ttk.Frame(self._right_paned)
        self._right_paned.add(images_frame, weight=2)

        ttk.Label(
            images_frame, text="Imagens", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        canvas_frame = ttk.Frame(images_frame)
        canvas_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            canvas_frame, bg=p["frame_bg"], highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            canvas_frame, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._cards_frame = tk.Frame(self._canvas, bg=p["frame_bg"])
        self._cards_window = self._canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        self._cards_frame.bind("<Configure>", self._on_cards_frame_configure)
        self._canvas.bind("<Configure>", self._on_cards_canvas_configure)

        # Bottom: PDF viewer
        pdf_frame = ttk.Frame(self._right_paned)
        self._right_paned.add(pdf_frame, weight=1)

        pdf_header = tk.Frame(pdf_frame, bg=p["frame_bg"])
        pdf_header.pack(fill="x")
        ttk.Label(pdf_header, text="Página do PDF").pack(side="left", padx=5)
        self._pdf_zoom_var = tk.DoubleVar(value=1.0)
        ttk.Label(pdf_header, text="Zoom:").pack(side="left", padx=(10, 2))
        ttk.Spinbox(
            pdf_header,
            from_=0.5,
            to=3.0,
            increment=0.25,
            textvariable=self._pdf_zoom_var,
            width=5,
            command=self._refresh_pdf_page,
        ).pack(side="left")

        self._crop_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pdf_header,
            text="Capturar região",
            variable=self._crop_mode,
            command=self._toggle_crop_mode,
        ).pack(side="left", padx=(10, 0))

        self._crop_rect_id = None
        self._crop_start = None

        pdf_canvas_frame = ttk.Frame(pdf_frame)
        pdf_canvas_frame.pack(fill="both", expand=True)
        self._pdf_canvas = tk.Canvas(
            pdf_canvas_frame, bg=p["frame_bg"], highlightthickness=0
        )
        pdf_vscroll = ttk.Scrollbar(
            pdf_canvas_frame, orient="vertical", command=self._pdf_canvas.yview
        )
        pdf_hscroll = ttk.Scrollbar(
            pdf_canvas_frame, orient="horizontal", command=self._pdf_canvas.xview
        )
        self._pdf_canvas.configure(
            yscrollcommand=pdf_vscroll.set, xscrollcommand=pdf_hscroll.set
        )
        pdf_hscroll.pack(side="bottom", fill="x")
        pdf_vscroll.pack(side="right", fill="y")
        self._pdf_canvas.pack(side="left", fill="both", expand=True)
        self._pdf_page_img_ref = None  # prevent GC

    def _on_cards_frame_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_cards_canvas_configure(self, event):
        try:
            self._canvas.itemconfig(self._cards_window, width=event.width)
        except tk.TclError:
            pass

    def _on_layout_change(self, _event=None):
        self.after_idle(self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        mode = _image_curator_layout_mode(self.winfo_width())
        if mode == self._layout_mode:
            return
        self._layout_mode = mode

        orient = "vertical" if mode == "stacked" else "horizontal"
        try:
            self._main_paned.configure(orient=orient)
        except tk.TclError:
            return

        total_width = max(self.winfo_width() - 40, 1)
        total_height = max(self.winfo_height() - 140, 1)
        try:
            if mode == "wide":
                self._main_paned.sashpos(0, min(340, max(total_width // 4, 260)))
                self._right_paned.sashpos(0, max(int(total_height * 0.58), 320))
            elif mode == "medium":
                self._main_paned.sashpos(0, min(260, max(total_width // 4, 220)))
                self._right_paned.sashpos(0, max(int(total_height * 0.52), 280))
            else:
                self._main_paned.sashpos(0, max(int(total_height * 0.30), 220))
                self._right_paned.sashpos(0, max(int(total_height * 0.44), 240))
        except tk.TclError:
            pass

    # ── Data Loading ───────────────────────────────────────────────────

    def _load_manifest(self):
        """Load manifest.json and populate the tree with entries that have images."""
        if not self._manifest_path.exists():
            self.status_var.set(
                "manifest.json não encontrado. Processe os PDFs primeiro."
            )
            return
        if not self._images_dir.exists():
            self.status_var.set("Pasta content/images/ não encontrada.")
            return

        try:
            self._manifest = json.loads(
                self._manifest_path.read_text(encoding="utf-8")
            )
        except Exception as e:
            self.status_var.set(f"Erro ao ler manifest: {e}")
            return

        # Find entries that have images in content/images/ (including scanned/)
        _IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        all_images = [
            f
            for f in self._images_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in _IMG_EXTS
        ]
        if not all_images:
            self.status_var.set("Nenhuma imagem encontrada em content/images/.")
            return

        entries = self._manifest.get("entries", [])
        self._entries_with_images = []
        for entry in entries:
            entry_id = entry.get("id", "")
            if not entry_id:
                continue
            groups = group_images_by_page(self._images_dir, entry_id)
            if not groups:
                continue
            entry["_image_groups"] = groups
            entry["_duplicate_images"] = _build_duplicate_index(groups)
            self._entries_with_images.append(entry)

        self._rebuild_tree()

        self.status_var.set(
            f"{len(self._entries_with_images)} entries com imagens encontradas."
        )

    def _rebuild_tree(
        self,
        selected_entry_id: Optional[str] = None,
        selected_page: Optional[Optional[int]] = None,
    ):
        """Rebuild tree from current in-memory entries and optionally restore selection."""
        self._tree.delete(*self._tree.get_children())
        selected_item = None

        for entry in self._entries_with_images:
            entry_id = entry.get("id", "")
            entry_node = self._tree.insert(
                "",
                "end",
                text=entry.get("title", entry_id),
                values=(entry_id,),
            )
            if selected_entry_id == entry_id and selected_page is None:
                selected_item = entry_node

            groups = entry.get("_image_groups", {})
            for page_num in sorted(groups.keys(), key=_page_sort_key):
                count = len(groups[page_num])
                label = (
                    f"Página {page_num} ({count} imgs)"
                    if page_num is not None
                    else f"Página desconhecida ({count} imgs)"
                )
                page_node = self._tree.insert(
                    entry_node,
                    "end",
                    text=label,
                    values=(
                        entry_id,
                        str(page_num) if page_num is not None else "none",
                    ),
                )
                if selected_entry_id == entry_id and selected_page == page_num:
                    selected_item = page_node

        if selected_item:
            self._tree.selection_set(selected_item)
            self._tree.focus(selected_item)
            self._tree.see(selected_item)

    def _refresh_entry_after_image_change(self, entry_id: str):
        """Reload groups for an entry after file-level mutations and refresh tree/UI."""
        entry = next(
            (e for e in self._entries_with_images if e.get("id") == entry_id),
            None,
        )
        if not entry:
            return

        groups = group_images_by_page(self._images_dir, entry_id)
        if groups:
            entry["_image_groups"] = groups
            entry["_duplicate_images"] = _build_duplicate_index(groups)
            selected_page = self._current_page if self._current_page in groups else next(
                iter(sorted(groups.keys(), key=_page_sort_key)),
                None,
            )
            self._rebuild_tree(entry_id, selected_page)
            self._current_entry = entry
            self._current_page = selected_page
            self._show_images(entry, selected_page, groups.get(selected_page, []))
            return

        self._entries_with_images = [
            e for e in self._entries_with_images if e.get("id") != entry_id
        ]
        if self._current_entry and self._current_entry.get("id") == entry_id:
            self._current_entry = None
            self._current_page = None
            for widget in self._cards_frame.winfo_children():
                widget.destroy()
            self._pdf_canvas.delete("all")
            self.status_var.set("Entry removido do Image Curator: nenhuma imagem restante.")
        self._rebuild_tree()

    # ── Tree Selection ─────────────────────────────────────────────────

    def _on_tree_select(self, event):
        """Handle tree selection — show images for selected page."""
        selection = self._tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self._tree.item(item, "values")
        if not values:
            return

        entry_id = values[0]
        page_str = values[1] if len(values) > 1 else None

        # Find entry
        entry = next(
            (e for e in self._entries_with_images if e.get("id") == entry_id),
            None,
        )
        if not entry:
            return

        self._current_entry = entry
        groups = entry.get("_image_groups", {})

        if page_str is None:
            # Entry-level selection — no page selected yet
            return

        page_num = int(page_str) if page_str != "none" else None
        self._current_page = page_num
        images = groups.get(page_num, [])
        self._show_images(entry, page_num, images)

    # ── Image Cards ────────────────────────────────────────────────────

    def _show_images(self, entry: dict, page_num: Optional[int], images: List[Path]):
        """Display image cards for the selected page."""
        p = self.theme_mgr.palette(self._theme_name)

        # Clear existing cards
        for widget in self._cards_frame.winfo_children():
            widget.destroy()
        self._thumbnail_refs.clear()
        self._image_widgets.clear()

        # Load existing curation data
        curation = entry.get("image_curation", {})
        page_key = _resolve_curation_page_key(curation, page_num, images)
        page_data = curation.get("pages", {}).get(page_key, {})
        include_page = page_data.get("include_page", True)
        curated_images = page_data.get("images", {})
        duplicate_images = entry.get("_duplicate_images", {})

        # Page-level include toggle
        page_frame = tk.Frame(self._cards_frame, bg=p["frame_bg"])
        page_frame.pack(fill="x", padx=5, pady=5)
        page_var = tk.BooleanVar(value=include_page)
        ttk.Checkbutton(
            page_frame,
            text="Incluir esta página",
            variable=page_var,
            command=lambda: self._toggle_page(page_var.get()),
        ).pack(side="left")
        ttk.Button(
            page_frame, text="Selecionar todas", command=lambda: self._set_all_selected(True)
        ).pack(side="right", padx=(4, 0))
        ttk.Button(
            page_frame, text="Limpar seleção", command=lambda: self._set_all_selected(False)
        ).pack(side="right", padx=(4, 0))
        ttk.Button(
            page_frame, text="Remover selecionadas", command=self._delete_selected_images
        ).pack(side="right", padx=(4, 0))

        # Image cards
        row_frame = None
        for idx, img_path in enumerate(images):
            if idx % 3 == 0:
                row_frame = tk.Frame(self._cards_frame, bg=p["frame_bg"])
                row_frame.pack(fill="x", padx=5, pady=5)

            fname = img_path.name
            existing = curated_images.get(fname, {})

            card = tk.Frame(
                row_frame, bg=p["input_bg"], relief="groove", bd=1, padx=8, pady=8
            )
            card.pack(side="left", padx=5, pady=5)

            # Thumbnail
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((200, 200))
                tk_img = ImageTk.PhotoImage(pil_img)
                self._thumbnail_refs.append(tk_img)
                lbl_img = tk.Label(card, image=tk_img, bg=p["input_bg"])
                lbl_img.pack(pady=(0, 5))
                lbl_img.bind(
                    "<Button-1>", lambda e, path=img_path: self._preview_full(path)
                )
            except Exception:
                tk.Label(
                    card, text="[erro ao carregar]", bg=p["input_bg"], fg=p["error"]
                ).pack()

            # Filename
            tk.Label(
                card,
                text=fname,
                bg=p["input_bg"],
                fg=p["muted"],
                font=("Segoe UI", 8),
                wraplength=200,
            ).pack()

            duplicate = duplicate_images.get(fname)
            if duplicate:
                other_pages = duplicate.get("other_pages", [])
                if other_pages:
                    pages_text = ", ".join(
                        f"{p}" if p is not None else "desconhecida"
                        for p in other_pages[:4]
                    )
                    if len(other_pages) > 4:
                        pages_text += ", ..."
                    tk.Label(
                        card,
                        text=f"Duplicada exata em: {pages_text}",
                        bg=p["input_bg"],
                        fg=p["warning"],
                        font=("Segoe UI", 8, "bold"),
                        wraplength=200,
                        justify="left",
                    ).pack(pady=(2, 0))

            # Type dropdown
            type_var = tk.StringVar(value=existing.get("type", "genérico"))
            type_frame = tk.Frame(card, bg=p["input_bg"])
            type_frame.pack(fill="x", pady=2)
            tk.Label(type_frame, text="Tipo:", bg=p["input_bg"], fg=p["fg"]).pack(
                side="left"
            )
            ttk.Combobox(
                type_frame,
                textvariable=type_var,
                values=IMAGE_TYPES,
                state="readonly",
                width=12,
            ).pack(side="left", padx=4)

            # Include checkbox
            include_var = tk.BooleanVar(value=existing.get("include", True))
            ttk.Checkbutton(card, text="Incluir", variable=include_var).pack(
                anchor="w"
            )
            selected_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(card, text="Selecionar", variable=selected_var).pack(
                anchor="w"
            )

            # Description preview (if exists) — click to view full
            desc = existing.get("description")
            if desc:
                desc_preview = desc[:80] + "..." if len(desc) > 80 else desc
                desc_lbl = tk.Label(
                    card,
                    text=desc_preview,
                    bg=p["input_bg"],
                    fg=p["success"],
                    font=("Segoe UI", 8),
                    wraplength=200,
                    justify="left",
                    cursor="hand2",
                )
                desc_lbl.pack(pady=(4, 0))
                desc_lbl.bind(
                    "<Button-1>",
                    lambda e, f=fname, d=desc: self._show_description(f, d),
                )

            # Action buttons
            btn_frame = tk.Frame(card, bg=p["input_bg"])
            btn_frame.pack(fill="x", pady=(6, 0))
            ttk.Button(
                btn_frame, text="Descrever",
                command=lambda fn=fname, ip=img_path: self._describe_single_image(fn, ip),
            ).pack(side="left", padx=(0, 4))
            ttk.Button(
                btn_frame, text="Extrair LaTeX",
                command=lambda fn=fname, ip=img_path: self._extract_latex_single(fn, ip),
            ).pack(side="left", padx=(0, 4))
            ttk.Button(
                btn_frame, text="Remover",
                command=lambda fn=fname, ip=img_path: self._delete_image(fn, ip),
            ).pack(side="left")

            self._image_widgets[fname] = {
                "type_var": type_var,
                "include_var": include_var,
                "selected_var": selected_var,
                "path": img_path,
            }

        page_label = (
            f"Página {page_num}" if page_num is not None else "Página desconhecida"
        )
        self.status_var.set(
            f"{entry.get('title', '')} — {page_label} — {len(images)} imagens"
        )

        # Render corresponding PDF page
        self._render_pdf_page(page_num if page_num is not None else 1)

    # ── Page Context Extraction ────────────────────────────────────────

    def _extract_page_contexts(self, entry_id: str) -> Dict[str, str]:
        """Extract markdown text per page from the entry's markdown file.

        Splits the markdown by page separators (pymupdf4llm inserts ``---`` or
        page-break markers) and returns a dict of ``page_key -> text_content``.
        This context is passed to the Vision model alongside the image.
        """
        contexts: Dict[str, str] = {}

        # Look for the entry's markdown in content/ and staging/
        md_candidates = [
            self.repo_dir / "content" / "curated" / f"{entry_id}.md",
            self.repo_dir / "staging" / "markdown-auto" / "pymupdf4llm" / f"{entry_id}.md",
            self.repo_dir / "staging" / "markdown-auto" / "docling" / f"{entry_id}.md",
            self.repo_dir / "staging" / "markdown-auto" / "marker" / f"{entry_id}.md",
        ]

        md_path = None
        for candidate in md_candidates:
            if candidate.exists():
                md_path = candidate
                break

        if not md_path:
            return contexts

        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            return contexts

        # Split by page separators — pymupdf4llm uses "-----" or form-feeds
        pages = re.split(r"\n-{3,}\n|\n\f\n", text)
        for i, page_text in enumerate(pages, start=1):
            contexts[str(i)] = page_text.strip()

        return contexts

    # ── Vision Client ─────────────────────────────────────────────────

    def _get_vision_client(self):
        """Get or create the configured vision client, checking availability."""
        if self._vision_busy:
            messagebox.showwarning(
                "Image Curator",
                "Já existe uma requisição em andamento. Aguarde.",
                parent=self,
            )
            return None

        if self._vision_client is not None:
            return self._vision_client

        from src.builder.vision_client import get_vision_client

        config = self._parent.config_obj if hasattr(self._parent, "config_obj") else None
        client = get_vision_client(config)
        available, msg = client.check_availability()
        if not available:
            messagebox.showerror("Vision indisponível", msg, parent=self)
            return None

        self._vision_client = client
        return client

    # ── Actions ────────────────────────────────────────────────────────

    def _toggle_page(self, include: bool):
        """Toggle all images on current page."""
        for widgets in self._image_widgets.values():
            widgets["include_var"].set(include)

    def _on_delete_key(self, _event=None):
        selected = _selected_image_names(self._image_widgets)
        if not selected:
            return
        self._delete_selected_images()

    def _set_all_selected(self, selected: bool):
        for widgets in self._image_widgets.values():
            widgets["selected_var"].set(selected)

    def _preview_full(self, image_path: Path):
        """Open full-size image preview in a new window."""
        p = self.theme_mgr.palette(self._theme_name)
        win = tk.Toplevel(self)
        win.title(image_path.name)
        win.configure(bg=p["bg"])

        try:
            pil_img = Image.open(image_path)
            max_w, max_h = 1200, 800
            pil_img.thumbnail((max_w, max_h))
            tk_img = ImageTk.PhotoImage(pil_img)
            lbl = tk.Label(win, image=tk_img, bg=p["bg"])
            lbl.image = tk_img  # prevent GC
            lbl.pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(win, text=f"Erro: {e}", bg=p["bg"], fg=p["error"]).pack(
                padx=20, pady=20
            )

    def _show_description(self, fname: str, description: str):
        """Show full image description in a scrollable window."""
        p = self.theme_mgr.palette(self._theme_name)
        win = tk.Toplevel(self)
        win.title(f"Descrição — {fname}")
        win.geometry("600x400")
        win.configure(bg=p["bg"])

        text_widget = tk.Text(
            win,
            wrap="word",
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        text_widget.insert("1.0", description)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=(0, 10))

    def _render_pdf_page(self, page_num: int):
        """Render a PDF page to the PDF canvas using pymupdf."""
        if not self._current_entry:
            return

        pdf_path = _resolve_entry_pdf_path(self.repo_dir, self._current_entry)

        if not pdf_path:
            self._pdf_canvas.delete("all")
            self._pdf_canvas.create_text(
                10, 10, text="PDF não encontrado.", anchor="nw", fill="gray"
            )
            return

        try:
            import pymupdf

            doc = pymupdf.open(str(pdf_path))
            page_idx = max(0, (page_num or 1) - 1)
            if page_idx >= len(doc):
                page_idx = len(doc) - 1
            page = doc[page_idx]
            zoom = self._pdf_zoom_var.get()
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")

            import io

            pil_img = Image.open(io.BytesIO(img_data))
            tk_img = ImageTk.PhotoImage(pil_img)
            self._pdf_page_img_ref = tk_img

            self._pdf_canvas.delete("all")
            self._pdf_canvas.create_image(0, 0, anchor="nw", image=tk_img)
            self._pdf_canvas.configure(
                scrollregion=(0, 0, pil_img.width, pil_img.height)
            )
            doc.close()
        except Exception as e:
            self._pdf_canvas.delete("all")
            self._pdf_canvas.create_text(
                10,
                10,
                text=f"Erro ao renderizar PDF: {e}",
                anchor="nw",
                fill="gray",
            )

    def _refresh_pdf_page(self):
        """Re-render current PDF page (e.g., after zoom change)."""
        if self._current_page is not None:
            self._render_pdf_page(self._current_page)

    # ── Region Crop ────────────────────────────────────────────────────

    def _toggle_crop_mode(self):
        """Enable or disable crop selection mode on the PDF canvas."""
        if self._crop_mode.get():
            self._pdf_canvas.config(cursor="crosshair")
            self._pdf_canvas.bind("<ButtonPress-1>", self._crop_start_drag)
            self._pdf_canvas.bind("<B1-Motion>", self._crop_drag)
            self._pdf_canvas.bind("<ButtonRelease-1>", self._crop_end_drag)
        else:
            self._pdf_canvas.config(cursor="")
            self._pdf_canvas.unbind("<ButtonPress-1>")
            self._pdf_canvas.unbind("<B1-Motion>")
            self._pdf_canvas.unbind("<ButtonRelease-1>")
            if self._crop_rect_id:
                self._pdf_canvas.delete(self._crop_rect_id)
                self._crop_rect_id = None

    def _crop_start_drag(self, event):
        self._crop_start = (
            self._pdf_canvas.canvasx(event.x),
            self._pdf_canvas.canvasy(event.y),
        )
        if self._crop_rect_id:
            self._pdf_canvas.delete(self._crop_rect_id)

    def _crop_drag(self, event):
        if not self._crop_start:
            return
        x0, y0 = self._crop_start
        x1 = self._pdf_canvas.canvasx(event.x)
        y1 = self._pdf_canvas.canvasy(event.y)
        if self._crop_rect_id:
            self._pdf_canvas.delete(self._crop_rect_id)
        self._crop_rect_id = self._pdf_canvas.create_rectangle(
            x0, y0, x1, y1, outline="#a6e3a1", width=2, dash=(4, 2)
        )

    def _crop_end_drag(self, event):
        if not self._crop_start:
            return
        x0, y0 = self._crop_start
        x1 = self._pdf_canvas.canvasx(event.x)
        y1 = self._pdf_canvas.canvasy(event.y)
        self._crop_start = None

        # Normalize coordinates
        rx0, rx1 = min(x0, x1), max(x0, x1)
        ry0, ry1 = min(y0, y1), max(y0, y1)

        if (rx1 - rx0) < 10 or (ry1 - ry0) < 10:
            return  # too small, ignore

        self._save_cropped_region(rx0, ry0, rx1, ry1)

    def _save_cropped_region(self, x0: float, y0: float, x1: float, y1: float):
        """Crop the selected region from the rendered PDF and save as image."""
        if not self._current_entry or self._current_page is None:
            return

        entry_id = self._current_entry.get("id", "")
        pdf_path = _resolve_entry_pdf_path(self.repo_dir, self._current_entry)

        if not pdf_path:
            return

        try:
            import pymupdf

            doc = pymupdf.open(str(pdf_path))
            page_idx = max(0, self._current_page - 1)
            page = doc[page_idx]
            zoom = self._pdf_zoom_var.get()

            # Convert canvas coords back to PDF coords
            rect = pymupdf.Rect(x0 / zoom, y0 / zoom, x1 / zoom, y1 / zoom)
            mat = pymupdf.Matrix(2.0, 2.0)  # 2x for quality
            pix = page.get_pixmap(matrix=mat, clip=rect)

            # Save to content/images/
            timestamp = datetime.now().strftime("%H%M%S")
            fname = (
                f"{entry_id}-page-{self._current_page:03d}-manual-{timestamp}.png"
            )
            out_path = self._images_dir / fname
            pix.save(str(out_path))
            doc.close()

            # Add to in-memory image groups
            groups = self._current_entry.setdefault("_image_groups", {})
            groups.setdefault(self._current_page, []).append(out_path)

            # Add to curation manifest as pending
            curation = self._current_entry.setdefault(
                "image_curation",
                {"status": "pending", "curated_at": None, "pages": {}},
            )
            page_key = str(self._current_page)
            page_data = curation["pages"].setdefault(
                page_key, {"include_page": True, "images": {}}
            )
            page_data["images"][fname] = {
                "type": "genérico",
                "include": True,
                "description": None,
                "described_at": None,
            }

            # Refresh UI
            self._show_images(
                self._current_entry, self._current_page, groups[self._current_page]
            )
            self.status_var.set(f"Região capturada e salva como '{fname}'.")

            # Disable crop mode
            self._crop_mode.set(False)
            self._toggle_crop_mode()

        except Exception as e:
            messagebox.showerror(
                "Erro", f"Falha ao capturar região:\n{e}", parent=self
            )

    def _delete_image(self, fname: str, img_path: Path):
        """Delete a single image from disk and update tree/manifest state."""
        self._delete_images([(fname, img_path)])

    def _delete_selected_images(self):
        selected_names = _selected_image_names(self._image_widgets)
        selected = [
            (fname, self._image_widgets[fname]["path"])
            for fname in selected_names
        ]
        if not selected:
            messagebox.showinfo(
                "Image Curator",
                "Selecione ao menos uma imagem para remover.",
                parent=self,
            )
            return
        self._delete_images(selected)

    def _delete_images(self, image_items: List[tuple[str, Path]]):
        """Delete one or more images from disk and remove them from curation data."""
        if not self._current_entry:
            return

        count = len(image_items)
        entry_id = self._current_entry.get("id", "")
        curation = self._current_entry.get("image_curation", {})
        page_images = self._current_entry.get("_image_groups", {}).get(self._current_page, [])
        page_key = _migrate_curation_page_key(curation, self._current_page, page_images)
        prompt = (
            f"Remover {count} imagem(ns) permanentemente?\n\n"
            "Isso remove os arquivos de content/images/ e atualiza o manifest."
            if count > 1
            else f"Remover '{image_items[0][0]}' permanentemente?\n\n"
            "Isso remove o arquivo de content/images/ e atualiza o manifest."
        )
        if not messagebox.askyesno("Remover imagem", prompt, parent=self):
            return

        failed = []
        for fname, img_path in image_items:
            try:
                if img_path.exists():
                    img_path.unlink()
            except Exception as e:
                failed.append(f"{fname}: {e}")

        if failed:
            messagebox.showerror(
                "Erro",
                "Não foi possível remover algumas imagens:\n\n" + "\n".join(failed),
                parent=self,
            )
            return

        _remove_images_from_curation(
            curation,
            page_key,
            [fname for fname, _ in image_items],
        )

        self._write_manifest_entry(entry_id)
        self._refresh_entry_after_image_change(entry_id)

        removed_count = count - len(failed)
        if removed_count > 0:
            self.status_var.set(
                f"{removed_count} imagem(ns) removida(s) e árvore atualizada."
            )

    def _preclassify(self):
        """Run heuristic pre-classification on all images for the current entry."""
        if not self._current_entry:
            messagebox.showinfo("Image Curator", "Selecione um entry primeiro.")
            return

        groups = self._current_entry.get("_image_groups", {})
        classified = 0
        for images in groups.values():
            for img_path in images:
                result = classify_image(img_path)
                fname = img_path.name
                if fname in self._image_widgets:
                    self._image_widgets[fname]["type_var"].set(result)
                    self._image_widgets[fname]["include_var"].set(
                        result != "decorativa"
                    )
                classified += 1

        self.status_var.set(
            f"Pré-classificação concluída: {classified} imagens analisadas."
        )

    def _save_curation(self):
        """Save curation decisions to manifest.json."""
        if not self._current_entry or self._current_page is None:
            return

        entry_id = self._current_entry.get("id", "")
        page_images = self._current_entry.get("_image_groups", {}).get(self._current_page, [])
        curation = self._current_entry.get("image_curation", {})
        page_key = _migrate_curation_page_key(curation, self._current_page, page_images)

        # Build page data from UI state
        images_data = {}
        for fname, widgets in self._image_widgets.items():
            existing = (
                curation.get("pages", {})
                .get(page_key, {})
                .get("images", {})
                .get(fname, {})
            )
            images_data[fname] = {
                "type": widgets["type_var"].get(),
                "include": widgets["include_var"].get(),
                "description": existing.get("description"),
                "described_at": existing.get("described_at"),
            }

        # Update entry's image_curation in manifest
        if "image_curation" not in self._current_entry:
            self._current_entry["image_curation"] = {
                "status": "pending",
                "curated_at": None,
                "pages": {},
            }

        curation = self._current_entry["image_curation"]
        curation["pages"][page_key] = {
            "include_page": any(d["include"] for d in images_data.values()),
            "images": images_data,
        }
        curation["curated_at"] = datetime.now().isoformat(timespec="seconds")

        # Check if all pages are curated
        all_curated = all(
            (str(p) if p is not None else "none") in curation["pages"]
            for p in self._current_entry.get("_image_groups", {}).keys()
        )
        if all_curated:
            curation["status"] = "curated"

        # Write back to manifest (removing internal _image_groups key)
        self._write_manifest_entry(entry_id)
        self.status_var.set(f"Curadoria salva para {entry_id}.")

    def _describe_single_image(self, fname: str, img_path: Path):
        """Generate (or regenerate) description for a single image."""
        if not self._current_entry or self._current_page is None:
            return

        client = self._get_vision_client()
        if not client:
            return

        # Save current UI state first
        self._save_curation()

        entry_id = self._current_entry.get("id", "")
        page_images = self._current_entry.get("_image_groups", {}).get(self._current_page, [])
        curation = self._current_entry.get("image_curation", {})
        page_key = _migrate_curation_page_key(curation, self._current_page, page_images)
        img_type = curation.get("pages", {}).get(page_key, {}).get("images", {}).get(fname, {}).get("type", "genérico")

        # Get page context
        page_contexts = self._extract_page_contexts(entry_id)
        page_ctx = page_contexts.get(page_key, "")

        self.status_var.set(f"Gerando descrição para {fname}...")
        self._vision_busy = True
        logger.info("[Vision] Iniciando descrição: %s (tipo: %s, modelo: %s)", fname, img_type, client.model)

        def _worker():
            try:
                desc = client.describe_image(img_path, img_type, page_context=page_ctx)
                curation.setdefault("pages", {}).setdefault(page_key, {"include_page": True, "images": {}})
                curation["pages"][page_key]["images"].setdefault(fname, {})
                curation["pages"][page_key]["images"][fname]["description"] = desc
                curation["pages"][page_key]["images"][fname]["described_at"] = (
                    datetime.now().isoformat(timespec="seconds")
                )
                curation["pages"][page_key]["images"][fname]["type"] = img_type
                curation["pages"][page_key]["images"][fname]["include"] = True

                desc_preview = desc[:120].replace("\n", " ")
                logger.info("[Vision] Descrição gerada para %s: %s...", fname, desc_preview)

                def _on_done():
                    self._write_manifest_entry(entry_id)
                    groups = self._current_entry.get("_image_groups", {})
                    images = groups.get(self._current_page, [])
                    self._show_images(self._current_entry, self._current_page, images)
                    self.status_var.set(f"Descrição gerada para {fname}.")

                self.after(0, _on_done)
            except Exception as e:
                logger.error("[Vision] Erro ao descrever %s: %s", fname, e)
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erro", f"Falha ao descrever {fname}:\n{e}", parent=self
                    ),
                )
                self.after(0, lambda: self.status_var.set(f"Erro ao descrever {fname}."))
            finally:
                self._vision_busy = False

        threading.Thread(target=_worker, daemon=True).start()

    def _extract_latex_single(self, fname: str, img_path: Path):
        """Extract text + LaTeX content from a scanned page image."""
        if not self._current_entry or self._current_page is None:
            return

        client = self._get_vision_client()
        if not client:
            return

        # Save current UI state first
        self._save_curation()

        entry_id = self._current_entry.get("id", "")
        page_images = self._current_entry.get("_image_groups", {}).get(self._current_page, [])
        curation = self._current_entry.get("image_curation", {})
        page_key = _migrate_curation_page_key(curation, self._current_page, page_images)

        # Get page context from adjacent pages
        page_contexts = self._extract_page_contexts(entry_id)
        page_ctx = page_contexts.get(page_key, "")

        self.status_var.set(f"Extraindo LaTeX de {fname}...")
        self._vision_busy = True
        logger.info("[Vision] Iniciando extração LaTeX: %s (modelo: %s)", fname, client.model)

        def _worker():
            try:
                extracted = client.extract_to_latex(img_path, page_context=page_ctx)
                curation.setdefault("pages", {}).setdefault(page_key, {"include_page": True, "images": {}})
                curation["pages"][page_key]["images"].setdefault(fname, {})
                curation["pages"][page_key]["images"][fname]["description"] = extracted
                curation["pages"][page_key]["images"][fname]["described_at"] = (
                    datetime.now().isoformat(timespec="seconds")
                )
                curation["pages"][page_key]["images"][fname]["type"] = "extração-latex"
                curation["pages"][page_key]["images"][fname]["include"] = True
                if fname in self._image_widgets:
                    self._image_widgets[fname]["type_var"].set("extração-latex")
                    self._image_widgets[fname]["include_var"].set(True)

                preview = extracted[:120].replace("\n", " ")
                logger.info("[Vision] Extração LaTeX para %s: %s...", fname, preview)

                def _on_done():
                    self._write_manifest_entry(entry_id)
                    groups = self._current_entry.get("_image_groups", {})
                    images = groups.get(self._current_page, [])
                    self._show_images(self._current_entry, self._current_page, images)
                    self.status_var.set(f"Extração LaTeX concluída para {fname}.")

                self.after(0, _on_done)
            except Exception as e:
                logger.error("[Vision] Erro na extração LaTeX de %s: %s", fname, e)
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erro", f"Falha na extração LaTeX de {fname}:\n{e}", parent=self
                    ),
                )
                self.after(0, lambda: self.status_var.set(f"Erro na extração de {fname}."))
            finally:
                self._vision_busy = False

        threading.Thread(target=_worker, daemon=True).start()

    def _generate_descriptions(self):
        """Generate descriptions for included images using the configured vision backend."""
        if not self._current_entry:
            messagebox.showinfo("Image Curator", "Selecione um entry primeiro.")
            return

        client = self._get_vision_client()
        if not client:
            return

        # Save current curation state first
        self._save_curation()

        entry_id = self._current_entry.get("id", "")
        curation = self._current_entry.get("image_curation", {})

        # Load page context from markdown for richer descriptions
        page_contexts = self._extract_page_contexts(entry_id)

        # Build fname -> full Path lookup from _image_groups
        fname_to_path: Dict[str, Path] = {}
        for imgs in self._current_entry.get("_image_groups", {}).values():
            for p in imgs:
                fname_to_path[p.name] = p

        # Collect all included images across all pages
        to_describe: list = []
        for page_key, page_data in curation.get("pages", {}).items():
            if not page_data.get("include_page", True):
                continue
            for fname, img_data in page_data.get("images", {}).items():
                if img_data.get("include") and not img_data.get("description"):
                    img_path = fname_to_path.get(fname, self._images_dir / fname)
                    if img_path.exists():
                        ctx = page_contexts.get(page_key, "")
                        to_describe.append(
                            (page_key, fname, img_data.get("type", "genérico"), img_path, ctx)
                        )

        if not to_describe:
            messagebox.showinfo(
                "Image Curator", "Nenhuma imagem pendente para descrever."
            )
            return

        total = len(to_describe)
        logger.info("[Vision] Iniciando geração em lote: %d imagens (modelo: %s)", total, client.model)
        self.status_var.set(f"Gerando descrições: 0/{total}...")
        self._vision_busy = True

        def _worker():
            try:
                errors = []
                for idx, (page_key, fname, img_type, img_path, page_ctx) in enumerate(
                    to_describe
                ):
                    logger.info("[Vision] Descrevendo %d/%d: %s (tipo: %s)", idx + 1, total, fname, img_type)
                    self.after(
                        0,
                        lambda i=idx, f=fname: self.status_var.set(
                            f"Gerando descrição {i + 1}/{total}: {f}..."
                        ),
                    )
                    try:
                        desc = client.describe_image(
                            img_path, img_type, page_context=page_ctx
                        )
                        curation["pages"][page_key]["images"][fname]["description"] = desc
                        curation["pages"][page_key]["images"][fname]["described_at"] = (
                            datetime.now().isoformat(timespec="seconds")
                        )
                        desc_preview = desc[:120].replace("\n", " ")
                        logger.info("[Vision] OK %s: %s...", fname, desc_preview)
                    except Exception as e:
                        logger.error("[Vision] Erro ao descrever %s: %s", fname, e)
                        curation["pages"][page_key]["images"][fname]["description"] = (
                            f"[ERRO: {e}]"
                        )
                        errors.append(f"{fname}: {e}")

                # Mark as described
                curation["status"] = "described"
                ok_count = total - len(errors)
                if errors:
                    logger.warning("[Vision] Lote concluído: %d/%d OK, %d erros", ok_count, total, len(errors))
                else:
                    logger.info("[Vision] Lote concluído: %d/%d descrições geradas com sucesso", ok_count, total)

                def _on_done():
                    self._write_manifest_entry(entry_id)
                    if self._current_entry and self._current_page is not None:
                        groups = self._current_entry.get("_image_groups", {})
                        images = groups.get(self._current_page, [])
                        self._show_images(self._current_entry, self._current_page, images)
                    ok_count = total - len(errors)
                    if errors:
                        self.status_var.set(
                            f"{ok_count}/{total} descrições geradas ({len(errors)} erros). Salvo no manifest."
                        )
                        error_detail = "\n".join(errors[:10])
                        messagebox.showwarning(
                            "Image Curator",
                            f"{ok_count} descrições geradas, {len(errors)} erros:\n\n{error_detail}",
                        )
                    else:
                        self.status_var.set(
                            f"Descrições geradas para {total} imagens. Salvo no manifest."
                        )
                        messagebox.showinfo(
                            "Image Curator", f"{total} descrições geradas com sucesso!"
                        )

                self.after(0, _on_done)
            finally:
                self._vision_busy = False

        threading.Thread(target=_worker, daemon=True).start()

    # ── Manifest Persistence ───────────────────────────────────────────

    def _write_manifest_entry(self, entry_id: str):
        """Write the current entry back to manifest.json, stripping internal keys."""
        # Build a clean copy of the entire manifest, removing internal keys
        # from ALL entries (not just the current one) to avoid Path objects
        clean_manifest = dict(self._manifest)
        clean_entries = []
        for e in clean_manifest.get("entries", []):
            clean_entries.append(
                {k: v for k, v in e.items() if not k.startswith("_")}
            )
        clean_manifest["entries"] = clean_entries

        self._manifest_path.write_text(
            json.dumps(clean_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _inject_all_image_descriptions_from_manifest(self.repo_dir, clean_manifest)
