"""Provider due-window (TIER 2 janela-de-prazo, spec 2026-07-22).

Fixtures sintéticas espelham o caso real MF: blocos 15 (2026-06-01..10) e
16 (2026-06-15..29); card TDE com dues por módulo.
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.due_window import tier2_due_scope, resolve_due_window


def _ctx(card_map=None):
    blocks = [
        {"id": "bloco-07", "block_uuid": "u07", "period_start": "2026-04-15", "period_end": "2026-04-15"},
        {"id": "bloco-08", "block_uuid": "u08", "period_start": "2026-04-20", "period_end": "2026-04-20"},
        {"id": "bloco-15", "block_uuid": "u15", "period_start": "2026-06-01", "period_end": "2026-06-10"},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29"},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map or {}, lessons_index={})


TDE = {"TDE Trabalho Discente Efetivo": {"block_ids": [], "source": "labels", "assign_dues": [
    {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"},
    {"name": "Entrega T2", "due": "2026-06-29", "source": "structured"},
]}}


def _t(eid, cat="trabalhos", sec="TDE Trabalho Discente Efetivo", title=None):
    return {"id": eid, "title": title or eid.replace("-", " "),
            "category": cat, "source_section": sec}


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
