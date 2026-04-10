import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Dict, Optional

from src.utils.helpers import DEFAULT_OCR_LANGUAGE

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e1e2e",
        "frame_bg": "#181825",
        "input_bg": "#313244",
        "fg": "#cdd6f4",
        "muted": "#6c7086",
        "accent": "#89b4fa",
        "accent2": "#cba6f7",
        "select_bg": "#45475a",
        "select_fg": "#cdd6f4",
        "button_bg": "#313244",
        "button_active": "#45475a",
        "border": "#45475a",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "header_bg": "#11111b",
        "header_fg": "#89b4fa",
        "tooltip_bg": "#313244",
        "tooltip_fg": "#cdd6f4",
        "treeview_odd": "#1e1e2e",
        "treeview_even": "#24273a",
    },
    "light": {
        "bg": "#eff1f5",
        "frame_bg": "#e6e9ef",
        "input_bg": "#ffffff",
        "fg": "#4c4f69",
        "muted": "#8c8fa1",
        "accent": "#1e66f5",
        "accent2": "#8839ef",
        "select_bg": "#c9cbff",
        "select_fg": "#4c4f69",
        "button_bg": "#dce0e8",
        "button_active": "#bcc0cc",
        "border": "#bcc0cc",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "error": "#d20f39",
        "header_bg": "#dce0e8",
        "header_fg": "#1e66f5",
        "tooltip_bg": "#feffe0",
        "tooltip_fg": "#4c4f69",
        "treeview_odd": "#eff1f5",
        "treeview_even": "#e6e9ef",
    },
    "solarized": {
        "bg": "#002b36",
        "frame_bg": "#073642",
        "input_bg": "#073642",
        "fg": "#839496",
        "muted": "#586e75",
        "accent": "#268bd2",
        "accent2": "#6c71c4",
        "select_bg": "#073642",
        "select_fg": "#93a1a1",
        "button_bg": "#073642",
        "button_active": "#0d4a5a",
        "border": "#586e75",
        "success": "#859900",
        "warning": "#b58900",
        "error": "#dc322f",
        "header_bg": "#00212b",
        "header_fg": "#268bd2",
        "tooltip_bg": "#073642",
        "tooltip_fg": "#93a1a1",
        "treeview_odd": "#002b36",
        "treeview_even": "#073642",
    },
}


CONFIG_PATH = Path.home() / ".gpt_tutor_config.json"

class AppConfig:
    """Manages persistent app configuration via ~/.gpt_tutor_config.json."""

    DEFAULTS: Dict[str, object] = {
        "theme": "dark",
        "default_mode": "auto",
        "default_ocr_language": DEFAULT_OCR_LANGUAGE,
        "default_profile": "auto",
        "default_backend": "auto",
        "image_format": "png",
        "stall_timeout": 300,
        "marker_chunking_mode": "fallback",
        "marker_use_llm": False,
        "marker_llm_model": "qwen3-vl:8b",
        "marker_torch_device": "auto",
        "prevent_sleep_during_build": True,
        "font_size": 10,
        "vision_backend": "ollama",
        "vision_model": "qwen3-vl:235b-cloud",
        "vision_model_quantization": "default",
        "ollama_base_url": "http://localhost:11434",
    }

    def __init__(self):
        self.data: Dict[str, object] = dict(self.DEFAULTS)
        self._load()

    def _load(self) -> None:
        try:
            if CONFIG_PATH.exists():
                stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                self.data.update({k: v for k, v in stored.items() if k in self.DEFAULTS})
                if self.data.get("vision_backend") == "ollama" and self.data.get("vision_model") in {"qwen3-vl", "qwen2.5vl:7b", "qwen3-vl:8b"}:
                    self.data["vision_model"] = "qwen3-vl:235b-cloud"
        except Exception:
            pass

    def save(self) -> None:
        try:
            CONFIG_PATH.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default if default is not None else self.DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self.data[key] = value


