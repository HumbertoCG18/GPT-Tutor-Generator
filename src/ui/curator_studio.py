import io
import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from PIL import Image, ImageTk
from src.models.core import FileEntry
from src.builder.artifacts.navigation import (
    _clean_extraction_noise,
    _inject_executive_summary,
)
from src.builder.engine import (
    RepoBuilder,
    migrate_legacy_url_manual_reviews,
)
from src.ui.image_curator import _inject_all_image_descriptions_from_manifest

from src.utils.helpers import HAS_PYMUPDF, slugify

if HAS_PYMUPDF:
    import pymupdf

logger = logging.getLogger(__name__)

CURATOR_PDF_PREVIEW_MAX_PAGES = 6
CURATOR_SOURCE_MAX_BYTES = 400_000
CURATOR_PREVIEW_BASE_WIDTH = 400
CURATOR_PREVIEW_ZOOM_MIN = 0.5
CURATOR_PREVIEW_ZOOM_MAX = 2.5
CURATOR_PREVIEW_ZOOM_STEP = 0.25


def _curator_studio_layout_mode(width: int) -> str:
    if width >= 1400:
        return "wide"
    if width >= 980:
        return "medium"
    return "stacked"


def _parse_review_frontmatter(content: str) -> dict:
    """Parse YAML-like frontmatter from a review markdown file."""
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


def _curator_supports_review_path(path: Path) -> bool:
    """Ignore review files that do not belong to the Curator Studio flow."""
    if path.parent.name not in {"pdfs", "images"}:
        return False
    if path.parent.name == "images":
        return True

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return True

    fm = _parse_review_frontmatter(content[:8192])
    if fm.get("type") == "manual_url_review":
        return False
    if fm.get("base_backend") == "url_fetcher":
        return False
    return True


