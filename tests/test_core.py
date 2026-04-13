"""Tests for utility functions and core logic."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest import mock

# Mock tkinter before importing the main module (not available in headless CI)
_tk_mock = mock.MagicMock()
sys.modules.setdefault("tkinter", _tk_mock)
sys.modules.setdefault("tkinter.filedialog", _tk_mock)
sys.modules.setdefault("tkinter.messagebox", _tk_mock)
sys.modules.setdefault("tkinter.simpledialog", _tk_mock)
sys.modules.setdefault("tkinter.ttk", _tk_mock)

import pytest

import src.builder.engine as engine_module
import src.utils.helpers as helpers_module

from src.builder.engine import (
    BackendSelector,
    _auto_map_entry_unit,
    _build_marker_page_chunks,
    _build_file_map_unit_index,
    _build_timeline_candidate_rows,
    _build_timeline_index,
    _serialize_timeline_index,
    _score_timeline_row_against_unit,
    _compact_notebook_markdown,
    _generated_repo_gitignore_text,
    rows_to_markdown_table,
    wrap_frontmatter,
    _html_to_structured_markdown,
    _parse_units_from_teaching_plan,
    _parse_bibliography_from_teaching_plan,
    _parse_syllabus_timeline,
    _parse_timeline_date_value,
    _match_timeline_to_units,
    _build_assessment_context_from_course,
    _topic_text,
    _topic_depth,
    _seed_glossary_fields,
    _repair_mojibake_text,
    _sanitize_external_markdown_text,
    _normalize_unicode_math,
    _detect_latex_corruption,
    _hybridize_marker_markdown_with_base,
    _find_glossary_evidence,
    _filter_live_manifest_entries,
    _marker_progress_hints,
    course_map_md,
    exercise_index_md,
    file_map_md,
    glossary_md,
    generate_claude_project_instructions,
    generate_gemini_instructions,
    generate_gpt_instructions,
)
from src.models.core import (
    DocumentProfileReport,
    FileEntry,
    PipelineDecision,
    PendingOperation,
)
from src.utils.helpers import (
    CODE_EXTENSIONS,
    LANG_MAP,
    auto_detect_category,
    ensure_dir,
    file_size_mb,
    pages_to_marker_range,
    parse_page_range,
    safe_rel,
    slugify,
    write_text,
)
from tests.fixtures.syllabus_timeline_cases import (
    METODOS_FORMAIS_SYLLABUS,
    METODOS_FORMAIS_UNITS,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        assert slugify("Cálculo I - 2024/1") == "calculo-i-20241"

    def test_multiple_spaces(self):
        assert slugify("  foo   bar  ") == "foo-bar"

    def test_empty_string(self):
        assert slugify("") == "untitled"

    def test_only_symbols(self):
        assert slugify("!!!") == "untitled"

    def test_underscores(self):
        assert slugify("foo_bar_baz") == "foo-bar-baz"

    def test_multiple_dashes(self):
        assert slugify("foo---bar") == "foo-bar"

    def test_leading_trailing_dashes(self):
        assert slugify("-foo-") == "foo"

    def test_removes_accents_for_technical_ids(self):
        assert slugify("Métodos Formais") == "metodos-formais"
        assert slugify("Verificação de Programas") == "verificacao-de-programas"


class TestCodeExtensions:
    def test_isabelle_theory_is_supported_as_code(self):
        assert ".thy" in CODE_EXTENSIONS
        assert LANG_MAP["thy"] == "isabelle"
        assert auto_detect_category("Aula01.thy") == "codigo-professor"
        assert auto_detect_category("Aula01.ipynb") == "codigo-professor"


class TestMarkerHybridMarkdownRescue:
    def test_recovers_accented_plain_text_without_touching_math_lines(self):
        base = (
            "---\nentry_id: \"x\"\n---\n"
            "# Título\n\n"
            "A função não é total e também não é injetiva.\n\n"
            "<math>x^2 + y^2 = z^2</math>\n"
        )
        marker = (
            "---\nentry_id: \"x\"\n---\n"
            "# Título\n\n"
            "A funcao nao e total e tambem nao e injetiva.\n\n"
            "<math>x^2 + y^2 = z^2</math>\n"
        )

        merged, stats = _hybridize_marker_markdown_with_base(base, marker)

        assert "A função não é total e também não é injetiva." in merged
        assert "<math>x^2 + y^2 = z^2</math>" in merged
        assert stats["replacements"] == 1


class TestMathNormalization:
    def test_normalizes_tex_accents_inside_math_regions(self):
        original = "$$= \\sum_{k=0}^{x_0+1} 2k \\quad (por \\ definição \\ do \\ somat\\'orio)$$"

        normalized = _normalize_unicode_math(original)

        assert "somatório" in normalized
        assert "\\sum_{k=0}^{x_0+1}" in normalized

    def test_preserves_regular_math_commands_while_fixing_textual_accents(self):
        original = "$\\hat{o} + \\text{somat\\'orio}$"

        normalized = _normalize_unicode_math(original)

        assert "\\hat{o}" in normalized
        assert "somatório" in normalized


class TestTimelineLabelFormatting:
    def test_normalizes_timeline_dates_to_dd_mm_yyyy(self):
        from src.ui.dialogs import _format_timeline_label_dates

        assert _format_timeline_label_dates("2026-04-09 - 16/04/2026") == "09/04/2026 a 16/04/2026"

    def test_timeline_block_display_period_always_uses_range_separator(self):
        from src.ui.dialogs import _timeline_block_display_period

        assert _timeline_block_display_period(
            {"period_start": "2026-04-06", "period_end": "2026-04-08", "period_label": "06/04/2026 a 08/04/2026"}
        ) == "06/04/2026 a 08/04/2026"


class TestLatexCorruptionDetection:
    def test_detect_no_corruption_clean_markdown(self):
        md = "## Seção\n\nTexto normal sem matemática.\n"
        result = _detect_latex_corruption(md)
        assert result["corrupted"] is False
        assert result["score"] < 25

    def test_detect_unbalanced_dollars(self):
        md = "A fórmula $x + y = z é importante mas ficou sem fechamento.\n"
        result = _detect_latex_corruption(md)
        assert "delimitadores $" in " ".join(result["signals"])

    def test_detect_unclosed_begin(self):
        md = "Veja o ambiente:\n\\begin{array}{cc}\na & b \\\\\n"
        result = _detect_latex_corruption(md)
        assert any("begin" in signal.lower() for signal in result["signals"])

    def test_detect_ignores_code_blocks(self):
        md = "```python\n$ echo hello\n{ not latex }\n```\n"
        result = _detect_latex_corruption(md)
        assert result["corrupted"] is False

    def test_detect_unicode_without_latex(self):
        md = ("A proposição x ∈ ℕ e também y ≥ x são válidas.\n" * 3)
        result = _detect_latex_corruption(md)
        assert result["score"] > 0

    def test_detect_clean_latex(self):
        md = "A fórmula $\\forall x \\in \\mathbb{N}, x + 0 = x$ está correta.\n"
        result = _detect_latex_corruption(md)
        assert result["corrupted"] is False


class TestMarkerCapabilities:
    def teardown_method(self):
        engine_module._MARKER_CAPABILITIES_CACHE = None

    def test_help_timeout_uses_conservative_defaults(self, monkeypatch):
        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")

        def _raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

        monkeypatch.setattr(engine_module.subprocess, "run", _raise_timeout)
        engine_module._MARKER_CAPABILITIES_CACHE = None

        caps = engine_module._detect_marker_capabilities()

        assert caps == {
            "page_range_flag": "--page_range",
            "force_ocr_flag": "--force_ocr",
            "use_llm_flag": "--use_llm",
            "llm_service_flag": "--llm_service",
            "ollama_base_url_flag": "--OllamaService_ollama_base_url",
            "ollama_model_flag": "--OllamaService_ollama_model",
            "ollama_timeout_flag": "--OllamaService_timeout",
            "redo_inline_math_flag": "--redo_inline_math",
            "disable_image_extraction_flag": "--disable_image_extraction",
        }

    def test_current_marker_help_preserves_optimistic_defaults_for_unknown_flags(self, monkeypatch):
        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        help_text = """
Usage: marker_single [OPTIONS] FPATH

Options:
  --page_range TEXT
  --disable_ocr
  --output_dir PATH
  --help
"""
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *args, **kwargs: mock.Mock(stdout=help_text, stderr=""),
        )
        engine_module._MARKER_CAPABILITIES_CACHE = None

        caps = engine_module._detect_marker_capabilities()

        assert caps["page_range_flag"] == "--page_range"
        assert caps["force_ocr_flag"] is None
        assert caps["use_llm_flag"] == "--use_llm"
        assert caps["llm_service_flag"] == "--llm_service"
        assert caps["ollama_base_url_flag"] == "--OllamaService_ollama_base_url"
        assert caps["ollama_model_flag"] == "--OllamaService_ollama_model"
        assert caps["redo_inline_math_flag"] == "--redo_inline_math"

    def test_marker_help_detects_ollama_llm_flags(self, monkeypatch):
        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        help_text = """
Usage: marker_single [OPTIONS] FPATH

Options:
  --page_range TEXT
  --use_llm
  --llm_service TEXT
  --ollama_base_url TEXT
  --ollama_model TEXT
  --redo_inline_math
  --output_dir PATH
  --help
"""
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *args, **kwargs: mock.Mock(stdout=help_text, stderr=""),
        )
        engine_module._MARKER_CAPABILITIES_CACHE = None

        caps = engine_module._detect_marker_capabilities()

        assert caps["use_llm_flag"] == "--use_llm"
        assert caps["llm_service_flag"] == "--llm_service"
        assert caps["ollama_base_url_flag"] == "--ollama_base_url"
        assert caps["ollama_model_flag"] == "--ollama_model"
        assert caps["redo_inline_math_flag"] == "--redo_inline_math"

    def test_marker_help_detects_ollama_service_scoped_flags(self, monkeypatch):
        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        help_text = """
Usage: marker_single [OPTIONS] FPATH

Options:
  --use_llm
  --llm_service TEXT
  --OllamaService_ollama_base_url TEXT
  --OllamaService_ollama_model TEXT
  --redo_inline_math
  --help
