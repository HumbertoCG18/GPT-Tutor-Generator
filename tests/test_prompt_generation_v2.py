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


def test_all_platforms_include_importable_student_state_block_as_default():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "bloco importável" in text.lower()
        assert "Student State" in text
        assert "unit:" in text
        assert "topic:" in text
        assert "topic_title:" in text
        assert "## Resumo da sessão" in text


def test_all_platforms_keep_manual_dictation_as_fallback():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "Ditado de fim de sessão" in text
        assert "Append em `student/batteries/<unit>/<topic>.md`" in text


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


def test_latex_rendering_helper_present_in_gpt_and_gemini():
    from src.builder.artifacts.prompts import generate_gpt_instructions, generate_gemini_instructions
    meta = {"course_name": "Métodos Formais"}
    for fn in (generate_gpt_instructions, generate_gemini_instructions):
        result = fn(meta, [], "")
        assert "inline" in result, f"{fn.__name__}: bloco de renderização LaTeX ausente"
        assert "display" in result, f"{fn.__name__}: sintaxe display LaTeX ausente"


def test_accessibility_helper_present_in_gpt_and_gemini():
    from src.builder.artifacts.prompts import generate_gpt_instructions, generate_gemini_instructions
    meta = {"course_name": "Métodos Formais"}
    for fn in (generate_gpt_instructions, generate_gemini_instructions):
        result = fn(meta, [], "")
        assert "dislexia" in result, f"{fn.__name__}: bloco de acessibilidade ausente"
        assert "Etapa 2" in result, f"{fn.__name__}: decomposição parte a parte ausente"
        assert "Analogia" in result or "Etapa 3" in result, f"{fn.__name__}: etapa de analogia ausente"
