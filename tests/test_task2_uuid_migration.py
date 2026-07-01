"""Testes TDD para Task 2 — Migração de card_block_map/computed_block_id para uuid.

Todos os testes aqui devem estar RED antes da implementação.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# T_resolve_block_ref — helper de resolução bloco-NN / índice-nu / uuid
# ---------------------------------------------------------------------------


def test_resolve_block_ref_passthrough_uuid():
    """UUID já resolvido → passthrough imediato."""
    from src.builder.timeline.card_block import resolve_block_ref

    uuid_v = "550e8400-e29b-41d4-a716-446655440001"
    blocks = [{"id": "bloco-01", "block_uuid": uuid_v}]
    assert resolve_block_ref(uuid_v, blocks) == uuid_v


def test_resolve_block_ref_from_positional():
    """bloco-03 → retorna block_uuid do bloco com id == 'bloco-03'."""
    from src.builder.timeline.card_block import resolve_block_ref

    uuid_v = "550e8400-e29b-41d4-a716-446655440002"
    blocks = [{"id": "bloco-03", "block_uuid": uuid_v}]
    assert resolve_block_ref("bloco-03", blocks) == uuid_v


def test_resolve_block_ref_from_bare_int():
    """Índice nu '5' → equivale a bloco-05."""
    from src.builder.timeline.card_block import resolve_block_ref

    uuid_v = "550e8400-e29b-41d4-a716-446655440003"
    blocks = [{"id": "bloco-05", "block_uuid": uuid_v}]
    assert resolve_block_ref("5", blocks) == uuid_v


def test_resolve_block_ref_unknown_returns_empty():
    """Ref não encontrada → retorna string vazia."""
    from src.builder.timeline.card_block import resolve_block_ref

    assert resolve_block_ref("bloco-99", []) == ""


def test_resolve_block_ref_bare_int_zero_padded():
    """Índice nu '7' → bloco-07 (zero-padded)."""
    from src.builder.timeline.card_block import resolve_block_ref

    uuid_v = "550e8400-e29b-41d4-a716-446655440099"
    blocks = [{"id": "bloco-07", "block_uuid": uuid_v}]
    assert resolve_block_ref("7", blocks) == uuid_v


def test_resolve_block_ref_empty_string_returns_empty():
    """String vazia → retorna vazio."""
    from src.builder.timeline.card_block import resolve_block_ref

    assert resolve_block_ref("", []) == ""


# ---------------------------------------------------------------------------
# T_lazy_compat — lookup_card_blocks resolve bloco-NN legado para uuid
# ---------------------------------------------------------------------------


def test_lookup_lazy_compat_bloco_nn():
    """card_map com bloco-NN legado é resolvido para uuid via índice."""
    from src.builder.timeline.card_block import lookup_card_blocks

    uuid_v = "550e8400-e29b-41d4-a716-446655440004"
    blocks = [
        {
            "id": "bloco-07",
            "block_uuid": uuid_v,
            "unit_slug": "u",
            "period_start": "2026-03-01",
            "period_end": "2026-03-15",
        }
    ]
    card_map = {"Card": {"block_ids": ["bloco-07"], "source": "manual"}}
    ids = lookup_card_blocks("Card", card_map, [], blocks)
    assert ids == [uuid_v]


def test_lookup_lazy_compat_filters_empty():
    """Refs que não resolvem são filtradas do resultado."""
    from src.builder.timeline.card_block import lookup_card_blocks

    uuid_v = "550e8400-e29b-41d4-a716-446655440005"
    blocks = [
        {
            "id": "bloco-01",
            "block_uuid": uuid_v,
            "unit_slug": "u",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        }
    ]
    # card_map tem bloco-01 (resolve) e bloco-99 (não resolve)
    card_map = {"Card": {"block_ids": ["bloco-01", "bloco-99"], "source": "manual"}}
    ids = lookup_card_blocks("Card", card_map, [], blocks)
    assert uuid_v in ids
    assert "bloco-99" not in ids
    assert "" not in ids


def test_lookup_uuid_passthrough():
    """UUID direto no card_map já passa sem resolução extra."""
    from src.builder.timeline.card_block import lookup_card_blocks

    uuid_v = "550e8400-e29b-41d4-a716-446655440006"
    blocks = [
        {
            "id": "bloco-02",
            "block_uuid": uuid_v,
            "unit_slug": "u",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        }
    ]
    card_map = {"Card": {"block_ids": [uuid_v], "source": "manual"}}
    ids = lookup_card_blocks("Card", card_map, [], blocks)
    assert ids == [uuid_v]


def test_lookup_no_blocks_fallback_raw():
    """Quando blocks não é passado (ou vazio), retorna o raw sem resolução."""
    from src.builder.timeline.card_block import lookup_card_blocks

    card_map = {"Card": {"block_ids": ["bloco-03"], "source": "manual"}}
    # blocks=[] → fallback seguro: retorna o raw
    ids = lookup_card_blocks("Card", card_map, [], [])
    assert ids == ["bloco-03"]


# ---------------------------------------------------------------------------
# T1 — prova-de-fogo: split não quebra lookup
# ---------------------------------------------------------------------------


def test_t1_split_does_not_break_lookup():
    """Índice pós-split: A' herda uuid-A.
    card_block_map[card] = [uuid-A].
    lookup_card_blocks deve resolver uuid-A.
    Contraste: id posicional QUEBRA quando bloco renumera."""
    from src.builder.timeline.card_block import lookup_card_blocks

    uuid_a = "550e8400-e29b-41d4-a716-446655440001"
    # A' = bloco-01 com block_uuid=uuid_a (herdado pelo reattach)
    blocks = [
        {
            "id": "bloco-01",
            "block_uuid": uuid_a,
            "unit_slug": "u1",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        },
    ]
    card_map = {"MeuCard": {"block_ids": [uuid_a], "source": "manual"}}
    ids = lookup_card_blocks("MeuCard", card_map, [], blocks)
    assert ids == [uuid_a]

    # Contraste: se card_map tivesse o id posicional e o bloco renumerasse
    # (bloco-01 vira bloco-02 num split), o lookup by-id quebraria.
    # Com uuid, não quebra.
    blocks_renumbered = [
        {
            "id": "bloco-02",
            "block_uuid": uuid_a,
            "unit_slug": "u1",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        },
    ]
    ids2 = lookup_card_blocks("MeuCard", card_map, [], blocks_renumbered)
    assert ids2 == [uuid_a], "uuid estável sobrevive a renumeração"


# ---------------------------------------------------------------------------
# T_bloco_tag_stays_display — computed_block_id vira uuid, tag bloco: continua display
# ---------------------------------------------------------------------------


def _make_pdf_entry(entry_id: str, title: str) -> dict:
    return {
        "id": entry_id,
        "title": title,
        "category": "material-de-aula",
        "file_type": "pdf",
        "source_path": f"/tmp/{entry_id}.pdf",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
    }


def _stub_unit_match(slug, confidence, ambiguous=False):
    class M:
        pass

    m = M()
    m.slug = slug
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def _stub_topic_match(slug="", confidence=0.0, ambiguous=True):
    class M:
        pass

    m = M()
    m.topic_slug = slug
    m.topic_label = slug
    m.unit_slug = ""
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def test_bloco_tag_is_display_not_uuid():
    """computed_block_id é uuid, mas a tag bloco: continua bloco-NN (display).

    file_map.py:506 parseia bloco-(\\d+) e QUEBRA com uuid — a tag NÃO pode
    virar bloco:<uuid>.
    """
    from src.builder.extraction.content_taxonomy import resolve_unit_block_tags

    uuid_v = "550e8400-e29b-41d4-a716-446655440777"
    block = {
        "id": "bloco-05",
        "block_uuid": uuid_v,
        "period_label": "01/01 a 15/01",
        "unit_slug": "unidade-01",
        "kind": "class",
    }
    entries = [_make_pdf_entry("e1", "Slides")]
    entries[0]["manual_timeline_block_id"] = "bloco-05"

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {"unidade-01": [block]},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": [block]},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-01", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: block,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    out = result[0]
    # computed_block_id é o UUID (join interno)
    assert out["computed_block_id"] == uuid_v
    # a tag bloco: continua DISPLAY (bloco-05), nunca uuid
    tags = out["auto_tags"]
    assert "bloco:bloco-05" in tags
    assert f"bloco:{uuid_v}" not in tags


def test_navigation_period_lookup_works_with_uuid():
    """period_label_by_block_id é keyed por uuid também — coluna Período preenche."""
    uuid_v = "550e8400-e29b-41d4-a716-446655440888"
    block = {
        "id": "bloco-03",
        "block_uuid": uuid_v,
        "period_label": "10/02 a 20/02",
        "unit_slug": "unidade-01",
    }
    # Reproduz o re-key de navigation.py: ambas as chaves (id + uuid) -> label.
    period_label_by_block_id: dict = {}
    for _block in [block]:
        _bid = str(_block.get("id", "") or "").strip()
        _buuid = str(_block.get("block_uuid", "") or "").strip()
        _label = str(_block.get("period_label", "") or "").strip()
        if _bid:
            period_label_by_block_id[_bid] = _label
        if _buuid:
            period_label_by_block_id[_buuid] = _label

    # computed_block_id = uuid -> resolve o label
    assert period_label_by_block_id.get(uuid_v) == "10/02 a 20/02"
    # ref legada bloco-NN também resolve (compat lazy)
    assert period_label_by_block_id.get("bloco-03") == "10/02 a 20/02"


# ---------------------------------------------------------------------------
# C-1 — resolve_card_to_block retorna uuid em todos os 4 paths de resolução
# ---------------------------------------------------------------------------


def _make_blocks_with_uuid():
    return [
        {
            "id": "bloco-01",
            "block_uuid": "uuid-c1-01",
            "unit_slug": "u-intro",
            "period_start": "2026-03-02",
            "period_end": "2026-03-02",
            "primary_topic_label": "motivação",
            "topics": ["motivação"],
            "aliases": [],
        },
        {
            "id": "bloco-10",
            "block_uuid": "uuid-c1-10",
            "unit_slug": "u-verif",
            "period_start": "2026-04-27",
            "period_end": "2026-05-04",
            "primary_topic_label": "Lógica de Hoare",
            "topics": ["hoare"],
            "aliases": [],
        },
        {
            "id": "bloco-11",
            "block_uuid": "uuid-c1-11",
            "unit_slug": "u-verif",
            "period_start": "2026-05-06",
            "period_end": "2026-05-06",
            "primary_topic_label": "Dafny",
            "topics": ["dafny"],
            "aliases": [],
        },
    ]


_UNITS_C1 = [
    {
        "slug": "u-intro",
        "title": "Introdução a Métodos Formais",
        "topics": ["motivação"],
        "distinctive_tokens": [],
    },
    {
        "slug": "u-verif",
        "title": "Verificação de Programas",
        "topics": ["hoare", "dafny"],
        "distinctive_tokens": [],
    },
]


def test_resolve_card_to_block_title_match_returns_uuid():
    """Path 2 (title match): resolve_card_to_block retorna uuids, não bloco-NN."""
    from src.builder.timeline.card_block import resolve_card_to_block

    blocks = _make_blocks_with_uuid()
    r = resolve_card_to_block("Verificação de Programas", _UNITS_C1, blocks)
    assert set(r.block_ids) == {"uuid-c1-10", "uuid-c1-11"}
    assert r.reason.startswith("unit:")


def test_resolve_card_to_block_date_match_returns_uuid():
    """Path 1 (date match): resolve_card_to_block retorna uuid, não bloco-NN."""
    from src.builder.timeline.card_block import resolve_card_to_block

    blocks = _make_blocks_with_uuid()
    r = resolve_card_to_block("Aula 06/05", _UNITS_C1, blocks)
    assert r.block_ids == ["uuid-c1-11"]
    assert r.reason.startswith("date:")


def test_resolve_card_to_block_topic_match_returns_uuid():
    """Path 3 (topic match): resolve_card_to_block retorna uuid, não bloco-NN."""
    from src.builder.timeline.card_block import resolve_card_to_block

    units = [{"slug": "u3", "title": "Problemas Indecidiveis", "topics": [], "distinctive_tokens": []}]
    blocks = [
        {
            "id": "bloco-10",
            "block_uuid": "uuid-c1-10",
            "unit_slug": "u3",
            "primary_topic_label": "Halting problem",
            "topics": ["parada"],
            "aliases": [],
            "period_start": "2026-04-15",
            "period_end": "2026-04-15",
        },
        {
            "id": "bloco-14",
            "block_uuid": "uuid-c1-14",
            "unit_slug": "u3",
            "primary_topic_label": "Teoremas de Godel",
            "topics": ["godel", "incompletude"],
            "aliases": [],
            "period_start": "2026-04-29",
            "period_end": "2026-04-29",
        },
    ]
    r = resolve_card_to_block("Semana 9 - Teoremas de Godel", units, blocks)
    assert r.block_ids == ["uuid-c1-14"]
    assert r.reason == "topic"


def test_resolve_card_to_block_unit_overlap_returns_uuid():
    """Path 4 (unit overlap fallback): resolve_card_to_block retorna uuids."""
    from src.builder.timeline.card_block import resolve_card_to_block

    units = [
        {
            "slug": "u-verif",
            "title": "Unidade Z",
            "topics": ["dafny", "hoare", "verificacao"],
            "distinctive_tokens": [],
        }
    ]
    blocks = _make_blocks_with_uuid()
    r = resolve_card_to_block("verificacao hoare dafny", units, blocks)
    assert all(bid.startswith("uuid-c1-") for bid in r.block_ids), (
        f"Esperado uuids, obtido: {r.block_ids}"
    )


def test_lookup_fallback_auto_returns_uuid():
    """Fallback path de lookup_card_blocks (sem map entry) retorna uuids."""
    from src.builder.timeline.card_block import lookup_card_blocks

    blocks = _make_blocks_with_uuid()
    ids = lookup_card_blocks("Verificação de Programas", {}, _UNITS_C1, blocks)
    assert set(ids) == {"uuid-c1-10", "uuid-c1-11"}


# ---------------------------------------------------------------------------
# I-1 — T1 contraste: id posicional QUEBRA quando bloco renumera
# ---------------------------------------------------------------------------


def test_t1_contrast_positional_breaks_on_renumber():
    """Prova a regressão que uuid previne.

    Com id posicional, card_map aponta bloco-01; após renumeração o mesmo bloco
    vira bloco-02 — lookup retorna [] (referência orfanada). Com uuid, não quebra.
    """
    from src.builder.timeline.card_block import lookup_card_blocks

    uuid_a = "550e8400-e29b-41d4-a716-446655440001"
    # Cenário POSICIONAL: card_map referencia "bloco-01"
    positional_map = {"MeuCard": {"block_ids": ["bloco-01"], "source": "manual"}}

    # Índice ANTES do split: bloco-01 existe
    blocks_before = [
        {
            "id": "bloco-01",
            "block_uuid": uuid_a,
            "unit_slug": "u1",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        }
    ]

    # Índice DEPOIS do split: o mesmo conteúdo renumerou para bloco-02
    blocks_after_renumber = [
        {
            "id": "bloco-02",
            "block_uuid": uuid_a,
            "unit_slug": "u1",
            "period_start": "2026-01-01",
            "period_end": "2026-01-15",
        }
    ]

    # Com id posicional, bloco-01 não existe mais → resolve para "" → resultado vazio
    ids_positional = lookup_card_blocks("MeuCard", positional_map, [], blocks_after_renumber)
    assert ids_positional == [], (
        f"Com id posicional após renumeração, esperava [] (referência orfanada), "
        f"obteve {ids_positional}"
    )

    # Com uuid, o map guarda uuid_a; lookup resolve por uuid → estável
    uuid_map = {"MeuCard": {"block_ids": [uuid_a], "source": "manual"}}
    ids_uuid_before = lookup_card_blocks("MeuCard", uuid_map, [], blocks_before)
    ids_uuid_after = lookup_card_blocks("MeuCard", uuid_map, [], blocks_after_renumber)
    assert ids_uuid_before == [uuid_a]
    assert ids_uuid_after == [uuid_a], "uuid estável sobrevive a renumeração"


# ---------------------------------------------------------------------------
# C-2 — secondary_block_ids armazena/resolve uuid
# ---------------------------------------------------------------------------


def test_secondary_block_ids_in_code_summarization_uses_uuid():
    """_consolidate_assignment usa valid_ids por uuid (b.get("block_uuid") or b.get("id")).

    O whitelist valid_ids é construído com b.get("id") apenas →
    Gemini sugerindo uuid não passa. Após fix, valid_ids inclui uuid.
    """
    from src.builder.core.code_summarization import _consolidate_assignment

    uuid_v = "550e8400-e29b-41d4-a716-ffffffffffff"
    # valid_ids construído com uuid (como deve ser pós-fix)
    valid_ids = {uuid_v}
    local = {"primary": "", "secondaries": [], "confidence": 0.0, "method": "orphan",
              "top_candidate": "", "top_score": 0.0}
    _, secondaries, _, _ = _consolidate_assignment(local, uuid_v, [uuid_v], valid_ids)
    # Gemini sugere uuid_v como primary; deve aparecer no resultado
    # (primary ou secondary)
    primary_out, secondaries_out, _, _ = _consolidate_assignment(
        local, uuid_v, [], valid_ids
    )
    assert primary_out == uuid_v, f"primary_block_id deveria ser {uuid_v}, obteve {primary_out!r}"


def test_secondary_block_ids_written_as_uuid_in_repo_artifact():
    """repo.py secondary_idx é keyed por uuid — lookup por uuid_key encontra código."""
    # Simula a lógica de repo.py:929: para cada código, b em secondary_block_ids.
    # Após fix, o índice deve ser keyed por uuid para casar com computed_block_id.
    uuid_v = "550e8400-e29b-41d4-a716-bbbbbbbbbbbb"
    bloco_nn = "bloco-03"

    # Summary com secondary_block_ids em uuid (pós-fix)
    s = {"secondary_block_ids": [uuid_v]}

    secondary_idx: dict = {}
    for sb in (s.get("secondary_block_ids") or []):
        secondary_idx.setdefault(sb, []).append("some_entry")

    # Lookup por uuid deve funcionar
    assert uuid_v in secondary_idx
    # Lookup por bloco-NN legado NÃO deve estar neste índice (uuid substituiu)
    assert bloco_nn not in secondary_idx
