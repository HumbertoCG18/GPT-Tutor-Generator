from pathlib import Path

from src.builder.engine import (
    _clean_extraction_noise,
    _extract_section_headers,
    _infer_unit_confidence,
    _inject_executive_summary,
    file_map_md,
    student_state_md,
)


def test_extract_headers_ignores_code_blocks():
    md = "## Real\n```\n## Fake\n```\n## Also Real\n"
    headers = _extract_section_headers(md)
    assert len(headers) == 2
    assert headers[0]["title"] == "Real"
    assert headers[1]["title"] == "Also Real"


def test_extract_headers_ignores_exec_summary():
    md = (
        "<!-- EXEC_SUMMARY_START -->\n## Fake\n<!-- EXEC_SUMMARY_END -->\n"
        "## Real\n"
    )
    headers = _extract_section_headers(md)
    assert len(headers) == 1
    assert headers[0]["title"] == "Real"


def test_inject_summary_idempotent(tmp_path: Path):
    target = tmp_path / "test.md"
    target.write_text("## Seção 1\nconteúdo\n## Seção 2\nconteúdo", encoding="utf-8")

    assert _inject_executive_summary(target) is True
    first = target.read_text(encoding="utf-8")
    assert _inject_executive_summary(target) is False
    assert target.read_text(encoding="utf-8") == first
    assert "EXEC_SUMMARY_START" in first


def test_inject_skips_single_header(tmp_path: Path):
    target = tmp_path / "test.md"
    target.write_text("## Única seção\nconteúdo", encoding="utf-8")
    assert _inject_executive_summary(target) is False
    assert "EXEC_SUMMARY_START" not in target.read_text(encoding="utf-8")


def test_clean_noise_removes_page_numbers():
    md = "## Seção\n\nconteúdo\n\n12\n\nmais\n\n- 15 -\n\nfim"
    cleaned = _clean_extraction_noise(md)
    lines = cleaned.splitlines()
    assert "12" not in lines
    assert "- 15 -" not in lines
    assert "mais" in cleaned


def test_clean_noise_preserves_code():
    md = "texto\n```python\n15\n---\n```\ntexto final"
    cleaned = _clean_extraction_noise(md)
    assert "15" in cleaned
    assert "---" in cleaned


def test_clean_noise_preserves_block_math():
    md = "texto\n$$\n12\n$$\ntexto final"
    cleaned = _clean_extraction_noise(md)
    assert "\n12\n" in cleaned


def test_clean_noise_limits_blank_lines():
    md = "a\n\n\n\n\nb"
    cleaned = _clean_extraction_noise(md)
    assert "\n\n\n\n" not in cleaned


def test_infer_confidence_manual_override():
    entry = {"manual_unit_slug": "unidade-01", "unit_slug": "unidade-01"}
    assert _infer_unit_confidence(entry) == "Alta"


def test_infer_confidence_no_unit():
    assert _infer_unit_confidence({}) == "Baixa"


def test_file_map_adds_sections_and_confidence_columns(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "content" / "aula1.md").write_text(
        "# Aula 1\n\n## Introdução\ntexto\n\n### Exemplo\ntexto\n\n## Aplicações\ntexto\n",
        encoding="utf-8",
    )
    course_meta = {
        "course_name": "Métodos Formais",
        "_repo_root": repo,
        "_unit_index_for_tests": [
            {"title": "Unidade 1 - Fundamentos", "topics": ["Introdução"]},
        ],
    }
    entries = [
        {
            "title": "Aula 1",
            "category": "material-de-aula",
            "tags": "",
            "base_markdown": "content/aula1.md",
            "raw_target": "raw/aula1.pdf",
            "manual_unit_slug": "unidade-01-fundamentos",
        }
    ]

    result = file_map_md(course_meta, entries)

    assert "Seções" in result
    assert "Confiança" in result
    assert "Introdução  Aplicações" in result
    assert "Alta" in result


def test_student_state_v2_yaml_format():
    result = student_state_md({"course_name": "Métodos Formais"})
    assert result.startswith("---\n")
    assert "course: Métodos Formais" in result
    assert "updated:" in result
    assert "## Histórico de sessões" not in result
    assert "## Progresso por unidade" not in result
    assert result.rstrip().endswith("---")
