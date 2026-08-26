from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import (
    provider_manual,
    provider_labels,
    provider_topic,
    resolve_window,
)
from src.builder.timeline.card_block import normalized_card_map

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02"},
    {"id": "bloco-02", "period_start": "2026-03-04"},
    {"id": "bloco-05", "period_start": "2026-04-06"},
    {"id": "bloco-06", "period_start": "2026-04-13"},
]

CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Introdução a Métodos Formais": {
        "block_ids": ["bloco-01", "bloco-02"], "source": "labels",
    },
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_p1_manual_returns_window_only_for_manual_source():
    ctx = _ctx()
    assert provider_manual({"source_section": "Provas por Indução"}, ctx) == ["bloco-05", "bloco-06"]
    # labels-source NÃO é P1:
    assert provider_manual({"source_section": "Introdução a Métodos Formais"}, ctx) == []


def test_p2_labels_returns_window_only_for_labels_source():
    ctx = _ctx()
    assert provider_labels({"source_section": "Introdução a Métodos Formais"}, ctx) == ["bloco-01", "bloco-02"]
    assert provider_labels({"source_section": "Provas por Indução"}, ctx) == []


def test_cascade_prefers_manual_then_labels():
    ctx = _ctx()
    win, prov = resolve_window({"source_section": "Provas por Indução"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")
    win, prov = resolve_window({"source_section": "Introdução a Métodos Formais"}, ctx)
    assert (win, prov) == (["bloco-01", "bloco-02"], "labels")


def test_empty_or_missing_card_yields_no_window():
    ctx = _ctx()
    assert resolve_window({"source_section": "Bibliografia-Livros"}, ctx) == ([], "")
    assert resolve_window({"source_section": "Card Inexistente"}, ctx) == ([], "")
    assert resolve_window({"source_section": ""}, ctx) == ([], "")


def test_card_lookup_is_accent_and_case_insensitive():
    ctx = _ctx()
    # "provas por inducao" (sem acento, minúsculo) casa "Provas por Indução"
    win, prov = resolve_window({"source_section": "provas por inducao"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")


def test_malformed_card_value_yields_no_window():
    """Card quebrado (valor não-dict) degrada para funil, não AttributeError."""
    malformed_cbm = {
        "Card Quebrado": ["bloco-01"],  # Lista em vez de dict
        "String Card": "Introdução",    # String em vez de dict
        "Valid Card": {"block_ids": ["bloco-02"], "source": "manual"},
    }
    blocks = [
        {"id": "bloco-01", "period_start": "2026-03-02"},
        {"id": "bloco-02", "period_start": "2026-03-04"},
    ]
    ctx = MotorContext.from_artifacts(
        blocks=blocks,
        card_block_map=malformed_cbm,
        lessons_index={}
    )
    # Malformed cards retornam janela vazia (funil) sem crash:
    assert resolve_window({"source_section": "Card Quebrado"}, ctx) == ([], "")
    assert resolve_window({"source_section": "String Card"}, ctx) == ([], "")
    # Card válido funciona normalmente:
    assert resolve_window({"source_section": "Valid Card"}, ctx) == (["bloco-02"], "manual")


def test_card_entry_usa_normalizacao_unica_do_card_block():
    # a MESMA chave com acento/caixa divergente resolve nos dois caminhos
    cbm = {"Verificação de Programas": {"source": "labels", "block_ids": ["bloco-10"]}}
    ctx = MotorContext.from_artifacts(blocks=[], card_block_map=cbm, lessons_index={})
    entry = {"source_section": "verificacao de programas"}
    win, provider = resolve_window(entry, ctx)
    assert win == ["bloco-10"] and provider == "labels"
    # e o índice público de card_block dá a mesma visão normalizada
    assert "verificacao de programas" in normalized_card_map(cbm)


def _ctx_com_datas():
    from src.builder.routing.motor.contracts import MotorContext
    blocks = [
        {"id": "bloco-01", "period_start": "2026-03-03",
         "sessions": [{"date": "2026-03-03", "label": "apresentacao"}]},
        {"id": "bloco-02", "period_start": "2026-03-10",
         "sessions": [{"date": "2026-03-10", "label": "processos"},
                      {"date": "2026-03-12", "label": "threads"}]},
    ]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})


class TestProviderDate:
    def test_data_casa_sessao(self):
        from src.builder.routing.motor.window_provider import provider_date
        win = provider_date({"title": "10.03 Processos"}, _ctx_com_datas())
        assert win == ["bloco-02"]

    def test_data_sem_sessao_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_date
        # 02.05: data válida mas nenhuma sessão nesse dia -> [] (funil/próximo provider)
        assert provider_date({"title": "02.05 Segmentação"}, _ctx_com_datas()) == []

    def test_sem_data_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_date
        assert provider_date({"title": "Plano de Ensino"}, _ctx_com_datas()) == []

    def test_cascata_p3_depois_de_labels(self):
        from src.builder.routing.motor.window_provider import resolve_window
        win, provider = resolve_window({"title": "10.03 Processos"}, _ctx_com_datas())
        assert (win, provider) == (["bloco-02"], "data")

    def test_card_manual_vence_data(self):
        from src.builder.routing.motor.contracts import MotorContext
        from src.builder.routing.motor.window_provider import resolve_window
        ctx = MotorContext.from_artifacts(
            blocks=_ctx_com_datas().blocks,
            card_block_map={"Card X": {"source": "manual", "block_ids": ["bloco-01"]}},
            lessons_index={},
        )
        win, provider = resolve_window(
            {"title": "10.03 Processos", "source_section": "Card X"}, ctx)
        assert (win, provider) == (["bloco-01"], "manual")


class TestExtractDateInName:
    def test_title_com_ponto(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "12.03 Processos"}) == (12, 3)

    def test_title_com_espaco(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "14 04 Troca de Mensagens"}) == (14, 4)

    def test_mes_invalido_rejeitado(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        # "Integer Programming 00.01" -> dd=00 inválido; não é data
        assert extract_date_in_name({"title": "Integer Programming 00.01"}) is None
        assert extract_date_in_name({"title": "25.13 Coisa"}) is None

    def test_data_no_meio_do_titulo_nao_conta(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        # convenção SO = PREFIXO; data no meio é ruído (CS 4244 etc.)
        assert extract_date_in_name({"title": "Aula sobre 12.03 Processos"}) is None

    def test_fallback_moodle_label_e_source_path(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name(
            {"title": "Processos", "moodle_label": {"text": "21.05 Paginação"}}
        ) == (21, 5)
        assert extract_date_in_name(
            {"title": "x", "source_path": r"C:\stash\SO\02.06 Interrupção.pdf"}
        ) == (2, 6)

    def test_sem_data(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "Plano de Ensino"}) is None
        assert extract_date_in_name({}) is None


class TestProviderTopic:
    @staticmethod
    def _ctx():
        from src.builder.routing.motor.contracts import MotorContext
        blocks = [
            {"id": "bloco-16", "period_start": "2026-05-06", "topic_text": "",
             "sessions": [{"date": "2026-05-06", "label": "prova p1 prova"}]},
            {"id": "bloco-21", "period_start": "2026-05-27",
             "topic_text": "reducoes polinomiais",
             "sessions": [{"date": "2026-05-27", "label": "reducoes np"}]},
            {"id": "bloco-22", "period_start": "2026-06-03",
             "topic_text": "complexidade tempo classe hard reducao problemas pspace complete",
             "sessions": [{"date": "2026-06-03", "label": "complexidade de tempo classe np hard"}]},
        ]
        return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})

    def test_topico_com_stem_prefix(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # caso real que falhava cru: "completude" ~ "complexidade"/"complete"
        win = provider_topic({"source_section": "Semana 12 - NP-completude"}, self._ctx())
        assert "bloco-22" in win

    def test_ordinal_nunca_vira_janela(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # F-TCC: card só-ordinal (sem tópico) NÃO rende janela por week-math
        assert provider_topic({"source_section": "Semana 5 -"}, self._ctx()) == []
        assert provider_topic({"source_section": "Semana 5"}, self._ctx()) == []

    def test_topico_so_digito_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # regex casa, mas tópico só-dígito não gera token útil -> sem janela
        assert provider_topic({"source_section": "Semana 5 - 2026"}, self._ctx()) == []

    def test_card_sem_semana_usa_o_nome_inteiro_como_topico(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # 2026-08-25: o prefixo "Semana N -" era vicio do formato do IA. Card
        # de topico puro casa as sessoes; nome sem eco em bloco nenhum -> [].
        assert provider_topic(
            {"source_section": "Verificação de Programas"}, self._ctx()) == []
        assert provider_topic({"source_section": "Reduções"}, self._ctx()) == ["bloco-21"]

    def test_card_threads_do_so_vira_janela_1(self):
        """SO: 3 `exemplo-threads-em-c` no card "Threads" iam ao funil (LLM
        errava); o bloco das aulas de threads tem "threads" nas sessoes."""
        from src.builder.routing.motor.window_provider import provider_topic
        ctx = MotorContext.from_artifacts(blocks=[
            {"id": "bloco-03", "period_start": "2026-03-10", "topic_text": "processos chamadas sistema",
             "sessions": [{"date": "2026-03-10", "label": "estruturas processos chamadas de sistema aula"}]},
            {"id": "bloco-04", "period_start": "2026-03-19", "topic_text": "escalonamento threads exclusao mutua",
             "sessions": [{"date": "2026-03-26", "label": "gerencia do processador threads e exclusao mutua aula"}]},
        ], card_block_map={}, lessons_index={})
        assert provider_topic({"source_section": "Threads"}, ctx) == ["bloco-04"]

    def test_topico_de_revisao_casa_bloco_de_prova(self):
        from src.builder.routing.motor.window_provider import provider_topic
        win = provider_topic({"source_section": "Semana 10 - Revisão para P1 e Prova P1"},
                             self._ctx())
        assert "bloco-16" in win

    def test_cascata_topic_por_ultimo(self):
        """Ordem por CONFIABILIDADE. `ordinal` (P3b, "Aula N" -> N-esimo
        encontro) entra depois de DATA — data aponta o dia exato — e antes de
        TOPICO, que casa por stems e e o mais fraco."""
        from src.builder.routing.motor.window_provider import resolve_window, _CASCADE
        assert [name for _, name in _CASCADE] == ["manual", "labels", "data", "ordinal", "topic"]

    def test_rotulo_taxonomia_rica_nao_vaza_prova_sem_sinal_forte(self):
        """C6 (diagnóstico 2026-08-06, re-flip TCC tentativa 4): bloco de AULA
        com primary_topic_label "Prova da Indecidibilidade..." (rótulo de
        taxonomia rica) vaza "prova" pro stem-matching do P4 via
        block_topic_tokens; sem sinal FORTE de exame no bloco (labels de
        sessão sem P1-4/PF/G2/PS/"prova N"), o bloco NÃO pode casar o card
        de PROVA."""
        blocks = [
            {"id": "bloco-13", "kind": "class", "period_start": "2026-05-06",
             "primary_topic_label": "Prova da Indecidibilidade do Problema da Parada",
             "topic_text": "problema da correspondencia de post",
             "sessions": [{"date": "2026-05-06",
                           "label": "problema da correspondencia de post aula"}]},
        ]
        ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
        win = provider_topic({"source_section": "Semana 10 - Revisão para P1 e Prova P1"}, ctx)
        assert "bloco-13" not in win

    def test_rotulo_taxonomia_rica_casa_prova_com_sinal_forte_no_bloco(self):
        """Controle positivo: sinal forte (aqui "p1") no PRÓPRIO bloco (session
        label) libera o token exam-vocab do lado topic também — o guard só
        filtra quando o bloco não tem sinal forte algum."""
        blocks = [
            {"id": "bloco-13b", "kind": "assessment", "period_start": "2026-05-06",
             "primary_topic_label": "Prova de Corretude do Algoritmo",
             "topic_text": "",
             "sessions": [{"date": "2026-05-06", "label": "prova p1 prova"}]},
        ]
        ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
        win = provider_topic({"source_section": "Semana 10 - Revisão para P1 e Prova P1"}, ctx)
        assert "bloco-13b" in win
