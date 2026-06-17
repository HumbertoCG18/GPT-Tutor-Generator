"""Testes sinteticos para score_against_gold — sem IO, sem repo real."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.eval_code_block_gold import score_against_gold


def _gold(*entries):
    """Monta gold_entries a partir de tuplas (id, true_block, confidence)."""
    return {eid: {"true_block_id": blk, "confidence": conf} for eid, blk, conf in entries}


def _rows(**kwargs):
    """Monta rows_by_id a partir de kwargs: id -> (funil_block, resolver_block, funil_band, resolver_band)."""
    return {
        eid: {
            "funil_block": v[0],
            "resolver_block": v[1],
            "funil_band": v[2],
            "resolver_band": v[3],
        }
        for eid, v in kwargs.items()
    }


def test_ambos_corretos():
    """Caso 1: funil certo + resolver certo — 0 confiante-errado."""
    gold = _gold(("a", "bloco-01", "alta"))
    rows = _rows(a=("bloco-01", "bloco-01", "alta", "alta"))
    r = score_against_gold(gold, rows)
    assert r["funil"]["correct"] == 1
    assert r["resolver"]["correct"] == 1
    assert r["funil"]["confident_wrong"] == 0
    assert r["resolver"]["confident_wrong"] == 0
    assert r["funil"]["block_accuracy"] == 1.0
    assert r["resolver"]["block_accuracy"] == 1.0


def test_funil_errado_band_alta():
    """Caso 2: funil errado com band alta -> confident_wrong funil = 1."""
    gold = _gold(("a", "bloco-01", "alta"))
    rows = _rows(a=("bloco-02", "bloco-01", "alta", "alta"))
    r = score_against_gold(gold, rows)
    assert r["funil"]["confident_wrong"] == 1
    assert r["resolver"]["confident_wrong"] == 0
    assert r["funil"]["correct"] == 0
    assert r["resolver"]["correct"] == 1


def test_resolver_melhor_que_funil():
    """Caso 3: resolver acerta onde funil erra -> resolver_accuracy > funil_accuracy."""
    gold = _gold(("a", "bloco-01", "alta"), ("b", "bloco-02", "alta"))
    rows = _rows(
        a=("bloco-99", "bloco-01", "baixa", "alta"),
        b=("bloco-99", "bloco-02", "baixa", "alta"),
    )
    r = score_against_gold(gold, rows)
    assert r["resolver"]["block_accuracy"] > r["funil"]["block_accuracy"]
    assert r["funil"]["correct"] == 0
    assert r["resolver"]["correct"] == 2


def test_entry_ausente_vai_para_missing():
    """Caso 4: entry do gold sem row -> missing, nao conta no total."""
    gold = _gold(("presente", "bloco-01", "alta"), ("ausente", "bloco-02", "alta"))
    rows = _rows(presente=("bloco-01", "bloco-01", "alta", "alta"))
    r = score_against_gold(gold, rows)
    assert "ausente" in r["missing"]
    assert r["funil"]["total"] == 1
    assert r["resolver"]["total"] == 1


def test_by_confidence_tier():
    """Caso 5: 1 alta correta + 1 media errada -> by_confidence['alta'] acc 1.0."""
    gold = _gold(("x", "bloco-01", "alta"), ("y", "bloco-02", "media"))
    rows = _rows(
        x=("bloco-01", "bloco-01", "alta", "alta"),
        y=("bloco-99", "bloco-99", "baixa", "baixa"),
    )
    r = score_against_gold(gold, rows)
    assert r["by_confidence"]["alta"]["funil"]["accuracy"] == 1.0
    assert r["by_confidence"]["alta"]["resolver"]["accuracy"] == 1.0
    assert r["by_confidence"]["media"]["funil"]["accuracy"] == 0.0
    assert r["funil"]["total"] == 2
    assert r["funil"]["correct"] == 1
    assert r["funil"]["block_accuracy"] == 0.5
