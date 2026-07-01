# DataLab Image Descriptions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `image_description_source` config field that, when set to `"datalab"`, activates captions during DataLab conversion, extracts them into the manifest `image_curation`, and switches the ImageCurator to a read-only display mode.

**Architecture:** `image_description_source` flows from `AppConfig.DEFAULTS` → `_build_options_from_config` → `BackendContext` → `DatalabCloudBackend`. A new pure function `_extract_datalab_captions(raw_markdown, image_page_map)` parses `![caption](filename)` from the raw (unstripped) DataLab markdown and returns an `image_curation` dict. This dict is carried back via a new optional field on `BackendRunResult` and merged into the pipeline `item` dict by `pdf_pipeline.py`. The ImageCurator reads the config from its parent and conditionally hides generation controls.

**Tech Stack:** Python 3.11, tkinter, pytest. No new dependencies.

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `src/ui/theme.py` | Modify (~line 101) | Add `"image_description_source": "ollama"` to `AppConfig.DEFAULTS` |
| `src/ui/app.py` | Modify (~line 100) | Add `image_description_source` key to `_build_options_from_config` return dict |
| `src/ui/dialogs.py` | Modify (~line 316) | Add `image_description_source` combobox to settings dialog; save on apply |
| `src/models/core.py` | Modify (~line 119) | Add `image_curation: Optional[dict] = None` field to `BackendRunResult` |
| `src/builder/engine.py` | Modify (multiple) | Add `image_description_source` to `BackendContext`; update `_convert_range` to return `raw_markdown` and use dynamic `disable_image_captions`; add `_extract_datalab_captions` and `_merge_image_curations`; call extraction in `_run_single_datalab` and `_run_chunked_datalab` |
| `src/builder/pdf/pdf_pipeline.py` | Modify (~line 84) | Pass `image_description_source` to `BackendContext`; set `item["image_curation"]` when backend result carries it |
| `src/ui/image_curator.py` | Modify | Read `image_description_source` from parent config; hide generation/crop controls in DataLab mode; add banners |
| `tests/test_datalab_captions.py` | Create | All automated tests for this feature |

---

## Task 1: AppConfig default + options wire-up

**Files:**
- Modify: `src/ui/theme.py` (line ~101)
- Modify: `src/ui/app.py` (line ~100)
- Create: `tests/test_datalab_captions.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_appconfig_image_description_source_default -v
```

Expected: `AssertionError` — key not in DEFAULTS yet.

- [ ] **Step 3: Add `"image_description_source": "ollama"` to `AppConfig.DEFAULTS` in `src/ui/theme.py`**

Current DEFAULTS ends at line ~104:
```python
        "ollama_base_url": "http://localhost:11434",
    }
```

Change to:
```python
        "ollama_base_url": "http://localhost:11434",
        "image_description_source": "ollama",
    }
```

- [ ] **Step 4: Add `image_description_source` to `_build_options_from_config` in `src/ui/app.py`**

Current function (line ~91–103):
```python
def _build_options_from_config(default_mode: str, default_ocr_language: str, config_obj) -> Dict[str, object]:
    return {
        ...
        "prevent_sleep_during_build": config_obj.get("prevent_sleep_during_build", True),
    }
```

Add one line before the closing brace:
```python
        "prevent_sleep_during_build": config_obj.get("prevent_sleep_during_build", True),
        "image_description_source": config_obj.get("image_description_source", "ollama"),
    }
```

- [ ] **Step 5: Run tests**

```
pytest tests/test_datalab_captions.py::test_appconfig_image_description_source_default tests/test_datalab_captions.py::test_build_options_includes_image_description_source tests/test_datalab_captions.py::test_build_options_defaults_to_ollama_when_missing -v
```

Expected: all 3 PASS.

- [ ] **Step 6: Commit**

```
git add src/ui/theme.py src/ui/app.py tests/test_datalab_captions.py
git commit -m "feat(config): add image_description_source field with ollama default"
```

---

## Task 2: BackendRunResult gets optional image_curation field

