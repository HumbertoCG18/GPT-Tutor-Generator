"""relative_margin_confidence: margem relativa x força absoluta (P2.1)."""
from src.builder.routing.thresholds import relative_margin_confidence, T


def test_nao_satura_com_scores_grandes():
    # bug antigo: (8-2) + 8*0.18 = 7.44 -> 1.0. Agora: rel=0.75, strength=1.0
    c = relative_margin_confidence(8.0, 2.0)
    assert c < 1.0 and abs(c - 0.75) < 0.02


def test_winner_fraco_tem_conf_baixa_mesmo_sem_runner():
    c = relative_margin_confidence(0.5, 0.0)
    assert c < 0.75            # rel=1.0 mas strength baixa segura


def test_empate_da_zero():
    assert relative_margin_confidence(3.0, 3.0) == 0.0


def test_winner_zero_ou_negativo():
    assert relative_margin_confidence(0.0, 0.0) == 0.0
    assert relative_margin_confidence(-1.0, 0.0) == 0.0


def test_monotonica_na_margem():
    assert (relative_margin_confidence(4.0, 1.0)
            > relative_margin_confidence(4.0, 3.0))
