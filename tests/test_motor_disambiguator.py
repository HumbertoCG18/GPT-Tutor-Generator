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


def test_janela_1_emite_band_alta_conf_1():
    # metrics.gate_report conta erro janela-1 como confiante_errado PORQUE o
    # fast-path emite band "alta"; este pino protege essa semântica.
    blocks = [{"id": "bloco-A", "period_start": "2026-03-01",
               "topic_text": "logica", "sessions": []}]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    d = disambiguate({"title": "qualquer"}, ["bloco-A"], ctx)
    assert d.method == "janela-1"
    assert d.band == "alta" and d.flag is False and d.conf == 1.0


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


def test_nome_do_curso_nao_pontua_assinatura():
    # bloco-A só tem tokens do nome do curso; bloco-B tem token real do material.
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "introducao metodos formais", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "logica predicados", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index={},
        course_name="Metodos-Formais",
    )
    entry = {"title": "exercicios metodos formais logica"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    # sem o desconto, bloco-A ganharia por "metodos"+"formais" (2 tokens vs 1)
    assert d.block_ref == "bloco-B"


def test_course_name_default_vazio_preserva_fase0():
    # sem course_name, comportamento FASE 0: nome do curso pontua normalmente
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "introducao metodos formais", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "logica predicados", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "exercicios metodos formais"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"


def test_vitoria_so_por_peso_sem_token_exclusivo_flagra():
    # os DOIS blocos casam exatamente os mesmos tokens do material ("inducao",
    # "estrutural"); o best vence só por peso (session-label 1.0 vs topic 0.6)
    # + len-norm (assinatura do runner é maior). Margem calculada: s1=0.980,
    # s2=0.416, rel_margin=0.576 >= MARGIN_TAU(0.55) e s2>0 => o gate ATUAL
    # dá "alta" sem nenhum token exclusivo — exatamente o furo do D4 proxy.
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01", "topic_text": "",
         "sessions": [{"date": "2026-03-02", "label": "inducao estrutural"}]},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "inducao estrutural conjuntos recursao", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "lista inducao estrutural"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"      # seleção não muda (peso decide)
    assert d.flag is True                 # mas SEM token exclusivo => nunca confiante
    assert d.band != "alta"


def test_token_exclusivo_permite_confianca():
    # best casa "hoare"+"axiomatica" (exclusivos) + "verificacao"; runner casa
    # só "verificacao". Margem calculada: rel_margin=0.661 (dois exclusivos p/
    # folga acima do MARGIN_TAU=0.55 pós-calibração FASE 1, 2026-07-07; com só
    # 1 exclusivo a margem cai p/ 0.526, que passava no MARGIN_TAU=0.45 da
    # FASE 0 mas não sobrevive à recalibração — ajustado para continuar
    # exercendo a mesma intenção qualitativa do teste).
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "verificacao logica hoare axiomatica", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "verificacao modelos", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "deducao hoare verificacao axiomatica"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"
    assert d.flag is False
    assert d.band == "alta"
