import json
from pathlib import Path

from scripts.eval_assignments import evaluate, load_gold, predict_block

GOLD = Path("tests/fixtures/eval/assignments_gold.json")


def test_predict_block_returns_id_and_band_for_date_case():
    gold = load_gold(GOLD)
    case = next(c for c in gold["cases"] if c["id"] == "case-date")
    block_id, band = predict_block(case, gold["timeline"]["blocks"])
    assert block_id == "bloco-01"
    assert band in {"alta", "media", "baixa"}


def test_evaluate_reports_accuracy_and_band_calibration():
    gold = load_gold(GOLD)
    report = evaluate(gold)
    assert report["total"] == len(gold["cases"])
    assert 0.0 <= report["block_accuracy"] <= 1.0
    # cada caso classificado como correto/errado e atribuido a uma band
    assert report["correct"] + report["wrong"] == report["total"]
    # calibracao por band existe e soma o total
    band_total = sum(b["correct"] + b["wrong"] for b in report["bands"].values())
    assert band_total == report["total"]
    # o caso de data deve acertar o bloco-01
    by_id = {r["id"]: r for r in report["cases"]}
    assert by_id["case-date"]["predicted"] == "bloco-01"
    assert by_id["case-date"]["correct"] is True


def test_block_accuracy_not_below_baseline():
    gold = load_gold(GOLD)
    report = evaluate(gold)
    baseline = float(gold["baseline"]["block_accuracy"])
    assert report["block_accuracy"] + 1e-9 >= baseline, (
        f"REGRESSAO: {report['block_accuracy']:.3f} < baseline {baseline:.3f}. "
        f"Erros: {[c['id'] for c in report['cases'] if not c['correct']]}"
    )


def test_no_orphan_when_instructional_blocks_exist():
    # Spec: com blocos instrucionais presentes, nenhum material vira orfao.
    gold = load_gold(GOLD)
    report = evaluate(gold)
    assert report["orphans"] == 0, (
        f"orfaos inesperados: {[c['id'] for c in report['cases'] if c['predicted'] == '']}"
    )
