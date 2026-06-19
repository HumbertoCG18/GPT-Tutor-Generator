"""Testes TDD para src/builder/routing/resolver_apply.py

Fixtures sintéticas: sem repo real, sem rede, sem IO.
Cobre os 4 contratos do brief:
  1. apply_concept_resolver overwrite (material vs não-material)
  2. bloco: tag mirror (só troca bloco:, resto preservado)
  3. assemble_resolver_inputs (com e sem summary.concepts)
  4. BLOCK-only: unit fields ficam intocados
"""
from __future__ import annotations

import copy
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures reutilizáveis
# ---------------------------------------------------------------------------

BLOCK_X = {
    "id": "bloco-X",
    "topic_text": "Arvores binarias e busca",
    "kind": "class",
    "unit_slug": "unit-1",
    "sessions": [],
    "topics": ["arvores", "busca binaria"],
    "aliases": [],
}

BLOCK_Y = {
    "id": "bloco-Y",
    "topic_text": "Listas encadeadas",
    "kind": "class",
    "unit_slug": "unit-2",
    "sessions": [],
    "topics": ["listas", "encadeadas"],
    "aliases": [],
}

BLOCKS = [BLOCK_X, BLOCK_Y]

UNITS = [
    {"slug": "unit-1", "title": "Arvores", "topics": []},
    {"slug": "unit-2", "title": "Listas", "topics": []},
]

# Entry material: PDF com computed_block_id do funil = bloco-X
MATERIAL_ENTRY = {
    "id": "mat-1",
    "title": "Lista encadeada introducao",
    "file_type": "pdf",
    "category": "",
    "computed_block_id": "bloco-X",
    "computed_block_band": "baixa",
    "computed_block_confidence": 0.3,
    "computed_block_method": "scorer_only",
    "computed_unit_slug": "unit-1",  # funil deixou unit-1 — NÃO deve mudar
    "auto_tags": ["unit:unit-1", "bloco:bloco-X", "ferramenta:dafny"],
    "manual_tags": [],
    "source_path": "mat-1.pdf",
}

# Entry não-material: código sem category e sem file_type pdf
NON_MATERIAL_ENTRY = {
    "id": "nm-1",
    "title": "Utils auxiliares",
    "file_type": "code",
    "category": "",
    "computed_block_id": "bloco-X",
    "auto_tags": ["bloco:bloco-X"],
    "manual_tags": [],
}

# code_curation com summary que aponta bloco-Y
CODE_CURATION_WITH_SUMMARY = {
    "entries": {
        "mat-1": {
            "summary": {
                "primary_block_id": "bloco-Y",
                "secondary_block_id": "bloco-X",
                "block_match_confidence": 0.85,
                "block_match_method": "consensus",
                "match_rationale": "Listas e estruturas encadeadas",
                "concepts": ["listas", "encadeadas", "ponteiros"],
            }
        }
    }
}

# code_curation sem summary para mat-1
CODE_CURATION_NO_SUMMARY = {
    "entries": {}
}


def _fake_assignment_bloco_y(entry_for_resolver, blocks, units, *, signals, llm_curation=None, lessons_index=None):
    """Stub do resolver: sempre retorna bloco-Y independente do input."""
    from src.builder.routing.concept_resolver import Assignment
    return Assignment(
        block_id="bloco-Y",
        unit_slug="unit-2",
        subunit_slug="",
        confidence=0.85,
        band="alta",
        method="consensus",
        signals={},
        conflict=None,
    )


def _fake_markdown(root, entry):
    """Stub de _entry_markdown_text_for_file_map: retorna string vazia."""
    return ""


def _fake_signals(entry, markdown):
    """Stub de collect_entry_unit_signals: retorna dict mínimo."""
    return {
        "title_text": str(entry.get("title", "") or ""),
        "markdown_text": "",
        "tool_tags_text": "",
        "source_section_text": "",
    }