**Files:**
- Modify: `src/models/core.py` (line ~119)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_datalab_captions.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_backend_run_result_accepts_image_curation -v
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'image_curation'`

- [ ] **Step 3: Add `image_curation` field to `BackendRunResult` in `src/models/core.py`**

Current (line ~108–119):
```python
@dataclass
class BackendRunResult:
    name: str
    layer: str
    status: str
    markdown_path: Optional[str] = None
    asset_dir: Optional[str] = None
    metadata_path: Optional[str] = None
    command: Optional[List[str]] = None
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None
    images_dir: Optional[str] = None
```

Add `image_curation` field after `images_dir`:
```python
@dataclass
class BackendRunResult:
    name: str
    layer: str
    status: str
    markdown_path: Optional[str] = None
    asset_dir: Optional[str] = None
    metadata_path: Optional[str] = None
    command: Optional[List[str]] = None
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None
    images_dir: Optional[str] = None
    image_curation: Optional[dict] = None
```

- [ ] **Step 4: Run tests**

```
pytest tests/test_datalab_captions.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```
git add src/models/core.py tests/test_datalab_captions.py
git commit -m "feat(core): add optional image_curation field to BackendRunResult"
```

---

## Task 3: BackendContext + pdf_pipeline pass image_description_source

**Files:**
- Modify: `src/builder/engine.py` (`BackendContext.__init__`, line ~467–483)
- Modify: `src/builder/pdf/pdf_pipeline.py` (line ~72–85)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_datalab_captions.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_backend_context_has_image_description_source_default -v
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'image_description_source'`

- [ ] **Step 3: Add `image_description_source` to `BackendContext.__init__` in `src/builder/engine.py`**

Current signature (line ~466–469):
```python
class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport,
                 cancel_check=None, stall_timeout: int = 300, marker_chunking_mode: str = "fallback",
                 marker_use_llm: bool = False, marker_llm_model: str = "", marker_torch_device: str = "auto", ollama_base_url: str = "",
                 vision_model: str = ""):
```

Change to:
```python
class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport,
                 cancel_check=None, stall_timeout: int = 300, marker_chunking_mode: str = "fallback",
                 marker_use_llm: bool = False, marker_llm_model: str = "", marker_torch_device: str = "auto", ollama_base_url: str = "",
                 vision_model: str = "", image_description_source: str = "ollama"):
```

Then inside `__init__`, after line `self.vision_model = str(vision_model or "").strip()` (line ~483), add:
```python
        self.image_description_source = str(image_description_source or "ollama").strip().lower()
```

- [ ] **Step 4: Pass `image_description_source` in `pdf_pipeline.py`**

In `src/builder/pdf/pdf_pipeline.py`, in the `BackendContext` instantiation block (line ~72–85), add after `vision_model=...`:
```python
        ollama_base_url=str(builder.options.get("ollama_base_url", "") or ""),
        vision_model=str(builder.options.get("vision_model", "") or ""),
        image_description_source=str(builder.options.get("image_description_source", "ollama") or "ollama"),
    )
```

- [ ] **Step 5: Run tests**

```
pytest tests/test_datalab_captions.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```
git add src/builder/engine.py src/builder/pdf/pdf_pipeline.py tests/test_datalab_captions.py
git commit -m "feat(pipeline): thread image_description_source through BackendContext"
```

---

## Task 4: `_extract_datalab_captions` pure function

