import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.eval_ground_truth import evaluate_ground_truth, check_baseline

def _report(acc_correct, total, cw):
    # constroi predictions/labels minimas p/ evaluate_ground_truth
    labels = {f"e{i}": "bloco-01" for i in range(total)}
    preds = {}
    for i in range(total):
        ok = i < acc_correct
        preds[f"e{i}"] = {"block_id": "bloco-01" if ok else "bloco-99",
                          "band": "alta" if (not ok and i < acc_correct + cw) else "media"}
    return evaluate_ground_truth(preds, labels, {})

def test_check_baseline_passes_at_floor():
    r = _report(7, 10, 0)   # 0.7 acc, 0 cw
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 0}) == 0

def test_check_baseline_regresses_accuracy():
    r = _report(5, 10, 0)   # 0.5
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 0}) == 1

def test_check_baseline_regresses_confident_wrong():
    r = _report(7, 10, 2)
    assert check_baseline(r, {"block_accuracy_min": 0.7, "confident_wrong_max": 1}) == 1

def test_check_baseline_empty_never_regresses():
    r = _report(0, 10, 9)
    assert check_baseline(r, {}) == 0
