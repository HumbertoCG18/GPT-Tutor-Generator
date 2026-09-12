"""Tests for marker routing heuristics in backend_runtime.

These functions control infrastructure decisions (device, cloud variant, vision model detection,
LLM usage, inline math redo, flag detection) with no test coverage. Any substring typo or
platform check inversion breaks device routing or leaks to cloud APIs unintentionally.
"""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from src.builder.runtime.backend_runtime import (
    marker_should_use_llm,
    marker_effective_torch_device,
    marker_model_is_qwen3_vl_8b,
    marker_model_is_cloud_variant,
    marker_model_is_probably_vision,
    marker_should_redo_inline_math,
    apply_marker_capabilities_help_text,
)


# ---------------------------------------------------------------------------
# marker_should_use_llm
# ---------------------------------------------------------------------------

def test_marker_should_use_llm_false_when_not_set():
    """Attribute missing → False."""
    ctx = mock.MagicMock(spec=[])  # No marker_use_llm attribute
    assert marker_should_use_llm(ctx) is False


def test_marker_should_use_llm_true_when_set():
    """marker_use_llm=True → True."""
    ctx = mock.MagicMock()
    ctx.marker_use_llm = True
    assert marker_should_use_llm(ctx) is True


def test_marker_should_use_llm_false_when_falsy():
    """marker_use_llm=False/0/None → False."""
    for val in (False, 0, None, ""):
        ctx = mock.MagicMock()
        ctx.marker_use_llm = val
        assert marker_should_use_llm(ctx) is False


# ---------------------------------------------------------------------------
# marker_effective_torch_device
# ---------------------------------------------------------------------------

def test_marker_effective_torch_device_respects_configured():
    """When torch_device is configured and not 'auto' → return configured."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = "cpu"
    assert marker_effective_torch_device(ctx) == "cpu"


def test_marker_effective_torch_device_ignores_auto():
    """When torch_device='auto' → fall back to platform default."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = "auto"
    expected = "mps" if sys.platform == "darwin" else "cuda"
    assert marker_effective_torch_device(ctx) == expected


def test_marker_effective_torch_device_ignores_empty():
    """When torch_device is empty string → fall back to platform default."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = ""
    expected = "mps" if sys.platform == "darwin" else "cuda"
    assert marker_effective_torch_device(ctx) == expected


def test_marker_effective_torch_device_normalizes_case():
    """Configured device is lowercased."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = "CPU"
    assert marker_effective_torch_device(ctx) == "cpu"


def test_marker_effective_torch_device_strips_whitespace():
    """Configured device has whitespace stripped."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = "  cpu  "
    assert marker_effective_torch_device(ctx) == "cpu"


@mock.patch("sys.platform", "darwin")
def test_marker_effective_torch_device_darwin_default():
    """On macOS (darwin) → default is 'mps'."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = None
    assert marker_effective_torch_device(ctx) == "mps"


@mock.patch("sys.platform", "linux")
def test_marker_effective_torch_device_linux_default():
    """On Linux → default is 'cuda'."""
    ctx = mock.MagicMock()
    ctx.marker_torch_device = None
    assert marker_effective_torch_device(ctx) == "cuda"


# ---------------------------------------------------------------------------
# marker_model_is_qwen3_vl_8b
# ---------------------------------------------------------------------------

def test_marker_model_is_qwen3_vl_8b_exact_match():
    """'qwen3-vl:8b' → True."""
    assert marker_model_is_qwen3_vl_8b("qwen3-vl:8b") is True


def test_marker_model_is_qwen3_vl_8b_with_prefix():
    """'qwen3-vl:8b-something' (startswith) → True."""
    assert marker_model_is_qwen3_vl_8b("qwen3-vl:8b-quantized") is True


def test_marker_model_is_qwen3_vl_8b_case_insensitive():
    """'QWEN3-VL:8B' (uppercase) → True."""
    assert marker_model_is_qwen3_vl_8b("QWEN3-VL:8B") is True


def test_marker_model_is_qwen3_vl_8b_with_whitespace():
    """'  qwen3-vl:8b  ' (whitespace) → True."""
    assert marker_model_is_qwen3_vl_8b("  qwen3-vl:8b  ") is True


def test_marker_model_is_qwen3_vl_8b_false_for_other_models():
    """'qwen2-vl:8b', 'qwen3-vl:7b', 'gpt-4' → False."""
    assert marker_model_is_qwen3_vl_8b("qwen2-vl:8b") is False
    assert marker_model_is_qwen3_vl_8b("qwen3-vl:7b") is False
    assert marker_model_is_qwen3_vl_8b("gpt-4") is False