"""
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *args, **kwargs: mock.Mock(stdout=help_text, stderr=""),
        )
        engine_module._MARKER_CAPABILITIES_CACHE = None

        caps = engine_module._detect_marker_capabilities()

        assert caps["use_llm_flag"] == "--use_llm"
        assert caps["llm_service_flag"] == "--llm_service"
        assert caps["ollama_base_url_flag"] == "--OllamaService_ollama_base_url"
        assert caps["ollama_model_flag"] == "--OllamaService_ollama_model"
        assert caps["redo_inline_math_flag"] == "--redo_inline_math"


class TestMarkerProgressHints:
    def test_marker_progress_hints_reports_phase_transition(self):
        phase, hints = _marker_progress_hints(
            "LLM processors running:  20%|##        | 5/25 [01:58<07:06, 21.31s/it]",
            None,
        )

        assert phase == "LLM processors running"
        assert hints == ["Fase detectada: LLM processors running"]

    def test_marker_progress_hints_reports_zero_item_phase_completion(self):
        phase, hints = _marker_progress_hints(
            "Detecting bboxes: 0it [00:00, ?it/s]",
            None,
        )

        assert phase == "Detecting bboxes"
        assert hints == [
            "Fase detectada: Detecting bboxes",
            "Fase 'Detecting bboxes' concluída sem itens para processar.",
        ]

class TestCliResolution:
    def test_marker_cli_prefers_project_venv(self, monkeypatch, tmp_path):
        project_root = tmp_path / "repo"
        scripts_dir = project_root / ".venv" / "Scripts"
        scripts_dir.mkdir(parents=True)
        local_marker = scripts_dir / "marker_single.exe"
        local_marker.write_text("", encoding="utf-8")

        monkeypatch.setattr(helpers_module, "__file__", str(project_root / "src" / "utils" / "helpers.py"))
        monkeypatch.setattr(helpers_module.os, "name", "nt")
        monkeypatch.setattr(helpers_module.shutil, "which", lambda _: "C:/Windows/marker_single.exe")

        resolved = helpers_module._resolve_cli_from_project_venv("marker_single")

        assert resolved == str(local_marker)


class TestAdvancedBackendPolicies:
    def _ctx(
        self,
        *,
        page_count=116,
        page_range="",
        profile="math_heavy",
        images_count=290,
        force_ocr=False,
        formula_priority=False,
        suspected_scan=False,
        stall_timeout=300,
    ):
        entry = FileEntry(
            source_path="C:/repo/raw/pdfs/material-de-aula/mlp.pdf",
            file_type="pdf",
            category="material-de-aula",
            title="MLP",
            document_profile=profile,
            preferred_backend="marker",
            page_range=page_range,
            force_ocr=force_ocr,
            formula_priority=formula_priority,
        )
        report = DocumentProfileReport(
            page_count=page_count,
            images_count=images_count,
            suggested_profile=profile,
            suspected_scan=suspected_scan,
        )
        return engine_module.BackendContext(
            Path("C:/repo"),
            Path("C:/repo/raw/pdfs/material-de-aula/mlp.pdf"),
            entry,
            report,
            stall_timeout=stall_timeout,
        )

    def test_large_heavy_marker_workload_uses_10_page_chunks(self):
        ctx = self._ctx(page_count=116, profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 10

    def test_medium_heavy_marker_workload_keeps_20_page_chunks(self):
        ctx = self._ctx(page_count=60, profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 20

    def test_formula_priority_no_longer_forces_marker_ocr(self):
        ctx = self._ctx(formula_priority=True, suspected_scan=False, force_ocr=False)
        assert engine_module._should_force_ocr_for_marker(ctx) is False

    def test_manual_force_ocr_still_forces_marker_ocr(self):
        ctx = self._ctx(force_ocr=True, suspected_scan=False)
        assert engine_module._should_force_ocr_for_marker(ctx) is True

    def test_scanned_pdf_still_forces_marker_ocr(self):
        ctx = self._ctx(suspected_scan=True)
        assert engine_module._should_force_ocr_for_marker(ctx) is True

    def test_large_heavy_marker_timeout_is_raised_to_2700(self):
        ctx = self._ctx(page_count=116, profile="math_heavy", stall_timeout=300)
        assert engine_module._advanced_cli_stall_timeout("marker", ctx) == 2700

    def test_marker_llm_with_qwen3_vl_8b_uses_higher_small_doc_timeout(self):
        ctx = self._ctx(page_count=10, profile="math_heavy", stall_timeout=300)
        ctx.marker_use_llm = True
        ctx.marker_llm_model = "qwen3-vl:8b"
        assert engine_module._advanced_cli_stall_timeout("marker", ctx) == 1200

    def test_large_heavy_marker_llm_with_qwen3_vl_8b_is_raised_to_3600(self):
        ctx = self._ctx(page_count=116, profile="math_heavy", stall_timeout=300)
        ctx.marker_use_llm = True
        ctx.marker_llm_model = "qwen3-vl:8b"
        assert engine_module._advanced_cli_stall_timeout("marker", ctx) == 3600

    def test_large_heavy_docling_timeout_is_raised_to_1800(self):
        ctx = self._ctx(page_count=116, profile="math_heavy", stall_timeout=300)
        assert engine_module._advanced_cli_stall_timeout("docling", ctx) == 1800

    def test_page_range_drives_large_workload_decision(self):
        ctx = self._ctx(page_count=200, page_range="1-10", profile="math_heavy")
        assert engine_module._marker_chunk_size_for_workload(ctx) == 20

    def test_datalab_long_document_policy_uses_20_page_chunks_for_math_heavy(self):
        ctx = self._ctx(page_count=90, profile="math_heavy")
        assert engine_module._datalab_chunk_size_for_workload(ctx) == 20
        assert engine_module._datalab_should_chunk(ctx) is True

    def test_datalab_run_uses_single_execution_for_small_selected_page_range(self, tmp_path, monkeypatch):
        backend = engine_module.DatalabCloudBackend()
        ctx = self._ctx(page_count=200, page_range="1-10", profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        calls = {"single": 0, "chunked": 0}

        def _fake_single(*args, **kwargs):
            calls["single"] += 1
            return engine_module.BackendRunResult(
                name="datalab",
                layer="advanced",
                status="ok",
            )

        def _fake_chunked(*args, **kwargs):
            calls["chunked"] += 1
            return engine_module.BackendRunResult(
                name="datalab",
                layer="advanced",
                status="ok",
            )

        monkeypatch.setattr(backend, "_run_single_datalab", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_datalab", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert calls == {"single": 1, "chunked": 0}

    def test_datalab_chunked_backend_merges_markdown_and_metadata(self, tmp_path, monkeypatch):
        backend = engine_module.DatalabCloudBackend()
        ctx = self._ctx(page_count=55, profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.entry.datalab_mode = "balanced"

        captured_ranges = []

        def _fake_convert(*args, **kwargs):
            page_range = kwargs.get("page_range")
            captured_ranges.append(page_range)
            chunk_start = page_range.split("-", 1)[0] if page_range else "0"
            return mock.Mock(
                request_id=f"req-{chunk_start}",
                request_check_url=f"https://www.datalab.to/api/v1/convert/req-{chunk_start}",
                markdown=f"# Chunk {chunk_start}\n\n![](figure-{chunk_start}.png)\n\nTexto {chunk_start}\n",
                images={},
                metadata={"source": "datalab"},
                page_count=len(engine_module.parse_page_range(page_range or "") or [0]),
                parse_quality_score=4.5,
                cost_breakdown={"total_cents": 2},
                raw_response={"status": "complete", "success": True, "error": None},
            )

        monkeypatch.setattr(engine_module, "convert_document_to_markdown", _fake_convert)
        monkeypatch.setattr(engine_module, "get_datalab_base_url", lambda: "https://www.datalab.to")

        result = backend.run(ctx)

        assert result.status == "ok"
        assert captured_ranges == ["0-19", "20-39", "40-54"]
        md_path = tmp_path / result.markdown_path
        md_text = md_path.read_text(encoding="utf-8")
        assert "DATALAB_CHUNK 1" in md_text
        assert "Texto 0" in md_text
        assert "Texto 20" in md_text
        assert "Texto 40" in md_text
        assert "![](figure-0.png)" not in md_text

        metadata = json.loads((tmp_path / "staging" / "markdown-auto" / "datalab" / "mlp" / "datalab-run.json").read_text(encoding="utf-8"))
        assert metadata["chunked"] is True
        assert metadata["chunk_size"] == 20
        assert metadata["page_range"] == "0-54"
        assert metadata["selected_pages_count"] == 55
        assert len(metadata["chunks"]) == 3
        assert metadata["cost_breakdown"]["total_cents"] == 6.0

    def test_datalab_backend_disables_api_side_images_and_captions(self, tmp_path, monkeypatch):
        backend = engine_module.DatalabCloudBackend()
        ctx = self._ctx(page_count=12, profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.entry.page_range = "1-2"
        ctx.pages = [0, 1]
        ctx.entry.datalab_mode = "fast"
        captured_kwargs = {}

        fake_result = mock.Mock(
            request_id="req-123",
            request_check_url="https://www.datalab.to/api/v1/convert/req-123",
            markdown="# Título\n\n![](figure-1.png)\n",
            images={"figure-1.png": "aGVsbG8="},
            metadata={"source": "datalab"},
            page_count=2,
            parse_quality_score=4.7,
            cost_breakdown={"total_cents": 2},
            raw_response={"status": "complete", "success": True, "error": None},
        )

        def _fake_convert(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return fake_result

        monkeypatch.setattr(engine_module, "convert_document_to_markdown", _fake_convert)
        monkeypatch.setattr(engine_module, "get_datalab_base_url", lambda: "https://www.datalab.to")

        result = backend.run(ctx)

        assert result.status == "ok"
        assert captured_kwargs["disable_image_extraction"] is True
        assert captured_kwargs["disable_image_captions"] is True
        md_path = tmp_path / result.markdown_path
        assert md_path.exists()
        md_text = md_path.read_text(encoding="utf-8")
        assert "![](figure-1.png)" not in md_text
        assert "Título" in md_text
        assert not (tmp_path / "staging" / "markdown-auto" / "datalab" / "mlp" / "mlp_images" / "figure-1.png").exists()
        metadata = json.loads((tmp_path / "staging" / "markdown-auto" / "datalab" / "mlp" / "datalab-run.json").read_text(encoding="utf-8"))
        assert metadata["mode"] == "fast"
        assert metadata["page_range"] == "0-1"
        assert metadata["parse_quality_score"] == 4.7
        assert metadata["disable_image_extraction"] is True
        assert metadata["disable_image_captions"] is True
        assert metadata["images_saved"] == []

    def test_marker_command_omits_force_ocr_when_only_formula_priority_is_enabled(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(formula_priority=True, force_ocr=False, suspected_scan=False)
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        out_dir = tmp_path / "staging" / "markdown-auto" / "marker" / "mlp"

        def _fake_run_cli(cmd, backend_name, ctx_obj, stall_timeout):
            output_dir = Path(cmd[cmd.index("--output_dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "result.md").write_text("# ok", encoding="utf-8")
            return 0, [], []

        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        monkeypatch.setattr(engine_module, "_run_cli_with_timeout", _fake_run_cli)

        result = backend._run_single_marker(
            ctx,
            out_dir,
            {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
                "use_llm_flag": None,
                "llm_service_flag": None,
                "ollama_base_url_flag": None,
                "ollama_model_flag": None,
                "redo_inline_math_flag": None,
            },
            None,
            300,
        )

        assert result.status == "ok"
        assert "--force_ocr" not in result.command

    def test_marker_command_uses_ollama_llm_when_enabled(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(formula_priority=False, force_ocr=False, suspected_scan=False, profile="diagram_heavy")
        ctx.marker_use_llm = True
        ctx.marker_llm_model = "qwen3-vl:235b-cloud"
        ctx.marker_torch_device = "cuda"
        ctx.ollama_base_url = "http://localhost:11434"
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        out_dir = tmp_path / "staging" / "markdown-auto" / "marker" / "mlp"

        def _fake_run_cli(cmd, backend_name, ctx_obj, stall_timeout):
            output_dir = Path(cmd[cmd.index("--output_dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "result.md").write_text("# ok", encoding="utf-8")
            return 0, [], []

        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        monkeypatch.setattr(engine_module, "_run_cli_with_timeout", _fake_run_cli)

        result = backend._run_single_marker(
            ctx,
            out_dir,
            {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
                "use_llm_flag": "--use_llm",
                "llm_service_flag": "--llm_service",
                "ollama_base_url_flag": "--ollama_base_url",
                "ollama_model_flag": "--ollama_model",
                "redo_inline_math_flag": "--redo_inline_math",
            },
            None,
            300,
        )

        assert result.status == "ok"
        assert "--use_llm" in result.command
        assert "--llm_service" in result.command
        assert engine_module.MARKER_OLLAMA_SERVICE in result.command
        assert "--ollama_base_url" in result.command
        assert "http://localhost:11434" in result.command
        assert "--ollama_model" in result.command
        assert "qwen3-vl:235b-cloud" in result.command
        assert "--redo_inline_math" not in result.command
        metadata = json.loads((out_dir / "marker-run.json").read_text(encoding="utf-8"))
        assert metadata["llm"]["recommended_model"] is False
        assert metadata["llm"]["is_cloud_variant"] is True
        assert metadata["llm"]["is_probably_vision"] is True
        assert metadata["torch_device"] == {"configured": "cuda", "effective": "cuda"}

    def test_marker_command_adds_redo_inline_math_for_formula_priority_with_llm(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(formula_priority=True, force_ocr=False, suspected_scan=False)
        ctx.marker_use_llm = True
        ctx.marker_llm_model = "qwen3-vl:8b"
        ctx.ollama_base_url = "http://localhost:11434"
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        out_dir = tmp_path / "staging" / "markdown-auto" / "marker" / "mlp"

        def _fake_run_cli(cmd, backend_name, ctx_obj, stall_timeout):
            output_dir = Path(cmd[cmd.index("--output_dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "result.md").write_text("# ok", encoding="utf-8")
            return 0, [], []

        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        monkeypatch.setattr(engine_module, "_run_cli_with_timeout", _fake_run_cli)

        result = backend._run_single_marker(
            ctx,
            out_dir,
            {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
                "use_llm_flag": "--use_llm",
                "llm_service_flag": "--llm_service",
                "ollama_base_url_flag": "--OllamaService_ollama_base_url",
                "ollama_model_flag": "--OllamaService_ollama_model",
                "redo_inline_math_flag": "--redo_inline_math",
            },
            None,
            300,
        )

        assert result.status == "ok"
        assert "--redo_inline_math" in result.command

        metadata = json.loads((out_dir / "marker-run.json").read_text(encoding="utf-8"))
        assert metadata["llm"] == {
            "enabled": True,
            "service": engine_module.MARKER_OLLAMA_SERVICE,
            "model": "qwen3-vl:8b",
            "base_url": "http://localhost:11434",
            "redo_inline_math": True,
            "recommended_model": True,
            "is_cloud_variant": False,
            "is_probably_vision": True,
            "visual_processors_disabled": False,
        }

    def test_marker_llm_model_does_not_fallback_to_vision_model(self):
        ctx = self._ctx()
        ctx.marker_llm_model = ""
        ctx.vision_model = "qwen3-vl:235b-cloud"

        assert engine_module._marker_ollama_model(ctx) == ""

    def test_marker_command_skips_llm_flags_without_explicit_marker_model(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(formula_priority=False, force_ocr=False, suspected_scan=False)
        ctx.marker_use_llm = True
        ctx.marker_llm_model = ""
        ctx.vision_model = "qwen3-vl:235b-cloud"
        ctx.ollama_base_url = "http://localhost:11434"
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        out_dir = tmp_path / "staging" / "markdown-auto" / "marker" / "mlp"

        def _fake_run_cli(cmd, backend_name, ctx_obj, stall_timeout):
            output_dir = Path(cmd[cmd.index("--output_dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "result.md").write_text("# ok", encoding="utf-8")
            return 0, [], []

        monkeypatch.setattr(engine_module, "MARKER_CLI", "marker_single")
        monkeypatch.setattr(engine_module, "_run_cli_with_timeout", _fake_run_cli)

        result = backend._run_single_marker(
            ctx,
            out_dir,
            {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
                "use_llm_flag": "--use_llm",
                "llm_service_flag": "--llm_service",
                "ollama_base_url_flag": "--OllamaService_ollama_base_url",
                "ollama_model_flag": "--OllamaService_ollama_model",
                "redo_inline_math_flag": "--redo_inline_math",
            },
            None,
            300,
        )

        assert result.status == "ok"
        assert "--use_llm" not in result.command
        assert "--llm_service" not in result.command
        assert "--OllamaService_ollama_base_url" not in result.command
        assert "--OllamaService_ollama_model" not in result.command

    def test_marker_run_uses_single_execution_for_small_selected_page_range(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(page_count=200, page_range="1-10", profile="math_heavy")
        called = {"single": 0, "chunked": 0}
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")

        monkeypatch.setattr(
            engine_module,
            "_detect_marker_capabilities",
            lambda: {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
            },
        )

        def _fake_single(*args, **kwargs):
            called["single"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        def _fake_chunked(*args, **kwargs):
            called["chunked"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        monkeypatch.setattr(backend, "_run_single_marker", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_marker", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert called == {"single": 1, "chunked": 0}

    def test_marker_default_fallback_mode_tries_single_before_chunking(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(page_count=200, page_range="", profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.marker_chunking_mode = "fallback"

        monkeypatch.setattr(
            engine_module,
            "_detect_marker_capabilities",
            lambda: {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
            },
        )
        calls = {"single": 0, "chunked": 0}

        def _fake_single(*args, **kwargs):
            calls["single"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        def _fake_chunked(*args, **kwargs):
            calls["chunked"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        monkeypatch.setattr(backend, "_run_single_marker", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_marker", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert calls == {"single": 1, "chunked": 0}

    def test_marker_fallback_mode_retries_in_chunks_after_timeout(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(page_count=200, page_range="", profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.marker_chunking_mode = "fallback"

        monkeypatch.setattr(
            engine_module,
            "_detect_marker_capabilities",
            lambda: {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
            },
        )
        calls = {"single": 0, "chunked": 0}

        def _fake_single(*args, **kwargs):
            calls["single"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="error",
                command=["marker_single"],
                error="marker travou (sem output por 1800s). Último output:\nRecognizing Text",
            )

        def _fake_chunked(*args, **kwargs):
            calls["chunked"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        monkeypatch.setattr(backend, "_run_single_marker", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_marker", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert calls == {"single": 1, "chunked": 1}

    def test_marker_off_mode_never_chunks_automatically(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(page_count=200, page_range="", profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.marker_chunking_mode = "off"

        monkeypatch.setattr(
            engine_module,
            "_detect_marker_capabilities",
            lambda: {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
            },
        )
        calls = {"single": 0, "chunked": 0}

        def _fake_single(*args, **kwargs):
            calls["single"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        def _fake_chunked(*args, **kwargs):
            calls["chunked"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        monkeypatch.setattr(backend, "_run_single_marker", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_marker", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert calls == {"single": 1, "chunked": 0}

    def test_marker_always_mode_chunks_large_documents(self, tmp_path, monkeypatch):
        backend = engine_module.MarkerCLIBackend()
        ctx = self._ctx(page_count=200, page_range="", profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        ctx.marker_chunking_mode = "always"

        monkeypatch.setattr(
            engine_module,
            "_detect_marker_capabilities",
            lambda: {
                "page_range_flag": "--page_range",
                "force_ocr_flag": "--force_ocr",
            },
        )
        calls = {"single": 0, "chunked": 0}

        def _fake_single(*args, **kwargs):
            calls["single"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        def _fake_chunked(*args, **kwargs):
            calls["chunked"] += 1
            return engine_module.BackendRunResult(
                name="marker",
                layer="advanced",
                status="ok",
                command=["marker_single"],
            )

        monkeypatch.setattr(backend, "_run_single_marker", _fake_single)
        monkeypatch.setattr(backend, "_run_chunked_marker", _fake_chunked)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert calls == {"single": 0, "chunked": 1}

    def test_docling_python_backend_runs_with_formula_enrichment_for_math_heavy(self, tmp_path, monkeypatch):
        class _FakePdfPipelineOptions:
            def __init__(self):
                self.do_formula_enrichment = False

        class _FakePdfFormatOption:
            def __init__(self, pipeline_options):
                self.pipeline_options = pipeline_options

        class _FakeDocument:
            def export_to_markdown(self):
                return "# converted"

        class _FakeResult:
            def __init__(self):
                self.document = _FakeDocument()

        captured = {}

        class _FakeDocumentConverter:
            def __init__(self, format_options):
                captured["format_options"] = format_options

            def convert(self, source):
                captured["source"] = source
                return _FakeResult()

        class _FakeInputFormat:
            PDF = "pdf"

        monkeypatch.setattr(
            engine_module,
            "_load_docling_python_api",
            lambda: {
                "DocumentConverter": _FakeDocumentConverter,
                "PdfFormatOption": _FakePdfFormatOption,
                "PdfPipelineOptions": _FakePdfPipelineOptions,
                "InputFormat": _FakeInputFormat,
            },
        )

        backend = engine_module.DoclingPythonBackend()
        ctx = self._ctx(profile="math_heavy")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")

        result = backend.run(ctx)

        assert result.status == "ok"
        assert captured["source"] == str(ctx.raw_target)
        fake_option = captured["format_options"][_FakeInputFormat.PDF]
        assert fake_option.pipeline_options.do_formula_enrichment is True
        metadata = json.loads((tmp_path / "staging" / "markdown-auto" / "docling-python" / ctx.entry_id / "docling-python-run.json").read_text(encoding="utf-8"))
        assert metadata["formula_enrichment"] is True
        assert metadata["effective_source_pdf"] == str(ctx.raw_target)
        assert metadata["page_range_applied"] is False
        assert metadata["gpu_standard"]["enabled"] is False

    def test_docling_python_backend_applies_page_range_via_sliced_pdf(self, tmp_path, monkeypatch):
        class _FakePdfPipelineOptions:
            def __init__(self):
                self.do_formula_enrichment = False

        class _FakePdfFormatOption:
            def __init__(self, pipeline_options):
                self.pipeline_options = pipeline_options

        class _FakeDocument:
            def export_to_markdown(self):
                return "# converted"

        class _FakeResult:
            def __init__(self):
                self.document = _FakeDocument()

        captured = {}

        class _FakeDocumentConverter:
            def __init__(self, format_options):
                captured["format_options"] = format_options

            def convert(self, source):
                captured["source"] = source
                return _FakeResult()

        class _FakeInputFormat:
            PDF = "pdf"

        monkeypatch.setattr(
            engine_module,
            "_load_docling_python_api",
            lambda: {
                "DocumentConverter": _FakeDocumentConverter,
                "PdfFormatOption": _FakePdfFormatOption,
                "PdfPipelineOptions": _FakePdfPipelineOptions,
                "InputFormat": _FakeInputFormat,
            },
        )

        backend = engine_module.DoclingPythonBackend()
        ctx = self._ctx(profile="math_heavy", page_range="1-3")
        ctx.root_dir = tmp_path
        ctx.raw_target = tmp_path / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        ctx.raw_target.parent.mkdir(parents=True, exist_ok=True)
        ctx.raw_target.write_text("pdf", encoding="utf-8")
        sliced_pdf = tmp_path / "staging" / "markdown-auto" / "docling-python" / ctx.entry_id / "selected-pages.pdf"

        def _fake_prepare_docling_source(_ctx, _out_dir):
            return sliced_pdf, True

        monkeypatch.setattr(engine_module, "_prepare_docling_python_source_pdf", _fake_prepare_docling_source)

        result = backend.run(ctx)

        assert result.status == "ok"
        assert captured["source"] == str(sliced_pdf)
        metadata = json.loads((tmp_path / "staging" / "markdown-auto" / "docling-python" / ctx.entry_id / "docling-python-run.json").read_text(encoding="utf-8"))
        assert metadata["effective_source_pdf"] == str(sliced_pdf)
        assert metadata["page_range_requested"] == "1-3"
        assert metadata["page_range_applied"] is True
        assert metadata["selected_pages_count"] == 3

    def test_configure_docling_python_standard_gpu_sets_cuda_and_batches(self):
        class _FakeAcceleratorDevice:
            CUDA = type("CudaValue", (), {"value": "cuda"})()

        class _FakeAcceleratorOptions:
            def __init__(self, device):
                self.device = device

        class _FakeRapidOcrOptions:
            def __init__(self, backend):
                self.backend = backend

        class _FakePerf:
            page_batch_size = 4

        class _FakeSettings:
            perf = _FakePerf()

        class _FakePipelineOptions:
            accelerator_options = None
            ocr_batch_size = 0
            layout_batch_size = 0
            table_batch_size = 0
            ocr_options = None

        gpu = engine_module._configure_docling_python_standard_gpu(
            {
                "AcceleratorOptions": _FakeAcceleratorOptions,
                "AcceleratorDevice": _FakeAcceleratorDevice,
                "RapidOcrOptions": _FakeRapidOcrOptions,
                "settings": _FakeSettings(),
            },
            _FakePipelineOptions(),
        )

        assert gpu["enabled"] is True
        assert gpu["device"] == "cuda"
        assert gpu["ocr_batch_size"] == 8
        assert gpu["layout_batch_size"] == 8
        assert gpu["table_batch_size"] == 4
        assert gpu["page_batch_size"] == 8
        assert gpu["ocr_backend"] == "torch"


class TestExternalMarkdownSanitization:
    def test_repairs_common_utf8_mojibake_sequences(self):
        text = "IntroduÃ§Ã£o ao conteÃºdo: nÃ£o, revisÃ£o e equaÃ§Ãµes."
        repaired = _repair_mojibake_text(text)
        assert repaired == "Introdução ao conteúdo: não, revisão e equações."

    def test_leaves_valid_utf8_text_unchanged(self):
        text = "Introdução ao conteúdo: não, revisão e equações."
        assert _repair_mojibake_text(text) == text

    def test_sanitize_external_markdown_normalizes_newlines_after_repair(self):
        text = "## IntroduÃ§Ã£o\r\n\r\nTexto com revisÃ£o.\r"
        assert _sanitize_external_markdown_text(text) == "## Introdução\n\nTexto com revisão.\n"


class TestBacklogMarkdownStatus:
    def test_marks_staging_markdown_as_processed_only(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"base_markdown": "staging/markdown-auto/pymupdf4llm/item.md"}
        (tmp_path / "staging" / "markdown-auto" / "pymupdf4llm").mkdir(parents=True)
        (tmp_path / "staging" / "markdown-auto" / "pymupdf4llm" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Processado (só staging)"
        assert status["needs_reprocess"] == "true"

    def test_marks_curated_markdown_as_final(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"curated_markdown": "content/curated/item.md"}
        (tmp_path / "content" / "curated").mkdir(parents=True)
        (tmp_path / "content" / "curated" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Curado/final"
        assert status["needs_reprocess"] == "false"

    def test_marks_approved_markdown_as_approved_final(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_markdown_status

        entry = {"approved_markdown": "content/curated/item.md"}
        (tmp_path / "content" / "curated").mkdir(parents=True)
        (tmp_path / "content" / "curated" / "item.md").write_text("# x", encoding="utf-8")

        status = _resolve_backlog_markdown_status(entry, tmp_path)

        assert status["status"] == "Aprovado/final"
        assert status["needs_reprocess"] == "false"

    def test_loads_manual_unit_options_from_course_map(self, tmp_path):
        from src.ui.dialogs import _load_file_map_unit_options

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "COURSE_MAP.md").write_text(
            """# COURSE_MAP

