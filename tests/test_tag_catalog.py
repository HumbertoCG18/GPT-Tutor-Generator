from src.models.core import FileEntry
from src.models.core import StudentProfile, SubjectProfile
from tests.fixtures.tagging_cases import (
    TAGGING_COURSE_MAP,
    TAGGING_GLOSSARY,
    TAGGING_TEACHING_PLAN,
)


def test_legacy_tags_are_migrated_to_manual_tags():
    payload = {
        "source_path": "/tmp/lista1.pdf",
        "file_type": "pdf",
        "category": "listas",
        "title": "Lista 1",
        "tags": "topico:funcoes-recursivas; tipo:lista",
    }

    entry = FileEntry.from_dict(payload)

    assert entry.manual_tags == ["topico:funcoes-recursivas", "tipo:lista"]
    assert entry.auto_tags == []


def test_missing_legacy_tags_keeps_manual_tags_empty():
    payload = {
        "source_path": "/tmp/lista1.pdf",
        "file_type": "pdf",
        "category": "listas",
        "title": "Lista 1",
    }

    entry = FileEntry.from_dict(payload)

    assert entry.manual_tags == []


def test_code_entries_do_not_migrate_language_from_legacy_tags():
    payload = {
        "source_path": "/tmp/demo.thy",
        "file_type": "code",
        "category": "codigo-professor",
        "title": "Demo",
        "tags": "isabelle",
    }

    entry = FileEntry.from_dict(payload)

    assert entry.tags == "isabelle"
    assert entry.manual_tags == []


def test_build_tag_catalog_extracts_topic_and_tool_tags():
    from src.builder.engine import _build_tag_catalog

    catalog = _build_tag_catalog(
        teaching_plan=TAGGING_TEACHING_PLAN,
        course_map_md=TAGGING_COURSE_MAP,
        glossary_md=TAGGING_GLOSSARY,
        strong_headings=["Introdução ao Isabelle"],
    )

    tags = set(catalog["tags"])
    assert "topico:funcoes-recursivas" in tags
    assert "topico:conjuntos-indutivos" in tags
    assert "ferramenta:isabelle" in tags


def test_build_tag_catalog_ignores_structural_and_bibliographic_noise():
    from src.builder.engine import _build_tag_catalog

    catalog = _build_tag_catalog(
        teaching_plan="""
        Ementa
        Avaliação
        Bibliografia
        Adquirir experiência na formalização de propriedades de modelos e programas
        Almeida J.B. et al. Rigorous Software Development. Springer. 2011.
        """,
        course_map_md="""
        ## Estrutura do curso
        ### Unidade 01 — Métodos Formais
        - [ ] 1.2.3. Especificação de Funções Recursivas
        """,
        glossary_md="""
        ## Termos
        ## Formato de entrada
        """,
    )

    tags = set(catalog["tags"])
    assert "topico:funcoes-recursivas" in tags
    assert "topico:bibliografia" not in tags
    assert "topico:avaliacao" not in tags
    assert "topico:ementa" not in tags
    assert "topico:formato-de-entrada" not in tags
    assert "topico:almeida-j-b-et-al-rigorous-software-development-springer-2011" not in tags
    assert "topico:timeline-cronograma-x-unidades" not in tags


def test_build_tag_catalog_ignores_weak_heading_phrases():
    from src.builder.engine import _build_tag_catalog

    catalog = _build_tag_catalog(
        teaching_plan="",
        course_map_md="",
        glossary_md="",
        strong_headings=[
            "Seja a seguinte especificação",
            "Um primeiro algoritmo",
            "Revisão",
            "Funções Recursivas",
        ],
    )

    tags = set(catalog["tags"])
    assert "topico:funcoes-recursivas" in tags
    assert "topico:seja-a-seguinte-especificacao" not in tags
    assert "topico:um-primeiro-algoritmo" not in tags
    assert "topico:revisao" not in tags


