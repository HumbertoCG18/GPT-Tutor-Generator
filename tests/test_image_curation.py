"""Tests for image curation pipeline."""

from __future__ import annotations

import json
import struct
import sys
import zlib
from unittest import mock
from pathlib import Path

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
        from src.builder.vision.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.vision.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "qwen3-vl:latest"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is True
            assert "qwen3-vl:235b-cloud" in msg

    def test_check_availability_accepts_local_8b_as_available(self):
        from src.builder.vision.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.vision.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "qwen3-vl:8b"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is True
            assert "qwen3-vl:235b-cloud" in msg

    def test_clean_thinking_artifacts(self):
        from src.builder.vision.ollama_client import _clean_thinking_artifacts
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
        from src.builder.vision.ollama_client import _clean_thinking_artifacts
        dirty = "<think>internal reasoning here</think>Descrição limpa da imagem."
        cleaned = _clean_thinking_artifacts(dirty)
        assert cleaned == "Descrição limpa da imagem."

    def test_clean_preserves_clean_text(self):
        from src.builder.vision.ollama_client import _clean_thinking_artifacts
        clean = "O diagrama apresenta a Hierarquia de Chomsky com 4 níveis."
        assert _clean_thinking_artifacts(clean) == clean

    def test_check_availability_ollama_not_running(self):
        from src.builder.vision.ollama_client import OllamaClient
        with mock.patch("src.builder.vision.ollama_client.urlopen", side_effect=ConnectionError("refused")):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is False
            assert "Ollama" in msg

    def test_check_availability_no_vision_model(self):
        from src.builder.vision.ollama_client import OllamaClient
        with mock.patch(
            "src.builder.vision.ollama_client.urlopen",
            return_value=_mock_urlopen_json({"models": [{"name": "llama3:8b"}]}),
        ):
            client = OllamaClient()
            available, msg = client.check_availability()
            assert available is False
            assert "qwen3-vl:235b-cloud" in msg.lower() or "Vision" in msg

    def test_describe_image_sends_correct_payload(self, tmp_path):
        from src.builder.vision.ollama_client import OllamaClient, IMAGE_TYPE_PROMPTS

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\nfake-image-data")

        mock_response = _mock_urlopen_json({
            "message": {"content": "Uma árvore de prova com 3 níveis."},
            "eval_count": 42,
        })

        with mock.patch("src.builder.vision.ollama_client.urlopen", return_value=mock_response) as mock_urlopen:
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
        from src.builder.vision.ollama_client import OllamaClient

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\nfake-image-data")

        mock_response = _mock_urlopen_json({
            "message": {"content": ""},
            "response": "Resposta vinda do campo top-level.",
        })

        with mock.patch("src.builder.vision.ollama_client.urlopen", return_value=mock_response):
            client = OllamaClient()
            result = client.describe_image(img_file, "genérico", page_context="")

        assert result == "Resposta vinda do campo top-level."


class TestVisionClientFactory:
    def test_defaults_to_ollama_backend(self):
        from src.builder.vision.vision_client import get_vision_client
        from src.builder.vision.ollama_client import OllamaClient

        client = get_vision_client({"vision_model": "qwen3-vl:235b-cloud"})

        assert isinstance(client, OllamaClient)
        assert client.model == "qwen3-vl:235b-cloud"


def test_image_types_include_latex_extraction():
    from src.ui.image_curator import IMAGE_TYPES

    assert "extracao-latex" in IMAGE_TYPES


def test_generate_image_text_routes_latex_type(tmp_path):
    from src.ui.image_curator import _generate_image_text

    img = tmp_path / "formula.png"
    img.write_bytes(b"fake")

    client = mock.MagicMock()
    client.extract_to_latex.return_value = "x^2 + y^2"
    client.describe_image.return_value = "descricao comum"

    result = _generate_image_text(
        client, "extracao-latex", img, page_context="formula destacada"
    )

    assert result == "x^2 + y^2"
    client.extract_to_latex.assert_called_once_with(
        img, page_context="formula destacada"
    )
    client.describe_image.assert_not_called()