| Unidade | Período | Slug |
|---|---|---|
| Unidade 01 — Métodos Formais | 02/03/2026 a 25/03/2026 | `unidade-01-metodos-formais` |
| Unidade 02 — Verificação de Programas | 27/04/2026 a 06/05/2026 | `unidade-02-verificacao-de-programas` |
""",
            encoding="utf-8",
        )

        options = _load_file_map_unit_options(repo)

        assert ("Unidade 01 — Métodos Formais (unidade-01-metodos-formais)", "unidade-01-metodos-formais") in options
        assert ("Unidade 02 — Verificação de Programas (unidade-02-verificacao-de-programas)", "unidade-02-verificacao-de-programas") in options

    def test_formats_effective_tag_summary_without_duplicates(self):
        from src.ui.dialogs import _format_backlog_tag_summary

        summary = _format_backlog_tag_summary(
            ["topico:funcoes-recursivas"],
            ["tipo:lista"],
            "topico:funcoes-recursivas, ferramenta:isabelle",
        )

        assert summary["manual"] == "topico:funcoes-recursivas"
        assert summary["auto"] == "tipo:lista"
        assert summary["effective"] == "topico:funcoes-recursivas, tipo:lista, ferramenta:isabelle"


class TestPdfImageExtractionPolicy:
    def _ctx(
        self,
        *,
        profile="math_heavy",
        page_count=116,
        images_count=290,
        suspected_scan=False,
        page_range="",
        extract_images=True,
    ):
        entry = FileEntry(
            source_path="C:/repo/raw/pdfs/material-de-aula/mlp.pdf",
            file_type="pdf",
            category="material-de-aula",
            title="MLP",
            document_profile=profile,
            page_range=page_range,
            extract_images=extract_images,
        )
        report = DocumentProfileReport(
            page_count=page_count,
            images_count=images_count,
            suggested_profile=profile,
            suspected_scan=suspected_scan,
        )
        return engine_module.BackendContext(
            Path("C:/repo"),
            Path("C:/repo/raw/pdfs/material-de-aula/mlp.pdf"),
            entry,
            report,
            stall_timeout=300,
        )

    def test_math_heavy_pdf_uses_permissive_image_policy(self):
        ctx = self._ctx(profile="math_heavy")
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "permissive"
        assert policy["keep_low_color"] is True

    def test_diagram_heavy_pdf_uses_balanced_image_policy(self):
        ctx = self._ctx(profile="diagram_heavy")
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "balanced"

    def test_scanned_pdf_uses_permissive_image_policy(self):
        ctx = self._ctx(profile="scanned", suspected_scan=True)
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "permissive"

    def test_auto_pdf_keeps_aggressive_noise_filter(self):
        ctx = self._ctx(profile="auto", page_count=20, images_count=3)
        policy = engine_module._pdf_image_extraction_policy(ctx)
        assert policy["mode"] == "standard"
        assert policy["keep_low_color"] is False

    def test_low_color_math_image_is_kept_by_permissive_policy(self, tmp_path, monkeypatch):
        ctx = self._ctx(profile="math_heavy")
        repo = tmp_path / "repo"
        raw_target = repo / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
        out_dir = repo / "staging" / "assets" / "images" / "mlp"
        raw_target.parent.mkdir(parents=True, exist_ok=True)
        raw_target.write_text("pdf", encoding="utf-8")

        builder = engine_module.RepoBuilder(repo, {}, [], {})

        class FakePage:
            @staticmethod
            def get_images(full=True):
                return [(17,)]

        class FakeDoc:
            page_count = 1

            def __getitem__(self, _idx):
                return FakePage()

            @staticmethod
            def extract_image(_xref):
                return {
                    "image": b"x" * 1500,
                    "width": 64,
                    "height": 64,
                    "ext": "png",
                }

            @staticmethod
            def close():
                return None

        monkeypatch.setattr(engine_module, "pymupdf", mock.Mock(open=lambda *_: FakeDoc()))
        monkeypatch.setattr(engine_module.RepoBuilder, "_is_noise_image", staticmethod(lambda _data: True))

        count = builder._extract_pdf_images(raw_target, out_dir, pages=[0], ctx=ctx)

        assert count == 1
        assert (out_dir / "page-001-img-01.png").exists()


class TestEntryImageSources:
    def test_entry_image_source_dirs_include_inline_and_extracted_assets(self, tmp_path):
        root = tmp_path / "repo"
        entry = {
            "id": "abc",
            "images_dir": "staging/assets/images/abc",
            "rendered_pages_dir": "content/images/scanned/abc",
        }

        dirs = engine_module._entry_image_source_dirs(root, entry)

        assert root / "staging" / "assets" / "inline-images" / "abc" in dirs
        assert root / "staging" / "assets" / "images" / "abc" in dirs
        assert root / "content" / "images" / "scanned" / "abc" in dirs

    def test_compact_manifest_keeps_images_dir_even_without_markdown_reference(self, tmp_path):
        repo = tmp_path / "repo"
        images_dir = repo / "staging" / "assets" / "images" / "entry-1"
        images_dir.mkdir(parents=True)
        builder = engine_module.RepoBuilder(repo, {}, [], {})

        manifest = {
            "entries": [
                {
                    "id": "entry-1",
                    "category": "material-de-aula",
                    "title": "Entry 1",
                    "images_dir": "staging/assets/images/entry-1",
                    "base_markdown": None,
                    "advanced_markdown": None,
                    "raw_target": None,
                }
            ]
        }

        result = builder._compact_manifest(manifest)

        assert len(result["entries"]) == 1
        assert result["entries"][0]["images_dir"] == "staging/assets/images/entry-1"


def test_parallel_image_extraction_runs_while_marker_remains_advanced_backend(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    raw_target = repo / "raw" / "pdfs" / "material-de-aula" / "mlp.pdf"
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    raw_target.write_bytes(b"%PDF-1.4")

    builder = engine_module.RepoBuilder(repo, {}, [], {})
    entry = FileEntry(
        source_path=str(raw_target),
        file_type="pdf",
        category="material-de-aula",
        title="MLP",
        document_profile="math_heavy",
        extract_images=True,
        preferred_backend="marker",
    )

    report = DocumentProfileReport(
        page_count=12,
        images_count=18,
        suggested_profile="math_heavy",
        suspected_scan=False,
    )
    decision = PipelineDecision(
        entry_id=entry.id(),
        processing_mode="auto",
        effective_profile="math_heavy",
        base_backend="pymupdf4llm",
        advanced_backend="marker",
        reasons=["profile:math_heavy"],
    )

    call_order = []

    monkeypatch.setattr(builder, "_profile_pdf", lambda *_args, **_kwargs: report)
    monkeypatch.setattr(builder.selector, "decide", lambda *_args, **_kwargs: decision)
    monkeypatch.setattr(
        builder.selector.backends["pymupdf4llm"],
        "run",
        lambda ctx: call_order.append("base") or engine_module.BackendRunResult(
            name="pymupdf4llm",
            layer="base",
            status="ok",
            markdown_path="staging/markdown-auto/pymupdf4llm/mlp.md",
        ),
    )
    monkeypatch.setattr(
        builder.selector.backends["marker"],
        "run",
        lambda ctx: call_order.append("marker") or engine_module.BackendRunResult(
            name="marker",
            layer="advanced",
            status="ok",
            markdown_path="staging/markdown-auto/marker/mlp.md",
            asset_dir="staging/markdown-auto/marker/mlp",
        ),
    )
    monkeypatch.setattr(builder, "_apply_math_normalization", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(engine_module, "HAS_PYMUPDF", True)
    monkeypatch.setattr(
        builder,
        "_extract_pdf_images",
        lambda pdf_path, out_dir, pages=None, ctx=None: call_order.append("images") or 3,
    )

    result = builder._process_pdf(entry, raw_target)

    assert result["base_backend"] == "pymupdf4llm"
    assert result["advanced_backend"] == "marker"
    assert result["images_dir"] == safe_rel(repo / "staging" / "assets" / "images" / entry.id(), repo)
    assert result["image_extraction"]["source"] == "pymupdf-pdf-images"
    assert result["image_extraction"]["mode"] == "permissive"
    assert call_order == ["base", "marker", "images"]


def test_process_url_writes_manual_review_to_web(tmp_path, monkeypatch):
    import urllib.request

    repo = tmp_path / "repo"
    repo.mkdir()

    builder = engine_module.RepoBuilder(repo, {}, [], {})
    entry = FileEntry(
        source_path="https://example.com/page",
        file_type="url",
        category="referencias",
        title="Example Page",
    )

    response = mock.MagicMock()
    response.read.return_value = b"<html><body><h1>Example</h1></body></html>"
    response.info.return_value.get_content_charset.return_value = "utf-8"
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: response)
    monkeypatch.setattr(
        engine_module,
        "_html_to_structured_markdown",
        lambda html, url, title: f"# {title}\n\nFonte: {url}\n",
    )

    result = builder._process_url(entry)
    manual_review = repo / result["manual_review"]

    assert result["base_backend"] == "url_fetcher"
    assert manual_review == repo / "manual-review" / "web" / f"{entry.id()}.md"
    assert manual_review.exists()
    assert "type: manual_url_review" in manual_review.read_text(encoding="utf-8")


def test_migrate_legacy_url_manual_reviews_moves_file_and_updates_manifest(tmp_path):
    repo = tmp_path / "repo"
    legacy_dir = repo / "manual-review" / "pdfs"
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "url-item.md"
    legacy_file.write_text(
        """---
