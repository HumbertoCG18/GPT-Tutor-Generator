import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import traceback
import logging
import threading
from pathlib import Path
import json

from src.models.core import FileEntry, SubjectStore, StudentStore, SubjectProfile
from src.utils.helpers import APP_NAME, auto_detect_category, auto_detect_title, HAS_PYMUPDF, HAS_PYMUPDF4LLM, HAS_PDFPLUMBER, DOCLING_CLI, MARKER_CLI, slugify
from src.builder.engine import RepoBuilder
from src.ui.theme import ThemeManager, AppConfig
from src.ui.dialogs import FileEntryDialog, URLEntryDialog, SubjectManagerDialog, StudentProfileDialog, MarkdownPreviewWindow, HelpWindow, add_tooltip, SettingsDialog

logger = logging.getLogger(__name__)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_obj = AppConfig()
        self.theme_mgr = ThemeManager()
        self.subject_store = SubjectStore()
        self.student_store = StudentStore()
        self._theme_name: str = self.config_obj.get("theme")  # type: ignore[assignment]
        self.title(APP_NAME)
        self.geometry("1360x900")
        self.minsize(900, 600)
        self.entries: List[FileEntry] = []
        self._quick_import = tk.BooleanVar(value=False)

        # Apply theme before building UI
        self.theme_mgr.apply(self, self._theme_name)

        self._build_ui()
        self.bind("<F1>", lambda _: self.open_help())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.config_obj.save()
        self.destroy()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)

        self.var_repo_root = tk.StringVar()
        self.var_course_name = tk.StringVar()
        self.var_course_slug = tk.StringVar()
        self.var_semester = tk.StringVar()
        self.var_professor = tk.StringVar()
        self.var_institution = tk.StringVar(value="PUCRS")
        self.var_default_mode = tk.StringVar(value=self.config_obj.get("default_mode"))
        self.var_default_ocr_language = tk.StringVar(value=self.config_obj.get("default_ocr_language"))

        # ─── Header bar ────────────────────────────────────────────────
        header = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        header.pack(fill="x")
        tk.Label(header, text=f"🎓  {APP_NAME}", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="v3 — Gerador de repositórios para GPT tutores acadêmicos",
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))

        # ─── Main content area ─────────────────────────────────────────
        top = ttk.Frame(self, padding=14)
        top.pack(fill="both", expand=True)

        # ── Subject selector ────────────────────────────────────────────
        subj_frame = ttk.Frame(top)
        subj_frame.pack(fill="x", pady=(0, 8))
        lbl_subj = ttk.Label(subj_frame, text="📚 Matéria ativa:", font=("Segoe UI", 10, "bold"))
        lbl_subj.pack(side="left")
        add_tooltip(lbl_subj, "Selecione uma matéria salva para preencher automaticamente todos os campos da disciplina.\nUse 'Gerenciar' para criar, editar ou excluir perfis de matérias.")
        self._var_active_subject = tk.StringVar(value="(nenhuma)")
        self._subject_combo = ttk.Combobox(subj_frame, textvariable=self._var_active_subject,
                                            values=["(nenhuma)"] + self.subject_store.names(),
                                            state="readonly", width=30)
        self._subject_combo.pack(side="left", padx=(8, 6))
        self._subject_combo.bind("<<ComboboxSelected>>", self._on_subject_selected)
        ttk.Button(subj_frame, text="📝 Gerenciar", command=self.open_subject_manager).pack(side="left")
        ttk.Separator(subj_frame, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(subj_frame, text="👤 Aluno", command=self.open_student_profile).pack(side="left")

        # Quick import toggle
        cb_quick = ttk.Checkbutton(subj_frame, text="⚡ Importação rápida", variable=self._quick_import)
        cb_quick.pack(side="right")
        add_tooltip(cb_quick, "Quando ativo, adicionar arquivos NÃO abre o diálogo de edição.\nUsa auto-detecção de categoria e título + defaults da matéria ativa.\nÚtil para importar muitos arquivos de uma vez.")

        # ── Course data frame ───────────────────────────────────────────
        course = ttk.LabelFrame(top, text="  📋  Dados da Disciplina", padding=12)
        course.pack(fill="x", pady=(0, 10))

        # Row 0: Course name + slug
        lbl_cn = ttk.Label(course, text="Nome da disciplina")
        lbl_cn.grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_course_name, font=("Segoe UI", 10, "bold"), foreground=p["accent"]).grid(row=0, column=1, sticky="w", padx=(8, 16))

        lbl_sl = ttk.Label(course, text="Slug")
        lbl_sl.grid(row=0, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_course_slug, font=("Segoe UI", 10, "bold")).grid(row=0, column=3, sticky="w", padx=(8, 0))

        # Row 1: Semester + professor
        lbl_sem = ttk.Label(course, text="Semestre")
        lbl_sem.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_semester, font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w", padx=(8, 16))

        lbl_prof = ttk.Label(course, text="Professor")
        lbl_prof.grid(row=1, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_professor, font=("Segoe UI", 10, "bold")).grid(row=1, column=3, sticky="w", padx=(8, 0))

        # Row 2: Institution
        lbl_inst = ttk.Label(course, text="Instituição")
        lbl_inst.grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_institution, font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky="w", padx=(8, 16))

        # Row 3: Repo path
        lbl_repo = ttk.Label(course, text="Pasta do repositório")
        lbl_repo.grid(row=3, column=0, sticky="w", pady=4)
        add_tooltip(lbl_repo, "Pasta onde o repositório será criado.\nDentro dela, uma subpasta com o slug da disciplina será gerada automaticamente.")
        ttk.Entry(course, textvariable=self.var_repo_root).grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 8))
        ttk.Button(course, text="📁 Escolher", width=12, command=self.pick_repo_root).grid(row=3, column=3, sticky="w")

        # Row 4: Default mode + OCR
        lbl_dm = ttk.Label(course, text="Modo padrão")
        lbl_dm.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_default_mode, font=("Segoe UI", 10, "bold")).grid(row=4, column=1, sticky="w", padx=(8, 16))

        lbl_ocr = ttk.Label(course, text="OCR padrão")
        lbl_ocr.grid(row=4, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_default_ocr_language, font=("Segoe UI", 10, "bold")).grid(row=4, column=3, sticky="w", padx=(8, 0))

        course.columnconfigure(1, weight=1)
        course.columnconfigure(3, weight=1)

        # ── Toolbar ─────────────────────────────────────────────────────
        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="➕ PDFs", command=self.add_pdfs).pack(side="left")
        ttk.Button(toolbar, text="🖼 Imagens/Fotos", command=self.add_images).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="🔗 Adicionar Link", command=self.add_url).pack(side="left", padx=(6, 0))
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(toolbar, text="✏ Editar", command=self.edit_selected).pack(side="left")
        ttk.Button(toolbar, text="⧉ Duplicar", command=self.duplicate_selected).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="✖ Remover", command=self.remove_selected).pack(side="left", padx=(6, 0))

        ttk.Button(toolbar, text="⚙ Configurações", command=self.open_settings).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="? Ajuda  F1", command=self.open_help).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="📄 Preview", command=self.open_preview).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="🖌 Curator Studio", command=self.open_curator_studio).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="🚀 Criar Repositório", style="Accent.TButton",
                   command=self.build_repo).pack(side="right", padx=(0, 6))

        # ── Table Notebook ──────────────────────────────────────────────────
        self.notebook = ttk.Notebook(top)
        self.notebook.pack(fill="both", expand=True)

        tab_queue = ttk.Frame(self.notebook)
        self.notebook.add(tab_queue, text="  ⏳ Fila a Processar  ")

        columns = ("type", "category", "mode", "profile", "backend", "title", "source")
        self.tree = ttk.Treeview(tab_queue, columns=columns, show="headings", height=14)
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("mode", text="Modo")
        self.tree.heading("profile", text="Perfil")
        self.tree.heading("backend", text="Backend")
        self.tree.heading("title", text="Título")
        self.tree.heading("source", text="Arquivo")
        self.tree.column("type", width=75, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("mode", width=120, anchor="center")
        self.tree.column("profile", width=120, anchor="center")
        self.tree.column("backend", width=120, anchor="center")
        self.tree.column("title", width=330)
        self.tree.column("source", width=360)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

        scroll_q = ttk.Scrollbar(tab_queue, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll_q.set)
        scroll_q.pack(side="right", fill="y")

        tab_backlog = ttk.Frame(self.notebook)
        self.notebook.add(tab_backlog, text="  📁 Backlog (Já Processados)  ")
        
        btn_refresh = ttk.Button(tab_backlog, text="🔄 Atualizar Backlog", command=self._refresh_backlog)
        btn_refresh.pack(anchor="w", pady=(8, 4), padx=8)

        columns_bk = ("category", "layer", "status", "title", "backend", "file")
        self.repo_tree = ttk.Treeview(tab_backlog, columns=columns_bk, show="headings", height=14)
        self.repo_tree.heading("category", text="Categoria")
        self.repo_tree.heading("layer", text="Camada")
        self.repo_tree.heading("status", text="Status")
        self.repo_tree.heading("title", text="Título")
        self.repo_tree.heading("backend", text="Backend")
        self.repo_tree.heading("file", text="Arquivo Original")
        self.repo_tree.column("category", width=140, anchor="center")
        self.repo_tree.column("layer", width=100, anchor="center")
        self.repo_tree.column("status", width=90, anchor="center")
        self.repo_tree.column("title", width=330)
        self.repo_tree.column("backend", width=120, anchor="center")
        self.repo_tree.column("file", width=360)
        self.repo_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        scroll_bk = ttk.Scrollbar(tab_backlog, orient="vertical", command=self.repo_tree.yview)
        self.repo_tree.configure(yscroll=scroll_bk.set)
        scroll_bk.pack(side="right", fill="y", pady=(0, 8))

        # ── Status bar ──────────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=p["header_bg"])
        status_bar.pack(fill="x", side="bottom")

        env_parts = []
        env_parts.append(f"PyMuPDF: {'✓' if HAS_PYMUPDF else '✗'}")
        env_parts.append(f"PyMuPDF4LLM: {'✓' if HAS_PYMUPDF4LLM else '✗'}")
        env_parts.append(f"pdfplumber: {'✓' if HAS_PDFPLUMBER else '✗'}")
        env_parts.append(f"docling: {'✓' if DOCLING_CLI else '✗'}")
        env_parts.append(f"marker: {'✓' if MARKER_CLI else '✗'}")
        env_text = "  |  ".join(env_parts)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(status_bar, textvariable=self._status_var,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="w", padx=10, pady=4).pack(side="left")
        tk.Label(status_bar, text=env_text,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="e", padx=10, pady=4).pack(side="right")

    def _set_status(self, msg: str):
        self._status_var.set(msg)
        self.update_idletasks()

    # ── Actions ──────────────────────────────────────────────────────────────

    def pick_repo_root(self):
        path = filedialog.askdirectory(title="Escolha a pasta onde o repositório será criado")
        if path:
            self.var_repo_root.set(path)

    def open_settings(self):
        SettingsDialog(self, self.config_obj, self.theme_mgr)
        # Sync default vars from config after settings close
        self.var_default_mode.set(self.config_obj.get("default_mode"))
        self.var_default_ocr_language.set(self.config_obj.get("default_ocr_language"))
        self._theme_name = self.config_obj.get("theme")

    def open_help(self):
        HelpWindow(self, self.theme_mgr)

    def open_subject_manager(self):
        SubjectManagerDialog(self, self.subject_store, self.theme_mgr)
        # Refresh combo values
        self._subject_combo["values"] = ["(nenhuma)"] + self.subject_store.names()

    def open_student_profile(self):
        StudentProfileDialog(self, self.student_store, self.theme_mgr)

    def open_preview(self):
        repo_root = self.var_repo_root.get().strip()
        slug = self.var_course_slug.get().strip() or slugify(self.var_course_name.get().strip())
        if repo_root and slug:
            repo_dir = str(Path(repo_root) / slug)
        elif repo_root:
            repo_dir = repo_root
        else:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para visualizar os Markdowns.")
            return
        MarkdownPreviewWindow(self, repo_dir, self.theme_mgr)

    def open_curator_studio(self):
        repo_root = self.var_repo_root.get().strip()
        slug = self.var_course_slug.get().strip() or slugify(self.var_course_name.get().strip())
        if repo_root and slug:
            repo_dir = str(Path(repo_root) / slug)
        elif repo_root:
            repo_dir = repo_root
        else:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para abrir o Curator Studio.")
            return
        
        from src.ui.curator_studio import CuratorStudio
        CuratorStudio(self, repo_dir, self.theme_mgr)

    def _on_subject_selected(self, _event=None):
        name = self._var_active_subject.get()
        if name == "(nenhuma)":
            return
        sp = self.subject_store.get(name)
        if not sp:
            return
        self.var_course_name.set(sp.name)
        self.var_course_slug.set(sp.slug)
        self.var_professor.set(sp.professor)
        self.var_institution.set(sp.institution)
        self.var_semester.set(sp.semester)
        self.var_default_mode.set(sp.default_mode)
        self.var_default_ocr_language.set(sp.default_ocr_lang)
        if sp.repo_root:
            self.var_repo_root.set(sp.repo_root)
        self._set_status(f"Matéria carregada: {sp.name}")
        self._refresh_backlog()

    def _refresh_backlog(self):
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
            
        repo_root = self.var_repo_root.get().strip()
        slug = self.var_course_slug.get().strip()
        if not repo_root or not slug:
            return
            
        repo_dir = Path(repo_root) / slug
        manifest_path = repo_dir / "manifest.json"
        
        if not manifest_path.exists():
            return
            
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            files = data.get("files", [])
            for i, f_data in enumerate(files):
                pipeline = f_data.get("pipeline", {})
                layer = pipeline.get("layer_achieved", "unknown")
                status = pipeline.get("status", "unknown")
                backend = pipeline.get("backend_used", "unknown")
                
                self.repo_tree.insert(
                    "",
                    "end",
                    iid=f"backlog_{i}",
                    values=(
                        f_data.get("category", ""),
                        layer,
                        status,
                        f_data.get("title", ""),
                        backend,
                        Path(f_data.get("source_file", "")).name
                    )
                )
        except Exception as e:
            logging.error(f"Erro ao ler backlog: {e}")

    def _entry_dialog(self, path: str, initial: Optional[FileEntry] = None) -> Optional[FileEntry]:
        dialog = FileEntryDialog(
            self, path, initial=initial,
            default_mode=self.var_default_mode.get(),
            default_ocr_language=self.var_default_ocr_language.get(),
        )
        return dialog.result_entry

    def _quick_add_file(self, path: str, is_image: bool = False) -> FileEntry:
        """Cria FileEntry automaticamente sem abrir diálogo."""
        src = Path(path)
        file_type = "image" if is_image else ("pdf" if src.suffix.lower() == ".pdf" else "image")
        return FileEntry(
            source_path=path,
            file_type=file_type,
            category=auto_detect_category(src.name, is_image),
            title=auto_detect_title(path),
            processing_mode=self.var_default_mode.get(),
            document_profile="auto",
            preferred_backend="auto",
            ocr_language=self.var_default_ocr_language.get(),
        )

    def add_pdfs(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("PDF files", "*.pdf")])
        if self._quick_import.get():
            for path in paths:
                self.entries.append(self._quick_add_file(path))
        else:
            for path in paths:
                entry = self._entry_dialog(path)
                if entry:
                    self.entries.append(entry)
        self.refresh_tree()
        self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_images(self):
        paths = filedialog.askopenfilenames(
            title="Selecione imagens/fotos",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")],
        )
        if self._quick_import.get():
            for path in paths:
                self.entries.append(self._quick_add_file(path, is_image=True))
        else:
            for path in paths:
                entry = self._entry_dialog(path)
                if entry:
                    self.entries.append(entry)
        self.refresh_tree()
        self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_url(self):
        dialog = URLEntryDialog(self)
        self.wait_window(dialog)
        if dialog.result_entry:
            self.entries.append(dialog.result_entry)
            self.refresh_tree()
            self._set_status(f"{len(self.entries)} arquivo(s) na lista.")


    def selected_index(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def edit_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para editar.")
            return
        entry = self.entries[idx]
        updated = self._entry_dialog(entry.source_path, initial=entry)
        if updated:
            self.entries[idx] = updated
            self.refresh_tree()

    def duplicate_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para duplicar.")
            return
        entry = self.entries[idx]
        copied = FileEntry(**asdict(entry))
        copied.title = f"{entry.title} (cópia)"
        self.entries.insert(idx + 1, copied)
        self.refresh_tree()
        self._set_status(f"Item duplicado: {copied.title}")

    def remove_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para remover.")
            return
        removed = self.entries[idx].title
        del self.entries[idx]
        self.refresh_tree()
        self._set_status(f"Removido: {removed}")

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, entry in enumerate(self.entries):
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    entry.file_type,
                    entry.category,
                    entry.processing_mode,
                    entry.document_profile,
                    entry.preferred_backend,
                    entry.title,
                    Path(entry.source_path).name,
                ),
            )

    def _course_meta(self) -> Optional[Dict[str, str]]:
        course_name = self.var_course_name.get().strip()
        repo_root = self.var_repo_root.get().strip()
        if not course_name or not repo_root:
            messagebox.showerror(APP_NAME, "Preencha ao menos o nome da disciplina e a pasta do repositório.")
            return None
        course_slug = self.var_course_slug.get().strip() or slugify(course_name)
        return {
            "course_name": course_name,
            "course_slug": course_slug,
            "semester": self.var_semester.get().strip(),
            "professor": self.var_professor.get().strip(),
            "institution": self.var_institution.get().strip() or "PUCRS",
        }

    def build_repo(self):
        meta = self._course_meta()
        if meta is None:
            return
        if not self.entries:
            if not messagebox.askyesno(APP_NAME, "Nenhum arquivo foi adicionado. Criar apenas a estrutura do repositório?"):
                return

        root_base = Path(self.var_repo_root.get().strip())
        repo_dir = root_base / meta["course_slug"]
        self._set_status(f"Criando repositório em {repo_dir} ...")

        try:
            # Gather student & subject for export
            student_p = self.student_store.profile if self.student_store.profile.full_name else None
            active_subj_name = self._var_active_subject.get()
            active_subj = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None

            builder = RepoBuilder(
                root_dir=repo_dir,
                course_meta=meta,
                entries=self.entries,
                options={
                    "default_processing_mode": self.var_default_mode.get(),
                    "default_ocr_language": self.var_default_ocr_language.get(),
                },
                student_profile=student_p,
                subject_profile=active_subj,
            )
            builder.build()
        except Exception:
            traceback_str = traceback.format_exc()
            self._set_status("Erro ao criar repositório.")
            messagebox.showerror(APP_NAME, f"Erro ao criar repositório:\n\n{traceback_str}")
            return

        self._set_status(f"✓ Repositório criado em: {repo_dir}")
        messagebox.showinfo(
            APP_NAME,
            f"Repositório criado com sucesso em:\n{repo_dir}\n\n"
            f"Próximo passo recomendado:\n"
            f"1. Revisar manual-review/\n"
            f"2. Escolher a melhor saída entre base e avançada\n"
            f"3. Promover conteúdo curado\n"
            f"4. Subir no GitHub"
        )


