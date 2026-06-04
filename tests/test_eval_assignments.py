import json
from pathlib import Path

from scripts.eval_assignments import load_gold, predict_block

GOLD = Path("tests/fixtures/eval/assignments_gold.json")


def test_predict_block_returns_id_and_band_for_date_case():
    gold = load_gold(GOLD)
    case = next(c for c in gold["cases"] if c["id"] == "case-date")
    block_id, band = predict_block(case, gold["timeline"]["blocks"])
    assert block_id == "bloco-01"
    assert band in {"alta", "media", "baixa"}
