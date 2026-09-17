from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.ui.curator_studio import CuratorStudioPanel
from src.ui.image_curator import ImageCuratorPanel


MANUAL_REVIEW_TAB = "Revisão Manual"
IMAGES_TAB = "Imagens"


class CurationWorkspace(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._app_parent = parent
        self._theme_name = (
            parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"
        )
        self._image_panel = None

        self.title("Curadoria")
        self.geometry("1600x900")
        self.minsize(1100, 650)
        self.theme_mgr.apply(self, self._theme_name)

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)

        self._manual_tab = ttk.Frame(self._notebook)
        self._images_tab = ttk.Frame(self._notebook)
        self._notebook.add(self._manual_tab, text=MANUAL_REVIEW_TAB)
        self._notebook.add(self._images_tab, text=IMAGES_TAB)

        self._manual_panel = CuratorStudioPanel(
            self._manual_tab,
            str(self.repo_dir),
            self.theme_mgr,
            app_parent=self._app_parent,
            bind_target=self,
            apply_theme=False,
            title_text="Revisão Manual",
            active_guard=self._is_manual_tab_active,
        )
        self._manual_panel.pack(fill="both", expand=True)

        self._build_images_placeholder()
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_images_placeholder(self) -> None:
        self._images_placeholder = ttk.Frame(self._images_tab)
        self._images_placeholder.pack(fill="both", expand=True)
        ttk.Label(
            self._images_placeholder,
            text="A curadoria de imagens será carregada quando esta aba for aberta.",
        ).pack(anchor="center", expand=True)

    def _on_tab_changed(self, _event=None) -> None:
        selected = self._notebook.select()
        if selected and self._notebook.tab(selected, "text") == IMAGES_TAB:
            self._ensure_image_panel()

    def _is_manual_tab_active(self) -> bool:
        selected = self._notebook.select()
        return bool(selected) and self._notebook.tab(selected, "text") == MANUAL_REVIEW_TAB

    def _is_images_tab_active(self) -> bool:
        selected = self._notebook.select()
        return bool(selected) and self._notebook.tab(selected, "text") == IMAGES_TAB

    def _ensure_image_panel(self):
        if self._image_panel is not None:
            return self._image_panel

        self._images_placeholder.destroy()
        self._image_panel = ImageCuratorPanel(
            self._images_tab,
            str(self.repo_dir),
            self.theme_mgr,
            app_parent=self._app_parent,
            bind_target=self,
            apply_theme=False,
            title_text="Imagens",
            active_guard=self._is_images_tab_active,
        )
        self._image_panel.pack(fill="both", expand=True)
        return self._image_panel
