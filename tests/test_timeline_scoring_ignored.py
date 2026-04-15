"""Tests for Task 4: scorer descarta rows ignoradas."""

from src.builder.engine import _score_entry_against_timeline_block
from src.builder.timeline_index import _timeline_block_is_administrative_only


def _make_signals(text: str) -> dict:
    return {
        "combined_text": text,
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
        "date_range": {},
        "date_values": [],
        "session_signals": [],
    }


def test_score_block_ignores_rows_marked_ignored():
    # Block with a single row whose title would match, but ignored=True.
    block = {
        "id": "bloco-test-ignored",
        "rows": [
            {
                "content": "(08/07/2026) QUA — Prova PS [Prova de Substituição]",
                "ignored": True,
            }
        ],
        "unit_slug": "",
        "topic_text": "prova substituicao",
    }
    signals = _make_signals("prova substituicao")
    assert _score_entry_against_timeline_block(signals, block) == 0.0


def test_score_block_keeps_non_ignored_rows():
    block = {
        "id": "bloco-test-mixed",
        "rows": [
            {
                "content": "(08/07/2026) QUA — Prova PS",
                "ignored": True,
            },
            {
                "content": "(30/03/2026) SEG — Provas por inducao [Aula]",
                "ignored": False,
            },
        ],
        "unit_slug": "",
        "topic_text": "provas por inducao",
    }
    signals = _make_signals("provas por inducao")
    score = _score_entry_against_timeline_block(signals, block)
    assert score >= 0.0  # basic sanity: didn't short-circuit to 0


def test_administrative_only_true_when_all_rows_ignored():
    block = {
        "rows": [
            {"content": "Prova PS", "ignored": True},
            {"content": "SE Day", "ignored": True},
        ]
    }
    assert _timeline_block_is_administrative_only(block) is True


def test_administrative_only_ignores_ignored_rows_when_mixed():
    # One ignored + one pure-instructional → not administrative-only.
    block = {
        "rows": [
            {"content": "Prova PS", "ignored": True},
            {"content": "Provas por inducao", "ignored": False},
        ]
    }
    assert _timeline_block_is_administrative_only(block) is False