# ---------------------------------------------------------------------------
# Teste 1 — apply_concept_resolver overwrite (material vira bloco-Y; não-material intacta)
# ---------------------------------------------------------------------------

def test_apply_concept_resolver_overwrites_material_block():
    """apply_concept_resolver substitui computed_block_id da entry material pelo
    bloco escolhido pelo resolver (bloco-Y), atualiza band/method/confidence, e
    não toca a entry não-material."""
    from src.builder.routing import resolver_apply

    entries = [copy.deepcopy(MATERIAL_ENTRY), copy.deepcopy(NON_MATERIAL_ENTRY)]
    root = None  # stub não usa root real

    with (
        patch.object(resolver_apply, "_entry_markdown_text_for_file_map", _fake_markdown),
        patch.object(resolver_apply, "collect_entry_unit_signals", _fake_signals),
        patch.object(resolver_apply, "resolve_material_assignment", _fake_assignment_bloco_y),
    ):
        result = resolver_apply.apply_concept_resolver(
            entries, BLOCKS, UNITS, CODE_CURATION_WITH_SUMMARY, root
        )

    mat = next(e for e in result if e["id"] == "mat-1")
    nm = next(e for e in result if e["id"] == "nm-1")

    # --- Material: campos de bloco sobrescritos ---
    assert mat["computed_block_id"] == "bloco-Y", f"esperado bloco-Y, got {mat['computed_block_id']}"
    assert mat["computed_block_band"] == "alta"
    assert mat["computed_block_method"] == "consensus"
    assert abs(mat["computed_block_confidence"] - 0.85) < 1e-9

    # --- Não-material: intacta ---
    assert nm["computed_block_id"] == "bloco-X", "não-material não deve ser modificada"

    # --- Unit untouched (BLOCK-only) ---
    assert mat["computed_unit_slug"] == "unit-1", "unit NÃO deve ser sobrescrita (BLOCK-only)"


# ---------------------------------------------------------------------------
# Teste 2 — bloco: tag mirror
# ---------------------------------------------------------------------------

def test_bloco_tag_mirror_only_replaces_bloco_prefix():
    """Após apply, a tag bloco:bloco-X vira bloco:bloco-Y, e as outras tags
    (unit:, ferramenta:) são preservadas sem duplicação."""
    from src.builder.routing import resolver_apply

    entry = copy.deepcopy(MATERIAL_ENTRY)
    # Garante estado inicial explícito
    entry["auto_tags"] = ["unit:unit-1", "bloco:bloco-X", "ferramenta:dafny"]

    entries = [entry]
    root = None

    with (
        patch.object(resolver_apply, "_entry_markdown_text_for_file_map", _fake_markdown),
        patch.object(resolver_apply, "collect_entry_unit_signals", _fake_signals),
        patch.object(resolver_apply, "resolve_material_assignment", _fake_assignment_bloco_y),
    ):
        result = resolver_apply.apply_concept_resolver(
            entries, BLOCKS, UNITS, CODE_CURATION_WITH_SUMMARY, root
        )

    mat = result[0]
    tags = mat["auto_tags"]

    assert "bloco:bloco-Y" in tags, f"esperado bloco:bloco-Y em {tags}"
    assert "bloco:bloco-X" not in tags, f"tag antiga bloco:bloco-X deve ser removida de {tags}"
    assert "unit:unit-1" in tags, f"tag unit: deve ser preservada, got {tags}"
    assert "ferramenta:dafny" in tags, f"tag ferramenta: deve ser preservada, got {tags}"
    # sem duplicatas
    assert tags.count("bloco:bloco-Y") == 1


# ---------------------------------------------------------------------------
# Teste 3 — assemble_resolver_inputs
# ---------------------------------------------------------------------------

