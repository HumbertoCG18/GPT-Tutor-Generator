"""P3b — provider ORDINAL: "Aula N" -> N-esimo ENCONTRO -> bloco.

Ruling user 2026-08-17 (TCC nomeia por contagem de aulas). O alvo e o ENCONTRO,
nao o bloco: um bloco tematico agrupa varias aulas. Medido no TCC: 16/19 contra
o gold por encontro; 1/19 por bloco.
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import provider_ordinal, resolve_window


def _block(bid, kind, *dates, topic=""):
    return {"id": bid, "kind": kind, "topic_text": topic,
            "primary_topic_label": topic,
            "period_start": dates[0] if dates else "",
            "period_end": dates[-1] if dates else "",
            "sessions": [{"date": d, "label": "aula"} for d in dates]}


def _ctx(blocks):
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})


def _tcc_like():
    """bloco-03 agrupa 3 encontros (geometria real do TCC)."""
    return [
        _block("bloco-01", "class", "2026-03-04"),
        _block("bloco-02", "class", "2026-03-06"),
        _block("bloco-03", "class", "2026-03-11", "2026-03-13", "2026-03-18"),
        _block("bloco-04", "deliverable", "2026-03-20"),
        _block("bloco-05", "class", "2026-03-25"),
    ]


def test_aula_dentro_de_bloco_agrupado():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Aula 05 - Minimização"}, ctx) == ["bloco-03"]


def test_aula_apos_agrupamento():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Aula 06 - Revisão"}, ctx) == ["bloco-05"]


def test_primeira_aula():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Aula 01 - Apresentação"}, ctx) == ["bloco-01"]


def test_deliverable_nao_conta_como_encontro():
    """bloco-04 (deliverable) nao entra na contagem: encontro 6 e o bloco-05."""
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Aula 06 - x"}, ctx) == ["bloco-05"]


def test_fora_do_range_nao_chuta():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Aula 99 - inexistente"}, ctx) == []


def test_sem_ordinal_e_inerte():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "Lista de Exercícios"}, ctx) == []


def test_ordinal_via_raw_target():
    ctx = _ctx(_tcc_like())
    assert provider_ordinal({"title": "", "raw_target": "raw/pdfs/aula-02-conjuntos.pdf"}, ctx) == ["bloco-02"]


def test_data_no_nome_vence_ordinal_na_cascata():
    """DATA e mais forte que ORDINAL: aponta o dia exato. O provider_date le o
    PREFIXO do nome (extract_date_in_name), entao o material datado tem a data
    na frente — mesmo que o titulo tambem traga "Aula N" com outro alvo."""
    ctx = _ctx(_tcc_like())
    win, name = resolve_window({"title": "25.03 Aula 01 - material do dia"}, ctx)
    assert name == "data" and win == ["bloco-05"]


def test_cascata_usa_ordinal_quando_nao_ha_data():
    ctx = _ctx(_tcc_like())
    win, name = resolve_window({"title": "Aula 02 - Conjuntos Enumeráveis"}, ctx)
    assert name == "ordinal" and win == ["bloco-02"]