def _read_curator_source_text(path: Path, max_bytes: int = CURATOR_SOURCE_MAX_BYTES) -> tuple[str, bool]:
    """Read source text for the editor without loading arbitrarily large files."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        content = handle.read(max_bytes + 1)
    truncated = len(content) > max_bytes
    if truncated:
        content = content[:max_bytes]
    return content, truncated


def _preview_page_indices(page_count: int, max_pages: int = CURATOR_PDF_PREVIEW_MAX_PAGES) -> list[int]:
    """Return the subset of PDF pages rendered in Curator Studio previews."""
    return list(range(min(max(page_count, 0), max_pages)))


def _clamp_preview_zoom(value: float) -> float:
    return max(CURATOR_PREVIEW_ZOOM_MIN, min(CURATOR_PREVIEW_ZOOM_MAX, round(value, 2)))


def _preview_target_width(zoom: float) -> int:
    return max(int(CURATOR_PREVIEW_BASE_WIDTH * _clamp_preview_zoom(zoom)), 120)


def _manual_crop_filename(entry_id: str, page_num: int) -> str:
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{entry_id}-page-{page_num:03d}-manual-{timestamp}.png"


_MARKDOWN_IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _markdown_image_reference(markdown_path: Path, image_path: Path, repo_dir: Path) -> str:
    try:
        rel = image_path.resolve().relative_to(repo_dir.resolve())
        return f"![]({str(rel).replace(chr(92), '/')})"
    except Exception:
        pass

    try:
        rel = Path(os.path.relpath(image_path, start=markdown_path.parent))
    except Exception:
        rel = image_path.relative_to(repo_dir)
    return f"![]({str(rel).replace(chr(92), '/')})"


def _normalize_repo_image_references(content: str, markdown_path: Path, repo_dir: Path) -> str:
    """Rewrite local markdown image refs to stable repo-relative paths.

    Curator Studio markdown can move between staging/, manual-review/ and
    content/curated/. Relative refs created from the current file location break
    after those moves, so repo-local assets are normalized to repo-relative
    paths such as ``content/images/...``.
    """
    repo_root = repo_dir.resolve()
    markdown_dir = markdown_path.parent.resolve()

    def repl(match: re.Match[str]) -> str:
        alt = match.group(1)
        raw_path = match.group(2).strip()
        normalized = raw_path.replace("\\", "/")

        if re.match(r"^[a-z]+://", normalized, re.IGNORECASE):
            return match.group(0)

        candidate: Path | None = None
        raw_candidate = Path(normalized)
        if raw_candidate.is_absolute() and raw_candidate.exists():
            candidate = raw_candidate.resolve()
        else:
            rel_to_md = (markdown_dir / normalized).resolve()
            if rel_to_md.exists():
                candidate = rel_to_md
            else:
                rel_to_repo = (repo_root / normalized).resolve()
                if rel_to_repo.exists():
                    candidate = rel_to_repo

        if candidate is None:
            return match.group(0)

        try:
            repo_rel = candidate.relative_to(repo_root)
        except ValueError:
            return match.group(0)

        return f"![{alt}]({str(repo_rel).replace(chr(92), '/')})"

    return _MARKDOWN_IMAGE_REF_RE.sub(repl, content)


def _curator_review_paths(repo_dir: Path) -> List[Path]:
    """Return only manual-review files handled by Curator Studio."""
    manual_dir = repo_dir / "manual-review"
    if not manual_dir.exists():
        return []

    paths: List[Path] = []
    for subdir in ("pdfs", "images"):
        review_dir = manual_dir / subdir
        if not review_dir.exists():
            continue
        for path in sorted(review_dir.rglob("*.md")):
            if _curator_supports_review_path(path):
                paths.append(path)
    return paths


def _merge_review_frontmatter_with_manifest(fm: dict, manifest_entry: dict | None) -> dict:
    """Overlay missing review-template fields with the current manifest entry."""
    merged = dict(fm or {})
    if not manifest_entry:
        return merged

    for key in (
        "id",
        "title",
        "category",
        "processing_mode",
        "effective_profile",
        "base_backend",
        "advanced_backend",
        "base_markdown",
        "advanced_markdown",
        "manual_review",
        "raw_target",
        "source_path",
    ):
        if not merged.get(key) and manifest_entry.get(key):
            merged[key] = manifest_entry.get(key)

    if not merged.get("source_pdf"):
        merged["source_pdf"] = manifest_entry.get("raw_target") or manifest_entry.get("source_path")

    return merged


def _is_pdf_preview_target(path_value: str | None) -> bool:
    """Return True only for paths that really look like PDFs."""
    if not path_value:
        return False
    return str(path_value).lower().endswith(".pdf")


class CuratorStudio(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        try:
            migrated = migrate_legacy_url_manual_reviews(self.repo_dir)
            if migrated:
                logger.info("Migrated %d legacy URL manual-review files to manual-review/web.", migrated)
        except Exception as exc:
            logger.warning("Could not migrate legacy URL manual-review files: %s", exc)
        self.theme_mgr = theme_mgr
        self._theme_name = parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"

        self.title("Curator Studio")
        self.geometry("1600x900")
        self.minsize(1100, 650)

        self.current_md_path = None          # review template .md path
        self._current_content_path = None    # actual markdown file being edited
        self._current_content_truncated = False
        self._current_frontmatter = {}
        self._available_sources = {}
        self.preview_images = []
        self._preview_zoom = 1.0
        self._preview_notice_var = tk.StringVar(value="")
        self._zoom_var = tk.StringVar(value="100%")
        self._crop_mode = tk.BooleanVar(value=False)
        self._preview_crop_rect = None
        self._preview_crop_start = None
        self._preview_crop_canvas = None
        self._preview_crop_meta = None
        self._preview_pdf_path = None
        self._layout_mode = ""

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_files()
        self.bind("<Configure>", self._on_layout_change)
        self.after_idle(self._apply_responsive_layout)

    def _repo_course_meta(self) -> dict:
        manifest_path = self.repo_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                course = manifest.get("course")
                if isinstance(course, dict):
                    course_name = str(course.get("course_name", "") or "").strip() or self.repo_dir.name
                    course_slug = str(course.get("course_slug", "") or "").strip() or slugify(course_name) or slugify(self.repo_dir.name) or "curso"
                    return {
                        "course_name": course_name,
                        "course_slug": course_slug,
                        "semester": str(course.get("semester", "") or "").strip(),
                        "professor": str(course.get("professor", "") or "").strip(),
                        "institution": str(course.get("institution", "") or "").strip() or "PUCRS",
                    }
            except Exception as exc:
                logger.warning("Falha ao carregar course_meta do manifest para reprovação: %s", exc)

        parent_app = self.master
        if hasattr(parent_app, "_find_subject_by_repo_root") and hasattr(parent_app, "_build_course_meta_for_subject"):
            try:
                subject = parent_app._find_subject_by_repo_root(self.repo_dir)
                return parent_app._build_course_meta_for_subject(subject, self.repo_dir)
            except Exception as exc:
                logger.warning("Falha ao montar course_meta via app principal para reprovação: %s", exc)

        course_name = self.repo_dir.name
        return {
            "course_name": course_name,
            "course_slug": slugify(course_name) or "curso",
            "semester": "",
            "professor": "",
            "institution": "PUCRS",
        }

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
        ttk.Button(toolbar, text="⛔ Reprovado", command=self._reject_current).pack(side="right", padx=5)
        ttk.Button(toolbar, text="✅ Aprovar Todos", command=self._approve_all_pending).pack(side="right", padx=5)
        ttk.Button(toolbar, text="🔄 Restaurar Pendentes", command=self._restore_orphan_entries).pack(side="right", padx=5)
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

        preview_header = ttk.Frame(preview_frame)
        preview_header.pack(fill="x", pady=(0, 5))
        ttk.Label(preview_header, text="Visualização (Preview original)", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Checkbutton(
            preview_header,
            text="Recortar região",
            variable=self._crop_mode,
            command=self._toggle_preview_crop_mode,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(preview_header, text="-", width=3, command=lambda: self._change_preview_zoom(-CURATOR_PREVIEW_ZOOM_STEP)).pack(side="right")
        ttk.Button(preview_header, text="+", width=3, command=lambda: self._change_preview_zoom(CURATOR_PREVIEW_ZOOM_STEP)).pack(side="right", padx=(4, 0))
        ttk.Button(preview_header, textvariable=self._zoom_var, width=7, command=self._reset_preview_zoom).pack(side="right", padx=(8, 4))

        self.canvas = tk.Canvas(preview_frame, bg=p["frame_bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        cvs_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        cvs_scroll.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=cvs_scroll.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.preview_notice = ttk.Label(preview_frame, textvariable=self._preview_notice_var)
        self.preview_notice.pack(fill="x", anchor="w", pady=(4, 0))

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

    def _on_layout_change(self, _event=None):
        self.after_idle(self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        mode = _curator_studio_layout_mode(self.winfo_width())
        if mode == self._layout_mode:
            return
        self._layout_mode = mode

        orient = "vertical" if mode == "stacked" else "horizontal"
        try:
            self.paned.configure(orient=orient)
        except tk.TclError:
            return

        total_width = max(self.winfo_width() - 40, 1)
        total_height = max(self.winfo_height() - 140, 1)
        try:
            if mode == "wide":
                self.paned.sashpos(0, min(320, max(total_width // 5, 240)))
                self.paned.sashpos(1, min(900, max(total_width // 2, 640)))
                self.info_label.configure(wraplength=700)
            elif mode == "medium":
                self.paned.sashpos(0, min(260, max(total_width // 5, 200)))
                self.paned.sashpos(1, min(620, max(total_width // 2, 480)))
                self.info_label.configure(wraplength=560)
            else:
                self.paned.sashpos(0, max(int(total_height * 0.22), 180))
                self.paned.sashpos(1, max(int(total_height * 0.56), 420))
                self.info_label.configure(wraplength=max(self.winfo_width() - 80, 320))
        except tk.TclError:
            pass

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

    def _set_preview_zoom(self, zoom: float):
        zoom = _clamp_preview_zoom(zoom)
        if abs(zoom - self._preview_zoom) < 1e-6:
            return
        self._preview_zoom = zoom
        self._zoom_var.set(f"{int(round(self._preview_zoom * 100))}%")
        self._refresh_previews()

    def _change_preview_zoom(self, delta: float):
        self._set_preview_zoom(self._preview_zoom + delta)

    def _reset_preview_zoom(self):
        self._set_preview_zoom(1.0)

    def _refresh_previews(self):
        if self._current_frontmatter:
            self._load_previews(self._current_frontmatter)

    def _toggle_preview_crop_mode(self):
        if not self._crop_mode.get():
            self._clear_preview_crop()
            self.canvas.config(cursor="")
        else:
            self.canvas.config(cursor="crosshair")
        self._refresh_previews()

    def _clear_preview_crop(self):
        if self._preview_crop_canvas is not None and self._preview_crop_rect is not None:
            try:
                self._preview_crop_canvas.delete(self._preview_crop_rect)
            except tk.TclError:
                pass
        self._preview_crop_rect = None
        self._preview_crop_start = None
        self._preview_crop_canvas = None
        self._preview_crop_meta = None

    def _preview_crop_start_drag(self, event, canvas: tk.Canvas, page_meta: dict):
        if not self._crop_mode.get():
            return
        self._preview_crop_canvas = canvas
        self._preview_crop_meta = page_meta
        self._preview_crop_start = (canvas.canvasx(event.x), canvas.canvasy(event.y))
        if self._preview_crop_rect is not None:
            canvas.delete(self._preview_crop_rect)
            self._preview_crop_rect = None

    def _preview_crop_drag(self, event, canvas: tk.Canvas):
        if not self._crop_mode.get() or not self._preview_crop_start:
            return
        x0, y0 = self._preview_crop_start
        x1 = canvas.canvasx(event.x)
        y1 = canvas.canvasy(event.y)
        if self._preview_crop_rect is not None:
            canvas.delete(self._preview_crop_rect)
        self._preview_crop_rect = canvas.create_rectangle(
            x0, y0, x1, y1, outline="#a6e3a1", width=2, dash=(4, 2)
        )

    def _preview_crop_end_drag(self, event, canvas: tk.Canvas):
        if not self._crop_mode.get() or not self._preview_crop_start or not self._preview_crop_meta:
            return
        x0, y0 = self._preview_crop_start
        x1 = canvas.canvasx(event.x)
        y1 = canvas.canvasy(event.y)
        self._preview_crop_start = None

        rx0, rx1 = min(x0, x1), max(x0, x1)
        ry0, ry1 = min(y0, y1), max(y0, y1)
        if (rx1 - rx0) < 10 or (ry1 - ry0) < 10:
            self._clear_preview_crop()
            return

        self._save_preview_crop(rx0, ry0, rx1, ry1, self._preview_crop_meta)

    def _bind_preview_crop_events(self, canvas: tk.Canvas, page_meta: dict):
        canvas.bind("<ButtonPress-1>", lambda event, c=canvas, meta=page_meta: self._preview_crop_start_drag(event, c, meta))
        canvas.bind("<B1-Motion>", lambda event, c=canvas: self._preview_crop_drag(event, c))
        canvas.bind("<ButtonRelease-1>", lambda event, c=canvas: self._preview_crop_end_drag(event, c))

    def _save_preview_crop(self, x0: float, y0: float, x1: float, y1: float, page_meta: dict):
        if not self._current_content_path:
            messagebox.showerror("Curator Studio", "Nenhum markdown aberto para receber a imagem.", parent=self)
            return
        if not self._preview_pdf_path or not HAS_PYMUPDF:
            messagebox.showerror("Curator Studio", "Preview de PDF indisponível para recorte.", parent=self)
            return

        page_num = page_meta["page_num"]
        render_scale = page_meta["render_scale"]
        display_scale = page_meta["display_scale"]
        entry_id = (
            self._current_frontmatter.get("id")
            or (self.current_md_path.stem if self.current_md_path else "entry")
        )
        crop_dir = self.repo_dir / "content" / "images" / "manual-crops"
        crop_dir.mkdir(parents=True, exist_ok=True)
        out_path = crop_dir / _manual_crop_filename(entry_id, page_num)

        try:
            doc = pymupdf.open(str(self._preview_pdf_path))
            page = doc[max(page_num - 1, 0)]
            rect = pymupdf.Rect(
                x0 / display_scale / render_scale,
                y0 / display_scale / render_scale,
                x1 / display_scale / render_scale,
                y1 / display_scale / render_scale,
            )
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0), clip=rect)
            pix.save(str(out_path))
            doc.close()
        except Exception as exc:
            messagebox.showerror("Curator Studio", f"Falha ao capturar região:\n{exc}", parent=self)
            return

        image_ref = _markdown_image_reference(self._current_content_path, out_path, self.repo_dir)
        insert_text = f"\n{image_ref}\n"
        self.editor.insert(tk.INSERT, insert_text)
        self.editor.edit_modified(True)
        self.status_var.set(f"Região capturada e inserida no markdown: {out_path.name}")
        self._crop_mode.set(False)
        self._toggle_preview_crop_mode()

    # ── File loading ────────────────────────────────────────────────────

    def _load_files(self):
        self.file_list.delete(0, tk.END)
        self.file_paths = []

        for p in _curator_review_paths(self.repo_dir):
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
        fm = _merge_review_frontmatter_with_manifest(
            fm,
            self._lookup_manifest_entry(fm.get("id") or self.current_md_path.stem),
        )
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
        return _parse_review_frontmatter(content)

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
        self._current_content_truncated = False
        try:
            content, truncated = _read_curator_source_text(path)
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, content)
            self.editor.edit_modified(False)
            self._current_content_truncated = truncated
            try:
                rel = path.relative_to(self.repo_dir)
            except ValueError:
                rel = path.name
            if truncated:
                self.status_var.set(
                    f"Visualização parcial: {rel} "
                    f"(arquivo grande; abra externamente para editar por completo)"
                )
            else:
                self.status_var.set(f"Editando: {rel}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler arquivo:\n{e}")

    # ── Image Previews ──────────────────────────────────────────────────

    def _load_previews(self, fm: dict):
        """Render preview from source PDF (via PyMuPDF) or raw images."""
        self._current_frontmatter = dict(fm or {})
        self._preview_pdf_path = None
        self._clear_preview_crop()
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.preview_images.clear()
        self._preview_notice_var.set("")

        bg = self.theme_mgr.palette(self._theme_name)["frame_bg"]
        target_width = _preview_target_width(self._preview_zoom)
        self._zoom_var.set(f"{int(round(self._preview_zoom * 100))}%")

        # 1) Try rendering directly from the source PDF
        source_pdf = fm.get("source_pdf")
        # Fallback: if frontmatter has no source_pdf, try manifest
        if not source_pdf:
            source_pdf = self._lookup_raw_target(fm.get("id"))
        if _is_pdf_preview_target(source_pdf) and HAS_PYMUPDF:
            pdf_path = self.repo_dir / source_pdf
            if pdf_path.exists():
                try:
                    self._preview_pdf_path = pdf_path
                    doc = pymupdf.open(str(pdf_path))
                    page_indices = _preview_page_indices(doc.page_count)
                    for page_num in page_indices:
                        page = doc[page_num]
                        render_scale = 1.5 * self._preview_zoom
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(render_scale, render_scale))
                        pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        w, h = pil_img.size
                        new_h = int(target_width * (h / w))
                        pil_img = pil_img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.preview_images.append(tk_img)
                        page_frame = ttk.Frame(self.inner_frame)
                        page_frame.pack(fill="x", pady=5, padx=5)
                        ttk.Label(page_frame, text=f"Página {page_num + 1}").pack(anchor="w", pady=(0, 4))
                        page_canvas = tk.Canvas(
                            page_frame,
                            width=pil_img.width,
                            height=pil_img.height,
                            bg=bg,
                            highlightthickness=0,
                        )
                        page_canvas.pack(anchor="w")
                        page_canvas.create_image(0, 0, anchor="nw", image=tk_img)
                        page_canvas.image = tk_img
                        if self._crop_mode.get():
                            self._bind_preview_crop_events(
                                page_canvas,
                                {
                                    "page_num": page_num + 1,
                                    "render_scale": render_scale,
                                    "display_scale": pil_img.width / max(pix.width, 1),
                                },
                            )
                    if doc.page_count > len(page_indices):
                        self._preview_notice_var.set(
                            f"Preview limitado às primeiras {len(page_indices)} páginas de {doc.page_count}."
                        )
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
            self._preview_notice_var.set("Nenhuma visualização disponível.")
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
                
    def _repo_relative(self, path: Path) -> str:
        """Converte um Path absoluto para caminho relativo ao repositório."""
        try:
            return str(path.relative_to(self.repo_dir)).replace("\\", "/")
        except Exception:
            return str(path).replace("\\", "/")

    def _update_manifest_for_approval(self, fm: dict, dest_path: Path, deleted_paths: List[Path]):
        """
        Atualiza o manifest.json após aprovação no Curator Studio.

        Regras:
        - grava o markdown final aprovado em approved_markdown e curated_markdown
        - limpa ponteiros antigos que foram apagados
        - preserva raw_target/source_path
        - adiciona log de aprovação
        """
        entry_id = fm.get("id")
        if not entry_id:
            logger.warning("Approve manifest sync: frontmatter sem id.")
            return

        manifest_path = self.repo_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Approve manifest sync: manifest.json não encontrado em %s", manifest_path)
            return

        try:
            import json
            from datetime import datetime

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = manifest.get("entries", [])
            target = next((e for e in entries if e.get("id") == entry_id), None)
            if not target:
                logger.warning("Approve manifest sync: entry %s não encontrada no manifest.", entry_id)
                return

            approved_rel = self._repo_relative(dest_path)
            approved_source_rel = None
            if self._current_content_path:
                approved_source_rel = self._repo_relative(self._current_content_path)

            deleted_rel_set = set()
            for p in deleted_paths:
                try:
                    deleted_rel_set.add(self._repo_relative(p))
                except Exception:
                    pass

            # Campo novo e explícito para o backlog / viewers
            target["approved_markdown"] = approved_rel
            target["curated_markdown"] = approved_rel
            target["approved_source_markdown"] = approved_source_rel
            target["approved_at"] = datetime.now().isoformat(timespec="seconds")
            target["review_status"] = "approved"

            # Limpa ponteiros antigos se eles foram apagados ou não existem mais
            for key in ("base_markdown", "advanced_markdown", "manual_review"):
                val = target.get(key)
                if not val:
                    continue

                abs_old = (self.repo_dir / val)
                was_deleted = val in deleted_rel_set
                if was_deleted or not abs_old.exists():
                    target[key] = None

            manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
            manifest.setdefault("logs", []).append({
                "entry": entry_id,
                "step": "curator_approve",
                "status": "ok",
                "approved_markdown": approved_rel,
                "approved_source_markdown": approved_source_rel,
                "category": fm.get("category", ""),
            })

            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            _inject_all_image_descriptions_from_manifest(self.repo_dir, manifest)
            logger.info("Approve manifest sync: entry %s atualizada com approved_markdown=%s", entry_id, approved_rel)

        except Exception as e:
            logger.warning("Approve manifest sync falhou para entry %s: %s", entry_id, e)

    def _lookup_raw_target(self, entry_id: str):
        """Look up raw_target from manifest.json for a given entry id."""
        entry = self._lookup_manifest_entry(entry_id)
        if entry:
            return entry.get("raw_target")
        return None

    def _lookup_manifest_entry(self, entry_id: str):
        """Look up the current manifest entry for a given review item id."""
        if not entry_id:
            return None
        manifest_path = self.repo_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for e in manifest.get("entries", []):
                if e.get("id") == entry_id:
                    return e
        except Exception:
            pass
        return None

    # ── Bulk operations ────────────────────────────────────────────────

    def _get_pending_entries(self) -> list:
        """Retorna entries do manifest que têm markdown mas não foram aprovados."""
        manifest_path = self.repo_dir / "manifest.json"
        if not manifest_path.exists():
            return []
        try:
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pending = []
            for e in manifest.get("entries", []):
                if e.get("approved_markdown") or e.get("curated_markdown"):
                    continue  # já aprovado
                md = (e.get("base_markdown") or e.get("advanced_markdown") or "")
                if not md:
                    continue  # sem markdown gerado
                # Verificar se o arquivo de fato existe
                if not (self.repo_dir / md).exists():
                    continue
                pending.append(e)
            return pending
        except Exception as ex:
            logger.warning("Erro ao ler manifest para pendentes: %s", ex)
            return []

    def _restore_orphan_entries(self):
        """Regenera templates de manual-review para entries que têm markdown
        no staging mas não aparecem no Curator Studio."""
        pending = self._get_pending_entries()
        if not pending:
            messagebox.showinfo("Restaurar Pendentes",
                                "Nenhum entry pendente encontrado.\n"
                                "Todos os arquivos já foram aprovados ou não têm markdown.")
            return

        titles = "\n".join(f"  - {e.get('title', '?')}" for e in pending[:15])
        if len(pending) > 15:
            titles += f"\n  ... e mais {len(pending) - 15}"

        if not messagebox.askyesno(
            "Restaurar Pendentes",
            f"{len(pending)} entries têm markdown mas não aparecem\n"
            f"no Curator Studio (template de revisão ausente).\n\n"
            f"{titles}\n\n"
            f"Deseja recriar os templates de revisão?"
        ):
            return

        from src.utils.helpers import write_text
        count = 0
        for e in pending:
            entry_id = e.get("id", "")
            if not entry_id:
                continue
            file_type = e.get("file_type", "pdf")
            base_backend = e.get("base_backend", "")
            if base_backend == "url_fetcher":
                subdir = "web"
            else:
                subdir = "pdfs" if file_type == "pdf" else "images"
            template_path = self.repo_dir / "manual-review" / subdir / f"{entry_id}.md"
            if template_path.exists():
                continue  # já tem template

            md_path = (e.get("base_markdown") or e.get("advanced_markdown") or "")
            adv_md = e.get("advanced_markdown") or ""
            raw_target = e.get("raw_target") or ""
            if subdir == "web":
                content = f"""---
