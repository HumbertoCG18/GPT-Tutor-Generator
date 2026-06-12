"""Regressão do bug B3: índice persistido (sem 'rows') degenerava pra 1º bloco.

Prova viva: blocos no shape de _serialize_timeline_index (id + sessions +
source_rows) devem ser reconhecidos como pré-construídos, não reconstruídos.
"""
import importlib.util
from pathlib import Path

from src.builder.routing.file_map import _is_prebuilt_block

_SPEC = importlib.util.spec_from_file_location(
    "eval_assignments",
    Path(__file__).resolve().parents[1] / "scripts" / "eval_assignments.py",
)
eval_assignments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(eval_assignments)


def _pblock(bid, topic, start, end, unit="unidade-01-metodos-formais"):
    """Bloco no shape PERSISTIDO (cf. _serialize_timeline_index, index.py:902)."""
    return {
        "id": bid, "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}", "kind": "class",
        "unit_slug": unit, "unit_confidence": 0.8,
        "primary_topic_slug": topic.replace(" ", "-"),
        "primary_topic_label": topic, "primary_topic_confidence": 0.8,
        "topic_ambiguous": False, "topic_candidates": [],
        "topic_text": topic, "topics": [topic],
        "aliases": [], "card_evidence": [],
        "sessions": [{"label": topic, "date": start}],
        "source_rows": [{"date": start, "description": topic}],
    }


def test_is_prebuilt_block_accepts_legacy_rows_shape():
    assert _is_prebuilt_block({"rows": [], "id": "b1"}) is True


def test_is_prebuilt_block_accepts_persisted_shape():
    assert _is_prebuilt_block(_pblock("bloco-01", "logica", "2026-03-02", "2026-03-02")) is True


def test_is_prebuilt_block_rejects_raw_cronograma_row():
    assert _is_prebuilt_block({"date": "2026-03-02", "description": "aula 1"}) is False
    assert _is_prebuilt_block({"id": "x"}) is False
    assert _is_prebuilt_block("nao-dict") is False


def test_persisted_index_does_not_degenerate_to_first_block():
    """ANTES do fix: blocos persistidos eram tratados como linhas cruas e a
    predição colapsava pro 1º bloco. DEPOIS: o scorer ranqueia os blocos reais."""
    blocks = [
        _pblock("bloco-01", "logica predicados sintaxe semantica", "2026-03-09", "2026-03-09"),
        _pblock("bloco-02", "inducao estrutural arvores listas", "2026-03-30", "2026-04-01"),
    ]
    case = {
        "id": "provas-arvores",
        "title": "ProvasIndutivas Arvores",
        "category": "material-de-aula",
        "raw_target": "raw/pdfs/ProvasIndutivas_Arvores.pdf",
        "tags": "inducao arvores",
        "markdown": "inducao estrutural sobre arvores e listas provas indutivas",
        "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                       "ambiguous": False},
        "expected_block_id": "bloco-02",
    }
    predicted, _band = eval_assignments.predict_block(case, blocks)
    assert predicted == "bloco-02"


def test_scoring_direto_funciona_com_bloco_persistido():
    """B3 no 2o call site: score_entry_against_timeline_block lia so 'rows' —
    bloco persistido pontuava 0.0 e o ranking degenerava pro primeiro."""
    from src.builder.routing.file_map import (
        score_entry_against_timeline_block, score_card_evidence_against_entry,
    )
    from src.builder.extraction.entry_signals import (
        collect_entry_unit_signals, score_text_against_row,
    )
    from src.builder.text.normalize import normalize_match_text
    block = _pblock("bloco-02", "inducao estrutural arvores", "2026-03-30", "2026-04-01")
    entry = {"id": "x", "title": "inducao arvores", "category": "material-de-aula",
             "tags": "", "manual_tags": [], "auto_tags": []}
    signals = collect_entry_unit_signals(entry, "inducao estrutural sobre arvores")
    score = score_entry_against_timeline_block(
        signals, block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text,
        ),
    )
    assert score > 0.0
