"""Provider due-window (TIER 2 janela-de-prazo, spec 2026-07-22).

Fixtures sintéticas espelham o caso real MF: blocos 15 (2026-06-01..10) e
16 (2026-06-15..29); card TDE com dues por módulo.
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.due_window import tier2_due_scope, resolve_due_window


def _ctx(card_map=None):
    blocks = [
        {"id": "bloco-07", "block_uuid": "u07", "period_start": "2026-04-15", "period_end": "2026-04-15", "topics": ["t"]},
        {"id": "bloco-08", "block_uuid": "u08", "period_start": "2026-04-20", "period_end": "2026-04-20", "topics": ["t"]},
        {"id": "bloco-15", "block_uuid": "u15", "period_start": "2026-06-01", "period_end": "2026-06-10", "topics": ["t"]},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29", "topics": ["t"]},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map or {}, lessons_index={})


TDE = {"TDE Trabalho Discente Efetivo": {"block_ids": [], "source": "labels", "assign_dues": [
    {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"},
    {"name": "Entrega T2", "due": "2026-06-29", "source": "structured"},
]}}


def _t(eid, cat="trabalhos", sec="TDE Trabalho Discente Efetivo", title=None, source_path=""):
    e = {"id": eid, "title": title or eid.replace("-", " "),
         "category": cat, "source_section": sec}
    if source_path:
        e["source_path"] = source_path
    return e


def test_scope_categorias():
    assert tier2_due_scope(_t("t1-2026-1"))
    assert tier2_due_scope(_t("x", cat="provas", sec="Revisao"))
    assert tier2_due_scope(_t("t1-thy", cat="codigo-professor"))
    assert not tier2_due_scope(_t("x", cat="codigo-professor", sec="Aulas"))
    assert not tier2_due_scope(_t("x", cat="bibliografia", sec=""))
    assert not tier2_due_scope(_t("x", cat="pdfs", sec="Materiais"))


def test_containment_stem_match_band_alta():
    d = resolve_due_window(_t("t1-2026-1"), _ctx(TDE))
    assert d.block_ref == "bloco-15" and d.band == "alta" and not d.flag
    assert d.provider == "due-window" and d.method == "due-contain"
    d2 = resolve_due_window(_t("t2-2026-1"), _ctx(TDE))
    assert d2.block_ref == "bloco-16"


def test_companion_codigo_no_tde_casa_pelo_stem():
    d = resolve_due_window(
        _t("t1-2026-1-thy", cat="codigo-professor", title="T1 2026 1"), _ctx(TDE))
    assert d.block_ref == "bloco-15"


def test_sem_due_casado_retorna_none():
    assert resolve_due_window(_t("revisao-p1-gabarito", cat="provas",
                                 sec="Exercicios de Revisao"), _ctx(TDE)) is None
    assert resolve_due_window(_t("t3-2026-1"), _ctx(TDE)) is None  # stem sem modulo


def test_secao_um_due_so_casa_sem_stem():
    cm = {"Trabalho Final": {"assign_dues": [
        {"name": "Entrega", "due": "2026-06-20", "source": "structured"}]}}
    d = resolve_due_window(_t("trabalho-final", sec="Trabalho Final"), _ctx(cm))
    assert d.block_ref == "bloco-16" and d.band == "alta"


def test_straddle_gap_bloco_anterior_media_flag():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-04-17", "source": "structured"}]}}
    d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm))
    assert d.block_ref == "bloco-07" and d.band == "media" and d.flag
    assert d.method == "due-straddle"


def test_due_antes_do_primeiro_bloco_none():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-03-01", "source": "structured"}]}}
    assert resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm)) is None


def test_named_source_band_media():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1 (10/06)", "due": "2026-06-10", "source": "named"}]}}
    d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm))
    assert d.block_ref == "bloco-15" and d.band == "media" and not d.flag


def test_lookup_de_card_fold_caso_acento():
    cm = {"Exercícios de Revisão": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}}
    d = resolve_due_window(_t("t1-x", sec="exercicios de revisao"), _ctx(cm))
    assert d is not None and d.block_ref == "bloco-15"


def test_due_unico_com_stem_conflitante_nao_casa():
    """Guard do review final F5: 1 due na secao mas stems disjuntos (t1 x Entrega T2)
    -> None. Extracao parcial nao pode virar chute com band alta."""
    cm = {"TDE Trabalho Discente Efetivo": {"assign_dues": [
        {"name": "Entrega T2", "due": "2026-06-29", "source": "structured"}]}}
    assert resolve_due_window(_t("t1-2026-1"), _ctx(cm)) is None


def test_empate_de_stem_retorna_none():
    """hits >= 2 -> None (nunca chuta)."""
    cm = {"TDE Trabalho Discente Efetivo": {"assign_dues": [
        {"name": "Entrega T1 parte A", "due": "2026-06-10", "source": "structured"},
        {"name": "Entrega T1 parte B", "due": "2026-06-29", "source": "structured"}]}}
    assert resolve_due_window(_t("t1-2026-1"), _ctx(cm)) is None


def test_tier2_scope_e_subconjunto_do_out_of_scope():
    """Invariante estrutural da cascata (review final F5): toda entry tier2-true
    e out-of-scope-true — flag-ON fora do TIER-2 fica identico ao pre-branch.
    Se este teste quebrar, a ordem pino > tier2 > out-of-scope precisa ser repensada."""
    from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope
    cases = [
        {"category": "trabalhos", "source_section": ""},
        {"category": "provas", "source_section": "Revisao"},
        {"category": "codigo-professor", "source_section": "TDE Trabalho Discente Efetivo"},
        {"category": "codigo-aluno", "source_section": "TDE X"},
    ]
    for e in cases:
        assert tier2_due_scope(e), e
        assert is_out_of_disamb_scope(e), e


TDE_POSICIONAL = {"TDE Trabalho Discente Efetivo": {
    "block_ids": [], "source": "labels",
    "file_dues": {
        "t1_2026_1.pdf": {"due": "2026-05-06", "source": "structured"},
        "t1_2026_1.thy": {"due": "2026-05-06", "source": "structured"},
        "t2_2026_1.pdf": {"due": "2026-07-06", "source": "structured"},
    },
    # dues SEM stem no nome (realidade MF): fallback stem nunca casa aqui
    "assign_dues": [
        {"name": "Sala de entrega", "due": "2026-05-06", "source": "structured"},
        {"name": "Sala de entrega", "due": "2026-07-06", "source": "structured"},
    ],
}}


def _ctx_mf_real(card_map):
    """Blocos do caso real (MF .timeline_index.json, kind conferido em disco):
    11 (kind=class, conteúdo, dia-único 06/05), 16 (kind=class, conteúdo),
    17 (kind=review, topics vazio — revisão), 18 (kind=assessment, topics
    vazio — prova)."""
    blocks = [
        {"id": "bloco-11", "block_uuid": "u11", "period_start": "2026-05-06", "period_end": "2026-05-06", "kind": "class", "topics": ["invariantes"]},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29", "kind": "class", "topics": ["modelos"]},
        {"id": "bloco-17", "block_uuid": "u17", "period_start": "2026-07-01", "period_end": "2026-07-01", "kind": "review", "topics": []},
        {"id": "bloco-18", "block_uuid": "u18", "period_start": "2026-07-06", "period_end": "2026-07-06", "kind": "assessment", "topics": []},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map, lessons_index={})


def test_posicional_casa_por_filename_e_ancora_containment_alta():
    d = resolve_due_window(
        _t("t1-2026-1", source_path="files/t1_2026_1.pdf"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-11" and d.band == "alta" and not d.flag
    assert d.method == "due-contain"


def test_posicional_companion_thy_casa_igual():
    d = resolve_due_window(
        _t("t1-2026-1-thy", cat="codigo-professor", source_path="files/T1_2026_1.thy"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-11"


def test_due_dentro_da_prova_ancora_na_prova():
    # #48: due 2026-07-06 CONTIDO no bloco-18 (assessment) -> ancora NELE, alta,
    # sem flag (antes pulava 18/17 e caia em bloco-16 por straddle). E o caso
    # real do T2 do MF (gold bloco-20 no indice completo).
    d = resolve_due_window(
        _t("t2-2026-1", source_path="files/t2_2026_1.pdf"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-18" and d.band == "alta" and not d.flag
    assert d.method == "due-contain"


def test_sem_file_dues_sem_stem_vai_pro_funil():
    # realidade MF pré-Task1: só assign_dues sem stem -> None (nunca chuta)
    so_assign = {"TDE Trabalho Discente Efetivo": {
        "block_ids": [], "source": "labels",
        "assign_dues": TDE_POSICIONAL["TDE Trabalho Discente Efetivo"]["assign_dues"]}}
    assert resolve_due_window(
        _t("t1-2026-1", source_path="files/t1_2026_1.pdf"),
        _ctx_mf_real(so_assign)) is None


# --- T17: filtro D-H topics(opcional) -> kind(required) --------------------
#
# Tabela kind -> classe, derivada dos 4 .timeline_index.json REAIS disponiveis
# em ~/Documents/GitHub (TCC-Tutor, Metodos-Formais-Tutor,
# Sistemas-Operacionais-Tutor, Engenharia-Software-2-Tutor; IA-Tutor nao tem
# indice — sem motor rodado). Criterio: um kind e NAO-CONTEUDO quando (e so
# quando) blocos REAIS desse kind aparecem hoje com topics=[] (o gate antigo
# ja os pulava). Todo outro kind observado tem topics SEMPRE populado hoje.
#
#   kind            topics=[] / topics!=[] (somado nos 4 cursos)   classe
#   assessment      10 / 5                                          NAO-CONTEUDO
#   review           2 / 1                                          NAO-CONTEUDO
#   class            0 / 45                                         CONTEUDO
#   deliverable       0 / 7                                          CONTEUDO
#   holiday           0 / 7                                          CONTEUDO
#   academic_event    0 / 2                                          CONTEUDO
#   office_hours      0 / 2                                          CONTEUDO
#   overview          0 / 2                                          CONTEUDO
#   results           0 / 1                                          CONTEUDO
#   reserved          0 / 1                                          CONTEUDO
#   suspended         0 / 1                                          CONTEUDO
#   workshop          0 / 1                                          CONTEUDO
#
# assessment/review batem com o uso ja existente em content_taxonomy.py:966,973
# (prova/revisao). Confirmado no MF real: bloco-17 kind=review topics=[],
# bloco-18 kind=assessment topics=[]. Desde #48 so review continua pulado
# (`test_kind_review_continua_fora_do_due_window`); a prova que contem o
# vencimento ancora (`test_due_dentro_da_prova_ancora_na_prova`), via kind.


def _ctx_kind_gate(card_map):
    blocks = [
        {"id": "bloco-20", "block_uuid": "u20", "period_start": "2026-08-01",
         "period_end": "2026-08-05", "kind": "class", "topics": []},
        {"id": "bloco-21", "block_uuid": "u21", "period_start": "2026-08-06",
         "period_end": "2026-08-10", "kind": "assessment", "topics": ["prova final"]},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map, lessons_index={})


def test_kind_class_topics_vazio_ancora():
    """T17 core: curso novo com topics ainda nao populado (rollout) nao pode
    ficar sem ancora so por isso. kind=class e conteudo mesmo com topics=[]."""
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-08-03", "source": "structured"}]}}
    d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx_kind_gate(cm))
    assert d.block_ref == "bloco-20" and d.method == "due-contain"


def test_kind_assessment_que_contem_o_vencimento_ancora():
    """#48 (decisao do usuario 06/09, "bloco de prova hospeda entrega"): o
    vencimento dentro do bloco de prova ancora NELE, nao no ultimo bloco de
    conteudo anterior. Medido nos 7 cursos: MF T2 -> bloco-20 (= gold), 0 perda;
    nenhuma entrada de provas/trabalhos ancorava por straddle antes."""
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T2", "due": "2026-08-08", "source": "structured"}]}}
    d = resolve_due_window(_t("t2-x", sec="TDE"), _ctx_kind_gate(cm))
    assert d.block_ref == "bloco-21" and d.method == "due-contain"
    assert d.band == "alta" and not d.flag


def test_kind_review_continua_fora_do_due_window():
    """review (e os kinds nao academicos) seguem NAO-CONTEUDO: vencimento
    dentro da revisao cai em straddle para o ultimo bloco de conteudo."""
    blocks = [
        {"id": "bloco-20", "block_uuid": "u20", "period_start": "2026-08-01",
         "period_end": "2026-08-05", "kind": "class", "topics": []},
        {"id": "bloco-21", "block_uuid": "u21", "period_start": "2026-08-06",
         "period_end": "2026-08-10", "kind": "review", "topics": ["revisao"]},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={"TDE": {"assign_dues": [
        {"name": "Entrega T2", "due": "2026-08-08", "source": "structured"}]}}, lessons_index={})
    d = resolve_due_window(_t("t2-x", sec="TDE"), ctx)
    assert d.block_ref == "bloco-20" and d.method == "due-straddle" and d.flag


def test_secao_tde_e_reconhecida_com_qualquer_categoria():
    """#48: PDF da secao TDE com categoria `outros` (t1/t2 do MF no pacote) caia
    em fora-de-escopo sem tentar o prazo. `tier2_due_scope` fica como esta (o
    funil continua so para trabalhos/provas); a secao TDE e tratada em apply."""
    from src.builder.routing.motor.due_window import tde_section
    assert tde_section(_t("t2-2026-1", cat="outros"))
    assert tde_section(_t("t2-2026-1", cat="pdfs", sec="TDE"))
    assert not tde_section(_t("x", cat="outros", sec="Aulas"))
    assert not tier2_due_scope(_t("x", cat="outros", sec="TDE Trabalho Discente Efetivo"))


# --- D-H expansao admin-kinds (pendencia pre-rollout ES2/curso novo) --------
#
# NON_ACADEMIC_KINDS (kinds.py) e o conjunto canonico "sem unit/topic/files
# esperados": holiday, suspended, academic_event, office_hours, planning,
# reserved, results. Nenhum deles pode ser "ultimo bloco de conteudo" de uma
# entrega — mesmo quando o corpus atual os traz com topics populado (holiday
# 0/7 na tabela acima). makeup/overview/unknown ficam CONTEUDO (reposicao e
# introducao sao aula; unknown preserva o fail-open documentado).


def _ctx_admin_kind(kind):
    blocks = [
        {"id": "bloco-30", "block_uuid": "u30", "period_start": "2026-09-01",
         "period_end": "2026-09-05", "kind": "class", "topics": ["t"]},
        {"id": "bloco-31", "block_uuid": "u31", "period_start": "2026-09-08",
         "period_end": "2026-09-12", "kind": kind, "topics": ["evento no calendario"]},
    ]
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-09-10", "source": "structured"}]}}
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cm, lessons_index={})


def test_admin_kinds_nunca_ancoram_mesmo_com_topics():
    """Due CONTIDO em bloco administrativo (mesmo topics!=[]) -> pula para o
    ultimo bloco de conteudo anterior (straddle+flag), nunca ancora no admin."""
    for kind in ("holiday", "suspended", "academic_event", "office_hours",
                 "planning", "reserved", "results"):
        d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx_admin_kind(kind))
        assert d is not None, kind
        assert d.block_ref == "bloco-30", (kind, d.block_ref)
        assert d.method == "due-straddle" and d.flag, kind


def test_makeup_e_overview_seguem_conteudo():
    """Reposicao e introducao sao aula: ancoram containment normal."""
    for kind in ("makeup", "overview"):
        d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx_admin_kind(kind))
        assert d is not None and d.block_ref == "bloco-31", (kind, d)
        assert d.method == "due-contain", kind


def test_vencimento_depois_da_prova_faz_straddle_para_a_prova():
    """#48 (revisao Astra): consequencia do contrato — a prova tambem vale como
    "ultimo bloco anterior": vencimento DEPOIS do period_end da prova cai nela por
    straddle (media + flag), nao no bloco de aula anterior."""
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T2", "due": "2026-08-12", "source": "structured"}]}}
    d = resolve_due_window(_t("t2-x", sec="TDE"), _ctx_kind_gate(cm))
    assert d.block_ref == "bloco-21" and d.method == "due-straddle"
    assert d.band == "media" and d.flag
