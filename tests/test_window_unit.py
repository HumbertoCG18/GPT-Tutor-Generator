# tests/test_window_unit.py
"""Sessao 6 (2026-09-06): a secao do Moodle que nomeia a unidade ('U2 - ...' ou o titulo da unidade) restringe a
janela de bloco aos blocos dessa unidade. Causa raiz no FR do zero: janela de 6 blocos em 4 unidades pelo provider
'topic', 8 dos 10 avisos de bloco."""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import narrow_window_by_unit, unit_named_by_section


def _ctx():
    blocks = [
        {"id": "bloco-03", "block_uuid": "u3", "period_start": "2026-08-13", "unit_slug": "unidade-02-nivel-de-aplicacao"},
        {"id": "bloco-05", "block_uuid": "u5", "period_start": "2026-08-27", "unit_slug": "unidade-02-nivel-de-aplicacao"},
        {"id": "bloco-06", "block_uuid": "u6", "period_start": "2026-09-03", "unit_slug": "unidade-03-nivel-de-transporte"},
        {"id": "bloco-22", "block_uuid": "u22", "period_start": "2026-11-10", "unit_slug": "unidade-05-nivel-de-enlace"},
    ]
    units = [{"slug": "unidade-01-introducao", "title": "Unidade 01 — Introdução a redes"},
             {"slug": "unidade-02-nivel-de-aplicacao", "title": "Unidade 02 — Nível de aplicação"},
             {"slug": "unidade-03-nivel-de-transporte", "title": "Unidade 03 — Nível de transporte"},
             {"slug": "unidade-05-nivel-de-enlace", "title": "Unidade 05 — Nível de enlace"}]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={}, course_name="FR", units=units)


def test_secao_u2_encolhe_a_janela_para_os_blocos_da_unidade():
    ctx = _ctx()
    e = {"id": "tcp-chat-c", "title": "tcp_chat_c", "source_section": "U2 - Camada de Aplicação"}
    assert unit_named_by_section(e, ctx) == "unidade-02-nivel-de-aplicacao"
    assert narrow_window_by_unit(e, ["bloco-03", "bloco-05", "bloco-06", "bloco-22"], ctx) == ["bloco-03", "bloco-05"]


def test_secao_com_titulo_da_unidade_tambem_nomeia():
    ctx = _ctx()
    e = {"id": "x", "title": "slides", "source_section": "Nível de transporte"}
    assert unit_named_by_section(e, ctx) == "unidade-03-nivel-de-transporte"
    assert narrow_window_by_unit(e, ["bloco-05", "bloco-06"], ctx) == ["bloco-06"]


def test_nunca_esvazia_e_nao_mexe_sem_secao_ou_sem_bloco_da_unidade():
    ctx = _ctx()
    e = {"id": "y", "title": "slides", "source_section": "Semana 3"}
    assert narrow_window_by_unit(e, ["bloco-03", "bloco-06"], ctx) == ["bloco-03", "bloco-06"]
    e2 = {"id": "z", "title": "slides", "source_section": "U5 - Enlace"}
    assert narrow_window_by_unit(e2, ["bloco-03", "bloco-05"], ctx) == ["bloco-03", "bloco-05"]   # nenhum bloco de U5 na janela
    assert narrow_window_by_unit(e2, ["bloco-22"], ctx) == ["bloco-22"]                            # janela de 1 nao muda
