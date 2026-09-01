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


# Raiz (2026-08-25): o kind da linha vinha SO do marcador {kind=} ou da coluna
# Atividade; o TEXTO da linha nunca era lido. "suspensao jogo copa do mundo" com
# Atividade "Aula" entrava como aula, fundia com a aula seguinte ("devops
# exercicios" = continuacao) e o classificador so via o agregado: ES2 bloco-11
# virou `suspended` inteiro, IA bloco-06 engoliu "suspensao de aulas" como class.
# Censo nos 5 cursos: 4 blocos mistos (IA 06/15, SO 25, ES2 11).
def test_texto_nao_academico_vence_atividade_aula_generica():
    rows = _build_timeline_candidate_rows([_row("suspensao jogo copa do mundo", "Aula", "19/06/2026")])
    assert rows[0]["kind"] == "suspended"


def test_texto_feriado_sem_atividade_vira_holiday():
    rows = _build_timeline_candidate_rows([_row("Feriado de Tiradentes", "", "21/04/2026")])
    assert rows[0]["kind"] == "holiday"


def test_texto_de_aula_continua_class():
    rows = _build_timeline_candidate_rows([_row("Prova de teoremas em Isabelle", "Aula"),
                                           _row("Correcao de exercicios", "Aula")])
    assert [r["kind"] for r in rows] == ["class", "class"]


def test_atividade_explicita_nao_class_continua_vencendo_o_texto():
    rows = _build_timeline_candidate_rows([_row("suspensao jogo", "Prova")])
    assert rows[0]["kind"] == "assessment"


def test_linha_suspensa_por_texto_nao_funde_com_a_aula_seguinte():
    from src.builder.timeline.index import _rows_belong_to_same_thematic_block
    rows = _build_timeline_candidate_rows([_row("suspensao jogo copa do mundo", "Aula", "19/06/2026"),
                                           _row("devops exercicios", "Aula", "26/06/2026")])
    assert _rows_belong_to_same_thematic_block(rows[0], rows[1], current_rows=[rows[0]]) is False


def test_ps_e_g2_agregam_como_source_kind_nao_aula():
    """A.1 (31/08): linhas {kind=ps}/{kind=g2} sao ignoradas nas SESSIONS, mas o
    BLOCO delas nao pode virar candidato a aula — sem hint, o bloco da PS do MF
    entrou no DP posicional e moveu a fronteira u02/u03 (5 entries fliparam,
    regua 66->61; bisect 31/08). Traducao no agregador: ps->makeup (prova
    substitutiva) e g2->assessment (recuperacao); a distincao fina (nao contar
    como prova PRINCIPAL) e assunto do D1, nao do hint."""
    assert _aggregate_source_kind([{"kind": "ps"}]) == "makeup"
    assert _aggregate_source_kind([{"kind": "g2"}]) == "assessment"
    assert _aggregate_source_kind([{"kind": "ps"}, {"kind": "class"}]) == "makeup"
