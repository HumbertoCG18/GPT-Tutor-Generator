import json
from datetime import datetime

from src.builder.engine import (
    UnitMatchResult,
    TopicMatchResult,
    _build_content_taxonomy,
    _build_timeline_index,
    _auto_map_entry_subtopic,
    _auto_map_entry_unit,
    _derive_unit_from_topic_match,
    _file_map_markdown_cell,
    _build_file_map_timeline_context_from_course,
    _build_file_map_unit_index_from_course,
    _build_file_map_unit_index,
    _collect_entry_unit_signals,
    _entry_markdown_text_for_file_map,
    _format_file_map_unit_cell,
    _select_probable_period_for_entry,
    _score_entry_against_unit,
    _score_entry_against_timeline_block,
    _serialize_timeline_index,
    _write_internal_content_taxonomy,
    file_map_md,
    _resolve_entry_manual_timeline_block,
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


def test_build_content_taxonomy_emits_repo_scoped_unit_topic_tree():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 1 - Metodos Formais
- 1.1 Sistemas Formais
- 1.3.3 Provadores de Teoremas

### Unidade 2 - Verificacao de Programas
- 2.1 Logica de Hoare
""".strip(),
        course_map_md="# COURSE_MAP - Metodos Formais",
        glossary_md="""
## Provadores de Teoremas
**Definicao:** Prova interativa.
**Sinonimos aceitos:** Isabelle, theorem proving
**Aparece em:** Unidade 1 - Metodos Formais

## Logica de Hoare
**Definicao:** Correcao de programas.
**Sinonimos aceitos:** pre e pos condicoes
**Aparece em:** Unidade 2 - Verificacao de Programas
""".strip(),
    )

    assert taxonomy["version"] == 1
    assert taxonomy["course_slug"] == "metodos-formais"
    unit_slugs = [unit["slug"] for unit in taxonomy["units"]]
    assert unit_slugs == [
        "unidade-01-metodos-formais",
        "unidade-02-verificacao-de-programas",
    ]

    unit1 = taxonomy["units"][0]
    topic_slugs = [topic["slug"] for topic in unit1["topics"]]
    assert "sistemas-formais" in topic_slugs
    assert "provadores-de-teoremas" in topic_slugs

    provadores = next(topic for topic in unit1["topics"] if topic["slug"] == "provadores-de-teoremas")
    assert "Isabelle" in provadores["aliases"]
    assert "theorem proving" in provadores["aliases"]


def test_build_content_taxonomy_enriches_official_topic_aliases_from_supported_headings():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 1 - Metodos Formais
- 1.2 Linguagens de Especificacao e Logicas
- 1.2.3 Especificacao de Funcoes Recursivas
""".strip(),
        course_map_md="# COURSE_MAP - Metodos Formais",
        glossary_md="",
        strong_headings=[
            "Lógica Proposicional",
            "Formalização de algoritmos como equações recursivas",
        ],
    )

    unit1 = taxonomy["units"][0]
    topic_by_slug = {topic["slug"]: topic for topic in unit1["topics"]}

    assert "logica-proposicional" not in topic_by_slug
    assert "formalizacao-de-algoritmos-como-equacoes-recursivas" not in topic_by_slug
    assert "Lógica Proposicional" in topic_by_slug["linguagens-de-especificacao-e-logicas"]["aliases"]
    assert (
        "Formalização de algoritmos como equações recursivas"
        in topic_by_slug["especificacao-de-funcoes-recursivas"]["aliases"]
    )


