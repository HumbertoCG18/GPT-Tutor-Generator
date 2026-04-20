import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import traceback
import logging
import threading
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json
try:
    import pymupdf
except ImportError:
    pymupdf = None

from src.models.core import (
    FileEntry, SubjectStore, StudentStore, SubjectProfile,
    PendingOperation, PendingOperationStore,
)
from src.models.task_queue import RepoTask, RepoTaskStore
from src.utils.helpers import APP_NAME, HAS_PYMUPDF, HAS_PYMUPDF4LLM, HAS_PDFPLUMBER, DOCLING_CLI, MARKER_CLI, TESSDATA_PATH, slugify, CODE_EXTENSIONS, ASSIGNMENT_CATEGORIES, CODE_CATEGORIES, WHITEBOARD_CATEGORIES, get_app_data_dir
from src.builder.runtime.datalab_client import has_datalab_api_key
from src.builder.engine import RepoBuilder
from src.builder.artifacts.prompts import (
    generate_claude_project_instructions,
    generate_gemini_instructions,
    generate_gpt_instructions,
)
from src.builder.ops.task_queue_runner import TaskQueueRunner
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text
from src.ui.theme import ThemeManager, AppConfig
from src.ui.dialogs import FileEntryDialog, URLEntryDialog, SubjectManagerDialog, StudentProfileDialog, HelpWindow, add_tooltip, SettingsDialog, BacklogEntryEditDialog, StatusDialog, _resolve_backlog_markdown_status
from src.ui.repo_dashboard import RepoDashboard, collect_repo_metrics

logger = logging.getLogger(__name__)


def _normalized_source_key(raw_path: str) -> str:
    value = str(raw_path or "").strip()
    if not value:
        return ""
    if "://" in value:
        return value.casefold()
    try:
        normalized = Path(value).expanduser().resolve()
    except Exception:
        normalized = Path(value).expanduser()
    return str(normalized).replace("\\", "/").casefold()


def _manifest_source_keys_for_repo(repo_dir: Optional[Path]) -> set[str]:
    if not repo_dir:
        return set()
    manifest_path = Path(repo_dir) / "manifest.json"
    if not manifest_path.exists():
        return set()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Falha ao ler manifest para reconciliar fila: %s", manifest_path)
        return set()
    return {
        _normalized_source_key(entry.get("source_path", ""))
        for entry in data.get("entries", [])
        if entry.get("source_path")
    }


def _prune_entries_against_manifest(entries: List[FileEntry], repo_dir: Optional[Path]) -> List[FileEntry]:
    processed_sources = _manifest_source_keys_for_repo(repo_dir)
    if not processed_sources:
        return list(entries)
    return [
        entry
        for entry in entries
        if _normalized_source_key(entry.source_path) not in processed_sources
    ]


def _format_backlog_title(entry_data: Dict[str, object]) -> str:
    title = str(entry_data.get("title", "sem título") or "sem título")
    latex = entry_data.get("latex_corruption") or {}
    if isinstance(latex, dict) and latex.get("detected"):
        score = int(latex.get("score", 0) or 0)
        return f"⚠ {title} [{score}/100]"
    return title


def _build_options_from_config(default_mode: str, default_ocr_language: str, config_obj) -> Dict[str, object]:
    return {
        "default_processing_mode": default_mode,
        "default_ocr_language": default_ocr_language,
        "image_format": config_obj.get("image_format"),
        "stall_timeout": config_obj.get("stall_timeout"),
        "marker_use_llm": config_obj.get("marker_use_llm", False),
        "marker_llm_model": config_obj.get("marker_llm_model", ""),
        "marker_torch_device": config_obj.get("marker_torch_device", "auto"),
        "vision_model": config_obj.get("vision_model"),
        "ollama_base_url": config_obj.get("ollama_base_url"),
        "prevent_sleep_during_build": config_obj.get("prevent_sleep_during_build", True),
    }


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


