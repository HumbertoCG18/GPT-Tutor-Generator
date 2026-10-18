def test_resolve_manual_block_falls_back_to_nth_instructional_block():
    from src.builder.routing.file_map import resolve_entry_manual_timeline_block

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
    resolved = resolve_entry_manual_timeline_block(entry, timeline_context)
    assert resolved["id"] == "bloco-auto-005"