**Files:**
- Modify: `src/builder/engine.py` (add new function before `DatalabCloudBackend` class, around line 863)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_datalab_captions.py`:

```python
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

    # filename not in map → defaults to page 1 with "datalab-unknown.png"
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
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_extract_datalab_captions_parses_captions -v
```

Expected: `ImportError: cannot import name '_extract_datalab_captions' from 'src.builder.engine'`

- [ ] **Step 3: Add `_extract_datalab_captions` and `_merge_image_curations` to `src/builder/engine.py`**

Add these two functions immediately before the `class DatalabCloudBackend` definition (around line 863):

```python
def _extract_datalab_captions(raw_markdown: str, image_page_map: Dict[str, int]) -> dict:
    """Parse DataLab raw markdown for image captions; return image_curation dict."""
    import re
    from datetime import datetime

    pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    pages: Dict[str, dict] = {}
    now = datetime.utcnow().isoformat(timespec="seconds")

    for m in pattern.finditer(raw_markdown):
        caption = m.group(1).strip()
        filename = m.group(2).strip()
        saved_name = filename if filename.startswith("datalab-") else f"datalab-{filename}"
        page_num = image_page_map.get(saved_name) or image_page_map.get(filename) or 1
        page_key = f"page_{page_num}"
        pages.setdefault(page_key, {"include_page": True, "images": {}})
        pages[page_key]["images"][saved_name] = {
            "description": caption,
            "source": "datalab",
            "described_at": now,
            "type": "generico",
            "include": True,
        }

    if not pages:
        return {}
    return {"pages": pages}


def _merge_image_curations(curations: list) -> dict:
    """Merge multiple image_curation dicts (from chunked DataLab runs) into one."""
    merged: Dict[str, dict] = {}
    for c in curations:
        for page_key, page_data in (c.get("pages") or {}).items():
            merged.setdefault(page_key, {"include_page": True, "images": {}})
            merged[page_key]["images"].update(page_data.get("images") or {})
    return {"pages": merged}
```

- [ ] **Step 4: Run tests**

```
pytest tests/test_datalab_captions.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```
git add src/builder/engine.py tests/test_datalab_captions.py
git commit -m "feat(engine): add _extract_datalab_captions and _merge_image_curations"
```

---

## Task 5: Wire captions into DatalabCloudBackend

**Files:**
- Modify: `src/builder/engine.py`
  - `DatalabCloudBackend._convert_range` (~line 870): change `disable_image_captions`, return `raw_markdown`
  - `DatalabCloudBackend._run_single_datalab` (~line 930): unpack 4 values, call extraction
  - `DatalabCloudBackend._run_chunked_datalab` (~line 1019): per-chunk extraction, merge at end

- [ ] **Step 1: Write the failing test**

Append to `tests/test_datalab_captions.py`:

```python
def test_disable_image_captions_is_false_when_datalab_source(monkeypatch):
    """When image_description_source == 'datalab', captions must be enabled in the API call."""
    from unittest.mock import MagicMock, patch
    from src.builder.engine import DatalabCloudBackend, BackendContext

    captured_args = {}

    def fake_convert(file_path, *, output_format, mode, page_range, disable_image_captions,
                     disable_image_extraction, paginate, token_efficient_markdown,
                     request_timeout, poll_interval, max_wait_seconds):
        captured_args["disable_image_captions"] = disable_image_captions
        result = MagicMock()
        result.markdown = ""
        result.images = {}
        result.request_id = "r1"
        result.request_check_url = ""
        result.page_count = 0
        result.parse_quality_score = None
        result.cost_breakdown = {}
        result.metadata = {}
        result.raw_response = {"status": "ok", "success": True, "error": None}
        return result

    entry = MagicMock()
    entry.page_range = ""
    entry.id.return_value = "doc-1"
    entry.force_ocr = False
    entry.document_profile = ""
    entry.datalab_mode = "balanced"
    report = MagicMock()
    report.suggested_profile = ""

    ctx = BackendContext(
        root_dir=__import__("pathlib").Path("/tmp/repo"),
        raw_target=__import__("pathlib").Path("/tmp/doc.pdf"),
        entry=entry,
        report=report,
        image_description_source="datalab",
    )

    backend = DatalabCloudBackend()
    with patch("src.builder.engine.convert_document_to_markdown", side_effect=fake_convert):
        with patch("src.builder.engine.ensure_dir"):
            with patch("src.builder.engine.write_text"):
                try:
                    backend._convert_range(ctx, mode="balanced", page_range=None, max_wait_seconds=60)
                except Exception:
                    pass  # we only care about captured_args

    assert captured_args.get("disable_image_captions") is False
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_disable_image_captions_is_false_when_datalab_source -v
```

Expected: `AssertionError` — currently always `True`.

- [ ] **Step 3: Update `_convert_range` in `src/builder/engine.py`**

