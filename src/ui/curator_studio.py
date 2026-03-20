import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from PIL import Image, ImageTk

from src.utils.helpers import HAS_PYMUPDF

if HAS_PYMUPDF:
    import pymupdf

logger = logging.getLogger(__name__)


class CuratorStudio(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._theme_name = parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"

        self.title("Curator Studio")
        self.geometry("1600x900")
        self.minsize(1100, 650)

        self.current_md_path = None          # review template .md path
        self._current_content_path = None    # actual markdown file being edited
        self._current_frontmatter = {}
        self._available_sources = {}
        self.preview_images = []

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_files()

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)

        # Toolbar
        toolbar = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        toolbar.pack(fill="x", side="top")
        tk.Label(
            toolbar, text="🖌 Curator Studio",
            bg=p["header_bg"], fg=p["header_fg"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        ttk.Button(toolbar, text="✅ Aprovar", command=self._approve_current).pack(side="right", padx=5)
        self.bind("<Control-s>", lambda e: self.save_current())  # hidden shortcut

        # Status bar
        self.status_var = tk.StringVar(value="Selecione um arquivo para revisar")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            bg=p["header_bg"], fg=p["header_fg"],
            anchor="w", padx=12, pady=4,
            font=("Segoe UI", 9),
        )
        status_bar.pack(fill="x", side="bottom")

        # PanedWindow
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ── 1. File List ────────────────────────────────────────────────
        list_frame = ttk.Frame(self.paned)
        self.paned.add(list_frame, weight=1)

        ttk.Label(list_frame, text="Arquivos em manual-review", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.file_list = tk.Listbox(
            list_frame,
            bg=p["input_bg"], fg=p["fg"],
            selectbackground=p["select_bg"], selectforeground=p["select_fg"],
            relief="flat", highlightthickness=1,
            highlightcolor=p["border"], highlightbackground=p["border"],
            font=("Segoe UI", 10),
        )
        self.file_list.pack(fill="both", expand=True, side="left")
        self.file_list.bind("<<ListboxSelect>>", self._on_select_file)

        list_scroll = ttk.Scrollbar(list_frame, command=self.file_list.yview)
        list_scroll.pack(side="right", fill="y")
        self.file_list.config(yscrollcommand=list_scroll.set)

        # ── 2. Image Preview ────────────────────────────────────────────
        preview_frame = ttk.Frame(self.paned)
        self.paned.add(preview_frame, weight=2)

        ttk.Label(preview_frame, text="Visualização (Preview original)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.canvas = tk.Canvas(preview_frame, bg=p["frame_bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        cvs_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        cvs_scroll.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=cvs_scroll.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.bind("<Destroy>", self._on_destroy)

        # ── 3. Right side: info + source selector + editor ──────────────
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        # Info panel
        info_frame = ttk.LabelFrame(right_frame, text="Documento")
        info_frame.pack(fill="x", pady=(0, 5))
        self.info_label = tk.Label(
            info_frame, text="Nenhum arquivo selecionado",
            bg=p["frame_bg"], fg=p["fg"],
            justify="left", anchor="w",
            font=("Segoe UI", 9), wraplength=700,
        )
        self.info_label.pack(fill="x", padx=8, pady=4)

        # Source selector bar
        src_bar = ttk.Frame(right_frame)
        src_bar.pack(fill="x", pady=(0, 3))
        ttk.Label(src_bar, text="Fonte:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self._source_var = tk.StringVar()
        self._source_combo = ttk.Combobox(
            src_bar, textvariable=self._source_var,
            state="readonly", width=50,
        )
        self._source_combo.pack(side="left", padx=5)
        self._source_combo.bind("<<ComboboxSelected>>", self._on_source_changed)

        # Editor header
        ttk.Label(
            right_frame, text="Markdown extraído (editável)",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 3))

        # Editor
        editor_container = ttk.Frame(right_frame)
        editor_container.pack(fill="both", expand=True)

        self.editor = tk.Text(
            editor_container, wrap="word",
            bg=p["input_bg"], fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"], selectforeground=p["select_fg"],
            font=("Consolas", 11),
            relief="flat", highlightthickness=1,
            highlightcolor=p["border"], highlightbackground=p["border"],
            undo=True,
        )
        self.editor.pack(side="left", fill="both", expand=True)

        ed_scroll = ttk.Scrollbar(editor_container, command=self.editor.yview)
        ed_scroll.pack(side="right", fill="y")
        self.editor.config(yscrollcommand=ed_scroll.set)

    # ── Events ──────────────────────────────────────────────────────────

    def _on_destroy(self, event):
        if event.widget is self:
            try:
                self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    # ── File loading ────────────────────────────────────────────────────

    def _load_files(self):
        self.file_list.delete(0, tk.END)
        self.file_paths = []

        manual_dir = self.repo_dir / "manual-review"
        if not manual_dir.exists():
            return

        for p in sorted(manual_dir.rglob("*.md")):
            self.file_paths.append(p)
            self.file_list.insert(tk.END, f"{p.parent.name}/{p.name}")

    def _on_select_file(self, event):
        selection = self.file_list.curselection()
        if not selection:
            return

        if self.current_md_path and self.editor.edit_modified():
            if not messagebox.askyesno(
                "Não Salvo",
                "Existem alterações não salvas. Deseja descartar e continuar?",
            ):
                return

        idx = selection[0]
        self.current_md_path = self.file_paths[idx]

        # Parse frontmatter from the review template
        try:
            content = self.current_md_path.read_text(encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler arquivo: {e}")
            return

        fm = self._parse_frontmatter(content)
        self._current_frontmatter = fm

        # Update info label
        self._update_info_label(fm)

        # Build available sources
        self._build_source_list(fm)

        # Auto-select best source (prefer base markdown, then advanced, then template)
        keys = list(self._available_sources.keys())
        if keys:
            # Pick first non-template source if available
            best = keys[0]
            self._source_var.set(best)
            self._load_selected_source()

        # Load previews — prefer rendering from source PDF directly
        self._load_previews(fm)

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from a review markdown file."""
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        result = {}
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value.lower() in ("null", "none", ""):
                    value = None
                result[key] = value
        return result

    def _update_info_label(self, fm: dict):
        parts = []
        if fm.get("title"):
            parts.append(f"Título: {fm['title']}")
        if fm.get("category"):
            parts.append(f"Categoria: {fm['category']}")
        if fm.get("effective_profile"):
            parts.append(f"Perfil: {fm['effective_profile']}")
        if fm.get("base_backend"):
            parts.append(f"Backend base: {fm['base_backend']}")
        if fm.get("advanced_backend"):
            parts.append(f"Backend avançado: {fm['advanced_backend']}")
        if fm.get("processing_mode"):
            parts.append(f"Modo: {fm['processing_mode']}")
        self.info_label.config(text="  |  ".join(parts) if parts else "Sem metadados")

    def _build_source_list(self, fm: dict):
        """Build dict of available markdown sources for this review entry."""
        sources = {}

        base_md = fm.get("base_markdown")
        if base_md:
            p = self.repo_dir / base_md
            if p.exists():
                backend_name = fm.get("base_backend", "base")
                sources[f"Base — {backend_name} ({p.name})"] = p

        adv_md = fm.get("advanced_markdown")
        if adv_md:
            p = self.repo_dir / adv_md
            if p.exists():
                backend_name = fm.get("advanced_backend", "advanced")
                sources[f"Avançado — {backend_name} ({p.name})"] = p

        # Always offer the review template itself
        sources[f"Template de revisão ({self.current_md_path.name})"] = self.current_md_path

        self._available_sources = sources
        self._source_combo["values"] = list(sources.keys())

    def _on_source_changed(self, event=None):
        if self.editor.edit_modified():
            if not messagebox.askyesno(
                "Não Salvo",
                "Existem alterações não salvas. Deseja descartar e trocar de fonte?",
            ):
                # Revert combo selection
                for name, path in self._available_sources.items():
                    if path == self._current_content_path:
                        self._source_var.set(name)
                        return
                return
        self._load_selected_source()

    def _load_selected_source(self):
        source_name = self._source_var.get()
        if source_name not in self._available_sources:
            return
        path = self._available_sources[source_name]
        self._current_content_path = path
        try:
            content = path.read_text(encoding="utf-8")
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, content)
            self.editor.edit_modified(False)
            try:
                rel = path.relative_to(self.repo_dir)
            except ValueError:
                rel = path.name
            self.status_var.set(f"Editando: {rel}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler arquivo:\n{e}")

    # ── Image Previews ──────────────────────────────────────────────────

    def _load_previews(self, fm: dict):
        """Render preview from source PDF (via PyMuPDF) or raw images."""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.preview_images.clear()

        bg = self.theme_mgr.palette(self._theme_name)["frame_bg"]
        target_width = 400

        # 1) Try rendering directly from the source PDF
        source_pdf = fm.get("source_pdf")
        if source_pdf and HAS_PYMUPDF:
            pdf_path = self.repo_dir / source_pdf
            if pdf_path.exists():
                try:
                    doc = pymupdf.open(str(pdf_path))
                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
                        pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        w, h = pil_img.size
                        new_h = int(target_width * (h / w))
                        pil_img = pil_img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.preview_images.append(tk_img)
                        lbl = tk.Label(self.inner_frame, image=tk_img, bg=bg)
                        lbl.pack(pady=5, padx=5)
                    doc.close()
                    return
                except Exception as e:
                    logger.error("Erro ao renderizar PDF %s: %s", pdf_path, e)

        # 2) Fallback: raw images (for image-type entries)
        file_id = self.current_md_path.stem if self.current_md_path else ""
        images_found = []
        if file_id:
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                images_found.extend(
                    list((self.repo_dir / "raw" / "images").rglob(f"{file_id}{ext[1:]}"))
                )

        if not images_found:
            ttk.Label(self.inner_frame, text="Nenhuma visualização disponível.").pack(pady=20)
            return

        for img_path in images_found:
            try:
                pil_img = Image.open(img_path)
                w, h = pil_img.size
                new_h = int(target_width * (h / w))
                pil_img = pil_img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                self.preview_images.append(tk_img)
                lbl = tk.Label(self.inner_frame, image=tk_img, bg=bg)
                lbl.pack(pady=5, padx=5)
            except Exception as e:
                logger.error("Erro ao carregar preview %s: %s", img_path, e)

    # ── Save / Approve ──────────────────────────────────────────────────

    def save_current(self):
        if not self._current_content_path:
            messagebox.showwarning("Nada selecionado", "Selecione um arquivo primeiro.")
            return

        content = self.editor.get("1.0", tk.END).strip() + "\n"
        try:
            self._current_content_path.write_text(content, encoding="utf-8")
            self.editor.edit_modified(False)
            self.status_var.set(f"💾 Salvo: {self._current_content_path.name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def _approve_current(self):
        if not self._current_content_path or not self._current_frontmatter:
            messagebox.showwarning("Nada selecionado", "Selecione um arquivo primeiro.")
            return

        fm = self._current_frontmatter
        category = fm.get("category", "")

        # Determine destination based on category
        if category in ("provas", "fotos-de-prova"):
            dest_dir = self.repo_dir / "exams" / "past-exams"
            dest_label = "exams/past-exams/"
        elif category in ("listas", "gabaritos"):
            dest_dir = self.repo_dir / "exercises" / "lists"
            dest_label = "exercises/lists/"
        else:
            dest_dir = self.repo_dir / "content" / "curated"
            dest_label = "content/curated/"

        file_id = fm.get("id", self.current_md_path.stem)
        dest_path = dest_dir / f"{file_id}.md"

        # Confirm
        msg = (
            f"Aprovar e copiar para:\n"
            f"  {dest_label}{file_id}.md\n\n"
            f"Categoria detectada: {category}\n"
            f"Fonte selecionada: {self._current_content_path.name}\n\n"
            f"Os demais arquivos MD deste documento serão excluídos.\n"
            f"Continuar?"
        )
        if not messagebox.askyesno("Aprovar arquivo", msg):
            return

        dest_dir.mkdir(parents=True, exist_ok=True)

        if dest_path.exists():
            if not messagebox.askyesno(
                "Sobrescrever?",
                f"O arquivo já existe:\n{dest_path.relative_to(self.repo_dir)}\n\nDeseja sobrescrever?",
            ):
                return

        # Save current editor content to the selected source
        content = self.editor.get("1.0", tk.END).strip() + "\n"
        try:
            self._current_content_path.write_text(content, encoding="utf-8")
            self.editor.edit_modified(False)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar fonte: {e}")
            return

        # Copy approved source to destination
        try:
            shutil.copy2(self._current_content_path, dest_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar: {e}")
            return

        # ── Cleanup: delete all OTHER source files ────────────────────
        approved_path = self._current_content_path.resolve()
        files_to_delete = []

        # Collect all source paths from frontmatter (base, advanced, template)
        for key in ("base_markdown", "advanced_markdown"):
            rel = fm.get(key)
            if rel:
                p = (self.repo_dir / rel).resolve()
                if p.exists() and p != approved_path:
                    files_to_delete.append(p)

        # The manual-review template itself
        if self.current_md_path and self.current_md_path.resolve() != approved_path:
            if self.current_md_path.exists():
                files_to_delete.append(self.current_md_path.resolve())

        # Also delete the approved source file if it's NOT the destination
        # (it was already copied to dest_path)
        if approved_path != dest_path.resolve() and approved_path.exists():
            files_to_delete.append(approved_path)

        deleted = []
        for f in files_to_delete:
            try:
                f.unlink()
                deleted.append(f.name)
                logger.info("Approve cleanup: deleted %s", f)
            except Exception as e:
                logger.warning("Approve cleanup: failed to delete %s: %s", f, e)

        # ── Remove entry from file list ───────────────────────────────
        # Find the index of the current review template in the list
        try:
            list_idx = self.file_paths.index(self.current_md_path)
            self.file_paths.pop(list_idx)
            self.file_list.delete(list_idx)
        except ValueError:
            pass

        # ── Reset editor state ────────────────────────────────────────
        self.editor.delete("1.0", tk.END)
        self.editor.edit_modified(False)
        self.current_md_path = None
        self._current_content_path = None
        self._current_frontmatter = {}
        self._available_sources = {}
        self._source_combo["values"] = []
        self._source_var.set("")
        self.info_label.config(text="Nenhum arquivo selecionado")

        # Clear previews
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.preview_images.clear()

        # Status
        cleanup_msg = f" | Removidos: {', '.join(deleted)}" if deleted else ""
        self.status_var.set(f"✅ Aprovado → {dest_label}{file_id}.md{cleanup_msg}")
