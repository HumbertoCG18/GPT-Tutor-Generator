import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from typing import List
from PIL import Image, ImageTk
from src.models.core import FileEntry
from src.builder.engine import RepoBuilder

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
        # Fallback: if frontmatter has no source_pdf, try manifest
        if not source_pdf:
            source_pdf = self._lookup_raw_target(fm.get("id"))
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
            logger.info("Approve manifest sync: entry %s atualizada com approved_markdown=%s", entry_id, approved_rel)

        except Exception as e:
            logger.warning("Approve manifest sync falhou para entry %s: %s", entry_id, e)

    def _lookup_raw_target(self, entry_id: str):
        """Look up raw_target from manifest.json for a given entry id."""
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
                    return e.get("raw_target")
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
            subdir = "pdfs" if file_type == "pdf" else "images"
            template_path = self.repo_dir / "manual-review" / subdir / f"{entry_id}.md"
            if template_path.exists():
                continue  # já tem template

            md_path = (e.get("base_markdown") or e.get("advanced_markdown") or "")
            adv_md = e.get("advanced_markdown") or ""
            raw_target = e.get("raw_target") or ""

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
            for subdir in ("pdfs", "images"):
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

        self._load_files()
        messagebox.showinfo("Aprovar Todos",
                            f"{approved_count} entries aprovados e movidos para curadoria.")

    # ── Save / Approve / Reject ───────────────────────────────────────

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
                course_meta={},
                entries=[],
                options={},
            )
            entry_data = builder.reject(entry_id, preserve_raw=False)
        except TypeError:
            # Compatibilidade se o engine local ainda estiver com assinatura antiga
            try:
                builder = RepoBuilder(
                    root_dir=self.repo_dir,
                    course_meta={},
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