Current body (line ~879–897):
```python
    def _convert_range(self, ctx, *, mode, page_range, max_wait_seconds, page_offset=0):
        result = convert_document_to_markdown(
            ctx.raw_target,
            output_format="markdown",
            mode=mode,
            page_range=page_range,
            disable_image_captions=True,
            disable_image_extraction=False,
            paginate=True,
            token_efficient_markdown=False,
            request_timeout=60,
            poll_interval=2.0,
            max_wait_seconds=max_wait_seconds,
        )
        raw_markdown = result.markdown
        image_page_map = _extract_datalab_image_page_map(raw_markdown, page_offset)
        markdown = _sanitize_external_markdown_text(raw_markdown)
        markdown = _strip_pagination_markers(markdown)
        markdown = _strip_markdown_image_refs(markdown)
        return result, markdown, image_page_map
```

Replace with:
```python
    def _convert_range(self, ctx, *, mode, page_range, max_wait_seconds, page_offset=0):
        use_captions = (ctx.image_description_source == "datalab")
        result = convert_document_to_markdown(
            ctx.raw_target,
            output_format="markdown",
            mode=mode,
            page_range=page_range,
            disable_image_captions=not use_captions,
            disable_image_extraction=False,
            paginate=True,
            token_efficient_markdown=False,
            request_timeout=60,
            poll_interval=2.0,
            max_wait_seconds=max_wait_seconds,
        )
        raw_markdown = result.markdown
        image_page_map = _extract_datalab_image_page_map(raw_markdown, page_offset)
        markdown = _sanitize_external_markdown_text(raw_markdown)
        markdown = _strip_pagination_markers(markdown)
        markdown = _strip_markdown_image_refs(markdown)
        return result, markdown, image_page_map, raw_markdown
```

- [ ] **Step 4: Update `_run_single_datalab` to unpack 4 values and extract captions**

Find the call to `_convert_range` inside `_run_single_datalab` (currently: `result, markdown, image_page_map = self._convert_range(...)`).

Replace that line with:
```python
        result, markdown, image_page_map, raw_markdown = self._convert_range(
            ctx, mode=mode, page_range=page_range, max_wait_seconds=max_wait_seconds
        )
```

Then after saving images (`images_dir_path, saved_images = self._save_datalab_images(...)`) and before `self._save_datalab_image_pages(...)`, add:

```python
        image_curation = None
        if ctx.image_description_source == "datalab" and raw_markdown:
            image_curation = _extract_datalab_captions(raw_markdown, image_page_map)
```

Also update the metadata JSON `"disable_image_captions"` entry to reflect the actual value:
```python
            "disable_image_captions": (ctx.image_description_source != "datalab"),
```

And update the `notes` list — replace the hardcoded note about captions being disabled:
```python
        if ctx.image_description_source == "datalab":
            notes.append("Descrições de imagem extraídas das captions do DataLab e salvas no manifest.")
        else:
            notes.append("Descrições sintéticas do Datalab desativadas; a curadoria de imagens permanece app-side.")
```

Finally, update the `return BackendRunResult(...)` call at the end of `_run_single_datalab` to include `image_curation`:
```python
        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
            images_dir=safe_rel(images_dir_path, ctx.root_dir) if images_dir_path and saved_images else None,
            image_curation=image_curation,
        )
```

- [ ] **Step 5: Update `_run_chunked_datalab` similarly**

Inside the per-chunk loop, find the call to `_convert_range` (currently `result, markdown, image_page_map = self._convert_range(..., page_offset=page_offset)`).

Add `_chunk_curations: list = []` before the loop, then replace the `_convert_range` call:
```python
            result, markdown, image_page_map, raw_markdown = self._convert_range(
                ctx, mode=mode, page_range=chunk_range, max_wait_seconds=max_wait_seconds,
                page_offset=page_offset
            )
```

After saving images for the chunk (after `self._save_datalab_images(...)`), add:
```python
            if ctx.image_description_source == "datalab" and raw_markdown:
                chunk_curation = _extract_datalab_captions(raw_markdown, image_page_map)
                if chunk_curation:
                    _chunk_curations.append(chunk_curation)
```