def test_build_timeline_index_annotates_primary_topic_and_derives_unit_from_winner():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [
                    {
                        "slug": "provadores-de-teoremas",
                        "label": "Provadores de Teoremas",
                        "aliases": ["Isabelle"],
                        "kind": "subtopic",
                        "unit_slug": "unidade-01-metodos-formais",
                    }
                ],
            },
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "logica-de-hoare",
                        "label": "Logica de Hoare",
                        "aliases": ["pre e pos condicoes"],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    }
                ],
            },
        ],
    }
    candidate_rows = [
        {
            "index": 1,
            "date_dt": datetime(2026, 4, 6),
            "date_text": "06/04/2026",
            "content": "Prova interativa de teoremas - Isabelle",
        },
        {
            "index": 2,
            "date_dt": datetime(2026, 4, 8),
            "date_text": "08/04/2026",
            "content": "Prova interativa de teoremas - Isabelle",
        },
    ]

    timeline_index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy=taxonomy)
    block = timeline_index["blocks"][0]

    assert block["primary_topic_slug"] == "provadores-de-teoremas"
    assert block["unit_slug"] == "unidade-01-metodos-formais"
    assert block["topic_candidates"]
    assert block["topic_candidates"][0]["topic_slug"] == "provadores-de-teoremas"
    assert block["topic_candidates"][0]["unit_slug"] == "unidade-01-metodos-formais"
    assert block["primary_topic_confidence"] > 0


def test_build_timeline_index_leaves_administrative_blocks_without_topic():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [
                    {
                        "slug": "sistemas-formais",
                        "label": "Sistemas Formais",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-metodos-formais",
                    }
                ],
            }
        ],
    }
    candidate_rows = [
        {
            "index": 1,
            "date_dt": datetime(2026, 4, 20),
            "date_text": "20/04/2026",
            "content": "Suspensao das aulas",
        }
    ]

    timeline_index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy=taxonomy)
    block = timeline_index["blocks"][0]

    assert block["primary_topic_slug"] == ""
    assert block["topic_candidates"] == []
    assert block["unit_slug"] == ""


def test_build_timeline_index_keeps_weak_generic_topic_unassigned():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [
                    {
                        "slug": "termo",
                        "label": "Termo",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-metodos-formais",
                    }
                ],
            },
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "termo",
                        "label": "Termo",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    }
                ],
            },
        ],
    }
    candidate_rows = [
            {
                "index": 1,
                "date_dt": datetime(2026, 4, 27),
                "date_text": "27/04/2026",
                "content": "Termos gerais",
            }
        ]

    timeline_index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy=taxonomy)
    block = timeline_index["blocks"][0]

    assert block["primary_topic_slug"] == ""
    assert block["topic_candidates"] == []
    assert block["unit_slug"] == ""


def test_write_internal_content_taxonomy_persists_json(tmp_path):
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [],
            }
        ],
    }

    _write_internal_content_taxonomy(tmp_path, taxonomy)
    persisted = json.loads((tmp_path / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))

    assert persisted == taxonomy


def test_file_map_markdown_cell_hides_staging_targets():
    assert _file_map_markdown_cell("staging/markdown-auto/pymupdf4llm/item.md") == "A revisar"
    assert _file_map_markdown_cell("content/curated/item.md") == "`content/curated/item.md`"


def test_collect_entry_unit_signals_uses_title_category_tags_and_markdown():
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "dafny",
        "manual_tags": ["topico:logica-de-hoare"],
        "auto_tags": ["tipo:lista"],
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercícios\n\n## Lógica de Hoare\n\nPré e Pós Condições."

    signals = _collect_entry_unit_signals(entry, markdown)

    assert signals["title_text"] == "exerciciosespecificacao"
    assert signals["category_text"] == "listas"
    assert "dafny" in signals["tags_text"]
    assert "topico logica de hoare" in signals["tags_text"]
    assert "tipo lista" in signals["tags_text"]
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


