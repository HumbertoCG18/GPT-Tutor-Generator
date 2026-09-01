from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02", "topic_text": "introducao"},
    {"id": "bloco-02", "period_start": "2026-03-04", "topic_text": "logica predicados"},
    {"id": "bloco-05", "period_start": "2026-04-06", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-06", "label": "inducao estrutural"}]},
    {"id": "bloco-06", "period_start": "2026-04-13", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-13", "label": "inducao arvores"}]},
]
CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_bibliografia_entra_no_motor_e_tde_continua_fora():
    """B-5 (2026-08-21): bibliografia/references/cronograma/apoio passam pela
    cascata — o gold da bloco a elas e 12/14 em producao ja tinham pino. Sem
    voter e sem janela o resultado e None (funil), como antes; a diferenca e
    que um card datado ou o llm-funil agora podem decidir. TDE segue fora."""
    assert is_out_of_disamb_scope({"category": "bibliografia"}) is False
    assert is_out_of_disamb_scope({"category": "cronograma"}) is False
    assert is_out_of_disamb_scope({"category": "bibliografia", "source_section": "TDE 3"}) is True
    eng = AnchorEngine()
    assert eng.resolve({"category": "bibliografia", "source_section": "Bibliografia-Livros"}, _ctx()) is None


def test_d6_trabalho_prova_tde_out_of_disambiguator():
    assert is_out_of_disamb_scope({"category": "trabalhos"}) is True
    assert is_out_of_disamb_scope({"category": "provas"}) is True
    assert is_out_of_disamb_scope({"source_section": "TDE 3 - entrega"}) is True
    assert is_out_of_disamb_scope({"category": "material"}) is False


def test_no_window_returns_none_funil():
    eng = AnchorEngine()
    assert eng.resolve({"category": "material", "source_section": "Card Sem Janela"}, _ctx()) is None


def test_multiblock_window_runs_disambiguator_and_sets_provider():
    eng = AnchorEngine()
    d = eng.resolve(
        {"category": "material", "source_section": "Provas por Indução",
         "title": "Prova por indução em árvores"},
        _ctx(),
    )
    assert d is not None
    assert d.block_ref == "bloco-06"      # session-label 'arvores' discrimina
    assert d.provider == "manual"
    assert d.method == "disamb"


def test_janela_com_ref_fantasma_nao_vira_confianca():
    """Ref obsoleto no card_block_map (drift) não pode virar confiança "alta"
    sem evidência de token. Janela com 2 refs onde só 1 resolve deve cair no
    scoring normal (1 bloco resolvível => s2=0 => flagado/media), não no
    fast-path janela-1. Janela 100% fantasma (nenhum ref resolve) => funil."""
    ctx = MotorContext.from_artifacts(
        blocks=BLOCKS,
        card_block_map={
            **CBM,
            "Janela Fantasma": {"block_ids": ["bloco-05", "bloco-fantasma"], "source": "manual"},
            "Janela Toda Fantasma": {"block_ids": ["bloco-x", "bloco-y"], "source": "manual"},
        },
        lessons_index={},
    )
    eng = AnchorEngine()

    d = eng.resolve(
        {"category": "material", "source_section": "Janela Fantasma",
         "title": "Prova por indução"},
        ctx,
    )
    assert d is not None
    assert d.band != "alta"
    assert d.flag is True

    assert eng.resolve(
        {"category": "material", "source_section": "Janela Toda Fantasma",
         "title": "Qualquer coisa"},
        ctx,
    ) is None


# TIER 3 Tests (FASE 3 Task 4)
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor import anchor_engine as ae


class _FakeVoter:
    def __init__(self, answer):
        self.answer = answer
        self.seen = []
        self.calls = 0

    def vote(self, entry, window, ctx, markdown=""):
        self.calls += 1
        self.seen.append(str(entry.get("id")))
        return self.answer


def _tier3_ctx():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01"}, {"id": "bloco-02"}],
        card_block_map={}, lessons_index={})