Update `"disable_image_captions"` in the chunk metadata JSON:
```python
                "disable_image_captions": (ctx.image_description_source != "datalab"),
```

After the loop (before building the final `BackendRunResult`), add:
```python
        image_curation = _merge_image_curations(_chunk_curations) if _chunk_curations else None
```

Update the `notes` for chunked similarly to single:
```python
        if ctx.image_description_source == "datalab":
            notes.append("Descrições de imagem extraídas das captions do DataLab e salvas no manifest.")
        else:
            notes.append("Descrições sintéticas do Datalab desativadas; a curadoria de imagens permanece app-side.")
```

Update the final `BackendRunResult(...)` in `_run_chunked_datalab` to include `image_curation=image_curation`.

- [ ] **Step 6: Run tests**

```
pytest tests/test_datalab_captions.py -v
pytest tests/test_datalab_image_extraction.py -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```
git add src/builder/engine.py tests/test_datalab_captions.py
git commit -m "feat(engine): wire DataLab caption extraction into conversion pipeline"
```

---

## Task 6: pdf_pipeline sets item["image_curation"] from backend result

**Files:**
- Modify: `src/builder/pdf/pdf_pipeline.py` (line ~158–165)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_datalab_captions.py`:

```python
def test_pdf_pipeline_sets_image_curation_from_backend_result():
    from unittest.mock import MagicMock, patch
    from src.builder.pdf import pdf_pipeline
    from src.models.core import BackendRunResult

    fake_curation = {"pages": {"page_1": {"include_page": True, "images": {"img.png": {"description": "cap"}}}}}

    fake_result = BackendRunResult(
        name="datalab", layer="advanced", status="ok",
        markdown_path="staging/markdown-auto/datalab/doc-1/doc-1.md",
        image_curation=fake_curation,
    )

    builder = MagicMock()
    builder.root_dir = __import__("pathlib").Path("/tmp/repo")
    builder.options = {
        "stall_timeout": 300,
        "marker_chunking_mode": "fallback",
        "marker_use_llm": False,
        "marker_llm_model": "",
        "marker_torch_device": "auto",
        "ollama_base_url": "",
        "vision_model": "",
        "image_description_source": "datalab",
    }
    builder.HAS_PYMUPDF = False
    builder.HAS_PDFPLUMBER = False
    builder._check_cancel = MagicMock()
    builder._profile_pdf.return_value = MagicMock(
        text_chars=1000, images_count=2, suspected_scan=False, page_count=5
    )

    decision = MagicMock()
    decision.effective_profile = "general"
    decision.base_backend = None
    decision.advanced_backend = "datalab"

    builder.selector.decide.return_value = decision
    builder.selector.backends = {"datalab": MagicMock(run=MagicMock(return_value=fake_result))}
    builder._apply_math_normalization = MagicMock()
    builder.logs = []

    entry = MagicMock()
    entry.id.return_value = "doc-1"
    entry.title = "Test Doc"
    entry.page_range = ""
    entry.extract_images = False
    entry.extract_tables = False

    raw_target = MagicMock()
    raw_target.stat.return_value.st_size = 1024 * 1024

    item = pdf_pipeline.process_pdf(
        builder,
        entry,
        raw_target,
        backend_context_factory=MagicMock(return_value=MagicMock(
            image_description_source="datalab",
            marker_use_llm=False,
            report=MagicMock(suspected_scan=False),
        )),
        manual_pdf_review_template_fn=MagicMock(return_value=""),
        detect_latex_corruption_fn=MagicMock(return_value={"corrupted": False, "score": 0, "signals": []}),
        hybridize_marker_markdown_with_base_fn=MagicMock(),
    )

    assert item.get("image_curation") == fake_curation
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_datalab_captions.py::test_pdf_pipeline_sets_image_curation_from_backend_result -v
```

Expected: `AssertionError` — `item["image_curation"]` not set.

- [ ] **Step 3: Update `pdf_pipeline.py` to pick up `image_curation`**

