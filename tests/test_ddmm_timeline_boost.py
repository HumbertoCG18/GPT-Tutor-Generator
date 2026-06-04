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


def _make_range_block(period_start: str, period_end: str, date_text: str = "") -> dict:
    block = _make_block(date_text=date_text or period_start)
    block["period_start"] = period_start
    block["period_end"] = period_end
    return block


def test_strong_boost_when_date_in_middle_of_text_falls_in_block_range():
    # O regex antigo era ancorado no início (raw começa com DD.MM). Aqui a data
    # está NO MEIO do título e ainda assim casa o range do bloco -> boost forte.
    block = _make_range_block("2026-03-10", "2026-03-20")
    signals_with = _make_signals("Slides da aula em 15/03/2026 sobre processos")
    signals_without = _make_signals("Slides da aula sobre processos")

    score_with = _call_score(signals_with, block)
    score_without = _call_score(signals_without, block)

    assert score_with > score_without


def test_strong_boost_beats_weak_month_only_boost():
    # Data exata dentro do range (forte) > mês compatível mas fora do range (fraco).
    block = _make_range_block("2026-03-10", "2026-03-20")
    signals_in_range = _make_signals("Aula 15/03/2026")
    signals_month_only = _make_signals("Aula 28/03/2026")  # mar, mas fora do range

    score_in_range = _call_score(signals_in_range, block)
    score_month_only = _call_score(signals_month_only, block)

    assert score_in_range > score_month_only


def test_weak_month_boost_when_month_matches_but_not_in_range():
    block = _make_range_block("2026-03-10", "2026-03-20")
    signals_month = _make_signals("Aula 28/03/2026")  # mesmo mês, fora do range
    signals_other = _make_signals("Aula 28/07/2026")  # outro mês

    score_month = _call_score(signals_month, block)
    score_other = _call_score(signals_other, block)

    assert score_month > score_other


def test_subchapter_number_pair_does_not_earn_date_boost():
    # Regressão: "Capitulo 5.12 - Introducao" normaliza para "capitulo 5 12 ..."
    # e ANTES casava como data(2026,12,5), aplicando o boost +0.30 mais forte.
    # O par de números é subcapítulo no MEIO do título -> NÃO deve dar boost.
    block = _make_range_block("2026-12-01", "2026-12-31")  # dezembro: month bateria
    signals_subchapter = _make_signals("Capitulo 5.12 - Introducao")
    signals_plain = _make_signals("Capitulo Introducao")

    score_subchapter = _call_score(signals_subchapter, block)
    score_plain = _call_score(signals_plain, block)

    # Sem data fantasma: o subcapítulo não pode pontuar acima do título sem data.
    assert score_subchapter == score_plain


def test_real_normalized_leading_date_still_earns_strong_boost():
    # Recall preservado: data real DD.MM no INÍCIO do material (como chega aos
    # signals, JÁ normalizada -> "12 03 ...") cai no range do bloco e ainda ganha
    # o boost forte. Prova que a correção não derruba o sinal verdadeiro.
    block = _make_range_block("2026-03-10", "2026-03-20")
    signals_with_date = _make_signals("Processos", raw_target="12.03 processos")
    signals_without = _make_signals("Processos", raw_target="processos")

    score_with = _call_score(signals_with_date, block)
    score_without = _call_score(signals_without, block)

    assert score_with - score_without == 0.30
