from scripts.retag_manifest import summarize_changes


def test_summarize_counts_block_id_changes():
    before = [
        {"id": "a", "computed_block_id": "bloco-01"},
        {"id": "b", "computed_block_id": "bloco-05"},
        {"id": "c", "computed_block_id": "bloco-03"},
    ]
    after = [
        {"id": "a", "computed_block_id": "bloco-01"},   # igual
        {"id": "b", "computed_block_id": "bloco-04"},   # mudou
        {"id": "c", "computed_block_id": ""},           # virou orfao
    ]
    rep = summarize_changes(before, after)
    assert rep["total"] == 3
    assert rep["changed"] == 2
    assert {"id": "b", "from": "bloco-05", "to": "bloco-04"} in rep["changes"]
    assert {"id": "c", "from": "bloco-03", "to": ""} in rep["changes"]
