import json
from datetime import datetime

from src.builder.engine import (
    UnitMatchResult,
    TopicMatchResult,
    _build_content_taxonomy,
    _build_timeline_index,
    _auto_map_entry_subtopic,
    _auto_map_entry_unit,
    _file_map_markdown_cell,
    _build_file_map_timeline_context_from_course,
    _build_file_map_unit_index_from_course,
    _build_file_map_unit_index,
    _collect_entry_unit_signals,
    _entry_markdown_text_for_file_map,
    _format_file_map_unit_cell,
    _score_entry_against_unit,
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
    # Topo ainda é a unidade de recursão...
    assert result.slug == "unidade-01-metodos-formais"
    # ...mas o sinal (só título concatenado, sem markdown) é fraco: com
    # relative_margin_confidence (idea 1) a confiança não satura mais via o termo
    # winner*k — fica honestamente baixa/ambígua, abaixo do gate de tag. A unidade
    # passa a ser herdada do BLOCO na reconciliação, em vez de cravada por ruído.
    assert result.ambiguous
    assert result.confidence < 0.65


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

    assert isinstance(result, TopicMatchResult)
    assert result.topic_slug in {"logica-de-hoare", "pre-e-pos-condicoes"}
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

    assert result.topic_slug == "especificacao-de-funcoes-recursivas"


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

    assert result.topic_slug == "linguagens-de-especificacao-e-logicas"


def _tie_taxonomy():
    """Dois tópicos DISTINTOS que casam o mesmo texto com o mesmo peso, slugs
    neutros (que não casam o texto) e MESMO kind → empate exato por construção.

    Labels distintos de propósito: desde o IDF intra-unidade (2026-08-19), label
    REPETIDO entre irmãos não discrimina e é descartado dos dois — o empate
    viraria "sem-sinal". `hoare` é comum aos dois e some; `alfa` e `beta`
    são exclusivos e sustentam a frase (termos neutros de propósito: `logica`
    está em UNIT_GENERIC_TOKENS e zeraria um dos lados)."""
    return {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "topico-a",
                        "label": "Alfa de Hoare",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                    {
                        "slug": "topico-b",
                        "label": "Beta de Hoare",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                ],
            },
        ],
    }


def test_auto_map_entry_subtopic_exact_tie_returns_no_slug():
    # Reproduz as 12 entries codigo-professor conf-0.0 do repo real: empate
    # exato entre tópicos → o sort estável elegia um vencedor ARBITRÁRIO
    # (menor índice na taxonomia) e o surfaçava com conf 0.0.
    entry = {
        "title": "Alfa de Hoare Beta de Hoare",
        "category": "codigo-professor",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/zip/hoare.zip",
    }
    result = _auto_map_entry_subtopic(entry, _tie_taxonomy(), "unidade-02-verificacao-de-programas")

    assert result.topic_slug == ""
    assert result.confidence == 0.0
    assert result.ambiguous is True
    assert any("empate-exato" in r for r in result.reasons)


def test_auto_map_entry_subtopic_zero_score_returns_no_slug():
    # Sem sinal nenhum (zip sem markdown, título não casa nada): winner_score
    # 0 não deve surfaçar o primeiro tópico da taxonomia como slug.
    entry = {
        "title": "xyzqwabc",
        "category": "codigo-professor",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/zip/xyzqwabc.zip",
    }
    result = _auto_map_entry_subtopic(entry, _tie_taxonomy(), "")

    assert result.topic_slug == ""
    assert result.confidence == 0.0
    assert result.ambiguous is True
    assert any("sem-sinal" in r for r in result.reasons)


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
            # Unidade espelha o manifest (fonte única): a coluna vem do
            # computed_unit_slug persistido pelo funil, sem recomputar matcher.
            "computed_unit_slug": "unidade-02-verificacao-de-programas",
            "base_markdown": "exercises/lists/exerciciosespecificacao.md",
            "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
        }
    ]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "unidade-02-verificacao-de-programas" in result
    # Período espelha o manifest: sem computed_block_id/manual o FILE_MAP não
    # recomputa mais o período via scorer — coluna fica em branco.
    assert "2026-03-16" not in result
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
    # Cutover passo 3: fixture ganhou uma 2ª unidade (fallback keyword de
    # unidade morreu; matcher posicional exige >=2 unidades no plano).
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Sistemas Formais
- Linguagens de Especificação e Lógicas
- Especificação de Conjuntos Indutivos
- Especificação de Funções Recursivas

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Invariantes de Laço
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
| 7 | 2026-04-27 | Unidade 2: Lógica de Hoare |
| 8 | 2026-05-06 | invariantes de laço |
""".strip()
    )
    entries = [
        {
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "tags": "",
            # Unidade espelha o manifest (fonte única) — sem recomputação.
            "computed_unit_slug": "unidade-01-metodos-formais",
            "base_markdown": "exercises/lists/exerciciosformalizacaoalgoritmosrecursao.md",
            "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
        }
    ]

    # Período espelha o manifest: o FILE_MAP não recomputa mais via scorer.
    # Com computed_block_id apontando para um bloco real do timeline, a coluna
    # mostra o period_label desse bloco (fonte única).
    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    target_block = context["blocks_by_unit"]["unidade-01-metodos-formais"][0]
    entries[0]["computed_block_id"] = target_block["id"]

    result = file_map_md(course_meta, entries, subject_profile)

    assert "unidade-01-metodos-formais" in result
    assert target_block["period_label"] in result
    assert "Exerciciosformalizacaoalgoritmosrecursao" in result




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
    # Cutover passo 3: fixture ganhou uma 2ª unidade — o fallback keyword que
    # cobria plano de 1 unidade morreu; com <2 unidades o matcher posicional
    # (m<2) recusa e nenhum bloco recebe unidade (comportamento honesto novo).
    subject_profile = SubjectProfile(
        teaching_plan="""
