"""Tests for image curation pipeline."""

from __future__ import annotations

import base64
import json
import struct
import sys
import zlib
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
    def test_check_availability_success_primary(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = json.dumps({
                "models": [{"name": "qwen3-vl:latest"}]
            }).encode()
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            available, msg = client.check_availability()
            assert available is True
            assert "qwen3-vl" in msg

    def test_check_availability_fallback(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen") as mock_urlopen:
            mock_resp = mock.MagicMock()
            mock_resp.read.return_value = json.dumps({
                "models": [{"name": "qwen2.5vl:7b"}]
            }).encode()
            mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = mock.MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            available, msg = client.check_availability()
            assert available is True
            assert "fallback" in msg

    def test_check_availability_ollama_not_running(self):
        from src.builder.ollama_client import OllamaClient
        client = OllamaClient()
        with mock.patch("src.builder.ollama_client.urlopen", side_effect=ConnectionError("refused")):
            available, msg = client.check_availability()
            assert available is False
            assert "Ollama" in msg

    def test_check_availability_no_vision_model(self):
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
            assert "qwen3-vl" in msg.lower() or "Vision" in msg

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

            result = client.describe_image(img_file, "diagrama", page_context="Exemplo de árvore de prova para 4 ∈ ℕ.")

            assert result == "Uma árvore de prova com 3 níveis."
            # Verify the request payload
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            body = json.loads(req.data)
            assert body["model"] == "qwen3-vl"
            assert body["images"][0] == base64.b64encode(img_file.read_bytes()).decode()
            assert "diagrama" in IMAGE_TYPE_PROMPTS
            assert body["prompt"].startswith(IMAGE_TYPE_PROMPTS["diagrama"])


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
