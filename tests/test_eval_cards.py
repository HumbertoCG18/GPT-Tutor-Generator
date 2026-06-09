from scripts.eval_cards import evaluate_cards


def test_evaluate_cards_counts_in_card_as_correct():
    entries = [
        {"id": "a", "source_section": "Verif", "computed_block_id": "bloco-10", "computed_block_band": "alta"},
        {"id": "b", "source_section": "Verif", "computed_block_id": "bloco-99", "computed_block_band": "alta"},
        {"id": "c", "source_section": "", "computed_block_id": "bloco-01", "computed_block_band": "media"},
    ]
    expected = {"Verif": ["bloco-10", "bloco-11"]}
    rep = evaluate_cards(entries, expected)
    assert rep["with_card"] == 2
    assert rep["correct"] == 1
    assert rep["confident_wrong"] == 1
    assert abs(rep["accuracy"] - 0.5) < 1e-9
