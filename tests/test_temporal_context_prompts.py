# -*- coding: utf-8 -*-
"""A seção de contexto temporal entra nas instruções dos 3 geradores."""

from src.builder.artifacts.prompts import (
    generate_claude_project_instructions,
    generate_gpt_instructions,
    generate_gemini_instructions,
)

META = {"course_name": "Cálculo I", "professor": "P", "institution": "I", "semester": "2026/1"}


def test_claude_instructions_include_temporal_section():
    out = generate_claude_project_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out
    assert "prova ≤ 7 dias" in out


def test_gpt_instructions_include_temporal_section():
    out = generate_gpt_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out


def test_gemini_instructions_include_temporal_section():
    out = generate_gemini_instructions(META)
    assert "## Contexto temporal" in out
    assert "setup/CONTEXTO_TEMPORAL.md" in out