def test_auto_map_entry_unit_uses_topic_index_to_break_ties_for_propositional_logic():
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
                "3.2. Fundamentos de Lógicas Temporais",
            ],
        },
    ]
    topic_index = [
        {
            "unit_slug": "unidade-01-metodos-formais",
            "topic_slug": "logica-proposicional",
            "topic_label": "Lógica Proposicional",
            "kind": "subtopic",
        },
        {
            "unit_slug": "unidade-03-verificacao-de-modelos",
            "topic_slug": "logicas-temporais",
            "topic_label": "Lógicas Temporais",
            "kind": "subtopic",
        },
    ]
    entry = {
        "title": "Logicaproposicional Sintaxe",
        "category": "material-de-aula",
        "tags": "",
        "raw_target": "raw/pdfs/material-de-aula/logicaproposicional-sintaxe.pdf",
    }
    markdown = "# LÓGICA PROPOCIONAL\n\nComposição de proposições.\n"

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown, topic_index=topic_index)

    assert result.slug == "unidade-01-metodos-formais"
    assert result.ambiguous is False
    assert result.confidence >= 0.55


def test_auto_map_entry_unit_ignores_generic_state_tokens_when_content_matches_unit_one():
    units = [
        {
            "title": "Unidade 01 - Metodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": [
                "1.1. Sistemas Formais",
                "1.2. Linguagens de Especificação e Lógicas",
                "1.2.1. Fundamentos de Lógica de Primeira Ordem",
            ],
        },
        {
            "title": "Unidade 03 - Verificacao de Modelos",
            "slug": "unidade-03-verificacao-de-modelos",
            "topics": [
                "3.1. Máquinas de Estado",
                "3.1.1. Modelos de Kripke",
                "3.2. Fundamentos de Lógicas Temporais",
            ],
        },
    ]
    entry = {
        "title": "Logicaproposicional Sintaxe",
        "category": "material-de-aula",
        "tags": "",
        "raw_target": "raw/pdfs/material-de-aula/logicaproposicional-sintaxe.pdf",
    }
    markdown = (
        "# Sintaxe\n\n"
        "## Estados da computação\n\n"
        "A sequência de estados da computação e variáveis.\n"
    )

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown)

    assert result.slug == "unidade-01-metodos-formais"


def test_auto_map_entry_subtopic_prefers_specific_topic_and_derives_unit():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [
                    {
                        "slug": "sistemas-formais",
                        "label": "Sistemas Formais",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-metodos-formais",
                    },
                    {
                        "slug": "provadores-de-teoremas",
                        "label": "Provadores de Teoremas",
                        "aliases": ["Isabelle"],
                        "kind": "subtopic",
                        "unit_slug": "unidade-01-metodos-formais",
                    },
                ],
            },
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "logica-de-hoare",
                        "label": "Logica de Hoare",
                        "aliases": ["pre e pos condicoes"],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                    {
                        "slug": "pre-e-pos-condicoes",
                        "label": "Pre e Pos Condicoes",
                        "aliases": [],
                        "kind": "subtopic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                ],
            },
        ],
    }
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercicios\n\n## Logica de Hoare\n\n### Pre e Pos Condicoes\n"

    result = _auto_map_entry_subtopic(entry, taxonomy, markdown)
    derived_unit = _derive_unit_from_topic_match(result, taxonomy)

    assert isinstance(result, TopicMatchResult)
    assert result.topic_slug in {"logica-de-hoare", "pre-e-pos-condicoes"}
    assert derived_unit == "unidade-02-verificacao-de-programas"
    assert result.confidence > 0


def test_auto_map_entry_subtopic_prefers_title_and_headings_over_late_body_mentions():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-01-metodos-formais",
                "title": "Unidade 1 - Metodos Formais",
                "topics": [
                    {
                        "slug": "especificacao-de-funcoes-recursivas",
                        "label": "Especificacao de Funcoes Recursivas",
                        "aliases": ["equacoes recursivas"],
                        "kind": "subtopic",
                        "unit_slug": "unidade-01-metodos-formais",
                    },
                ],
            },
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "pre-e-pos-condicoes",
                        "label": "Pre e Pos Condicoes",
                        "aliases": [],
                        "kind": "subtopic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                ],
            },
        ],
    }
    entry = {
        "title": "Formalizacaoalgoritmos Recursao",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/formalizacaoalgoritmos-recursao.pdf",
    }
    markdown = (
        "# Formalizando a Noção de Algoritmo Via Equações Recursivas\n\n"
        "## Tipos de recursão\n\n"
        "Descrição de equações recursivas e recursão na cauda.\n\n"
        "## Observação final\n\n"
        "Também podemos explicitar as pré e pós condições quando necessário.\n"
    )

    result = _auto_map_entry_subtopic(entry, taxonomy, markdown)
    derived_unit = _derive_unit_from_topic_match(result, taxonomy)

    assert result.topic_slug == "especificacao-de-funcoes-recursivas"
    assert derived_unit == "unidade-01-metodos-formais"


