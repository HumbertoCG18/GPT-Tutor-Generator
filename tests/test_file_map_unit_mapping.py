from src.builder.engine import (
    UnitMatchResult,
    _auto_map_entry_unit,
    _file_map_markdown_cell,
    _build_file_map_timeline_context_from_course,
    _build_file_map_unit_index_from_course,
    _build_file_map_unit_index,
    _collect_entry_unit_signals,
    _entry_markdown_text_for_file_map,
    _format_file_map_unit_cell,
    _select_probable_period_for_entry,
    _score_entry_against_unit,
    file_map_md,
)
from src.models.core import SubjectProfile


def test_build_file_map_unit_index_normalizes_unit_slugs():
    units = [
        {
            "title": "Unidade 02 — Verificação de Programas",
            "topics": ["2.1. Lógica de Hoare"],
        }
    ]

    index = _build_file_map_unit_index(units)

    assert index[0]["slug"] == "unidade-02-verificacao-de-programas"
    assert "logica de hoare" in index[0]["topic_tokens"]
    assert "hoare" in index[0]["topic_tokens"]


def test_file_map_markdown_cell_hides_staging_targets():
    assert _file_map_markdown_cell("staging/markdown-auto/pymupdf4llm/item.md") == "A revisar"
    assert _file_map_markdown_cell("content/curated/item.md") == "`content/curated/item.md`"


def test_collect_entry_unit_signals_uses_title_category_tags_and_markdown():
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "dafny",
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercícios\n\n## Lógica de Hoare\n\nPré e Pós Condições."

    signals = _collect_entry_unit_signals(entry, markdown)

    assert signals["title_text"] == "exerciciosespecificacao"
    assert signals["category_text"] == "listas"
    assert signals["tags_text"] == "dafny"
    assert "logica de hoare" in signals["markdown_text"]


def test_score_entry_against_unit_prefers_topic_overlap():
    unit = {
        "title": "Unidade 02 — Verificação de Programas",
        "slug": "unidade-02-verificacao-de-programas",
        "normalized_title": "unidade 02 verificacao de programas",
        "topics": ["2.1. Lógica de Hoare", "2.1.1. Pré e Pós Condições"],
        "topic_tokens": ["2 1 logica de hoare", "2 1 1 pre e pos condicoes"],
    }
    signals = {
        "title_text": "exercicios especificacao",
        "category_text": "listas",
        "tags_text": "",
        "raw_text": "raw pdfs listas exercicios especificacao pdf",
        "markdown_text": "logica de hoare pre e pos condicoes",
    }

    score = _score_entry_against_unit(signals, unit)

    assert score > 0


def test_auto_map_entry_unit_matches_exercise_to_recursive_definitions():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": [
                "1.2.2. Especificação de Conjuntos Indutivos",
                "1.2.3. Especificação de Funções Recursivas",
            ],
        },
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": [
                "2.1. Lógica de Hoare",
                "2.1.1. Pré e Pós Condições",
            ],
        },
    ]
    entry = {
        "title": "Exerciciosformalizacaoalgoritmosrecursao",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
    }

    result = _auto_map_entry_unit(entry, units, markdown_text="")

    assert isinstance(result, UnitMatchResult)
    assert result.slug == "unidade-01-metodos-formais"
    assert result.confidence > 0


def test_auto_map_entry_unit_uses_markdown_headings_as_signal():
    units = [
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": [
                "2.1. Lógica de Hoare",
                "2.1.2. Correção Parcial e Total",
            ],
        },
        {
            "title": "Unidade 03 — Verificação de Modelos",
            "slug": "unidade-03-verificacao-de-modelos",
            "topics": [
                "3.1. Máquinas de Estado",
                "3.2. Lógicas Temporais",
            ],
        },
    ]
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercícios\n\n## Lógica de Hoare\n\n### Pré e Pós Condições\n"

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown)

    assert result.slug == "unidade-02-verificacao-de-programas"


def test_auto_map_entry_unit_marks_ambiguous_when_scores_tie():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": ["Lógica", "Sistemas Formais"],
        },
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": ["Lógica", "Programas"],
        },
    ]
    entry = {
        "title": "Revisao",
        "category": "material-de-aula",
        "tags": "",
        "raw_target": "raw/pdfs/material-de-aula/revisao.pdf",
    }

    result = _auto_map_entry_unit(entry, units, markdown_text="Revisão geral de lógica.")

    assert result.slug in {
        "unidade-01-metodos-formais",
        "unidade-02-verificacao-de-programas",
    }
    assert result.confidence < 0.5
    assert result.ambiguous is True