### Unidade 1 — Métodos Formais
- Especificação de Conjuntos Indutivos
- Especificação de Funções Recursivas

### Unidade 2 — Verificação de Programas
- Lógica de Hoare
- Invariantes de Laço
""".strip(),
        syllabus="""
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
|---|---|---|---|---|---|---|
| 4 | QUA | 11/03/2026 | LM 19:15 - 20:45 | Conjuntos indutivos e equações recursivas | Aula |  |
| 5 | SEG | 16/03/2026 | LM 19:15 - 20:45 | Exercícios | Aula |  |
| 6 | QUA | 18/03/2026 | LM 19:15 - 20:45 | Estudo de caso: listas | Aula |  |
| 7 | SEG | 23/03/2026 | LM 19:15 - 20:45 | Estudo de caso: árvores | Aula |  |
| 8 | QUA | 25/03/2026 | LM 19:15 - 20:45 | Exercícios | Aula |  |
| 9 | SEG | 27/04/2026 | LM 19:15 - 20:45 | Lógica de Hoare | Aula |  |
| 10 | QUA | 06/05/2026 | LM 19:15 - 20:45 | Invariantes de Laço | Aula |  |
""".strip(),
    )

    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    blocks = context["blocks_by_unit"]["unidade-01-metodos-formais"]

    assert context["timeline_index"]["version"] == 4
    assert blocks[0]["period_label"] == "5 dias · 11/03/2026 a 25/03/2026"


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
    # Cutover passo 3: serializador unico (persist_enriched, v4).
    from src.builder.core.core_utils import persist_enriched_timeline_index
    serialized = persist_enriched_timeline_index(timeline_index)

    assert timeline_index["version"] == 4
    assert serialized["version"] == 4
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

    # Positional matcher: todos os blocos-aula sao da unica unidade ancorada
    # (verificacao de programas), incluindo "Verificacao de modelos/logica
    # temporal" em 15/06 que o scorer-keyword antigo descartava por threshold.
    assert context["unit_periods"]["unidade-02-verificacao-de-programas"] == "5 blocos · 27/04/2026 a 15/06/2026"










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

    assert "| Unidade | Subtópico | Confiança | Período |" in result
    assert "Aula 1" in result


def test_file_map_md_leaves_unit_blank_without_computed_slug():
    """Fonte única: sem computed_unit_slug/manual no manifest, a coluna Unidade
    fica em branco — o FILE_MAP nunca recomputa via matcher. O sufixo
    "_(ambíguo)_" morreu junto: computed_unit_slug nunca é gravado ambíguo
    (gate em resolve_unit_block_tags)."""
    course_meta = {
        "course_name": "Métodos Formais",
        "_content_taxonomy_for_tests": {"units": []},
        "_period_index_for_tests": {
            "unidade-01-metodos-formais": "2026-03-04 a 2026-05-04",
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

    assert "_(ambíguo)_" not in result
    assert "2026-03-04 a 2026-05-04" not in result
    row = next(line for line in result.splitlines() if "| Revisao |" in line)
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    # Columns: #, Título, Categoria, Quando abrir, Prioridade, Markdown, Seções, Unidade, Subtópico, Confiança, Período
    assert cells[7] == ""


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
    # Período espelha o manifest: manual_unit_slug não dispara mais recomputação
    # de período via scorer — sem computed_block_id/bloco manual a coluna fica vazia.
    assert "2026-05-06" not in result
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
            # bloco-01 é o único bloco instrucional deste syllabus. Antes o teste
            # usava "bloco-02" (dangling) e a data vinha da RECOMPUTAÇÃO do scorer;
            # agora o período vem do próprio bloco manual resolvido (fonte única).
            "manual_timeline_block_id": "bloco-01",
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
        # Columns: #, Título, Categoria, Quando abrir, Prioridade, Markdown, Seções, Unidade, Subtópico, Confiança, Período
        unit_cell = cells[7]
        period_cell = cells[10]
        assert unit_cell in ("", "curso-inteiro")
        assert "unidade-" not in unit_cell
        assert period_cell == ""




def test_resolve_entry_manual_timeline_block_falls_back_to_nth_instructional_block():
    timeline_context = {
        "timeline_index": {
            "blocks": [
                {"id": "bloco-auto-001", "unit_slug": "u1", "rows": [{"content": "Aula 1"}]},
                {"id": "bloco-auto-002", "unit_slug": "u1", "rows": [{"content": "Feriado"}]},
                {"id": "bloco-auto-003", "unit_slug": "u1", "rows": [{"content": "Aula 3"}]},
                {"id": "bloco-auto-004", "unit_slug": "u1", "rows": [{"content": "Aula 4"}]},
                {"id": "bloco-auto-005", "unit_slug": "u1", "rows": [{"content": "Aula 5"}]},
            ]
        }
    }
    entry = {"manual_timeline_block_id": "bloco-04", "unit_slug": "u1"}

    resolved = _resolve_entry_manual_timeline_block(entry, timeline_context)

    assert resolved is not None
    assert resolved["id"] == "bloco-auto-005"


def test_file_map_md_period_mirrors_computed_block_id_from_manifest():
    """FILE_MAP espelha o manifest (fonte única): a coluna Período vem do
    computed_block_id do entry, sem recomputar via scorer. Cobre lookup tanto
    em blocks_by_unit quanto em unassigned_blocks."""
    course_meta = {
        "course_name": "Métodos Formais",
        "_unit_index_for_tests": [
            {"title": "Unidade 01 — Métodos Formais", "topics": ["Sistemas Formais"]},
        ],
        "_timeline_context_for_tests": {
            "timeline_index": {"blocks": []},
            "blocks_by_unit": {
                "unidade-01-metodos-formais": [
                    {
                        "id": "bloco-03",
                        "period_label": "16/03/2026 a 25/03/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "rows": [],
                    }
                ]
            },
            "unassigned_blocks": [
                {"id": "bloco-10", "period_label": "08/06/2026 a 10/06/2026", "rows": []}
            ],
        },
    }
    entries = [
        {
            "title": "Aula Sistemas",
            "category": "material-de-aula",
            "tags": "",
            "computed_block_id": "bloco-03",
            "base_markdown": "content/aula-sistemas.md",
            "raw_target": "raw/aula-sistemas.pdf",
            "_markdown_text_for_tests": "Sistemas formais.",
        },
        {
            "title": "Aula Final",
            "category": "material-de-aula",
            "tags": "",
            "computed_block_id": "bloco-10",
            "base_markdown": "content/aula-final.md",
            "raw_target": "raw/aula-final.pdf",
            "_markdown_text_for_tests": "Sistemas formais.",
        },
    ]

    result = file_map_md(course_meta, entries)

    row_sistemas = next(line for line in result.splitlines() if "| Aula Sistemas |" in line)
    row_final = next(line for line in result.splitlines() if "| Aula Final |" in line)
    assert "16/03/2026 a 25/03/2026" in row_sistemas
    assert "08/06/2026 a 10/06/2026" in row_final


def test_file_map_md_period_empty_without_computed_block_id():
    """Sem computed_block_id (e sem bloco manual) o Período fica em branco —
    nada de recomputação via select_probable_period_for_entry."""
    course_meta = {
        "course_name": "Métodos Formais",
        "_unit_index_for_tests": [
            {"title": "Unidade 01 — Métodos Formais", "topics": ["Sistemas Formais"]},
        ],
        "_timeline_context_for_tests": {
            "timeline_index": {"blocks": []},
            "blocks_by_unit": {
                "unidade-01-metodos-formais": [
                    {
                        "id": "bloco-03",
                        "period_label": "16/03/2026 a 25/03/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "rows": [
                            {"index": 1, "date_text": "16/03/2026", "content": "Sistemas formais"},
                        ],
                    }
                ]
            },
            "unassigned_blocks": [],
        },
    }
    entries = [
        {
            "title": "Aula Sistemas",
            "category": "material-de-aula",
            "tags": "",
            "base_markdown": "content/aula-sistemas.md",
            "raw_target": "raw/aula-sistemas.pdf",
            "_markdown_text_for_tests": "Sistemas formais.",
        }
    ]

    result = file_map_md(course_meta, entries)

    row = next(line for line in result.splitlines() if "| Aula Sistemas |" in line)
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    # Columns: #, Título, Categoria, Quando abrir, Prioridade, Markdown, Seções, Unidade, Subtópico, Confiança, Período
    assert cells[10] == ""
    assert "16/03/2026 a 25/03/2026" not in result


def test_file_map_md_period_prefers_manual_block_over_computed():
    """manual_timeline_block_id (override do tutor) vence o computed_block_id."""
    course_meta = {
        "course_name": "Métodos Formais",
        "_unit_index_for_tests": [
            {"title": "Unidade 01 — Métodos Formais", "topics": ["Sistemas Formais"]},
        ],
        "_timeline_context_for_tests": {
            "timeline_index": {
                "blocks": [
                    {
                        "id": "bloco-03",
                        "period_label": "16/03/2026 a 25/03/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "administrative_only": False,
                        "rows": [],
                    },
                    {
                        "id": "bloco-10",
                        "period_label": "08/06/2026 a 10/06/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "administrative_only": False,
                        "rows": [],
                    },
                ]
            },
            "blocks_by_unit": {
                "unidade-01-metodos-formais": [
                    {
                        "id": "bloco-03",
                        "period_label": "16/03/2026 a 25/03/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "rows": [],
                    },
                    {
                        "id": "bloco-10",
                        "period_label": "08/06/2026 a 10/06/2026",
                        "unit_slug": "unidade-01-metodos-formais",
                        "rows": [],
                    },
                ]
            },
            "unassigned_blocks": [],
        },
    }
    entries = [
        {
            "title": "Aula Sistemas",
            "category": "material-de-aula",
            "tags": "",
            "computed_block_id": "bloco-03",
            "manual_timeline_block_id": "bloco-10",
            "base_markdown": "content/aula-sistemas.md",
            "raw_target": "raw/aula-sistemas.pdf",
            "_markdown_text_for_tests": "Sistemas formais.",
        }
    ]

    result = file_map_md(course_meta, entries)

    row = next(line for line in result.splitlines() if "| Aula Sistemas |" in line)
    assert "08/06/2026 a 10/06/2026" in row
    assert "16/03/2026 a 25/03/2026" not in row


def test_build_content_taxonomy_filters_noise_topics_without_code():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 01 — Introdução ao estudo de sistemas operacionais
- [ ] **1.1** Evolução histórica
- [ ] **1.2** Chamadas de sistema
- [ ] Aulas expositivas nas quais se buscará a participação dos alunos em um processo de discussão.
- [ ] Uso de projetor multimídia.
- [ ] Uso de laboratório para elaboração de trabalhos práticos.
- [ ] Nesta unidade deve-se abordar a evolução histórica dos sistemas operacionais.
""".strip(),
        course_map_md="",
        glossary_md="",
    )

    unit = taxonomy["units"][0]
    slugs = [t["slug"] for t in unit["topics"]]
    codes = {t["slug"]: t["code"] for t in unit["topics"]}

    # Tópicos com código devem estar presentes. O slug NAO carrega o codigo
    # (forma de producao: `maquinas-de-turing` + code "2.1"); o `11-...` antigo
    # era artefato do checkbox `[ ]` vazando para o texto do topico.
    assert "evolucao-historica" in slugs
    assert "chamadas-de-sistema" in slugs
    assert codes["evolucao-historica"] == "1.1"

    # Noise topics sem código devem ter sido filtrados
    noise_slugs = [
        "uso-de-projetor-multimidia",
        "uso-de-laboratorio-para-elaboracao-de-trabalhos-praticos",
    ]
    for noise in noise_slugs:
        assert noise not in slugs, f"Noise topic '{noise}' should have been filtered"

    # Descrição longa (7+ palavras) sem código deve ser filtrada
    long_noise = [s for s in slugs if len(s) > 60]
    assert not long_noise, f"Long noise slug found: {long_noise}"