def test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 1 - Metodos Formais
- 1.2 Linguagens de Especificacao e Logicas
""".strip(),
        course_map_md="# COURSE_MAP - Metodos Formais",
        glossary_md="",
        strong_headings=["Lógica Proposicional"],
    )
    entry = {
        "title": "Logicaproposicional Sintaxe",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/logicaproposicional-sintaxe.pdf",
    }
    markdown = "# Lógica Proposicional\n\n# Sintaxe\n\nFórmulas bem-formadas."

    result = _auto_map_entry_subtopic(entry, taxonomy, markdown)
    derived_unit = _derive_unit_from_topic_match(result, taxonomy)

    assert result.topic_slug == "linguagens-de-especificacao-e-logicas"
    assert derived_unit == "unidade-01-metodos-formais"


def test_derive_unit_from_topic_match_uses_topic_unit_when_present():
    taxonomy = {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "logica-de-hoare",
                        "label": "Logica de Hoare",
                        "aliases": ["pre e pos condicoes"],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                ],
            },
        ],
    }
    match = TopicMatchResult(
        topic_slug="logica-de-hoare",
        topic_label="Logica de Hoare",
        unit_slug="unidade-02-verificacao-de-programas",
        confidence=0.93,
    )

    assert _derive_unit_from_topic_match(match, taxonomy) == "unidade-02-verificacao-de-programas"


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


def test_file_map_timeline_context_exposes_blocks_by_unit():
    course_meta = {"course_name": "Métodos Formais"}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
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
""".strip(),
    )

    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    blocks = context["blocks_by_unit"]["unidade-01-metodos-formais"]

    assert context["timeline_index"]["version"] == 3
    assert blocks[0]["period_label"] == "11/03/2026 a 25/03/2026"


def test_build_timeline_index_serializes_sessions_inside_block():
    candidate_rows = [
        {
            "index": 1,
            "date_dt": datetime(2026, 3, 30),
            "date_text": "30/03/2026",
            "content": "Card: Especificações recursivas e provas por indução",
        },
        {
            "index": 2,
            "date_dt": datetime(2026, 3, 31),
            "date_text": "",
            "content": "Atividade assíncrona: Complementar os estudos com as leituras recomendadas",
        },
        {
            "index": 3,
            "date_dt": datetime(2026, 4, 1),
            "date_text": "01/04/2026",
            "content": "Card: Especificações recursivas e provas por indução",
        },
    ]

    timeline_index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy={})
    serialized = _serialize_timeline_index(timeline_index)

    assert timeline_index["version"] == 3
    assert serialized["version"] == 3
    assert timeline_index["blocks"][0]["card_evidence"]
    assert timeline_index["blocks"][0]["card_evidence"][0]["normalized_title"] == "especificacoes recursivas e provas por inducao"
    assert timeline_index["blocks"][0]["sessions"]
    assert [item["kind"] for item in timeline_index["blocks"][0]["sessions"]] == ["class", "async", "class"]
    assert timeline_index["blocks"][0]["sessions"][0]["date"] == "2026-03-30"
    assert timeline_index["blocks"][0]["sessions"][1]["date"] == ""
    assert timeline_index["blocks"][0]["sessions"][2]["date"] == "2026-04-01"
    assert timeline_index["blocks"][0]["sessions"][0]["card_evidence"][0]["normalized_title"] == "especificacoes recursivas e provas por inducao"
    assert timeline_index["blocks"][0]["sessions"][2]["card_evidence"][0]["normalized_title"] == "especificacoes recursivas e provas por inducao"
    assert serialized["blocks"][0]["sessions"] == timeline_index["blocks"][0]["sessions"]