class ThemeManager:
    """Applies a colour palette to all ttk/tk widgets via ttk.Style."""

    def __init__(self):
        self._current: str = "dark"

    @property
    def current(self) -> str:
        return self._current

    def palette(self, name: str) -> Dict[str, str]:
        return THEMES.get(name, THEMES["dark"])

    def apply_titlebar_color(self, window: tk.Widget) -> None:
        try:
            import platform
            if platform.system() != "Windows":
                return
            import ctypes
            
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            is_dark = self._current == "dark"
            
            value = ctypes.c_int(2 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
            value_win10 = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value_win10), 4)
        except Exception:
            pass

    def apply(self, root: tk.Tk, name: str) -> None:
        p = self.palette(name)
        self._current = name
        style = ttk.Style(root)

        # Use a clean base theme
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Root background
        root.configure(bg=p["bg"])
        
        # Apply dark mode titlebar on Windows
        def _on_map(event):
            if isinstance(event.widget, (tk.Tk, tk.Toplevel)):
                self.apply_titlebar_color(event.widget)
        root.bind_all("<Map>", _on_map, add="+")


        # Fix Standard Tk Widgets (Text, Listbox, etc.) white backgrounds
        root.option_add("*Text.background", p["input_bg"])
        root.option_add("*Text.foreground", p["fg"])
        root.option_add("*Listbox.background", p["input_bg"])
        root.option_add("*Listbox.foreground", p["fg"])
        root.option_add("*Listbox.selectBackground", p["select_bg"])
        root.option_add("*Listbox.selectForeground", p["select_fg"])

        font_body = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")
        font_small = ("Segoe UI", 9)

        # TFrame / TLabelFrame
        style.configure("TFrame", background=p["bg"])
        style.configure("TLabelframe", background=p["frame_bg"], bordercolor=p["border"], relief="flat")
        style.configure("TLabelframe.Label", background=p["frame_bg"], foreground=p["accent"], font=font_bold)

        # TLabel
        style.configure("TLabel", background=p["bg"], foreground=p["fg"], font=font_body)
        style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"], font=font_small)
        style.configure("Header.TLabel", background=p["header_bg"], foreground=p["header_fg"], font=font_bold)
        style.configure("Accent.TLabel", background=p["bg"], foreground=p["accent"], font=font_bold)

        # TEntry
        style.configure("TEntry", fieldbackground=p["input_bg"], foreground=p["fg"],
                         insertcolor=p["fg"], bordercolor=p["border"], font=font_body)
        style.map("TEntry", bordercolor=[("focus", p["accent"])])

        # TCombobox
        style.configure("TCombobox", fieldbackground=p["input_bg"], foreground=p["fg"],
                         background=p["button_bg"], selectbackground=p["select_bg"],
                         selectforeground=p["select_fg"], bordercolor=p["border"], font=font_body)
        style.map("TCombobox", fieldbackground=[("readonly", p["input_bg"])],
                  selectbackground=[("readonly", p["select_bg"])],
                  foreground=[("readonly", p["fg"])])
        root.option_add("*TCombobox*Listbox.background", p["input_bg"])
        root.option_add("*TCombobox*Listbox.foreground", p["fg"])
        root.option_add("*TCombobox*Listbox.selectBackground", p["select_bg"])
        root.option_add("*TCombobox*Listbox.selectForeground", p["select_fg"])

        # TButton
        style.configure("TButton", background=p["button_bg"], foreground=p["fg"],
                         bordercolor=p["border"], font=font_body, padding=(8, 4))
        style.map("TButton",
                  background=[("active", p["button_active"]), ("pressed", p["accent"])],
                  foreground=[("pressed", p["bg"])])
        style.configure("Accent.TButton", background=p["accent"], foreground=p["bg"],
                         bordercolor=p["accent"], font=font_bold, padding=(10, 5))
        style.map("Accent.TButton",
                  background=[("active", p["accent2"]), ("pressed", p["accent2"])])

        # TCheckbutton
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"], font=font_body)
        style.map("TCheckbutton", background=[("active", p["bg"])],
                  foreground=[("active", p["accent"])])

        # TRadiobutton
        style.configure("TRadiobutton", background=p["bg"], foreground=p["fg"], font=font_body)
        style.map("TRadiobutton", background=[("active", p["bg"])],
                  foreground=[("active", p["accent"])])

        # TNotebook
        style.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
        style.configure("TNotebook.Tab", background=p["button_bg"], foreground=p["muted"],
                         font=font_body, padding=(12, 5))
        style.map("TNotebook.Tab",
                  background=[("selected", p["frame_bg"])],
                  foreground=[("selected", p["accent"])])

        # PanedWindow
        style.configure("TPanedwindow", background=p["bg"], sashthickness=8)
        style.configure("Sash", background=p["border"], sashthickness=8)

        # Treeview
        style.configure("Treeview", background=p["treeview_odd"], foreground=p["fg"],
                         fieldbackground=p["treeview_odd"], bordercolor=p["border"],
                         rowheight=26, font=font_body)
        style.configure("Treeview.Heading", background=p["header_bg"], foreground=p["header_fg"],
                         font=font_bold, relief="flat")
        style.map("Treeview",
                  background=[("selected", p["select_bg"])],
                  foreground=[("selected", p["select_fg"])])
        style.map("Treeview.Heading", background=[("active", p["button_active"])])

        # Scrollbar
        style.configure("TScrollbar", background=p["button_bg"], troughcolor=p["bg"],
                         bordercolor=p["bg"], arrowcolor=p["muted"])

        # Separator
        style.configure("TSeparator", background=p["border"])

        # Progressbar
        style.configure("TProgressbar", background=p["accent"], troughcolor=p["border"])

        # Status bar style
        style.configure("Status.TLabel", background=p["header_bg"], foreground=p["muted"],
                         font=font_small, padding=(6, 3))


