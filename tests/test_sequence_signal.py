from src.builder.routing.sequence import extract_lecture_ordinal


def test_extracts_ordinal_after_aula_marker():
    assert extract_lecture_ordinal("aula 03 slides") == 3


def test_extracts_ordinal_with_single_digit():
    assert extract_lecture_ordinal("aula 3") == 3


def test_extracts_ordinal_after_encontro_marker():
    assert extract_lecture_ordinal("encontro 2 logica") == 2


def test_extracts_ordinal_when_glued_to_marker():
    # "Aula03.pdf" normaliza para "aula03 pdf" (sem espaco)
    assert extract_lecture_ordinal("aula03 pdf") == 3


def test_picks_digit_adjacent_to_marker_not_trailing_year():
    assert extract_lecture_ordinal("aula 03 2024") == 3


def test_returns_none_for_lista_marker():
    assert extract_lecture_ordinal("lista 2 inducao") is None


def test_returns_none_for_prova_marker():
    assert extract_lecture_ordinal("prova 1") is None


def test_returns_none_for_subchapter_pair():
    # "Capitulo 5.12" normaliza para "capitulo 5 12" -> sem marcador de aula
    assert extract_lecture_ordinal("capitulo 5 12 introducao") is None


def test_returns_none_for_bare_year():
    assert extract_lecture_ordinal("slides 2024 revisao") is None


def test_returns_none_for_roman_numeral():
    assert extract_lecture_ordinal("aula iii predicados") is None


def test_returns_none_when_no_ordinal():
    assert extract_lecture_ordinal("slides de logica") is None


def test_returns_none_for_year_glued_to_marker():
    # "aula2024" nao deve casar (mais de 3 digitos colados, sem fronteira)
    assert extract_lecture_ordinal("aula2024 revisao") is None


from src.builder.routing.sequence import annotate_class_ordinals


def _blocks():
    return [
        {"id": "b1", "kind": "class"},
        {"id": "b2", "kind": "class"},
        {"id": "b3", "kind": "holiday"},
        {"id": "b4", "kind": "review"},
        {"id": "b5", "kind": "class"},
    ]


def test_numbers_only_class_blocks_in_order():
    blocks = annotate_class_ordinals(_blocks())
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_block_without_kind_gets_none():
    blocks = annotate_class_ordinals([{"id": "x"}])
    assert blocks[0]["class_ordinal"] is None


def test_is_idempotent():
    blocks = _blocks()
    annotate_class_ordinals(blocks)
    annotate_class_ordinals(blocks)
    by_id = {b["id"]: b["class_ordinal"] for b in blocks}
    assert by_id == {"b1": 1, "b2": 2, "b3": None, "b4": None, "b5": 3}


def test_no_class_blocks_all_none():
    blocks = annotate_class_ordinals([{"id": "h", "kind": "holiday"}])
    assert blocks[0]["class_ordinal"] is None


from src.builder.routing.thresholds import T


def test_sequence_boost_is_moderate_tiebreaker():
    # Menor que data (0.30) e topico-compativel (0.48): desempata sem sobrepor.
    assert T.SEQUENCE_BOOST == 0.20
    assert T.SEQUENCE_BOOST < 0.30


from src.builder.routing.sequence import score_sequence_match


def _signals(title="", raw=""):
    return {"title_text": title, "raw_text": raw}


def test_boost_when_title_ordinal_matches_class_ordinal():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.20


def test_boost_uses_raw_when_title_has_no_ordinal():
    block = {"class_ordinal": 2}
    assert score_sequence_match(_signals(title="slides", raw="aula 2"), block) == 0.20


def test_no_boost_when_ordinal_mismatches():
    block = {"class_ordinal": 1}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.0


def test_no_boost_when_material_has_no_ordinal():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="slides de logica"), block) == 0.0


def test_no_boost_when_block_is_not_class():
    block = {"class_ordinal": None}
    assert score_sequence_match(_signals(title="aula 03"), block) == 0.0


def test_no_boost_when_block_missing_ordinal_key():
    assert score_sequence_match(_signals(title="aula 03"), {}) == 0.0


def test_explicit_boost_value_overrides_default():
    block = {"class_ordinal": 3}
    assert score_sequence_match(_signals(title="aula 03"), block, boost=0.5) == 0.5


from src.builder.routing.file_map import score_entry_against_timeline_block
from src.builder.routing.sequence import annotate_class_ordinals
from src.builder.extraction.entry_signals import (
    normalize_match_text,
    score_text_against_row,
)
from src.builder.routing.file_map import score_card_evidence_against_entry


def _full_signals(title):
    # Mesmo formato dos signals reais; campos vazios exceto o titulo.
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
        "raw_text": "",
    }


def _class_block(block_id):
    return {
        "id": block_id,
        "kind": "class",
        "rows": [{"content": "aula expositiva geral", "date_text": "", "ignored": False}],
        "unit_slug": "",
        "unit_confidence": 0.0,
        "primary_topic_slug": "",
        "primary_topic_confidence": 0.0,
        "topic_ambiguous": True,
        "topic_candidates": [],
        "topic_text": "",
        "card_evidence": [],
        "sessions": [],
        "period_label": block_id,
        "scores": [0.0],
    }


def _score(signals, block):
    return score_entry_against_timeline_block(
        signals,
        block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text
        ),
    )


def test_scorer_boosts_matching_class_ordinal_block():
    blocks = annotate_class_ordinals([_class_block("b1"), _class_block("b2"), _class_block("b3")])
    signals = _full_signals("Aula 03")
    score_third = _score(signals, blocks[2])   # class_ordinal == 3, matches
    score_first = _score(signals, blocks[0])   # class_ordinal == 1, no match
    assert round(score_third - score_first, 2) == 0.20


def test_scorer_no_sequence_delta_without_ordinal():
    blocks = annotate_class_ordinals([_class_block("b1"), _class_block("b2"), _class_block("b3")])
    signals = _full_signals("Slides de logica")
    score_third = _score(signals, blocks[2])
    score_first = _score(signals, blocks[0])
    assert score_third == score_first
