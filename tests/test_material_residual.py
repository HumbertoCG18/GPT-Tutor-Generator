import json
from src.builder.core.summary_core import (
    load_summary_cache, write_summary_cache, assign_concepts_to_block,
)


def test_cache_roundtrip(tmp_path):
    write_summary_cache(tmp_path, "material_curation.json", {"version": 1, "entries": {"e1": {"x": 1}}})
    data = load_summary_cache(tmp_path, "material_curation.json")
    assert data["entries"]["e1"]["x"] == 1


def test_cache_missing_returns_empty(tmp_path):
    assert load_summary_cache(tmp_path, "material_curation.json") == {"version": 1, "entries": {}}


def test_assign_concepts_picks_best_block():
    blocks = [
        {"id": "bloco-01", "topic_text": "logica de predicados", "primary_topic_label": "Logica"},
        {"id": "bloco-02", "topic_text": "maquina de turing", "primary_topic_label": "Turing"},
    ]
    bid, conf = assign_concepts_to_block(["maquina", "turing"], blocks)
    assert bid == "bloco-02"
    assert conf > 0