def test_build_tag_catalog_only_uses_heading_topics_when_supported_by_course_vocab():
    from src.builder.engine import _build_tag_catalog

    catalog = _build_tag_catalog(
        teaching_plan="""
        1.2.3. Especificação de Funções Recursivas
        """,
        course_map_md="",
        glossary_md="",
        strong_headings=[
            "Funções recursivas sobre árvores",
            "Prof. Júlio Machado",
            "Ariane 5",
            "Página 1",
        ],
    )

    tags = set(catalog["tags"])
    assert "topico:funcoes-recursivas" in tags
    assert "topico:funcoes-recursivas-sobre-arvores" in tags
    assert "topico:prof-julio-machado" not in tags
    assert "topico:ariane-5" not in tags
    assert "topico:pagina-1" not in tags


def test_build_tag_catalog_intermediate_mode_blocks_loose_heading_rewrites():
    from src.builder.engine import _build_tag_catalog

    catalog = _build_tag_catalog(
        teaching_plan="""
        1.2.2. Especificação de Conjuntos Indutivos
        1.2.3. Especificação de Funções Recursivas
        1.2.4. Fundamentos de Lógica de Primeira Ordem
        """,
        course_map_md="",
        glossary_md="",
        strong_headings=[
            "Conjuntos e Funções",
            "Especificação Formal",
            "Lógica de Predicados",
            "Lógica de Primeira Ordem",
            "Funções Recursivas sobre Árvores",
        ],
    )

    tags = set(catalog["tags"])
    assert "topico:funcoes-recursivas-sobre-arvores" in tags
    assert "topico:logica-de-primeira-ordem" in tags
    assert "topico:conjuntos-e-funcoes" not in tags
    assert "topico:especificacao-formal" not in tags
    assert "topico:logica-de-predicados" not in tags


def test_infer_entry_auto_tags_uses_controlled_catalog_and_category():
    from src.builder.engine import _infer_entry_auto_tags

    vocabulary = {
        "tags": [
            "topico:funcoes-recursivas",
            "topico:conjuntos-indutivos",
            "ferramenta:isabelle",
        ]
    }
    entry = {
        "title": "Exerciciosformalizacaoalgoritmosrecursao",
        "category": "listas",
        "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
    }
    markdown_text = "# Exercícios\n\n## Funções Recursivas\n\nExercícios sobre listas."

    auto_tags = _infer_entry_auto_tags(entry, markdown_text, vocabulary)

    assert "topico:funcoes-recursivas" in auto_tags
    assert "tipo:lista" in auto_tags


def test_infer_entry_auto_tags_rejects_weak_single_token_topic_tags():
    from src.builder.engine import _infer_entry_auto_tags

    vocabulary = {
        "tags": [
            "topico:termo",
            "topico:isabelle",
        ]
    }
    entry = {
        "title": "Termos e Isabelle",
        "category": "listas",
        "raw_target": "raw/pdfs/listas/termos-e-isabelle.pdf",
    }
    markdown_text = "# Termos\n\n## Isabelle\n\nExemplo de uso de Isabelle."

    auto_tags = _infer_entry_auto_tags(entry, markdown_text, vocabulary)

    assert "topico:isabelle" in auto_tags
    assert "topico:termo" not in auto_tags
    assert "tipo:lista" in auto_tags


def test_infer_entry_auto_tags_ignore_body_only_mentions_without_strong_headings():
    from src.builder.engine import _infer_entry_auto_tags

    vocabulary = {
        "tags": [
            "topico:pre-e-pos-condicoes",
            "topico:logica-de-hoare",
        ]
    }
    entry = {
        "title": "Exerciciosformalizacaoalgoritmosrecursao",
        "category": "listas",
        "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
    }
    markdown_text = "# Exercícios\n\nTexto com pré e pós condições no corpo, sem heading forte."

    auto_tags = _infer_entry_auto_tags(entry, markdown_text, vocabulary)

    assert "topico:pre-e-pos-condicoes" not in auto_tags
    assert "topico:logica-de-hoare" not in auto_tags
    assert "tipo:lista" in auto_tags