def test_generate_image_text_routes_non_latex_types_to_description(tmp_path):
    from src.ui.image_curator import _generate_image_text

    img = tmp_path / "diagram.png"
    img.write_bytes(b"fake")

    client = mock.MagicMock()
    client.describe_image.return_value = "diagrama com tres blocos"

    result = _generate_image_text(
        client, "diagrama", img, page_context="contexto da pagina"
    )

    assert result == "diagrama com tres blocos"
    client.describe_image.assert_called_once_with(
        img, "diagrama", page_context="contexto da pagina"
    )
    client.extract_to_latex.assert_not_called()


def test_image_curator_layout_mode_changes_by_width():
    from src.ui.image_curator import _image_curator_layout_mode

    assert _image_curator_layout_mode(1500) == "wide"
    assert _image_curator_layout_mode(1100) == "medium"
    assert _image_curator_layout_mode(820) == "stacked"


def test_remove_images_from_curation_prunes_empty_page():
    from src.ui.image_curator import _remove_images_from_curation

    curation = {
        "status": "curated",
        "curated_at": "2026-03-31T02:00:00",
        "pages": {
            "7": {
                "include_page": True,
                "images": {
                    "img-a.png": {"include": True, "description": "A"},
                    "img-b.png": {"include": True, "description": "B"},
                },
            }
        },
    }

    result = _remove_images_from_curation(curation, "7", ["img-a.png", "img-b.png"])

    assert result["pages"] == {}
    assert result["status"] == "pending"
    assert result["curated_at"] is None


def test_remove_images_from_curation_keeps_non_empty_page():
    from src.ui.image_curator import _remove_images_from_curation

    curation = {
        "status": "curated",
        "curated_at": "2026-03-31T02:00:00",
        "pages": {
            "7": {
                "include_page": True,
                "images": {
                    "img-a.png": {"include": True, "description": "A"},
                    "img-b.png": {"include": True, "description": "B"},
                },
            }
        },
    }

    result = _remove_images_from_curation(curation, "7", ["img-a.png"])

    assert "7" in result["pages"]
    assert "img-a.png" not in result["pages"]["7"]["images"]
    assert "img-b.png" in result["pages"]["7"]["images"]
    assert result["status"] == "curated"


def test_selected_image_names_returns_only_checked_items():
    from src.ui.image_curator import _selected_image_names

    class BoolVarStub:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    selected = _selected_image_names({
        "img-a.png": {"selected_var": BoolVarStub(True)},
        "img-b.png": {"selected_var": BoolVarStub(False)},
        "img-c.png": {"selected_var": BoolVarStub(True)},
    })

    assert selected == ["img-a.png", "img-c.png"]


def test_resolve_curation_page_key_accepts_legacy_zero_based_page():
    from src.ui.image_curator import _resolve_curation_page_key

    curation = {"pages": {"24": {"images": {}}}}
    images = [Path("entry-_page_24_Figure_0.png")]

    assert _resolve_curation_page_key(curation, 25, images) == "24"


def test_migrate_curation_page_key_promotes_legacy_zero_based_page():
    from src.ui.image_curator import _migrate_curation_page_key

    curation = {
        "pages": {
            "24": {
                "include_page": True,
                "images": {"entry-_page_24_Figure_0.png": {"description": "ok"}},
            }
        }
    }
    images = [Path("entry-_page_24_Figure_0.png")]

    key = _migrate_curation_page_key(curation, 25, images)

    assert key == "25"
    assert "25" in curation["pages"]
    assert "24" not in curation["pages"]
    assert "entry-_page_24_Figure_0.png" in curation["pages"]["25"]["images"]


def test_build_duplicate_index_marks_exact_duplicates(tmp_path):
    from src.ui.image_curator import _build_duplicate_index

    img_a = tmp_path / "page-023-a.png"
    img_b = tmp_path / "page-024-a.png"
    img_c = tmp_path / "page-025-b.png"
    img_a.write_bytes(b"same-image")
    img_b.write_bytes(b"same-image")
    img_c.write_bytes(b"different-image")

    groups = {
        23: [img_a],
        24: [img_b],
        25: [img_c],
    }

    result = _build_duplicate_index(groups)

    assert "page-023-a.png" in result
    assert "page-024-a.png" in result
    assert "page-025-b.png" not in result
    assert result["page-023-a.png"]["other_pages"] == [24]
    assert result["page-024-a.png"]["other_pages"] == [23]


