def test_resolve_manual_block_falls_back_to_nth_instructional_block():
    from src.builder.routing.file_map import resolve_entry_manual_timeline_block

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
    resolved = resolve_entry_manual_timeline_block(entry, timeline_context)
    assert resolved["id"] == "bloco-auto-005"
