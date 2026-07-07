from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.disambiguator import (
    entry_tokens,
    block_topic_tokens,
    block_session_tokens,
)


def test_entry_tokens_merge_title_label_markdown_and_drop_generics():
    entry = {
        "title": "LogicaDeHoare2",              # camelCase quebrado no fold
        "moodle_label": "Exemplos (Lógica de Floyd-Hoare)",
        "approved_markdown": "",
    }
    toks = entry_tokens(entry, markdown="Introdução ao cálculo de Hoare")
    assert "hoare" in toks
    assert "logica" in toks
    assert "introduc" not in toks and "introducao" not in toks  # stem genérico dropado
    assert all(len(t) >= 3 for t in toks)


def test_block_session_tokens_come_from_lessons_index_by_date():
    block = {
        "id": "bloco-05",
        "topic_text": "provas inducao",
        "primary_topic_label": "Provas por Indução",
        "sessions": [{"date": "2026-04-06", "label": "inducao estrutural aula"}],
    }
    ctx = MotorContext.from_artifacts(
        blocks=[block], card_block_map={},
        lessons_index={"2026-04-06": "inducao estrutural sobre listas"},
    )
    sess = block_session_tokens(block, ctx)
    # vem do lessons_index (roteiro do dia) E do label embutido na sessão
    assert "estrutural" in sess
    assert "listas" in sess
    topic = block_topic_tokens(block)
    assert "provas" in topic and "inducao" in topic
    # session-label e topic são conjuntos SEPARADOS (pesagem distinta no scorer)
    assert "listas" not in topic
