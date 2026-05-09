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


def test_backend_context_has_image_description_source_default():
    from unittest.mock import MagicMock
    from src.builder.engine import BackendContext

    entry = MagicMock()
    entry.page_range = ""
    entry.id.return_value = "test-entry"
    report = MagicMock()

    ctx = BackendContext(
        root_dir=__import__("pathlib").Path("/tmp"),
        raw_target=__import__("pathlib").Path("/tmp/doc.pdf"),
        entry=entry,
        report=report,
    )
    assert ctx.image_description_source == "ollama"


def test_backend_context_accepts_datalab_image_description_source():
    from unittest.mock import MagicMock
    from src.builder.engine import BackendContext

    entry = MagicMock()
    entry.page_range = ""
    entry.id.return_value = "test-entry"
    report = MagicMock()

    ctx = BackendContext(
        root_dir=__import__("pathlib").Path("/tmp"),
        raw_target=__import__("pathlib").Path("/tmp/doc.pdf"),
        entry=entry,
        report=report,
        image_description_source="datalab",
    )
    assert ctx.image_description_source == "datalab"


def test_extract_datalab_captions_parses_captions():
    from src.builder.engine import _extract_datalab_captions

    raw_md = (
        "## Página 1\n\n"
        "Texto antes.\n\n"
        "![Diagrama de estados do protocolo TCP](img-001.png)\n\n"
        "Texto depois.\n"
    )
    image_page_map = {"datalab-img-001.png": 1}

    result = _extract_datalab_captions(raw_md, image_page_map)

    assert "pages" in result
    assert "page_1" in result["pages"]
    images = result["pages"]["page_1"]["images"]
    assert "datalab-img-001.png" in images
    entry = images["datalab-img-001.png"]
    assert entry["description"] == "Diagrama de estados do protocolo TCP"
    assert entry["source"] == "datalab"
    assert entry["include"] is True
    assert "described_at" in entry


def test_extract_datalab_captions_empty_caption_stores_empty_description():
    from src.builder.engine import _extract_datalab_captions

    raw_md = "![](img-002.png)\n"
    image_page_map = {"datalab-img-002.png": 2}

    result = _extract_datalab_captions(raw_md, image_page_map)

    images = result["pages"]["page_2"]["images"]
    assert images["datalab-img-002.png"]["description"] == ""
    assert images["datalab-img-002.png"]["source"] == "datalab"


def test_extract_datalab_captions_returns_empty_when_no_images():
    from src.builder.engine import _extract_datalab_captions

    raw_md = "# Título\n\nSó texto, sem imagens.\n"
    result = _extract_datalab_captions(raw_md, {})

    assert result == {}


def test_extract_datalab_captions_falls_back_to_page_1_when_not_in_map():
    from src.builder.engine import _extract_datalab_captions

    raw_md = "![Legenda](unknown.png)\n"
    result = _extract_datalab_captions(raw_md, {})

    assert "page_1" in result["pages"]


def test_merge_image_curations_merges_pages():
    from src.builder.engine import _merge_image_curations

    a = {"pages": {"page_1": {"include_page": True, "images": {"img-a.png": {"description": "A"}}}}}
    b = {"pages": {"page_2": {"include_page": True, "images": {"img-b.png": {"description": "B"}}}}}

    merged = _merge_image_curations([a, b])

    assert "page_1" in merged["pages"]
    assert "page_2" in merged["pages"]
    assert "img-a.png" in merged["pages"]["page_1"]["images"]
    assert "img-b.png" in merged["pages"]["page_2"]["images"]


def test_merge_image_curations_empty_input():
    from src.builder.engine import _merge_image_curations

    assert _merge_image_curations([]) == {"pages": {}}
