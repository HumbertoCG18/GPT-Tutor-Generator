"""Limpeza de categorias fora da timeline — PORTADA pro motor no cutover
passo 3 (era de resolve_unit_block_tags, content_taxonomy; hoje vive em
resolver_apply.apply_concept_resolver). Cobre também o contrato novo do
cutover: motor SEMEIA entries sem computed_block_id (gate antigo removido).
"""
from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES
from src.builder.routing import resolver_apply


def _no_timeline_entry():
    return {
        "id": "afp-lib",
        "title": "Archive of Formal Proofs",
        "category": "references",
        "file_type": "url",
        "tags": "",
        "manual_tags": [],
        "auto_tags": ["bloco:bloco-06", "outro-tag"],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        # campos orfaos do bug B1
        "computed_block_id": "bloco-06",
        "computed_block_confidence": 1.0,
        "computed_block_band": "instrucional",
        "computed_block_method": "manual",
    }


def test_references_en_esta_no_filtro():
    assert "references" in _NO_TIMELINE_CATEGORIES
    assert {"cronograma", "bibliografia", "referencias"} <= _NO_TIMELINE_CATEGORIES


def test_no_timeline_limpa_campos_orfaos_no_motor():
    """Entry categoria 'references' com campos computed_block_* e auto_tag
    bloco: sai de apply_concept_resolver sem esses campos e sem a tag bloco:
    (residuo do bug B1 nao persiste ao reprocessar o manifest)."""
    result = resolver_apply.apply_concept_resolver(
        [_no_timeline_entry()], blocks=[], units=[], code_curation={}, root=None,
    )[0]

    for k in ("computed_block_id", "computed_block_confidence",
              "computed_block_band", "computed_block_method"):
        assert k not in result, f"{k} deve ser removido"

    tags = result.get("auto_tags", [])
    assert [t for t in tags if str(t).startswith("bloco:")] == []
    assert "outro-tag" in tags, "Tags nao-bloco devem ser preservadas"
    # manual_timeline_block_id NAO deve ser tocado (decisao do usuario)
    assert "manual_timeline_block_id" in result


def test_no_timeline_nunca_entra_no_resolver(monkeypatch):
    """Categoria fora da timeline nao passa pelo resolver (limpa e pula)."""
    def _boom(*args, **kwargs):
        raise AssertionError("resolver nao deve rodar p/ categoria no-timeline")

    monkeypatch.setattr(resolver_apply, "resolve_material_assignment", _boom)
    resolver_apply.apply_concept_resolver(
        [_no_timeline_entry()], blocks=[], units=[], code_curation={}, root=None,
    )


def test_motor_semeia_entry_sem_computed(monkeypatch):
    """Cutover passo 3: entry material SEM computed_block_id E' processado
    (o gate antigo 'so re-resolve quem ja tinha bloco' morreu com o funil —
    o motor e' o atribuidor unico e semeia imports novos)."""
    calls = []

    def _fake_assignment(entry, blocks, units, **kwargs):
        calls.append(entry.get("id"))
        return {"block_id": "bloco-01", "confidence": 0.9,
                "band": "alta", "method": "concept-fused"}

    monkeypatch.setattr(resolver_apply, "resolve_material_assignment", _fake_assignment)
    blocks = [{"id": "bloco-01", "block_uuid": "u-1", "kind": "class",
               "sessions": [], "topic_candidates": []}]
    entry = {"id": "novo", "title": "novo material", "category": "listas",
             "file_type": "pdf", "auto_tags": []}

    result = resolver_apply.apply_concept_resolver(
        [entry], blocks=blocks, units=[], code_curation={}, root=None,
    )[0]

    assert calls == ["novo"], "motor deve semear entry sem computed_block_id"
    assert result["computed_block_id"] == "u-1"  # uuid canonico via resolve_block_ref
    assert "bloco:bloco-01" in result["auto_tags"]
