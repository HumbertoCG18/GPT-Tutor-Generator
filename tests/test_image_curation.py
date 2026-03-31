"""Tests for image curation pipeline."""

from __future__ import annotations

import json
import struct
import sys
import zlib
from unittest import mock

_tk_mock = mock.MagicMock()
sys.modules.setdefault("tkinter", _tk_mock)
sys.modules.setdefault("tkinter.filedialog", _tk_mock)
sys.modules.setdefault("tkinter.messagebox", _tk_mock)
sys.modules.setdefault("tkinter.simpledialog", _tk_mock)
sys.modules.setdefault("tkinter.ttk", _tk_mock)

import pytest


def _mock_urlopen_json(payload):
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


class TestOllamaClient:
    def test_check_availability_success_primary(self):
        from src.builder.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "qwen3-vl:latest"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is True
            assert "qwen3-vl:235b-cloud" in msg

    def test_check_availability_accepts_local_8b_as_available(self):
        from src.builder.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "qwen3-vl:8b"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is True
            assert "qwen3-vl:235b-cloud" in msg

    def test_clean_thinking_artifacts(self):
        from src.builder.ollama_client import _clean_thinking_artifacts
        dirty = (
            "Okay, I need to describe this diagram. Let me look at the image.\n"
            "It shows a hierarchy. The labels are in Portuguese.\n"
            "I should structure my answer properly.\n\n"
            "O diagrama apresenta a Hierarquia de Chomsky com 4 níveis."
        )
        cleaned = _clean_thinking_artifacts(dirty)
        assert cleaned.startswith("O diagrama")
        assert "Okay, I need" not in cleaned

    def test_clean_thinking_tags(self):
        from src.builder.ollama_client import _clean_thinking_artifacts
        dirty = "<think>internal reasoning here</think>Descrição limpa da imagem."
        cleaned = _clean_thinking_artifacts(dirty)
        assert cleaned == "Descrição limpa da imagem."

    def test_clean_preserves_clean_text(self):
        from src.builder.ollama_client import _clean_thinking_artifacts
        clean = "O diagrama apresenta a Hierarquia de Chomsky com 4 níveis."
        assert _clean_thinking_artifacts(clean) == clean

    def test_check_availability_ollama_not_running(self):
        from src.builder.ollama_client import OllamaClient
        with mock.patch("src.builder.ollama_client.urlopen", side_effect=ConnectionError("refused")):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is False
            assert "Ollama" in msg

    def test_check_availability_no_vision_model(self):
        from src.builder.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "llama3:8b"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is False
            assert "qwen3-vl:235b-cloud" in msg.lower() or "Vision" in msg

    def test_describe_image_sends_correct_payload(self, tmp_path):
        from src.builder.ollama_client import OllamaClient, IMAGE_TYPE_PROMPTS

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\nfake-image-data")

        mock_response = _mock_urlopen_json({
            "message": {"content": "Uma árvore de prova com 3 níveis."},
            "eval_count": 42,
        })

        with mock.patch("src.builder.ollama_client.urlopen", return_value=mock_response) as mock_urlopen:
            client = OllamaClient()
            result = client.describe_image(img_file, "diagrama", page_context="Exemplo de árvore de prova para 4 ∈ ℕ.")

            assert result == "Uma árvore de prova com 3 níveis."
            request = mock_urlopen.call_args.args[0]
            payload = json.loads(request.data.decode("utf-8"))
            assert payload["model"] == "qwen3-vl:235b-cloud"
            assert payload["options"]["think"] is False
            assert payload["messages"][0]["role"] == "system"
            msg_content = payload["messages"][1]["content"]
            assert IMAGE_TYPE_PROMPTS["diagrama"] in msg_content
            assert payload["messages"][1]["images"]

    def test_describe_image_uses_top_level_response_when_message_is_empty(self, tmp_path):
        from src.builder.ollama_client import OllamaClient

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\nfake-image-data")

        mock_response = _mock_urlopen_json({
            "message": {"content": ""},
            "response": "Resposta vinda do campo top-level.",
        })

        with mock.patch("src.builder.ollama_client.urlopen", return_value=mock_response):
            client = OllamaClient()
            result = client.describe_image(img_file, "genérico", page_context="")

        assert result == "Resposta vinda do campo top-level."


class TestVisionClientFactory:
    def test_defaults_to_ollama_backend(self):
        from src.builder.vision_client import get_vision_client
        from src.builder.ollama_client import OllamaClient

        client = get_vision_client({"vision_model": "qwen3-vl:235b-cloud"})

        assert isinstance(client, OllamaClient)
        assert client.model == "qwen3-vl:235b-cloud"


def test_image_types_include_latex_extraction():
    from src.ui.image_curator import IMAGE_TYPES

    assert "extração-latex" in IMAGE_TYPES


def test_app_config_migrates_legacy_ollama_model(tmp_path):
    from src.ui import theme

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "vision_backend": "ollama",
        "vision_model": "qwen3-vl",
    }), encoding="utf-8")

    original = theme.CONFIG_PATH
    try:
        theme.CONFIG_PATH = config_path
        cfg = theme.AppConfig()
    finally:
        theme.CONFIG_PATH = original

    assert cfg.get("vision_model") == "qwen3-vl:235b-cloud"


def test_app_config_migrates_local_8b_to_cloud_235b(tmp_path):
    from src.ui import theme

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "vision_backend": "ollama",
        "vision_model": "qwen3-vl:8b",
    }), encoding="utf-8")

    original = theme.CONFIG_PATH
    try:
        theme.CONFIG_PATH = config_path
        cfg = theme.AppConfig()
    finally:
        theme.CONFIG_PATH = original

    assert cfg.get("vision_model") == "qwen3-vl:235b-cloud"


def test_app_config_migrates_qwen25_fallback_to_cloud_235b(tmp_path):
    from src.ui import theme

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "vision_backend": "ollama",
        "vision_model": "qwen2.5vl:7b",
    }), encoding="utf-8")

    original = theme.CONFIG_PATH
    try:
        theme.CONFIG_PATH = config_path
        cfg = theme.AppConfig()
    finally:
        theme.CONFIG_PATH = original

    assert cfg.get("vision_model") == "qwen3-vl:235b-cloud"


def test_ollama_client_encode_image_validates_input(tmp_path):
    from src.builder.ollama_client import OllamaClient

    client = OllamaClient()
    missing = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError):
        client._encode_image(missing)


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
        img.write_bytes(_create_minimal_png(200, 200, (128, 128, 128)))
        result = classify_image(img)
        assert result == "decorativa"

    def test_small_filesize_is_decorative(self, tmp_path):
        from src.builder.image_classifier import classify_image
        img = tmp_path / "small.png"
        img.write_bytes(_create_minimal_png(100, 100))
        if img.stat().st_size < 5000:
            assert classify_image(img) == "decorativa"


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
        # unknown doesn't match entry1 prefix, so not included
        assert None not in groups


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
