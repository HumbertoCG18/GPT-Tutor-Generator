"""F5: cadeira sem prova — "Fechamento da parte N" (entrega numerada) segmenta as
unidades: bloco-aula entre o marco N-1 e o N pertence a unidade N (Lab SO, censo 28/08)."""
from src.builder.timeline.unit_matcher import assign_units_by_work_milestones

UNITS = [{"slug": f"unidade-0{i}-x"} for i in (1, 2)]


def _aula(txt):
    return {"topic_text": txt, "sessions": [{"label": txt}]}


def _marco(n):
    return {"source_kind": "deliverable", "topic_text": "fechamento parte trabalho",
            "sessions": [{"label": f"fechamento da parte {n} trabalho"}]}


def test_segmenta_pelas_entregas_numeradas():
    aulas = [_aula("introducao"), _aula("device drivers")]
    blocos = [aulas[0], _marco(1), aulas[1], _marco(2)]
    assert assign_units_by_work_milestones(blocos, aulas, UNITS) is True
    assert aulas[0]["unit_slug"] == "unidade-01-x"
    assert aulas[1]["unit_slug"] == "unidade-02-x"


def test_nao_aplica_quando_marcos_nao_batem_com_o_plano():
    """SO 2026/1: partes 1..4 mas 7 unidades -> DP decide como sempre."""
    aulas = [_aula("a"), _aula("b")]
    blocos = [aulas[0], _marco(1), aulas[1]]  # so 1 marco p/ 2 unidades
    assert assign_units_by_work_milestones(blocos, aulas, UNITS) is False
    assert "unit_slug" not in aulas[0]


def test_parte_sem_numero_ou_em_aula_nao_e_marco():
    aulas = [_aula("formalizacao - parte 1"), _aula("b")]  # "parte 1" em AULA (MF)
    blocos = [aulas[0], {"source_kind": "deliverable", "topic_text": "entrega",
                         "sessions": [{"label": "entrega trabalho"}]}, aulas[1]]
    assert assign_units_by_work_milestones(blocos, aulas, UNITS) is False


def test_aula_depois_do_ultimo_marco_fica_na_ultima_unidade():
    aulas = [_aula("a"), _aula("b"), _aula("depois")]
    blocos = [aulas[0], _marco(1), aulas[1], _marco(2), aulas[2]]
    assert assign_units_by_work_milestones(blocos, aulas, UNITS) is True
    assert aulas[2]["unit_slug"] == "unidade-02-x"
