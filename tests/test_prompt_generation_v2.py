from src.builder.artifacts.prompts import (
    generate_claude_project_instructions,
    generate_gpt_instructions,
    generate_gemini_instructions,
)


def _common():
    meta = {"course_name": "Cálculo", "professor": "P", "institution": "I", "semester": "S"}
    return meta


def test_claude_instrucoes_describe_v2_yaml_format():
    text = generate_claude_project_instructions(_common())
    assert "STUDENT_STATE" in text
    assert "YAML" in text or "yaml" in text
    assert "active_unit_progress" in text
    assert "Histórico de sessões" not in text


def test_all_platforms_include_two_block_dictation_template():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "batteries/" in text
        assert "active_unit_progress" in text


def test_all_platforms_include_consolidation_detection_rule():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "Consolidar unidade" in text or "consolidar" in text.lower()


def test_all_platforms_include_revision_dictation():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "reestudar" in text.lower() or "revisão" in text.lower()


def test_no_legacy_history_table_references():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "Histórico de sessões" not in text
        assert "Progresso por unidade" not in text