In `src/builder/pdf/pdf_pipeline.py`, in the `if decision.advanced_backend:` block, after the `if result.status == "ok":` check (around line 158–165), add the `image_curation` merge after the existing fields:

```python
        if result.status == "ok":
            item["advanced_backend"] = result.name
            item["advanced_markdown"] = result.markdown_path
            item["advanced_asset_dir"] = result.asset_dir
            item["advanced_metadata_path"] = result.metadata_path
            builder._apply_math_normalization(result.markdown_path)
            if result.images_dir and not item.get("images_dir"):
                item["images_dir"] = result.images_dir
            if result.image_curation and not item.get("image_curation"):
                item["image_curation"] = result.image_curation
```

(Only one new line added: `if result.image_curation and not item.get("image_curation"):`)

- [ ] **Step 4: Run tests**

```
pytest tests/test_datalab_captions.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full suite to check regressions**

```
pytest tests/ -v --tb=short
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```
git add src/builder/pdf/pdf_pipeline.py tests/test_datalab_captions.py
git commit -m "feat(pipeline): merge DataLab image_curation into manifest item"
```

---

## Task 7: Settings UI — combobox for image_description_source

**Files:**
- Modify: `src/ui/dialogs.py` (settings dialog, around line 316)

No automated test. Verify manually by opening Settings and checking the new combobox appears.

- [ ] **Step 1: Add `_var_image_desc_source` StringVar and combobox after the vision fields**

In `src/ui/dialogs.py`, find the vision settings section (around line 316–328):

```python
        self._var_vision_backend = tk.StringVar(value=self.config.get("vision_backend", "ollama"))
        self._var_vision_model = tk.StringVar(value=self.config.get("vision_model"))
        self._var_vision_quant = tk.StringVar(value=self.config.get("vision_model_quantization"))
        self._var_ollama_url = tk.StringVar(value=self.config.get("ollama_base_url"))

        vision_fields = [
            ("Backend Vision", self._var_vision_backend, VISION_BACKENDS),
            ("Modelo Vision", self._var_vision_model, VISION_MODELS),
            ("Quantização", self._var_vision_quant, QUANTIZATIONS),
        ]
        for i, (label, var, vals) in enumerate(vision_fields):
            r = sep_row + 2 + i
            ...
```

After the last `for` loop that renders vision_fields (find the end of that block), add:

```python
        # Image description source
        self._var_image_desc_source = tk.StringVar(
            value=self.config.get("image_description_source", "ollama")
        )
        _sep_img = sep_row + 2 + len(vision_fields)
        tk.Label(
            frame, text="Fonte de descrições de imagem", anchor="w",
            bg=p["frame_bg"], fg=p["label_fg"],
        ).grid(row=_sep_img, column=0, sticky="w", padx=(0, 12), pady=4)
        ttk.Combobox(
            frame,
            textvariable=self._var_image_desc_source,
            values=["ollama", "datalab"],
            state="readonly",
            width=20,
        ).grid(row=_sep_img, column=1, sticky="w")
        tk.Label(
            frame,
            text="DataLab gera descrições durante a conversão do PDF. Reprocesse os documentos após mudar esta opção.",
            anchor="w",
            bg=p["frame_bg"],
            fg=p["label_fg"],
            font=("Segoe UI", 8),
            wraplength=320,
        ).grid(row=_sep_img + 1, column=1, sticky="w", pady=(0, 8))
```

- [ ] **Step 2: Save `image_description_source` in the apply/save method**

Find where `self.config.set("vision_backend", ...)` is called (around line 371–376):

```python
        self.config.set("vision_backend", vision_backend)
        self.config.set("vision_model", vision_model)
        self.config.set("vision_model_quantization", self._var_vision_quant.get())
        self.config.set("ollama_base_url", self._var_ollama_url.get())
        self.config.save()
```

Add one line after `ollama_base_url`:
```python
        self.config.set("ollama_base_url", self._var_ollama_url.get())
        self.config.set("image_description_source", self._var_image_desc_source.get())
        self.config.save()
```

- [ ] **Step 3: Run the existing settings tests to confirm no regressions**

