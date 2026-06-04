"""Fase 0 — higiene do modelo de dados.

Garante que os 5 campos escritos-mas-ausentes no `FileEntry` sobrevivem ao
round-trip `from_dict -> to_dict` (antes eram filtrados silenciosamente por
`from_dict`, que descarta chave desconhecida). Tambem guarda os renomes de
colisao e o verify-then-remove dos campos de bloco.
"""

from __future__ import annotations

from src.models.core import FileEntry


_PERSISTED_ENTRY_FIELDS = (
    "manual_subunit_slug",
    "unit_match_confidence",
    "unit_match_reasons",
    "subunit_match_confidence",
    "subunit_match_reasons",
)


def _make_entry_dict() -> dict:
    return {
        "source_path": "staging/aula.pdf",
        "file_type": "pdf",
        "category": "material",
        "title": "Aula 1",
        "manual_subunit_slug": "subunidade-02-inducao",
        "unit_match_confidence": 0.87,
        "unit_match_reasons": ["winner_score=3.50", "date_boost"],
        "subunit_match_confidence": 0.63,
        "subunit_match_reasons": ["topic_overlap"],
    }


def test_fileentry_roundtrip_preserves_persisted_match_fields():
    payload = _make_entry_dict()

    first = FileEntry.from_dict(payload).to_dict()
    second = FileEntry.from_dict(first).to_dict()

    for name in _PERSISTED_ENTRY_FIELDS:
        assert name in second, f"campo {name!r} sumiu no round-trip"
        assert second[name] == payload[name], f"campo {name!r} divergiu: {second[name]!r}"


def test_fileentry_reason_lists_default_to_empty_list():
    entry = FileEntry(
        source_path="staging/x.pdf",
        file_type="pdf",
        category="material",
        title="X",
    )
    assert entry.unit_match_reasons == []
    assert entry.subunit_match_reasons == []
    # listas mutaveis nao podem ser compartilhadas entre instancias
    other = FileEntry(
        source_path="staging/y.pdf",
        file_type="pdf",
        category="material",
        title="Y",
    )
    entry.unit_match_reasons.append("z")
    assert other.unit_match_reasons == []


def test_block_curation_merge_uses_block_scoped_unit_key(tmp_path):
    """O override de unidade em escopo BLOCO entra na chave renomeada
    `block_manual_unit_slug`, sem colidir com `FileEntry.manual_unit_slug`."""
    from src.builder.timeline.curation import apply_block_curation, set_block_override

    set_block_override(tmp_path, "bloco-12", "manual_unit_slug", "unidade-03-indecidibilidade")
    blocks = [{"id": "bloco-12", "unit_slug": ""}]
    touched = apply_block_curation(blocks, tmp_path)

    assert touched == 1
    assert blocks[0]["block_manual_unit_slug"] == "unidade-03-indecidibilidade"
    # a chave entry-scoped NUNCA deve aparecer no bloco em memoria
    assert "manual_unit_slug" not in blocks[0]


def test_apply_curation_overrides_promotes_block_unit(tmp_path):
    """O merge de alto nivel em index.py promove o override de bloco para
    `unit_slug`/`unit_confidence` lendo a chave renomeada."""
    from src.builder.timeline.curation import set_block_override
    from src.builder.timeline.index import _apply_curation_overrides

    set_block_override(tmp_path, "bloco-12", "manual_unit_slug", "unidade-03")
    ti = {"version": 4, "blocks": [
        {"id": "bloco-12", "kind": "class", "unit_slug": "", "unit_confidence": 0.0,
         "topic_text": "halting problem", "sessions": [{"d": 1}]}
    ]}
    touched = _apply_curation_overrides(ti, tmp_path)

    assert touched == 1
    blk = ti["blocks"][0]
    assert blk["unit_slug"] == "unidade-03"
    assert blk["unit_confidence"] == 1.0
    assert blk["block_manual_unit_slug"] == "unidade-03"


# --- Verify-then-remove (Fase 0, item 4) -------------------------------------
# Os 4 campos candidatos a remocao TEM leitor vivo em src/, entao FICAM. Este
# teste documenta os leitores e protege contra remocao acidental: se alguem
# tirar o campo da serializacao, o leitor correspondente quebra silenciosamente.
#   - unit_confidence          -> file_map.score_entry_against_timeline_block (boost)
#   - primary_topic_confidence -> file_map.score_entry_against_timeline_block (boost)
#   - topic_candidates         -> file_map.timeline_block_matches_preferred_topic
#                                 + index._vote_unit_from_topic_candidates
#   - topic_ambiguous          -> mantido por consistencia do shape do bloco
#     (round-trip de serializacao); caso mais fraco, sem consumidor downstream.
_KEPT_BLOCK_FIELDS = (
    "unit_confidence",
    "primary_topic_confidence",
    "topic_candidates",
    "topic_ambiguous",
)


def test_serialize_timeline_index_keeps_fields_with_live_readers():
    from src.builder.timeline.index import _serialize_timeline_index

    timeline_index = {
        "version": 4,
        "blocks": [
            {
                "id": "bloco-01",
                "kind": "class",
                "unit_slug": "unidade-01",
                "unit_confidence": 0.95,
                "primary_topic_slug": "tema",
                "primary_topic_confidence": 0.8,
                "topic_ambiguous": False,
                "topic_candidates": [{"topic_slug": "tema", "unit_slug": "unidade-01"}],
                "topic_text": "conteudo instrucional",
                "rows": [{"content": "Aula sobre conteudo instrucional"}],
            }
        ],
    }

    serialized = _serialize_timeline_index(timeline_index)
    assert serialized["blocks"], "bloco instrucional nao deveria ser filtrado"
    payload = serialized["blocks"][0]
    for name in _KEPT_BLOCK_FIELDS:
        assert name in payload, f"campo {name!r} tem leitor vivo e nao pode sumir"


def test_block_scope_unit_key_not_entry_scoped_in_serialization():
    """O bloco serializado NUNCA expoe a chave entry-scoped `manual_unit_slug`;
    o override de unidade em escopo bloco usa `block_manual_unit_slug`."""
    from src.builder.timeline.index import _serialize_timeline_index

    timeline_index = {
        "version": 4,
        "blocks": [
            {
                "id": "bloco-01",
                "kind": "class",
                "unit_slug": "unidade-01",
                "block_manual_unit_slug": "unidade-01",
                "topic_text": "conteudo",
                "rows": [{"content": "Aula sobre conteudo"}],
            }
        ],
    }

    payload = _serialize_timeline_index(timeline_index)["blocks"][0]
    assert payload["block_manual_unit_slug"] == "unidade-01"
    assert "manual_unit_slug" not in payload
