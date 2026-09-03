"""Fase 3c (item 5): tokenizador unico do motor (corte 3 do refactor, strangler so no disambiguator) e
tokens CURTOS consagrados pelo cronograma no desempate, nos dois lados, so onde a decisao e flagada.

Blocos com o shape real do `.timeline_index.json` (kind/sessions[{date,label}]/topic_text/primary_topic_label);
labels de sessao no estilo do IA ("algoritmo genetico ag") e do FR ("protocolo tcp udp").
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.disambiguator import _GENERIC_STEMS, _toks, course_short_vocab, disambiguate
from src.builder.text.tokens import motor_tokens


def test_motor_tokens_matches_the_disambiguator_tokenizer_byte_for_byte():
    text = "LogicaDeHoare parte 2: Exercicios sobre IA e 2026"
    assert motor_tokens(text, generic_stems=_GENERIC_STEMS) == _toks(text) == {"logica", "hoare"}


def test_motor_tokens_keeps_short_tokens_only_when_consecrated():
    assert motor_tokens("Busca com AG e HC", generic_stems=_GENERIC_STEMS) == {"busca"}
    assert motor_tokens("Busca com AG e HC", generic_stems=_GENERIC_STEMS, short_vocab={"ag"}) == {"busca", "ag"}


def _block(n, date, label, topic):
    return {"id": f"bloco-{n:02d}", "block_uuid": f"uuid-{n:02d}", "kind": "class", "period_start": date, "period_end": date,
            "primary_topic_label": topic, "topic_text": topic.lower(),
            "sessions": [{"id": f"s{n}", "date": date, "kind": "class", "label": label}]}


BLOCKS = [_block(13, "2026-05-18", "algoritmo genetico ag", "Algoritmos geneticos"),
          _block(15, "2026-06-01", "busca local hc e sa", "Hill climbing e simulated annealing")]


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map={}, lessons_index={}, course_name="Inteligencia Artificial")


def test_course_short_vocab_comes_from_schedule_labels_and_topics():
    assert course_short_vocab(_ctx()) == frozenset({"ag", "hc", "sa"})


def _entry(title):
    return {"id": "x", "title": title, "category": "codigo-professor", "file_type": "pdf", "moodle_label": title}


def test_short_vocab_decides_a_flagged_tie_and_is_watched_separately():
    ctx = _ctx()
    d = disambiguate(_entry("Exercicios AG"), ["bloco-13", "bloco-15"], ctx, provider="labels")
    assert (d.block_ref, d.method, d.flag) == ("bloco-13", "disamb-curto", False)


def test_confident_standard_decision_is_not_recomputed():
    ctx = _ctx()
    d = disambiguate(_entry("Exemplos de hill climbing"), ["bloco-13", "bloco-15"], ctx, provider="labels")
    assert (d.block_ref, d.method, d.flag) == ("bloco-15", "disamb", False)


def test_short_vocab_absent_keeps_the_flag():
    ctx = MotorContext.from_artifacts(blocks=[_block(13, "2026-05-18", "algoritmo genetico", "Algoritmos geneticos"),
                                              _block(15, "2026-06-01", "busca local", "Hill climbing")],
                                      card_block_map={}, lessons_index={}, course_name="")
    d = disambiguate(_entry("Exercicios AG"), ["bloco-13", "bloco-15"], ctx, provider="labels")
    assert d.method == "disamb" and d.flag