def test_marker_model_is_qwen3_vl_8b_empty_string():
    """Empty string → False."""
    assert marker_model_is_qwen3_vl_8b("") is False
    assert marker_model_is_qwen3_vl_8b(None) is False


# ---------------------------------------------------------------------------
# marker_model_is_cloud_variant
# ---------------------------------------------------------------------------

def test_marker_model_is_cloud_variant_detects_cloud_substring():
    """'model-cloud', 'cloud-model' → True."""
    assert marker_model_is_cloud_variant("gpt-4-cloud") is True
    assert marker_model_is_cloud_variant("cloud-ollama") is True


def test_marker_model_is_cloud_variant_case_insensitive():
    """'MODEL-CLOUD' → True."""
    assert marker_model_is_cloud_variant("MODEL-CLOUD") is True


def test_marker_model_is_cloud_variant_false_for_local():
    """'qwen3-vl:8b', 'gpt-4' (no 'cloud') → False."""
    assert marker_model_is_cloud_variant("qwen3-vl:8b") is False
    assert marker_model_is_cloud_variant("gpt-4") is False
    assert marker_model_is_cloud_variant("local-ollama") is False


def test_marker_model_is_cloud_variant_empty():
    """Empty string → False."""
    assert marker_model_is_cloud_variant("") is False
    assert marker_model_is_cloud_variant(None) is False


# ---------------------------------------------------------------------------
# marker_model_is_probably_vision
# ---------------------------------------------------------------------------

def test_marker_model_is_probably_vision_detects_vl():
    """Model with '-vl' token → True."""
    assert marker_model_is_probably_vision("qwen3-vl:8b") is True


def test_marker_model_is_probably_vision_detects_vision():
    """Model with 'vision' token → True."""
    assert marker_model_is_probably_vision("gpt-4-vision") is True


def test_marker_model_is_probably_vision_detects_gemma3():
    """Model with 'gemma3' token → True."""
    assert marker_model_is_probably_vision("gemma3-pro") is True


def test_marker_model_is_probably_vision_detects_gemma4():
    """Model with 'gemma4' token → True."""
    assert marker_model_is_probably_vision("gemma4-large") is True


def test_marker_model_is_probably_vision_case_insensitive():
    """'QWEN3-VL:8B' → True."""
    assert marker_model_is_probably_vision("QWEN3-VL:8B") is True


def test_marker_model_is_probably_vision_false_for_non_vision():
    """'qwen2:7b', 'gpt-4', 'llama2' (no vision tokens) → False."""
    assert marker_model_is_probably_vision("qwen2:7b") is False
    assert marker_model_is_probably_vision("gpt-4") is False
    assert marker_model_is_probably_vision("llama2") is False


def test_marker_model_is_probably_vision_empty():
    """Empty string → False."""
    assert marker_model_is_probably_vision("") is False
    assert marker_model_is_probably_vision(None) is False


# ---------------------------------------------------------------------------
# marker_should_redo_inline_math
# ---------------------------------------------------------------------------

def test_marker_should_redo_inline_math_formula_priority_true():
    """When entry.formula_priority=True → True."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = True
    ctx.report.suggested_profile = "general"
    assert marker_should_redo_inline_math(ctx) is True


def test_marker_should_redo_inline_math_math_heavy_profile():
    """When report.suggested_profile='math_heavy' → True."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = False
    ctx.report.suggested_profile = "math_heavy"
    assert marker_should_redo_inline_math(ctx) is True


def test_marker_should_redo_inline_math_both_true():
    """When both are true → True."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = True
    ctx.report.suggested_profile = "math_heavy"
    assert marker_should_redo_inline_math(ctx) is True


def test_marker_should_redo_inline_math_false_for_neither():
    """When both are false/absent → False."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = False
    ctx.report.suggested_profile = "general"
    assert marker_should_redo_inline_math(ctx) is False