id: url-item
title: Example
type: manual_pdf_review
base_backend: url_fetcher
---
legacy
""",
        encoding="utf-8",
    )
    manifest_path = repo / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "url-item",
                        "manual_review": "manual-review/pdfs/url-item.md",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    moved = engine_module.migrate_legacy_url_manual_reviews(repo)

    assert moved == 1
    assert not legacy_file.exists()
    migrated_file = repo / "manual-review" / "web" / "url-item.md"
    assert migrated_file.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["entries"][0]["manual_review"] == "manual-review/web/url-item.md"


    def test_resolves_backlog_unit_status_from_file_map(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_unit_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Unidade | Período |
|---|---|---|---|---|---|---|---|
| 1 | Exerciciosespecificacao | listas | praticar | alta | `exercises/lists/exerciciosespecificacao.md` | unidade-02-verificacao-de-programas | 27/04/2026 a 06/05/2026 |
""",
            encoding="utf-8",
        )

        status = _resolve_backlog_unit_status(
            {"title": "Exerciciosespecificacao", "category": "listas"},
            repo,
        )

        assert status["assigned"] == "unidade-02-verificacao-de-programas"
        assert status["source"] == "FILE_MAP atual"

    def test_resolves_backlog_unit_status_with_manual_override_pending_reprocess(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_unit_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Unidade | Período |
|---|---|---|---|---|---|---|---|
| 1 | Exerciciosespecificacao | listas | praticar | alta | `exercises/lists/exerciciosespecificacao.md` | unidade-01-metodos-formais | 04/03/2026 |
""",
            encoding="utf-8",
        )

        status = _resolve_backlog_unit_status(
            {
                "title": "Exerciciosespecificacao",
                "category": "listas",
                "manual_unit_slug": "unidade-02-verificacao-de-programas",
            },
            repo,
            {"unidade-02-verificacao-de-programas": "Unidade 02 — Verificação de Programas"},
        )

        assert status["assigned"] == "Unidade 02 — Verificação de Programas"
        assert status["source"] == "Override manual salvo"
        assert "reprocesse o repositório" in status["note"].lower()

    def test_resolves_backlog_timeline_status_from_timeline_index(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_timeline_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Unidade | Período |
|---|---|---|---|---|---|---|---|
| 1 | Exerciciosformalizacaoalgoritmosrecursao | listas | praticar | alta | `exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md` | unidade-01-metodos-formais | 11/03/2026 a 25/03/2026 |
""",
            encoding="utf-8",
        )
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "blocks": [
                        {
                            "id": "bloco-02",
                            "period_label": "11/03/2026 a 25/03/2026",
                            "unit_slug": "unidade-01-metodos-formais",
                            "topics": ["definições indutivas", "funções recursivas"],
                            "aliases": ["indução", "recursão"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        status = _resolve_backlog_timeline_status(
            {"title": "Exerciciosformalizacaoalgoritmosrecursao", "category": "listas"},
            repo,
        )

        assert status["period"] == "11/03/2026 a 25/03/2026"
        assert status["block"] == "bloco-02"
        assert "funções recursivas" in status["topics"]

    def test_resolves_backlog_timeline_status_from_current_file_map_layout(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_timeline_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Exerciciosformalizacaoalgoritmosrecursao | listas | praticar | alta | `exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md` | Definições indutivas | unidade-01-metodos-formais | Alta | 11/03/2026 a 25/03/2026 |
|  | ↳ rastreabilidade |  | raw: `raw/aula.pdf` |  |  |  |  |  |  |
""",
            encoding="utf-8",
        )
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "blocks": [
                        {
                            "id": "bloco-02",
                            "period_label": "11/03/2026 a 25/03/2026",
                            "unit_slug": "unidade-01-metodos-formais",
                            "topics": ["definições indutivas", "funções recursivas"],
                            "aliases": ["indução", "recursão"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        status = _resolve_backlog_timeline_status(
            {"title": "Exerciciosformalizacaoalgoritmosrecursao", "category": "listas"},
            repo,
        )

        assert status["period"] == "11/03/2026 a 25/03/2026"
        assert status["block"] == "bloco-02"
        assert "recursão" in status["aliases"]

    def test_resolves_backlog_timeline_status_with_manual_block_pending_reprocess(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_timeline_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        course_dir.mkdir(parents=True)
        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Unidade | Período |
|---|---|---|---|---|---|---|---|
| 1 | Exerciciosformalizacaoalgoritmosrecursao | listas | praticar | alta | `exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md` | unidade-01-metodos-formais | 04/03/2026 |
""",
            encoding="utf-8",
        )
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "blocks": [
                        {
                            "id": "bloco-02",
                            "period_label": "16/03/2026 a 25/03/2026",
                            "unit_slug": "unidade-01-metodos-formais",
                            "topics": ["definições indutivas", "funções recursivas"],
                            "aliases": ["indução", "recursão"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        status = _resolve_backlog_timeline_status(
            {
                "title": "Exerciciosformalizacaoalgoritmosrecursao",
                "category": "listas",
                "manual_timeline_block_id": "bloco-02",
            },
            repo,
        )

        assert status["period"] == "16/03/2026 a 25/03/2026"
        assert status["block"] == "bloco-02"
        assert "reprocesse o repositório" in status["note"].lower()

    def test_resolves_backlog_timeline_status_prefers_best_matching_block_within_same_unit(self, tmp_path):
        from src.ui.dialogs import _resolve_backlog_timeline_status

        repo = tmp_path / "repo"
        course_dir = repo / "course"
        exercises_dir = repo / "exercises" / "lists"
        course_dir.mkdir(parents=True)
        exercises_dir.mkdir(parents=True)

        (course_dir / "FILE_MAP.md").write_text(
            """# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Lista Isabelle | listas | praticar | alta | `exercises/lists/lista-isabelle.md` | Prova de teoremas | unidade-01-metodos-formais | Alta | 01/04/2026 a 10/04/2026 |
""",
            encoding="utf-8",
        )
        (exercises_dir / "lista-isabelle.md").write_text(
            "# Lista Isabelle\n\nExercícios de prova de teoremas usando Isabelle.\n",
            encoding="utf-8",
        )
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "blocks": [
                        {
                            "id": "bloco-recursao",
                            "period_label": "01/04/2026 a 03/04/2026",
                            "period_start": "2026-04-01",
                            "period_end": "2026-04-03",
                            "unit_slug": "unidade-01-metodos-formais",
                            "topics": ["funções recursivas", "indução"],
                            "aliases": ["recursão"],
                            "primary_topic_label": "Funções Recursivas",
                            "primary_topic_confidence": 0.95,
                        },
                        {
                            "id": "bloco-isabelle",
                            "period_label": "06/04/2026 a 08/04/2026",
                            "period_start": "2026-04-06",
                            "period_end": "2026-04-08",
                            "unit_slug": "unidade-01-metodos-formais",
                            "topics": ["prova de teoremas", "isabelle"],
                            "aliases": ["theorem proving", "isabelle"],
                            "primary_topic_label": "Prova de Teoremas - Isabelle",
                            "primary_topic_confidence": 0.98,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        status = _resolve_backlog_timeline_status(
            {
                "title": "Lista Isabelle",
                "category": "listas",
                "approved_markdown": "exercises/lists/lista-isabelle.md",
            },
            repo,
        )

        assert status["block"] == "bloco-isabelle"
        assert status["period"] == "06/04/2026 a 08/04/2026"
        assert "isabelle" in status["topics"].lower() or "isabelle" in status["aliases"].lower()


class TestNotebookCompaction:
    def test_compacts_ipynb_into_jupyter_markdown(self):
        raw = json.dumps({
            "cells": [
                {"cell_type": "markdown", "source": ["# Título\n", "Resumo curto."]},
                {"cell_type": "code", "source": ["print('oi')"], "outputs": [{"text": ["oi\n"]}]},
            ]
        })
        lang, content = _compact_notebook_markdown(raw)
        assert lang == "jupyter"
        assert "## Célula 1 — Markdown" in content
        assert "## Célula 2 — Código" in content
        assert "```python" in content
        assert "**Saída:**" in content


class TestInstructionCutover:
    def test_claude_instructions_no_longer_ask_tutor_to_fill_file_map_manually(self):
        text = generate_claude_project_instructions(
            {"course_name": "Métodos Formais"},
            first_session_pending=True,
        )

        assert "preencha a coluna **Unidade**" not in text
        assert "reprocessar repositório" in text.lower()
        assert "backlog" in text.lower()


# ---------------------------------------------------------------------------
# parse_page_range
# ---------------------------------------------------------------------------

class TestParsePageRange:
    def test_empty_string(self):
        assert parse_page_range("") is None

    def test_none_input(self):
        assert parse_page_range(None) is None

    def test_whitespace_only(self):
        assert parse_page_range("   ") is None

    def test_single_page_one_based(self):
        # "3" is one-based → returns [2] (zero-based)
        assert parse_page_range("3") == [2]

    def test_range_one_based(self):
        assert parse_page_range("1-3") == [0, 1, 2]

    def test_comma_separated_one_based(self):
        assert parse_page_range("1, 3, 5") == [0, 2, 4]

    def test_mixed_range_and_individual(self):
        assert parse_page_range("2, 5-7") == [1, 4, 5, 6]

    def test_zero_based_explicit(self):
        # "0,2,4" has a zero → treat as zero-based
        assert parse_page_range("0,2,4") == [0, 2, 4]

    def test_reversed_range(self):
        assert parse_page_range("5-3") == [2, 3, 4]

    def test_duplicates_removed(self):
        result = parse_page_range("1,1,2,2")
        assert result == [0, 1]

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError):
            parse_page_range("abc")

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError):
            parse_page_range("a-b")


# ---------------------------------------------------------------------------
# pages_to_marker_range
# ---------------------------------------------------------------------------

class TestPagesToMarkerRange:
    def test_none(self):
        assert pages_to_marker_range(None) is None

    def test_empty(self):
        assert pages_to_marker_range([]) is None

    def test_single_page(self):
        assert pages_to_marker_range([3]) == "3"

    def test_consecutive_range(self):
        assert pages_to_marker_range([0, 1, 2, 3]) == "0-3"

    def test_non_consecutive(self):
        assert pages_to_marker_range([0, 2, 4]) == "0,2,4"

    def test_mixed(self):
        assert pages_to_marker_range([0, 1, 2, 5, 7, 8]) == "0-2,5,7-8"


class TestBuildMarkerPageChunks:
    def test_full_document_is_split_into_20_page_chunks(self):
        chunks = _build_marker_page_chunks(None, page_count=60, chunk_size=20)
        assert chunks == [
            list(range(0, 20)),
            list(range(20, 40)),
            list(range(40, 60)),
        ]

    def test_selected_pages_are_chunked_without_reordering(self):
        chunks = _build_marker_page_chunks([0, 1, 2, 25, 26, 27], page_count=100, chunk_size=3)
        assert chunks == [
            [0, 1, 2],
            [25, 26, 27],
        ]


# ---------------------------------------------------------------------------
# file_size_mb
# ---------------------------------------------------------------------------

class TestFileSizeMb:
    def test_nonexistent_file(self):
        assert file_size_mb(Path("/nonexistent/file.pdf")) == 0.0

    def test_real_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("x" * (1024 * 1024))  # 1 MB
        assert file_size_mb(f) >= 1.0


# ---------------------------------------------------------------------------
# safe_rel
# ---------------------------------------------------------------------------

class TestSafeRel:
    def test_none_path(self):
        assert safe_rel(None, Path("/root")) is None

    def test_relative(self):
        root = Path("/root/project")
        child = Path("/root/project/sub/file.txt")
        assert safe_rel(child, root) == "sub/file.txt"

    def test_outside_root(self):
        root = Path("/root/project")
        outside = Path("/other/file.txt")
        result = safe_rel(outside, root)
        assert result is not None
        assert "file.txt" in result


# ---------------------------------------------------------------------------
# ensure_dir / write_text
# ---------------------------------------------------------------------------

class TestEnsureDirAndWriteText:
    def test_ensure_dir_creates_parents(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        result = ensure_dir(deep)
        assert result.exists()
        assert result.is_dir()

    def test_write_text_creates_file(self, tmp_path):
        target = tmp_path / "sub" / "file.md"
        write_text(target, "hello world")
        assert target.read_text(encoding="utf-8") == "hello world"


# ---------------------------------------------------------------------------
# wrap_frontmatter
# ---------------------------------------------------------------------------

class TestWrapFrontmatter:
    def test_basic(self):
        result = wrap_frontmatter({"title": "Test"}, "Body content")
        assert result.startswith("---\n")
        assert "title:" in result
        assert "Body content" in result
        assert result.endswith("\n")


# ---------------------------------------------------------------------------
# rows_to_markdown_table
# ---------------------------------------------------------------------------

class TestRowsToMarkdownTable:
    def test_empty(self):
        assert rows_to_markdown_table([]) == ""

    def test_basic_table(self):
        rows = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        result = rows_to_markdown_table(rows)
        assert "| Name | Age |" in result
        assert "| --- | --- |" in result
        assert "| Alice | 30 |" in result

    def test_uneven_rows(self):
        rows = [["A", "B", "C"], ["x"]]
        result = rows_to_markdown_table(rows)
        lines = result.strip().split("\n")
        assert len(lines) == 3  # header, separator, one data row


# ---------------------------------------------------------------------------
# URL fetcher markdown formatting
# ---------------------------------------------------------------------------

class TestUrlFetcherMarkdownFormatting:
    def test_html_is_rendered_as_structured_markdown(self):
        pytest.importorskip("bs4")

        html = """
        <html>
          <head>
            <title>Minha Pagina</title>
            <meta name="description" content="Resumo curto da pagina." />
          </head>
          <body>
            <article>
              <h1>Titulo Principal</h1>
              <p>Primeiro paragrafo com <a href="https://example.com/ref">link</a>.</p>
              <ul>
                <li>Item A</li>
                <li>Item B</li>
              </ul>
              <pre>print("oi")</pre>
              <table>
                <tr><th>Coluna</th><th>Valor</th></tr>
                <tr><td>A</td><td>1</td></tr>
              </table>
            </article>
          </body>
        </html>
        """

        md = _html_to_structured_markdown(html, "https://example.com/aula", "Titulo Manual")

        assert md.startswith("# Titulo Manual")
        assert "Resumo curto da pagina." in md
        assert "- URL: [https://example.com/aula](https://example.com/aula)" in md
        assert "## Conteúdo Extraído" in md
        assert "# Titulo Principal" in md
        assert "Primeiro paragrafo com [link](https://example.com/ref)." in md
        assert "- Item A" in md
        assert "```text" in md
        assert '| Coluna | Valor |' in md

    def test_prefers_main_content_over_sidebar_and_footer(self):
        pytest.importorskip("bs4")

        html = """
        <html>
          <body>
            <div class="sidebar">
              <p>Home</p>
              <p>Produtos</p>
              <p>Contato</p>
            </div>
            <div id="main-content">
              <h1>Aula 5</h1>
              <p>Este é o conteúdo principal da página com explicação suficiente para vencer o menu lateral.</p>
              <p>Segundo parágrafo com mais detalhes, exemplos e contexto pedagógico para a disciplina.</p>
            </div>
            <footer>
              <p>Política de privacidade</p>
            </footer>
          </body>
        </html>
        """

        md = _html_to_structured_markdown(html, "https://example.com/aula-5", "Aula 5")

        assert "# Aula 5" in md
        assert "Este é o conteúdo principal da página" in md
        assert "Segundo parágrafo com mais detalhes" in md
        assert "Política de privacidade" not in md
        assert "Home" not in md


# ---------------------------------------------------------------------------
# FileEntry
# ---------------------------------------------------------------------------

class TestFileEntry:
    def test_id_generation(self):
        entry = FileEntry(
            source_path="/path/to/My Document.pdf",
            file_type="pdf",
            category="course-material",
            title="My Document",
        )
        assert entry.id() == "my-document"

    def test_default_values(self):
        entry = FileEntry(
            source_path="/path/to/test.pdf",
            file_type="pdf",
            category="exams",
            title="Test",
        )
        assert entry.processing_mode == "auto"


class TestPendingOperation:
    def test_roundtrip_serialization(self):
        entry = FileEntry(
            source_path="/tmp/a.pdf",
            file_type="pdf",
            category="provas",
            title="A",
        )
        op = PendingOperation(
            operation_type="build",
            requested_mode="full",
            repo_root="/tmp/repo",
            course_meta={"course_name": "Calculo I"},
            active_subject="Calculo I",
            selected_entry_source="/tmp/a.pdf",
            entries=[entry],
            created_at="2026-03-25T10:00:00",
        )

        restored = PendingOperation.from_dict(op.to_dict())

        assert restored.operation_type == "build"
        assert restored.repo_root == "/tmp/repo"
        assert restored.active_subject == "Calculo I"
        assert len(restored.entries) == 1
        assert restored.entries[0].title == "A"
        assert entry.document_profile == "auto"
        assert entry.preferred_backend == "auto"
        assert entry.include_in_bundle is True
        assert entry.relevant_for_exam is True


class TestQueueManifestReconciliation:
    def test_prune_processed_queue_entries_removes_manifest_sources(self, tmp_path):
        from src.ui.app import _prune_entries_against_manifest

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "manifest.json").write_text(
            json.dumps({
                "entries": [
                    {"source_path": str(repo / "raw" / "pdfs" / "a.pdf")},
                ]
            }),
            encoding="utf-8",
        )

        entries = [
            FileEntry(source_path=str(repo / "raw" / "pdfs" / "a.pdf"), file_type="pdf", category="material-de-aula", title="A"),
            FileEntry(source_path=str(repo / "raw" / "pdfs" / "b.pdf"), file_type="pdf", category="material-de-aula", title="B"),
        ]

        remaining = _prune_entries_against_manifest(entries, repo)

        assert [entry.title for entry in remaining] == ["B"]

    def test_restore_pending_operation_context_drops_processed_entries(self, tmp_path):
        from src.ui.app import _prune_entries_against_manifest

        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "manifest.json").write_text(
            json.dumps({
                "entries": [
                    {"source_path": str(repo / "raw" / "pdfs" / "done.pdf")},
                ]
            }),
            encoding="utf-8",
        )

        op = PendingOperation(
            operation_type="build",
            requested_mode="incremental",
            repo_root=str(repo),
            entries=[
                FileEntry(source_path=str(repo / "raw" / "pdfs" / "done.pdf"), file_type="pdf", category="material-de-aula", title="Done"),
                FileEntry(source_path=str(repo / "raw" / "pdfs" / "todo.pdf"), file_type="pdf", category="material-de-aula", title="Todo"),
            ],
        )

        remaining = _prune_entries_against_manifest(op.entries, repo)

        assert [entry.title for entry in remaining] == ["Todo"]


def test_app_build_options_include_sleep_prevention():
    from src.ui.app import _build_options_from_config

    config_obj = mock.Mock(
        get=lambda key, default=None: {
            "image_format": "png",
            "stall_timeout": 300,
            "marker_torch_device": "cuda",
            "prevent_sleep_during_build": True,
        }.get(key, default)
    )

    options = _build_options_from_config("auto", "por,eng", config_obj)

    assert options["prevent_sleep_during_build"] is True
    assert options["marker_torch_device"] == "cuda"


def test_file_entry_preserves_datalab_mode_roundtrip():
    entry = FileEntry(
        source_path="/test.pdf",
        file_type="pdf",
        category="material-de-aula",
        title="Test",
        preferred_backend="datalab",
        datalab_mode="balanced",
    )

    restored = FileEntry.from_dict(entry.to_dict())

    assert restored.preferred_backend == "datalab"
    assert restored.datalab_mode == "balanced"


# ---------------------------------------------------------------------------
# BackendSelector
# ---------------------------------------------------------------------------

class TestBackendSelector:
    def test_auto_mode_math_heavy_prefers_datalab_when_available(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="math_heavy")
        with mock.patch.object(
            BackendSelector,
            "available_backends",
            return_value={"pymupdf4llm": True, "pymupdf": True, "datalab": True, "docling": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "datalab"

    def test_auto_mode_diagram_heavy_prefers_docling_when_available(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="diagram_heavy")
        with mock.patch.object(
            BackendSelector,
            "available_backends",
            return_value={"pymupdf4llm": True, "pymupdf": True, "docling": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "docling"

    def test_quick_mode_selects_base_only(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="quick",
        )
        report = DocumentProfileReport(suggested_profile="auto")
        decision = selector.decide(entry, report)
        assert decision.processing_mode == "quick"
        assert decision.advanced_backend is None

    def test_auto_mode_auto_no_advanced(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="auto")
        decision = selector.decide(entry, report)
        assert decision.advanced_backend is None

    def test_auto_mode_math_heavy_tries_advanced(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="math_heavy")
        decision = selector.decide(entry, report)
        # Even if no advanced backend is available, the logic should try
        assert decision.effective_profile == "math_heavy"

    def test_formula_priority_activates_advanced(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="quick",
            formula_priority=True,
        )
        report = DocumentProfileReport(suggested_profile="auto")
        decision = selector.decide(entry, report)
        available = selector.available_backends()
        has_advanced = available.get("datalab") or available.get("docling") or available.get("marker")
        if has_advanced:
            assert decision.advanced_backend is not None
            assert "formula_priority" in " ".join(decision.reasons)
        else:
            # No advanced backend installed; formula_priority cannot activate one
            assert decision.advanced_backend is None

    def test_available_backends_returns_dict(self):
        selector = BackendSelector()
        available = selector.available_backends()
        assert isinstance(available, dict)
        assert "pymupdf4llm" in available
        assert "pymupdf" in available
        assert "datalab" in available
        assert "docling" in available
        assert "docling_python" in available
        assert "marker" in available

    def test_manual_preferred_docling_python_is_respected(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
            preferred_backend="docling_python",
        )
        report = DocumentProfileReport(suggested_profile="math_heavy")
        with mock.patch.object(
            BackendSelector,
            "available_backends",
            return_value={"pymupdf4llm": True, "pymupdf": True, "docling": True, "docling_python": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "docling_python"

    def test_manual_preferred_datalab_is_respected(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
            preferred_backend="datalab",
        )
        report = DocumentProfileReport(suggested_profile="math_heavy")
        with mock.patch.object(
            BackendSelector,
            "available_backends",
            return_value={"pymupdf4llm": True, "pymupdf": True, "datalab": True, "docling": True, "docling_python": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "datalab"


# ---------------------------------------------------------------------------
# DocumentProfileReport
# ---------------------------------------------------------------------------

class TestDocumentProfileReport:
    def test_defaults(self):
        report = DocumentProfileReport()
        assert report.page_count == 0
        assert report.suggested_profile == "auto"
        assert report.suspected_scan is False

    def test_serializable(self):
        report = DocumentProfileReport(page_count=5, text_chars=1000)
        data = asdict(report)
        json_output = json.dumps(data)
        assert '"page_count": 5' in json_output


# ---------------------------------------------------------------------------
# _parse_units_from_teaching_plan
# ---------------------------------------------------------------------------

PUCRS_PLAN = """
N°. DA UNIDADE: 01
CONTEÚDO: Métodos Formais
1.1. Sistemas Formais
1.2. Linguagens de Especificação e Lógicas
1.2.1. Fundamentos de Lógica de Primeira Ordem
1.3. Abordagens para Verificação Formal

N°. DA UNIDADE: 02
CONTEÚDO: Verificação de Programas
2.1. Lógica de Hoare
2.1.1. Pré e Pós Condições
2.2. Softwares de Suporte

N°. DA UNIDADE: 03
CONTEÚDO: Verificação de Modelos
3.1. Máquinas de Estado
3.2. Fundamentos de Lógicas Temporais

PROCEDIMENTOS METODOLÓGICOS
Texto que não deve ser parseado.
"""

GENERIC_PLAN = """
### Unidade 1 — Fundamentos
- Lógica proposicional
- Conjuntos indutivos

### Unidade 2 — Verificação
- Lógica de Hoare
- Dafny

### Unidade 3 — Modelos
- Model checking
- TLA+
"""

PUCRS_PLAN_WITH_MARKDOWN_SECTIONS = """
N°. DA UNIDADE: 01
CONTEÚDO: Métodos Formais
1.1. Sistemas Formais
1.2. Linguagens de Especificação e Lógicas

## **PROCEDIMENTOS METODOLÓGICOS**
Texto que não deve ser parseado.

## **AVALIAÇÃO**
Outro texto que não deve ser parseado.
"""

LEARNING_UNIT_PLAN = """
Unidade de Aprendizagem 1: Visão Geral (5%)
Conceituação
Breve Histórico de IA
Subáreas e disciplinas afins

Unidade de Aprendizagem 2: Solução de Problemas (10%)
Introdução a agentes em ambientes determinísticos
Representação de problemas
Busca informada (heurística)

AVALIAÇÃO:
Texto que não deve ser parseado.
"""

ASSESSMENT_CONFLICT_PLAN = """
N°. DA UNIDADE: 01
CONTEÚDO: Métodos Formais
1.1. Sistemas Formais
1.2. Linguagens de Especificação e Lógicas
1.3. Abordagens para Verificação Formal
1.3.3. Provadores de Teoremas

N°. DA UNIDADE: 02
CONTEÚDO: Verificação de Programas
2.1. Lógica de Hoare
2.1.1. Pré e Pós Condições
2.2. Softwares de Suporte

AVALIAÇÃO:
P1: Prova individual abrangendo as unidades 1 e 2

BIBLIOGRAFIA
"""

ASSESSMENT_CONFLICT_SYLLABUS = """
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-02 | Unidade 1: Métodos Formais |
| 2 | 2026-03-09 | Continuação Unidade 1 |
| 3 | 2026-03-16 | Provadores de Teoremas - Isabelle |
| 4 | 2026-03-23 | Revisão |
| 5 | 2026-04-22 | P1 |
| 6 | 2026-04-27 | Unidade 2: Lógica de Hoare |
| 7 | 2026-05-04 | Continuação Unidade 2 |
"""


class TestParseUnitsFromTeachingPlan:
    def test_pucrs_format_detects_three_units(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        assert len(units) == 3

    def test_pucrs_format_unit_titles(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        titles = [u[0] for u in units]
        assert any("Métodos Formais" in t for t in titles)
        assert any("Verificação de Programas" in t for t in titles)
        assert any("Verificação de Modelos" in t for t in titles)

    def test_pucrs_format_extracts_topics(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        topics_u1 = [_topic_text(t) for t in units[0][1]]
        assert any("Sistemas Formais" in t for t in topics_u1)
        assert any("Lógica de Primeira Ordem" in t for t in topics_u1)

    def test_pucrs_stops_at_procedimentos(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        all_topics = [_topic_text(t) for _, topics in units for t in topics]
        assert not any("não deve" in t for t in all_topics)

    def test_pucrs_stops_at_markdown_section_heading(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN_WITH_MARKDOWN_SECTIONS)
        all_topics = [_topic_text(t) for _, topics in units for t in topics]
        assert "Sistemas Formais" in all_topics
        assert not any("PROCEDIMENTOS" in t for t in all_topics)
        assert not any("AVALIAÇÃO" in t for t in all_topics)

    def test_generic_markdown_detects_three_units(self):
        units = _parse_units_from_teaching_plan(GENERIC_PLAN)
        assert len(units) == 3

    def test_generic_markdown_strips_hashes_from_title(self):
        units = _parse_units_from_teaching_plan(GENERIC_PLAN)
        for title, _ in units:
            assert not title.startswith("#")

    def test_generic_markdown_extracts_bullet_topics(self):
        units = _parse_units_from_teaching_plan(GENERIC_PLAN)
        topics_u1 = [_topic_text(t) for t in units[0][1]]
        assert "Lógica proposicional" in topics_u1
        assert "Conjuntos indutivos" in topics_u1

    def test_learning_unit_format_detects_units(self):
        units = _parse_units_from_teaching_plan(LEARNING_UNIT_PLAN)
        assert len(units) == 2
        assert "Visão Geral" in units[0][0]
        assert "Solução de Problemas" in units[1][0]

    def test_learning_unit_format_extracts_plain_topics(self):
        units = _parse_units_from_teaching_plan(LEARNING_UNIT_PLAN)
        topics_u1 = [_topic_text(t) for t in units[0][1]]
        assert "Conceituação" in topics_u1
        assert "Breve Histórico de IA" in topics_u1
        assert "Subáreas e disciplinas afins" in topics_u1

    def test_empty_string_returns_empty(self):
        assert _parse_units_from_teaching_plan("") == []

    def test_no_units_returns_empty(self):
        assert _parse_units_from_teaching_plan("Texto sem unidades aqui.") == []

    # ── Hierarchy / depth tests ──────────────────────────────────────

    def test_pucrs_topics_are_tuples(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        for _, topics in units:
            for topic in topics:
                assert isinstance(topic, tuple), f"Expected tuple, got {type(topic)}"
                assert len(topic) == 2

    def test_pucrs_depth_main_topic(self):
        """1.1. Sistemas Formais → depth 0 (tópico principal)"""
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        topics_u1 = units[0][1]
        sistemas = [t for t in topics_u1 if _topic_text(t) == "Sistemas Formais"]
        assert len(sistemas) == 1
        assert _topic_depth(sistemas[0]) == 0

    def test_pucrs_depth_subtopic(self):
        """1.2.1. Fundamentos de Lógica de Primeira Ordem → depth 1 (sub-tópico)"""
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        topics_u1 = units[0][1]
        fundamentos = [t for t in topics_u1 if "Lógica de Primeira Ordem" in _topic_text(t)]
        assert len(fundamentos) == 1
        assert _topic_depth(fundamentos[0]) == 1

    def test_pucrs_depth_second_unit(self):
        """2.1.1. Pré e Pós Condições → depth 1"""
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        topics_u2 = units[1][1]
        pre_pos = [t for t in topics_u2 if "Pré e Pós Condições" in _topic_text(t)]
        assert len(pre_pos) == 1
        assert _topic_depth(pre_pos[0]) == 1

    def test_generic_bullets_depth_zero(self):
        """Marcadores genéricos (-, •) → depth 0"""
        units = _parse_units_from_teaching_plan(GENERIC_PLAN)
        for _, topics in units:
            for topic in topics:
                assert _topic_depth(topic) == 0

    def test_topic_text_helper_with_tuple(self):
        assert _topic_text(("Foo", 2)) == "Foo"

    def test_topic_text_helper_with_string(self):
        assert _topic_text("Bar") == "Bar"

    def test_topic_depth_helper_with_tuple(self):
        assert _topic_depth(("Foo", 3)) == 3

    def test_topic_depth_helper_with_string(self):
        assert _topic_depth("Bar") == 0

# ---------------------------------------------------------------------------
# _parse_bibliography_from_teaching_plan
# ---------------------------------------------------------------------------

BIB_PLAN = """
CONTEÚDO ANTERIOR

BIBLIOGRAFIA

BÁSICA:
1. HUTH, M. R. A; RYAN, M. D. Lógica em Ciência da Computação. 2ª ed. LTC, 2008.
2. MONIN, J.F. Understanding Formal Methods. Springer Verlag, 2003.
3. KRÖGER, F.; MERZ, S. Temporal Logic and State Systems. Springer, 2008.

COMPLEMENTAR:
1. ALMEIDA, J. B. et al. Rigorous Software Development. Springer-Verlag, 2011.
2. KOURIE, D.G; WATSON, B.W. The correctness-by-construction approach. Springer, 2012.
"""


class TestParseBibliographyFromTeachingPlan:
    def test_detects_three_basic_refs(self):
        result = _parse_bibliography_from_teaching_plan(BIB_PLAN)
        assert len(result["basica"]) == 3

    def test_detects_two_complementar_refs(self):
        result = _parse_bibliography_from_teaching_plan(BIB_PLAN)
        assert len(result["complementar"]) == 2

    def test_basic_ref_content(self):
        result = _parse_bibliography_from_teaching_plan(BIB_PLAN)
        assert any("HUTH" in r for r in result["basica"])
        assert any("MONIN" in r for r in result["basica"])

    def test_complementar_ref_content(self):
        result = _parse_bibliography_from_teaching_plan(BIB_PLAN)
        assert any("ALMEIDA" in r for r in result["complementar"])

    def test_no_bibliografia_section_returns_empty(self):
        result = _parse_bibliography_from_teaching_plan("Texto sem bibliografia.")
        assert result["basica"] == []
        assert result["complementar"] == []

    def test_empty_string_returns_empty(self):
        result = _parse_bibliography_from_teaching_plan("")
        assert result["basica"] == []
        assert result["complementar"] == []


# ---------------------------------------------------------------------------
# _parse_syllabus_timeline / _match_timeline_to_units
# ---------------------------------------------------------------------------

SYLLABUS_TABLE = """\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-02 | Apresentação e Unidade 1: Métodos Formais |
| 2 | 2026-03-09 | Continuação Unidade 1 |
| 3 | 2026-03-16 | Unidade 1 — finalização |
| 4 | 2026-03-23 | Unidade 2: Verificação de Programas |
| 5 | 2026-03-30 | Continuação Unidade 2 |
| 6 | 2026-04-06 | Unidade 3: Verificação de Modelos |
| 7 | 2026-04-13 | Continuação Unidade 3 |
| 8 | 2026-04-20 | Revisão |
| 9 | 2026-04-27 | P1 |
"""

class TestParseSyllabusTimeline:
    def test_parses_markdown_table(self):
        rows = _parse_syllabus_timeline(SYLLABUS_TABLE)
        assert len(rows) == 9
        assert rows[0]["semana"] == "1"
        assert rows[0]["data"] == "2026-03-02"

    def test_empty_input(self):
        assert _parse_syllabus_timeline("") == []
        assert _parse_syllabus_timeline(None) == []

    def test_no_table(self):
        assert _parse_syllabus_timeline("Texto sem tabela nenhuma.") == []

    def test_column_names_normalized(self):
        rows = _parse_syllabus_timeline(SYLLABUS_TABLE)
        for row in rows:
            for key in row:
                assert key == key.lower()


class TestMatchTimelineToUnits:
    def test_matches_units_to_timeline(self):
        timeline = _parse_syllabus_timeline(SYLLABUS_TABLE)
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        mapping = _match_timeline_to_units(timeline, units)

        assert len(mapping) == 3  # 3 units
        # Unit 1 should match weeks 1-3
        u1 = mapping[0]
        assert "Métodos Formais" in u1["unit_title"]
        assert u1["period"]  # should have date range
        assert "2026-03-02" in u1["dates"]

    def test_unit_2_matched(self):
        timeline = _parse_syllabus_timeline(SYLLABUS_TABLE)
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        mapping = _match_timeline_to_units(timeline, units)
        u2 = mapping[1]
        assert "Verificação de Programas" in u2["unit_title"]
        assert "2026-03-23" in u2["dates"]

    def test_period_uses_readable_interval(self):
        timeline = _parse_syllabus_timeline(SYLLABUS_TABLE)
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        mapping = _match_timeline_to_units(timeline, units)
        u2 = mapping[1]
        assert u2["period"] == "2026-03-23 a 2026-03-30"

    def test_slug_generated(self):
        timeline = _parse_syllabus_timeline(SYLLABUS_TABLE)
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        mapping = _match_timeline_to_units(timeline, units)
        for m in mapping:
            assert m["unit_slug"]
            assert " " not in m["unit_slug"]

    def test_empty_inputs(self):
        assert _match_timeline_to_units([], []) == []
        assert _match_timeline_to_units([], [("Unit 1", [])]) == []

    def test_matches_by_distinctive_topics_with_accent_normalization(self):
        timeline = _parse_syllabus_timeline("""\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-02 | Introdução e visão geral |
| 2 | 2026-03-09 | Pré e pós condições; invariantes de laço |
| 3 | 2026-03-16 | Modelos de Kripke e lógica temporal |
""")
        units = [
            ("Unidade 01 — Verificação de Programas", [
                "Lógica de Hoare",
                "Pré e Pós Condições",
                "Invariante e Variante de Laço",
            ]),
            ("Unidade 02 — Verificação de Modelos", [
                "Modelos de Kripke",
                "Lógica Temporal Linear",
            ]),
        ]

        mapping = _match_timeline_to_units(timeline, units)

        assert mapping[0]["period"] == "2026-03-09"
        assert "2026-03-16" not in mapping[0]["dates"]
        assert mapping[1]["period"] == "2026-03-16"

    def test_segmented_periods_do_not_overlap_between_units(self):
        timeline = _parse_syllabus_timeline("""\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-04-27 | Lógica de Hoare |
| 2 | 2026-04-29 | Lógica de Hoare |
| 3 | 2026-05-04 | Exercícios |
| 4 | 2026-05-06 | Correção parcial e total |
| 5 | 2026-05-11 | Dafny |
| 6 | 2026-06-15 | Modelos de Kripke |
""")
        units = [
            ("Unidade 01 — Métodos Formais", ["Sistemas Formais"]),
            ("Unidade 02 — Verificação de Programas", [
                "Lógica de Hoare",
                "Correção Parcial e Total",
                "Softwares de Suporte à Verificação Formal de Programas",
            ]),
            ("Unidade 03 — Verificação de Modelos", ["Modelos de Kripke"]),
        ]

        mapping = _match_timeline_to_units(timeline, units)

        assert mapping[1]["period"] == "2026-04-27 a 2026-05-11"
        assert mapping[2]["period"] == "2026-06-15"


class TestTimelineIndex:
    def test_build_timeline_index_groups_related_rows_into_blocks(self):
        timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
        candidate_rows = _build_timeline_candidate_rows(timeline)
        unit_index = _build_file_map_unit_index(METODOS_FORMAIS_UNITS)

        timeline_index = _build_timeline_index(candidate_rows, unit_index=unit_index)
        periods = [block["period_label"] for block in timeline_index["blocks"]]

        assert "11/03/2026 a 25/03/2026" in periods
        assert "30/03/2026 a 01/04/2026" in periods
        assert "06/04/2026 a 08/04/2026" in periods

    def test_build_timeline_index_assigns_matching_block_to_unit(self):
        timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
        candidate_rows = _build_timeline_candidate_rows(timeline)
        unit_index = _build_file_map_unit_index(METODOS_FORMAIS_UNITS)

        timeline_index = _build_timeline_index(candidate_rows, unit_index=unit_index)

        recursion_block = next(
            block for block in timeline_index["blocks"]
            if "recursivas" in block["topic_text"]
        )
        isabelle_block = next(
            block for block in timeline_index["blocks"]
            if "isabelle" in block["topic_text"]
        )

        assert recursion_block["unit_slug"] == "unidade-01-metodos-formais"
        assert isabelle_block["unit_slug"] == "unidade-02-prova-interativa-de-teoremas"

    def test_timeline_unit_scoring_is_conservative_for_generic_logic_and_admin_rows(self):
        unit_index = _build_file_map_unit_index(_parse_units_from_teaching_plan(PUCRS_PLAN))
        scores_by_slug = {
            unit["slug"]: _score_timeline_row_against_unit("Lógica de Hoare", unit)
            for unit in unit_index
        }

        assert scores_by_slug["unidade-02-verificacao-de-programas"] > scores_by_slug["unidade-01-metodos-formais"]
        assert scores_by_slug["unidade-02-verificacao-de-programas"] > scores_by_slug["unidade-03-verificacao-de-modelos"]

        predicados_scores = {
            unit["slug"]: _score_timeline_row_against_unit("Lógica de Predicados", unit)
            for unit in unit_index
        }
        assert predicados_scores["unidade-03-verificacao-de-modelos"] == 0.0
        assert _score_timeline_row_against_unit(
            "Lógica de Programas - coleções Dafny (conjuntos)",
            next(unit for unit in unit_index if unit["slug"] == "unidade-01-metodos-formais"),
        ) == 0.0

        assert all(
            _score_timeline_row_against_unit("Suspensão de aulas", unit) == 0.0
            for unit in unit_index
        )

    def test_timeline_index_does_not_assign_administrative_blocks(self):
        timeline = _parse_syllabus_timeline("""\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-09 | Suspensão de aulas |
| 2 | 2026-04-27 | Lógica de Hoare |
| 3 | 2026-06-15 | Modelos de Kripke |
""")
        unit_index = _build_file_map_unit_index([
            ("Unidade 01 — Métodos Formais", ["Lógica de Predicados"]),
            ("Unidade 02 — Verificação de Programas", ["Lógica de Hoare"]),
            ("Unidade 03 — Verificação de Modelos", ["Modelos de Kripke"]),
        ])

        timeline_index = _build_timeline_index(_build_timeline_candidate_rows(timeline), unit_index=unit_index)
        suspension_block = next(
            block for block in timeline_index["blocks"]
            if "suspensao" in block["topic_text"]
        )
        hoare_block = next(
            block for block in timeline_index["blocks"]
            if "hoare" in block["topic_text"]
        )
        kripke_block = next(
            block for block in timeline_index["blocks"]
            if "kripke" in block["topic_text"]
        )

        assert suspension_block["unit_slug"] == ""
        assert hoare_block["unit_slug"] == "unidade-02-verificacao-de-programas"
        assert kripke_block["unit_slug"] == "unidade-03-verificacao-de-modelos"

        serialized = _serialize_timeline_index(timeline_index)
        assert all("suspensao" not in block["topic_text"] for block in serialized["blocks"])

    def test_timeline_index_serialization_keeps_review_sessions_but_drops_admin_events(self):
        timeline = _parse_syllabus_timeline("""\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-04-15 | Exercícios de revisão |
| 2 | 2026-05-27 | Evento Acadêmico |
| 3 | 2026-06-03 | Prova de Teoremas - Isabelle |
""")
        unit_index = _build_file_map_unit_index(_parse_units_from_teaching_plan(PUCRS_PLAN))

        timeline_index = _build_timeline_index(_build_timeline_candidate_rows(timeline), unit_index=unit_index)
        serialized = _serialize_timeline_index(timeline_index)

        periods = [str(block.get("period_start", "")) for block in serialized["blocks"]]
        topics = [str(block.get("topic_text", "")) for block in serialized["blocks"]]
        assert "2026-04-15" in periods
        assert any("isabelle" in topic for topic in topics)
        assert "2026-05-27" not in periods

    def test_timeline_index_keeps_weak_single_token_overlap_unassigned(self):
        timeline = _parse_syllabus_timeline("""\
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-05-13 | Lógica de Programas - coleções Dafny (conjuntos) |
""")
        unit_index = _build_file_map_unit_index(_parse_units_from_teaching_plan(PUCRS_PLAN))

        timeline_index = _build_timeline_index(_build_timeline_candidate_rows(timeline), unit_index=unit_index)

        assert timeline_index["blocks"][0]["unit_slug"] == ""


class TestEntryUnitMatcher:
    def test_ignores_accidental_estado_match_in_logic_file(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        entry = {
            "title": "Logicaproposicional Sintaxe",
            "category": "material-de-aula",
            "raw_target": "raw/pdfs/material/logicaproposicional-sintaxe.pdf",
            "manual_tags": [],
            "auto_tags": [],
            "tags": "",
        }
        markdown_text = """\
# Lógica Proposicional

A cidade de Salvador é a capital do estado do Amazonas.
"""

        match = _auto_map_entry_unit(entry, units, markdown_text)

        assert match.ambiguous is True
        assert match.confidence <= 0.4

    def test_prefers_verificacao_de_programas_when_markdown_has_hoare_signals(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        entry = {
            "title": "Exerciciosespecificacao",
            "category": "listas",
            "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
            "manual_tags": [],
            "auto_tags": [],
            "tags": "",
        }
        markdown_text = """\
## Especificação Formal

Construa pré e pós condições em lógica de predicados.
Use invariantes de laço e discuta correção parcial e total.
"""

        match = _auto_map_entry_unit(entry, units, markdown_text)

        assert match.slug == "unidade-02-verificacao-de-programas"


class TestCourseMapTimeline:
    """Testa que course_map_md inclui a seção Timeline quando há cronograma."""

    def test_timeline_section_present(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=SYLLABUS_TABLE,
            teaching_plan=PUCRS_PLAN,
        )
        result = course_map_md({"course_name": "Métodos Formais"}, sp)
        assert "Timeline" in result
        assert "Cronograma" in result

    def test_timeline_section_present_for_learning_unit_format(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Inteligência Artificial",
            slug="inteligencia-artificial",
            syllabus=SYLLABUS_TABLE,
            teaching_plan=LEARNING_UNIT_PLAN,
        )
        result = course_map_md({"course_name": "Inteligência Artificial"}, sp)
        assert "Timeline" in result
        assert "[não identificado]" not in result

    def test_timeline_includes_all_pucrs_units_when_matched(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=SYLLABUS_TABLE,
            teaching_plan=PUCRS_PLAN,
        )
        result = course_map_md({"course_name": "Métodos Formais"}, sp)
        assert "| Unidade 01" in result
        assert "| Unidade 02" in result
        assert "| Unidade 03" in result
        assert "2026-03-23 a 2026-03-30" in result

    def test_no_timeline_without_syllabus(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus="",
            teaching_plan=PUCRS_PLAN,
        )
        result = course_map_md({"course_name": "Métodos Formais"}, sp)
        assert "Timeline" not in result

    def test_course_map_prefers_cached_timeline_and_assessment_context(self, monkeypatch):
        from src.models.core import SubjectProfile
        import src.builder.engine as engine

        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus="texto qualquer de cronograma",
            teaching_plan=PUCRS_PLAN,
        )
        course_meta = {
            "course_name": "Métodos Formais",
            "_timeline_context": {
                "blocks_by_unit": {
                    "unidade-01-metodos-formais": [
                        {
                            "period_start": "2026-03-02",
                            "period_end": "2026-03-25",
                            "period_label": "02/03/2026 a 25/03/2026",
                        }
                    ]
                }
            },
            "_assessment_context": {
                "version": 1,
                "assessments": [],
                "conflicts": [
                    {
                        "label": "P1",
                        "assessment_date": "2026-04-22",
                        "declared_unit_numbers": [1, 2],
                        "declared_unit_slugs": ["unidade-01-metodos-formais"],
                        "conflicts": ["P1 em 2026-04-22 antecede Unidade 1 (previsto para 02/03/2026 a 25/03/2026)."],
                    }
                ],
            },
        }

        def _fail(*args, **kwargs):
            raise AssertionError("cached contexts should avoid recomputation")

        monkeypatch.setattr(engine, "_build_file_map_timeline_context_from_course", _fail)
        monkeypatch.setattr(engine, "_build_assessment_context_from_course", _fail)

        result = course_map_md(course_meta, sp)

        assert "Timeline" in result
        assert "02/03/2026 a 25/03/2026" in result
        assert "Conflitos de avaliação x cronograma" in result

    def test_course_map_does_not_recover_missing_units_from_raw_syllabus(self, monkeypatch):
        from src.models.core import SubjectProfile
        import src.builder.engine as engine

        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus="texto qualquer de cronograma",
            teaching_plan=PUCRS_PLAN,
        )
        course_meta = {
            "course_name": "Métodos Formais",
            "_timeline_context": {
                "blocks_by_unit": {
                    "unidade-01-metodos-formais": [
                        {
                            "period_start": "2026-03-02",
                            "period_end": "2026-03-25",
                            "period_label": "02/03/2026 a 25/03/2026",
                        }
                    ]
                }
            },
        }

        def _fail(*args, **kwargs):
            raise AssertionError("legacy timeline fallback should not be used")

        monkeypatch.setattr(engine, "_match_timeline_to_units", _fail)

        result = course_map_md(course_meta, sp)

        assert "| Unidade 01" in result
        assert "| Unidade 02" not in result
        assert "02/03/2026 a 25/03/2026" in result


class TestAssessmentConflicts:
    def test_build_assessment_context_detects_scope_conflict(self):
        from src.models.core import SubjectProfile

        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=ASSESSMENT_CONFLICT_SYLLABUS,
            teaching_plan=ASSESSMENT_CONFLICT_PLAN,
        )
        context = _build_assessment_context_from_course({"course_name": "Métodos Formais"}, sp)

        assert context["version"] == 1
        assert context["conflicts"]
        conflict = context["conflicts"][0]
        assert conflict["label"] == "P1"
        assert conflict["assessment_date"] == "2026-04-22"
        assert conflict["declared_unit_numbers"] == [1, 2]
        assert "unidade-02-verificacao-de-programas" in conflict["declared_unit_slugs"]
        assert any("antecede" in item for item in conflict["conflicts"])

    def test_course_map_includes_assessment_conflict_section(self):
        from src.models.core import SubjectProfile

        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=ASSESSMENT_CONFLICT_SYLLABUS,
            teaching_plan=ASSESSMENT_CONFLICT_PLAN,
        )
        result = course_map_md({"course_name": "Métodos Formais"}, sp)

        assert "Conflitos de avaliação x cronograma" in result
        assert "P1" in result

    def test_file_map_prefers_cached_content_taxonomy_and_timeline_context(self, monkeypatch):
        from src.models.core import SubjectProfile
        import src.builder.engine as engine

        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=SYLLABUS_TABLE,
            teaching_plan=PUCRS_PLAN,
        )
        course_meta = {
            "course_name": "Métodos Formais",
            "_repo_root": None,
            "_content_taxonomy": {
                "version": 1,
                "course_slug": "metodos-formais",
                "units": [
                    {
                        "slug": "unidade-01-metodos-formais",
                        "title": "Unidade 1 — Métodos Formais",
                        "topics": [
                            {
                                "slug": "provadores-de-teoremas",
                                "label": "Provadores de Teoremas",
                                "aliases": ["Isabelle"],
                                "kind": "subtopic",
                                "unit_slug": "unidade-01-metodos-formais",
                            }
                        ],
                    }
                ],
            },
            "_timeline_context": {
                "timeline_index": {
                    "blocks": [
                        {
                            "id": "bloco-01",
                            "period_label": "02/03/2026 a 25/03/2026",
                            "unit_slug": "unidade-01-metodos-formais",
                            "unit_confidence": 0.98,
                            "primary_topic_slug": "provadores-de-teoremas",
                            "primary_topic_confidence": 0.96,
                            "topic_candidates": [
                                {
                                    "topic_slug": "provadores-de-teoremas",
                                    "topic_label": "Provadores de Teoremas",
                                    "unit_slug": "unidade-01-metodos-formais",
                                }
                            ],
                            "rows": [
                                {"index": 1, "date_text": "02/03/2026", "content": "Provadores de Teoremas - Isabelle"},
                                {"index": 2, "date_text": "04/03/2026", "content": "Provadores de Teoremas - Isabelle"},
                            ],
                        }
                    ]
                },
                "blocks_by_unit": {
                    "unidade-01-metodos-formais": [
                        {
                            "id": "bloco-01",
                            "period_label": "02/03/2026 a 25/03/2026",
                            "unit_slug": "unidade-01-metodos-formais",
                            "unit_confidence": 0.98,
                            "primary_topic_slug": "provadores-de-teoremas",
                            "primary_topic_confidence": 0.96,
                            "topic_candidates": [],
                            "rows": [
                                {"index": 1, "date_text": "02/03/2026", "content": "Provadores de Teoremas - Isabelle"},
                                {"index": 2, "date_text": "04/03/2026", "content": "Provadores de Teoremas - Isabelle"},
                            ],
                        }
                    ]
                },
                "unit_periods": {"unidade-01-metodos-formais": "02/03/2026 a 25/03/2026"},
                "unit_period_bounds": {
                    "unidade-01-metodos-formais": (
                        _parse_timeline_date_value("2026-03-02"),
                        _parse_timeline_date_value("2026-03-25"),
                    )
                },
            },
        }

        entry = {
            "title": "Isabelle",
            "category": "listas",
            "tags": "",
            "raw_target": "raw/pdfs/listas/isabelle.pdf",
            "_markdown_text_for_tests": "# Provadores de Teoremas\n\nIsabelle",
        }

        def _fail(*args, **kwargs):
            raise AssertionError("cached contexts should avoid recomputation")

        monkeypatch.setattr(engine, "_build_file_map_content_taxonomy_from_course", _fail)
        monkeypatch.setattr(engine, "_build_file_map_timeline_context_from_course", _fail)

        result = file_map_md(course_meta, [entry], sp)

        assert "unidade-01-metodos-formais" in result
        assert "02/03/2026 a 25/03/2026" in result
        assert "Isabelle" in result


class TestGlossarySeed:
    def test_seed_glossary_specific_term(self):
        definition, synonyms, not_confuse = _seed_glossary_fields(
            "Lógica de Hoare",
            "Unidade 02 — Verificação de Programas",
        )
        assert "programas" in definition.lower()
        assert synonyms != "—"
        assert not_confuse != "—"

    def test_seed_glossary_generic_term_uses_unit_hint(self):
        definition, synonyms, not_confuse = _seed_glossary_fields(
            "Conceituação",
            "Unidade de Aprendizagem 1 — Visão Geral (5%)",
        )
        assert "visão geral" in definition.lower()
        assert synonyms == "visão geral"
        assert not_confuse == "detalhamento técnico"

    def test_glossary_md_seeds_short_definitions(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Inteligência Artificial",
            slug="inteligencia-artificial",
            teaching_plan=LEARNING_UNIT_PLAN,
        )
        result = glossary_md({"course_name": "Inteligência Artificial"}, sp)
        assert "aguardando análise do tutor" not in result
        assert "**Definição:**" in result

    def test_glossary_md_enriches_generic_term_from_curated_markdown(self, tmp_path):
        from src.models.core import SubjectProfile
        curated_dir = tmp_path / "content" / "curated"
        curated_dir.mkdir(parents=True)
        (curated_dir / "conceituacao.md").write_text(
            "# Conceituação\n\n"
            "## Visão geral\n"
            "Conceituação estabelece o escopo, a terminologia e a intenção pedagógica do tema.\n"
            "Essa etapa evita excesso de detalhe técnico logo no início.",
            encoding="utf-8",
        )
        sp = SubjectProfile(
            name="Inteligência Artificial",
            slug="inteligencia-artificial",
            teaching_plan=LEARNING_UNIT_PLAN,
        )
        manifest_entries = [
            {
                "title": "Conceituação",
                "base_markdown": "content/curated/conceituacao.md",
            }
        ]
        result = glossary_md(
            {"course_name": "Inteligência Artificial"},
            sp,
            root_dir=tmp_path,
            manifest_entries=manifest_entries,
        )
        block = result.split("## Conceituação", 1)[1].split("\n## ", 1)[0]
        assert "Conceituação estabelece o escopo, a terminologia e a intenção pedagógica do tema." in result
        assert "##" not in block
        assert "Conceituação Conceituação" not in block
        assert len(block) <= 260
        assert "excesso de detalhe técnico" not in result

    def test_glossary_ignores_noisy_author_like_evidence(self):
        docs = [{
            "title": "Especificação de Conjuntos Indutivos",
            "manifest_title": "",
            "headings": [],
            "text": "Júlio Machado Conjuntos Indutivos 1. Conjuntos indutivos definem coleções fechadas por regras de construção.",
        }]
        evidence = _find_glossary_evidence(
            "Especificação de Conjuntos Indutivos",
            "Unidade 01 â€” Métodos Formais",
            docs,
        )
        assert "júlio machado" not in evidence.lower()
        assert "regras" in evidence.lower()
        assert "constru" in evidence.lower()

    def test_regenerate_pedagogical_files_passes_manifest_entries_to_glossary(self, tmp_path):
        from src.builder.engine import RepoBuilder
        from src.models.core import SubjectProfile

        repo = tmp_path / "repo"
        curated_dir = repo / "content" / "curated"
        curated_dir.mkdir(parents=True, exist_ok=True)
        (curated_dir / "conceituacao.md").write_text(
            "# Conteúdo base\n\n"
            "## Visão geral\n"
            "Conceituação estabelece o escopo, a terminologia e a intenção pedagógica do tema.\n"
            "Essa etapa evita excesso de detalhe técnico logo no início.",
            encoding="utf-8",
        )

        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {"course_name": "Inteligência Artificial", "course_slug": "ia"}
        builder.student_profile = None
        builder.subject_profile = SubjectProfile(
            name="Inteligência Artificial",
            slug="inteligencia-artificial",
            teaching_plan=LEARNING_UNIT_PLAN,
        )
        builder.logs = []
        builder.progress_callback = None
        builder.entries = []
        builder.options = {}

        manifest = {
            "entries": [
                {
                    "title": "Conceituação",
                    "base_markdown": "content/curated/conceituacao.md",
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "advanced_markdown": None,
                }
            ]
        }

        builder._regenerate_pedagogical_files(manifest)
        glossary = (repo / "course" / "GLOSSARY.md").read_text(encoding="utf-8")

        assert "Conceituação estabelece o escopo, a terminologia e a intenção pedagógica do tema." in glossary
        assert "excesso de detalhe técnico" not in glossary
        assert "manifest" not in glossary.lower()

        taxonomy = json.loads((repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
        timeline_index = json.loads((repo / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
        assessment_context = json.loads((repo / "course" / ".assessment_context.json").read_text(encoding="utf-8"))
        assert taxonomy["version"] == 1
        assert taxonomy["course_slug"]
        assert taxonomy["units"]
        assert isinstance(timeline_index["blocks"], list)
        assert assessment_context["version"] == 1

    def test_file_map_does_not_restore_period_from_unit_periods_fallback(self, monkeypatch):
        import src.builder.engine as engine
        from src.models.core import SubjectProfile

        course_meta = {
            "course_name": "Métodos Formais",
            "course_slug": "metodos-formais",
            "_repo_root": None,
            "_content_taxonomy": {
                "version": 1,
                "course_slug": "metodos-formais",
                "units": [
                    {
                        "slug": "unidade-01-metodos-formais",
                        "title": "Unidade 1 — Métodos Formais",
                        "topics": [
                            {
                                "slug": "provadores-de-teoremas",
                                "label": "Provadores de Teoremas",
                                "aliases": ["Isabelle"],
                                "kind": "subtopic",
                                "unit_slug": "unidade-01-metodos-formais",
                            }
                        ],
                    }
                ],
            },
            "_timeline_context": {
                "timeline_index": {"version": 1, "blocks": []},
                "blocks_by_unit": {},
                "rows_by_unit": {},
                "unassigned_blocks": [],
                "unit_periods": {
                    "unidade-01-metodos-formais": "02/03/2026 a 25/03/2026"
                },
                "unit_period_bounds": {
                    "unidade-01-metodos-formais": (
                        _parse_timeline_date_value("2026-03-02"),
                        _parse_timeline_date_value("2026-03-25"),
                    )
                },
            },
        }
        subject_profile = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            teaching_plan="""
### Unidade 1 — Métodos Formais
- Provadores de Teoremas
""".strip(),
        )
        entry = {
            "title": "Isabelle",
            "category": "listas",
            "tags": "",
            "manual_unit_slug": "unidade-01-metodos-formais",
            "base_markdown": "content/curated/isabelle.md",
            "approved_markdown": None,
            "curated_markdown": None,
            "advanced_markdown": None,
            "_markdown_text_for_tests": "# Provadores de Teoremas\n\nIsabelle",
        }

        def _fail(*args, **kwargs):
            raise AssertionError("cached contexts should avoid recomputation")

        monkeypatch.setattr(engine, "_build_file_map_content_taxonomy_from_course", _fail)
        monkeypatch.setattr(engine, "_build_file_map_timeline_context_from_course", _fail)

        result = file_map_md(course_meta, [entry], subject_profile)

        assert "unidade-01-metodos-formais" in result
        assert "02/03/2026 a 25/03/2026" not in result
        assert "| unidade-01-metodos-formais | Alta |  |" in result

    def test_build_passes_manifest_entries_to_glossary(self, tmp_path, monkeypatch):
        from src.builder import engine
        from src.builder.engine import RepoBuilder
        from src.models.core import SubjectProfile

        repo = tmp_path / "repo"
        repo.mkdir()

        class FakeEntry:
            def __init__(self, payload):
                self._payload = payload
                self.title = payload["title"]
                self.category = payload["category"]
                self.file_type = payload["file_type"]
                self.source_path = payload["source_path"]
                self.enabled = True

            def to_dict(self):
                return self._payload

        entry_payload = {
            "id": "entry-1",
            "title": "Aula 1",
            "category": "material-de-aula",
            "file_type": "pdf",
            "source_path": "raw/pdfs/material-de-aula/aula-1.pdf",
        }

        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {
            "course_name": "Inteligência Artificial",
            "course_slug": "ia",
            "professor": "Prof",
            "semester": "2026/1",
            "institution": "PUCRS",
        }
        builder.student_profile = None
        builder.subject_profile = SubjectProfile(
            name="Inteligência Artificial",
            slug="inteligencia-artificial",
            teaching_plan=LEARNING_UNIT_PLAN,
        )
        builder.options = {}
        builder.logs = []
        builder.progress_callback = None
        builder.entries = [FakeEntry(entry_payload)]

        captured_manifest_entries = []

        def fake_glossary_md(course_meta, subject_profile, *, root_dir=None, manifest_entries=None):
            captured_manifest_entries.append(manifest_entries)
            return "# GLOSSARY\n"

        monkeypatch.setattr(engine, "glossary_md", fake_glossary_md)
        monkeypatch.setattr(RepoBuilder, "_process_entry", lambda self, entry: entry.to_dict())
        monkeypatch.setattr(RepoBuilder, "_write_source_registry", lambda self, manifest: None)
        monkeypatch.setattr(RepoBuilder, "_write_bundle_seed", lambda self, manifest: None)
        monkeypatch.setattr(RepoBuilder, "_write_build_report", lambda self, manifest: None)
        monkeypatch.setattr(RepoBuilder, "_resolve_content_images", lambda self: None)
        monkeypatch.setattr(RepoBuilder, "_inject_all_image_descriptions", lambda self: None)
        monkeypatch.setattr(RepoBuilder, "_regenerate_pedagogical_files", lambda self, manifest: None)

        builder.build()

        assert [entry_payload] in captured_manifest_entries
        assert captured_manifest_entries.count([entry_payload]) >= 1

    def test_no_timeline_without_teaching_plan(self):
        from src.models.core import SubjectProfile
        sp = SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            syllabus=SYLLABUS_TABLE,
            teaching_plan="",
        )
        result = course_map_md({"course_name": "Métodos Formais"}, sp)
        assert "Timeline" not in result


# ---------------------------------------------------------------------------
# System prompt — file references + first session protocol
# ---------------------------------------------------------------------------

class TestSystemPromptFileReferences:
    META = {"course_name": "Test", "professor": "P", "institution": "I", "semester": "S"}

    def test_no_conditional_dirs_without_entries(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        # These should NOT appear as rows in the file reference table
        assert "| `assignments/`" not in result
        assert "| `code/professor/`" not in result
        assert "| `whiteboard/`" not in result

    def test_conditional_dirs_with_flags(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(
            self.META, has_assignments=True, has_code=True, has_whiteboard=True)
        assert "| `assignments/`" in result
        assert "| `code/professor/`" in result
        assert "| `whiteboard/`" in result

    def test_file_map_always_referenced(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        assert "FILE_MAP.md" in result

    def test_first_session_protocol_present(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        assert "Primeira Sessão" in result
        assert "FILE_MAP" in result
        assert "COURSE_MAP" in result
        assert "GLOSSARY" in result

    def test_first_session_has_checklist(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        assert "artefatos estruturais gerados pelo app" in result
        assert "Reprocessar Repositório" in result
        assert "EXERCISE_INDEX.md" in result
        assert "GLOSSARY.md" in result

    def test_instructions_prefer_maps_before_long_files(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        assert "Fluxo `map-first`" in result
        assert "Ordem de leitura econômica" in result
        assert "Comece por `course/COURSE_MAP.md`" in result
        assert "student/STUDENT_STATE.md" in result
        assert "exercises/EXERCISE_INDEX.md" in result
        assert "Use `course/FILE_MAP.md` para localizar o material certo" in result
        assert "Só então abra um markdown em `content/`, `exercises/` ou `exams/`" in result


class TestPromptArchitectureAlignment:
    META = {"course_name": "Métodos Formais", "professor": "P", "institution": "I", "semester": "S"}

    def test_claude_prompt_treats_maps_as_generated_artifacts(self):
        text = generate_claude_project_instructions(self.META, first_session_pending=True)

        assert "artefatos estruturais gerados pelo app" in text
        assert "Reprocessar Repositório" in text
        assert "backlog" in text

    def test_claude_prompt_no_longer_requests_manual_file_map_fill(self):
        text = generate_claude_project_instructions(self.META, first_session_pending=True)

        assert "preencha a coluna **Unidade** dos itens vazios" not in text
        assert "retorne o `FILE_MAP.md` e o `COURSE_MAP.md` atualizados" not in text

    def test_gpt_prompt_uses_same_structural_contract(self):
        text = generate_gpt_instructions(self.META)

        assert "artefatos estruturais gerados pelo app" in text
        assert "não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente" in text

    def test_gemini_prompt_uses_same_structural_contract(self):
        text = generate_gemini_instructions(self.META)

        assert "artefatos estruturais gerados pelo app" in text
        assert "não reescreva `FILE_MAP.md`/`COURSE_MAP.md` manualmente" in text

    def test_gemini_prompt_includes_guided_learning_contract(self):
        text = generate_gemini_instructions(self.META)

        assert "## Compatibilidade com Aprendizado Guiado" in text
        assert "no modo `class_companion`, seja curto e direto" in text
        assert "Ao final de sessões substanciais" in text

    def test_prompts_do_not_surface_internal_json_indexes(self):
        texts = [
            generate_claude_project_instructions(self.META, first_session_pending=True),
            generate_gpt_instructions(self.META),
            generate_gemini_instructions(self.META),
        ]

        for text in texts:
            assert ".timeline_index.json" not in text
            assert ".content_taxonomy.json" not in text
            assert ".tag_catalog.json" not in text
            assert ".assessment_context.json" not in text

    def test_engine_source_no_longer_contains_legacy_manual_mapping_instruction(self):
        source = Path(engine_module.__file__).read_text(encoding="utf-8")

        assert "Mapear arquivos → unidades" not in source
        assert "preencha a coluna **Unidade** dos itens vazios" not in source
        assert "retorne o `FILE_MAP.md` e o `COURSE_MAP.md` atualizados" not in source

    def test_engine_source_no_longer_contains_redundant_v2_prompt_wrapper(self):
        source = Path(engine_module.__file__).read_text(encoding="utf-8")

        assert "def _low_token_generate_claude_project_instructions_v2(" not in source


class TestGeneratedRepoGitignore:
    def test_ignores_only_regenerable_internal_indexes_and_prompt_exports(self):
        text = _generated_repo_gitignore_text()

        assert "course/.content_taxonomy.json" in text
        assert "course/.timeline_index.json" in text
        assert "course/.assessment_context.json" in text
        assert "course/.tag_catalog.json" in text
        assert "INSTRUCOES_CLAUDE_PROJETO.md" in text
        assert "INSTRUCOES_GPT_PROJETO.md" in text
        assert "INSTRUCOES_GEMINI_PROJETO.md" in text
        assert "manifest.json" not in text
        assert "course/FILE_MAP.md" not in text
        assert "course/COURSE_MAP.md" not in text


# ---------------------------------------------------------------------------
# file_map_md
# ---------------------------------------------------------------------------

class TestFileMapMd:
    META = {"course_name": "Métodos Formais"}

    def test_empty_entries(self):
        result = file_map_md(self.META, [])
        assert "FILE_MAP" in result
        assert "Nenhum arquivo processado ainda." in result

    def test_with_entries(self):
        entries = [
            {"title": "Aula 1", "category": "material-de-aula",
             "tags": "", "base_markdown": "content/aula-1.md", "raw_target": "raw/aula-1.pdf"},
            {"title": "Prova 1", "category": "provas",
             "tags": "unidade-01", "base_markdown": "exams/prova-1.md", "raw_target": "raw/prova-1.pdf"},
        ]
        result = file_map_md(self.META, entries)
        assert "| 1 |" in result
        assert "Aula 1" in result
        assert "Prova 1" in result
        assert "material-de-aula" in result
        assert "`content/aula-1.md`" in result
        assert "unidade-01" in result

    def test_cronograma_auto_tagged(self):
        entries = [
            {"title": "Cronograma 2026", "category": "cronograma",
             "tags": "", "base_markdown": "content/crono.md", "raw_target": ""},
        ]
        result = file_map_md(self.META, entries)
        assert "curso-inteiro" in result

    def test_low_token_routing_headers(self):
        entries = [
            {"title": "Aula 1", "category": "material-de-aula",
             "tags": "", "base_markdown": "content/aula-1.md", "raw_target": "raw/aula-1.pdf"},
        ]
        result = file_map_md(self.META, entries)
        assert "Ordem de consulta econômica" in result
        assert "Quando abrir" in result
        assert "Prioridade" in result
        assert "teoria base" in result

    def test_large_file_map_stays_roteable_and_truncates(self):
        entries = [
            {
                "title": f"Aula {i:03d}",
                "category": "material-de-aula",
                "tags": "",
                "base_markdown": f"content/aula-{i:03d}.md",
                "raw_target": f"raw/aula-{i:03d}.pdf",
            }
            for i in range(200)
        ]
        result = file_map_md(self.META, entries)
        assert "FILE_MAP" in result
        assert "Quando abrir" in result
        assert "Conteúdo truncado" in result
        assert len(result) <= 12000

    def test_filters_orphan_manifest_entries_when_repo_root_is_known(self, tmp_path):
        repo = tmp_path / "repo"
        (repo / "content").mkdir(parents=True)
        (repo / "content" / "live.md").write_text("# live", encoding="utf-8")
        entries = [
            {
                "title": "Ativo",
                "category": "material-de-aula",
                "tags": "",
                "base_markdown": "content/live.md",
                "raw_target": "",
            },
            {
                "title": "Órfão",
                "category": "references",
                "tags": "",
                "base_markdown": "content/missing.md",
                "raw_target": "",
            },
        ]
        result = file_map_md({**self.META, "_repo_root": repo}, entries)
        assert "Ativo" in result
        assert "Órfão" not in result


class TestBundleSeedLowToken:
    def test_bundle_priority_prefers_exam_relevant_content(self):
        from src.builder.engine import _bundle_priority_score

        exam_entry = {
            "category": "provas",
            "include_in_bundle": False,
            "relevant_for_exam": True,
            "effective_profile": "diagram_heavy",
            "title": "P1 2025",
        }
        bibliography_entry = {
            "category": "bibliografia",
            "include_in_bundle": False,
            "relevant_for_exam": False,
            "effective_profile": "textbook",
            "title": "Livro base",
        }

        assert _bundle_priority_score(exam_entry) > _bundle_priority_score(bibliography_entry)

    def test_write_bundle_seed_adds_policy_and_reasons(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        (repo / "build" / "claude-knowledge").mkdir(parents=True)
        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {"course_slug": "ia"}

        manifest = {
            "generated_at": "2026-03-31T10:00:00",
            "entries": [
                {
                    "id": "p1",
                    "title": "P1",
                    "category": "provas",
                    "include_in_bundle": False,
                    "relevant_for_exam": True,
                    "base_markdown": "exams/p1.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "diagram_heavy",
                },
                {
                    "id": "bib",
                    "title": "Livro",
                    "category": "bibliografia",
                    "include_in_bundle": False,
                    "relevant_for_exam": False,
                    "base_markdown": "content/bib.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "textbook",
                },
            ],
        }

        builder._write_bundle_seed(manifest)

        data = json.loads((repo / "build" / "claude-knowledge" / "bundle.seed.json").read_text(encoding="utf-8"))
        assert set(data["selection_policy"].keys()) == {
            "min_score",
            "goal",
            "routing_first",
            "exclude_full_text",
            "metadata_only",
        }
        assert data["selection_policy"]["goal"] == "baixo-custo-alto-sinal"
        assert data["selection_policy"]["exclude_full_text"] is True
        assert data["selection_policy"]["metadata_only"] is True
        assert len(data["bundle_candidates"]) == 1
        candidate = data["bundle_candidates"][0]
        assert set(candidate.keys()) == {
            "id",
            "title",
            "category",
            "preferred_manual_review",
            "approved_markdown",
            "curated_markdown",
            "advanced_markdown",
            "base_markdown",
            "effective_profile",
            "relevant_for_exam",
            "bundle_priority_score",
            "bundle_reasons",
        }
        assert candidate["id"] == "p1"
        assert "relevante-para-prova" in candidate["bundle_reasons"]

    def test_bundle_seed_excludes_raw_text_fields(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        (repo / "build" / "claude-knowledge").mkdir(parents=True)
        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {"course_slug": "ia"}

        manifest = {
            "generated_at": "2026-03-31T10:00:00",
            "entries": [
                {
                    "id": "x",
                    "title": "Material",
                    "category": "material-de-aula",
                    "include_in_bundle": True,
                    "relevant_for_exam": True,
                    "base_markdown": "content/a.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "diagram_heavy",
                    "full_markdown": "isso nunca deve ir para o bundle",
                    "raw_markdown": "isso também não",
                }
            ],
        }

        builder._write_bundle_seed(manifest)
        data = json.loads((repo / "build" / "claude-knowledge" / "bundle.seed.json").read_text(encoding="utf-8"))
        payload = json.dumps(data, ensure_ascii=False)
        candidate = data["bundle_candidates"][0]
        assert "full_markdown" not in payload
        assert "raw_markdown" not in payload
        assert "isso nunca deve ir para o bundle" not in payload
        assert "isso também não" not in payload
        assert "full_markdown" not in candidate
        assert "raw_markdown" not in candidate
        assert set(candidate.keys()) == {
            "id",
            "title",
            "category",
            "preferred_manual_review",
            "approved_markdown",
            "curated_markdown",
            "advanced_markdown",
            "base_markdown",
            "effective_profile",
            "relevant_for_exam",
            "bundle_priority_score",
            "bundle_reasons",
        }

    def test_reject_uses_manifest_course_meta_when_builder_course_meta_is_empty(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        (repo / "build" / "claude-knowledge").mkdir(parents=True)
        (repo / "course").mkdir(parents=True)
        (repo / "content").mkdir(parents=True)
        (repo / "content" / "aula1.md").write_text("# Aula 1", encoding="utf-8")

        manifest = {
            "generated_at": "2026-04-09T15:00:00",
            "course": {
                "course_name": "Métodos Formais",
                "course_slug": "metodos-formais",
                "semester": "2026/1",
                "professor": "Prof",
                "institution": "PUCRS",
            },
            "entries": [
                {
                    "id": "aula1",
                    "title": "Aula 1",
                    "category": "material-de-aula",
                    "file_type": "pdf",
                    "source_path": "C:/tmp/aula1.pdf",
                    "base_markdown": "content/aula1.md",
                }
            ],
            "logs": [],
        }
        (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        builder = RepoBuilder(root_dir=repo, course_meta={}, entries=[], options={})
        builder._resolve_content_images = lambda: None

        entry_data = builder.reject("aula1")

        assert entry_data is not None
        data = json.loads((repo / "build" / "claude-knowledge" / "bundle.seed.json").read_text(encoding="utf-8"))
        assert data["course_slug"] == "metodos-formais"

    def test_reject_preserves_page_range_from_manifest_entry(self, tmp_path):
        from src.builder.engine import RepoBuilder
        from src.models.core import FileEntry

        repo = tmp_path / "repo"
        (repo / "build" / "claude-knowledge").mkdir(parents=True)
        (repo / "course").mkdir(parents=True)
        (repo / "content").mkdir(parents=True)
        (repo / "content" / "aula1.md").write_text("# Aula 1", encoding="utf-8")

        manifest = {
            "generated_at": "2026-04-09T15:00:00",
            "course": {
                "course_name": "Métodos Formais",
                "course_slug": "metodos-formais",
                "semester": "2026/1",
                "professor": "Prof",
                "institution": "PUCRS",
            },
            "entries": [
                {
                    "id": "aula1",
                    "title": "Aula 1",
                    "category": "material-de-aula",
                    "file_type": "pdf",
                    "source_path": "C:/tmp/aula1.pdf",
                    "base_markdown": "content/aula1.md",
                    "page_range": "3-8",
                    "processing_mode": "full",
                    "document_profile": "math_heavy",
                    "preferred_backend": "marker",
                }
            ],
            "logs": [],
        }
        (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        builder = RepoBuilder(root_dir=repo, course_meta={}, entries=[], options={})
        builder._resolve_content_images = lambda: None

        entry_data = builder.reject("aula1")

        restored = FileEntry.from_dict({**entry_data, "enabled": True})
        assert restored.page_range == "3-8"

    def test_unprocess_removes_final_markdowns_and_consolidated_entry_images(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        (repo / "build" / "claude-knowledge").mkdir(parents=True)
        (repo / "course").mkdir(parents=True)
        (repo / "content" / "curated").mkdir(parents=True)
        (repo / "content" / "images" / "scanned" / "aula1").mkdir(parents=True)

        approved_md = repo / "content" / "curated" / "aula1.md"
        approved_md.write_text("# Aula 1\n", encoding="utf-8")
        consolidated_img = repo / "content" / "images" / "aula1-page-400-img-01.png"
        consolidated_img.write_bytes(b"old")
        scanned_img = repo / "content" / "images" / "scanned" / "aula1" / "page-001.jpg"
        scanned_img.write_bytes(b"old")

        manifest = {
            "generated_at": "2026-04-10T10:00:00",
            "course": {
                "course_name": "MÃ©todos Formais",
                "course_slug": "metodos-formais",
                "semester": "2026/1",
                "professor": "Prof",
                "institution": "PUCRS",
            },
            "entries": [
                {
                    "id": "aula1",
                    "title": "Aula 1",
                    "category": "material-de-aula",
                    "file_type": "pdf",
                    "source_path": "C:/tmp/aula1.pdf",
                    "approved_markdown": "content/curated/aula1.md",
                    "curated_markdown": "content/curated/aula1.md",
                    "rendered_pages_dir": "content/images/scanned/aula1",
                }
            ],
            "logs": [],
        }
        (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        builder = RepoBuilder(root_dir=repo, course_meta={}, entries=[], options={})
        builder._resolve_content_images = lambda: None

        assert builder.unprocess("aula1") is True
        assert not approved_md.exists()
        assert not consolidated_img.exists()
        assert not scanned_img.exists()

        updated = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        assert updated["entries"] == []

    def test_process_entry_persists_page_range_and_processing_options(self, tmp_path):
        from src.builder.engine import RepoBuilder
        from src.models.core import FileEntry

        repo = tmp_path / "repo"
        repo.mkdir()
        source = tmp_path / "entrada.pdf"
        source.write_bytes(b"%PDF-1.4\n%fake\n")

        builder = RepoBuilder(root_dir=repo, course_meta={"course_slug": "mf"}, entries=[], options={})
        builder._process_pdf = lambda entry, raw_target: {"base_markdown": "staging/example.md"}

        entry = FileEntry(
            source_path=str(source),
            file_type="pdf",
            category="material-de-aula",
            title="Entrada",
            processing_mode="full",
            document_profile="math_heavy",
            preferred_backend="marker",
            page_range="2-5",
            force_ocr=True,
            extract_images=False,
            extract_tables=False,
            formula_priority=True,
            datalab_mode="accurate",
        )

        item = builder._process_entry(entry)

        assert item["page_range"] == "2-5"
        assert item["force_ocr"] is True
        assert item["extract_images"] is False
        assert item["extract_tables"] is False
        assert item["formula_priority"] is True
        assert item["datalab_mode"] == "accurate"


class TestCourseMapLowToken:
    def test_course_map_is_short_router_not_parallel_apostila(self):
        from src.builder.engine import course_map_md
        result = course_map_md({"course_name": "Métodos Formais"}, None)
        assert "Mapa pedagógico curto da disciplina" in result
        assert "Não replique explicações longas aqui" in result
        assert "INSTRUÇÃO PARA O MANTENEDOR" not in result

    def test_large_course_map_stays_roteable_and_truncates(self):
        from src.models.core import SubjectProfile

        teaching_plan_parts = []
        for i in range(1, 70):
            teaching_plan_parts.append(
                f"Unidade de Aprendizagem {i}: Tópico {i}\n"
                f"Subtópico {i}.1\n"
                f"Subtópico {i}.2\n"
                f"Subtópico {i}.3\n"
            )

        sp = SubjectProfile(
            name="Teste",
            slug="teste",
            syllabus=SYLLABUS_TABLE,
            teaching_plan="\n".join(teaching_plan_parts),
        )
        result = course_map_md({"course_name": "Teste"}, sp)
        assert "COURSE_MAP" in result
        assert "Timeline" in result
        assert "[não identificado]" not in result
        assert len(result) <= 14000

    def test_course_map_omits_empty_exam_and_professor_sections(self):
        result = course_map_md({"course_name": "Métodos Formais"}, None)
        assert "Tópicos de alta incidência em prova" not in result
        assert "Notas do professor" not in result


class TestExerciseIndexLowToken:
    def test_exercise_index_is_routing_table(self):
        entries = [
            FileEntry(
                title="Lista 1",
                source_path="raw/lista1.pdf",
                category="listas",
                file_type="pdf",
                tags="unidade-01",
                notes="Tem gabarito",
            ),
            FileEntry(
                title="P1 2025",
                source_path="raw/p1-2025.pdf",
                category="provas",
                file_type="pdf",
                tags="unidade-01;unidade-02",
                notes="Alta incidência",
            ),
        ]
        result = exercise_index_md({"course_name": "Teste"}, entries)
        assert "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |" in result
        assert "Mapeamento de exercícios por tópico" not in result
        assert "revisão de prova" in result

    def test_exercise_index_empty_state_stays_short(self):
        result = exercise_index_md({"course_name": "Teste"}, [])
        assert "| [a preencher] | | | | | |" in result
        assert "Mapeamento de exercícios por tópico" not in result

    def test_exercise_index_uses_auto_tags_when_manual_tags_are_empty(self):
        entries = [
            FileEntry(
                title="Lista 1",
                source_path="raw/lista1.pdf",
                category="listas",
                file_type="pdf",
                manual_tags=[],
                auto_tags=["topico:funcoes-recursivas", "tipo:lista"],
            ),
        ]
        result = exercise_index_md({"course_name": "Teste"}, entries)
        assert "topico:funcoes-recursivas" in result
        assert "tipo:lista" in result


class TestIncrementalBuildLowTokenRollout:
    def test_incremental_build_reapplies_low_token_architecture_without_new_entries(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        for rel in [
            "course",
            "content",
            "content/images",
            "build/claude-knowledge",
            "student",
        ]:
            (repo / rel).mkdir(parents=True, exist_ok=True)

        image_name = "entry1-page-003-img-01.png"
        (repo / "content" / "images" / image_name).write_bytes(b"fake-image")
        (repo / "content" / "lesson.md").write_text(
            f"# Aula\n\n![](content/images/{image_name})\n",
            encoding="utf-8",
        )
        (repo / "student" / "STUDENT_STATE.md").write_text(
            "---\nlast_updated: 2026-03-01\n---\n",
            encoding="utf-8",
        )

        manifest = {
            "generated_at": "2026-03-31T10:00:00",
            "entries": [
                {
                    "id": "entry1",
                    "title": "Aula 1",
                    "category": "material-de-aula",
                    "file_type": "pdf",
                    "source_path": "raw/pdfs/material-de-aula/aula-1.pdf",
                    "raw_target": "raw/pdfs/material-de-aula/aula-1.pdf",
                    "base_markdown": "content/lesson.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "math_heavy",
                    "include_in_bundle": True,
                    "relevant_for_exam": True,
                    "image_curation": {
                        "status": "described",
                        "pages": {
                            "3": {
                                "include_page": True,
                                "images": {
                                    image_name: {
                                        "type": "diagrama",
                                        "include": True,
                                        "description": (
                                            "Diagrama de árvore com três níveis e duas ramificações principais. "
                                            "Há uma legenda longa que não precisa ser repetida por completo."
                                        ),
                                    }
                                },
                            }
                        },
                    },
                }
            ],
            "logs": [],
        }
        (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {
            "course_name": "Inteligência Artificial",
            "course_slug": "ia",
            "professor": "Prof",
            "institution": "PUCRS",
            "semester": "2026/1",
        }
        builder.entries = []
        builder.options = {}
        builder.student_profile = None
        builder.subject_profile = None
        builder.logs = []
        builder.progress_callback = None

        builder.incremental_build()

        file_map = (repo / "course" / "FILE_MAP.md").read_text(encoding="utf-8")
        course_map = (repo / "course" / "COURSE_MAP.md").read_text(encoding="utf-8")
        content_taxonomy = json.loads((repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
        timeline_index = json.loads((repo / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
        assessment_context = json.loads((repo / "course" / ".assessment_context.json").read_text(encoding="utf-8"))
        instructions = (repo / "INSTRUCOES_CLAUDE_PROJETO.md").read_text(encoding="utf-8")
        bundle = json.loads((repo / "build" / "claude-knowledge" / "bundle.seed.json").read_text(encoding="utf-8"))
        lesson = (repo / "content" / "lesson.md").read_text(encoding="utf-8")

        assert "Ordem de consulta econômica" in file_map
        assert "Quando abrir" in file_map
        assert "Mapa pedagógico curto da disciplina" in course_map
        assert content_taxonomy["version"] == 1
        assert timeline_index["version"] == 1
        assert isinstance(timeline_index["blocks"], list)
        assert assessment_context["version"] == 1
        assert "Ordem de leitura econômica" in instructions
        assert "artefatos estruturais gerados pelo app" in instructions
        assert "Reprocessar Repositório" in instructions
        assert "backlog" in instructions
        assert "preencha a coluna **Unidade** dos itens vazios" not in instructions
        assert ".timeline_index.json" not in instructions
        assert ".content_taxonomy.json" not in instructions
        assert ".tag_catalog.json" not in instructions
        assert ".assessment_context.json" not in instructions
        assert bundle["selection_policy"]["goal"] == "baixo-custo-alto-sinal"
        assert bundle["bundle_candidates"][0]["id"] == "entry1"
        assert "> **[Descrição de imagem]** Diagrama de árvore com três níveis e duas ramificações principais." in lesson
        assert "legenda longa" not in lesson

    def test_incremental_build_prunes_orphan_entries_and_compacts_logs(self, tmp_path):
        from src.builder.engine import RepoBuilder

        repo = tmp_path / "repo"
        for rel in [
            "course",
            "content",
            "student",
            "build/claude-knowledge",
        ]:
            (repo / rel).mkdir(parents=True, exist_ok=True)

        (repo / "content" / "live.md").write_text("# live", encoding="utf-8")
        manifest = {
            "app": "GPT Tutor Generator",
            "generated_at": "2026-04-01T10:00:00",
            "course": {"course_name": "Métodos Formais", "course_slug": "mf"},
            "options": {},
            "environment": {},
            "entries": [
                {
                    "id": "live-entry",
                    "title": "Aula viva",
                    "category": "material-de-aula",
                    "file_type": "pdf",
                    "source_path": "raw/pdfs/material-de-aula/aula-viva.pdf",
                    "raw_target": None,
                    "base_markdown": "content/live.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "math_heavy",
                    "include_in_bundle": True,
                    "relevant_for_exam": True,
                },
                {
                    "id": "dead-entry",
                    "title": "Aula morta",
                    "category": "references",
                    "file_type": "url",
                    "source_path": "https://example.com/dead",
                    "raw_target": None,
                    "base_markdown": "content/missing.md",
                    "advanced_markdown": None,
                    "approved_markdown": None,
                    "curated_markdown": None,
                    "effective_profile": "textbook",
                    "include_in_bundle": False,
                    "relevant_for_exam": False,
                },
            ],
            "logs": [{"entry": str(i), "step": "x", "status": "ok"} for i in range(500)],
        }
        (repo / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        builder = RepoBuilder.__new__(RepoBuilder)
        builder.root_dir = repo
        builder.course_meta = {
            "course_name": "Métodos Formais",
            "course_slug": "mf",
            "professor": "Prof",
            "institution": "PUCRS",
            "semester": "2026/1",
        }
        builder.entries = []
        builder.options = {}
        builder.student_profile = None
        builder.subject_profile = None
        builder.logs = []
        builder.progress_callback = None

        builder.incremental_build()

        updated = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        file_map = (repo / "course" / "FILE_MAP.md").read_text(encoding="utf-8")

        assert [e["id"] for e in updated["entries"]] == ["live-entry"]
        assert len(updated["logs"]) == 200
        assert "Aula viva" in file_map
        assert "Aula morta" not in file_map


# ---------------------------------------------------------------------------
# Incremento 1 — Novos geradores e detecção GitHub
# ---------------------------------------------------------------------------

class TestNewGenerators:
    COURSE_META = {"course_name": "Estruturas de Dados",
                   "course_slug": "ed", "professor": "Prof",
                   "semester": "2026/1", "institution": "PUCRS"}

    def _e(self, cat, title, ext=".py"):
        return FileEntry(source_path=f"/fake/{title}{ext}",
                         file_type="code", category=cat, title=title)

    def test_assignment_index_empty(self):
        from src.builder.engine import assignment_index_md
        assert "ASSIGNMENT_INDEX" in assignment_index_md(self.COURSE_META, [])

    def test_assignment_index_entries(self):
        from src.builder.engine import assignment_index_md
        r = assignment_index_md(self.COURSE_META,
                                [self._e("trabalhos", "T1", ".pdf")])
        assert "T1" in r

    def test_code_index_professor(self):
        from src.builder.engine import code_index_md
        r = code_index_md(self.COURSE_META,
                          [self._e("codigo-professor", "linked_list")])
        assert "linked_list" in r

    def test_code_index_empty(self):
        from src.builder.engine import code_index_md
        assert "Nenhum arquivo" in code_index_md(self.COURSE_META, [])

    def test_whiteboard_professor_signal(self):
        from src.builder.engine import whiteboard_index_md
        e = self._e("quadro-branco", "AulaHash", ".png")
        e.professor_signal = "usa colisão linear"
        assert "colisão linear" in whiteboard_index_md(self.COURSE_META, [e])

    def test_whiteboard_empty(self):
        from src.builder.engine import whiteboard_index_md
        assert "WHITEBOARD_INDEX" in whiteboard_index_md(self.COURSE_META, [])


class TestGitHubDetection:
    def test_detects_repo(self):
        from src.ui.dialogs import _is_github_repo
        assert _is_github_repo("https://github.com/user/repo")
        assert _is_github_repo("https://github.com/user/repo.git")

    def test_rejects_file(self):
        from src.ui.dialogs import _is_github_repo
        assert not _is_github_repo(
            "https://github.com/user/repo/blob/main/file.py")
        assert not _is_github_repo("https://google.com")

    def test_base_is_professor(self):
        from src.utils.helpers import STUDENT_BRANCHES
        assert "base" not in STUDENT_BRANCHES

    def test_main_is_student(self):
        from src.utils.helpers import STUDENT_BRANCHES
        assert "main" in STUDENT_BRANCHES
