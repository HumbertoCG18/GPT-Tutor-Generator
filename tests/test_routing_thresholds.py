from src.builder.routing.thresholds import margin_confidence, T


def test_margin_confidence_formula():
    # (winner - runner) + winner*k, clamp 0..1
    assert margin_confidence(2.0, 1.0, k=0.18) == 1.0  # 1.0 + 0.36 -> clamp 1.0
    assert round(margin_confidence(1.2, 1.0, k=0.18), 3) == round((0.2) + 1.2 * 0.18, 3)
    assert margin_confidence(0.0, 0.0, k=0.18) == 0.0


def test_thresholds_present():
    # limiares nomeados centralizados
    assert T.UNIT_TAG == 0.65
    assert T.SUBUNIT_TAG == 0.60
    assert T.BLOCO_TAG == 0.50
    assert T.BLOCK_UNIT_MIN_WINNER == 1.0
    assert T.BLOCK_UNIT_MIN_GAP == 0.35
    assert T.VOTE_DOMINANCE == 0.60
    assert T.MATERIAL_COVERAGE_MIN == 0.70  # gate de cobertura (Fase 4)