def test_build_content_taxonomy_includes_topic_42_comunicacao():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 03 — Programação concorrente
- [ ] **4.1** Programas multithreads
- [ ] **4.2** Comunicação e sincronização de processos
- [ ] **4.3** Primitivas de sincronização
""".strip(),
        course_map_md="",
        glossary_md="",
    )

    unit = taxonomy["units"][0]
    slugs = [t["slug"] for t in unit["topics"]]
    # slug sem codigo (forma de producao); o codigo vive em `code`.
    assert "programas-multithreads" in slugs
    assert "comunicacao-e-sincronizacao-de-processos" in slugs
    assert "primitivas-de-sincronizacao" in slugs
    assert {t["code"] for t in unit["topics"]} == {"4.1", "4.2", "4.3"}


def test_file_map_md_includes_subtopic_column_in_header():
    profile = SubjectProfile(
        name="Sistemas Operacionais",
        teaching_plan="""
### Unidade 02 — Gerência do Processador
- [ ] **3.2** Escalonamento
- [ ] **3.3** Algoritmos de escalonamento
""".strip(),
    )
    entries = [
        {
            "id": "2604-escalonamento",
            "title": "26.04 Algoritimos de Escalonamento",
            "category": "material-de-aula",
            "auto_tags": ["topico:32-escalonamento"],
        }
    ]
    course_meta = {
        "course_name": "Sistemas Operacionais",
        "_timeline_context_for_tests": {},
    }
    result = file_map_md(course_meta, entries, subject_profile=profile)

    assert "Subtópico" in result, "FILE_MAP header should contain 'Subtópico' column"


def test_file_map_md_shows_subtopic_label_for_matched_entry():
    profile = SubjectProfile(
        name="Sistemas Operacionais",
        teaching_plan="""
