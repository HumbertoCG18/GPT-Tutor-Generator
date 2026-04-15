from src.builder.timeline_index import _build_timeline_index


def test_build_timeline_index_marks_ignored_rows_from_kind():
    candidate_rows = [
        {"date_text": "30/03/2026", "title": "Provas por indução", "kind": "class"},
        {"date_text": "22/04/2026", "title": "Prova P1", "kind": "exam"},
        {"date_text": "20/04/2026", "title": "Suspensão", "kind": "suspension", "ignored": True},
    ]
    index = _build_timeline_index(candidate_rows, unit_index=[])
    blocks = index.get("blocks", [])
    # Nenhum bloco deve ter row ignorada ativa no scoring
    for block in blocks:
        for row in block.get("rows", []):
            if row.get("date_text") == "20/04/2026":
                assert row.get("ignored") is True