class _FlexToolbar(ttk.Frame):
    """Responsive toolbar that lays out action sections in a wrapping grid."""

    def __init__(self, parent, min_section_width: int = 300, **kwargs):
        super().__init__(parent, **kwargs)
        self._min_section_width = min_section_width
        self._sections: List[ttk.LabelFrame] = []
        self.bind("<Configure>", self._on_configure)

    def add_section(self, title: str) -> ttk.Frame:
        card = ttk.LabelFrame(self, text=f"  {title}", padding=(10, 8))
        inner = ttk.Frame(card)
        inner.pack(fill="both", expand=True)
        self._sections.append(card)
        self.after_idle(self._relayout)
        return inner

    def _on_configure(self, _event=None):
        self.after_idle(self._relayout)

    def _relayout(self):
        if not self.winfo_exists():
            return
        width = max(self.winfo_width(), 1)
        count = len(self._sections)
        if count == 0:
            return

        cols = max(1, min(count, width // self._min_section_width))
        if cols <= 0:
            cols = 1

        for i in range(max(count, cols)):
            self.grid_columnconfigure(i, weight=0)

        for idx, section in enumerate(self._sections):
            row = idx // cols
            col = idx % cols
            section.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        for col in range(cols):
            self.grid_columnconfigure(col, weight=1, uniform="toolbar")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_obj = AppConfig()
        self.theme_mgr = ThemeManager()
        self.subject_store = SubjectStore()
        self.student_store = StudentStore()
        self.pending_op_store = PendingOperationStore()
        self._repo_task_store = RepoTaskStore(get_app_data_dir() / "repo_tasks.json")
        self._repo_tasks: List[RepoTask] = self._repo_task_store.load_all()
        self._repo_task_runner = TaskQueueRunner(
            self._execute_repo_task,
            on_event=self._handle_repo_task_event,
            before_task=self._prepare_repo_task,
        )
        self._repo_task_thread: Optional[threading.Thread] = None
        self._repo_queue_cancel_requested = False
        self._theme_name: str = self.config_obj.get("theme")  # type: ignore[assignment]
        self.title(APP_NAME)
        self.geometry("1360x900")
        self.minsize(900, 600)
        self.entries: List[FileEntry] = []
        self._shutdown_after_build = tk.BooleanVar(value=False)
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()   # clear = paused, set = running
        self._pause_event.set()                 # start in "running" state
        self._active_operation: Optional[PendingOperation] = None
        self._normalize_repo_tasks()

        # Apply theme before building UI
        self.theme_mgr.apply(self, self._theme_name)

        self._build_ui()
        self.bind("<F1>", lambda _: self.open_help())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._offer_resume_pending_operation)

    def _on_close(self):
        if self._active_operation:
            answer = messagebox.askyesnocancel(
                APP_NAME,
                "Existe um processamento em andamento.\n\n"
                "Deseja pausar e sair?\n\n"
                "Sim -> pausa o processamento, salva o estado e fecha o app\n"
                "Não -> fecha o app sem salvar retomada\n"
                "Cancelar -> volta para o aplicativo"
            )
            if answer is None:
                return
            if answer:
                self._persist_pending_operation()
            else:
                self.pending_op_store.clear()
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
        tk.Label(header, text="v3 — Repositórios acadêmicos para Claude, GPT e Gemini",
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
        toolbar = _FlexToolbar(top, min_section_width=320)
        toolbar.pack(fill="x", pady=(0, 10))

        import_actions = toolbar.add_section("Importação")
        build_actions = toolbar.add_section("Processamento e Build")
        tool_actions = toolbar.add_section("Ferramentas")

        for col in range(2):
            import_actions.grid_columnconfigure(col, weight=1, uniform="import")
            tool_actions.grid_columnconfigure(col, weight=1, uniform="tools")
        for col in range(2):
            build_actions.grid_columnconfigure(col, weight=1, uniform="build")

        ttk.Button(import_actions, text="➕ PDFs", command=self.add_pdfs).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(import_actions, text="🖼 Imagens/Fotos", command=self.add_images).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Button(import_actions, text="🔗 Link", command=self.add_url).grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(import_actions, text="💻 Código / ZIP", command=self.add_code_files).grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        ttk.Button(build_actions, text="📂 Abrir Repo", command=self.open_repo_folder).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(build_actions, text="🗂 FILE_MAP", command=self.open_file_map).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self._btn_process = ttk.Button(build_actions, text="⚡ Processar",
                                       command=self.process_selected_single)
        self._btn_process.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self._btn_pause_build = ttk.Button(
            build_actions,
            text="⏸ Pausar Build",
            command=self._toggle_pause_build,
        )
        self._btn_pause_build.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self._btn_pause_build.grid_remove()
        self._btn_build = ttk.Button(build_actions, text="🚀 Criar Repositório",
                                      style="Accent.TButton", command=self.build_repo)
        self._btn_build.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(6, 4))

        ttk.Button(tool_actions, text="🖼 Image Curator", command=self.open_image_curator).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(tool_actions, text="🖌 Curator Studio", command=self.open_curator_studio).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Button(tool_actions, text="⚙ Configurações", command=self.open_settings).grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(tool_actions, text="? Ajuda  F1", command=self.open_help).grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        cb_shutdown = ttk.Checkbutton(
            tool_actions,
            text="⏻ Desligar ao concluir build/fila",
            variable=self._shutdown_after_build,
        )
        cb_shutdown.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 2))
        add_tooltip(
            cb_shutdown,
            "Ative para builds grandes ou filas noturnas.\n"
            "Quando a operação ou a fila terminar com sucesso, o Windows será desligado automaticamente.",
        )

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

        tab_repo_tasks = ttk.Frame(self.notebook)
        self.notebook.add(tab_repo_tasks, text="  🧱 Tasks de Repositório  ")

        repo_task_toolbar = ttk.Frame(tab_repo_tasks)
        repo_task_toolbar.pack(fill="x", padx=8, pady=(6, 4))
        repo_enqueue_menu = tk.Menu(repo_task_toolbar, tearoff=False)
        repo_enqueue_menu.add_command(label="➕ Enfileirar Build Atual", command=self.enqueue_current_repo_build)
        repo_enqueue_menu.add_command(label="➕ Enfileirar Reprocessamento", command=self.enqueue_current_repo_refresh)
        repo_enqueue_menu.add_command(label="➕ Enfileirar Item Selecionado", command=self.enqueue_selected_repo_task)
        self._btn_repo_task_enqueue_menu = ttk.Menubutton(repo_task_toolbar, text="➕ Enfileirar")
        self._btn_repo_task_enqueue_menu.pack(side="left")
        self._btn_repo_task_enqueue_menu["menu"] = repo_enqueue_menu
        self._repo_task_enqueue_menu = repo_enqueue_menu

        self._btn_run_repo_queue = ttk.Button(repo_task_toolbar, text="▶ Executar Fila", command=self.run_repo_task_queue)
        self._btn_run_repo_queue.pack(side="left", padx=(12, 0))
        self._btn_pause_repo_queue = ttk.Button(repo_task_toolbar, text="⏸ Pausar Fila", command=self._toggle_pause_repo_queue, state="disabled")
        self._btn_pause_repo_queue.pack(side="left", padx=(6, 0))
        self._btn_cancel_repo_queue = ttk.Button(repo_task_toolbar, text="⏹ Cancelar Fila", command=self._cancel_repo_task_queue, state="disabled")
        self._btn_cancel_repo_queue.pack(side="left", padx=(6, 0))

        ttk.Separator(repo_task_toolbar, orient="vertical").pack(side="left", fill="y", padx=(10, 10))

        repo_cleanup_menu = tk.Menu(repo_task_toolbar, tearoff=False)
        repo_cleanup_menu.add_command(label="🗑 Remover Task Selecionada", command=self.remove_selected_repo_task)
        repo_cleanup_menu.add_command(label="🧹 Limpar Finalizadas", command=self.clear_finished_repo_tasks)
        self._btn_repo_task_cleanup_menu = ttk.Menubutton(repo_task_toolbar, text="🧹 Limpeza")
        self._btn_repo_task_cleanup_menu.pack(side="left")
        self._btn_repo_task_cleanup_menu["menu"] = repo_cleanup_menu
        self._repo_task_cleanup_menu = repo_cleanup_menu

        repo_task_columns = ("status", "subject", "action", "repo", "created_at", "finished_at", "notes")
        repo_task_body = ttk.Frame(tab_repo_tasks)
        repo_task_body.pack(fill="both", expand=True)
        self.repo_task_tree = ttk.Treeview(repo_task_body, columns=repo_task_columns, show="headings", height=14)
        self.repo_task_tree.heading("status", text="Status")
        self.repo_task_tree.heading("subject", text="Matéria")
        self.repo_task_tree.heading("action", text="Ação")
        self.repo_task_tree.heading("repo", text="Repositório")
        self.repo_task_tree.heading("created_at", text="Criada")
        self.repo_task_tree.heading("finished_at", text="Finalizada")
        self.repo_task_tree.heading("notes", text="Observações")
        self.repo_task_tree.column("status", width=90, anchor="center")
        self.repo_task_tree.column("subject", width=180)
        self.repo_task_tree.column("action", width=130, anchor="center")
        self.repo_task_tree.column("repo", width=260)
        self.repo_task_tree.column("created_at", width=130, anchor="center")
        self.repo_task_tree.column("finished_at", width=130, anchor="center")
        self.repo_task_tree.column("notes", width=260)
        self.repo_task_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        scroll_tasks = ttk.Scrollbar(repo_task_body, orient="vertical", command=self.repo_task_tree.yview)
        self.repo_task_tree.configure(yscroll=scroll_tasks.set)
        scroll_tasks.pack(side="right", fill="y", pady=(0, 8))

        tab_backlog = ttk.Frame(self.notebook)
        self.notebook.add(tab_backlog, text="  📁 Backlog (Já Processados)  ")
        backlog_toolbar = ttk.Frame(tab_backlog)
        backlog_toolbar.pack(fill="x", padx=8, pady=(4, 6))
        ttk.Button(backlog_toolbar, text="🔄 Atualizar Backlog", command=self._refresh_backlog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(backlog_toolbar, text="✏ Editar", command=self.edit_backlog_entry).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(backlog_toolbar, text="🗑 Limpar Processamento", command=self.remove_processed_single).pack(
            side="left", padx=(0, 10)
        )

        ttk.Separator(backlog_toolbar, orient="vertical").pack(side="left", fill="y", padx=(0, 10))

        backlog_repo_menu = tk.Menu(backlog_toolbar, tearoff=False)
        backlog_repo_menu.add_command(label="🔄 Reprocessar Repositório", command=self._reprocess_repo)
        backlog_repo_menu.add_command(label="📋 Gerar Instruções LLM", command=self._generate_llm_instructions)
        backlog_repo_menu.add_command(label="📦 Consolidar Unidade...", command=self._open_consolidate_dialog)
        backlog_repo_menu.add_command(label="📚 Abrir pasta batteries", command=self._open_batteries_folder)
        backlog_repo_menu.add_command(label="📎 Copiar Instruções LLM", command=self._copy_llm_instructions_to_clipboard)

        self._backlog_repo_menu_btn = ttk.Menubutton(backlog_toolbar, text="🗂 Repo")
        self._backlog_repo_menu_btn.pack(side="left")
        self._backlog_repo_menu_btn["menu"] = backlog_repo_menu
        self._backlog_repo_menu = backlog_repo_menu

        columns_bk = ("status", "category", "layer", "tags", "title", "backend", "file")
        backlog_body = ttk.Frame(tab_backlog)
        backlog_body.pack(fill="both", expand=True)

        self.repo_tree = ttk.Treeview(backlog_body, columns=columns_bk, show="headings", height=20)
        self.repo_tree.heading("status", text="Status")
        self.repo_tree.heading("category", text="Categoria")
        self.repo_tree.heading("layer", text="Camada")
        self.repo_tree.heading("tags", text="Tags")
        self.repo_tree.heading("title", text="Título")
        self.repo_tree.heading("backend", text="Backend")
        self.repo_tree.heading("file", text="Arquivo Original")
        self.repo_tree.column("status", width=150, anchor="center")
        self.repo_tree.column("category", width=130, anchor="center")
        self.repo_tree.column("layer", width=100, anchor="center")
        self.repo_tree.column("tags", width=110, anchor="center")
        self.repo_tree.column("title", width=280)
        self.repo_tree.column("backend", width=110, anchor="center")
        self.repo_tree.column("file", width=300)
        self.repo_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        self.repo_tree.bind("<Double-1>", lambda _e: self.edit_backlog_entry())
        self.repo_tree.bind("<Delete>", lambda _e: self.remove_processed_single())

        scroll_bk = ttk.Scrollbar(backlog_body, orient="vertical", command=self.repo_tree.yview)
        self.repo_tree.configure(yscroll=scroll_bk.set)
        scroll_bk.pack(side="right", fill="y", pady=(0, 8))

        tab_dashboard = ttk.Frame(self.notebook)
        self._dashboard_tab = tab_dashboard
        self.notebook.add(tab_dashboard, text="  🖥 Dashboard  ")
        self._repo_dashboard = RepoDashboard(tab_dashboard, on_refresh=self._refresh_repo_dashboard)
        self._repo_dashboard.pack(fill="both", expand=True)

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
        env_parts.append(f"datalab: {'✓' if has_datalab_api_key() else '✗'}")
        env_parts.append(f"docling: {'✓' if DOCLING_CLI else '✗'}")
        env_parts.append(f"marker: {'✓' if MARKER_CLI else '✗'}")
        marker_torch_device = str(self.config_obj.get("marker_torch_device", "auto") or "auto").strip().lower() or "auto"
        marker_torch_effective = "mps" if (marker_torch_device == "auto" and sys.platform == "darwin") else ("cuda" if marker_torch_device == "auto" else marker_torch_device)
        env_parts.append(f"marker torch: {marker_torch_effective}")
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
        self._refresh_repo_task_views()
        self._set_repo_queue_state(False)

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
            self._btn_pause_build.configure(text="⏸ Pausar Build", state="normal")
            self._btn_pause_build.grid()
            # Navega para a aba Log automaticamente
            log_idx = self.notebook.index("end") - 1
            self.notebook.select(log_idx)
        else:
            self._btn_process.configure(state="normal")
            self._btn_build.configure(text="🚀 Criar Repositório",
                                      style="Accent.TButton", command=self.build_repo)
            self._btn_pause_build.grid_remove()

    def _cancel_build(self):
        self._clear_pending_operation()
        self._cancel_event.set()
        self._pause_event.set()
        self._btn_build.configure(state="disabled", text="⏳ Cancelando...")
        if hasattr(self, "_btn_pause_build"):
            self._btn_pause_build.configure(state="disabled")

    def _toggle_pause_build(self):
        if self._pause_event.is_set():
            self._pause_event.clear()
            self._set_status("Build pausado.")
            if hasattr(self, "_btn_pause_build"):
                self._btn_pause_build.configure(text="▶ Retomar Build")
        else:
            self._pause_event.set()
            self._set_status("Build retomado...")
            if hasattr(self, "_btn_pause_build"):
                self._btn_pause_build.configure(text="⏸ Pausar Build")

    # ── Processing-single state (Cancel / Pause / Resume) ─────────────

    def _set_processing_state(self, processing: bool):
        """Muda a UI para o estado de processamento individual."""
        if processing:
            self._cancel_event.clear()
            self._pause_event.set()  # not paused
            self._btn_build.configure(state="disabled")
            self._btn_process.configure(text="⏹ Cancelar",
                                        command=self._cancel_single)
            # Adiciona botão Pausar ao lado (se ainda não existe)
            if not hasattr(self, "_btn_pause"):
                self._btn_pause = ttk.Button(self._btn_process.master,
                                             text="⏸ Pausar",
                                             command=self._toggle_pause_single)
            self._btn_pause.configure(text="⏸ Pausar", state="normal")
            self._btn_pause.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        else:
            self._btn_build.configure(state="normal")
            self._btn_process.configure(text="⚡ Processar",
                                        command=self.process_selected_single)
            if hasattr(self, "_btn_pause"):
                self._btn_pause.grid_remove()

    def _cancel_single(self):
        self._clear_pending_operation()
        self._cancel_event.set()
        self._pause_event.set()  # desbloqueia se estiver pausado
        self._btn_process.configure(state="disabled", text="⏳ Cancelando...")
        if hasattr(self, "_btn_pause"):
            self._btn_pause.configure(state="disabled")

    def _toggle_pause_single(self):
        if self._pause_event.is_set():
            # Pausar
            self._pause_event.clear()
            self._btn_pause.configure(text="▶ Retomar")
            self._progress_animate = False
            self._set_status("Processamento pausado.")
        else:
            # Retomar
            self._pause_event.set()
            self._btn_pause.configure(text="⏸ Pausar")
            self._progress_animate = True
            self._tick_fake_indeterminate()
            self._set_status("Processamento retomado...")

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

    def _make_pending_operation(self, operation_type: str, requested_mode: str,
                                selected_entry_source: str = "") -> PendingOperation:
        return PendingOperation(
            operation_type=operation_type,
            requested_mode=requested_mode,
            repo_root=str(self._repo_dir() or ""),
            course_meta=self._course_meta() or {},
            options=self._build_options(),
            active_subject=self._var_active_subject.get(),
            selected_entry_source=selected_entry_source,
            shutdown_after_build=self._shutdown_after_build.get(),
            entries=[FileEntry.from_dict(e.to_dict()) for e in self.entries],
            created_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _persist_pending_operation(self):
        if not self._active_operation:
            return
        self._save_current_queue()
        self.pending_op_store.save(self._active_operation)

    def _clear_pending_operation(self):
        self._active_operation = None
        self.pending_op_store.clear()

    def _normalize_repo_tasks(self):
        changed = False
        for task in self._repo_tasks:
            if task.status == "running":
                task.status = "pending"
                task.started_at = None
                task.finished_at = None
                changed = True
        if changed:
            self._save_repo_tasks()

    def _save_repo_tasks(self):
        self._repo_task_store.save_all(self._repo_tasks)

    def _refresh_repo_tasks_tree(self):
        if not hasattr(self, "repo_task_tree"):
            return
        self.repo_task_tree.delete(*self.repo_task_tree.get_children())
        for idx, task in enumerate(self._repo_tasks):
            notes = (task.notes or "").strip().replace("\n", " | ")
            self.repo_task_tree.insert(
                "",
                "end",
                iid=f"repo_task_{idx}",
                values=(
                    task.status,
                    task.subject_name,
                    task.action,
                    task.repo_root,
                    task.created_at or "—",
                    task.finished_at or "—",
                    notes[:120] if notes else "—",
                ),
            )

    def _refresh_repo_dashboard(self):
        if not hasattr(self, "_repo_dashboard"):
            return
        subjects = [
            self.subject_store.get(name)
            for name in self.subject_store.names()
        ]
        rows = collect_repo_metrics([sp for sp in subjects if sp], self._repo_tasks)
        self._repo_dashboard.set_rows(rows)

    def _refresh_repo_task_views(self):
        self._save_repo_tasks()
        self._refresh_repo_tasks_tree()
        self._refresh_repo_dashboard()

    @staticmethod
    def _new_repo_task_id() -> str:
        return datetime.now().strftime("task-%Y%m%d%H%M%S%f")

    def _is_repo_task_queue_running(self) -> bool:
        return bool(self._repo_task_thread and self._repo_task_thread.is_alive())

    def _set_repo_queue_state(self, running: bool):
        if hasattr(self, "_btn_run_repo_queue"):
            self._btn_run_repo_queue.configure(state="disabled" if running else "normal")
        if hasattr(self, "_btn_pause_repo_queue"):
            self._btn_pause_repo_queue.configure(
                state="normal" if running else "disabled",
                text="⏸ Pausar Fila" if not running or self._pause_event.is_set() else "▶ Retomar Fila",
            )
        if hasattr(self, "_btn_cancel_repo_queue"):
            self._btn_cancel_repo_queue.configure(state="normal" if running else "disabled")
        if hasattr(self, "_btn_repo_task_enqueue_menu"):
            self._btn_repo_task_enqueue_menu.configure(state="disabled" if running else "normal")
        if hasattr(self, "_btn_repo_task_cleanup_menu"):
            self._btn_repo_task_cleanup_menu.configure(state="disabled" if running else "normal")

    def _queue_task_note(self, action: str, entry_payloads: List[Dict]) -> str:
        if action == "refresh_repo":
            return "Regenerar artefatos estruturais"
        if action == "process_selected":
            if entry_payloads:
                source = Path(entry_payloads[0].get("source_path", "")).name or "item selecionado"
                return f"Processar item: {source}"
            return "Processar item selecionado"
        count = len(entry_payloads)
        return f"Snapshot de {count} arquivo(s)" if count else "Criar/atualizar repositório sem novos arquivos"

    def _build_course_meta_for_subject(self, subject: Optional[SubjectProfile], repo_dir: Path) -> Dict[str, str]:
        course_name = subject.name if subject and subject.name else repo_dir.name
        course_slug = (
            subject.slug if subject and getattr(subject, "slug", "").strip() else slugify(course_name)
        )
        return {
            "course_name": course_name,
            "course_slug": course_slug,
            "semester": getattr(subject, "semester", "") if subject else "",
            "professor": getattr(subject, "professor", "") if subject else "",
            "institution": (getattr(subject, "institution", "") if subject else "") or "PUCRS",
        }

    def _subject_for_task(self, task: RepoTask) -> Optional[SubjectProfile]:
        subject = self.subject_store.get(task.subject_name) if task.subject_name else None
        if subject:
            return subject
        return self._find_subject_by_repo_root(Path(task.repo_root))

    def enqueue_current_repo_build(self):
        self._enqueue_repo_task("build_repo")

    def enqueue_current_repo_refresh(self):
        self._enqueue_repo_task("refresh_repo")

    def enqueue_selected_repo_task(self):
        self._enqueue_repo_task("process_selected")

    def _enqueue_repo_task(self, action: str):
        meta = self._course_meta()
        if meta is None:
            return
        repo_dir = self._repo_dir()
        if not repo_dir:
            return
        entry_payloads: List[Dict] = []
        if action == "build_repo":
            entry_payloads = [entry.to_dict() for entry in self.entries]
        elif action == "process_selected":
            idx = self.selected_index()
            if idx is None:
                messagebox.showinfo(APP_NAME, "Selecione um item na fila a processar para enfileirar o processamento individual.")
                return
            entry_payloads = [self.entries[idx].to_dict()]
        if action == "build_repo" and not entry_payloads and not messagebox.askyesno(
            APP_NAME,
            "Nenhum arquivo novo está na fila.\n\nDeseja enfileirar apenas a criação/atualização estrutural do repositório?",
        ):
            return

        task = RepoTask(
            task_id=self._new_repo_task_id(),
            subject_name=meta["course_name"],
            repo_root=str(repo_dir),
            action=action,
            entry_payloads=entry_payloads,
            shutdown_after_completion=self._shutdown_after_build.get(),
            notes=self._queue_task_note(action, entry_payloads),
        )
        self._repo_tasks.append(task)
        self._refresh_repo_task_views()
        self._set_status(f"Task enfileirada para {task.subject_name}: {task.action}")

    def _prepare_repo_task(self, _task: RepoTask):
        self._pause_event.wait()
        if self._cancel_event.is_set():
            raise InterruptedError("Fila cancelada pelo usuário.")

    def run_repo_task_queue(self):
        if self._is_repo_task_queue_running():
            messagebox.showinfo(APP_NAME, "A fila de repositórios já está em execução.")
            return
        if self._active_operation:
            messagebox.showinfo(APP_NAME, "Finalize ou cancele a operação atual antes de executar a fila de repositórios.")
            return
        if not any(task.status == "pending" for task in self._repo_tasks):
            messagebox.showinfo(APP_NAME, "Não há tasks pendentes na fila de repositórios.")
            return

        self._cancel_event.clear()
        self._pause_event.set()
        self._repo_queue_cancel_requested = False
        self._set_repo_queue_state(True)
        self._start_progress(0)
        self._set_status("Executando fila de repositórios...")

        def worker():
            self._repo_task_runner.run_pending(self._repo_tasks)
            self.after(0, self._on_repo_task_queue_finished)

        self._repo_task_thread = threading.Thread(target=worker, daemon=True)
        self._repo_task_thread.start()

    def _toggle_pause_repo_queue(self):
        if not self._is_repo_task_queue_running():
            return
        if self._pause_event.is_set():
            self._pause_event.clear()
            self._set_status("Fila de repositórios pausada.")
            self._btn_pause_repo_queue.configure(text="▶ Retomar Fila")
        else:
            self._pause_event.set()
            self._set_status("Fila de repositórios retomada.")
            self._btn_pause_repo_queue.configure(text="⏸ Pausar Fila")

    def _cancel_repo_task_queue(self):
        if not self._is_repo_task_queue_running():
            return
        self._repo_queue_cancel_requested = True
        self._cancel_event.set()
        self._pause_event.set()
        self._set_status("Cancelando fila de repositórios...")
        self._btn_cancel_repo_queue.configure(state="disabled")

    def remove_selected_repo_task(self):
        selected = self.repo_task_tree.selection() if hasattr(self, "repo_task_tree") else ()
        if not selected:
            messagebox.showinfo(APP_NAME, "Selecione uma task de repositório para remover.")
            return
        idx = int(selected[0].replace("repo_task_", ""))
        task = self._repo_tasks[idx]
        if task.status == "running":
            messagebox.showinfo(APP_NAME, "Não é possível remover uma task em execução.")
            return
        del self._repo_tasks[idx]
        self._refresh_repo_task_views()

    def clear_finished_repo_tasks(self):
        self._repo_tasks = [task for task in self._repo_tasks if task.status not in {"completed", "failed", "cancelled"}]
        self._refresh_repo_task_views()
        self._set_status("Tasks finalizadas removidas da fila.")

    def open_repo_dashboard_tab(self):
        if hasattr(self, "_dashboard_tab"):
            self.notebook.select(self._dashboard_tab)
            self._refresh_repo_dashboard()

    def _handle_repo_task_event(self, event_name: str, task: RepoTask, error: Optional[Exception]):
        error_text = str(error) if error else ""
        self.after(0, lambda: self._apply_repo_task_event(event_name, task.task_id, error_text))

    def _apply_repo_task_event(self, event_name: str, task_id: str, error_text: str):
        task = next((item for item in self._repo_tasks if item.task_id == task_id), None)
        if not task:
            return
        if event_name == "started":
            self._set_status(f"[Fila] Executando {task.action} em {task.subject_name}...")
        elif event_name == "completed":
            self._consume_repo_task_snapshot(task)
            self._refresh_backlog()
            self._set_status(f"[Fila] Task concluída: {task.subject_name} ({task.action})")
        elif event_name == "cancelled":
            self._set_status(f"[Fila] Task cancelada: {task.subject_name} ({task.action})")
        elif event_name == "failed":
            self._set_status(f"[Fila] Falha em {task.subject_name}: {error_text}")
        self._refresh_repo_task_views()

    def _consume_repo_task_snapshot(self, task: RepoTask):
        if task.action not in {"build_repo", "process_selected"} or not task.entry_payloads:
            return
        processed_sources = {
            item.get("source_path", "")
            for item in task.entry_payloads
            if item.get("source_path")
        }
        if not processed_sources:
            return
        subject = self._subject_for_task(task)
        if subject:
            processed_keys = {_normalized_source_key(path) for path in processed_sources if path}
            updated_queue = [
                entry
                for entry in subject.queue
                if _normalized_source_key(entry.source_path) not in processed_keys
            ]
            if len(updated_queue) != len(subject.queue):
                subject.queue = updated_queue
                self.subject_store.add(subject)
            if self._var_active_subject.get() == subject.name:
                self.entries = [
                    entry
                    for entry in self.entries
                    if _normalized_source_key(entry.source_path) not in processed_keys
                ]
                self.refresh_tree()
                self._save_current_queue()

    def _prune_processed_queue_entries(self, repo_dir: Optional[Path], persist: bool = True) -> List[FileEntry]:
        remaining_entries = _prune_entries_against_manifest(getattr(self, "entries", []), repo_dir)
        entries_changed = len(remaining_entries) != len(getattr(self, "entries", []))
        self.entries = remaining_entries

        subject_store = getattr(self, "subject_store", None)
        matched_subject = self._find_subject_by_repo_root(repo_dir) if repo_dir and subject_store else None
        subject_changed = False
        if matched_subject:
            pruned_queue = _prune_entries_against_manifest(matched_subject.queue, repo_dir)
            if len(pruned_queue) != len(matched_subject.queue):
                matched_subject.queue = pruned_queue
                subject_store.add(matched_subject)
                subject_changed = True

        if persist and entries_changed:
            self.refresh_tree()
            self._save_current_queue()
        elif persist and subject_changed:
            self._refresh_repo_dashboard()

        return remaining_entries

    def _refresh_repo_progress_state(self, repo_dir: Optional[Path]) -> None:
        remaining_entries = self._prune_processed_queue_entries(repo_dir, persist=True)
        if remaining_entries != getattr(self, "entries", []):
            self.entries = remaining_entries
        self._refresh_backlog()
        self._refresh_repo_dashboard()

    def _execute_repo_task(self, task: RepoTask) -> None:
        repo_dir = Path(task.repo_root)
        subject = self._subject_for_task(task)
        meta = self._build_course_meta_for_subject(subject, repo_dir)
        entries = [FileEntry.from_dict(payload) for payload in task.entry_payloads]
        student_profile = self.student_store.profile if self.student_store.profile.full_name else None

        def on_progress(current, total, title):
            self._pause_event.wait()
            if self._cancel_event.is_set():
                raise InterruptedError("Fila cancelada pelo usuário.")
            if title:
                self.after(0, lambda repo_path=repo_dir: self._refresh_repo_progress_state(repo_path))
                self.after(
                    0,
                    lambda c=current, t=total, ti=title, task_ref=task: self._set_status(
                        f"[Fila] {task_ref.subject_name}: ({c + 1}/{max(t, 1)}) {ti}"
                    ),
                )

        builder = RepoBuilder(
            root_dir=repo_dir,
            course_meta=meta,
            entries=entries,
            options=self._build_options(),
            student_profile=student_profile,
            subject_profile=subject,
            progress_callback=on_progress,
        )

        if task.action == "refresh_repo":
            builder.incremental_build()
            return
        if task.action == "process_selected":
            if not entries:
                raise ValueError("Task 'process_selected' sem snapshot do arquivo.")
            builder.process_single(entries[0], force=False)
            return

        manifest_path = repo_dir / "manifest.json"
        if manifest_path.exists():
            builder.incremental_build()
        else:
            builder.build()

    def _on_repo_task_queue_finished(self):
        self._end_progress()
        self._set_repo_queue_state(False)
        self._repo_task_thread = None
        self._cancel_event.clear()
        self._pause_event.set()
        self._refresh_repo_task_views()
        self._refresh_backlog()
        if self._repo_queue_cancel_requested:
            self._set_status("Fila de repositórios interrompida.")
        elif TaskQueueRunner.should_request_shutdown(self._repo_tasks):
            self._schedule_shutdown_after_queue()
        else:
            self._set_status("Fila de repositórios concluída.")
        self._repo_queue_cancel_requested = False

    def _schedule_shutdown_after_queue(self):
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [
                        "shutdown", "/s", "/t", "60",
                        "/c", "Academic Tutor Repo Builder: fila de repositórios concluída.",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Shutdown agendado para 60s após conclusão da fila de repositórios.")
                self._set_status("Fila concluída. Desligamento agendado para 60s. Use 'shutdown /a' para abortar.")
            else:
                logger.warning("Desligamento automático após fila não suportado nesta plataforma.")
                self._set_status("Fila concluída. Desligamento automático não é suportado nesta plataforma.")
        except Exception as e:
            logger.warning("Falha ao agendar desligamento após fila: %s", e)
            self._set_status(f"Fila concluída, mas falhou ao agendar desligamento: {e}")

    def _find_subject_by_repo_root(self, repo_dir: Optional[Path]) -> Optional[SubjectProfile]:
        if not repo_dir:
            return None
        try:
            target = repo_dir.resolve()
        except Exception:
            target = Path(str(repo_dir))
        for name in self.subject_store.names():
            sp = self.subject_store.get(name)
            if not sp or not getattr(sp, "repo_root", ""):
                continue
            try:
                candidate = Path(sp.repo_root).resolve()
            except Exception:
                candidate = Path(sp.repo_root)
            if str(candidate).lower() == str(target).lower():
                return sp
        return None

    def _resolve_subject_profile(self, repo_dir: Optional[Path] = None) -> Optional[SubjectProfile]:
        active_name = self._var_active_subject.get()
        active = self.subject_store.get(active_name) if active_name != "(nenhuma)" else None
        matched = self._find_subject_by_repo_root(repo_dir)
        if matched:
            if active and active.name != matched.name:
                logger.info(
                    "Active subject '%s' ignored for repo %s; using matched profile '%s'.",
                    active.name,
                    repo_dir,
                    matched.name,
                )
            return matched
        return active

    def _reset_build_finish_options(self):
        self._shutdown_after_build.set(False)

    def _schedule_shutdown_after_build(self):
        if not self._shutdown_after_build.get():
            return
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [
                        "shutdown", "/s", "/t", "60",
                        "/c", "Academic Tutor Repo Builder: build concluido com sucesso.",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Shutdown agendado para 60s após conclusão do build.")
                self._set_status("Build concluído. Desligamento agendado para 60s. Use 'shutdown /a' para abortar.")
            else:
                logger.warning("Desligamento automático após build não suportado nesta plataforma.")
                self._set_status("Build concluído. Desligamento automático não é suportado nesta plataforma.")
        except Exception as e:
            logger.warning("Falha ao agendar desligamento após build: %s", e)
            self._set_status(f"Build concluído, mas falhou ao agendar desligamento: {e}")

    def _restore_pending_operation_context(self, op: PendingOperation):
        meta = op.course_meta or {}
        self.var_course_name.set(meta.get("course_name", ""))
        self.var_course_slug.set(meta.get("course_slug", ""))
        self.var_semester.set(meta.get("semester", ""))
        self.var_professor.set(meta.get("professor", ""))
        self.var_institution.set(meta.get("institution", "PUCRS"))
        self.var_repo_root.set(op.repo_root or "")
        self._shutdown_after_build.set(bool(op.shutdown_after_build))
        active_subject = op.active_subject or "(nenhuma)"
        self._var_active_subject.set(active_subject)
        self.entries = [FileEntry.from_dict(e.to_dict()) for e in op.entries]
        self._prune_processed_queue_entries(Path(op.repo_root) if op.repo_root else None, persist=False)
        self.refresh_tree()
        self._save_current_queue()

    def _offer_resume_pending_operation(self):
        op = self.pending_op_store.load()
        if not op:
            return
        type_label = "Build" if op.operation_type == "build" else "Processamento individual"
        item_line = ""
        if op.operation_type == "single" and op.selected_entry_source:
            item_line = f"Arquivo: {Path(op.selected_entry_source).name}\n"
        answer = messagebox.askyesno(
            APP_NAME,
            "Foi encontrada uma sessão anterior com processamento pausado.\n\n"
            f"Tipo: {type_label}\n"
            f"{item_line}"
            f"Repo: {op.repo_root}\n"
            f"Salvo em: {op.created_at or '(sem horário)'}\n\n"
            f"Desligar ao concluir: {'sim' if op.shutdown_after_build else 'não'}\n\n"
            "Deseja retomar o processamento de onde parou?"
        )
        if not answer:
            self.pending_op_store.clear()
            return
        self._restore_pending_operation_context(op)
        if op.operation_type == "build":
            self._resume_pending_build(op)
        elif op.operation_type == "single":
            self._resume_pending_single(op)
        else:
            self.pending_op_store.clear()

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
        self._refresh_repo_dashboard()

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

    def open_image_curator(self):
        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para abrir o Image Curator.")
            return

        from src.ui.image_curator import ImageCurator
        ImageCurator(self, str(repo_dir), self.theme_mgr)

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
        self._refresh_repo_dashboard()
        self._maybe_offer_state_migration(sp)

    def _maybe_offer_state_migration(self, subject) -> None:
        from src.builder.artifacts.student_state import detect_state_version, migrate_v1_to_v2
        repo_dir = self._repo_dir()
        if not repo_dir or detect_state_version(repo_dir) != "v1":
            return
        if not messagebox.askyesno(
            "Migração do STUDENT_STATE",
            "Este repositório usa o formato antigo (v1) do STUDENT_STATE.md.\n"
            "Quer migrar agora para o formato v2 (YAML + baterias)?\n\n"
            "A operação cria backup automático em build/migration-v1-backup/.",
        ):
            return
        teaching_plan = getattr(subject, "teaching_plan", "") or ""
        parsed = _parse_units_from_teaching_plan(teaching_plan)
        units = [
            (slugify(title), [(slugify(_topic_text(t)), _topic_text(t)) for t in topics])
            for title, topics in parsed
        ]
        try:
            result = migrate_v1_to_v2(root_dir=repo_dir, course_map_units=units)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Falha na migração: {exc}")
            return
        if not result.skipped:
            messagebox.showinfo(
                "Migração concluída",
                f"{len(result.created_batteries)} baterias criadas.\n"
                f"Backup em: {result.backup_dir.relative_to(repo_dir)}",
            )

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
                status = _resolve_backlog_markdown_status(f_data, repo_dir)
                self.repo_tree.insert(
                    "",
                    "end",
                    iid=f"backlog_{i}",
                    values=(
                        status.get("status", ""),
                        f_data.get("category", ""),
                        f_data.get("effective_profile", ""),
                        f_data.get("tags", ""),
                        _format_backlog_title(f_data),
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

    def _get_backlog_sources(self) -> set:
        """Return set of source filenames already in the manifest (backlog)."""
        manifest_path = self._manifest_path()
        if not manifest_path:
            return set()
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {Path(e.get("source_path", "")).name for e in data.get("entries", []) if e.get("source_path")}
        except Exception:
            return set()

    def _warn_if_in_backlog(self, paths) -> list:
        """Filter paths, warning about files already in backlog. Returns paths to add."""
        backlog_names = self._get_backlog_sources()
        if not backlog_names:
            return list(paths)

        to_add = []
        for path in paths:
            fname = Path(path).name
            if fname in backlog_names:
                if not messagebox.askyesno(
                    APP_NAME,
                    f"O arquivo '{fname}' já está no backlog (já processado).\n\n"
                    "Deseja adicioná-lo à fila mesmo assim?"
                ):
                    continue
            to_add.append(path)
        return to_add

    def add_pdfs(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("PDF files", "*.pdf")])
        if not paths:
            return
        paths = self._warn_if_in_backlog(paths)
        for path in paths:
            initial = FileEntry(
                source_path=path,
                file_type="pdf",
                title=Path(path).stem,
                category="material-de-aula",
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
        if not paths:
            return
        paths = self._warn_if_in_backlog(paths)
        for path in paths:
            initial = FileEntry(
                source_path=path,
                file_type="image",
                title=Path(path).stem,
                category="fotos-de-prova",
                processing_mode=self.var_default_mode.get(),
                ocr_language=self.var_default_ocr_language.get(),
            )
            entry = self._entry_dialog(path, initial=initial)
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
        paths = self._warn_if_in_backlog(paths)
        for path in paths:
            src = Path(path)
            ft  = "zip" if src.suffix.lower() == ".zip" else "code"
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

    def _build_options(self) -> Dict[str, object]:
        """Monta o dict de opções para o RepoBuilder."""
        return _build_options_from_config(
            self.var_default_mode.get(),
            self.var_default_ocr_language.get(),
            self.config_obj,
        )

    def _repo_dir(self) -> Optional[Path]:
        """Retorna o caminho completo do repositório a partir de var_repo_root.

        var_repo_root armazena o caminho direto da pasta do repo (sem slug).
        """
        repo_root = self.var_repo_root.get().strip()
        if not repo_root:
            return None
        return Path(repo_root)

    def _repo_dir_from_active_subject(self) -> Optional[Path]:
        active_name = self._var_active_subject.get()
        if active_name and active_name != "(nenhuma)":
            sp = self.subject_store.get(active_name)
            if sp and getattr(sp, "repo_root", "").strip():
                return Path(sp.repo_root.strip())
        return self._repo_dir()

    def _open_path_in_system(self, path: Path) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Não foi possível abrir:\n{path}\n\n{e}")

    def build_repo(self):
        if self._is_repo_task_queue_running():
            messagebox.showinfo(APP_NAME, "A fila de repositórios está em execução. Aguarde terminar antes de iniciar um build manual.")
            return
        meta = self._course_meta()
        if meta is None:
            return
        if not self.entries:
            if not messagebox.askyesno(APP_NAME, "Nenhum arquivo foi adicionado. Criar apenas a estrutura do repositório?"):
                return

        platform = self._select_llm_platform()
        if platform is None:
            return
        self._selected_platform = platform
        self._continue_build_repo(meta)

    def _select_llm_platform(self):
        """Mostra dialog para confirmar/alterar a plataforma principal."""
        active_subj_name = self._var_active_subject.get()
        sp = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None
        default = (getattr(sp, "preferred_llm", None) if sp else None) or "claude"

        dialog = tk.Toplevel(self)
        dialog.title("Plataforma principal")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 340) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 240) // 2
        dialog.geometry(f"340x240+{x}+{y}")

        result = {"value": None}

        ttk.Label(dialog,
                  text="Qual plataforma você vai usar principalmente?",
                  wraplength=300, justify="center").pack(pady=(18, 6))

        ttk.Label(dialog,
                  text="O build gera instruções para as três plataformas.\n"
                       "Esta escolha destaca a principal no relatório\n"
                       "e é salva no perfil da matéria.",
                  wraplength=300, justify="center",
                  foreground="gray").pack(pady=(0, 14))

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack()

        PLATFORMS = [
            ("claude", "Claude"),
            ("gpt",    "GPT"),
            ("gemini", "Gemini"),
        ]

        def pick(val):
            result["value"] = val
            if sp:
                sp.preferred_llm = val
                self.subject_store.add(sp)
            dialog.destroy()

        for val, label in PLATFORMS:
            display = f">> {label} <<" if val == default else label
            ttk.Button(btn_frame, text=display, width=14,
                       command=lambda v=val: pick(v)).pack(side="left", padx=4)

        ttk.Button(dialog, text="Cancelar",
                   command=dialog.destroy).pack(pady=(12, 0))

        dialog.wait_window()
        return result["value"]
        
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
        self._pause_event.set()
        self._set_building_state(True)
        self._start_progress(max(len(self.entries), 1))
        total = len(self.entries)
        self._set_status(f"{'Atualizando' if incremental else 'Criando'} repositório em {repo_dir} ...")
        self._active_operation = self._make_pending_operation(
            operation_type="build",
            requested_mode="incremental" if incremental else "full",
        )
        self._persist_pending_operation()

        student_p = self.student_store.profile if self.student_store.profile.full_name else None
        active_subj = self._resolve_subject_profile(repo_dir)

        def on_progress(current, t, title):
            self._pause_event.wait()
            if self._cancel_event.is_set():
                raise InterruptedError("Build cancelado pelo usuário.")
            if title:
                self.after(0, lambda repo_path=repo_dir: self._refresh_repo_progress_state(repo_path))
                self.after(0, lambda c=current, tot=t, ti=title: (
                    self._step_progress(c, max(tot, 1)),
                    self._set_status(f"({c + 1}/{tot}) Processando: {ti}...")
                ))

        def worker():
            try:
                logger.info("Worker iniciado — modo %s, %d entries, repo=%s",
                            "incremental" if incremental else "full", len(self.entries), repo_dir)
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),  # cópia da lista para thread safety
                    options=self._build_options(),
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
        self._end_progress()
        self._set_building_state(False)
        if self._active_operation and self._active_operation.repo_root:
            self._refresh_repo_progress_state(Path(self._active_operation.repo_root))
        self._active_operation = None
        self._reset_build_finish_options()
        self._set_status("Build cancelado.")

    def _on_build_complete(self, meta: dict, repo_dir: Path, incremental: bool):
        self._end_progress()
        self._set_building_state(False)
        n_entries = len(self.entries)
        self.entries = []
        self.refresh_tree()
        self._save_current_queue()
        self._clear_pending_operation()
        shutdown_after_build = self._shutdown_after_build.get()
        self._set_status(f"✓ Repositório {'atualizado' if incremental else 'criado'} em: {repo_dir}")
        if shutdown_after_build:
            logger.info("Build concluído com opção de desligamento ativada.")
            self._schedule_shutdown_after_build()
        elif incremental:
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
        self._reset_build_finish_options()
        self._refresh_backlog()
        self._refresh_repo_dashboard()

    def _on_build_error(self, traceback_str: str):
        self._end_progress()
        self._set_building_state(False)
        if self._active_operation and self._active_operation.repo_root:
            self._refresh_repo_progress_state(Path(self._active_operation.repo_root))
        self._reset_build_finish_options()
        self._set_status("Erro ao criar repositório.")
        messagebox.showerror(APP_NAME, f"Erro ao criar repositório:\n\n{traceback_str}")

    def process_selected_single(self):
        if self._is_repo_task_queue_running():
            messagebox.showinfo(APP_NAME, "A fila de repositórios está em execução. Aguarde terminar antes de processar um item manualmente.")
            return
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

        active_subj = self._resolve_subject_profile(repo_dir)

        self._set_processing_state(True)
        self._set_status(f"Processando item: {entry.title}...")
        self._start_progress(0)  # indeterminate para arquivo único
        self._active_operation = self._make_pending_operation(
            operation_type="single",
            requested_mode="single",
            selected_entry_source=entry.source_path,
        )
        self._persist_pending_operation()

        def on_progress(current, t, title):
            # Pausa: bloqueia a thread worker até retomar
            self._pause_event.wait()
            if self._cancel_event.is_set():
                raise InterruptedError("Processamento cancelado pelo usuário.")

        def worker(force=False):
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),
                    options=self._build_options(),
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj,
                    progress_callback=on_progress,
                )
                result = builder.process_single(entry, force=force)

                if result == "already_exists":
                    self.after(0, lambda: self._ask_reprocess(entry, idx, meta, active_subj, repo_dir))
                else:
                    self.after(0, lambda: self._on_single_processed_success(idx))
            except InterruptedError:
                self.after(0, lambda: self._on_single_interrupted("Processamento cancelado."))
            except Exception:
                traceback_str = traceback.format_exc()
                self.after(0, self._end_progress)
                self.after(0, lambda: self._set_processing_state(False))
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao processar item:\n\n{traceback_str}"))
                self.after(0, lambda: self._set_status("Erro no processamento."))

        threading.Thread(target=worker, daemon=True).start()

    def _ask_reprocess(self, entry, idx, meta, active_subj, repo_dir):
        """Pergunta ao usuário se quer reprocessar um arquivo já existente."""
        self._end_progress()
        self._set_processing_state(False)
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

        self._set_processing_state(True)
        self._set_status(f"Reprocessando: {entry.title}...")
        self._start_progress(0)

        def on_progress(current, t, title):
            self._pause_event.wait()
            if self._cancel_event.is_set():
                raise InterruptedError("Reprocessamento cancelado pelo usuário.")

        def reprocess_worker():
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),
                    options=self._build_options(),
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj,
                    progress_callback=on_progress,
                )
                builder.process_single(entry, force=True)
                self.after(0, lambda: self._on_single_processed_success(idx))
            except InterruptedError:
                self.after(0, lambda: self._on_single_interrupted("Reprocessamento cancelado."))
            except Exception:
                traceback_str = traceback.format_exc()
                self.after(0, self._end_progress)
                self.after(0, lambda: self._set_processing_state(False))
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao reprocessar:\n\n{traceback_str}"))
                self.after(0, lambda: self._set_status("Erro no reprocessamento."))

        threading.Thread(target=reprocess_worker, daemon=True).start()

    def _on_single_processed_success(self, idx):
        self._end_progress()
        self._set_processing_state(False)
        if idx < len(self.entries):
            del self.entries[idx]
            self.refresh_tree()
            self._save_current_queue()
        self._clear_pending_operation()
        self._refresh_backlog()
        self._set_status("Item processado com sucesso.")

    def _on_single_interrupted(self, status_msg: str):
        self._end_progress()
        self._set_processing_state(False)
        self._active_operation = None
        self._set_status(status_msg)

    def _resume_pending_build(self, op: PendingOperation):
        meta = op.course_meta
        repo_dir = Path(op.repo_root)
        self._cancel_event.clear()
        self._pause_event.set()
        self._set_building_state(True)
        self._start_progress(max(len(self.entries), 1))
        self._active_operation = op

        requested_incremental = op.requested_mode == "incremental"
        effective_incremental = requested_incremental or (repo_dir / "manifest.json").exists()
        self._set_status(f"Retomando {'build incremental' if effective_incremental else 'build'} em {repo_dir}...")

        student_p = self.student_store.profile if self.student_store.profile.full_name else None
        active_subj = self._resolve_subject_profile(repo_dir)

        def on_progress(current, t, title):
            self._pause_event.wait()
            if self._cancel_event.is_set():
                raise InterruptedError("Build cancelado pelo usuário.")
            if title:
                self.after(0, lambda repo_path=repo_dir: self._refresh_repo_progress_state(repo_path))
                self.after(0, lambda c=current, tot=t, ti=title: (
                    self._step_progress(c, max(tot, 1)),
                    self._set_status(f"({c + 1}/{tot}) Processando: {ti}...")
                ))

        def worker():
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=list(self.entries),
                    options=op.options or self._build_options(),
                    student_profile=student_p,
                    subject_profile=active_subj,
                    progress_callback=on_progress,
                )
                if effective_incremental:
                    builder.incremental_build()
                else:
                    builder.build()
                self.after(0, lambda: self._on_build_complete(meta, repo_dir, effective_incremental))
            except InterruptedError:
                self.after(0, self._on_build_cancelled)
            except Exception:
                tb = traceback.format_exc()
                self.after(0, lambda: self._on_build_error(tb))

        threading.Thread(target=worker, daemon=True).start()

    def _resume_pending_single(self, op: PendingOperation):
        if not self.entries:
            self.pending_op_store.clear()
            return
        idx = next((i for i, e in enumerate(self.entries) if e.source_path == op.selected_entry_source), None)
        if idx is None:
            self.pending_op_store.clear()
            messagebox.showinfo(APP_NAME, "O item pausado não está mais disponível na fila.")
            return
        self.tree.selection_set(str(idx))
        self.tree.focus(str(idx))
        self.tree.see(str(idx))
        self.process_selected_single()

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
        if self._is_repo_task_queue_running():
            messagebox.showinfo(APP_NAME, "A fila de repositórios está em execução. Aguarde terminar antes de reprocessar manualmente.")
            return
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
            "Isso vai regenerar os artefatos derivados do repositório com o código atual.\n\n"
            "Inclui:\n"
            "• instruções LLM\n"
            "• COURSE_MAP.md e FILE_MAP.md\n"
            "• bundle.seed.json\n"
            "• reinjeção de descrições de imagem no markdown final\n\n"
            "Esse é o caminho recomendado para aplicar a arquitetura low-token em repositórios antigos.\n\n"
            "Deseja continuar?"
        ):
            return

        active_subj = self._resolve_subject_profile(repo_dir)

        def worker():
            try:
                builder = RepoBuilder(
                    root_dir=repo_dir,
                    course_meta=meta,
                    entries=[],
                    options=self._build_options(),
                    student_profile=self.student_store.profile,
                    subject_profile=active_subj,
                )
                builder.incremental_build()
                self.after(0, lambda: self._on_reprocess_done(None))
            except Exception as e:
                self.after(0, lambda: self._on_reprocess_done(e))

        if active_subj:
            self._set_status(f"Reprocessando repositório com perfil da matéria: {active_subj.name}...")
        else:
            self._set_status("Reprocessando repositório sem perfil de matéria associado...")
        threading.Thread(target=worker, daemon=True).start()

    def _on_reprocess_done(self, error):
        if error:
            messagebox.showerror(APP_NAME, f"Erro ao reprocessar: {error}")
            self._set_status("Erro ao reprocessar.")
        else:
            self._refresh_backlog()
            self._set_status("Repositório reprocessado com sucesso e arquitetura reaplicada.")

    def _open_batteries_folder(self) -> None:
        repo_dir = self._repo_dir_from_active_subject()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Selecione uma matéria com repositório configurado.")
            return
        batteries = repo_dir / "student" / "batteries"
        batteries.mkdir(parents=True, exist_ok=True)
        self._open_path_in_system(batteries)

    def _copy_llm_instructions_to_clipboard(self) -> None:
        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório.")
            return

        PLATFORMS = [
            ("claude", "Claude", "INSTRUCOES_CLAUDE_PROJETO.md"),
            ("gpt",    "GPT",    "INSTRUCOES_GPT_PROJETO.md"),
            ("gemini", "Gemini", "INSTRUCOES_GEMINI_PROJETO.md"),
        ]

        dialog = tk.Toplevel(self)
        dialog.title("Copiar Instruções LLM")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 340) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"340x180+{x}+{y}")

        ttk.Label(dialog, text="Qual plataforma você quer copiar?",
                  wraplength=300, justify="center").pack(pady=(18, 6))
        ttk.Label(dialog,
                  text="O conteúdo do arquivo de instruções será copiado\npara a área de transferência.",
                  wraplength=300, justify="center", foreground="gray").pack(pady=(0, 14))

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack()

        def pick(filename):
            dialog.destroy()
            path = repo_dir / "setup" / filename
            if not path.exists():
                messagebox.showwarning(
                    APP_NAME,
                    f"Arquivo não encontrado:\n{path}\n\n"
                    "Use 'Gerar Instruções LLM' primeiro."
                )
                return
            try:
                content = path.read_text(encoding="utf-8")
                self.clipboard_clear()
                self.clipboard_append(content)
                self._set_status(f"Instruções copiadas para a área de transferência: {filename}")
                messagebox.showinfo(
                    APP_NAME,
                    f"Instruções copiadas!\n\nArquivo: setup/{filename}\n"
                    f"Caracteres: {len(content):,}\n\n"
                    "Cole no campo de instruções do projeto na plataforma escolhida."
                )
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Erro ao ler instruções:\n{e}")

        for _val, label, fname in PLATFORMS:
            ttk.Button(btn_frame, text=label, width=10,
                       command=lambda f=fname: pick(f)).pack(side="left", padx=4)

    def _open_consolidate_dialog(self) -> None:
        repo_dir = self._repo_dir_from_active_subject()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Selecione uma matéria com repositório configurado.")
            return
        active_name = self._var_active_subject.get()
        subject = self.subject_store.get(active_name) if active_name != "(nenhuma)" else None
        if not subject:
            messagebox.showinfo(APP_NAME, "Nenhuma matéria ativa.")
            return
        teaching_plan = getattr(subject, "teaching_plan", "") or ""
        from src.ui.consolidate_unit_dialog import ConsolidateUnitDialog
        parsed = _parse_units_from_teaching_plan(teaching_plan)
        units = {
            slugify(title): [(slugify(_topic_text(t)), _topic_text(t)) for t in topics]
            for title, topics in parsed
        }
        if not units:
            messagebox.showinfo(
                APP_NAME,
                "Plano de ensino da matéria não tem unidades detectáveis.",
            )
            return
        ConsolidateUnitDialog(self, repo_dir, units)

    def _generate_llm_instructions(self):
        """Gera/regenera os arquivos de instruções para as 3 plataformas (Claude, GPT, Gemini)."""
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

        # Detectar estado do COURSE_MAP e FILE_MAP
        file_map_path = repo_dir / "course" / "FILE_MAP.md"
        course_map_path = repo_dir / "course" / "COURSE_MAP.md"
        file_map_complete = False
        course_map_exists = course_map_path.exists()
        if file_map_path.exists():
            try:
                fm_content = file_map_path.read_text(encoding="utf-8")
                file_map_complete = "status: pending_review" not in fm_content
            except Exception:
                pass

        repo_ready = file_map_complete and course_map_exists

        if repo_ready:
            # Repo completo — perguntar se quer trocar plataforma ou só gerar
            answer = messagebox.askyesnocancel(
                APP_NAME,
                "O repositório já está configurado:\n"
                "  - COURSE_MAP.md existe\n"
                "  - FILE_MAP.md está completo\n\n"
                "O Protocolo de Primeira Sessão continuará INCLUÍDO.\n\n"
                "Sim → Gerar instruções (manter LLM atual)\n"
                "Não → Escolher outra plataforma principal\n"
                "Cancelar → Abortar"
            )
            if answer is None:
                return
            if answer:
                # Manter plataforma atual
                sp = self._resolve_subject_profile(repo_dir)
                platform = getattr(sp, "preferred_llm", "claude") or "claude"
            else:
                platform = self._select_llm_platform()
                if platform is None:
                    return
        else:
            # Repo incompleto — mostrar seletor normalmente
            status_parts = []
            if not course_map_exists:
                status_parts.append("COURSE_MAP.md não encontrado")
            if not file_map_complete:
                status_parts.append("FILE_MAP.md pendente")
            messagebox.showinfo(
                APP_NAME,
                f"Estado do repositório:\n"
                f"  - {chr(10).join(status_parts)}\n\n"
                f"O Protocolo de Primeira Sessão será INCLUÍDO.\n"
                f"Escolha a plataforma principal:"
            )
            platform = self._select_llm_platform()
            if platform is None:
                return

        active_subj = self._resolve_subject_profile(repo_dir)
        student_p = self.student_store.profile if self.student_store.profile.full_name else None

        try:
            from src.utils.helpers import write_text
            from src.models.core import FileEntry

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            all_entries = []
            try:
                all_entries = [FileEntry.from_dict(e) for e in manifest.get("entries", [])]
            except Exception:
                pass

            common = dict(
                has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in all_entries),
                has_code=any(e.category in CODE_CATEGORIES for e in all_entries),
                has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in all_entries),
            )

            write_text(repo_dir / "setup" / "INSTRUCOES_CLAUDE_PROJETO.md",
                       generate_claude_project_instructions(
                           meta, student_p, active_subj, **common))
            write_text(repo_dir / "setup" / "INSTRUCOES_GPT_PROJETO.md",
                       generate_gpt_instructions(
                           meta, student_p, active_subj, **common))
            write_text(repo_dir / "setup" / "INSTRUCOES_GEMINI_PROJETO.md",
                       generate_gemini_instructions(
                           meta, student_p, active_subj, **common))

            platform_map = {
                "claude": "setup/INSTRUCOES_CLAUDE_PROJETO.md",
                "gpt": "setup/INSTRUCOES_GPT_PROJETO.md",
                "gemini": "setup/INSTRUCOES_GEMINI_PROJETO.md",
            }
            primary = platform_map.get(platform, platform_map["claude"])
            messagebox.showinfo(
                APP_NAME,
                f"Instruções geradas para as 3 plataformas.\n\n"
                f"Plataforma principal: {platform.upper()}\n"
                f"Arquivo: {primary}\n\n"
                "Protocolo de Primeira Sessão INCLUÍDO."
            )
            self._set_status(f"Instruções LLM geradas — principal: {platform.upper()}")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erro ao gerar instruções:\n{e}")
            self._set_status("Erro ao gerar instruções LLM.")

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
            dialog = BacklogEntryEditDialog(self, entry_data, repo_dir=repo_dir, theme_mgr=self.theme_mgr)
            self.wait_window(dialog)

            if dialog.result_data:
                data["entries"][idx].update(dialog.result_data)
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self._refresh_backlog()
                self._set_status(f"✓ Entrada '{dialog.result_data['title']}' atualizada.")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erro ao editar entrada: {e}")

    def open_repo_folder(self):
        """Abre a pasta do repositório da matéria ativa no explorador de arquivos."""
        repo_dir = self._repo_dir_from_active_subject()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Nenhum repositório configurado para a matéria ativa.")
            return
        if not repo_dir.exists():
            messagebox.showerror(APP_NAME, f"A pasta do repositório não existe:\n{repo_dir}")
            return
        self._open_path_in_system(repo_dir)
        self._set_status(f"Pasta do repositório aberta: {repo_dir}")

    def open_file_map(self):
        """Abre course/FILE_MAP.md do repositório da matéria ativa."""
        repo_dir = self._repo_dir_from_active_subject()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Nenhum repositório configurado para a matéria ativa.")
            return
        file_map_path = repo_dir / "course" / "FILE_MAP.md"
        if not file_map_path.exists():
            messagebox.showerror(
                APP_NAME,
                f"FILE_MAP.md não encontrado em:\n{file_map_path}\n\n"
                f"Crie ou processe o repositório antes de tentar abrir esse arquivo."
            )
            return
        self._open_path_in_system(file_map_path)
        self._set_status(f"FILE_MAP aberto: {file_map_path}")