def test_marker_should_redo_inline_math_case_insensitive_profile():
    """Profile match is case-insensitive."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = False
    ctx.report.suggested_profile = "MATH_HEAVY"
    assert marker_should_redo_inline_math(ctx) is True


def test_marker_should_redo_inline_math_strips_whitespace():
    """Whitespace in profile is stripped."""
    ctx = mock.MagicMock()
    ctx.entry.formula_priority = False
    ctx.report.suggested_profile = "  math_heavy  "
    assert marker_should_redo_inline_math(ctx) is True


def test_marker_should_redo_inline_math_missing_attributes():
    """Missing attributes default to False."""
    ctx = mock.MagicMock()
    # Simulate missing attributes: getattr with default "" and False
    ctx.entry.formula_priority = None  # Falsy
    ctx.report.suggested_profile = None  # Falsy
    assert marker_should_redo_inline_math(ctx) is False


# ---------------------------------------------------------------------------
# apply_marker_capabilities_help_text
# ---------------------------------------------------------------------------

def test_apply_marker_capabilities_page_range_flag_dashed():
    """Help text with '--page-range' (dashed) → sets flag to '--page-range'."""
    caps = {}
    result = apply_marker_capabilities_help_text("Usage: marker --page-range 1-5", caps)
    assert result["page_range_flag"] == "--page-range"


def test_apply_marker_capabilities_page_range_flag_underscore():
    """Help text with '--page_range' (underscore) → sets flag to '--page_range'."""
    caps = {}
    result = apply_marker_capabilities_help_text("Usage: marker --page_range 1-5", caps)
    assert result["page_range_flag"] == "--page_range"


def test_apply_marker_capabilities_page_range_flag_none():
    """Help text without page range flag → sets flag to None."""
    caps = {}
    result = apply_marker_capabilities_help_text("Usage: marker --help", caps)
    assert result["page_range_flag"] is None


def test_apply_marker_capabilities_force_ocr_dashed():
    """Help text with '--force-ocr' (dashed) → sets flag to '--force-ocr'."""
    caps = {}
    result = apply_marker_capabilities_help_text("Usage: marker --force-ocr", caps)
    assert result["force_ocr_flag"] == "--force-ocr"


def test_apply_marker_capabilities_force_ocr_underscore():
    """Help text with '--force_ocr' (underscore) → sets flag to '--force_ocr'."""
    caps = {}
    result = apply_marker_capabilities_help_text("Usage: marker --force_ocr", caps)
    assert result["force_ocr_flag"] == "--force_ocr"


def test_apply_marker_capabilities_use_llm():
    """Help text with '--use-llm' or '--use_llm' → sets use_llm_flag."""
    caps = {}
    result = apply_marker_capabilities_help_text("--use-llm", caps)
    assert result["use_llm_flag"] == "--use-llm"

    caps = {}
    result = apply_marker_capabilities_help_text("--use_llm", caps)
    assert result["use_llm_flag"] == "--use_llm"


def test_apply_marker_capabilities_llm_service():
    """Help text with '--llm-service' or '--llm_service' → sets llm_service_flag."""
    caps = {}
    result = apply_marker_capabilities_help_text("--llm-service", caps)
    assert result["llm_service_flag"] == "--llm-service"

    caps = {}
    result = apply_marker_capabilities_help_text("--llm_service", caps)
    assert result["llm_service_flag"] == "--llm_service"


def test_apply_marker_capabilities_case_insensitive():
    """Flag detection is case-insensitive."""
    caps = {}
    result = apply_marker_capabilities_help_text("USAGE: MARKER --PAGE-RANGE 1-5", caps)
    assert result["page_range_flag"] == "--page-range"


def test_apply_marker_capabilities_ollama_base_url():
    """Detects ollama base URL flags in various formats."""
    candidates = [
        ("--OllamaService_ollama_base_url", "--OllamaService_ollama_base_url"),
        ("--ollama-base-url", "--ollama-base-url"),
        ("--ollama_base_url", "--ollama_base_url"),
        ("--ollamaservice-ollama-base-url", "--ollamaservice-ollama-base-url"),
    ]
    for help_snippet, expected_flag in candidates:
        caps = {}
        result = apply_marker_capabilities_help_text(f"Usage: {help_snippet} http://localhost", caps)
        assert result["ollama_base_url_flag"] == expected_flag, f"Failed for {help_snippet}"


def test_apply_marker_capabilities_preserves_existing_caps():
    """Function preserves caps dict that already has values."""
    caps = {"existing_key": "existing_value"}
    result = apply_marker_capabilities_help_text("--page-range", caps)
    assert result["existing_key"] == "existing_value"
    assert result["page_range_flag"] == "--page-range"


def test_apply_marker_capabilities_handles_empty_help_text():
    """Empty help text → all flags set to None (or not set)."""
    caps = {}
    result = apply_marker_capabilities_help_text("", caps)
    assert result.get("page_range_flag") is None
    assert result.get("force_ocr_flag") is None
