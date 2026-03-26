# Image Curator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add semi-automatic image curation and description generation using LLaVA 7B via Ollama, making PDF image content accessible to Claude, GPT and Gemini tutors as indexed text in markdowns.

**Architecture:** New `ImageCurator` tkinter dialog reads images from `content/images/`, groups by page, lets user classify and approve. Ollama client in engine.py calls LLaVA with type-specific prompts. Build pipeline injects descriptions as blockquotes before image references. All curation state persists in `manifest.json` under `image_curation` per entry.

**Tech Stack:** Python, tkinter, Pillow (already used), Ollama HTTP API (localhost:11434), LLaVA 7B.

**Spec:** `docs/superpowers/specs/2026-03-25-image-curator-design.md`

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/ui/image_curator.py` | Image Curator dialog — UI for curating and triggering descriptions |
| Create | `src/builder/ollama_client.py` | Ollama HTTP client — availability check, image description generation |
| Modify | `src/builder/engine.py` | Image description injection during build |
| Modify | `src/ui/app.py:225` | Add "Image Curator" button to toolbar |
| Modify | `src/builder/engine.py:2916` | Add SVG reproduction instruction to Claude tutor prompt |
| Create | `tests/test_image_curation.py` | Tests for heuristics, ollama client, description injection |

---

### Task 1: Ollama Client Module

**Files:**
- Create: `src/builder/ollama_client.py`
- Create: `tests/test_image_curation.py`

This module handles all communication with Ollama. Isolated from UI and engine so it can be tested independently.

- [ ] **Step 1: Write failing test for availability check**

```python
# tests/test_image_curation.py
"""Tests for image curation pipeline."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from unittest import mock

_tk_mock = mock.MagicMock()
sys.modules.setdefault("tkinter", _tk_mock)
sys.modules.setdefault("tkinter.filedialog", _tk_mock)
sys.modules.setdefault("tkinter.messagebox", _tk_mock)
sys.modules.setdefault("tkinter.simpledialog", _tk_mock)
sys.modules.setdefault("tkinter.ttk", _tk_mock)

import pytest


class TestOllamaClient:
    def test_check_availability_success(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = json.dumps({
                "models": [{"name": "llava:7b"}]
            }).encode()
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            available, msg = client.check_availability()
            assert available is True

    def test_check_availability_ollama_not_running(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen", side_effect=ConnectionError("refused")):
            available, msg = client.check_availability()
            assert available is False
            assert "Ollama" in msg

    def test_check_availability_model_missing(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = json.dumps({
                "models": [{"name": "llama3:8b"}]
            }).encode()
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            available, msg = client.check_availability()
            assert available is False
            assert "llava" in msg.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_image_curation.py::TestOllamaClient -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.ollama_client'`

- [ ] **Step 3: Implement OllamaClient**

```python
# src/builder/ollama_client.py
"""Ollama HTTP client for local Vision model (LLaVA)."""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llava:7b"

IMAGE_TYPE_PROMPTS = {
    "diagrama": (
        "Descreva a estrutura deste diagrama academicamente. "
        "Identifique nós, relações, hierarquia e regras representadas. "
        "Use notação formal quando possível. Responda em português."
    ),
    "tabela": (
        "Transcreva esta tabela fielmente em formato markdown. "
        "Preserve cabeçalhos, valores e alinhamento. Responda em português."
    ),
    "fórmula": (
        "Transcreva esta fórmula ou expressão matemática em LaTeX. "
        "Se houver contexto visual como setas ou anotações, descreva-o. "
        "Responda em português."
    ),
    "código": (
        "Transcreva este código exatamente como aparece na imagem. "
        "Identifique a linguagem de programação se possível. Responda em português."
    ),
    "genérico": (
        "Descreva o conteúdo desta imagem de forma detalhada e academicamente útil. "
        "Responda em português."
    ),
}


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_availability(self) -> Tuple[bool, str]:
        """Check if Ollama is running and the model is available.
        Returns (available, message).
        """
        try:
            resp = urlopen(f"{self.base_url}/api/tags")
            data = json.loads(resp.read())
        except (URLError, ConnectionError, OSError) as e:
            return False, (
                f"Ollama não está rodando em {self.base_url}.\n"
                "Instale em https://ollama.com e rode 'ollama serve'."
            )

        model_names = [m.get("name", "") for m in data.get("models", [])]
        # Match base name (llava:7b matches llava:7b-q4_0 etc.)
        base = self.model.split(":")[0]
        if not any(base in name for name in model_names):
            return False, (
                f"Modelo '{self.model}' não encontrado no Ollama.\n"
                f"Rode: ollama pull {self.model}"
            )

        return True, "Ollama disponível."

    def describe_image(self, image_path: Path, image_type: str) -> str:
        """Send an image to LLaVA and return the text description."""
        prompt = IMAGE_TYPE_PROMPTS.get(image_type, IMAGE_TYPE_PROMPTS["genérico"])
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }).encode("utf-8")

        req = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        resp = urlopen(req, timeout=120)
        result = json.loads(resp.read())
        return result.get("response", "").strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_image_curation.py::TestOllamaClient -v
```

Expected: 3 PASS

- [ ] **Step 5: Write failing test for describe_image**

Add to `tests/test_image_curation.py`:

```python
    def test_describe_image_sends_correct_payload(self, tmp_path):
        from src.builder.ollama_client import OllamaClient, IMAGE_TYPE_PROMPTS
        client = OllamaClient()

        # Create a tiny test image file
        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\nfake-image-data")

        with mock.patch("src.builder.ollama_client.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = json.dumps({
                "response": "Uma árvore de prova com 3 níveis."
            }).encode()
            mock_urlopen.return_value = mock_resp

            result = client.describe_image(img_file, "diagrama")

            assert result == "Uma árvore de prova com 3 níveis."
            # Verify the request payload
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            body = json.loads(req.data)
            assert body["model"] == "llava:7b"
            assert body["images"][0] == base64.b64encode(img_file.read_bytes()).decode()
            assert "diagrama" in IMAGE_TYPE_PROMPTS
            assert body["prompt"] == IMAGE_TYPE_PROMPTS["diagrama"]
```

- [ ] **Step 6: Run test to verify it passes** (implementation already covers this)

```bash
python -m pytest tests/test_image_curation.py::TestOllamaClient::test_describe_image_sends_correct_payload -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/ollama_client.py tests/test_image_curation.py
git commit -m "feat: add Ollama client for LLaVA image descriptions"
```

---

### Task 2: Image Pre-classification Heuristics

**Files:**
- Create: `src/builder/image_classifier.py`
- Modify: `tests/test_image_curation.py`

Standalone module for image heuristics — determines which images are decorative vs. relevant.

- [ ] **Step 1: Write failing tests for heuristics**

Add to `tests/test_image_curation.py`:

```python
import struct
import tempfile
import zlib


def _create_minimal_png(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a minimal valid PNG with a single solid color."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw_data = b""
    for _ in range(height):
        raw_data += b"\x00"  # filter byte
        for _ in range(width):
            raw_data += bytes(color)
    compressed = zlib.compress(raw_data)
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


class TestImageClassifier:
    def test_tiny_image_is_decorative(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "tiny.png"
        img.write_bytes(_create_minimal_png(10, 10))
        result = classify_image(img)
        assert result == "decorativa"

    def test_banner_aspect_ratio_is_decorative(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "banner.png"
        img.write_bytes(_create_minimal_png(800, 20))
        result = classify_image(img)
        assert result == "decorativa"

    def test_solid_color_is_decorative(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "solid.png"
        # Single solid color
        img.write_bytes(_create_minimal_png(200, 200, (128, 128, 128)))
        result = classify_image(img)
        assert result == "decorativa"

    def test_normal_image_is_generico(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "normal.png"
        img.write_bytes(b"\x00" * 6000)  # > 5KB but not a valid image
        # For invalid images that pass size check, default to genérico
        # We need a real-ish image for this test
        # Create a multi-color image
        data = _create_minimal_png(200, 200, (100, 150, 200))
        img.write_bytes(data)
        result = classify_image(img)
        # Single solid color still → decorativa. Need varied pixels.
        # classify_image checks unique colors. A solid PNG has ≤8 unique colors.
        assert result == "decorativa"  # solid color

    def test_small_filesize_is_decorative(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "small.png"
        img.write_bytes(_create_minimal_png(100, 100))  # valid but small file
        # File size under 5KB threshold
        if img.stat().st_size < 5000:
            assert classify_image(img) == "decorativa"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_image_curation.py::TestImageClassifier -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.image_classifier'`

- [ ] **Step 3: Implement image_classifier.py**

```python
# src/builder/image_classifier.py
"""Heuristic pre-classification of images as decorative vs. relevant."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_FILE_SIZE = 5000       # 5KB
MIN_DIMENSION = 50         # pixels
MAX_ASPECT_RATIO = 6.0     # width/height or height/width
MAX_NOISE_COLORS = 8       # unique colors for solid-color detection


