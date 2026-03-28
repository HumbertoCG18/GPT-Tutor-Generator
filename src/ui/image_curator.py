"""Image Curator — UI for curating and describing images from PDFs."""

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

logger = logging.getLogger(__name__)

IMAGE_TYPES = ["diagrama", "tabela", "fórmula", "código", "genérico", "decorativa"]


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
        self._image_widgets: Dict[str, dict] = {}  # fname -> {type_var, include_var}

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_manifest()

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
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel: entry + page tree
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

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
        right_paned = ttk.PanedWindow(paned, orient="vertical")
        paned.add(right_paned, weight=3)

        # Top: image cards
        images_frame = ttk.Frame(right_paned)
        right_paned.add(images_frame, weight=2)

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
        self._canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        self._cards_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            ),
        )

        # Bottom: PDF viewer
        pdf_frame = ttk.Frame(right_paned)
        right_paned.add(pdf_frame, weight=1)

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

        # Find entries that have images in content/images/
        all_images = [
            f
            for f in self._images_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
        ]
        if not all_images:
            self.status_var.set("Nenhuma imagem encontrada em content/images/.")
            return

        entries = self._manifest.get("entries", [])
        for entry in entries:
            entry_id = entry.get("id", "")
            if not entry_id:
                continue
            groups = group_images_by_page(self._images_dir, entry_id)
            if not groups:
                continue

            entry["_image_groups"] = groups
            self._entries_with_images.append(entry)

            # Add to tree
            entry_node = self._tree.insert(
                "",
                "end",
                text=entry.get("title", entry_id),
                values=(entry_id,),
            )
            for page_num in sorted(
                groups.keys(), key=lambda x: x if x is not None else 9999
            ):
                count = len(groups[page_num])
                if page_num is not None:
                    label = f"Página {page_num} ({count} imgs)"
                else:
                    label = f"Página desconhecida ({count} imgs)"
                self._tree.insert(
                    entry_node,
                    "end",
                    text=label,
                    values=(
                        entry_id,
                        str(page_num) if page_num is not None else "none",
                    ),
                )

        self.status_var.set(
            f"{len(self._entries_with_images)} entries com imagens encontradas."
        )

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
        page_key = str(page_num) if page_num is not None else "none"
        page_data = curation.get("pages", {}).get(page_key, {})
        include_page = page_data.get("include_page", True)
        curated_images = page_data.get("images", {})

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
                btn_frame, text="Remover",
                command=lambda fn=fname, ip=img_path: self._delete_image(fn, ip),
            ).pack(side="left")

            self._image_widgets[fname] = {
                "type_var": type_var,
                "include_var": include_var,
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

    # ── Actions ────────────────────────────────────────────────────────

    def _toggle_page(self, include: bool):
        """Toggle all images on current page."""
        for widgets in self._image_widgets.values():
            widgets["include_var"].set(include)

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

        entry_id = self._current_entry.get("id", "")
        source_path = self._current_entry.get("source_path", "")

        # Try to find the PDF file
        pdf_path = None
        if source_path and Path(source_path).exists():
            pdf_path = Path(source_path)
        else:
            # Search in repo raw/ directory
            raw_dir = self.repo_dir / "raw"
            if raw_dir.exists():
                candidates = list(raw_dir.rglob(f"*{entry_id}*.pdf"))
                if not candidates:
                    candidates = list(raw_dir.rglob("*.pdf"))
                if candidates:
                    pdf_path = candidates[0]

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
        source_path = self._current_entry.get("source_path", "")

        pdf_path = None
        if source_path and Path(source_path).exists():
            pdf_path = Path(source_path)
        else:
            raw_dir = self.repo_dir / "raw"
            if raw_dir.exists():
                candidates = list(raw_dir.rglob(f"*{entry_id}*.pdf"))
                if candidates:
                    pdf_path = candidates[0]

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
        """Delete an image from disk and remove from manifest curation data."""
        if not messagebox.askyesno(
            "Remover imagem",
            f"Remover '{fname}' permanentemente?\n\n"
            "Isso remove o arquivo de content/images/ e a entrada no manifest.",
            parent=self,
        ):
            return

        # Delete from disk
        try:
            if img_path.exists():
                img_path.unlink()
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível remover o arquivo:\n{e}", parent=self
            )
            return

        # Remove from manifest curation data
        if self._current_entry and self._current_page is not None:
            page_key = (
                str(self._current_page) if self._current_page is not None else "none"
            )
            curation = self._current_entry.get("image_curation", {})
            page_data = curation.get("pages", {}).get(page_key, {})
            page_data.get("images", {}).pop(fname, None)

        # Remove from in-memory image groups
        groups = (
            self._current_entry.get("_image_groups", {})
            if self._current_entry
            else {}
        )
        page_imgs = groups.get(self._current_page, [])
        groups[self._current_page] = [p for p in page_imgs if p.name != fname]

        # Save manifest
        self._save_curation()

        # Refresh the image panel
        images = groups.get(self._current_page, [])
        self._show_images(self._current_entry, self._current_page, images)
        self.status_var.set(f"'{fname}' removida.")

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
        page_key = (
            str(self._current_page) if self._current_page is not None else "none"
        )

        # Build page data from UI state
        images_data = {}
        for fname, widgets in self._image_widgets.items():
            existing = (
                self._current_entry.get("image_curation", {})
                .get("pages", {})
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

        # Save current UI state first
        self._save_curation()

        from src.builder.ollama_client import OllamaClient

        config = self._parent.config_obj if hasattr(self._parent, "config_obj") else None
        model = config.get("vision_model", "qwen3-vl") if config else "qwen3-vl"
        quant = config.get("vision_model_quantization", "default") if config else "default"
        base_url = config.get("ollama_base_url", "http://localhost:11434") if config else "http://localhost:11434"
        if quant != "default":
            model = f"{model}:{quant}" if ":" not in model else model.split(":")[0] + f":{quant}"

        client = OllamaClient(base_url=base_url, model=model)
        available, msg = client.check_availability()
        if not available:
            messagebox.showerror("Ollama indisponível", msg)
            return

        entry_id = self._current_entry.get("id", "")
        page_key = str(self._current_page) if self._current_page is not None else "none"
        curation = self._current_entry.get("image_curation", {})
        img_type = curation.get("pages", {}).get(page_key, {}).get("images", {}).get(fname, {}).get("type", "genérico")

        # Get page context
        page_contexts = self._extract_page_contexts(entry_id)
        page_ctx = page_contexts.get(page_key, "")

        self.status_var.set(f"Gerando descrição para {fname}...")

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

                def _on_done():
                    self._write_manifest_entry(entry_id)
                    groups = self._current_entry.get("_image_groups", {})
                    images = groups.get(self._current_page, [])
                    self._show_images(self._current_entry, self._current_page, images)
                    self.status_var.set(f"Descrição gerada para {fname}.")

                self.after(0, _on_done)
            except Exception as e:
                logger.error("Erro ao descrever %s: %s", fname, e)
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erro", f"Falha ao descrever {fname}:\n{e}", parent=self
                    ),
                )
                self.after(0, lambda: self.status_var.set(f"Erro ao descrever {fname}."))

        threading.Thread(target=_worker, daemon=True).start()

    def _generate_descriptions(self):
        """Generate descriptions for included images using Ollama Vision model."""
        if not self._current_entry:
            messagebox.showinfo("Image Curator", "Selecione um entry primeiro.")
            return

        from src.builder.ollama_client import OllamaClient

        config = self._parent.config_obj if hasattr(self._parent, "config_obj") else None
        model = config.get("vision_model", "qwen3-vl") if config else "qwen3-vl"
        quant = config.get("vision_model_quantization", "default") if config else "default"
        base_url = config.get("ollama_base_url", "http://localhost:11434") if config else "http://localhost:11434"

        # Append quantization tag if not default
        if quant != "default":
            model = f"{model}:{quant}" if ":" not in model else model.split(":")[0] + f":{quant}"

        client = OllamaClient(base_url=base_url, model=model)

        # Check availability first
        available, msg = client.check_availability()
        if not available:
            messagebox.showerror("Ollama indisponível", msg)
            return

        # Save current curation state first
        self._save_curation()

        entry_id = self._current_entry.get("id", "")
        curation = self._current_entry.get("image_curation", {})

        # Load page context from markdown for richer descriptions
        page_contexts = self._extract_page_contexts(entry_id)

        # Collect all included images across all pages
        to_describe: list = []
        for page_key, page_data in curation.get("pages", {}).items():
            if not page_data.get("include_page", True):
                continue
            for fname, img_data in page_data.get("images", {}).items():
                if img_data.get("include") and not img_data.get("description"):
                    img_path = self._images_dir / fname
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
        self.status_var.set(f"Gerando descrições: 0/{total}...")

        def _worker():
            errors = []
            for idx, (page_key, fname, img_type, img_path, page_ctx) in enumerate(
                to_describe
            ):
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
                except Exception as e:
                    logger.error("Erro ao descrever %s: %s", fname, e)
                    curation["pages"][page_key]["images"][fname]["description"] = (
                        f"[ERRO: {e}]"
                    )
                    errors.append(f"{fname}: {e}")

            # Mark as described
            curation["status"] = "described"

            def _on_done():
                self._write_manifest_entry(entry_id)
                # Refresh cards to show descriptions
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
