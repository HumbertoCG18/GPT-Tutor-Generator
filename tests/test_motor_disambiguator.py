from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.disambiguator import (
    entry_tokens,
    block_topic_tokens,
    block_session_tokens,
    disambiguate,
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


def _ctx(blocks, lessons=None):
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index=lessons or {}
    )


def test_window_of_one_places_directly_high_band_no_flag():
    blocks = [{"id": "bloco-04", "topic_text": "especificacoes indutivas recursivas"}]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "ConjuntosIndutivos.pdf"}, ["bloco-04"], ctx)
    assert d.block_ref == "bloco-04"
    assert d.band == "alta" and d.flag is False and d.method == "janela-1"


def test_len_norm_beats_verbose_sink_block():
    # bloco-verboso tem assinatura enorme (sink); bloco-alvo é enxuto e casa 'hoare'.
    blocks = [
        {"id": "bloco-10", "topic_text": "hoare"},
        {"id": "bloco-11", "topic_text": (
            "logica proposicional predicados conjuntos relacoes funcoes inducao "
            "recursao provas semantica sintaxe modelos verificacao"
        )},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "Logica de Hoare"}, ["bloco-10", "bloco-11"], ctx)
    assert d.block_ref == "bloco-10"  # len-norm impede o sumidouro verboso


def test_session_label_outranks_topic_text_on_multiblock():
    # Ambos os blocos têm o MESMO topic grosso; só o session-label discrimina.
    blocks = [
        {"id": "bloco-05", "topic_text": "provas inducao",
         "sessions": [{"date": "2026-04-06", "label": "inducao estrutural listas"}]},
        {"id": "bloco-06", "topic_text": "provas inducao",
         "sessions": [{"date": "2026-04-13", "label": "inducao arvores binarias"}]},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "Prova por indução em árvores"}, ["bloco-05", "bloco-06"], ctx)
    assert d.block_ref == "bloco-06"  # 'arvores' vem do session-label, não do topic


def test_tie_flags_and_is_not_high_band():
    # Sem token discriminante em nenhum lado -> empate -> flag, band != alta.
    blocks = [
        {"id": "bloco-05", "topic_text": "provas inducao"},
        {"id": "bloco-06", "topic_text": "provas inducao"},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "material sem sinal"}, ["bloco-05", "bloco-06"], ctx)
    assert d.flag is True
    assert d.band != "alta"
    assert d.block_ref in {"bloco-05", "bloco-06"}
    assert d.window == ["bloco-05", "bloco-06"]
