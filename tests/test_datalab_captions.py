# tests/test_datalab_captions.py
from __future__ import annotations

import sys
from unittest import mock

_tk_mock = mock.MagicMock()
sys.modules.setdefault("tkinter", _tk_mock)
sys.modules.setdefault("tkinter.filedialog", _tk_mock)
sys.modules.setdefault("tkinter.messagebox", _tk_mock)
sys.modules.setdefault("tkinter.simpledialog", _tk_mock)
sys.modules.setdefault("tkinter.ttk", _tk_mock)


def test_appconfig_image_description_source_default():
    from src.ui.theme import AppConfig
    config = AppConfig.__new__(AppConfig)
    config.data = dict(AppConfig.DEFAULTS)
    assert config.data.get("image_description_source") == "ollama"


def test_build_options_includes_image_description_source():
    from src.ui.app import _build_options_from_config

    class FakeConfig:
        def get(self, key, default=None):
            return {"image_description_source": "datalab"}.get(key, default)

    opts = _build_options_from_config("auto", "pt", FakeConfig())
    assert opts["image_description_source"] == "datalab"


def test_build_options_defaults_to_ollama_when_missing():
    from src.ui.app import _build_options_from_config

    class FakeConfig:
        def get(self, key, default=None):
            return default  # key not found

    opts = _build_options_from_config("auto", "pt", FakeConfig())
    assert opts.get("image_description_source") == "ollama"


def test_backend_run_result_accepts_image_curation():
    from src.models.core import BackendRunResult

    r = BackendRunResult(
        name="datalab",
        layer="advanced",
        status="ok",
        image_curation={"pages": {"page_1": {"include_page": True, "images": {}}}},
    )
    assert r.image_curation is not None
    assert "page_1" in r.image_curation["pages"]


def test_backend_run_result_image_curation_defaults_to_none():
    from src.models.core import BackendRunResult

    r = BackendRunResult(name="base", layer="base", status="ok")
    assert r.image_curation is None
