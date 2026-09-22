"""Issue #50: rotulo de bloco de avaliacao (P1/P2/PS/G2/PF) a partir do texto
cru, secao 'PROCEDIMENTOS E CRITERIOS DE AVALIACAO' do plano de ensino (FR),
e unidades selecionaveis mesmo sem bloco (unidade 06 do FR na taxonomia)."""

import json

from src.builder.timeline.index import (
    _assessment_block_label,
    _parse_assessments_from_teaching_plan,
    _normalize_match_text,
)
from src.builder.extraction.teaching_plan import _normalize_teaching_plan_heading
from src.ui.timeline_dashboard import _available_unit_slugs


def test_assessment_block_label():
    assert _assessment_block_label(
        {"period_label": "1 dia · 26/11/2026", "sessions": [{"label": "prova 2 prova"}]}
    ) == "P2"
    assert _assessment_block_label(
        {"period_label": "1 dia · 24/09/2026", "sessions": [{"label": "prova p1 prova"}]}
    ) == "P1"
    assert _assessment_block_label(
        {"period_label": "1 dia · 05/12/2026", "sessions": [{"label": "prova final"}]}
    ) == "PF"
    assert _assessment_block_label(
        {"period_label": "1 dia · 01/12/2026", "sessions": [{"label": "prova ps prova de substituicao"}]}
    ) == "PS"
    assert _assessment_block_label(
        {"period_label": "1 dia · 05/12/2026", "sessions": [{"label": "p final"}]}
    ) == "PF"
    assert _assessment_block_label({}) == ""


_FR_TEACHING_PLAN_TEXT = """## **Nº DA UNIDADE: 06**

CONTEÚDO: Nível físico

- 6.1. Classificação e topologias de redes de computadores

## **PROCEDIMENTOS E CRITÉRIOS DE AVALIAÇÃO:**

G1 = (2*P1 + 2*P2 + TF) / 5

Onde:

P1 – Prova versando sobre as unidades 01, 02 e 03.

P2 – Prova versando sobre as unidades 04, 05 e 06.

TF – Trabalho final da disciplina.

## **BIBLIOGRAFIA BÁSICA:**
"""


def test_parse_assessments_from_teaching_plan_heading_ends_in_avaliacao():
    items = _parse_assessments_from_teaching_plan(
        _FR_TEACHING_PLAN_TEXT,
        normalize_match_text=_normalize_match_text,
        normalize_teaching_plan_heading=_normalize_teaching_plan_heading,
    )
    assert len(items) == 2
    assert [item["label"] for item in items] == ["P1", "P2"]
    assert items[0]["declared_unit_numbers"] == [1, 2, 3]
    assert items[1]["declared_unit_numbers"] == [4, 5, 6]


def test_parse_assessments_from_teaching_plan_heading_starts_with_avaliacao_regression():
    text = """AVALIAÇÃO:

P1 - unidades 1 e 2

BIBLIOGRAFIA:
"""
    items = _parse_assessments_from_teaching_plan(
        text,
        normalize_match_text=_normalize_match_text,
        normalize_teaching_plan_heading=_normalize_teaching_plan_heading,
    )
    assert len(items) == 1
    assert items[0]["label"] == "P1"
    assert items[0]["declared_unit_numbers"] == [1, 2]


def test_parse_assessments_from_teaching_plan_ementa_sentence_does_not_open_section():
    text = (
        "Desenvolvimento de experimentos que abranjam análise do funcionamento e "
        "avaliação de desempenho de protocolos da Arquitetura Internet."
    )
    items = _parse_assessments_from_teaching_plan(
        text,
        normalize_match_text=_normalize_match_text,
        normalize_teaching_plan_heading=_normalize_teaching_plan_heading,
    )
    assert items == []


def test_available_unit_slugs_includes_taxonomy_units_without_block(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    taxonomy = {
        "units": [
            {"slug": "unidade-06-nivel-fisico"},
            {"slug": "unidade-02-nivel-de-aplicacao"},
        ]
    }
    (course_dir / ".content_taxonomy.json").write_text(
        json.dumps(taxonomy, ensure_ascii=False), encoding="utf-8"
    )
    blocks = [{"unit_slug": "unidade-02-nivel-de-aplicacao"}, {"unit_slug": ""}]
    assert _available_unit_slugs(blocks, course_dir) == [
        "unidade-02-nivel-de-aplicacao",
        "unidade-06-nivel-fisico",
    ]


def test_available_unit_slugs_without_taxonomy_on_disk(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    blocks = [{"unit_slug": "unidade-02-nivel-de-aplicacao"}, {"unit_slug": ""}]
    assert _available_unit_slugs(blocks, course_dir) == ["unidade-02-nivel-de-aplicacao"]
