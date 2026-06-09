"""Deriva kind do bloco a partir da coluna Atividade do cronograma (sem {kind=})."""

from src.builder.timeline.index import _build_timeline_candidate_rows


def _row(descricao, atividade, data="03/07/2026"):
    # chaves espelham os headers normalizados da tabela do syllabus
    return {"data": data, "descricao": descricao, "atividade": atividade}


def test_atividade_prova_sets_assessment_kind():
    rows = _build_timeline_candidate_rows([_row("Prova P2", "Prova")])
    assert rows[0]["kind"] == "assessment"


def test_atividade_aula_stays_class():
    rows = _build_timeline_candidate_rows([_row("Maquinas de Turing", "Aula")])
    assert rows[0]["kind"] == "class"


def test_atividade_trabalho_sets_deliverable():
    rows = _build_timeline_candidate_rows([_row("Apresentacao T1", "Trabalho")])
    assert rows[0]["kind"] == "deliverable"


def test_atividade_feriado_sets_holiday():
    rows = _build_timeline_candidate_rows([_row("Feriado", "Feriado")])
    assert rows[0]["kind"] == "holiday"


def test_atividade_accented_prova_substituicao_maps_assessment():
    rows = _build_timeline_candidate_rows([_row("Prova PS", "Prova de Substituição")])
    assert rows[0]["kind"] == "assessment"


def test_explicit_kind_marker_wins_over_atividade():
    # {kind=holiday} no conteudo vence a coluna Atividade=Prova
    rows = _build_timeline_candidate_rows(
        [{"data": "03/07/2026", "descricao": "X {kind=holiday}", "atividade": "Prova"}]
    )
    assert rows[0]["kind"] == "holiday"


def test_no_atividade_column_defaults_class():
    rows = _build_timeline_candidate_rows([{"data": "03/07/2026", "conteudo": "Aula normal"}])
    assert rows[0]["kind"] == "class"


def test_atividade_header_variant_capitalized():
    rows = _build_timeline_candidate_rows([{"Data": "03/07/2026", "Descricao": "Prova P2", "Atividade": "Prova"}])
    assert rows[0]["kind"] == "assessment"


from src.builder.timeline.index import _aggregate_source_kind
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind


def test_prova_rows_aggregate_to_assessment_source_kind():
    rows = _build_timeline_candidate_rows([
        {"data": "01/07/2026", "descricao": "Revisao para Prova P2", "atividade": "Aula"},
        {"data": "03/07/2026", "descricao": "Prova P2", "atividade": "Prova"},
    ])
    assert [r["kind"] for r in rows] == ["class", "assessment"]
    # bloco que agrupa as duas linhas herda source_kind assessment (mais forte)
    assert _aggregate_source_kind(rows) == "assessment"
    block = {"source_kind": _aggregate_source_kind(rows), "unit_slug": "u1"}
    assert classify_block(block) == BlockKind.ASSESSMENT
