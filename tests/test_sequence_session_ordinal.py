"""Sinal de sequencia mira o ordinal de ENCONTRO, nao o de bloco.

Ruling user 2026-08-17 (TCC usa "Aula N" com N = contagem de aulas): um bloco
tematico pode agrupar varias aulas, entao contar BLOCOS desanda o alvo a partir
do primeiro agrupamento. Medido no TCC: por sessao 16/19 vs por bloco 1/19.
"""
from src.builder.routing.sequence import annotate_class_ordinals, score_sequence_match
from src.builder.routing.thresholds import T


def _block(bid, kind, *dates):
    return {"id": bid, "kind": kind,
            "sessions": [{"date": d, "label": "aula"} for d in dates]}


def _sig(title):
    return {"title_text": title, "raw_text": ""}


def _blocks_tcc_like():
    """Geometria real do TCC: bloco-03 agrupa 3 encontros."""
    return annotate_class_ordinals([
        _block("bloco-01", "class", "2026-03-04"),
        _block("bloco-02", "class", "2026-03-06"),
        _block("bloco-03", "class", "2026-03-11", "2026-03-13", "2026-03-18"),
        _block("bloco-04", "deliverable", "2026-03-20"),
        _block("bloco-05", "class", "2026-03-25"),
    ])


def test_session_ordinals_contam_encontros_nao_blocos():
    blocks = _blocks_tcc_like()
    by_id = {b["id"]: b for b in blocks}
    assert by_id["bloco-01"]["session_ordinals"] == [1]
    assert by_id["bloco-02"]["session_ordinals"] == [2]
    assert by_id["bloco-03"]["session_ordinals"] == [3, 4, 5]   # 3 encontros
    assert by_id["bloco-04"]["session_ordinals"] == []          # nao e aula
    assert by_id["bloco-05"]["session_ordinals"] == [6]         # segue de 5
    # class_ordinal (contagem de BLOCOS) preservado p/ compat
    assert by_id["bloco-05"]["class_ordinal"] == 4


def test_aula_dentro_de_bloco_agrupado_casa():
    """"Aula 05" cai no bloco-03 (encontros 3,4,5) — com o alvo antigo
    (class_ordinal) teria ido pro bloco-05, que e a 4a aula do curso."""
    blocks = _blocks_tcc_like()
    by_id = {b["id"]: b for b in blocks}
    assert score_sequence_match(_sig("aula 05 minimizacao"), by_id["bloco-03"]) == T.SEQUENCE_BOOST
    assert score_sequence_match(_sig("aula 05 minimizacao"), by_id["bloco-05"]) == 0.0


def test_aula_apos_agrupamento_casa_o_bloco_certo():
    blocks = _blocks_tcc_like()
    by_id = {b["id"]: b for b in blocks}
    assert score_sequence_match(_sig("aula 06 revisao"), by_id["bloco-05"]) == T.SEQUENCE_BOOST
    assert score_sequence_match(_sig("aula 06 revisao"), by_id["bloco-03"]) == 0.0


def test_bloco_nao_aula_nunca_casa():
    blocks = _blocks_tcc_like()
    by_id = {b["id"]: b for b in blocks}
    assert score_sequence_match(_sig("aula 04 trabalho"), by_id["bloco-04"]) == 0.0


def test_material_sem_ordinal_e_inerte():
    blocks = _blocks_tcc_like()
    assert score_sequence_match(_sig("lista de exercicios"), blocks[0]) == 0.0


def test_fallback_class_ordinal_sem_sessions():
    """Bloco sem sessions (fixture minima): mantem o alvo historico."""
    blocks = annotate_class_ordinals([
        {"id": "b1", "kind": "class"},
        {"id": "b2", "kind": "class"},
    ])
    assert blocks[1]["session_ordinals"] == [2]  # 1 sessao implicita por bloco
    assert score_sequence_match(_sig("aula 02 x"), blocks[1]) == T.SEQUENCE_BOOST