def test_file_map_timeline_context_extends_program_verification_unit_with_glossary_and_topic_vocab():
    course_meta = {"course_name": "Métodos Formais"}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Correção Parcial e Total
- Invariante e Variante de Laço
""".strip(),
        syllabus="""
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
|---|---|---|---|---|---|---|
| 16 | SEG | 27/04/2026 | LM 19:15 - 20:45 | Lógica de Hoare | Aula |  |
| 19 | QUA | 06/05/2026 | LM 19:15 - 20:45 | Lógica de Programas, Correção Parcial, Correção Total e Terminação, Invariantes de Laço | Aula |  |
| 20 | SEG | 11/05/2026 | LM 19:15 - 20:45 | Terminação, introdução ao Dafny | Aula |  |
| 21 | QUA | 13/05/2026 | LM 19:15 - 20:45 | Lógica de Programas - Dafny | Aula |  |
| 22 | SEG | 18/05/2026 | LM 19:15 - 20:45 | Lógica de Programas - coleções Dafny (arrays) | Aula |  |
| 28 | SEG | 08/06/2026 | LM 19:15 - 20:45 | Lógica de Programas - orientação a objetos Dafny (ghosts, autocontrato) | Aula |  |
| 30 | SEG | 15/06/2026 | LM 19:15 - 20:45 | Verificação de modelos, lógica temporal | Aula |  |
""".strip(),
    )

    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)

    assert context["unit_periods"]["unidade-02-verificacao-de-programas"] == "27/04/2026 a 08/06/2026"


def test_select_probable_period_for_entry_prefers_blocks_matching_subtopic():
    unit = {
        "slug": "unidade-01-metodos-formais",
        "title": "Unidade 1 — Métodos Formais",
    }
    blocks = [
        {
            "id": "bloco-01",
            "period_label": "16/03/2026 a 18/03/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "conjuntos-indutivos",
            "primary_topic_label": "Conjuntos Indutivos",
            "primary_topic_confidence": 0.92,
            "topic_ambiguous": False,
            "topic_candidates": [
                {
                    "topic_slug": "conjuntos-indutivos",
                    "topic_label": "Conjuntos Indutivos",
                    "unit_slug": "unidade-01-metodos-formais",
                }
            ],
            "rows": [
                {"index": 1, "date_text": "16/03/2026", "content": "Exercícios"},
                {"index": 2, "date_text": "18/03/2026", "content": "Exercícios"},
            ],
        },
        {
            "id": "bloco-02",
            "period_label": "23/03/2026 a 25/03/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "provadores-de-teoremas",
            "primary_topic_label": "Provadores de Teoremas",
            "primary_topic_confidence": 0.98,
            "topic_ambiguous": False,
            "topic_candidates": [
                {
                    "topic_slug": "provadores-de-teoremas",
                    "topic_label": "Provadores de Teoremas",
                    "unit_slug": "unidade-01-metodos-formais",
                }
            ],
            "rows": [
                {"index": 3, "date_text": "23/03/2026", "content": "Exercícios"},
                {"index": 4, "date_text": "25/03/2026", "content": "Exercícios"},
            ],
        },
    ]
    entry = {
        "title": "Isabelle",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/isabelle.pdf",
    }

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=unit,
        candidate_rows=blocks,
        markdown_text="# Provadores de Teoremas\n\nIsabelle",
        preferred_topic_slug="provadores-de-teoremas",
    )

    assert period == "23/03/2026 a 25/03/2026"
    assert ambiguous is False
    assert confidence > 0
    assert any(reason == "topic=provadores-de-teoremas" for reason in reasons)
    assert any(reason == "topic-filtered" for reason in reasons)


def test_select_probable_period_for_entry_prefers_matching_session_over_stronger_block_text():
    unit = {
        "slug": "unidade-01-metodos-formais",
        "title": "Unidade 1 — Métodos Formais",
    }
    blocks = [
        {
            "id": "bloco-01",
            "period_label": "30/03/2026 a 03/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {"index": 1, "date_text": "30/03/2026", "content": "Aula"},
                {"index": 2, "date_text": "01/04/2026", "content": "Aula"},
            ],
            "sessions": [
                {
                    "id": "bloco-01-sessao-2026-03-30",
                    "date": "2026-03-30",
                    "kind": "class",
                    "label": "Especificações recursivas e provas por indução",
                    "signals": [
                        "2026-03-30",
                        "especificacoes recursivas",
                        "provas por inducao",
                    ],
                }
            ],
        },
        {
            "id": "bloco-02",
            "period_label": "06/04/2026 a 10/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {
                    "index": 3,
                    "date_text": "06/04/2026",
                    "content": "Especificações recursivas e provas por indução",
                },
                {
                    "index": 4,
                    "date_text": "08/04/2026",
                    "content": "Especificações recursivas e provas por indução",
                },
            ],
            "sessions": [
                {
                    "id": "bloco-02-sessao-2026-04-06",
                    "date": "2026-04-06",
                    "kind": "class",
                    "label": "Aula de revisão",
                    "signals": ["2026-04-06", "aula", "revisao"],
                }
            ],
        },
    ]
    entry = {
        "title": "Lista de revisão",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/lista-revisao.pdf",
    }
    markdown_text = """
