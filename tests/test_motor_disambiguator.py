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


class TestGateConcordanciaData:
    """D4 para janela-1 vinda de P3: alta só com token discriminante global."""

    @staticmethod
    def _ctx():
        from src.builder.routing.motor.contracts import MotorContext
        # "gerencia" aparece em 3 blocos (df alto = boilerplate do curso);
        # "escalonamento" e "memoria" são específicos (df=1).
        blocks = [
            {"id": "bloco-03", "period_start": "2026-03-10",
             "topic_text": "escalonamento gerencia processador",
             "sessions": [{"date": "2026-03-10", "label": "escalonamento"}]},
            {"id": "bloco-11", "period_start": "2026-05-12",
             "topic_text": "gerencia memoria paginacao",
             "sessions": [{"date": "2026-05-12", "label": "gerencia de memoria"}]},
            {"id": "bloco-12", "period_start": "2026-06-02",
             "topic_text": "enunciado gerencia",
             "sessions": [{"date": "2026-06-02", "label": "enunciado do tp2"}]},
        ]
        return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})

    def test_concordancia_discriminante_ancora_alta(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        d = disambiguate({"title": "24.03 Escalonamento de Processos"},
                         ["bloco-03"], self._ctx(), provider="data")
        assert (d.block_ref, d.band, d.flag) == ("bloco-03", "alta", False)

    def test_token_boilerplate_nao_da_alta(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # caso real 02.06: material de I/O postado no dia do enunciado TP2.
        # "gerencia" casa bloco-12 mas tem df=3 -> NÃO discriminante -> flag.
        d = disambiguate({"title": "02.06 Lâminas Gerência de I O"},
                         ["bloco-12"], self._ctx(), provider="data")
        assert d.block_ref == "bloco-12"       # ancora no melhor (invariante)
        assert d.flag is True
        assert d.band != "alta"

    def test_silencio_lexical_flagado(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        d = disambiguate({"title": "09.04 Lâminas Semáforos"},
                         ["bloco-12"], self._ctx(), provider="data")
        assert (d.flag, d.band != "alta") == (True, True)

    def test_provider_default_preserva_fast_path(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # P1/P2 (manual/labels ou default ""): janela-1 segue alta/1.0 (FASE 0/1)
        d = disambiguate({"title": "qualquer"}, ["bloco-12"], self._ctx())
        assert (d.band, d.conf, d.flag) == ("alta", 1.0, False)

    def test_janela1_topic_concordante_ancora_alta(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # P4 janela-1: mesmo gate do P3 — token discriminante global => alta
        d = disambiguate({"title": "Escalonamento de Processos"},
                         ["bloco-03"], self._ctx(), provider="topic")
        assert (d.block_ref, d.band, d.flag) == ("bloco-03", "alta", False)

    def test_janela1_topic_sem_discriminante_flagada(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # P4 janela-1 sem concordância específica: ancora + flag, nunca alta
        # cega (simetria com "data"; fecha o buraco Halteproblem mascarado
        # por pino manual no TCC).
        d = disambiguate({"title": "Material genérico sobre gerência"},
                         ["bloco-12"], self._ctx(), provider="topic")
        assert d.block_ref == "bloco-12"
        assert d.flag is True
        assert d.band != "alta"


def test_evidencia_exclusiva_sem_competicao_e_confiante():
    """D4 relido (2026-08-21): `s2 > 0` exigia "competicao real" e confundia
    SEM COMPETICAO com SEM EVIDENCIA. Quando so um bloco da janela casa algum
    token do material (s1>0, s2=0) e ha token discriminante, e a evidencia
    lexica mais exclusiva possivel. Medido nos 5 cursos (87 janelas >= 2):
    nesse balde o lexico acerta 21/23, o LLM 22/23 — mesma acuracia total
    (73/87) com 22 votos de LLM a menos."""
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "logica hoare triplas", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "modelos kripke temporal", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    d = disambiguate({"title": "exercicios triplas de hoare"}, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"
    assert d.flag is False and d.band == "alta"


def test_silencio_total_continua_flagado():
    """s1 = 0 (nenhum token casa bloco nenhum) NAO e evidencia: segue flag."""
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01", "topic_text": "hoare", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08", "topic_text": "kripke", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    d = disambiguate({"title": "material qualquer"}, ["bloco-A", "bloco-B"], ctx)
    assert d.flag is True and d.band != "alta"


def test_boilerplate_de_curso_nao_e_token():
    """"Apresentacao da DISCIPLINA", "ESTUDO de CASO" aparecem em todo curso e
    puxavam o material para o bloco-01 (MF `introducao`, ES2 `azure`)."""
    toks = entry_tokens({"title": "Estudo de caso: apresentacao da disciplina"})
    assert not ({"estudo", "caso", "disciplina"} & toks)


def test_trabalho_nao_e_token_de_assunto():
    """ES2 `kubernetes` ia sozinho para "Entrega trabalho final" pelo token
    "trabalho" — nome da categoria, nao do assunto."""
    assert "trabalho" not in entry_tokens({"title": "Kubernetes trabalho final"})


# R3 titulo-topico (2026-08-26): titulo/rotulo contem TODOS os tokens do topico de
# exatamente 1 bloco da janela -> escolha confiante, sem voto.
def _ctx_hoare():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-10", "kind": "class", "period_start": "2026-04-27", "primary_topic_label": "Lógica de Hoare",
                 "sessions": [{"date": "2026-04-27", "label": "logica de hoare aula"}]},
                {"id": "bloco-11", "kind": "deliverable", "period_start": "2026-05-06", "primary_topic_label": "Correção Parcial e Total",
                 "sessions": [{"date": "2026-05-06", "label": "correcao parcial e total"}]}],
        card_block_map={}, lessons_index={})


def test_titulo_topico_escolhe_bloco_nomeado_sem_voto():
    e = {"id": "logicadehoare2", "title": "LogicaDeHoare2", "moodle_label": "Lógica de Hoare (parte 2)"}
    d = disambiguate(e, ["bloco-10", "bloco-11"], _ctx_hoare(), "correcao parcial total invariantes terminacao " * 20)
    assert d.block_ref == "bloco-10" and d.method == "titulo-topico" and d.flag is False


def test_titulo_topico_ambiguo_cai_no_desempate():
    e = {"id": "x", "title": "Lógica de Hoare: correção parcial e total"}
    d = disambiguate(e, ["bloco-10", "bloco-11"], _ctx_hoare(), "")
    assert d.method != "titulo-topico"


def test_titulo_topico_ignora_topico_so_de_enchimento():
    ctx = MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01", "kind": "class", "period_start": "2026-03-02", "primary_topic_label": "Introdução", "sessions": []},
                {"id": "bloco-02", "kind": "class", "period_start": "2026-03-09", "primary_topic_label": "Processos", "sessions": []}],
        card_block_map={}, lessons_index={})
    d = disambiguate({"id": "y", "title": "Introdução aos sistemas"}, ["bloco-01", "bloco-02"], ctx, "")
    assert d.method != "titulo-topico"