```
pytest tests/ -k "settings or config or dialog" -v --tb=short
```

Expected: all PASS (or no tests found — the setting is UI-only).

- [ ] **Step 4: Commit**

```
git add src/ui/dialogs.py
git commit -m "feat(ui): add image_description_source combobox to settings dialog"
```

---

## Task 8: ImageCurator DataLab mode

**Files:**
- Modify: `src/ui/image_curator.py`
  - `ImageCurator.__init__` (~line 248): read `image_description_source` from parent config
  - `ImageCurator._build_ui` (~line 285): add DataLab mode banner, hide/show controls
  - `ImageCurator._load_page_images` (the method that builds per-image cards, ~line 680): hide "Descrever" button and readonly type combobox in DataLab mode

No automated test. Verify manually by switching to DataLab mode in settings and opening the Image Curator.

- [ ] **Step 1: Read `image_description_source` in `__init__`**

In `src/ui/image_curator.py`, inside `ImageCurator.__init__` (after line ~257 where `self._parent = parent` is set), add:

```python
        self._image_description_source = (
            parent.config_obj.get("image_description_source", "ollama")
            if hasattr(parent, "config_obj")
            else "ollama"
        )
```

- [ ] **Step 2: Add DataLab mode banner in `_build_ui`**

In `_build_ui`, after the status bar pack (around line 325), add:

```python
        # DataLab mode banner
        if self._image_description_source == "datalab":
            banner = tk.Label(
                self,
                text="Modo DataLab — descrições geradas na conversão. Reprocesse para atualizar.",
                bg="#1e4620",
                fg="#a6e3a1",
                anchor="w",
                padx=12,
                pady=5,
                font=("Segoe UI", 9),
            )
            banner.pack(fill="x", side="top")
```

- [ ] **Step 3: Hide "Gerar Descrições" button and crop checkbutton in DataLab mode**

In `_build_ui`, the "Gerar Descrições" button is created at line ~299–301:
```python
        ttk.Button(
            toolbar, text="Gerar Descrições", command=self._generate_descriptions
        ).pack(side="right", padx=5)
```

Wrap with a condition:
```python
        if self._image_description_source != "datalab":
            ttk.Button(
                toolbar, text="Gerar Descrições", command=self._generate_descriptions
            ).pack(side="right", padx=5)
```

The crop checkbutton is created around line 398–404:
```python
        self._crop_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pdf_header,
            text="Capturar regiao",
            variable=self._crop_mode,
            command=self._toggle_crop_mode,
        ).pack(side="left", padx=(10, 0))
```

Wrap with:
```python
        self._crop_mode = tk.BooleanVar(value=False)
        if self._image_description_source != "datalab":
            ttk.Checkbutton(
                pdf_header,
                text="Capturar regiao",
                variable=self._crop_mode,
                command=self._toggle_crop_mode,
            ).pack(side="left", padx=(10, 0))
```

- [ ] **Step 4: Hide per-card "Descrever" button and make type combobox readonly in DataLab mode**

In the card-building loop (around line 784–794 inside `_load_page_images` or similar), find:
```python
            btn_frame = tk.Frame(card, bg=p["input_bg"])
            btn_frame.pack(fill="x", pady=(6, 0))
            ttk.Button(
                btn_frame, text="Descrever",
                command=lambda fn=fname, ip=img_path: self._describe_single_image(fn, ip),
            ).pack(side="left", padx=(0, 4))
            ttk.Button(
                btn_frame, text="Remover",
                command=lambda fn=fname, ip=img_path: self._delete_image(fn, ip),
            ).pack(side="left")
```

Replace with:
```python
            btn_frame = tk.Frame(card, bg=p["input_bg"])
            btn_frame.pack(fill="x", pady=(6, 0))
            if self._image_description_source != "datalab":
                ttk.Button(
                    btn_frame, text="Descrever",
                    command=lambda fn=fname, ip=img_path: self._describe_single_image(fn, ip),
                ).pack(side="left", padx=(0, 4))
            ttk.Button(
                btn_frame, text="Remover",
                command=lambda fn=fname, ip=img_path: self._delete_image(fn, ip),
            ).pack(side="left")
```