Semana 30/03/2026 a 03/04/2026
(30/03/2026): Especificações recursivas e provas por indução
""".strip()

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=unit,
        candidate_rows=blocks,
        markdown_text=markdown_text,
        preferred_topic_slug="",
    )

    assert period == "30/03/2026 a 03/04/2026"
    assert ambiguous is False
    assert confidence > 0
    assert any(reason == "session-first" for reason in reasons)
    assert any(reason == "session=bloco-01-sessao-2026-03-30" for reason in reasons)


def test_select_probable_period_for_entry_reports_card_evidence_when_it_reinforces_session():
    unit = {"slug": "unidade-01-metodos-formais"}
    blocks = [
        {
            "id": "bloco-01",
            "period_label": "30/03/2026 a 03/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {"index": 1, "date_text": "30/03/2026", "content": "Aula"},
                {"index": 2, "date_text": "01/04/2026", "content": "Aula"},
            ],
            "sessions": [
                {
                    "id": "bloco-01-sessao-2026-03-30",
                    "date": "2026-03-30",
                    "kind": "class",
                    "label": "Especificações recursivas e provas por indução",
                    "signals": [
                        "2026-03-30",
                        "especificacoes recursivas",
                        "provas por inducao",
                    ],
                    "card_evidence": [
                        {
                            "title": "Especificações recursivas e provas por indução",
                            "normalized_title": "especificacoes recursivas e provas por inducao",
                            "date": "",
                            "source_kind": "topic-title",
                        }
                    ],
                }
            ],
            "card_evidence": [
                {
                    "title": "Especificações recursivas e provas por indução",
                    "normalized_title": "especificacoes recursivas e provas por inducao",
                    "date": "",
                    "source_kind": "card-title",
                }
            ],
        },
        {
            "id": "bloco-02",
            "period_label": "06/04/2026 a 10/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [{"index": 3, "date_text": "06/04/2026", "content": "Revisao geral"}],
            "sessions": [
                {
                    "id": "bloco-02-sessao-2026-04-06",
                    "date": "2026-04-06",
                    "kind": "class",
                    "label": "Revisao geral",
                    "signals": ["2026-04-06", "revisao", "geral"],
                }
            ],
            "card_evidence": [],
        },
    ]
    entry = {
        "title": "Lista de revisão - Especificações recursivas e provas por indução",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/lista-revisao.pdf",
    }
    markdown_text = """