def test_auto_map_entry_unit_prefers_verification_programs_for_specification_sheet():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": [
                "1.2.2. Especificação de Conjuntos Indutivos",
                "1.2.3. Especificação de Funções Recursivas",
            ],
        },
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": [
                "2.1. Lógica de Hoare",
                "2.1.1. Pré e Pós Condições",
                "2.1.2. Correção Parcial e Total",
            ],
        },
    ]
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = (
        "# Exercícios\n\n"
        "Com base nessas respostas, construa uma especificação formal para pré e pós condições.\n"
        "Utilize fórmulas em lógica de predicados.\n"
    )

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown)

    assert result.slug == "unidade-02-verificacao-de-programas"
    assert result.confidence > 0.45


def test_auto_map_entry_unit_avoids_forcing_temporal_models_for_propositional_semantics():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": [
                "1.2. Linguagens de Especificação e Lógicas",
                "1.2.1. Fundamentos de Lógica de Primeira Ordem",
            ],
        },
        {
            "title": "Unidade 03 — Verificação de Modelos",
            "slug": "unidade-03-verificacao-de-modelos",
            "topics": [
                "3.1. Máquinas de Estado",
                "3.1.1. Modelos de Kripke",
                "3.2. Fundamentos de Lógicas Temporais",
            ],
        },
    ]
    entry = {
        "title": "Logicaproposicional Semantica",
        "category": "material-de-aula",
        "tags": "",
        "raw_target": "raw/pdfs/material-de-aula/logicaproposicional-semantica.pdf",
    }
    markdown = (
        "# Lógica Proposicional\n\n"
        "Semântica.\n"
        "O estudo da semântica da lógica proposicional consiste em atribuir valores verdade.\n"
    )

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown)

    assert result.slug == "unidade-01-metodos-formais"
    assert result.ambiguous is True or result.confidence >= 0.35


def test_format_file_map_unit_cell_marks_ambiguous_result():
    text = _format_file_map_unit_cell(
        slug="unidade-01-metodos-formais",
        confidence=0.32,
        ambiguous=True,
    )

    assert "unidade-01-metodos-formais" in text
    assert "ambíguo" in text


def test_file_map_md_auto_fills_unit_column_from_subject_profile(tmp_path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    md_file = md_dir / "exerciciosespecificacao.md"
    md_file.write_text(
        "# Exercícios\n\n## Lógica de Hoare\n\n### Pré e Pós Condições\n",
        encoding="utf-8",
    )

    course_meta = {"course_name": "Métodos Formais", "_repo_root": repo}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Pré e Pós Condições
""".strip()
        ,
        syllabus="""
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-02 | Unidade 1: Métodos Formais |
| 2 | 2026-03-16 | Unidade 2: Verificação de Programas - Lógica de Hoare |
| 3 | 2026-03-27 | Unidade 2: Verificação de Programas - Pré e Pós Condições |
""".strip()
    )
    entries = [
        {
            "title": "Exerciciosespecificacao",
            "category": "listas",
            "tags": "",
            "base_markdown": "exercises/lists/exerciciosespecificacao.md",
            "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
        }
    ]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "unidade-02-verificacao-de-programas" in result
    assert "2026-03-16" in result
    assert "Exerciciosespecificacao" in result


def test_file_map_md_refines_period_by_subtopic_within_unit(tmp_path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    md_file = md_dir / "exerciciosformalizacaoalgoritmosrecursao.md"
    md_file.write_text(
        "# Exercícios\n\n## Formalização de Algoritmos — Recursão\n\n### Definições indutivas e recursivas\n",
        encoding="utf-8",
    )

    course_meta = {"course_name": "Métodos Formais", "_repo_root": repo}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais
- Linguagens de Especificação e Lógicas
- Especificação de Conjuntos Indutivos
- Especificação de Funções Recursivas
""".strip()
        ,
        syllabus="""
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-04 | Unidade 1: Métodos Formais |
| 2 | 2026-03-16 | definições indutivas e recursivas, exercícios |
| 3 | 2026-03-18 | definições indutivas e recursivas sobre listas |
| 4 | 2026-03-23 | definições indutivas e recursivas sobre árvores |
| 5 | 2026-03-25 | exercícios |
| 6 | 2026-03-27 | atividade assíncrona: complementar os estudos com as leituras recomendadas, realizar os exercícios. |
""".strip()
    )
    entries = [
        {
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "tags": "",
            "base_markdown": "exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md",
            "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
        }
    ]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "unidade-01-metodos-formais" in result
    assert "2026-03-16" in result
    assert "Exerciciosformalizacaoalgoritmosrecursao" in result