def _stub_cascade(monkeypatch, *, flag: bool, band: str = "baixa"):
    monkeypatch.setattr(ae, "resolve_window",
                        lambda e, c: (["bloco-01", "bloco-02"], "topic"))
    monkeypatch.setattr(
        ae, "disambiguate",
        lambda e, w, c, m, provider="": AnchorDecision(
            block_ref="bloco-01", conf=0.9 if band == "alta" else 0.2,
            band=band, flag=flag, window=list(w)))


def test_tier3_flagged_voto_valido_ancora_media(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-02"
    assert d.band == "media" and d.flag is False
    assert d.provider == "llm" and d.method == "llm"
    assert voter.seen == ["e1"]


def test_tier3_voto_none_mantem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d = ae.AnchorEngine(voter=_FakeVoter(None)).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-01" and d.flag is True and d.provider == "topic"


def test_tier3_sem_voter_byte_identico(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d0 = ae.AnchorEngine().resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d0.block_ref == "bloco-01" and d0.flag is True and d0.band == "baixa"


def test_tier3_nao_flagado_fora_de_serie_nao_vota(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == [] and d.block_ref == "bloco-01" and d.band == "alta"


def test_tier3_membro_de_serie_vota_mesmo_sem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter, series_ids={"e1"}).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == ["e1"]
    assert d.block_ref == "bloco-02" and d.band == "media" and d.provider == "llm"


def _ctx_janela_unica():
    return MotorContext.from_artifacts(
        blocks=BLOCKS,
        card_block_map={**CBM, "aula unica": {"block_ids": ["bloco-01"], "source": "manual"}},
        lessons_index={},
    )


def test_janela_1_nao_entra_no_voto_mesmo_em_serie():
    """D4×janela-1 (decisão D-A, 10/07): voto com 1 candidato desflaga sem
    informação nova. |janela|==1 fica FORA do escopo do voter; a decisão
    determinística (e o FLAG, se houver) sobrevive pra fila humana."""
    ctx = _ctx_janela_unica()          # card 'aula unica' -> ['bloco-01']
    entry = {"id": "e1", "title": "Aula 3", "source_section": "aula unica",
             "category": "materiais"}
    voter = _FakeVoter("bloco-01")
    eng = AnchorEngine(voter=voter, series_ids={"e1"})
    d = eng.resolve(entry, ctx)
    assert d is not None and d.block_ref
    assert voter.calls == 0            # janela-1: voter NUNCA chamado
    assert d.provider != "llm" and d.method != "llm"


# B-4 (2026-08-21): llm-funil — sem janela, o LLM vota com janela = blocos do curso.
def _funil_ctx():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01"}, {"id": "bloco-02"}, {"id": "bloco-03"}],
        card_block_map={}, lessons_index={})


def test_llm_funil_vota_com_janela_de_todos_os_blocos():
    """Medido 2026-08-21: funil concept-fused 6/26 -> LLM janela=tudo 13/26,
    0 regressoes. band media + flag=True: 50% e honesto, fica na fila humana."""
    voter = _FakeVoter("bloco-03")
    d = ae.AnchorEngine(voter=voter).resolve_funnel(
        {"id": "e1", "category": "material-de-aula"}, _funil_ctx())
    assert d.block_ref == "bloco-03"
    assert d.method == "llm-funil" and d.provider == "llm-funil"
    assert d.band == "media" and d.flag is True
    assert d.window == ["bloco-01", "bloco-02", "bloco-03"]
    assert voter.seen == ["e1"]


def test_llm_funil_sem_voter_ou_sem_voto_devolve_none():
    ctx = _funil_ctx()
    assert ae.AnchorEngine(voter=None).resolve_funnel({"id": "e1"}, ctx) is None
    assert ae.AnchorEngine(voter=_FakeVoter(None)).resolve_funnel({"id": "e1"}, ctx) is None


def test_resolve_sem_janela_cai_no_llm_funil(monkeypatch):
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: ([], ""))
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _funil_ctx())
    assert d is not None and d.method == "llm-funil" and d.block_ref == "bloco-02"