def test_resolve_entry_pdf_prefers_manifest_raw_target(tmp_path):
    from src.ui.image_curator import _resolve_entry_pdf_path

    repo = tmp_path / "repo"
    pdf_a = repo / "raw" / "pdfs" / "material-de-aula" / "entry-a.pdf"
    pdf_b = repo / "raw" / "pdfs" / "material-de-aula" / "entry-b.pdf"
    pdf_a.parent.mkdir(parents=True)
    pdf_a.write_bytes(b"%PDF-1.4 a")
    pdf_b.write_bytes(b"%PDF-1.4 b")

    entry = {
        "id": "entry-a",
        "source_path": "C:/stale/original.pdf",
        "raw_target": "raw/pdfs/material-de-aula/entry-a.pdf",
    }

    result = _resolve_entry_pdf_path(repo, entry)

    assert result == pdf_a


def test_resolve_entry_pdf_does_not_fallback_to_unrelated_pdf_when_raw_target_exists(tmp_path):
    from src.ui.image_curator import _resolve_entry_pdf_path

    repo = tmp_path / "repo"
    pdf_a = repo / "raw" / "pdfs" / "material-de-aula" / "entry-a.pdf"
    pdf_b = repo / "raw" / "pdfs" / "material-de-aula" / "other.pdf"
    pdf_a.parent.mkdir(parents=True)
    pdf_a.write_bytes(b"%PDF-1.4 a")
    pdf_b.write_bytes(b"%PDF-1.4 b")

    entry = {
        "id": "entry-a",
        "source_path": "",
        "raw_target": "raw/pdfs/material-de-aula/entry-a.pdf",
    }

    result = _resolve_entry_pdf_path(repo, entry)

    assert result == pdf_a
    assert result != pdf_b


