import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

class CuratorStudio(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._theme_name = parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"
        
        self.title("Curator Studio")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        
        self.current_md_path = None
        self.preview_images = []
        
        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_files()
        
    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)
        
        # Toolbar
        toolbar = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        toolbar.pack(fill="x", side="top")
        tk.Label(toolbar, text="🖌 Curator Studio", bg=p["header_bg"], fg=p["header_fg"], font=("Segoe UI", 14, "bold")).pack(side="left")
        
        ttk.Button(toolbar, text="💾 Salvar (Ctrl+S)", command=self.save_current).pack(side="right", padx=5)
        self.bind("<Control-s>", lambda e: self.save_current())
        
        # PanedWindow
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 1. File List
        list_frame = ttk.Frame(self.paned)
        self.paned.add(list_frame, weight=1)
        
        ttk.Label(list_frame, text="Arquivos em manual-review", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.file_list = tk.Listbox(list_frame, bg=p["input_bg"], fg=p["fg"], selectbackground=p["select_bg"],
                                    selectforeground=p["select_fg"], relief="flat", highlightthickness=1,
                                    highlightcolor=p["border"], highlightbackground=p["border"], font=("Segoe UI", 10))
        self.file_list.pack(fill="both", expand=True, side="left")
        self.file_list.bind("<<ListboxSelect>>", self._on_select_file)
        
        list_scroll = ttk.Scrollbar(list_frame, command=self.file_list.yview)
        list_scroll.pack(side="right", fill="y")
        self.file_list.config(yscrollcommand=list_scroll.set)
        
        # 2. Image Preview
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
        
        # 3. Text Editor
        editor_frame = ttk.Frame(self.paned)
        self.paned.add(editor_frame, weight=3)
        
        ttk.Label(editor_frame, text="Editor Markdown (Revisão humana)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.editor = tk.Text(editor_frame, wrap="word", bg=p["input_bg"], fg=p["fg"],
                              insertbackground=p["fg"], selectbackground=p["select_bg"],
                              selectforeground=p["select_fg"], font=("Consolas", 11),
                              relief="flat", highlightthickness=1, highlightcolor=p["border"],
                              highlightbackground=p["border"], undo=True)
        self.editor.pack(side="left", fill="both", expand=True)
        
        ed_scroll = ttk.Scrollbar(editor_frame, command=self.editor.yview)
        ed_scroll.pack(side="right", fill="y")
        self.editor.config(yscrollcommand=ed_scroll.set)
        
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
        
    def _load_files(self):
        self.file_list.delete(0, tk.END)
        self.file_paths = []
        
        manual_dir = self.repo_dir / "manual-review"
        if not manual_dir.exists():
            return
            
        for ext in ("*.md",):
            for p in manual_dir.rglob(ext):
                self.file_paths.append(p)
                self.file_list.insert(tk.END, f"{p.parent.name}/{p.name}")
                
    def _on_select_file(self, event):
        selection = self.file_list.curselection()
        if not selection:
            return
            
        if self.current_md_path and self.editor.edit_modified():
            if not messagebox.askyesno("Não Salvo", "Existem alterações não salvas. Deseja descartar e continuar?"):
                return
                
        idx = selection[0]
        self.current_md_path = self.file_paths[idx]
        
        # Carregar texto
        try:
            content = self.current_md_path.read_text(encoding="utf-8")
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, content)
            self.editor.edit_modified(False)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler arquivo: {e}")
            
        # Tentar achar imagens para preview
        file_id = self.current_md_path.stem
        self._load_previews(file_id)
        
    def _load_previews(self, file_id: str):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.preview_images.clear()
        
        # Look in page-previews
        preview_dir = self.repo_dir / "staging" / "assets" / "page-previews" / file_id
        images_found = []
        if preview_dir.exists():
            images_found = sorted(preview_dir.glob("*.png"))
        else:
            # Maybe it's a direct image review
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                images_found.extend(list((self.repo_dir / "raw" / "images").rglob(f"{file_id}{ext[1:]}")))
                
        if not images_found:
            ttk.Label(self.inner_frame, text="Nenhuma visualização disponível.").pack(pady=20)
            return
            
        target_width = 400
        for img_path in images_found:
            try:
                pil_img = Image.open(img_path)
                w, h = pil_img.size
                ratio = h / w
                new_h = int(target_width * ratio)
                pil_img = pil_img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                self.preview_images.append(tk_img) # Keep ref
                
                lbl = tk.Label(self.inner_frame, image=tk_img, bg=self.theme_mgr.palette(self._theme_name)["frame_bg"])
                lbl.pack(pady=5, padx=5)
            except Exception as e:
                logger.error(f"Erro ao carregar preview {img_path}: {e}")
                
    def save_current(self):
        if not self.current_md_path:
            return
            
        content = self.editor.get("1.0", tk.END).strip() + "\n"
        try:
            self.current_md_path.write_text(content, encoding="utf-8")
            self.editor.edit_modified(False)
            messagebox.showinfo("Salvo", f"Arquivo salvo com sucesso:\n{self.current_md_path.name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