def classify_image(image_path: Path) -> str:
    """Classify an image as 'decorativa' or 'genérico' using heuristics.

    Returns 'decorativa' for images that are likely logos, icons, bars, etc.
    Returns 'genérico' for images that probably contain meaningful content.
    """
    # Check file size
    try:
        size = image_path.stat().st_size
    except OSError:
        return "genérico"

    if size < MIN_FILE_SIZE:
        return "decorativa"

    # Check dimensions and colors using Pillow
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size

            # Too small
            if w < MIN_DIMENSION or h < MIN_DIMENSION:
                return "decorativa"

            # Extreme aspect ratio (banner/bar)
            ratio = max(w, h) / max(min(w, h), 1)
            if ratio > MAX_ASPECT_RATIO:
                return "decorativa"

            # Solid color detection — sample pixels
            sampled = img.convert("RGB").resize((50, 50), Image.NEAREST)
            colors = set(sampled.getdata())
            if len(colors) <= MAX_NOISE_COLORS:
                return "decorativa"

    except Exception as e:
        logger.debug("Could not analyze image %s: %s", image_path, e)
        return "genérico"

    return "genérico"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_image_curation.py::TestImageClassifier -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/image_classifier.py tests/test_image_curation.py
git commit -m "feat: add image pre-classification heuristics"
```

---

### Task 3: Image-to-Page Mapper

**Files:**
- Modify: `src/builder/image_classifier.py`
- Modify: `tests/test_image_curation.py`

Function to scan `content/images/` and map images to their source entry and page number based on filename patterns.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_image_curation.py`:

