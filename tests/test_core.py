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
    rows_to_markdown_table,
    wrap_frontmatter,
    _parse_units_from_teaching_plan,
    _parse_bibliography_from_teaching_plan,
    _parse_syllabus_timeline,
    _match_timeline_to_units,
    _topic_text,
    _topic_depth,
    _format_units_for_prompt,
    course_map_md,
    file_map_md,
)
from src.models.core import (
    DocumentProfileReport,
    FileEntry,
    PipelineDecision,
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
        assert entry.document_profile == "auto"
        assert entry.preferred_backend == "auto"
        assert entry.include_in_bundle is True
        assert entry.relevant_for_exam is True


# ---------------------------------------------------------------------------
# BackendSelector
# ---------------------------------------------------------------------------

class TestBackendSelector:
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
        assert "glossário" in result.lower()


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