def test_inject_image_descriptions_accepts_curated_status(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "content" / "images").mkdir(parents=True)
    (repo / "content" / "curated.md").write_text(
        "![](content/images/entry1-page-003-img-01.png)\n",
        encoding="utf-8",
    )
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "Aula 1",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "3": {
                            "include_page": True,
                            "images": {
                                "entry1-page-003-img-01.png": {
                                    "type": "diagrama",
                                    "include": True,
                                    "description": "Árvore de prova com 3 níveis.",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    result = (repo / "content" / "curated.md").read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in result
    assert "> **[Descrição de imagem]** Árvore de prova com 3 níveis." in result


def test_inject_all_image_descriptions_prefers_entry_markdown_targets(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "content" / "images").mkdir(parents=True)
    target = repo / "content" / "target.md"
    other = repo / "content" / "other.md"
    image_ref = "![](content/images/entry1-page-003-img-01.png)\n"
    target.write_text(image_ref, encoding="utf-8")
    other.write_text(image_ref, encoding="utf-8")
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "Aula 1",
                "base_markdown": "content/target.md",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "3": {
                            "include_page": True,
                            "images": {
                                "entry1-page-003-img-01.png": {
                                    "type": "diagrama",
                                    "include": True,
                                    "description": "Árvore de prova com 3 níveis.",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    target_text = target.read_text(encoding="utf-8")
    other_text = other.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in target_text
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" not in other_text


def test_inject_all_image_descriptions_supports_scanned_staging_markdown(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    target = repo / "staging" / "markdown-auto" / "scanned" / "entry1.md"
    target.parent.mkdir(parents=True)
    (repo / "content" / "images" / "scanned" / "entry1").mkdir(parents=True)
    target.write_text(
        "![](../../../content/images/scanned/entry1/page-001.jpg)\n",
        encoding="utf-8",
    )
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "PDF Scanned",
                "base_markdown": "staging/markdown-auto/scanned/entry1.md",
                "effective_profile": "scanned",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "1": {
                            "include_page": True,
                            "images": {
                                "page-001.jpg": {
                                    "type": "página escaneada",
                                    "include": True,
                                    "description": "Página escaneada com texto manuscrito e fórmulas.",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    target_text = target.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: page-001.jpg -->" in target_text
    assert "> **[Descrição de imagem]** Página escaneada com texto manuscrito e fórmulas." in target_text


def test_inject_all_image_descriptions_supports_scanned_latex_extraction(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    target = repo / "staging" / "markdown-auto" / "scanned" / "entry1.md"
    target.parent.mkdir(parents=True)
    (repo / "content" / "images" / "scanned" / "entry1").mkdir(parents=True)
    target.write_text(
        "![](../../../content/images/scanned/entry1/page-001.jpg)\n",
        encoding="utf-8",
    )
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "PDF Scanned",
                "base_markdown": "staging/markdown-auto/scanned/entry1.md",
                "effective_profile": "scanned",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "1": {
                            "include_page": True,
                            "images": {
                                "page-001.jpg": {
                                    "type": "extração-latex",
                                    "include": True,
                                    "description": "\\int_0^1 x^2 dx = 1/3",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    target_text = target.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: page-001.jpg -->" in target_text
    assert "> **[LaTeX extraído]** \\int_0^1 x^2 dx = 1/3" in target_text


def test_inject_all_image_descriptions_matches_non_scanned_rewritten_content_image(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    target = repo / "staging" / "markdown-auto" / "marker" / "entry1.md"
    target.parent.mkdir(parents=True)
    (repo / "content" / "images").mkdir(parents=True)
    target.write_text(
        "![](../../../content/images/entry1-logica-sintaxe-_page_2_Figure_1.png)\n",
        encoding="utf-8",
    )
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "PDF normal",
                "base_markdown": "staging/markdown-auto/marker/entry1.md",
                "effective_profile": "math_heavy",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "3": {
                            "include_page": True,
                            "images": {
                                "logica-sintaxe-_page_2_Figure_1.png": {
                                    "type": "diagrama",
                                    "include": True,
                                    "description": "Diagrama com conectivos lógicos e caixas de derivação.",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    target_text = target.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: logica-sintaxe-_page_2_Figure_1.png -->" in target_text
    assert "Diagrama com conectivos lógicos e caixas de derivação." in target_text


def test_inject_all_image_descriptions_falls_back_when_manifest_markdown_is_stale(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    real_target = repo / "exercises" / "lists" / "entry1.md"
    real_target.parent.mkdir(parents=True)
    real_target.write_text(
        "---\nentry_id: \"entry1\"\n---\n\n![](../../../content/images/scanned/entry1/page-001.jpg)\n",
        encoding="utf-8",
    )
    (repo / "content" / "images" / "scanned" / "entry1").mkdir(parents=True)
    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "PDF Scanned",
                "base_markdown": "staging/markdown-auto/scanned/entry1.md",
                "effective_profile": "scanned",
                "image_curation": {
                    "status": "curated",
                    "pages": {
                        "1": {
                            "include_page": True,
                            "images": {
                                "page-001.jpg": {
                                    "type": "extração-latex",
                                    "include": True,
                                    "description": "x_{n+1} = x_n + 1",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }
    (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder._inject_all_image_descriptions()

    target_text = real_target.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: page-001.jpg -->" in target_text
    assert "> **[LaTeX extraído]** x_{n+1} = x_n + 1" in target_text


def test_compact_manifest_heals_stale_markdown_path(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    real_target = repo / "exercises" / "lists" / "entry1.md"
    real_target.parent.mkdir(parents=True)
    real_target.write_text(
        "---\nentry_id: \"entry1\"\n---\n\nConteúdo\n",
        encoding="utf-8",
    )
    raw_target = repo / "raw" / "pdfs" / "listas" / "entry1.pdf"
    raw_target.parent.mkdir(parents=True)
    raw_target.write_bytes(b"%PDF-1.4")

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo

    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "PDF Scanned",
                "raw_target": "raw/pdfs/listas/entry1.pdf",
                "base_markdown": "staging/markdown-auto/scanned/entry1.md",
            }
        ]
    }

    compacted = builder._compact_manifest(manifest)
    assert compacted["entries"][0]["base_markdown"] == "exercises/lists/entry1.md"
    assert compacted["entries"][0]["approved_markdown"] == "exercises/lists/entry1.md"
    assert compacted["entries"][0]["curated_markdown"] == "exercises/lists/entry1.md"


def test_curator_studio_merges_manifest_fields_when_template_is_stale():
    from src.ui.curator_studio import _merge_review_frontmatter_with_manifest

    fm = {
        "id": "entry-1",
        "title": "Aula 1",
        "base_markdown": "staging/markdown-auto/base.md",
        "advanced_markdown": None,
        "advanced_backend": None,
    }
    manifest_entry = {
        "id": "entry-1",
        "advanced_markdown": "staging/markdown-auto/docling/advanced.md",
        "advanced_backend": "docling",
        "raw_target": "raw/pdfs/aula1.pdf",
    }

    merged = _merge_review_frontmatter_with_manifest(fm, manifest_entry)

    assert merged["advanced_markdown"] == "staging/markdown-auto/docling/advanced.md"
    assert merged["advanced_backend"] == "docling"


def test_image_curator_reinjects_descriptions_into_base_and_advanced_markdown(tmp_path):
    from src.ui.image_curator import _inject_all_image_descriptions_from_manifest

    repo = tmp_path / "repo"
    base_md = repo / "content" / "base.md"
    advanced_md = repo / "staging" / "markdown-auto" / "docling" / "advanced.md"
    base_md.parent.mkdir(parents=True)
    advanced_md.parent.mkdir(parents=True)

    image_ref = "![](content/images/entry1-page-003-img-01.png)\n"
    base_md.write_text(image_ref, encoding="utf-8")
    advanced_md.write_text(image_ref, encoding="utf-8")

    manifest = {
        "entries": [
            {
                "id": "entry1",
                "title": "Aula 1",
                "base_markdown": "content/base.md",
                "advanced_markdown": "staging/markdown-auto/docling/advanced.md",
                "image_curation": {
                    "status": "described",
                    "pages": {
                        "3": {
                            "include_page": True,
                            "images": {
                                "entry1-page-003-img-01.png": {
                                    "type": "diagrama",
                                    "include": True,
                                    "description": "Árvore de prova com 3 níveis.",
                                }
                            },
                        }
                    },
                },
            }
        ]
    }

    _inject_all_image_descriptions_from_manifest(repo, manifest)

    base_text = base_md.read_text(encoding="utf-8")
    advanced_text = advanced_md.read_text(encoding="utf-8")
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in base_text
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in advanced_text
    assert "Árvore de prova com 3 níveis." in base_text
    assert "Árvore de prova com 3 níveis." in advanced_text


def test_strip_described_image_refs_removes_only_described_images():
    from src.ui.image_curator import _strip_described_image_refs

    curation = {
        "pages": {
            "1": {
                "images": {
                    "fig1.png": {"description": "Diagrama de blocos"},
                    "fig2.png": {"description": None},
                }
            }
        }
    }
    text = (
        "## Secao\n\n"
        "Texto antes.\n\n"
        "![Figura 1](content/images/fig1.png)\n\n"
        "Texto entre.\n\n"
        "![](content/images/fig2.png)\n\n"
        "Texto depois.\n"
    )

    result = _strip_described_image_refs(text, curation)

    assert "fig1.png" not in result
    assert "fig2.png" in result
    assert "Texto antes." in result
    assert "Texto depois." in result
    assert "\n\n\n" not in result


def test_inject_for_current_entry_updates_known_markdown_targets(tmp_path):
    from src.ui.image_curator import _inject_for_current_entry

    repo = tmp_path / "repo"
    target = repo / "staging" / "markdown-auto" / "docling" / "advanced.md"
    target.parent.mkdir(parents=True)
    target.write_text(
        "Texto.\n\n![](content/images/entry1-page-003-img-01.png)\n",
        encoding="utf-8",
    )

    entry = {
        "id": "entry1",
        "advanced_markdown": "staging/markdown-auto/docling/advanced.md",
        "image_curation": {
            "status": "described",
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Arvore de prova com 3 niveis.",
                        }
                    },
                }
            },
        },
    }

    modified = _inject_for_current_entry(repo, entry)
    result = target.read_text(encoding="utf-8")

    assert modified == [target]
    assert "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->" in result
    assert "Arvore de prova com 3 niveis." in result
    assert "![](content/images/entry1-page-003-img-01.png)" not in result


def test_curator_studio_preserves_template_values_when_already_present():
    from src.ui.curator_studio import _merge_review_frontmatter_with_manifest

    fm = {
        "id": "entry-1",
        "advanced_markdown": "manual-review/custom-advanced.md",
        "advanced_backend": "marker",
    }
    manifest_entry = {
        "id": "entry-1",
        "advanced_markdown": "staging/markdown-auto/docling/advanced.md",
        "advanced_backend": "docling",
    }

    merged = _merge_review_frontmatter_with_manifest(fm, manifest_entry)

    assert merged["advanced_markdown"] == "manual-review/custom-advanced.md"
    assert merged["advanced_backend"] == "marker"




def test_curator_studio_pdf_preview_guard_accepts_only_pdf_paths():
    from src.ui.curator_studio import _is_pdf_preview_target

    assert _is_pdf_preview_target("raw/pdfs/aula1.pdf") is True
    assert _is_pdf_preview_target("raw/code/professor/xor-mlp.ipynb") is False
    assert _is_pdf_preview_target("raw/zip/projeto.zip") is False
    assert _is_pdf_preview_target(None) is False


def test_curator_studio_preview_zoom_helpers():
    from src.ui.curator_studio import _clamp_preview_zoom, _preview_target_width

    assert _clamp_preview_zoom(0.1) == 0.5
    assert _clamp_preview_zoom(1.0) == 1.0
    assert _clamp_preview_zoom(9.0) == 2.5
    assert _preview_target_width(1.0) == 400
    assert _preview_target_width(2.0) == 800


def test_curator_studio_markdown_image_reference_uses_repo_relative_path(tmp_path):
    from src.ui.curator_studio import _markdown_image_reference

    repo = tmp_path / "repo"
    markdown_path = repo / "staging" / "markdown-auto" / "marker" / "entry1.md"
    image_path = repo / "content" / "images" / "manual-crops" / "entry1-page-003-manual-101010.png"
    markdown_path.parent.mkdir(parents=True)
    image_path.parent.mkdir(parents=True)

    ref = _markdown_image_reference(markdown_path, image_path, repo)
    assert ref == "![](content/images/manual-crops/entry1-page-003-manual-101010.png)"


def test_curator_studio_normalize_repo_image_references_rewrites_relative_paths(tmp_path):
    from src.ui.curator_studio import _normalize_repo_image_references

    repo = tmp_path / "repo"
    markdown_path = repo / "staging" / "markdown-auto" / "marker" / "entry1.md"
    image_path = repo / "content" / "images" / "manual-crops" / "entry1-page-003-manual-101010.png"
    markdown_path.parent.mkdir(parents=True)
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"fake")

    markdown = (
        "Texto antes.\n\n"
        "![](../../../content/images/manual-crops/entry1-page-003-manual-101010.png)\n"
    )

    normalized = _normalize_repo_image_references(markdown, markdown_path, repo)

    assert normalized == (
        "Texto antes.\n\n"
        "![](content/images/manual-crops/entry1-page-003-manual-101010.png)\n"
    )


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
    from src.builder.vision.ollama_client import OllamaClient

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
        from src.builder.vision.image_classifier import classify_image
        img = tmp_path / "tiny.png"
        img.write_bytes(_create_minimal_png(10, 10))
        result = classify_image(img)
        assert result == "decorativa"

    def test_banner_aspect_ratio_is_decorative(self, tmp_path):
        from src.builder.vision.image_classifier import classify_image
        img = tmp_path / "banner.png"
        img.write_bytes(_create_minimal_png(800, 20))
        result = classify_image(img)
        assert result == "decorativa"

    def test_solid_color_is_decorative(self, tmp_path):
        from src.builder.vision.image_classifier import classify_image
        img = tmp_path / "solid.png"
        img.write_bytes(_create_minimal_png(200, 200, (128, 128, 128)))
        result = classify_image(img)
        assert result == "decorativa"

    def test_small_filesize_is_decorative(self, tmp_path):
        from src.builder.vision.image_classifier import classify_image
        img = tmp_path / "small.png"
        img.write_bytes(_create_minimal_png(100, 100))
        if img.stat().st_size < 5000:
            assert classify_image(img) == "decorativa"


class TestImageMapper:
    def test_maps_page_from_filename(self):
        from src.builder.vision.image_classifier import extract_page_number
        assert extract_page_number("page-006-img-01.png") == 6
        assert extract_page_number("page-001-img-02.jpg") == 1

    def test_maps_page_from_pymupdf4llm_pattern(self):
        from src.builder.vision.image_classifier import extract_page_number
        # pymupdf4llm pattern: {entry}-_page_N_Figure_M.png
        assert extract_page_number("logica-sintaxe-_page_6_Figure_1.png") == 7
        assert extract_page_number("aula01-_page_12_Figure_3.png") == 13
        assert extract_page_number("entry-_page_0_Figure_1.png") == 1

    def test_maps_page_from_resolved_pdf_asset_pattern(self):
        from src.builder.vision.image_classifier import extract_page_number
        assert extract_page_number("aula01-introducao-ia-aula01-introducao-ia.pdf-0004-09.png") == 4
        assert extract_page_number("aprendizadosupervisionado-classificacao-knn.pdf-0023-01.png") == 23

    def test_maps_page_from_additional_asset_variants(self):
        from src.builder.vision.image_classifier import extract_page_number
        assert extract_page_number("entry-page-004-table-01.md") == 4
        assert extract_page_number("entry.pdf-0007.png") == 7
        assert extract_page_number("entry-p_08-figure.png") == 8
        assert extract_page_number("entry-page12.webp") == 12

    def test_unknown_pattern_returns_none(self):
        from src.builder.vision.image_classifier import extract_page_number
        assert extract_page_number("random-image.png") is None
        assert extract_page_number("logo.jpg") is None
        assert extract_page_number("banner-2026.png") is None

    def test_group_images_by_page(self, tmp_path):
        from src.builder.vision.image_classifier import group_images_by_page
        images_dir = tmp_path / "content" / "images"
        images_dir.mkdir(parents=True)

        # Create fake image files with known patterns
        (images_dir / "entry1-page-003-img-01.png").write_bytes(b"fake")
        (images_dir / "entry1-page-003-img-02.png").write_bytes(b"fake")
        (images_dir / "entry1-page-007-img-01.png").write_bytes(b"fake")
        (images_dir / "entry1-_page_5_Figure_1.png").write_bytes(b"fake")
        (images_dir / "entry1-aula.pdf-0009-03.png").write_bytes(b"fake")
        (images_dir / "entry1-page-011-table-01.png").write_bytes(b"fake")
        (images_dir / "entry1-p_12-figure.png").write_bytes(b"fake")
        (images_dir / "unknown-image.png").write_bytes(b"fake")

        groups = group_images_by_page(images_dir, "entry1")
        assert 3 in groups  # page-003
        assert len(groups[3]) == 2
        assert 7 in groups
        assert 6 in groups  # _page_5 is zero-based -> page 6
        assert 9 in groups  # .pdf-0009-03
        assert 11 in groups  # page-011-table-01
        assert 12 in groups  # p_12
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

    def test_replace_adjacent_stale_description_blocks(self):
        from src.builder.engine import RepoBuilder
        markdown = (
            "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->\n"
            "<!-- Tipo: diagrama -->\n"
            "> **[Descrição de imagem]** Descrição antiga 1.\n"
            "<!-- /IMAGE_DESCRIPTION -->\n"
            "<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->\n"
            "<!-- Tipo: diagrama -->\n"
            "> **[Descrição de imagem]** Descrição antiga 2.\n"
            "<!-- /IMAGE_DESCRIPTION -->\n"
            "![](content/images/entry1-page-003-img-01.png)\n"
        )
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Diagrama atualizado sem duplicação.",
                        }
                    }
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "Descrição antiga 1." not in result
        assert "Descrição antiga 2." not in result
        assert result.count("<!-- IMAGE_DESCRIPTION: entry1-page-003-img-01.png -->") == 1
        assert "Diagrama atualizado sem duplicação." in result

    def test_compact_long_description_to_single_sentence(self):
        from src.builder.engine import RepoBuilder
        markdown = "![](content/images/entry1-page-003-img-01.png)"
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": (
                                "Árvore de derivação com três níveis e dois ramos principais. "
                                "A imagem também mostra observações laterais e uma legenda extensa que não "
                                "precisa ser repetida integralmente no contexto do tutor."
                            ),
                        }
                    },
                }
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "Árvore de derivação com três níveis e dois ramos principais." in result
        assert "legenda extensa" not in result

    def test_inject_orphan_descriptions_into_generated_section_when_image_ref_is_missing(self):
        from src.builder.engine import RepoBuilder

        markdown = "# Lista de revisão\n\nConteúdo sem referência explícita da imagem.\n"
        curation = {
            "pages": {
                "1": {
                    "include_page": True,
                    "images": {
                        "revisao-p1-revisao-p1.pdf-0001-07.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Árvore binária com exemplos crescentes para revisão.",
                        }
                    },
                }
            }
        }

        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "## Imagens Curadas" in result
        assert "<!-- IMAGE_DESCRIPTION_ORPHANS -->" in result
        assert "<!-- IMAGE_DESCRIPTION: revisao-p1-revisao-p1.pdf-0001-07.png -->" in result
        assert "Árvore binária com exemplos crescentes para revisão." in result

    def test_replace_existing_orphan_section_without_duplication(self):
        from src.builder.engine import RepoBuilder

        markdown = (
            "# Aula\n\n"
            "<!-- IMAGE_DESCRIPTION_ORPHANS -->\n"
            "## Imagens Curadas\n\n"
            "<!-- IMAGE_DESCRIPTION: entry1-page-026-manual-01.png -->\n"
            "<!-- Tipo: diagrama -->\n"
            "> **[Descrição de imagem]** Texto antigo.\n"
            "<!-- /IMAGE_DESCRIPTION -->\n"
            "<!-- /IMAGE_DESCRIPTION_ORPHANS -->\n"
        )
        curation = {
            "pages": {
                "26": {
                    "include_page": True,
                    "images": {
                        "entry1-page-026-manual-01.png": {
                            "type": "extração-latex",
                            "include": True,
                            "description": "Teorema com soma e produto de funções recursivas primitivas.",
                        }
                    },
                }
            }
        }

        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert result.count("<!-- IMAGE_DESCRIPTION_ORPHANS -->") == 1
        assert "Texto antigo." not in result
        assert "Teorema com soma e produto de funções recursivas primitivas." in result

    def test_place_orphan_description_near_matching_section_when_vocab_overlaps(self):
        from src.builder.engine import RepoBuilder

        markdown = (
            "# Aula 03\n\n"
            "Introdução geral.\n\n"
            "## Funções Básicas\n\n"
            "Conteúdo sobre função zero, sucessora e projeções.\n\n"
            "## Soma e Produto\n\n"
            "Nesta parte estudamos soma e produto de funções recursivas primitivas.\n"
        )
        curation = {
            "pages": {
                "26": {
                    "include_page": True,
                    "images": {
                        "entry1-page-026-manual-01.png": {
                            "type": "extração-latex",
                            "include": True,
                            "description": "Teorema com soma e produto de funções recursivas primitivas.",
                        }
                    },
                }
            }
        }

        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "## Imagens Curadas" not in result
        assert "<!-- IMAGE_DESCRIPTION: entry1-page-026-manual-01.png -->" in result
        assert result.index("## Soma e Produto") < result.index("entry1-page-026-manual-01.png")

    def test_duplicate_exact_description_becomes_short_reference(self):
        from src.builder.engine import RepoBuilder
        markdown = (
            "![](content/images/entry1-page-003-img-01.png)\n\n"
            "![](content/images/entry1-page-004-img-01.png)"
        )
        curation = {
            "pages": {
                "3": {
                    "include_page": True,
                    "images": {
                        "entry1-page-003-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Diagrama de rede neural com três camadas.",
                        }
                    },
                },
                "4": {
                    "include_page": True,
                    "images": {
                        "entry1-page-004-img-01.png": {
                            "type": "diagrama",
                            "include": True,
                            "description": "Diagrama de rede neural com três camadas.",
                        }
                    },
                },
            }
        }
        result = RepoBuilder.inject_image_descriptions(markdown, curation)
        assert "Diagrama de rede neural com três camadas." in result
        assert "Mesma imagem da página 3; mantendo só referência curta." in result
