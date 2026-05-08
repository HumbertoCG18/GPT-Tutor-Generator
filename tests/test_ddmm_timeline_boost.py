from src.builder.routing.file_map import score_entry_against_timeline_block
from src.builder.extraction.entry_signals import normalize_match_text


def _make_signals(title: str, raw_target: str = "") -> dict:
    return {
        "title_text": normalize_match_text(title),
        "markdown_headings_text": "",
        "markdown_lead_text": "",
        "markdown_text": "",
        "category_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
        "tags_text": "",
        "raw_text": normalize_match_text(raw_target),
    }


def _make_block(date_text: str, content: str = "Aula generica") -> dict:
    return {
        "id": "bloco-01",
        "rows": [{"content": content, "date_text": date_text, "ignored": False}],
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": True,
        "topic_candidates": [],
        "topic_text": "",
        "topics": [],
        "aliases": [],
        "card_evidence": [],
        "sessions": [],
        "period_label": date_text,
        "scores": [0.0],
    }


def _call_score(signals, block):
    from src.builder.extraction.entry_signals import (
        normalize_match_text,
        score_text_against_row,
    )
    from src.builder.routing.file_map import score_card_evidence_against_entry

    def _score_card(s, items):
        return score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text
        )

    return score_entry_against_timeline_block(
        signals,
        block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=_score_card,
    )


def test_ddmm_boost_applied_when_filename_date_matches_block_date():
    signals = _make_signals("Processos", raw_target="12.03 processos")
    block = _make_block(date_text="12/03/2026")
    score_with_match = _call_score(signals, block)

    signals_no_date = _make_signals("Processos", raw_target="processos")
    score_without = _call_score(signals_no_date, block)

    assert score_with_match > score_without


def test_ddmm_boost_not_applied_when_date_mismatches():
    signals_mismatch = _make_signals("Processos", raw_target="15.04 processos")
    signals_match = _make_signals("Processos", raw_target="12.03 processos")
    block = _make_block(date_text="12/03/2026")

    score_mismatch = _call_score(signals_mismatch, block)
    score_match = _call_score(signals_match, block)

    assert score_match > score_mismatch


def test_ddmm_boost_not_applied_when_no_date_prefix():
    signals = _make_signals("Processos", raw_target="processos sem data")
    block = _make_block(date_text="12/03/2026")
    score = _call_score(signals, block)
    assert isinstance(score, float)