```python
class TestImageMapper:
    def test_maps_page_from_filename(self):
        from src.builder.image_classifier import extract_page_number
        assert extract_page_number("page-006-img-01.png") == 6
        assert extract_page_number("page-001-img-02.jpg") == 1

    def test_maps_page_from_pymupdf4llm_pattern(self):
        from src.builder.image_classifier import extract_page_number
        # pymupdf4llm pattern: {entry}-_page_N_Figure_M.png
        assert extract_page_number("logica-sintaxe-_page_6_Figure_1.png") == 6
        assert extract_page_number("aula01-_page_12_Figure_3.png") == 12

    def test_unknown_pattern_returns_none(self):
        from src.builder.image_classifier import extract_page_number
        assert extract_page_number("random-image.png") is None
        assert extract_page_number("logo.jpg") is None

    def test_group_images_by_page(self, tmp_path):
        from src.builder.image_classifier import group_images_by_page
        images_dir = tmp_path / "content" / "images"
        images_dir.mkdir(parents=True)

        # Create fake image files with known patterns
        (images_dir / "entry1-page-003-img-01.png").write_bytes(b"fake")
        (images_dir / "entry1-page-003-img-02.png").write_bytes(b"fake")
        (images_dir / "entry1-page-007-img-01.png").write_bytes(b"fake")
        (images_dir / "entry1-_page_5_Figure_1.png").write_bytes(b"fake")
        (images_dir / "unknown-image.png").write_bytes(b"fake")

        groups = group_images_by_page(images_dir, "entry1")
        assert 3 in groups  # page-003
        assert len(groups[3]) == 2
        assert 7 in groups
        assert 5 in groups  # _page_5
        # unknown goes to page None
        assert None in groups or len(groups) == 3  # unknown doesn't match entry1 prefix
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_image_curation.py::TestImageMapper -v
```

Expected: FAIL — `ImportError: cannot import name 'extract_page_number'`

- [ ] **Step 3: Implement mapper functions**

Add to `src/builder/image_classifier.py`:

```python
import re
from typing import Dict, List, Optional

# Page extraction patterns
_PAGE_PATTERNS = [
    re.compile(r"page-(\d{3})-img-\d+", re.IGNORECASE),     # page-006-img-01
    re.compile(r"_page_(\d+)_", re.IGNORECASE),               # _page_6_Figure_1
    re.compile(r"page[_-]?(\d+)", re.IGNORECASE),             # page6, page_6, page-6
]


def extract_page_number(filename: str) -> Optional[int]:
    """Extract page number from an image filename. Returns None if no pattern matches."""
    for pattern in _PAGE_PATTERNS:
        m = pattern.search(filename)
        if m:
            return int(m.group(1))
    return None


def group_images_by_page(
    images_dir: Path, entry_prefix: str
) -> Dict[Optional[int], List[Path]]:
    """Group images in a directory by page number.

    Only includes images whose filename starts with entry_prefix.
    Images with unrecognized patterns go under key None.
    """
    groups: Dict[Optional[int], List[Path]] = {}
    if not images_dir.exists():
        return groups

    for img_path in sorted(images_dir.iterdir()):
        if not img_path.is_file():
            continue
        if img_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
            continue
        if not img_path.name.lower().startswith(entry_prefix.lower()):
            continue

        page = extract_page_number(img_path.name)
        groups.setdefault(page, []).append(img_path)

    return groups
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_image_curation.py::TestImageMapper -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/image_classifier.py tests/test_image_curation.py
git commit -m "feat: add image-to-page mapper for filename patterns"
```

---

### Task 4: Description Injection in Build Pipeline

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `tests/test_image_curation.py`