id: {entry_id}
title: {e.get('title', '')}
type: manual_url_review
category: {e.get('category', '')}
source_url: {e.get('source_path', '')}
processing_mode: {e.get('processing_mode', '')}
base_backend: {e.get('base_backend', '')}
base_markdown: {e.get('base_markdown') or ''}
---

# Revisão Manual — {e.get('title', entry_id)}

Template restaurado automaticamente.
Revise o markdown extraído da página web fora do Curator Studio, se necessário.
"""
                write_text(template_path, content)
                count += 1
                continue

            content = f"""---
id: {entry_id}
title: {e.get('title', '')}
type: manual_pdf_review
category: {e.get('category', '')}
source_pdf: {raw_target}
processing_mode: {e.get('processing_mode', '')}
effective_profile: {e.get('effective_profile', '')}
base_backend: {e.get('base_backend', '')}
advanced_backend: {e.get('advanced_backend', '')}
base_markdown: {e.get('base_markdown') or ''}
advanced_markdown: {adv_md}
---

# Revisão Manual — {e.get('title', entry_id)}

Template restaurado automaticamente.
Selecione a fonte (Base ou Avançado) no seletor à direita para revisar.
"""
            write_text(template_path, content)
            count += 1

        self._load_files()
        messagebox.showinfo("Restaurar Pendentes",
                            f"{count} templates de revisão criados.\n"
                            f"Os arquivos agora aparecem na lista à esquerda.")

    def _approve_all_pending(self):
        """Aprova todos os entries pendentes de uma vez, movendo os markdowns
        para o diretório curado correto pela categoria."""
        pending = self._get_pending_entries()
        if not pending:
            messagebox.showinfo("Aprovar Todos",
                                "Nenhum entry pendente encontrado.\n"
                                "Todos os arquivos já foram aprovados ou não têm markdown.")
            return

        titles = "\n".join(f"  - {e.get('title', '?')}" for e in pending[:15])
        if len(pending) > 15:
            titles += f"\n  ... e mais {len(pending) - 15}"

        if not messagebox.askyesno(
            "Aprovar Todos Pendentes",
            f"{len(pending)} entries serão aprovados:\n\n"
            f"{titles}\n\n"
            f"O markdown de cada um será copiado para o diretório\n"
            f"curado (content/curated/, exercises/lists/ ou exams/past-exams/)\n"
            f"e o manifest será atualizado.\n\n"
            f"Continuar?"
        ):
            return

        import json
        from datetime import datetime
        from src.utils.helpers import write_text

        manifest_path = self.repo_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries_map = {e.get("id"): e for e in manifest.get("entries", [])}

        approved_count = 0
        for pe in pending:
            entry_id = pe.get("id", "")
            category = pe.get("category", "")
            md_rel = (pe.get("base_markdown") or pe.get("advanced_markdown") or "")
            if not md_rel or not entry_id:
                continue

            md_src = self.repo_dir / md_rel
            if not md_src.exists():
                continue

            # Determinar destino pela categoria
            if category in ("provas", "fotos-de-prova"):
                dest_dir = self.repo_dir / "exams" / "past-exams"
            elif category in ("listas", "gabaritos"):
                dest_dir = self.repo_dir / "exercises" / "lists"
            else:
                dest_dir = self.repo_dir / "content" / "curated"

            dest_path = dest_dir / f"{entry_id}.md"
            dest_dir.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(md_src, dest_path)
            except Exception as ex:
                logger.warning("Aprovar Todos: falha ao copiar %s → %s: %s", md_src, dest_path, ex)
                continue

            # Atualizar manifest
            target = entries_map.get(entry_id)
            if target:
                approved_rel = self._repo_relative(dest_path)
                target["approved_markdown"] = approved_rel
                target["curated_markdown"] = approved_rel
                target["approved_at"] = datetime.now().isoformat(timespec="seconds")
                target["review_status"] = "approved"
                approved_count += 1

            # Limpar template de manual-review se existir
            for subdir in ("pdfs", "images", "web"):
                template = self.repo_dir / "manual-review" / subdir / f"{entry_id}.md"
                if template.exists():
                    try:
                        template.unlink()
                    except Exception:
                        pass

        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).append({
            "step": "curator_approve_all",
            "status": "ok",
            "count": approved_count,
        })
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        _inject_all_image_descriptions_from_manifest(self.repo_dir, manifest)

        self._load_files()
        messagebox.showinfo("Aprovar Todos",
                            f"{approved_count} entries aprovados e movidos para curadoria.")

    # ── Save / Approve / Reject ───────────────────────────────────────

    def save_current(self):
        if not self._current_content_path:
            messagebox.showwarning("Nada selecionado", "Selecione um arquivo primeiro.")
            return
        if self._current_content_truncated:
            messagebox.showwarning(
                "Arquivo grande",
                "Esta fonte foi carregada parcialmente para evitar travamento. "
                "Abra o arquivo externamente para editar e salvar o conteúdo completo.",
            )
            return

        content = self.editor.get("1.0", tk.END).strip() + "\n"
        content = _normalize_repo_image_references(
            content,
            self._current_content_path,
            self.repo_dir,
        )
        try:
            self._current_content_path.write_text(content, encoding="utf-8")
            entry_id = self._current_frontmatter.get("id") if self._current_frontmatter else None
            if entry_id:
                manifest_entry = self._lookup_manifest_entry(entry_id)
                if manifest_entry and manifest_entry.get("image_curation"):
                    _inject_all_image_descriptions_from_manifest(
                        self.repo_dir,
                        {"entries": [manifest_entry]},
                    )
            self.editor.edit_modified(False)
            self.status_var.set(f"💾 Salvo: {self._current_content_path.name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def _reset_current_view(self, status_msg: str):
        """Limpa a seleção atual da UI após aprovar/reprovar."""
        try:
            list_idx = self.file_paths.index(self.current_md_path)
            self.file_paths.pop(list_idx)
            self.file_list.delete(list_idx)
        except Exception:
            pass

        self.editor.delete("1.0", tk.END)
        self.editor.edit_modified(False)
        self.current_md_path = None
        self._current_content_path = None
        self._current_content_truncated = False
        self._current_frontmatter = {}
        self._available_sources = {}
        self._source_combo["values"] = []
        self._source_var.set("")
        self.info_label.config(text="Nenhum arquivo selecionado")

        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.preview_images.clear()

        self.status_var.set(status_msg)

    def _reject_current(self):
        """
        Reprova o item atual:
        - remove os arquivos gerados
        - remove o PDF/raw do repo
        - tira a entry do manifest
        - devolve o FileEntry para a fila principal
        """
        if not self._current_frontmatter:
            messagebox.showwarning("Nada selecionado", "Selecione um arquivo primeiro.")
            return

        fm = self._current_frontmatter
        entry_id = fm.get("id")
        if not entry_id:
            messagebox.showerror("Erro", "O arquivo selecionado não possui id no frontmatter.")
            return

        msg = (
            "Reprovar este arquivo?\n\n"
            "Isso irá:\n"
            "- remover os arquivos Markdown gerados\n"
            "- remover o PDF/arquivo bruto copiado para o repositório\n"
            "- retirar a entry do manifest\n"
            "- devolver o arquivo para a fila 'A Processar'\n"
        )
        if not messagebox.askyesno("Reprovar arquivo", msg):
            return

        try:
            builder = RepoBuilder(
                root_dir=self.repo_dir,
                course_meta=self._repo_course_meta(),
                entries=[],
                options={},
            )
            entry_data = builder.reject(entry_id, preserve_raw=False)
        except TypeError:
            # Compatibilidade se o engine local ainda estiver com assinatura antiga
            try:
                builder = RepoBuilder(
                    root_dir=self.repo_dir,
                    course_meta=self._repo_course_meta(),
                    entries=[],
                    options={},
                )
                entry_data = builder.reject(entry_id)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao reprovar:\n{e}")
                return
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao reprovar:\n{e}")
            return

        if not entry_data:
            messagebox.showerror("Erro", "Não foi possível localizar a entry no manifest.")
            return

        try:
            queue_entry = FileEntry.from_dict({
                **entry_data,
                "page_range": entry_data.get("page_range") or fm.get("page_range") or "",
                "enabled": True,
            })
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao reconstruir item para a fila:\n{e}")
            return

        parent_app = self.master
        try:
            if hasattr(parent_app, "entries"):
                existing_sources = {getattr(e, "source_path", "") for e in parent_app.entries}
                if queue_entry.source_path not in existing_sources:
                    parent_app.entries.append(queue_entry)
                    if hasattr(parent_app, "refresh_tree"):
                        parent_app.refresh_tree()
                    if hasattr(parent_app, "_save_current_queue"):
                        parent_app._save_current_queue()

            if hasattr(parent_app, "_refresh_backlog"):
                parent_app._refresh_backlog()
            if hasattr(parent_app, "_set_status"):
                parent_app._set_status(f"Item reprovado e devolvido à fila: {queue_entry.title}")
        except Exception as e:
            logger.warning("Rejeição concluída, mas falhou ao sincronizar com a UI principal: %s", e)

        self._reset_current_view(f"⛔ Reprovado → devolvido para a fila: {queue_entry.title}")

    def _approve_current(self):
        if not self._current_content_path or not self._current_frontmatter:
            messagebox.showwarning("Nada selecionado", "Selecione um arquivo primeiro.")
            return
        if self._current_content_truncated:
            messagebox.showwarning(
                "Fonte incompleta",
                "A fonte selecionada foi carregada parcialmente. "
                "Selecione o template de revisão ou edite o arquivo completo fora do Curator Studio antes de aprovar.",
            )
            return

        fm = self._current_frontmatter
        category = fm.get("category", "")

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

        content = self.editor.get("1.0", tk.END).strip() + "\n"
        content = _normalize_repo_image_references(
            content,
            self._current_content_path,
            self.repo_dir,
        )
        try:
            self._current_content_path.write_text(content, encoding="utf-8")
            self.editor.edit_modified(False)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar fonte: {e}")
            return

        try:
            shutil.copy2(self._current_content_path, dest_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar: {e}")
            return

        try:
            promoted_content = dest_path.read_text(encoding="utf-8")
            cleaned_content = _clean_extraction_noise(promoted_content)
            if cleaned_content != promoted_content:
                dest_path.write_text(cleaned_content, encoding="utf-8")
            _inject_executive_summary(dest_path)
        except Exception as e:
            logger.warning("Falha no pós-processamento do markdown aprovado %s: %s", dest_path, e)

        approved_path = self._current_content_path.resolve()
        files_to_delete = []

        for key in ("base_markdown", "advanced_markdown"):
            rel = fm.get(key)
            if rel:
                p = (self.repo_dir / rel).resolve()
                if p.exists() and p != approved_path:
                    files_to_delete.append(p)

        if self.current_md_path and self.current_md_path.resolve() != approved_path:
            if self.current_md_path.exists():
                files_to_delete.append(self.current_md_path.resolve())

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

        self._update_manifest_for_approval(fm, dest_path, files_to_delete)
        self._reset_current_view(
            f"✅ Aprovado → {dest_label}{file_id}.md"
            + (f" | Removidos: {', '.join(deleted)}" if deleted else "")
        )
