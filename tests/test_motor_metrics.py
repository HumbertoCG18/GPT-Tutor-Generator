# tests/test_motor_metrics.py
from src.builder.routing.motor.metrics import gate_report


def _o(correct, band, flag, method="disamb"):
    return {"correct": correct, "band": band, "flag": flag, "method": method}


def test_recall_basico_erros_flagados_sobre_erros():
    outcomes = [
        _o(True, "alta", False),          # acerto confiante — não conta como erro
        _o(False, "media", True),         # erro flagado (gate pegou)
        _o(False, "alta", False),         # confiante-errado (gate NÃO pegou)
        _o(False, "baixa", True),         # erro flagado
    ]
    r = gate_report(outcomes)
    assert r["total"] == 4
    assert r["erros"] == 3
    assert r["erros_flagados"] == 2
    assert r["confiante_errado"] == 1
    assert abs(r["recall_gate"] - 2 / 3) < 1e-9


def test_recall_sem_erros_e_1():
    r = gate_report([_o(True, "alta", False), _o(True, "media", True)])
    assert r["erros"] == 0
    assert r["recall_gate"] == 1.0


def test_flagged_certos_mede_falso_alarme():
    # flag em decisão CERTA = custo de fila humana/TIER 3, não recall
    r = gate_report([_o(True, "media", True), _o(False, "media", True)])
    assert r["flagged_total"] == 2
    assert r["flagged_certos"] == 1


def test_janela1_erro_reportado_separado():
    # erro em janela-1 é erro de JANELA (curadoria), não do gate; entra em
    # erros/confiante_errado (é confiante-errado REAL) mas ganha contador próprio
    r = gate_report([_o(False, "alta", False, method="janela-1")])
    assert r["erros"] == 1
    assert r["confiante_errado"] == 1
    assert r["janela1_erros"] == 1


def test_lista_vazia_nao_divide_por_zero():
    r = gate_report([])
    assert r["total"] == 0
    assert r["recall_gate"] == 1.0
