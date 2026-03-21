import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import traceback
import logging
import threading
from pathlib import Path
from dataclasses import asdict
import json
try:
    import pymupdf
except ImportError:
    pymupdf = None

from src.models.core import FileEntry, SubjectStore, StudentStore, SubjectProfile
from src.utils.helpers import APP_NAME, auto_detect_category, auto_detect_title, HAS_PYMUPDF, HAS_PYMUPDF4LLM, HAS_PDFPLUMBER, DOCLING_CLI, MARKER_CLI, TESSDATA_PATH, slugify, CODE_EXTENSIONS
from src.builder.engine import RepoBuilder
from src.ui.theme import ThemeManager, AppConfig
from src.ui.dialogs import FileEntryDialog, URLEntryDialog, SubjectManagerDialog, StudentProfileDialog, HelpWindow, add_tooltip, SettingsDialog, BacklogEntryEditDialog, StatusDialog

logger = logging.getLogger(__name__)


class _UILogHandler(logging.Handler):
    """Handler que encaminha registros de log para um widget tk.Text."""

    LEVEL_TAG = {
        logging.DEBUG:    "debug",
        logging.INFO:     "info",
        logging.WARNING:  "warning",
        logging.ERROR:    "error",
        logging.CRITICAL: "error",
    }

    def __init__(self, text_widget: "tk.Text", app: "tk.Misc"):
        super().__init__()
        self._text = text_widget
        self._app = app
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                                datefmt="%H:%M:%S")
        self.setFormatter(fmt)

    def emit(self, record: logging.LogRecord):
        msg = self.format(record) + "\n"
        tag = self.LEVEL_TAG.get(record.levelno, "info")
        self._app.after(0, self._write, msg, tag)

    def _write(self, msg: str, tag: str):
        try:
            self._text.configure(state="normal")
            self._text.insert("end", msg, tag)
            self._text.configure(state="disabled")
            self._text.see("end")
        except tk.TclError:
            pass


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
        self._cancel_event = threading.Event()

        # Apply theme before building UI
        self.theme_mgr.apply(self, self._theme_name)

        self._build_ui()
        self.bind("<F1>", lambda _: self.open_help())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.config_obj.save()
        if hasattr(self, "_ui_log_handler"):
            logging.getLogger("src").removeHandler(self._ui_log_handler)
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
        tk.Label(header, text="v3 — Gerador de repositórios para tutores acadêmicos no Claude Projects",
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
        ttk.Button(subj_frame, text="📊 Status", command=self.open_status).pack(side="left", padx=(6, 0))

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
        add_tooltip(lbl_repo, "Caminho completo da pasta do repositório.\nExemplo: C:\\Users\\Humberto\\Documents\\GitHub\\Metodos-Formais-Tutor")
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
        ttk.Button(toolbar, text="💻 Código / ZIP", command=self.add_code_files).pack(side="left", padx=(6, 0))
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        self._btn_process = ttk.Button(toolbar, text="⚡ Processar",
                                       command=self.process_selected_single)
        self._btn_process.pack(side="left")
        ttk.Button(toolbar, text="🔁 Todos → Auto", command=self._set_all_modes_auto).pack(side="left", padx=(6, 0))
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(toolbar, text="📂 Abrir Repo", command=self.open_existing_repo).pack(side="left")

        ttk.Button(toolbar, text="⚙ Configurações", command=self.open_settings).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="? Ajuda  F1", command=self.open_help).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="🖌 Curator Studio", command=self.open_curator_studio).pack(side="right", padx=(6, 0))
        self._btn_build = ttk.Button(toolbar, text="🚀 Criar Repositório",
                                      style="Accent.TButton", command=self.build_repo)
        self._btn_build.pack(side="right", padx=(0, 6))

        # ── Table Notebook ──────────────────────────────────────────────────
        self.notebook = ttk.Notebook(top)
        self.notebook.pack(fill="both", expand=True)

        tab_queue = ttk.Frame(self.notebook)
        self.notebook.add(tab_queue, text="  ⏳ Fila a Processar  ")

        columns = ("enabled", "type", "category", "tags", "mode", "profile", "backend", "title", "source")
        self.tree = ttk.Treeview(tab_queue, columns=columns, show="headings", height=14)
        self.tree.heading("enabled", text="On")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("tags", text="Unidade / Tags")
        self.tree.heading("mode", text="Modo")
        self.tree.heading("profile", text="Perfil")
        self.tree.heading("backend", text="Backend")
        self.tree.heading("title", text="Título")
        self.tree.heading("source", text="Arquivo")
        self.tree.column("enabled", width=40, anchor="center", stretch=False)
        self.tree.column("type", width=75, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("tags", width=120, anchor="center")
        self.tree.column("mode", width=120, anchor="center")
        self.tree.column("profile", width=120, anchor="center")
        self.tree.column("backend", width=120, anchor="center")
        self.tree.column("title", width=280)
        self.tree.column("source", width=300)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())
        self.tree.bind("<Delete>", lambda _e: self.remove_selected())
        self.tree.bind("<space>", lambda _e: self._toggle_selected_enabled())
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        scroll_q = ttk.Scrollbar(tab_queue, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll_q.set)
        scroll_q.pack(side="right", fill="y")

        tab_backlog = ttk.Frame(self.notebook)
        self.notebook.add(tab_backlog, text="  📁 Backlog (Já Processados)  ")
        
        btn_refresh = ttk.Button(tab_backlog, text="🔄 Atualizar Backlog", command=self._refresh_backlog)
        btn_refresh.pack(side="left", pady=(8, 4), padx=8)

        btn_edit_bk = ttk.Button(tab_backlog, text="✏ Editar", command=self.edit_backlog_entry)
        btn_edit_bk.pack(side="left", pady=(8, 4), padx=4)

        btn_unprocess = ttk.Button(tab_backlog, text="🗑 Limpar Processamento", command=self.remove_processed_single)
        btn_unprocess.pack(side="left", pady=(8, 4), padx=4)

        ttk.Separator(tab_backlog, orient="vertical").pack(side="left", fill="y", padx=6, pady=(8, 4))
        btn_reprocess = ttk.Button(tab_backlog, text="🔄 Reprocessar Repositório", command=self._reprocess_repo)
        btn_reprocess.pack(side="left", pady=(8, 4), padx=4)

        columns_bk = ("category", "layer", "tags", "title", "backend", "file")
        self.repo_tree = ttk.Treeview(tab_backlog, columns=columns_bk, show="headings", height=14)
        self.repo_tree.heading("category", text="Categoria")
        self.repo_tree.heading("layer", text="Camada")
        self.repo_tree.heading("tags", text="Tags")
        self.repo_tree.heading("title", text="Título")
        self.repo_tree.heading("backend", text="Backend")
        self.repo_tree.heading("file", text="Arquivo Original")
        self.repo_tree.column("category", width=130, anchor="center")
        self.repo_tree.column("layer", width=100, anchor="center")
        self.repo_tree.column("tags", width=110, anchor="center")
        self.repo_tree.column("title", width=280)
        self.repo_tree.column("backend", width=110, anchor="center")
        self.repo_tree.column("file", width=300)
        self.repo_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        self.repo_tree.bind("<Double-1>", lambda _e: self.edit_backlog_entry())
        self.repo_tree.bind("<Delete>", lambda _e: self.remove_processed_single())

        scroll_bk = ttk.Scrollbar(tab_backlog, orient="vertical", command=self.repo_tree.yview)
        self.repo_tree.configure(yscroll=scroll_bk.set)
        scroll_bk.pack(side="right", fill="y", pady=(0, 8))

        # ── Aba LOG ──────────────────────────────────────────────────────
        tab_log = ttk.Frame(self.notebook)
        self.notebook.add(tab_log, text="  📋 Log  ")

        log_toolbar = ttk.Frame(tab_log)
        log_toolbar.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Button(log_toolbar, text="🗑 Limpar", command=self._clear_log).pack(side="left")

        log_text_frame = ttk.Frame(tab_log)
        log_text_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._log_text = tk.Text(
            log_text_frame,
            state="disabled",
            wrap="none",
            font=("Consolas", 9),
            bg=p["input_bg"],
            fg=p["fg"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=p["border"],
            highlightbackground=p["border"],
        )
        self._log_text.tag_configure("debug",   foreground=p["muted"])
        self._log_text.tag_configure("info",    foreground=p["fg"])
        self._log_text.tag_configure("warning", foreground="#f9e2af")
        self._log_text.tag_configure("error",   foreground="#f38ba8")

        scroll_log_y = ttk.Scrollbar(log_text_frame, orient="vertical",   command=self._log_text.yview)
        scroll_log_x = ttk.Scrollbar(log_text_frame, orient="horizontal", command=self._log_text.xview)
        self._log_text.configure(yscrollcommand=scroll_log_y.set, xscrollcommand=scroll_log_x.set)

        scroll_log_y.pack(side="right",  fill="y")
        scroll_log_x.pack(side="bottom", fill="x")
        self._log_text.pack(side="left", fill="both", expand=True)

        # Registra o handler no logger raiz do projeto
        self._ui_log_handler = _UILogHandler(self._log_text, self)
        self._ui_log_handler.setLevel(logging.DEBUG)
        logging.getLogger("src").addHandler(self._ui_log_handler)

        # ── Status bar ──────────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=p["header_bg"])
        status_bar.pack(fill="x", side="bottom")

        env_parts = []
        env_parts.append(f"PyMuPDF: {'✓' if HAS_PYMUPDF else '✗'}")
        env_parts.append(f"PyMuPDF4LLM: {'✓' if HAS_PYMUPDF4LLM else '✗'}")
        env_parts.append(f"pdfplumber: {'✓' if HAS_PDFPLUMBER else '✗'}")
        env_parts.append(f"docling: {'✓' if DOCLING_CLI else '✗'}")
        env_parts.append(f"marker: {'✓' if MARKER_CLI else '✗'}")
        env_parts.append(f"tessdata: {'✓' if TESSDATA_PATH else '✗'}")
        env_text = "  |  ".join(env_parts)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(status_bar, textvariable=self._status_var,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="w", padx=10, pady=4).pack(side="left")
        tk.Label(status_bar, text=env_text,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="e", padx=10, pady=4).pack(side="right")
        self._progress_bar = ttk.Progressbar(status_bar, mode="determinate", length=200)
        # oculta por padrão; aparece durante operações longas

    def _set_status(self, msg: str):
        self._status_var.set(msg)
        self.update_idletasks()

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _set_building_state(self, building: bool):
        """Muda a UI para o estado de build (botão Cancelar) ou estado normal."""
        if building:
            self._btn_process.configure(state="disabled")
            self._btn_build.configure(text="⏹ Cancelar Build",
                                      style="TButton", command=self._cancel_build)
            # Navega para a aba Log automaticamente
            log_idx = self.notebook.index("end") - 1
            self.notebook.select(log_idx)
        else:
            self._btn_process.configure(state="normal")
            self._btn_build.configure(text="🚀 Criar Repositório",
                                      style="Accent.TButton", command=self.build_repo)

    def _cancel_build(self):
        self._cancel_event.set()
        self._btn_build.configure(state="disabled", text="⏳ Cancelando...")

    def _start_progress(self, total: int):
        """Exibe a barra de progresso. total=0 → animação manual (fake indeterminate)."""
        self._progress_animate = False  # para animação anterior, se houver
        self._progress_bar.configure(mode="determinate", value=0,
                                     maximum=100 if total == 0 else total)
        self._progress_bar.pack(side="right", padx=6, pady=3)
        if total == 0:
            self._progress_animate = True
            self._tick_fake_indeterminate()
        self.update_idletasks()

    def _tick_fake_indeterminate(self):
        """Avança a barra manualmente para simular animação indeterminate."""
        if not getattr(self, "_progress_animate", False):
            return
        v = self._progress_bar["value"]
        self._progress_bar["value"] = (v + 4) % 101
        self.after(40, self._tick_fake_indeterminate)

    def _step_progress(self, current: int, total: int):
        self._progress_bar["value"] = current + 1
        self.update_idletasks()

    def _end_progress(self):
        self._progress_animate = False
        self._progress_bar.pack_forget()
        self._progress_bar["value"] = 0
        self.update_idletasks()

    def _save_current_queue(self):
        """Persiste a fila atual de arquivos no perfil da matéria ativa."""
        name = self._var_active_subject.get()
        if name == "(nenhuma)":
            return
        sp = self.subject_store.get(name)
        if sp:
            sp.queue = self.entries
            self.subject_store.add(sp)  # calls save() internally

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

    def open_status(self):
        StatusDialog(self, self.config_obj, self.student_store, self.theme_mgr)

    def open_curator_studio(self):
        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para abrir o Curator Studio.")
            return
        
        from src.ui.curator_studio import CuratorStudio
        CuratorStudio(self, str(repo_dir), self.theme_mgr)

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
        
        # Carrega a fila salva
        self.entries = [FileEntry.from_dict(e.to_dict()) if hasattr(e, "to_dict") else FileEntry.from_dict(e) for e in sp.queue]
        self.refresh_tree()
        
        self._set_status(f"Matéria carregada: {sp.name} ({len(self.entries)} itens na fila)")
        self._refresh_backlog()

    def _refresh_backlog(self):
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)

        repo_dir = self._repo_dir()
        if not repo_dir:
            return

        manifest_path = repo_dir / "manifest.json"
        
        if not manifest_path.exists():
            return
            
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            entries = data.get("entries", [])
            for i, f_data in enumerate(entries):
                self.repo_tree.insert(
                    "",
                    "end",
                    iid=f"backlog_{i}",
                    values=(
                        f_data.get("category", ""),
                        f_data.get("effective_profile", ""),
                        f_data.get("tags", ""),
                        f_data.get("title", ""),
                        f_data.get("base_backend", ""),
                        Path(f_data.get("source_path", f_data.get("source_file", ""))).name,
                    )
                )
        except Exception as e:
            logging.error(f"Erro ao ler backlog: {e}")

    def _entry_dialog(self, path: str, initial: Optional[FileEntry] = None,
                      file_type_hint: str = "") -> Optional[FileEntry]:
        dialog = FileEntryDialog(
            self, path, initial=initial,
            default_mode=self.var_default_mode.get(),
            default_ocr_language=self.var_default_ocr_language.get(),
            file_type_hint=file_type_hint,
        )
        return dialog.result_entry

    @staticmethod
    def _pdf_page_range(path: str) -> str:
        """Retorna '1-N' com o total de páginas do PDF, ou '' em caso de erro."""
        try:
            doc = pymupdf.open(path)
            n = doc.page_count
            doc.close()
            return f"1-{n}" if n > 0 else ""
        except Exception:
            return ""

    @staticmethod
    def _get_page_count(entry) -> int:
        """Retorna o número de páginas a partir do page_range ou abrindo o PDF."""
        pr = entry.page_range.strip()
        if pr:
            # "1-50" → 50
            parts = pr.split("-")
            try:
                return int(parts[-1])
            except ValueError:
                pass
        try:
            doc = pymupdf.open(entry.source_path)
            n = doc.page_count
            doc.close()
            return n
        except Exception:
            return 0

    def _quick_add_file(self, path: str, is_image: bool = False,
                        file_type_hint: str = "") -> FileEntry:
        """Cria FileEntry automaticamente sem abrir diálogo."""
        src = Path(path)
        if file_type_hint:
            ft = file_type_hint
        elif is_image:
            ft = "image"
        elif src.suffix.lower() == ".pdf":
            ft = "pdf"
        elif src.suffix.lower() == ".zip":
            ft = "zip"
        elif src.suffix.lower() in CODE_EXTENSIONS:
            ft = "code"
        else:
            ft = "image"
        cat = auto_detect_category(src.name, is_image=(ft == "image"))
        page_range = self._pdf_page_range(path) if ft == "pdf" else ""
        return FileEntry(
            source_path=path,
            file_type=ft,
            category=cat,
            title=auto_detect_title(path),
            tags=src.suffix.lower().lstrip(".") if ft == "code" else "",
            processing_mode=self.var_default_mode.get(),
            document_profile="auto",
            preferred_backend="auto",
            ocr_language=self.var_default_ocr_language.get(),
            page_range=page_range,
        )

    def add_pdfs(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("PDF files", "*.pdf")])
        if self._quick_import.get():
            for path in paths:
                self.entries.append(self._quick_add_file(path))
        else:
            for path in paths:
                initial = FileEntry(
                    source_path=path,
                    file_type="pdf",
                    title=auto_detect_title(path),
                    category=auto_detect_category(Path(path).name, False),
                    page_range=self._pdf_page_range(path),
                    processing_mode=self.var_default_mode.get(),
                    ocr_language=self.var_default_ocr_language.get(),
                )
                entry = self._entry_dialog(path, initial=initial)
                if entry:
                    self.entries.append(entry)
        self.refresh_tree()
        self._save_current_queue()
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
        self._save_current_queue()
        self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_url(self):
        dialog = URLEntryDialog(self)
        self.wait_window(dialog)
        if dialog.result_entry:
            self.entries.append(dialog.result_entry)
            self.refresh_tree()
            self._save_current_queue()
            self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_code_files(self):
        ext_str = " ".join(f"*{e}" for e in sorted(CODE_EXTENSIONS))
        paths = filedialog.askopenfilenames(
            title="Selecione arquivos de código ou .zip",
            filetypes=[
                ("Código e ZIP", f"{ext_str} *.zip"),
                ("Python",                  "*.py"),
                ("JavaScript / TypeScript", "*.js *.ts *.jsx *.tsx"),
                ("Java / Kotlin",           "*.java *.kt"),
                ("C / C++",                 "*.c *.cpp *.h *.hpp"),
                ("ZIP com código",          "*.zip"),
                ("Todos os arquivos",       "*.*"),
            ]
        )
        if not paths:
            return
        for path in paths:
            src = Path(path)
            ft  = "zip" if src.suffix.lower() == ".zip" else "code"
            if self._quick_import.get():
                entry = self._quick_add_file(path, file_type_hint=ft)
            else:
                entry = self._entry_dialog(path, file_type_hint=ft)
            if entry:
                self.entries.append(entry)
        self.refresh_tree()
        self._save_current_queue()
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
            self._save_current_queue()

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
        self._save_current_queue()
        self._set_status(f"Item duplicado: {copied.title}")

    def remove_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para remover.")
            return
        removed = self.entries[idx].title
        del self.entries[idx]
        self.refresh_tree()
        self._save_current_queue()
        self._set_status(f"Removido: {removed}")

    def _on_tree_click(self, event):
        """Toggle enabled quando clica na coluna 'On'."""
        region = self.tree.identify_region(event.x, event.y)
        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        logger.debug("Tree click: region=%s col=%s row=%s x=%d", region, col, row_id, event.x)
        if region != "cell":
            return
        if col != "#1":  # coluna "enabled" é a primeira
            return
        if not row_id:
            return
        idx = int(row_id)
        old_val = getattr(self.entries[idx], "enabled", True)
        self.entries[idx].enabled = not old_val
        logger.debug("Toggled entry %d (%s) enabled: %s → %s", idx, self.entries[idx].title, old_val, self.entries[idx].enabled)
        self.refresh_tree()
        self._save_current_queue()
        if self.tree.exists(row_id):
            self.tree.selection_set(row_id)

    def _toggle_selected_enabled(self):
        """Toggle enabled/disabled para os itens selecionados (Space ou clique na coluna On)."""
        selected = self.tree.selection()
        if not selected:
            return
        for iid in selected:
            idx = int(iid)
            entry = self.entries[idx]
            entry.enabled = not getattr(entry, "enabled", True)
        self.refresh_tree()
        self._save_current_queue()
        # Re-selecionar os mesmos itens
        for iid in selected:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)

    def _set_all_modes_auto(self):
        if not self.entries:
            return
        for e in self.entries:
            e.processing_mode = "auto"
        self.refresh_tree()
        self._save_current_queue()
        self._set_status(f"✓ {len(self.entries)} arquivo(s) definidos como modo Auto.")

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.tag_configure("disabled", foreground="#888888")
        for i, entry in enumerate(self.entries):
            enabled = getattr(entry, "enabled", True)
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    "✓" if enabled else "✗",
                    entry.file_type,
                    entry.category,
                    entry.tags,
                    entry.processing_mode,
                    entry.document_profile,
                    entry.preferred_backend,
                    entry.title,
                    Path(entry.source_path).name,
                ),
                tags=() if enabled else ("disabled",),
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

    def _repo_dir(self) -> Optional[Path]:
        """Retorna o caminho completo do repositório a partir de var_repo_root.

        var_repo_root armazena o caminho direto da pasta do repo (sem slug).
        """
        repo_root = self.var_repo_root.get().strip()
        if not repo_root:
            return None
        return Path(repo_root)

    def build_repo(self):
        meta = self._course_meta()
        if meta is None:
            return
        if not self.entries:
            if not messagebox.askyesno(APP_NAME, "Nenhum arquivo foi adicionado. Criar apenas a estrutura do repositório?"):
                return

        self._continue_build_repo(meta)
        
    def _continue_build_repo(self, meta: dict):
        repo_dir = self._repo_dir()
        if not repo_dir:
            return
        manifest_path = repo_dir / "manifest.json"

        # Diálogos devem rodar na thread principal
        incremental = False
        if manifest_path.exists() and self.entries:
            answer = messagebox.askyesnocancel(
                APP_NAME,
                f"Repositório existente detectado em:\n{repo_dir}\n\n"
                f"Deseja adicionar os novos arquivos (Sim)\n"
                f"ou recriar do zero (Não)?\n\n"
                f"Cancelar para abortar."
            )
            if answer is None:
                return
            incremental = answer

        # Detecta PDFs grandes (50+ páginas) e pergunta a ordem
        large_pdfs = [e for e in self.entries if e.file_type == "pdf" and self._get_page_count(e) >= 50]
        if large_pdfs:
            names = "\n".join(f"  • {e.title} ({self._get_page_count(e)} págs)" for e in large_pdfs)
            answer = messagebox.askyesnocancel(
                APP_NAME,
                f"Os seguintes PDFs têm 50+ páginas e podem demorar:\n\n{names}\n\n"
                f"Sim → Processar esses primeiro (prioridade)\n"
                f"Não → Processar esses por último\n"
                f"Cancelar → Manter ordem atual"
            )
            if answer is True:
                # Grandes primeiro
                small = [e for e in self.entries if e not in large_pdfs]
                self.entries = large_pdfs + small
            elif answer is False:
                # Grandes por último
                small = [e for e in self.entries if e not in large_pdfs]
                self.entries = small + large_pdfs
            # None = manter ordem

        self._cancel_event.clear()
        self._set_building_state(True)
        total = len(self.entries)
        self._set_status(f"{'Atualizando' if incremental else 'Criando'} repositório em {repo_dir} ...")

        student_p = self.student_store.profile if self.student_store.profile.full_name else None
        active_subj_name = self._var_active_subject.get()
        active_subj = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None

        def on_progress(current, t, title):
            if self._cancel_event.is_set():
                raise InterruptedError("Build cancelado pelo usuário.")
            if title:
                self.after(0, lambda c=current, tot=t, ti=title:
                           self._set_status(f"({c + 1}/{tot}) Processando: {ti}..."))

        def worker():
            try:
                logger.info("Worker iniciado — modo %s, %d entries, repo=%s",
                            "incremental" if incremental else "full", len(self.entries), repo_dir)
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),  # cópia da lista para thread safety
                    options={
                        "default_processing_mode": self.var_default_mode.get(),
                        "default_ocr_language": self.var_default_ocr_language.get(),
                    },
                    student_profile=student_p,
                    subject_profile=active_subj,
                    progress_callback=on_progress,
                )
                if incremental:
                    builder.incremental_build()
                else:
                    builder.build()
                logger.info("Worker concluído com sucesso.")
                self.after(0, lambda: self._on_build_complete(meta, repo_dir, incremental))
            except InterruptedError:
                self.after(0, self._on_build_cancelled)
            except Exception:
                tb = traceback.format_exc()
                logger.error("Worker falhou:\n%s", tb)
                self.after(0, lambda: self._on_build_error(tb))

        threading.Thread(target=worker, daemon=True).start()

    def _on_build_cancelled(self):
        self._set_building_state(False)
        self._set_status("Build cancelado.")

    def _on_build_complete(self, meta: dict, repo_dir: Path, incremental: bool):
        self._set_building_state(False)
        n_entries = len(self.entries)
        self.entries = []
        self.refresh_tree()
        self._save_current_queue()
        self._set_status(f"✓ Repositório {'atualizado' if incremental else 'criado'} em: {repo_dir}")
        if incremental:
            messagebox.showinfo(
                APP_NAME,
                f"Repositório atualizado com sucesso em:\n{repo_dir}\n\n"
                f"{n_entries} arquivo(s) processado(s).\n\n"
                f"Próximo passo: dar push no GitHub."
            )
        else:
            messagebox.showinfo(
                APP_NAME,
                f"Repositório criado com sucesso em:\n{repo_dir}\n\n"
                f"Próximo passo recomendado:\n"
                f"1. Revisar manual-review/\n"
                f"2. Escolher a melhor saída entre base e avançada\n"
                f"3. Promover conteúdo curado\n"
                f"4. Subir no GitHub"
            )
        self._refresh_backlog()

    def _on_build_error(self, traceback_str: str):
        self._set_building_state(False)
        self._set_status("Erro ao criar repositório.")
        messagebox.showerror(APP_NAME, f"Erro ao criar repositório:\n\n{traceback_str}")

    def process_selected_single(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um arquivo na fila para processar.")
            return
            
        meta = self._course_meta()
        if not meta: return
        
        entry = self.entries[idx]
        repo_dir = self._repo_dir()
        if not repo_dir:
            return
        
        active_subj_name = self._var_active_subject.get()
        active_subj = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None

        self._set_status(f"Processando item: {entry.title}...")
        self._start_progress(0)  # indeterminate para arquivo único

        def worker(force=False):
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),
                    options={
                        "default_processing_mode": self.var_default_mode.get(),
                        "default_ocr_language": self.var_default_ocr_language.get(),
                    },
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj
                )
                result = builder.process_single(entry, force=force)

                if result == "already_exists":
                    self.after(0, lambda: self._ask_reprocess(entry, idx, meta, active_subj, repo_dir))
                else:
                    self.after(0, lambda: self._on_single_processed_success(idx))
            except Exception:
                traceback_str = traceback.format_exc()
                self.after(0, self._end_progress)
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao processar item:\n\n{traceback_str}"))
                self.after(0, lambda: self._set_status("Erro no processamento."))

        threading.Thread(target=worker, daemon=True).start()

    def _ask_reprocess(self, entry, idx, meta, active_subj, repo_dir):
        """Pergunta ao usuário se quer reprocessar um arquivo já existente."""
        self._end_progress()
        answer = messagebox.askyesno(
            APP_NAME,
            f"O arquivo já foi processado anteriormente:\n\n"
            f"  {entry.title}\n"
            f"  ({entry.source_path})\n\n"
            f"Deseja reprocessar, substituindo o resultado anterior?",
        )
        if not answer:
            self._set_status("Reprocessamento cancelado.")
            return

        self._set_status(f"Reprocessando: {entry.title}...")
        self._start_progress(0)

        def reprocess_worker():
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),
                    options={
                        "default_processing_mode": self.var_default_mode.get(),
                        "default_ocr_language": self.var_default_ocr_language.get(),
                    },
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj,
                )
                builder.process_single(entry, force=True)
                self.after(0, lambda: self._on_single_processed_success(idx))
            except Exception:
                traceback_str = traceback.format_exc()
                self.after(0, self._end_progress)
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao reprocessar:\n\n{traceback_str}"))
                self.after(0, lambda: self._set_status("Erro no reprocessamento."))

        threading.Thread(target=reprocess_worker, daemon=True).start()

    def _on_single_processed_success(self, idx):
        self._end_progress()
        if idx < len(self.entries):
            del self.entries[idx]
            self.refresh_tree()
            self._save_current_queue()
        self._refresh_backlog()
        self._set_status("Item processado com sucesso.")

    def remove_processed_single(self):
        selected = self.repo_tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, "Selecione um item no backlog para remover o processamento.")
            return

        meta = self._course_meta()
        if not meta: return

        repo_dir = self._repo_dir()
        if not repo_dir: return
        manifest_path = repo_dir / "manifest.json"

        if not manifest_path.exists(): return
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            idx_str = selected[0]
            if not idx_str.startswith("backlog_"): return
            idx = int(idx_str.replace("backlog_", ""))
            
            entry_data = data["entries"][idx]
            entry_id = entry_data["id"]

            if not messagebox.askyesno(APP_NAME, f"Deseja remover o processamento de '{entry_data['title']}'?\n\nOs arquivos gerados no repositório serão deletados."):
                return

            builder = RepoBuilder(repo_dir, meta, [], {})
            if builder.unprocess(entry_id):
                self._refresh_backlog()
                self._set_status(f"Processamento de '{entry_id}' removido.")
            else:
                self._set_status("Falha ao remover processamento.")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erro ao remover processamento: {e}")

    def _reprocess_repo(self):
        """Regenera todos os arquivos pedagógicos do repositório com o código atual."""
        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório.")
            return
        manifest_path = repo_dir / "manifest.json"
        if not manifest_path.exists():
            messagebox.showinfo(APP_NAME, "Nenhum repositório encontrado nessa pasta.")
            return
        meta = self._course_meta()
        if meta is None:
            return

        if not messagebox.askyesno(
            APP_NAME,
            "Isso vai regenerar todos os arquivos pedagógicos (instruções, course map, glossário, etc.) "
            "com o código atual.\n\nDeseja continuar?"
        ):
            return

        active_subj_name = self._var_active_subject.get()
        active_subj = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None

        def worker():
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=[],
                    options={
                        "default_processing_mode": self.var_default_mode.get(),
                        "default_ocr_language": self.var_default_ocr_language.get(),
                    },
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj,
                )
                builder.incremental_build()
                self.after(0, lambda: self._on_reprocess_done(None))
            except Exception as e:
                self.after(0, lambda: self._on_reprocess_done(e))

        self._set_status("Reprocessando repositório...")
        threading.Thread(target=worker, daemon=True).start()

    def _on_reprocess_done(self, error):
        if error:
            messagebox.showerror(APP_NAME, f"Erro ao reprocessar: {error}")
            self._set_status("Erro ao reprocessar.")
        else:
            self._refresh_backlog()
            self._set_status("Repositório reprocessado com sucesso.")

    def _manifest_path(self) -> Optional[Path]:
        """Retorna o caminho do manifest.json do repositório ativo, ou None."""
        repo_dir = self._repo_dir()
        if not repo_dir:
            return None
        p = repo_dir / "manifest.json"
        return p if p.exists() else None

    def edit_backlog_entry(self):
        selected = self.repo_tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, "Selecione um item no backlog para editar.")
            return

        idx_str = selected[0]
        if not idx_str.startswith("backlog_"):
            return
        idx = int(idx_str.replace("backlog_", ""))

        manifest_path = self._manifest_path()
        if not manifest_path:
            messagebox.showerror(APP_NAME, "Repositório não encontrado.")
            return

        repo_dir = self._repo_dir()

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entry_data = data["entries"][idx]
            dialog = BacklogEntryEditDialog(self, entry_data, repo_dir=repo_dir)

            if dialog.result_data:
                data["entries"][idx].update(dialog.result_data)
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self._refresh_backlog()
                self._set_status(f"✓ Entrada '{dialog.result_data['title']}' atualizada.")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erro ao editar entrada: {e}")

    def open_existing_repo(self):
        """Abre um repositório existente e carrega seus dados."""
        path = filedialog.askdirectory(title="Selecione a pasta raiz do repositório")
        if not path:
            return
        repo_dir = Path(path)
        manifest_path = repo_dir / "manifest.json"
        if not manifest_path.exists():
            messagebox.showerror(APP_NAME, f"Nenhum manifest.json encontrado em:\n{repo_dir}\n\nEsta pasta não parece ser um repositório gerado.")
            return
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            course = data.get("course", {})
            self.var_course_name.set(course.get("course_name", ""))
            self.var_course_slug.set(course.get("course_slug", ""))
            self.var_professor.set(course.get("professor", ""))
            self.var_institution.set(course.get("institution", "PUCRS"))
            self.var_semester.set(course.get("semester", ""))
            # Caminho completo do repositório
            self.var_repo_root.set(str(repo_dir))
            self._set_status(f"Repositório carregado: {course.get('course_name', repo_dir.name)}")
            self._refresh_backlog()
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erro ao carregar repositório:\n{e}")


