from __future__ import annotations

from src.builder.routing.file_map import resolve_effective_block


def _blocks(*ids):
    return [{"id": bid, "administrative_only": False} for bid in ids]


def test_manual_wins_over_computed_divergent():
    """Manual aponta X, computed aponta Y -> efetivo = X (manual vence)."""
    entry = {
        "manual_timeline_block_id": "bloco-X",
        "computed_block_id": "bloco-Y",
        "auto_tags": ["bloco:bloco-Y"],
    }
    eff = resolve_effective_block(entry, _blocks("bloco-X", "bloco-Y"))
    assert eff.block_id == "bloco-X"
    assert eff.source == "manual"


def test_auto_when_no_manual():
    entry = {"computed_block_id": "bloco-Y", "auto_tags": ["bloco:bloco-Y"]}
    eff = resolve_effective_block(entry, _blocks("bloco-Y"))
    assert eff.block_id == "bloco-Y"
    assert eff.source == "auto"


def test_auto_from_tag_mirror_when_no_computed_field():
    """Sem campo computed_block_id, lê o espelho auto_tags["bloco:"]."""
    entry = {"auto_tags": ["unit:u1", "bloco:bloco-Z"]}
    eff = resolve_effective_block(entry, _blocks("bloco-Z"))
    assert eff.block_id == "bloco-Z"
    assert eff.source == "auto"


def test_manual_nonexistent_falls_back_to_computed():
    """Manual aponta id inexistente -> cai em computed (logado), spec 195-197."""
    entry = {
        "manual_timeline_block_id": "bloco-naoexiste",
        "computed_block_id": "bloco-Y",
        "auto_tags": ["bloco:bloco-Y"],
    }
    eff = resolve_effective_block(entry, _blocks("bloco-Y"))
    assert eff.block_id == "bloco-Y"
    assert eff.source == "auto"


def test_manual_ordinal_fallback_resolves():
    """Manual "bloco-2" ordinal resolve para o 2o bloco instrucional."""
    entry = {"manual_timeline_block_id": "bloco-2", "computed_block_id": "blk-a"}
    blocks = [
        {"id": "blk-a", "administrative_only": False},
        {"id": "blk-b", "administrative_only": False},
    ]
    eff = resolve_effective_block(entry, blocks)
    assert eff.block_id == "blk-b"
    assert eff.source == "manual"


def test_nothing_resolves_empty():
    eff = resolve_effective_block({"auto_tags": []}, _blocks("bloco-Y"))
    assert eff.block_id == ""
    assert eff.source == ""


def test_works_without_blocks_arg():
    """Sem lista de blocos, confia no manual id cru (não pode validar)."""
    entry = {"manual_timeline_block_id": "bloco-X", "computed_block_id": "bloco-Y"}
    eff = resolve_effective_block(entry)
    assert eff.block_id == "bloco-X"
    assert eff.source == "manual"