# B-6 (2026-08-21): referencia sem card -> primeiro bloco overview/class.
def test_referencia_sem_card_vai_para_o_primeiro_bloco():
    """Convencao dos pinos manuais (aws/archive/o-que-e-IA/ia-responsavel, 4/5
    no gold). IA e SO tem kind=overview no bloco-01 (plano/apresentacao)."""
    ctx = MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01", "kind": "overview", "period_start": "2026-03-02"},
                {"id": "bloco-02", "kind": "class", "period_start": "2026-03-04"}],
        card_block_map={}, lessons_index={})
    d = ae.resolve_generic_reference({"category": "bibliografia", "title": "AFP"}, ctx)
    assert d is not None and d.block_ref == "bloco-01"
    assert d.method == "ref-generica" and d.flag is False
    # com card segue a cascata normal (card datado do IA resolve `artigo` sozinho)
    assert ae.resolve_generic_reference(
        {"category": "bibliografia", "source_section": "Semana 8 - 20.04 a 24.04"}, ctx) is None
    assert ae.resolve_generic_reference({"category": "material-de-aula"}, ctx) is None


def test_trabalho_com_janela_multipla_nao_usa_token_de_conteudo():
    """lexical=False (trabalhos/provas): enunciado descreve o CONTEUDO cobrado,
    nao a entrega. TCC `t1-enunciado`: tokens "minimizacao/primitivas" casam a
    aula 03; a entrega e o bloco-04. Com janela > 1 so o voto sobre a janela
    decide; sem voter, None (funil/limpo). Janela-1 segue estrutural."""
    ctx = MotorContext.from_artifacts(
        blocks=[{"id": "bloco-03", "period_start": "2026-03-11",
                 "topic_text": "funcoes recursivas primitivas minimizacao", "sessions": []},
                {"id": "bloco-04", "period_start": "2026-03-20", "kind": "deliverable",
                 "topic_text": "entrega", "sessions": []}],
        card_block_map={"Semana 3 - Trabalho T1": {"source": "manual", "block_ids": ["bloco-03", "bloco-04"]}},
        lessons_index={})
    entry = {"id": "t1", "category": "trabalhos", "title": "T1 - Enunciado",
             "source_section": "Semana 3 - Trabalho T1"}
    md = "minimizacao de funcoes recursivas primitivas e parciais"
    # com token de conteudo, o lexico iria para bloco-03 (errado para uma entrega)
    assert ae.AnchorEngine(voter=None).resolve_unscoped(entry, ctx, md, lexical=True).block_ref == "bloco-03"
    assert ae.AnchorEngine(voter=None).resolve_unscoped(entry, ctx, md, lexical=False) is None
    voter = _FakeVoter("bloco-04")
    d = ae.AnchorEngine(voter=voter).resolve_unscoped(entry, ctx, md, lexical=False)
    assert d.block_ref == "bloco-04" and d.method == "llm" and d.window == ["bloco-03", "bloco-04"]


# prep-prova (2026-08-25): "lista/revisao pN" sem janela -> ultimo bloco hospedavel
# antes da N-esima prova PRINCIPAL (substituicao/entrega nao contam; suspended,
# feriado, atendimento e a propria prova nao hospedam). Gold: 7/7 nos 5 cursos.
def _ctx_provas():
    # Contrato real (dump 01/09 dos 6 cursos): bloco de prova principal tem
    # topic_text VAZIO e o rotulo "prova pN" na LABEL da sessao; PS carrega
    # "substituicao"; G2 "prova g2"; resquicio LightGrey vira assessment com
    # label "aula" (SO-27/IA-24) e NAO conta como principal (D1).
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01", "kind": "class", "period_start": "2026-03-02"},
                {"id": "bloco-02", "kind": "review", "period_start": "2026-04-15"},
                {"id": "bloco-03", "kind": "suspended", "period_start": "2026-04-20", "topic_text": "suspensao"},
                {"id": "bloco-04", "kind": "assessment", "period_start": "2026-04-22",
                 "sessions": [{"label": "prova p1 prova"}]},
                {"id": "bloco-05", "kind": "class", "period_start": "2026-06-16"},
                {"id": "bloco-06", "kind": "office_hours", "period_start": "2026-06-23"},
                {"id": "bloco-07", "kind": "assessment", "period_start": "2026-06-25",
                 "sessions": [{"label": "prova p2 entrega do t2 prova"}]},
                {"id": "bloco-08", "kind": "assessment", "period_start": "2026-06-30", "topic_text": "substituicao"},
                {"id": "bloco-09", "kind": "assessment", "period_start": "2026-07-07",
                 "sessions": [{"label": "prova g2 prova de g2"}]},
                {"id": "bloco-10", "kind": "assessment", "period_start": "2026-07-14",
                 "sessions": [{"label": "aula"}]}],
        card_block_map={}, lessons_index={})


