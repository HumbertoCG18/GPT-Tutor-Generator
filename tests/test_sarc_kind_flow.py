"""SARC type (Atividade column + row color) -> canonical BlockKind flow."""

from src.utils.helpers import parse_html_schedule


def _sarc_html(atividade: str, descricao: str = "Conteudo", style: str = "") -> str:
    tr_style = f' style="{style}"' if style else ""
    return f"""
    <html><body><table id="dgAulas">
      <tr{tr_style}>
        <td><span id="dgAulas_ctl02_lblData">03/07/2026</span></td>
        <td><span id="dgAulas_ctl02_lblDia">Qui</span></td>
        <td><span id="dgAulas_ctl02_lblDescricao">{descricao}</span></td>
        <td><span id="dgAulas_ctl02_lblAtividade">{atividade}</span></td>
        <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
      </tr>
    </table></body></html>
    """


def test_atividade_prova_emits_assessment():
    md = parse_html_schedule(_sarc_html("Prova"))
    assert "{kind=assessment}" in md


def test_atividade_avaliacao_accented_emits_assessment():
    md = parse_html_schedule(_sarc_html("Avaliação"))
    assert "{kind=assessment}" in md


def test_atividade_trabalho_emits_deliverable():
    md = parse_html_schedule(_sarc_html("Trabalho"))
    assert "{kind=deliverable}" in md


def test_atividade_aula_with_orange_row_stays_class():
    # Atividade explicita vence a cor: Aula + laranja -> class (sem marcador).
    md = parse_html_schedule(_sarc_html("Aula", style="background-color:#ffa500"))
    assert "{kind=" not in md


def test_empty_atividade_with_orange_row_falls_back_to_assessment():
    md = parse_html_schedule(_sarc_html("", style="background-color:#ffa500"))
    assert "{kind=assessment}" in md


def test_orange_row_no_longer_emits_legacy_exam_token():
    md = parse_html_schedule(_sarc_html("", style="background-color:#ffa500"))
    assert "{kind=exam}" not in md


def test_atividade_feriado_emits_holiday():
    md = parse_html_schedule(_sarc_html("Feriado"))
    assert "{kind=holiday}" in md


def test_atividade_revisao_emits_review():
    md = parse_html_schedule(_sarc_html("Revisão"))
    assert "{kind=review}" in md


from src.builder.timeline.index import _build_timeline_candidate_rows


def test_candidate_row_keeps_valid_kind():
    rows = [{"content": "Prova final {kind=assessment}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "assessment"
    assert out[0]["ignored"] is False


def test_candidate_row_invalid_kind_becomes_class():
    rows = [{"content": "Algo {kind=foobar}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "class"


def test_candidate_row_ignored_token_preserved():
    rows = [{"content": "Greve {kind=suspension}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "suspension"
    assert out[0]["ignored"] is True
