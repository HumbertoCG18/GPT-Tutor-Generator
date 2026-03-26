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