def test_assemble_resolver_inputs_with_summary_injects_concepts():
    """Quando summary tem concepts, entry_for_resolver deve ter entry['concepts']
    com os valores do summary."""
    from src.builder.routing import resolver_apply

    entry = copy.deepcopy(MATERIAL_ENTRY)
    root = None

    with (
        patch.object(resolver_apply, "_entry_markdown_text_for_file_map", _fake_markdown),
        patch.object(resolver_apply, "collect_entry_unit_signals", _fake_signals),
    ):
        entry_for_resolver, signals, summary = resolver_apply.assemble_resolver_inputs(
            root, entry, CODE_CURATION_WITH_SUMMARY
        )

    assert entry_for_resolver.get("concepts") == ["listas", "encadeadas", "ponteiros"]
    assert summary.get("primary_block_id") == "bloco-Y"
    assert isinstance(signals, dict)


def test_assemble_resolver_inputs_no_summary_no_concepts_no_crash():
    """Quando não há summary, entry_for_resolver não deve ter 'concepts'
    injetados e llm_curation-equivalent (summary) é dict vazio. Sem crash."""
    from src.builder.routing import resolver_apply

    entry = copy.deepcopy(MATERIAL_ENTRY)
    # Remove concepts prévios se existirem
    entry.pop("concepts", None)
    root = None

    with (
        patch.object(resolver_apply, "_entry_markdown_text_for_file_map", _fake_markdown),
        patch.object(resolver_apply, "collect_entry_unit_signals", _fake_signals),
    ):
        entry_for_resolver, signals, summary = resolver_apply.assemble_resolver_inputs(
            root, entry, CODE_CURATION_NO_SUMMARY
        )

    # Sem concepts do summary: entry_for_resolver não deve ter concepts (ou igual ao original)
    assert "concepts" not in entry_for_resolver or entry_for_resolver["concepts"] == entry.get("concepts")
    # summary deve ser dict vazio
    assert summary == {}
    # não crashou


# ---------------------------------------------------------------------------
# Teste 4 — BLOCK-only: unit slug e unit: tags ficam intocados
# ---------------------------------------------------------------------------

def test_unit_fields_untouched_after_apply():
    """BLOCK-only: computed_unit_slug e tags unit:/subunit: não são alterados."""
    from src.builder.routing import resolver_apply

    entry = copy.deepcopy(MATERIAL_ENTRY)
    entry["computed_unit_slug"] = "unit-1"
    entry["auto_tags"] = ["unit:unit-1", "subunit:sub-a", "bloco:bloco-X"]

    entries = [entry]
    root = None

    with (
        patch.object(resolver_apply, "_entry_markdown_text_for_file_map", _fake_markdown),
        patch.object(resolver_apply, "collect_entry_unit_signals", _fake_signals),
        patch.object(resolver_apply, "resolve_material_assignment", _fake_assignment_bloco_y),
    ):
        result = resolver_apply.apply_concept_resolver(
            entries, BLOCKS, UNITS, CODE_CURATION_WITH_SUMMARY, root
        )

    mat = result[0]
    # Unit fields intocados
    assert mat["computed_unit_slug"] == "unit-1"
    tags = mat["auto_tags"]
    assert "unit:unit-1" in tags
    assert "subunit:sub-a" in tags
    # Bloco foi atualizado
    assert "bloco:bloco-Y" in tags
    assert "bloco:bloco-X" not in tags


# ---------------------------------------------------------------------------
# Teste 5 — captação alavanca 0: load do .lessons_index.json (infra; o consumo
# pelo resolver foi revertido — termo regredia o gold, aguarda alavanca 1)
# ---------------------------------------------------------------------------

def test_load_lessons_index_present_and_absent(tmp_path):
    from src.builder.routing import resolver_apply
    assert resolver_apply.load_lessons_index(tmp_path) is None     # sem arquivo -> None
    course = tmp_path / "course"
    course.mkdir()
    (course / ".lessons_index.json").write_text(
        '{"version": 1, "by_date": {"2026-05-09": "invariantes"}}', encoding="utf-8")
    idx = resolver_apply.load_lessons_index(tmp_path)
    assert idx["by_date"]["2026-05-09"] == "invariantes"
