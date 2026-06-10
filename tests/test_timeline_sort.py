from src.ui.timeline_dashboard import timeline_sort_key


def _sorted_ids(blocks, column):
    return [b["id"] for b in sorted(blocks, key=lambda b: timeline_sort_key(b, column))]


def test_sort_by_sequence_is_numeric_not_lexical():
    # Sequence is derived from the numeric suffix in the block id (e.g. "bloco-10" -> 10)
    blocks = [{"id": "bloco-10"}, {"id": "bloco-9"}, {"id": "bloco-2"}]
    assert _sorted_ids(blocks, "#") == ["bloco-2", "bloco-9", "bloco-10"]


def test_sort_by_date_chronological():
    blocks = [
        {"id": "a", "period_start": "2026-03-20"},
        {"id": "b", "period_start": "2026-03-02"},
        {"id": "c", "period_start": "2026-03-10"},
    ]
    assert _sorted_ids(blocks, "Data") == ["b", "c", "a"]


def test_sort_missing_values_go_last_stable():
    blocks = [
        {"id": "a", "period_start": "2026-03-10"},
        {"id": "b"},
        {"id": "c", "period_start": "2026-03-05"},
    ]
    assert _sorted_ids(blocks, "Data") == ["c", "a", "b"]


def test_sort_by_unit_string():
    blocks = [{"id": "a", "unit_slug": "u3"}, {"id": "b", "unit_slug": "u1"}]
    assert _sorted_ids(blocks, "Unidade") == ["b", "a"]


def test_sort_by_file_count():
    # _file_count is injected by the view before sorting
    blocks = [{"id": "a", "_file_count": 3}, {"id": "b", "_file_count": 1}]
    assert _sorted_ids(blocks, "Arq.") == ["b", "a"]