Semana 30/03/2026 a 03/04/2026
(30/03/2026): Especificações recursivas e provas por indução
""".strip()

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=unit,
        candidate_rows=blocks,
        markdown_text=markdown_text,
        preferred_topic_slug="",
    )

    assert period == "30/03/2026 a 03/04/2026"
    assert ambiguous is False
    assert confidence > 0
    assert any(reason == "session-first" for reason in reasons)
    assert any(reason == "card-evidence" for reason in reasons)


def test_select_probable_period_for_entry_keeps_explicit_session_ahead_of_stronger_card_evidence():
    unit = {"slug": "unidade-01-metodos-formais"}
    blocks = [
        {
            "id": "bloco-01",
            "period_label": "30/03/2026 a 03/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [
                {"index": 1, "date_text": "30/03/2026", "content": "Especificações recursivas e provas por indução"},
                {"index": 2, "date_text": "01/04/2026", "content": "Especificações recursivas e provas por indução"},
            ],
            "sessions": [
                {
                    "id": "bloco-01-sessao-2026-03-30",
                    "date": "2026-03-30",
                    "kind": "class",
                    "label": "Especificações recursivas e provas por indução",
                    "signals": [
                        "2026-03-30",
                        "especificacoes recursivas",
                        "provas por inducao",
                    ],
                }
            ],
            "card_evidence": [],
        },
        {
            "id": "bloco-02",
            "period_label": "06/04/2026 a 10/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.95,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "rows": [{"index": 3, "date_text": "06/04/2026", "content": "Aula de revisão"}],
            "sessions": [
                {
                    "id": "bloco-02-sessao-2026-04-06",
                    "date": "2026-04-06",
                    "kind": "class",
                    "label": "Aula de revisão",
                    "signals": ["2026-04-06", "aula", "revisao"],
                    "card_evidence": [
                        {
                            "title": "Especificações recursivas e provas por indução",
                            "normalized_title": "especificacoes recursivas e provas por inducao",
                            "date": "",
                            "source_kind": "topic-title",
                        }
                    ],
                }
            ],
            "card_evidence": [
                {
                    "title": "Especificações recursivas e provas por indução",
                    "normalized_title": "especificacoes recursivas e provas por inducao",
                    "date": "",
                    "source_kind": "card-title",
                }
            ],
        },
    ]
    entry = {
        "title": "Lista de revisão - Especificações recursivas e provas por indução",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/lista-revisao.pdf",
    }
    markdown_text = """
Semana 30/03/2026 a 03/04/2026
(30/03/2026): Especificações recursivas e provas por indução
""".strip()

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=unit,
        candidate_rows=blocks,
        markdown_text=markdown_text,
        preferred_topic_slug="",
    )

    assert period == "30/03/2026 a 03/04/2026"
    assert ambiguous is False
    assert confidence > 0
    assert any(reason == "session-first" for reason in reasons)
    assert not any(reason == "card-evidence" for reason in reasons)


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

    assert "| Unidade | Confiança | Período |" in result
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


def test_file_map_md_respects_manual_unit_override(tmp_path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    (md_dir / "exerciciosespecificacao.md").write_text(
        "# Exercícios\n\n## Especificação Formal\n\nPré e pós condições.\n",
        encoding="utf-8",
    )

    course_meta = {"course_name": "Métodos Formais", "_repo_root": repo}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Linguagens de Especificação e Lógicas

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Pré e Pós Condições
""".strip(),
        syllabus="""
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-04 | Introdução |
| 2 | 2026-04-27 | Lógica de Hoare |
| 3 | 2026-05-06 | Pré e Pós Condições |
""".strip(),
    )
    entries = [
        {
            "title": "Exerciciosespecificacao",
            "category": "listas",
            "tags": "",
            "manual_unit_slug": "unidade-02-verificacao-de-programas",
            "base_markdown": "exercises/lists/exerciciosespecificacao.md",
            "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
        }
    ]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "unidade-02-verificacao-de-programas" in result
    assert "2026-05-06" in result
    assert "unidade-manual" in result


