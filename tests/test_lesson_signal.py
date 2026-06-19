from src.builder.routing.concept_resolver import (
    score_lesson_match,
    resolve_material_assignment,
    W_LESSON,
)
from src.builder.text.normalize import normalize_match_text


_LESSONS = {"version": 1, "by_date": {
    "2026-04-27": "Lógica de Hoare",
    "2026-04-29": "Lógica de Hoare",
    "2026-05-13": "Programas em Dafny",
}}


def _block(bid, unit, dates):
    return {
        "id": bid, "unit_slug": unit, "primary_topic_label": "", "topics": [],
        "sessions": [{"id": f"{bid}-{d}", "date": d, "kind": "class", "label": "", "signals": []} for d in dates],
        "card_evidence": [],
    }


def test_lesson_match_uses_clean_label_against_block_lesson_topics():
    block = _block("bloco-10", "u-verif", ["2026-04-27", "2026-04-29"])
    # sinal LIMPO do material casa o tópico da aula daquele bloco
    signals = {"moodle_label_text": "logica de hoare parte 2", "title_text": "LogicaDeHoare2"}
    score = score_lesson_match(signals, block, _LESSONS, normalize_match_text)
    assert score > 0.0


def test_lesson_match_ignores_markdown_and_concepts():
    block = _block("bloco-10", "u-verif", ["2026-04-27"])
    # sem label/título limpos; só markdown ruidoso não deve casar a lesson
    signals = {"moodle_label_text": "", "title_text": "", "markdown_text": "logica de hoare hoare hoare"}
    assert score_lesson_match(signals, block, _LESSONS, normalize_match_text) == 0.0


def test_lesson_match_capped():
    # overlap > LESSON_OVERLAP_CAP deve TRUNCAR em W_LESSON*cap, não crescer
    # linearmente — exercita o min() (anti-envenenamento), não só o teto folgado.
    rich = {"version": 1, "by_date": {
        "2026-04-27": "logica hoare dafny invariantes terminacao",
    }}
    block = _block("bloco-10", "u-verif", ["2026-04-27"])
    # sinal limpo casa 5 tokens distintos (> cap 3) -> score travado em W_LESSON*3
    signals = {"moodle_label_text": "logica hoare dafny invariantes", "title_text": "terminacao"}
    score = score_lesson_match(signals, block, rich, normalize_match_text)
    assert score == W_LESSON * 3  # truncamento real (overlap 5 -> cap 3)


def test_lesson_index_absent_scores_zero():
    block = _block("bloco-10", "u-verif", ["2026-04-27"])
    signals = {"moodle_label_text": "logica de hoare", "title_text": "hoare"}
    assert score_lesson_match(signals, block, None, normalize_match_text) == 0.0
    assert score_lesson_match(signals, block, {"by_date": {}}, normalize_match_text) == 0.0


def test_resolver_lesson_term_breaks_tie_toward_lesson_block():
    # 2 blocos sem outro sinal discriminante; a lesson + label limpo decide
    b_hoare = _block("bloco-10", "u-verif", ["2026-04-27", "2026-04-29"])
    b_dafny = _block("bloco-13", "u-verif", ["2026-05-13"])
    entry = {"id": "e1", "file_type": "pdf"}
    signals = {"moodle_label_text": "logica de hoare parte 2", "title_text": "LogicaDeHoare2"}
    a = resolve_material_assignment(entry, [b_dafny, b_hoare], [], signals=signals, lessons_index=_LESSONS)
    assert a["block_id"] == "bloco-10"
    assert a["signals"].get("lesson", 0.0) > 0.0


def test_resolver_without_lessons_index_unchanged_default():
    # lessons_index default None → termo lesson ausente, comportamento atual
    b = _block("bloco-10", "u-verif", ["2026-04-27"])
    entry = {"id": "e1", "file_type": "pdf"}
    a = resolve_material_assignment(entry, [b], [], signals={"title_text": "x"})
    assert a["signals"].get("lesson", 0.0) == 0.0
