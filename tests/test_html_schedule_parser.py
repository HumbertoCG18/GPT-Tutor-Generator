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


ASPNET_WITH_SUSPENSION = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr style="background-color:Red;">
    <td><span id="dgAulas_ctl16_lblAula"></span></td>
    <td><span id="dgAulas_ctl16_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl16_lblData">20/04/2026</span></td>
    <td><span id="dgAulas_ctl16_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl16_lblDescricao">Suspensão de aulas</span></td>
    <td><span id="dgAulas_ctl16_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl16_lblRecursos"></span></td>
  </tr>
</table>
"""


ASPNET_WITH_RESOURCE = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr>
    <td><span id="dgAulas_ctl13_lblAula">12</span></td>
    <td><span id="dgAulas_ctl13_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl13_lblData">08/04/2026</span></td>
    <td><span id="dgAulas_ctl13_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl13_lblDescricao">Prova Interativa de Teoremas - Isabelle</span></td>
    <td><span id="dgAulas_ctl13_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl13_lblRecursos">Laboratório 409/412</span></td>
  </tr>
</table>
"""


def test_aspnet_suspension_row_gets_ignored_marker():
    result = parse_html_schedule(ASPNET_WITH_SUSPENSION)
    assert "(20/04/2026) SEG — Suspensão de aulas [Aula] ⊘" in result


def test_aspnet_row_with_resource_appends_at_marker():
    result = parse_html_schedule(ASPNET_WITH_RESOURCE)
    assert "@Laboratório 409/412" in result
    assert "— Prova Interativa de Teoremas - Isabelle [Aula]" in result