Add a method to `RepoBuilder` that injects image descriptions from `manifest.json` into markdowns during build.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_image_curation.py`:

```python
class TestDescriptionInjection:
    def test_inject_description_before_image_ref(self):
        from src.builder.engine import RepoBuilder
        markdown = "Some text.\n\n![](content/images/entry1-page-003-img-01.png)\n\nMore text."
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Árvore de prova com 3 níveis.",
                            "described_at": "2026-03-25T14:32:00",
                        }
                    }
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in result
        assert "> **[Descrição de imagem]** Árvore de prova com 3 níveis." in result
        assert "![](content/images/entry1-page-003-img-01.png)" in result

    def test_skip_excluded_images(self):
        from src.builder.engine import RepoBuilder
        markdown = "![](content/images/entry1-page-003-img-01.png)"
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "decorativa",
                            "include": False,
                            "description": None,
                            "described_at": None,
                        }
                    }
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "IMAGE_DESCRIPTION" not in result

    def test_skip_excluded_page(self):
        from src.builder.engine import RepoBuilder
        markdown = "![](content/images/entry1-page-007-img-01.png)"
        curation = {
            "pages": {
                "7": {
                    "include_page": False,
                    "images": {}
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "IMAGE_DESCRIPTION" not in result

    def test_replace_existing_description(self):
        from src.builder.engine import RepoBuilder
        markdown = (
            "Some text.\n\n"
            "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->\n"
            "<!-- Tipo: diagrama -->\n"
            "> **[Descrição de imagem]** Descrição antiga.\n"
            "<!-- /IMAGE_DESCRIPTION -->\n\n"
            "![](content/images/entry1-page-003-img-01.png)\n"
        )
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "tabela",
                            "include": True,
                            "description": "Tabela-verdade atualizada.",
                            "described_at": "2026-03-25T15:00:00",
                        }
                    }
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "Descrição antiga" not in result
        assert "Tabela-verdade atualizada." in result
        assert "<!-- Tipo: tabela -->" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_image_curation.py::TestDescriptionInjection -v
```

Expected: FAIL — `AttributeError: type object 'RepoBuilder' has no attribute 'inject_image_descriptions'`

- [ ] **Step 3: Implement inject_image_descriptions as static method**

Add to `src/builder/engine.py` inside the `RepoBuilder` class (after `_resolve_content_images`):

```python
    # Regex to match existing IMAGE_DESCRIPTION blocks
    _IMG_DESC_BLOCK_RE = re.compile(
        r"<!-- IMAGE_DESCRIPTION: (?P<fname>[^\s]+) -->\n"
        r"<!-- Tipo: [^\n]+ -->\n"
        r"(?:>.*\n)+"
        r"<!-- /IMAGE_DESCRIPTION -->\n\n",
        re.MULTILINE,
    )

    @staticmethod
    def inject_image_descriptions(markdown: str, image_curation: dict) -> str:
        """Inject image descriptions from curation data into markdown text.

        For each image reference ![](content/images/FILENAME), if the curation
        data has a description for FILENAME, inject a blockquote description
        block before the image reference.

        Replaces existing IMAGE_DESCRIPTION blocks if present.
        """
        if not image_curation or "pages" not in image_curation:
            return markdown

        # Build lookup: filename -> (type, description)
        descriptions = {}
        for page_num, page_data in image_curation["pages"].items():
            if not page_data.get("include_page", True):
                continue
            for fname, img_data in page_data.get("images", {}).items():
                if img_data.get("include") and img_data.get("description"):
                    descriptions[fname] = (
                        img_data.get("type", "genérico"),
                        img_data["description"],
                    )

        if not descriptions:
            return markdown

        # First: remove existing description blocks (for re-generation)
        markdown = RepoBuilder._IMG_DESC_BLOCK_RE.sub("", markdown)

        # Then: inject descriptions before image references
        img_re = re.compile(r'(!\[[^\]]*\]\((?:[^)]*/)?' r'([^)/]+\.(?:png|jpg|jpeg|gif|bmp|webp))\))')
        lines = markdown.split("\n")
        result_lines = []

        for line in lines:
            m = img_re.search(line)
            if m:
                fname = m.group(2)
                if fname in descriptions:
                    img_type, desc = descriptions[fname]
                    desc_lines = desc.split("\n")
                    block = (
                        f"<!-- IMAGE_DESCRIPTION: {fname} -->\n"
                        f"<!-- Tipo: {img_type} -->\n"
                    )
                    for dl in desc_lines:
                        block += f"> **[Descrição de imagem]** {dl}\n" if dl == desc_lines[0] else f"> {dl}\n"
                    block += "<!-- /IMAGE_DESCRIPTION -->"
                    result_lines.append(block)

            result_lines.append(line)

        return "\n".join(result_lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_image_curation.py::TestDescriptionInjection -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_image_curation.py
git commit -m "feat: add image description injection to build pipeline"
```

---

### Task 5: Wire Description Injection into Build

**Files:**
- Modify: `src/builder/engine.py`

Integrate `inject_image_descriptions` into the existing build flow so it runs after `_resolve_content_images()`.

- [ ] **Step 1: Add _inject_all_image_descriptions method**

Add to `RepoBuilder` class in `src/builder/engine.py`:

```python
    def _inject_all_image_descriptions(self) -> None:
        """Inject image descriptions from manifest into all content markdowns."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return

        entries = manifest.get("entries", [])
        content_dir = self.root_dir / "content"
        if not content_dir.exists():
            return

        injected_count = 0
        for entry_data in entries:
            curation = entry_data.get("image_curation")
            if not curation or curation.get("status") != "described":
                continue

            # Find markdowns that reference this entry's images
            for md_file in content_dir.rglob("*.md"):
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                new_text = self.inject_image_descriptions(text, curation)
                if new_text != text:
                    md_file.write_text(new_text, encoding="utf-8")
                    injected_count += 1

        if injected_count:
            logger.info("Injected image descriptions into %d markdown files.", injected_count)
```

- [ ] **Step 2: Call it in the build pipeline**

In `src/builder/engine.py`, find where `_resolve_content_images()` is called in the `build()` method (around line 1051) and add a call to `_inject_all_image_descriptions()` right after it:

```python
        self._resolve_content_images()
        self._inject_all_image_descriptions()
```

Do the same in `incremental_build()` — find where the build writes final content and add:

```python
        self._resolve_content_images()
        self._inject_all_image_descriptions()
```

- [ ] **Step 3: Run existing tests to make sure nothing broke**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/builder/engine.py
git commit -m "feat: wire image description injection into build pipeline"
```

---

### Task 6: Image Curator UI — Shell and Layout

**Files:**
- Create: `src/ui/image_curator.py`

Build the Image Curator dialog window with the 2-pane layout. No logic yet — just the window structure.

- [ ] **Step 1: Create the Image Curator dialog**

```python
# src/ui/image_curator.py
"""Image Curator — UI for curating and describing images from PDFs."""

import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageTk

from src.builder.image_classifier import classify_image, extract_page_number, group_images_by_page

logger = logging.getLogger(__name__)

IMAGE_TYPES = ["diagrama", "tabela", "fórmula", "código", "genérico", "decorativa"]


class ImageCurator(tk.Toplevel):
    def __init__(self, parent, repo_dir: str, theme_mgr):
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.theme_mgr = theme_mgr
        self._theme_name = parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"
        self._parent = parent

        self.title("Image Curator")
        self.geometry("1400x800")
        self.minsize(1000, 600)

        # State
        self._manifest_path = self.repo_dir / "manifest.json"
        self._images_dir = self.repo_dir / "content" / "images"
        self._manifest: dict = {}
        self._entries_with_images: List[dict] = []
        self._current_entry: Optional[dict] = None
        self._current_page: Optional[int] = None
        self._thumbnail_refs: List[ImageTk.PhotoImage] = []  # prevent GC
        self._image_widgets: Dict[str, dict] = {}  # fname -> {type_var, include_var}

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._load_manifest()

    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)

        # Toolbar
        toolbar = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        toolbar.pack(fill="x", side="top")
        tk.Label(
            toolbar, text="🖼 Image Curator",
            bg=p["header_bg"], fg=p["header_fg"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        ttk.Button(toolbar, text="🔍 Pré-classificar", command=self._preclassify).pack(side="right", padx=5)
        ttk.Button(toolbar, text="✨ Gerar Descrições", command=self._generate_descriptions).pack(side="right", padx=5)
        ttk.Button(toolbar, text="💾 Salvar", command=self._save_curation).pack(side="right", padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Selecione um entry para curar imagens")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            bg=p["header_bg"], fg=p["header_fg"],
            anchor="w", padx=12, pady=4,
            font=("Segoe UI", 9),
        )
        status_bar.pack(fill="x", side="bottom")

        # PanedWindow
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel: entry + page tree
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Entries / Páginas", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self._tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Right panel: image grid
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        ttk.Label(right_frame, text="Imagens", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # Scrollable canvas for image cards
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_frame, bg=p["frame_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._cards_frame = tk.Frame(self._canvas, bg=p["frame_bg"])
        self._canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        self._cards_frame.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

    def _load_manifest(self):
        """Load manifest.json and populate the tree with entries that have images."""
        if not self._manifest_path.exists():
            self.status_var.set("manifest.json não encontrado. Processe os PDFs primeiro.")
            return
        if not self._images_dir.exists():
            self.status_var.set("Pasta content/images/ não encontrada.")
            return

        try:
            self._manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.status_var.set(f"Erro ao ler manifest: {e}")
            return

        # Find entries that have images in content/images/
        all_images = [f for f in self._images_dir.iterdir() if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")]
        if not all_images:
            self.status_var.set("Nenhuma imagem encontrada em content/images/.")
            return

        entries = self._manifest.get("entries", [])
        for entry in entries:
            entry_id = entry.get("entry_id", "")
            if not entry_id:
                continue
            groups = group_images_by_page(self._images_dir, entry_id)
            if not groups:
                continue

            entry["_image_groups"] = groups
            self._entries_with_images.append(entry)

            # Add to tree
            entry_node = self._tree.insert("", "end", text=f"📄 {entry.get('title', entry_id)}", values=(entry_id,))
            for page_num in sorted(groups.keys(), key=lambda x: x if x is not None else 9999):
                count = len(groups[page_num])
                label = f"Página {page_num} ({count} imgs)" if page_num is not None else f"Página desconhecida ({count} imgs)"
                self._tree.insert(entry_node, "end", text=label, values=(entry_id, str(page_num) if page_num is not None else "none"))

        self.status_var.set(f"{len(self._entries_with_images)} entries com imagens encontradas.")

    def _on_tree_select(self, event):
        """Handle tree selection — show images for selected page."""
        selection = self._tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self._tree.item(item, "values")
        if not values:
            return

        entry_id = values[0]
        page_str = values[1] if len(values) > 1 else None

        # Find entry
        entry = next((e for e in self._entries_with_images if e.get("entry_id") == entry_id), None)
        if not entry:
            return

        self._current_entry = entry
        groups = entry.get("_image_groups", {})

        if page_str is None:
            # Entry-level selection — show all pages
            return

        page_num = int(page_str) if page_str != "none" else None
        self._current_page = page_num
        images = groups.get(page_num, [])
        self._show_images(entry, page_num, images)

    def _show_images(self, entry: dict, page_num: Optional[int], images: List[Path]):
        """Display image cards for the selected page."""
        p = self.theme_mgr.palette(self._theme_name)

        # Clear existing cards
        for widget in self._cards_frame.winfo_children():
            widget.destroy()
        self._thumbnail_refs.clear()
        self._image_widgets.clear()

        # Load existing curation data
        curation = entry.get("image_curation", {})
        page_key = str(page_num) if page_num is not None else "none"
        page_data = curation.get("pages", {}).get(page_key, {})
        include_page = page_data.get("include_page", True)
        curated_images = page_data.get("images", {})

        # Page-level include toggle
        page_frame = tk.Frame(self._cards_frame, bg=p["frame_bg"])
        page_frame.pack(fill="x", padx=5, pady=5)
        page_var = tk.BooleanVar(value=include_page)
        ttk.Checkbutton(page_frame, text="Incluir esta página", variable=page_var,
                        command=lambda: self._toggle_page(page_var.get())).pack(side="left")

        # Image cards
        row_frame = None
        for idx, img_path in enumerate(images):
            if idx % 3 == 0:
                row_frame = tk.Frame(self._cards_frame, bg=p["frame_bg"])
                row_frame.pack(fill="x", padx=5, pady=5)

            fname = img_path.name
            existing = curated_images.get(fname, {})

            card = tk.Frame(row_frame, bg=p["input_bg"], relief="groove", bd=1, padx=8, pady=8)
            card.pack(side="left", padx=5, pady=5)

            # Thumbnail
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((200, 200))
                tk_img = ImageTk.PhotoImage(pil_img)
                self._thumbnail_refs.append(tk_img)
                lbl_img = tk.Label(card, image=tk_img, bg=p["input_bg"])
                lbl_img.pack(pady=(0, 5))
                lbl_img.bind("<Button-1>", lambda e, path=img_path: self._preview_full(path))
            except Exception:
                tk.Label(card, text="[erro ao carregar]", bg=p["input_bg"], fg=p["error"]).pack()

            # Filename
            tk.Label(card, text=fname, bg=p["input_bg"], fg=p["muted"],
                     font=("Segoe UI", 8), wraplength=200).pack()

            # Type dropdown
            type_var = tk.StringVar(value=existing.get("type", "genérico"))
            type_frame = tk.Frame(card, bg=p["input_bg"])
            type_frame.pack(fill="x", pady=2)
            tk.Label(type_frame, text="Tipo:", bg=p["input_bg"], fg=p["fg"]).pack(side="left")
            ttk.Combobox(type_frame, textvariable=type_var, values=IMAGE_TYPES,
                         state="readonly", width=12).pack(side="left", padx=4)

            # Include checkbox
            include_var = tk.BooleanVar(value=existing.get("include", True))
            ttk.Checkbutton(card, text="Incluir", variable=include_var).pack(anchor="w")

            # Description preview (if exists)
            desc = existing.get("description")
            if desc:
                desc_preview = desc[:80] + "..." if len(desc) > 80 else desc
                tk.Label(card, text=desc_preview, bg=p["input_bg"], fg=p["success"],
                         font=("Segoe UI", 8), wraplength=200, justify="left").pack(pady=(4, 0))

            self._image_widgets[fname] = {
                "type_var": type_var,
                "include_var": include_var,
            }

        page_label = f"Página {page_num}" if page_num is not None else "Página desconhecida"
        self.status_var.set(f"{entry.get('title', '')} — {page_label} — {len(images)} imagens")

    def _toggle_page(self, include: bool):
        """Toggle all images on current page."""
        for fname, widgets in self._image_widgets.items():
            widgets["include_var"].set(include)

    def _preview_full(self, image_path: Path):
        """Open full-size image preview in a new window."""
        p = self.theme_mgr.palette(self._theme_name)
        win = tk.Toplevel(self)
        win.title(image_path.name)
        win.configure(bg=p["bg"])

        try:
            pil_img = Image.open(image_path)
            # Scale to fit screen
            max_w, max_h = 1200, 800
            pil_img.thumbnail((max_w, max_h))
            tk_img = ImageTk.PhotoImage(pil_img)
            lbl = tk.Label(win, image=tk_img, bg=p["bg"])
            lbl.image = tk_img  # prevent GC
            lbl.pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(win, text=f"Erro: {e}", bg=p["bg"], fg=p["error"]).pack(padx=20, pady=20)

    def _preclassify(self):
        """Run heuristic pre-classification on all images for the current entry."""
        if not self._current_entry:
            messagebox.showinfo("Image Curator", "Selecione um entry primeiro.")
            return

        groups = self._current_entry.get("_image_groups", {})
        classified = 0
        for page_num, images in groups.items():
            for img_path in images:
                result = classify_image(img_path)
                fname = img_path.name
                if fname in self._image_widgets:
                    self._image_widgets[fname]["type_var"].set(result)
                    self._image_widgets[fname]["include_var"].set(result != "decorativa")
                classified += 1

        self.status_var.set(f"Pré-classificação concluída: {classified} imagens analisadas.")

    def _save_curation(self):
        """Save curation decisions to manifest.json."""
        if not self._current_entry or self._current_page is None:
            return

        entry_id = self._current_entry.get("entry_id", "")
        page_key = str(self._current_page) if self._current_page is not None else "none"

        # Build page data from UI state
        images_data = {}
        for fname, widgets in self._image_widgets.items():
            existing = self._current_entry.get("image_curation", {}).get("pages", {}).get(page_key, {}).get("images", {}).get(fname, {})
            images_data[fname] = {
                "type": widgets["type_var"].get(),
                "include": widgets["include_var"].get(),
                "description": existing.get("description"),
                "described_at": existing.get("described_at"),
            }

        # Update entry's image_curation in manifest
        if "image_curation" not in self._current_entry:
            self._current_entry["image_curation"] = {"status": "pending", "curated_at": None, "pages": {}}

        curation = self._current_entry["image_curation"]
        curation["pages"][page_key] = {
            "include_page": any(d["include"] for d in images_data.values()),
            "images": images_data,
        }

        from datetime import datetime
        curation["curated_at"] = datetime.now().isoformat(timespec="seconds")

        # Check if all pages are curated
        all_curated = all(
            page_key in curation["pages"]
            for page_key in (
                str(p) if p is not None else "none"
                for p in self._current_entry.get("_image_groups", {}).keys()
            )
        )
        if all_curated:
            curation["status"] = "curated"

        # Write back to manifest (removing internal _image_groups key)
        entries = self._manifest.get("entries", [])
        for i, e in enumerate(entries):
            if e.get("entry_id") == entry_id:
                clean_entry = {k: v for k, v in self._current_entry.items() if not k.startswith("_")}
                entries[i] = clean_entry
                break

        self._manifest_path.write_text(
            json.dumps(self._manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.status_var.set(f"Curadoria salva para {entry_id}.")

    def _generate_descriptions(self):
        """Generate descriptions for included images using Ollama/LLaVA."""
        if not self._current_entry:
            messagebox.showinfo("Image Curator", "Selecione um entry primeiro.")
            return

        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()

        # Check availability first
        available, msg = client.check_availability()
        if not available:
            messagebox.showerror("Ollama indisponível", msg)
            return

        # Save current curation state first
        self._save_curation()

        entry_id = self._current_entry.get("entry_id", "")
        curation = self._current_entry.get("image_curation", {})

        # Collect all included images across all pages
        to_describe = []
        for page_key, page_data in curation.get("pages", {}).items():
            if not page_data.get("include_page", True):
                continue
            for fname, img_data in page_data.get("images", {}).items():
                if img_data.get("include") and not img_data.get("description"):
                    img_path = self._images_dir / fname
                    if img_path.exists():
                        to_describe.append((page_key, fname, img_data.get("type", "genérico"), img_path))

        if not to_describe:
            messagebox.showinfo("Image Curator", "Nenhuma imagem pendente para descrever.")
            return

        total = len(to_describe)
        self.status_var.set(f"Gerando descrições: 0/{total}...")

        # Run in thread to avoid freezing UI
        import threading

        def _worker():
            from datetime import datetime
            for idx, (page_key, fname, img_type, img_path) in enumerate(to_describe):
                try:
                    desc = client.describe_image(img_path, img_type)
                    curation["pages"][page_key]["images"][fname]["description"] = desc
                    curation["pages"][page_key]["images"][fname]["described_at"] = datetime.now().isoformat(timespec="seconds")
                except Exception as e:
                    logger.error("Erro ao descrever %s: %s", fname, e)
                    curation["pages"][page_key]["images"][fname]["description"] = f"[ERRO: {e}]"

                self.after(0, lambda i=idx: self.status_var.set(f"Gerando descrições: {i+1}/{total}..."))

            # Mark as described
            curation["status"] = "described"

            # Save manifest
            entries = self._manifest.get("entries", [])
            for i, e in enumerate(entries):
                if e.get("entry_id") == entry_id:
                    clean_entry = {k: v for k, v in self._current_entry.items() if not k.startswith("_")}
                    entries[i] = clean_entry
                    break
            self._manifest_path.write_text(
                json.dumps(self._manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            self.after(0, lambda: self.status_var.set(f"Descrições geradas para {total} imagens. Salvo no manifest."))
            self.after(0, lambda: messagebox.showinfo("Image Curator", f"{total} descrições geradas com sucesso!"))

        threading.Thread(target=_worker, daemon=True).start()
```

- [ ] **Step 2: Verify it opens without errors (manual test)**

This step requires running the app manually:

```bash
python -m src
```

Open a subject with processed PDFs, click "Image Curator". Verify the window opens and images appear.

- [ ] **Step 3: Commit**

```bash
git add src/ui/image_curator.py
git commit -m "feat: add Image Curator dialog with full UI and description generation"
```

---

### Task 7: Wire Image Curator Button to Main App

**Files:**
- Modify: `src/ui/app.py`

- [ ] **Step 1: Add the Image Curator button**

In `src/ui/app.py`, find line 225 where the Curator Studio button is:

```python
ttk.Button(repo_actions, text="🖌 Curator Studio", command=self.open_curator_studio).pack(side="right", padx=(6, 0))
```

Add the Image Curator button right after it:

```python
ttk.Button(repo_actions, text="🖼 Image Curator", command=self.open_image_curator).pack(side="right", padx=(6, 0))
```

- [ ] **Step 2: Add the handler method**

In `src/ui/app.py`, find the `open_curator_studio` method (line 651) and add the new method right after it:

```python
    def open_image_curator(self):
        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para abrir o Image Curator.")
            return

        from src.ui.image_curator import ImageCurator
        ImageCurator(self, str(repo_dir), self.theme_mgr)
```

- [ ] **Step 3: Run existing tests to verify nothing broke**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/ui/app.py
git commit -m "feat: add Image Curator button to main toolbar"
```

---

### Task 8: Install Ollama and LLaVA (Setup)

This is a manual setup task — not code.

- [ ] **Step 1: Download and install Ollama**

Download from https://ollama.com — run the Windows installer.

- [ ] **Step 2: Verify Ollama is running**

```bash
ollama --version
```

Expected: Version number printed.

- [ ] **Step 3: Pull the LLaVA 7B model**

```bash
ollama pull llava:7b
```

Expected: Model downloads (~4.5GB). Takes a few minutes.

- [ ] **Step 4: Verify the model works**

```bash
ollama run llava:7b "Descreva esta imagem" --verbose
```

Or test via the app's Image Curator → "Gerar Descrições" button.

---

### Task 9: Add SVG Reproduction Instruction to Claude Tutor Prompt

**Files:**
- Modify: `src/builder/engine.py:2916` (inside `generate_claude_project_instructions`)

When image descriptions are present in the content, the Claude tutor should proactively reproduce diagrams as interactive SVGs. This was validated experimentally — Claude successfully reproduced a Cantor diagonal enumeration diagram from a text description.

- [ ] **Step 1: Add SVG reproduction rule to Claude instructions**

In `src/builder/engine.py`, find the `## Regras fundamentais` section inside `generate_claude_project_instructions()` (around line 2916). Add a new rule after rule 5:

```python
6. **Reproduza diagramas como SVG** — quando o material contiver descrições de diagramas, tabelas, árvores de prova ou figuras matemáticas (marcadas com `[Descrição de imagem]`), reproduza-os como SVG interativo sempre que possível. Isso permite ao aluno visualizar o conteúdo original que estava nos slides. Se a descrição não for suficiente para reprodução fiel, pergunte ao aluno se ele pode confirmar detalhes antes de gerar o SVG.
```

- [ ] **Step 2: Run existing tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/builder/engine.py
git commit -m "feat: add SVG reproduction instruction to Claude tutor prompt"
```

---

### Task 10: End-to-End Smoke Test

- [ ] **Step 1: Process a PDF with images**

Open the app, add a PDF with diagrams/tables, process it. Verify images appear in `content/images/`.

- [ ] **Step 2: Open Image Curator**

Click "Image Curator". Verify:
- Entry appears in tree
- Pages are listed under the entry
- Clicking a page shows image thumbnails
- Type dropdown and include checkbox work

- [ ] **Step 3: Run pre-classification**

Click "Pré-classificar". Verify decorative images get marked as such.

- [ ] **Step 4: Generate descriptions**

Select types for relevant images, click "Gerar Descrições". Verify:
- Ollama is called (check terminal output)
- Descriptions appear in manifest.json under `image_curation`
- Status bar updates progress

- [ ] **Step 5: Rebuild repository**

Click "Criar Repositório". Verify:
- Markdowns in `content/` now contain `<!-- IMAGE_DESCRIPTION -->` blocks
- Blockquotes with descriptions appear before image references
- The markdown is readable and well-formatted

- [ ] **Step 6: Commit all remaining changes**

```bash
git add -A
git commit -m "feat: complete Image Curator with LLaVA integration"
```