def test_refresh_manifest_auto_tags_populates_existing_entry(tmp_path):
    from src.builder.engine import _refresh_manifest_auto_tags

    repo = tmp_path / "repo"
    md_path = repo / "content" / "curated"
    md_path.mkdir(parents=True)
    (md_path / "item.md").write_text("# Exercícios\n\n## Funções Recursivas\n", encoding="utf-8")

    entries = [
        {
            "id": "item",
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "base_markdown": "content/curated/item.md",
        }
    ]
    vocabulary = {"tags": ["topico:funcoes-recursivas"]}

    refreshed = _refresh_manifest_auto_tags(repo, entries, vocabulary)

    assert refreshed[0]["auto_tags"] == ["topico:funcoes-recursivas", "tipo:lista"]


def test_backlog_tag_summary_keeps_manual_and_auto_tags_separate():
    from src.ui.dialogs import _format_backlog_tag_summary

    summary = _format_backlog_tag_summary(
        ["topico:funcoes-recursivas"],
        ["topico:funcoes-recursivas", "tipo:lista"],
    )

    assert summary["manual"] == "topico:funcoes-recursivas"
    assert summary["auto"] == "topico:funcoes-recursivas, tipo:lista"


def test_manual_tag_selection_is_constrained_by_catalog():
    from src.ui.dialogs import _normalize_selected_manual_tags

    selected = _normalize_selected_manual_tags(
        ["topico:funcoes-recursivas", "topico:inexistente"],
        ["topico:funcoes-recursivas", "tipo:lista"],
    )

    assert selected == ["topico:funcoes-recursivas"]


def test_regenerate_pedagogical_files_writes_tag_catalog_and_auto_tags(tmp_path):
    import json

    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    builder = RepoBuilder(
        repo,
        {"course_name": "Métodos Formais", "course_slug": "metodos-formais", "semester": "2026/1", "professor": "Prof", "institution": "PUCRS"},
        [],
        {},
        student_profile=StudentProfile(),
        subject_profile=SubjectProfile(
            name="Métodos Formais",
            slug="metodos-formais",
            teaching_plan=TAGGING_TEACHING_PLAN,
        ),
    )
    builder._create_structure()
    (repo / "content" / "curated" / "item.md").write_text(
        "# Exercícios\n\n## Funções Recursivas\n",
        encoding="utf-8",
    )
    manifest = {
        "entries": [
            {
                "id": "item",
                "title": "Exerciciosformalizacaoalgoritmosrecursao",
                "category": "listas",
                "file_type": "pdf",
                "source_path": "raw/lista.pdf",
                "base_markdown": "content/curated/item.md",
                "tags": "",
            }
        ]
    }

    builder._regenerate_pedagogical_files(manifest)

    payload = json.loads((repo / "course" / ".tag_catalog.json").read_text(encoding="utf-8"))
    assert payload["version"] == 2
    assert payload["scope"]["course_slug"] == "metodos-formais"
    assert "topico:funcoes-recursivas" in payload["tags"]
    assert manifest["entries"][0]["auto_tags"] == ["topico:funcoes-recursivas", "tipo:lista"]


def test_write_tag_catalog_preserves_manual_catalog_tags(tmp_path):
    import json

    from src.builder.engine import _write_tag_catalog

    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".tag_catalog.json").write_text(
        json.dumps(
            {
                "version": 2,
                "scope": {"course_name": "Métodos Formais", "course_slug": "metodos-formais"},
                "manual_tags": ["ferramenta:isabelle"],
                "auto_tags": [],
                "tags": ["ferramenta:isabelle"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = _write_tag_catalog(
        repo,
        SubjectProfile(name="Métodos Formais", slug="metodos-formais", teaching_plan=TAGGING_TEACHING_PLAN),
        [],
        course_map_text=TAGGING_COURSE_MAP,
        glossary_text=TAGGING_GLOSSARY,
    )

    assert "ferramenta:isabelle" in payload["manual_tags"]
    assert "ferramenta:isabelle" in payload["tags"]