### Unidade 02 — Gerência do Processador
- [ ] **3.2** Escalonamento
""".strip(),
    )
    entries = [
        {
            "id": "2604-escalonamento",
            "title": "Algoritimos de Escalonamento",
            "category": "material-de-aula",
            # Subtópico espelha o manifest (fonte única): a coluna vem do
            # computed_subunit_slug persistido, sem recomputar o matcher.
            "computed_subunit_slug": "32-escalonamento",
            "auto_tags": ["topico:32-escalonamento"],
        }
    ]
    course_meta = {
        "course_name": "Sistemas Operacionais",
        "_timeline_context_for_tests": {},
    }
    result = file_map_md(course_meta, entries, subject_profile=profile)

    assert "3.2" in result and "Escalonamento" in result


def test_file_map_md_drops_low_confidence_suffix_keeps_confidence_column():
    # Fonte única: a coluna Unidade espelha o computed_unit_slug do manifest e
    # a Confiança lê o unit_match_confidence persistido (via _infer_unit_confidence).
    # Confiança baixa aparece só na coluna ("Baixa"), nunca como sufixo na célula.
    course_meta = {
        "course_name": "Semântica Formal",
        "_content_taxonomy_for_tests": {"units": []},
        "_period_index_for_tests": {},
    }
    entries = [
        {
            "title": "Revisao",
            "category": "material-de-aula",
            "tags": "",
            "computed_unit_slug": "unidade-01-programacao-denotacional",
            "unit_match_confidence": 0.40,
            "base_markdown": "content/curated/revisao.md",
            "raw_target": "raw/pdfs/material-de-aula/revisao.pdf",
            "_markdown_text_for_tests": "denotacional proposicional",
        }
    ]

    result = file_map_md(course_meta, entries)

    assert "_(baixa confiança)_" not in result  # redundant suffix removed
    assert "Baixa" in result  # Confiança column still flags low confidence
    # sanity: the mirrored slug itself is still present
    assert "unidade-01-programacao-denotacional" in result


# Card do Moodle como sinal de unidade: TENTADO e REVERTIDO em 2026-08-18 — a
# versao por frase e inerte (os `topic_phrases` do indice de unidade vem do dict
# serializado do topico, ver `_topic_text`) e por via indireta regride o MF: 6
# entries do card `Verificacao de Programas` saem de
# `unidade-02-verificacao-de-programas`. Patch guardado no relatorio da medicao.
# Reabrir SO depois de corrigir `_topic_text` e com a regua entry->unidade de pe.


# --- topico como DICT no indice de unidade (bug achado em 2026-08-18) ---
# `build_content_taxonomy` devolve cada topico como dict
# {code, slug, label, aliases, kind, unit_slug}; `_topic_text` tratava tupla e
# str, entao caia no `str(topic)` e o topic_phrase virava o dict serializado.

_TOPICO_DICT = {
    "code": "1.2",
    "slug": "visoes-arquiteturais-estrutural-e-dinamica",
    "label": "Visões arquiteturais: estrutural e dinâmica",
    "aliases": ["1.2 Visões arquiteturais: estrutural e dinâmica"],
    "kind": "topic",
    "unit_slug": "unidade-01-arquitetura-de-software",
}


def test_topic_text_extrai_label_de_topico_dict():
    from src.builder.extraction.teaching_plan import _topic_text as tt

    assert tt(_TOPICO_DICT) == "Visões arquiteturais: estrutural e dinâmica"
    assert tt(("2.1 Lógica de Hoare", 0)) == "2.1 Lógica de Hoare"
    assert tt("texto solto") == "texto solto"


def test_build_file_map_unit_index_nao_serializa_dict_do_topico():
    index = _build_file_map_unit_index([
        {"title": "Unidade 01 — Arquitetura de Software", "topics": [_TOPICO_DICT]},
    ])

    frases = index[0]["topic_phrases"]
    assert frases == ["visoes arquiteturais estrutural e dinamica"]
    # lixo estrutural do dict fora dos tokens
    for sujeira in ("code", "slug", "label", "aliases", "kind"):
        assert sujeira not in index[0]["topic_tokens"]


def test_score_entry_against_unit_casa_frase_de_topico_dict():
    """Com o dict serializado, `topic_phrase in headings_text` nunca casava e os
    pesos altos de frase (3.0/2.8/2.7) ficavam inertes no eixo de unidade."""
    unit = _build_file_map_unit_index([
        {"title": "Unidade 01 — Arquitetura de Software", "topics": [_TOPICO_DICT]},
    ])[0]
    signals = _collect_entry_unit_signals(
        {"title": "aula", "category": "material-de-aula"},
        "# Visões arquiteturais: estrutural e dinâmica\n\nconteudo.")

    assert _score_entry_against_unit(signals, unit) >= 3.0


def test_unit_index_descarta_frase_que_e_titulo_de_outra_unidade():
    """Glossario e aliases injetavam na u01 do MF duas frases `verificacao de
    programas` — o titulo da u02. Qualquer sinal com o nome de OUTRA unidade
    rouba material dela (medido 2026-08-18: card `Verificacao de Programas`
    levava 6 entries da u02 para a u01)."""
    index = _build_file_map_unit_index([
        {"title": "Unidade 01 — Métodos Formais",
         "topics": ["Sistemas Formais"],
         "extra_signals": ["Verificação de Programas", "Provadores de Teoremas"]},
        {"title": "Unidade 02 — Verificação de Programas",
         "topics": ["Lógica de Hoare"]},
    ])

    u01 = next(u for u in index if u["slug"].startswith("unidade-01"))
    u02 = next(u for u in index if u["slug"].startswith("unidade-02"))
    assert "verificacao de programas" not in u01["topic_phrases"]
    assert "sistemas formais" in u01["topic_phrases"]
    assert "provadores de teoremas" in u01["topic_phrases"]
    assert "logica de hoare" in u02["topic_phrases"]


def _plano_duas_unidades():
    return (
        "Unidade 01 - Introducao\n"
        "1.1 Evolucao historica\n"
        "1.2 Chamadas de sistema\n"
        "Unidade 02 - Gerencia do processador\n"
        "2.1 Escalonamento\n"
        "2.2 Algoritmos de escalonamento\n"
    )


def _glossario_com_template(definicao_boilerplate: str) -> str:
    """GLOSSARY.md como o build gera: duas secoes de TEMPLATE sem `Aparece em`,
    e termos reais cuja definicao e a mesma frase-modelo para todas as unidades."""
    return (
        "# GLOSSARY - Curso\n"
        "\n"
        "## Formato de entrada\n"
        "```\n"
        "## [Termo]\n"
        "```\n"
        "\n"
        "## Termos\n"
        "> Termos extraidos automaticamente do plano de ensino.\n"
        "\n"
        "## 1.1 Evolucao historica\n"
        f"**Definicao:** {definicao_boilerplate}\n"
        "**Sinonimos aceitos:** \u2014\n"
        "**Aparece em:** Unidade 01 - Introducao\n"
        "\n"
        "## 2.1 Escalonamento\n"
        f"**Definicao:** {definicao_boilerplate}\n"
        "**Sinonimos aceitos:** \u2014\n"
        "**Aparece em:** Unidade 02 - Gerencia do processador\n"
    )


def _indice(monkeypatch, glossario: str):
    import src.builder.routing.file_map as fm

    monkeypatch.setattr(
        "src.builder.facade.file_map.glossary_md",
        lambda *a, **k: glossario,
        raising=False,
    )
    profile = SubjectProfile(name="Curso", teaching_plan=_plano_duas_unidades())
    return _build_file_map_unit_index_from_course({"name": "Curso"}, profile)


def test_secao_de_template_do_glossario_nao_vira_sinal_de_unidade(monkeypatch):
    """`## Formato de entrada` e `## Termos` sao secoes do TEMPLATE, nao termos.

    Nao tem `Aparece em`, entao o unit_hint fica vazio e o guard antigo
    (`if unit_hint and ...`) as colava em TODA unidade — medido nos 5 cursos
    de producao em 2026-08-18.
    """
    index = _indice(monkeypatch, _glossario_com_template("Definicao real e especifica."))

    for unit in index:
        frases = " | ".join(unit["topic_phrases"])
        assert "formato de entrada" not in frases
        assert frases.count("termos") == 0


def test_sinal_presente_em_todas_as_unidades_e_descartado(monkeypatch):
    """Token em TODAS as unidades tem poder discriminante ZERO.

    A definicao auto-gerada e a MESMA frase-modelo para todo termo, entao
    `conceito`/`central`/`reconhecido`/... viravam frase de todas as unidades.
    """
    boiler = (
        "Conceito central de esta unidade que deve ser reconhecido e usado "
        "corretamente nas respostas e revisoes."
    )
    index = _indice(monkeypatch, _glossario_com_template(boiler))

    ubiquas = set.intersection(*(set(u["topic_phrases"]) for u in index))
    assert not ubiquas, f"frases presentes em todas as unidades: {sorted(ubiquas)}"


def test_travessao_de_formatacao_nao_vira_alias():
    """`**Sinonimos aceitos:** \u2014` e placeholder de VAZIO, nao um sinonimo."""
    from src.builder.extraction.content_taxonomy import _parse_glossary_terms

    termos = _parse_glossary_terms(
        "## Escalonamento\n"
        "**Definicao:** Ordem de execucao.\n"
        "**Sinonimos aceitos:** \u2014\n"
        "**Aparece em:** Unidade 02\n"
        "\n"
        "## Deadlock\n"
        "**Sinonimos aceitos:** impasse; \u2013\n"
        "**Aparece em:** Unidade 04\n"
    )

    por_termo = {t["term"]: t["synonyms"] for t in termos}
    assert por_termo["Escalonamento"] == []
    assert por_termo["Deadlock"] == ["impasse"]


def test_topico_sem_vocabulario_proprio_nao_ganha_bonus_fantasma():
    """Topico cujos tokens sao TODOS genericos nao pode pontuar sem casar nada.

    `topic_tokens` vazio caia em `len(overlap) >= len(topic_tokens)` -> `0 >= 0`
    e somava +1.4 INCONDICIONAL. Vivo em producao (2026-08-19): 3 topicos do MF,
    entre eles "Linguagens de Especificacao e Logicas".
    """
    from src.builder.engine import _score_entry_against_taxonomy_topic
    from src.builder.timeline.index import UNIT_GENERIC_TOKENS

    label = "Linguagens de Especificacao e Logicas"
    assert all(
        tok in UNIT_GENERIC_TOKENS
        for tok in label.lower().split()
        if len(tok) >= 4
    ), "fixture depende de todos os tokens serem genericos"

    topico = {"topic_label": label, "topic_slug": "linguagens-de-especificacao-e-logicas",
              "aliases": [], "kind": "topic"}
    signals = {"title_text": "conteudo totalmente sem relacao xyzqwabc",
               "markdown_headings_text": "", "markdown_lead_text": "", "markdown_text": "",
               "category_text": "", "manual_tags_text": "", "auto_tags_text": "",
               "legacy_tags_text": "", "raw_text": ""}

    assert _score_entry_against_taxonomy_topic(signals, topico) == 0.0


def _revisao_taxonomy():
    return {
        "version": 1,
        "course_slug": "metodos-formais",
        "units": [
            {
                "slug": "unidade-02-verificacao-de-programas",
                "title": "Unidade 2 - Verificacao de Programas",
                "topics": [
                    {
                        "slug": "topico-a",
                        "label": "Alfa de Hoare",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                    {
                        "slug": "topico-b",
                        "label": "Gama de Dijkstra",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-verificacao-de-programas",
                    },
                ],
            },
        ],
    }


def test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio():
    # Item (a) 2026-08-31: aula de "revisao" cujo vocabulario nao acerta NENHUMA
    # subunit com forca revisa conteudo de FORA da taxonomia (pre-requisito,
    # prova) — slug vazio e a resposta honesta. Caso real: TCC aula-06 (revisao
    # de automatos da cadeira anterior, winner_score=3.24, gold VAZIO).
    entry = {
        "title": "Revisão Alfabeto, Cadeia, Linguagem e Propriedades",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/revisao.pdf",
    }
    markdown = (
        "# Alfabeto e cadeias\n\nConteudo extenso sobre automatos da cadeira "
        "anterior.\n\nNo fim, uma mencao tardia a alfa de hoare.\n"
    )
    result = _auto_map_entry_subtopic(entry, _revisao_taxonomy(), markdown)

    assert result.topic_slug == ""
    assert result.confidence == 0.0
    assert result.ambiguous is True
    assert any("revisao-sem-assunto-dominante" in r for r in result.reasons)


def test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug():
    # Armadilha (ii) do handoff 31/08: revisao LEGITIMAMENTE mono-assunto
    # (TCC aula-01 ws=8.97, ES2 revisaoarquiteturapadroes ws=15.81) pontua
    # acima do piso e NAO pode ser esvaziada.
    entry = {
        "title": "Revisão Alfa de Hoare",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/revisao-alfa.pdf",
    }
    markdown = "# Alfa de Hoare\n\nRevisao aprofundada de alfa de hoare.\n"
    result = _auto_map_entry_subtopic(entry, _revisao_taxonomy(), markdown)

    assert result.topic_slug == "topico-a"


def test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug():
    # O piso e ESCOPADO a materiais de revisao: score fraco em material comum
    # continua best-effort (certos legitimos medidos com ws 1.04-4.32).
    entry = {
        "title": "Exemplo de Uso no Unix",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/exemplo-unix.pdf",
    }
    markdown = (
        "# Exemplo pratico\n\nCodigo extenso do exemplo no unix.\n\n"
        "No fim, uma mencao tardia a alfa de hoare.\n"
    )
    result = _auto_map_entry_subtopic(entry, _revisao_taxonomy(), markdown)

    assert result.topic_slug == "topico-a"


def test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide():
    """Short-vocab (2026-09-01, fenomeno do holdout FR): o plano de redes so
    usa SIGLAS e os tokenizadores cortavam len<4 — "Modelos OSI e TCP/IP"
    reduzia a 'modelos' e o material de OSI/TCP-IP caia no label irmao de
    tokens longos (02-modelos conf 0.92 ERRADO). Token curto consagrado por
    LABEL do curso passa a contar."""
    taxonomy = {
        "version": 1,
        "course_slug": "fundamentos-de-redes",
        "units": [
            {
                "slug": "unidade-01-introducao",
                "title": "Unidade 01 - Introducao a redes",
                "topics": [
                    {
                        "slug": "conceitos-de-redes-de-computadores-e-internet",
                        "label": "Conceitos de redes de computadores e Internet",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-introducao",
                    },
                    {
                        "slug": "modelos-osi-e-tcpip",
                        "label": "Modelos OSI e TCP/IP",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-introducao",
                    },
                ],
            },
        ],
    }
    entry = {
        "title": "02 - Modelos de Referencia",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/02-modelos-de-referencia.pdf",
    }
    markdown = (
        "# Modelos de Referencia\n\n## Modelo OSI\n\nAs redes de computadores da "
        "internet usam camadas.\n\n## TCP/IP\n\nOSI versus TCP/IP nas redes de "
        "computadores. O modelo OSI define camadas; TCP/IP define a arquitetura "
        "da internet para computadores em rede.\n"
    )
    result = _auto_map_entry_subtopic(entry, taxonomy, markdown)
    assert result.topic_slug == "modelos-osi-e-tcpip"


def test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total():
    """Artefato de slugify (2026-09-01, holdout FR): "TCP/IP" vira "tcpip" no
    slug — um token que NUNCA existe no texto normalizado ("tcp ip"). Ele
    entrava em topic_tokens e o bonus de cobertura-total nunca disparava
    (02-modelos: 4/5 cobertos, o 5o era o proprio artefato), enquanto o
    label-aspirador ("Conceitos de ... e Internet") cobria 2/2 migalhas e
    ganhava. Token que o slug INVENTA fundindo tokens adjacentes do label
    nao conta como topic_token."""
    # 3 unidades para o df por curso nao engolir o vocabulario (com 1 unidade
    # tudo vira generico e o cenario deixa de ser o do FR real, onde
    # conceitos/internet/modelos sao distintivos da u01: df 1/6).
    taxonomy = {
        "version": 1,
        "course_slug": "fundamentos-de-redes",
        "course_name": "Fundamentos de Redes de Computadores",
        "units": [
            {
                "slug": "unidade-01-introducao",
                "title": "Unidade 01 - Introducao a redes",
                "topics": [
                    {
                        "slug": "conceitos-de-redes-de-computadores-e-internet",
                        "label": "Conceitos de redes de computadores e Internet",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-introducao",
                    },
                    {
                        "slug": "modelos-osi-e-tcpip",
                        "label": "Modelos OSI e TCP/IP",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-01-introducao",
                    },
                ],
            },
            {
                "slug": "unidade-02-aplicacao",
                "title": "Unidade 02 - Nivel de aplicacao",
                "topics": [
                    {
                        "slug": "protocolo-http",
                        "label": "Protocolo HTTP",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-02-aplicacao",
                    },
                ],
            },
            {
                "slug": "unidade-03-transporte",
                "title": "Unidade 03 - Nivel de transporte",
                "topics": [
                    {
                        "slug": "controle-de-congestionamento",
                        "label": "Controle de congestionamento",
                        "aliases": [],
                        "kind": "topic",
                        "unit_slug": "unidade-03-transporte",
                    },
                ],
            },
        ],
    }
    entry = {
        "title": "02 - Modelos de Referencia",
        "category": "material-de-aula",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "raw_target": "raw/pdfs/material-de-aula/02-modelos-de-referencia.pdf",
    }
    # Configuracao REAL do erro: lead com as migalhas do aspirador (conceitos +
    # internet, 2/2 cobertos) e o assunto de verdade espalhado em headings que
    # nao casam nenhuma frase de label — so tokens (modelos, osi, tcp, ip),
    # 4/5 porque "tcpip" e artefato.
    markdown = (
        "Conceitos gerais sobre a internet e as camadas.\n\n"
        "## Modelo OSI\n\nCamada fisica e de enlace.\n\n"
        "## Camadas do TCP e do IP\n\nOSI versus modelos da arquitetura.\n"
    )
    result = _auto_map_entry_subtopic(entry, taxonomy, markdown)
    assert result.topic_slug == "modelos-osi-e-tcpip"