def test_prep_prova_p1_pula_suspended_e_para_na_revisao():
    d = ae.resolve_exam_prep({"id": "revisao-p1", "category": "listas"}, _ctx_provas())
    assert d is not None and d.block_ref == "bloco-02" and d.method == "prep-prova"


def test_prep_prova_p2_ignora_substituicao_e_atendimento():
    d = ae.resolve_exam_prep({"id": "lista-exercicios-p2", "category": "listas",
                              "source_section": "Informações Gerais"}, _ctx_provas())
    assert d is not None and d.block_ref == "bloco-05"


def test_prep_prova_sem_cue_ou_prova_inexistente_devolve_none():
    assert ae.resolve_exam_prep({"id": "exercicios", "category": "listas"}, _ctx_provas()) is None
    assert ae.resolve_exam_prep({"id": "lista-p3", "category": "listas"}, _ctx_provas()) is None


def test_resolve_sem_janela_tenta_prep_prova_antes_do_funil(monkeypatch):
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: ([], ""))
    voter = _FakeVoter("bloco-01")     # o funil votaria 01; a regra decide antes
    d = ae.AnchorEngine(voter=voter).resolve({"id": "lista-p1", "category": "listas"}, _ctx_provas())
    assert d is not None and d.method == "prep-prova" and d.block_ref == "bloco-02"


def test_prep_prova_nao_se_aplica_a_propria_prova(monkeypatch):
    """provas/trabalhos sem due chegam aqui com lexical=False: a prova antiga do
    IA (`prova-1-2024-02`, gold no TDE) nao e preparacao — cai no funil."""
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: ([], ""))
    d = ae.AnchorEngine(voter=None).resolve_unscoped(
        {"id": "prova-1-2024-02", "category": "provas"}, _ctx_provas(), lexical=False)
    assert d is None


def test_provider_labels_resolve_datas_contra_os_blocos_atuais():
    """2026-08-25: o window_provider lia block_ids do card map direto; com o
    split do ES2 bloco-11 a aula nova de 26/06 ficava fora da janela do card
    "DevOps" mesmo com a data no rotulo. Datas mandam; block_ids e cache."""
    from src.builder.routing.motor.window_provider import provider_labels
    ctx = MotorContext.from_artifacts(
        blocks=[{"id": "bloco-11", "block_uuid": "u-11", "kind": "suspended", "period_start": "2026-06-19", "period_end": "2026-06-19"},
                {"id": "bloco-12", "block_uuid": "u-12", "kind": "class", "period_start": "2026-06-26", "period_end": "2026-06-26"},
                {"id": "bloco-13", "block_uuid": "u-13", "kind": "assessment", "period_start": "2026-07-03", "period_end": "2026-07-03"}],
        card_block_map={"DevOps": {"source": "labels", "block_ids": ["u-11", "u-13"], "dates": ["2026-06-26", "2026-07-03"]}},
        lessons_index={})
    assert provider_labels({"id": "devops", "source_section": "DevOps"}, ctx) == ["u-12", "u-13"]


# Balde B (2026-08-26): janela INDIRETA (topic/ordinal) + cue de preparacao de
# prova -> prep-prova decide antes do desempate/voto. MF revisao-p1: card por
# topico dava [05, 06] e o LLM votava 05 (gold 07); TCC aula-16: ordinal 19 (gold 16).
def _ctx_prep_janela():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-05", "kind": "class", "period_start": "2026-03-30", "topic_text": "inducao arvores"},
                {"id": "bloco-06", "kind": "class", "period_start": "2026-04-06", "topic_text": "isabelle"},
                {"id": "bloco-07", "kind": "review", "period_start": "2026-04-15"},
                {"id": "bloco-09", "kind": "assessment", "period_start": "2026-04-22",
                 "sessions": [{"label": "prova p1 prova"}]}],
        card_block_map={}, lessons_index={})


