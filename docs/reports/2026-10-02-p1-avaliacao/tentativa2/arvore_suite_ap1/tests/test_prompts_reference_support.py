"""O prompt do tutor explica como usar as linhas 📖 Apoio do COURSE_MAP."""
from src.builder.artifacts import prompts


def test_prompt_explains_support_references():
    text = prompts._prompt_reference_support_text()
    assert "📖 Apoio" in text
    assert "apoio" in text.lower()
    assert "principal" in text.lower()


def test_support_text_is_included_in_main_prompt():
    block = prompts._prompt_reference_support_text()
    assert block.strip() != ""