def test_file_map_md_respects_manual_timeline_block_override(tmp_path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    (md_dir / "exerciciosformalizacaoalgoritmosrecursao.md").write_text(
        "# Exercícios\n\n## Formalização de Algoritmos — Recursão\n\n### Exercícios\n",
        encoding="utf-8",
    )

    course_meta = {"course_name": "Métodos Formais", "_repo_root": repo}
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Especificação de Funções Recursivas
""".strip(),
        syllabus="""
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 2026-03-04 | Introdução |
| 2 | 2026-03-16 | definições indutivas e recursivas, exercícios |
| 3 | 2026-03-18 | definições indutivas e recursivas sobre listas |
| 4 | 2026-03-23 | definições indutivas e recursivas sobre árvores |
| 5 | 2026-03-25 | exercícios |
""".strip(),
    )
    entries = [
        {
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "tags": "",
            "manual_timeline_block_id": "bloco-02",
            "base_markdown": "exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md",
            "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
        }
    ]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "2026-03-04 a 2026-03-25" in result
    assert "bloco-manual" in result


def test_file_map_skips_timeline_for_reference_categories():
    course_meta = {
        "course_name": "Métodos Formais",
        "_unit_index_for_tests": [
            {"title": "Unidade 01 — Métodos Formais", "topics": ["Lógica"]},
        ],
        "_period_index_for_tests": {
            "unidade-01-metodos-formais": "2026-03-04 a 2026-05-04",
        },
    }
    entries = [
        {
            "title": "Ref X",
            "category": "references",
            "tags": "main",
            "base_markdown": "content/curated/ref-x.md",
            "raw_target": "raw/pdfs/references/ref-x.pdf",
        },
        {
            "title": "Bib Y",
            "category": "bibliografia",
            "tags": "main",
            "base_markdown": "content/curated/bib-y.md",
            "raw_target": "raw/pdfs/bibliografia/bib-y.pdf",
        },
        {
            "title": "Refs PT",
            "category": "referencias",
            "tags": "main",
            "base_markdown": "content/curated/refs-pt.md",
            "raw_target": "raw/pdfs/referencias/refs-pt.pdf",
        },
    ]

    result = file_map_md(course_meta, entries)

    # Period column must be empty for reference-like categories regardless of tags.
    assert "2026-03-04 a 2026-05-04" not in result
    for title in ("Ref X", "Bib Y", "Refs PT"):
        row = next(line for line in result.splitlines() if f"| {title} |" in line)
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        # Columns: #, Título, Categoria, Quando abrir, Prioridade, Markdown, Seções, Unidade, Confiança, Período
        unit_cell = cells[7]
        period_cell = cells[9]
        assert unit_cell in ("", "curso-inteiro")
        assert "unidade-" not in unit_cell
        assert period_cell == ""


def test_score_entry_against_timeline_block_ignores_rows_marked_ignored():
    signals = {
        "title_text": "Lista de exercicios",
        "markdown_text": "Lista de exercicios",
        "category_text": "",
        "tags_text": "listas",
        "raw_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
    }
    ignored_block = {"rows": [{"content": "Lista de exercicios", "ignored": True}]}
    active_block = {"rows": [{"content": "Lista de exercicios"}]}

    assert _score_entry_against_timeline_block(signals, ignored_block) == 0.0
    assert _score_entry_against_timeline_block(signals, active_block) > 0.0


def test_resolve_entry_manual_timeline_block_falls_back_to_nth_instructional_block():
    timeline_context = {
        "timeline_index": {
            "blocks": [
                {"id": "bloco-auto-001", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-002", "administrative_only": True, "unit_slug": "u1"},
                {"id": "bloco-auto-003", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-004", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-005", "administrative_only": False, "unit_slug": "u1"},
            ]
        }
    }
    entry = {"manual_timeline_block_id": "bloco-04", "unit_slug": "u1"}

    resolved = _resolve_entry_manual_timeline_block(entry, timeline_context)

    assert resolved is not None
    assert resolved["id"] == "bloco-auto-005"