def test_prep_prova_vence_janela_por_topico(monkeypatch):
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: (["bloco-05", "bloco-06"], "topic"))
    entry = {"id": "revisao-p1", "category": "listas", "title": "Exercicios para P1",
             "source_section": "Exercícios de Revisão para Prova"}
    d = ae.AnchorEngine(voter=_FakeVoter("bloco-05")).resolve_unscoped(entry, _ctx_prep_janela(), "inducao")
    assert d.block_ref == "bloco-07" and d.method == "prep-prova"


def test_prep_prova_nao_sobrepoe_card_manual_ou_datado(monkeypatch):
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: (["bloco-05"], "labels"))
    entry = {"id": "revisao-p1", "category": "listas", "source_section": "Semana 5"}
    d = ae.AnchorEngine(voter=None).resolve_unscoped(entry, _ctx_prep_janela(), "")
    assert d.block_ref == "bloco-05" and d.method == "janela-1"


def test_gabarito_da_revisao_e_preparacao_mesmo_com_categoria_provas(monkeypatch):
    monkeypatch.setattr(ae, "resolve_window", lambda e, c: (["bloco-05", "bloco-06"], "topic"))
    gab = {"id": "revisao-p1-gabarito", "category": "provas", "title": "Respostas",
           "source_section": "Exercícios de Revisão para Prova"}
    assert ae.is_exam_prep_material(gab) is True
    d = ae.AnchorEngine(voter=_FakeVoter("bloco-05")).resolve_unscoped(gab, _ctx_prep_janela(), "", lexical=False)
    assert d.block_ref == "bloco-07" and d.method == "prep-prova"


def test_prova_antiga_nao_e_material_de_preparacao():
    assert ae.is_exam_prep_material({"id": "prova-1-2024-02", "category": "provas",
                                     "title": "Prova 1 2024/02", "source_section": "TDE"}) is False


def test_is_main_exam_block_d1_padroes_reais():
    """D1: rotulo P<n>/'Prova N' decide; PS/G2/PF/mudo nunca. Padroes copiados
    do dump real dos 6 cursos (01/09)."""
    def bloco(label, kind="assessment", topic=""):
        return {"kind": kind, "topic_text": topic, "sessions": [{"label": label}]}
    assert ae.is_main_exam_block(bloco("prova p1 prova"))
    assert ae.is_main_exam_block(bloco("p1 prova"))                       # SO
    assert ae.is_main_exam_block(bloco("prova 1 prova"))                  # IA
    assert ae.is_main_exam_block(bloco("prova p2 entrega do t2 prova", topic="entrega"))  # MF/ES2: entrega junto NAO derruba
    assert not ae.is_main_exam_block(bloco("prova g2 prova de g2"))
    assert not ae.is_main_exam_block(bloco("prova ps prova de substituicao", topic="substituicao"))
    assert not ae.is_main_exam_block(bloco("aula"))                        # SO-27/IA-24: mudo
    assert not ae.is_main_exam_block(bloco("atendimento a duvidas aula"))  # TCC-34
    assert not ae.is_main_exam_block(bloco("prova p1 prova", kind="review"))
    assert not ae.is_main_exam_block(bloco("prova final"))
    assert not ae.is_main_exam_block(bloco("apresentacao tp1 parte 1"))    # tp1 nao e p1


def test_prep_prova_p2_ancora_antes_da_p2_real_nao_da_g2():
    """Antes do D1 a P2 do MF ('entrega' no topic) saia das mains e a G2 (topic
    vazio) entrava — a prep-P2 ancorava na G2."""
    d = ae.resolve_exam_prep({"id": "lista-exercicios-p2", "category": "listas",
                              "source_section": "Informações Gerais"}, _ctx_provas())
    assert d is not None and d.block_ref == "bloco-05"
