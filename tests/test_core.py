"""Tests for utility functions and core logic."""

from __future__ import annotations

import json
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

from src.builder.engine import (
    BackendSelector,
    _build_marker_page_chunks,
    rows_to_markdown_table,
    wrap_frontmatter,
    _html_to_structured_markdown,
    _parse_units_from_teaching_plan,
    _parse_bibliography_from_teaching_plan,
    _parse_syllabus_timeline,
    _match_timeline_to_units,
    _topic_text,
    _topic_depth,
    _format_units_for_prompt,
    _seed_glossary_fields,
    course_map_md,
    file_map_md,
    glossary_md,
)
from src.models.core import (
    DocumentProfileReport,
    FileEntry,
    PipelineDecision,
    PendingOperation,
)
from src.utils.helpers import (
    ensure_dir,
    file_size_mb,
    pages_to_marker_range,
    parse_page_range,
    safe_rel,
    slugify,
    write_text,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        assert slugify("Cálculo I - 2024/1") == "cálculo-i-20241"

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


# ---------------------------------------------------------------------------
# BackendSelector
# ---------------------------------------------------------------------------

class TestBackendSelector:
    def test_auto_mode_math_heavy_prefers_marker_when_available(self):
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
            return_value={"pymupdf4llm": True, "pymupdf": True, "docling": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "marker"

    def test_auto_mode_layout_heavy_prefers_marker_when_available(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="layout_heavy")
        with mock.patch.object(
            BackendSelector,
            "available_backends",
            return_value={"pymupdf4llm": True, "pymupdf": True, "docling": True, "marker": True},
        ):
            decision = selector.decide(entry, report)
        assert decision.advanced_backend == "marker"

    def test_quick_mode_selects_base_only(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="quick",
        )
        report = DocumentProfileReport(suggested_profile="general")
        decision = selector.decide(entry, report)
        assert decision.processing_mode == "quick"
        assert decision.advanced_backend is None

    def test_auto_mode_general_no_advanced(self):
        selector = BackendSelector()
        entry = FileEntry(
            source_path="/test.pdf",
            file_type="pdf",
            category="course-material",
            title="Test",
            processing_mode="auto",
        )
        report = DocumentProfileReport(suggested_profile="general")
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
        report = DocumentProfileReport(suggested_profile="general")
        decision = selector.decide(entry, report)
        available = selector.available_backends()
        has_advanced = available.get("docling") or available.get("marker")
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
        assert "docling" in available
        assert "marker" in available


# ---------------------------------------------------------------------------
# DocumentProfileReport
# ---------------------------------------------------------------------------

class TestDocumentProfileReport:
    def test_defaults(self):
        report = DocumentProfileReport()
        assert report.page_count == 0
        assert report.suggested_profile == "general"
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

    def test_format_units_for_prompt_structure(self):
        units = _parse_units_from_teaching_plan(PUCRS_PLAN)
        result = _format_units_for_prompt(units)
        assert "slug:" in result
        assert "Métodos Formais" in result
        assert "Sistemas Formais" in result
        # Sub-topics should be more indented
        lines = result.split("\n")
        sistemas_line = [l for l in lines if "Sistemas Formais" in l][0]
        fundamentos_line = [l for l in lines if "Lógica de Primeira Ordem" in l][0]
        # fundamentos should have more leading whitespace
        assert len(fundamentos_line) - len(fundamentos_line.lstrip()) > len(sistemas_line) - len(sistemas_line.lstrip())

    def test_format_units_for_prompt_empty(self):
        assert _format_units_for_prompt([]) == ""


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

        assert captured_manifest_entries == [[entry_payload]]

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
        assert "Mapear arquivos" in result
        assert "alta incidência" in result
        assert "GLOSSARY.md" in result

    def test_instructions_prefer_maps_before_long_files(self):
        from src.builder.engine import generate_claude_project_instructions
        result = generate_claude_project_instructions(self.META)
        assert "Fluxo `map-first`" in result
        assert "Ordem de leitura econômica" in result
        assert "Comece por `course/COURSE_MAP.md`" in result
        assert "student/STUDENT_STATE.md" in result
        assert "Use `course/FILE_MAP.md` para localizar o material certo" in result
        assert "Só então abra um markdown em `content/`, `exercises/` ou `exams/`" in result


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


class TestBundleSeedLowToken:
    def test_bundle_priority_prefers_exam_relevant_content(self):
        from src.builder.engine import _bundle_priority_score

        exam_entry = {
            "category": "provas",
            "include_in_bundle": False,
            "relevant_for_exam": True,
            "effective_profile": "exam_pdf",
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
                    "effective_profile": "exam_pdf",
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
                    "effective_profile": "layout_heavy",
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
        instructions = (repo / "INSTRUCOES_CLAUDE_PROJETO.md").read_text(encoding="utf-8")
        bundle = json.loads((repo / "build" / "claude-knowledge" / "bundle.seed.json").read_text(encoding="utf-8"))
        lesson = (repo / "content" / "lesson.md").read_text(encoding="utf-8")

        assert "Ordem de consulta econômica" in file_map
        assert "Quando abrir" in file_map
        assert "Mapa pedagógico curto da disciplina" in course_map
        assert "Ordem de leitura econômica" in instructions
        assert bundle["selection_policy"]["goal"] == "baixo-custo-alto-sinal"
        assert bundle["bundle_candidates"][0]["id"] == "entry1"
        assert "> **[Descrição de imagem]** Diagrama de árvore com três níveis e duas ramificações principais." in lesson
        assert "legenda longa" not in lesson


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