def apply_theme_to_toplevel(window: "tk.Toplevel", parent) -> dict:
    """
    Aplica a paleta do app a um Toplevel sem acesso direto ao ThemeManager.
    Retorna a paleta p para uso imediato no __init__.

    Uso padrão em qualquer novo Dialog:
        p = apply_theme_to_toplevel(self, parent)
        self.configure(bg=p["bg"])
    """
    theme_name = "dark"
    if hasattr(parent, "_theme_mgr") and parent._theme_mgr:
        theme_name = parent._theme_mgr.current
    elif hasattr(parent, "_theme_name"):
        theme_name = parent._theme_name
    elif hasattr(parent, "theme_mgr") and parent.theme_mgr:
        theme_name = parent.theme_mgr.current

    p = THEMES.get(theme_name, THEMES["dark"])
    window.configure(bg=p["bg"])

    window.option_add("*Background",              p["bg"])
    window.option_add("*Foreground",              p["fg"])
    window.option_add("*Text.background",         p["input_bg"])
    window.option_add("*Text.foreground",         p["fg"])
    window.option_add("*Text.insertBackground",   p["fg"])
    window.option_add("*Text.selectBackground",   p["select_bg"])
    window.option_add("*Text.selectForeground",   p["select_fg"])
    window.option_add("*Listbox.background",      p["input_bg"])
    window.option_add("*Listbox.foreground",      p["fg"])
    window.option_add("*Listbox.selectBackground",p["select_bg"])
    window.option_add("*Listbox.selectForeground",p["select_fg"])
    window.option_add("*TCombobox*Listbox.background", p["input_bg"])
    window.option_add("*TCombobox*Listbox.foreground", p["fg"])
    window.option_add("*TCombobox*Listbox.selectBackground", p["select_bg"])
    window.option_add("*TCombobox*Listbox.selectForeground", p["select_fg"])
    window.option_add("*Canvas.background",       p["frame_bg"])
    window.option_add("*Canvas.highlightThickness","0")

    return p