def test_file_map_md_prefers_exercise_block_over_intro_row_in_realistic_schedule(tmp_path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    md_file = md_dir / "exerciciosformalizacaoalgoritmosrecursao.md"
    md_file.write_text(
        "# Exercícios\n\n## Formalização de Algoritmos — Recursão\n\n### Exercícios\n",
        encoding="utf-8",
    )

    course_meta = {"course_name": "Métodos Formais", "_repo_root": repo}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais
- Linguagens de Especificação e Lógicas
- Especificação de Conjuntos Indutivos
- Especificação de Funções Recursivas
""".strip(),
        syllabus="""
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
|---|---|---|---|---|---|---|
| 4 | QUA | 11/03/2026 | LM 19:15 - 20:45 | Conjuntos indutivos e equações recursivas | Aula |  |
| 5 | SEG | 16/03/2026 | LM 19:15 - 20:45 | Exercícios | Aula |  |
| 6 | QUA | 18/03/2026 | LM 19:15 - 20:45 | Estudo de caso: listas | Aula |  |
| 7 | SEG | 23/03/2026 | LM 19:15 - 20:45 | Estudo de caso: árvores | Aula |  |
| 8 | QUA | 25/03/2026 | LM 19:15 - 20:45 | Exercícios | Aula |  |
| 9 | SEG | 30/03/2026 | LM 19:15 - 20:45 | Provas por indução | Aula |  |
""".strip(),
    )
    entries = [
        {
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "tags": "",
            "base_markdown": "exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md",
            "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
        }
    ]

    markdown_text = _entry_markdown_text_for_file_map(repo, entries[0])
    unit_index = _build_file_map_unit_index_from_course(course_meta, subject_profile)
    unit_match = _auto_map_entry_unit(entries[0], unit_index, markdown_text)
    timeline_context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    unit_rows = timeline_context["rows_by_unit"][unit_match.slug]
    unit_by_slug = {unit["slug"]: unit for unit in unit_index}

    probable_period, _, period_ambiguous, _ = _select_probable_period_for_entry(
        entry=entries[0],
        unit=unit_by_slug[unit_match.slug],
        candidate_rows=unit_rows,
        markdown_text=markdown_text,
    )

    assert unit_match.slug == "unidade-01-metodos-formais"
    assert period_ambiguous is False
    assert probable_period == "11/03/2026 a 25/03/2026"


def test_file_map_timeline_context_filters_rows_outside_unit_period():
    course_meta = {"course_name": "Métodos Formais"}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais
- Linguagens de Especificação e Lógicas

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Invariantes de Laço
""".strip(),
        syllabus="""
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
|---|---|---|---|---|---|---|
| 1 | QUA | 04/03/2026 | LM 19:15 - 20:45 | Introdução a Métodos Formais | Aula |  |
| 2 | QUA | 11/03/2026 | LM 19:15 - 20:45 | Conjuntos indutivos e equações recursivas | Aula |  |
| 3 | SEG | 16/03/2026 | LM 19:15 - 20:45 | Exercícios | Aula |  |
| 4 | SEG | 27/04/2026 | LM 19:15 - 20:45 | Lógica de Hoare | Aula |  |
| 5 | QUA | 06/05/2026 | LM 19:15 - 20:45 | Invariantes de Laço | Aula |  |
""".strip(),
    )

    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    unit1_rows = context["rows_by_unit"]["unidade-01-metodos-formais"]
    unit1_dates = {row["date_text"] for row in unit1_rows}

    assert "27/04/2026" not in unit1_dates
    assert "06/05/2026" not in unit1_dates


def test_file_map_md_keeps_period_column_empty_without_subject_profile():
    course_meta = {"course_name": "Métodos Formais"}
    entries = [
        {
            "title": "Aula 1",
            "category": "material-de-aula",
            "tags": "",
            "base_markdown": "content/aula-1.md",
            "raw_target": "raw/aula-1.pdf",
        }
    ]

    result = file_map_md(course_meta, entries)

    assert "| Unidade | Período |" in result
    assert "Aula 1" in result


def test_file_map_md_omits_period_for_ambiguous_match():
    course_meta = {
        "course_name": "Métodos Formais",
        "_unit_index_for_tests": [
            {"title": "Unidade 01 — Métodos Formais", "topics": ["Lógica", "Sistemas Formais"]},
            {"title": "Unidade 02 — Verificação de Programas", "topics": ["Lógica", "Programas"]},
        ],
        "_period_index_for_tests": {
            "unidade-01-metodos-formais": "2026-03-04 a 2026-05-04",
            "unidade-02-verificacao-de-programas": "2026-05-06 a 2026-06-10",
        },
    }
    entries = [
        {
            "title": "Revisao",
            "category": "material-de-aula",
            "tags": "",
            "base_markdown": "content/curated/revisao.md",
            "raw_target": "raw/pdfs/material-de-aula/revisao.pdf",
            "_markdown_text_for_tests": "Revisão geral de lógica.",
        }
    ]

    result = file_map_md(course_meta, entries)

    assert "unidade-01-metodos-formais _(ambíguo)_" in result
    assert "2026-03-04 a 2026-05-04" not in result