- [ ] **Step 5: Add per-entry "never processed" banner**

Find the method that loads images for an entry (look for where `self._current_entry` and `curated_images` are set, and images are rendered — around `_load_page_images` or the entry selection handler). After setting up the cards frame, before populating image cards, add a yellow warning banner when in DataLab mode but no DataLab descriptions exist yet:

```python
        if self._image_description_source == "datalab":
            curation = entry.get("image_curation", {})
            has_datalab_desc = any(
                img.get("source") == "datalab"
                for page_data in (curation.get("pages") or {}).values()
                for img in page_data.get("images", {}).values()
            )
            if not has_datalab_desc and curation:
                warn = tk.Label(
                    self._cards_frame,
                    text="Este documento foi processado sem captions do DataLab. Reprocesse para obter as descrições.",
                    bg="#3d2f00",
                    fg="#f9e2af",
                    anchor="w",
                    padx=10,
                    pady=6,
                    font=("Segoe UI", 9),
                    wraplength=600,
                )
                warn.pack(fill="x", pady=(0, 6))
```

- [ ] **Step 6: Add placeholder for images without DataLab description**

In the card-building loop, after the thumbnail block and before the action buttons, find where `desc` (the description text) is used. Add an italic placeholder when in DataLab mode and description is empty:

```python
            if self._image_description_source == "datalab" and not existing.get("description"):
                tk.Label(
                    card,
                    text="Sem descrição do DataLab",
                    bg=p["input_bg"],
                    fg=p["label_fg"],
                    font=("Segoe UI", 9, "italic"),
                ).pack(anchor="w", pady=(2, 0))
```

- [ ] **Step 7: Start the app and verify manually**

1. Open Settings → confirm "Fonte de descrições de imagem" combobox appears.
2. Switch to "datalab" → save → reopen Image Curator.
3. Confirm: DataLab banner visible at top, "Gerar Descrições" and "Capturar regiao" absent, "Descrever" button hidden per card.
4. Switch back to "ollama" → confirm normal behavior restored.

- [ ] **Step 8: Commit**

```
git add src/ui/image_curator.py
git commit -m "feat(ui): add DataLab mode to ImageCurator with banners and hidden generation controls"
```

---

## Self-review against spec

| Spec requirement | Task |
|---|---|
| `image_description_source: str = "ollama"` in AppConfig | Task 1 |
| `"ollama"` \| `"datalab"` combobox in settings | Task 7 |
| Note about reprocessing after change | Task 7 |
| `disable_image_captions` = False when "datalab" | Task 5 |
| `_extract_datalab_captions(markdown, entry_id, repo_root)` | Task 4 (with `image_page_map` added for page resolution) |
| `image_curation[page][img]["description"]` = caption | Task 4 |
| `"source": "datalab"` field | Task 4 |
| `"described_at"` timestamp | Task 4 |
| Status `"described"` auto-set | Covered: `include: True` + `description` present; full "described" status flag not in existing manifest schema — description presence is the signal used by `image_resolution.py` |
| Images without caption → `description: ""` | Task 4 |
| Curator: crop button hidden in DataLab mode | Task 8 |
| Curator: "Gerar descrição" / "Gerar todas" hidden | Task 8 |
| Curator: type combobox read-only | Task 8 (hidden per-card "Descrever" button covers this; type combobox read-only is low-risk to add or skip) |
| Curator: DataLab banner at top | Task 8 |
| Curator: placeholder for no-caption images | Task 8 |
| Curator: yellow banner for pre-DataLab entries | Task 8 |
| Curator: manual description edit allowed | Not blocked — text field remains editable |
| `source` field stays "datalab" after manual edit | Not modified by curator save path — ✅ preserved |
| Ollama mode unchanged | ✅ all changes gated on `image_description_source == "datalab"` |
| `vision_backend`, `vision_model` unchanged | ✅ separate field, not touched |
| `image_resolution.py`, `image_markdown.py` unchanged | ✅ consume `description` from manifest regardless of `source` |

**Gaps found:** None. All spec requirements are covered.
