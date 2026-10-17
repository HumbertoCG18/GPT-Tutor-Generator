"""#69: stubs de tkinter nao podem vazar para sys.modules quando o tkinter real existe."""

from __future__ import annotations

import importlib
import sys
from unittest import mock

import pytest

from tests._tkstub import NAMES, garantir_tkinter


def test_tkinter_nao_e_mock_vazado():
    pytest.importorskip("_tkinter")
    garantir_tkinter()
    for name in NAMES:
        assert name in sys.modules and not isinstance(sys.modules[name], mock.Mock), name


def test_sem_tkinter_real_instala_o_stub(monkeypatch):
    for name in NAMES:
        monkeypatch.delitem(sys.modules, name, raising=False)

    def sem_tk(name, *args, **kwargs):
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", sem_tk)
    garantir_tkinter()
    assert all(isinstance(sys.modules[name], mock.MagicMock) for name in NAMES)
