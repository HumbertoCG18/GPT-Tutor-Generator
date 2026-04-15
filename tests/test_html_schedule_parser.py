from src.utils.helpers import parse_html_schedule


ASPNET_SAMPLE = """
<table id="dgAulas">
  <tbody>
    <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
    <tr>
      <td><span id="dgAulas_ctl02_lblAula">1</span></td>
      <td><span id="dgAulas_ctl02_lblDia">SEG</span></td>
      <td><span id="dgAulas_ctl02_lblData">30/03/2026</span></td>
      <td><span id="dgAulas_ctl02_lblHora">LM<br>19:15 - 20:45</span></td>
      <td><span id="dgAulas_ctl02_lblDescricao">Provas por indução</span></td>
      <td><span id="dgAulas_ctl02_lblAtividade">Aula</span></td>
      <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
    </tr>
  </tbody>
</table>
"""


def test_parse_aspnet_schedule_emits_structured_line():
    result = parse_html_schedule(ASPNET_SAMPLE)
    assert "## Cronograma de Aulas" in result
    assert "- (30/03/2026) SEG — Provas por indução [Aula]" in result


def test_parse_non_aspnet_html_keeps_legacy_table_format():
    html = """
    <table>
      <tr><th>Col1</th><th>Col2</th></tr>
      <tr><td>a</td><td>b</td></tr>
    </table>
    """
    result = parse_html_schedule(html)
    assert result.startswith("| Col1 | Col2 |")
    assert "| a | b |" in result
