"""tkinter dos testes (#69): o real quando importa; stub só onde ele falta (CI sem Tk).

O stub antigo entrava em sys.modules mesmo com o tkinter real disponível e vazava para o
resto da sessão. Sem o real não há módulo para contaminar, então o stub pode ficar.
"""

from __future__ import annotations

import importlib
import sys
from unittest import mock

NAMES = ("tkinter", "tkinter.filedialog", "tkinter.messagebox",
         "tkinter.simpledialog", "tkinter.ttk")


def garantir_tkinter() -> None:
    try:
        for name in NAMES:
            importlib.import_module(name)
    except ImportError:
        stub = mock.MagicMock()
        for name in NAMES:
            sys.modules.setdefault(name, stub)
