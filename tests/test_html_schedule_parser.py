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


from src.builder.timeline_signals import extract_timeline_session_signals


FULL_FIXTURE = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr>
    <td><span id="dgAulas_ctl02_lblAula">1</span></td>
    <td><span id="dgAulas_ctl02_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl02_lblData">30/03/2026</span></td>
    <td><span id="dgAulas_ctl02_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl02_lblDescricao">Provas por indução</span></td>
    <td><span id="dgAulas_ctl02_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
  </tr>
  <tr>
    <td><span id="dgAulas_ctl03_lblAula">2</span></td>
    <td><span id="dgAulas_ctl03_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl03_lblData">01/04/2026</span></td>
    <td><span id="dgAulas_ctl03_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl03_lblDescricao">Provas por indução: listas e árvores</span></td>
    <td><span id="dgAulas_ctl03_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl03_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:Red;">
    <td><span id="dgAulas_ctl04_lblAula"></span></td>
    <td><span id="dgAulas_ctl04_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl04_lblData">20/04/2026</span></td>
    <td><span id="dgAulas_ctl04_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl04_lblDescricao">Suspensão de aulas</span></td>
    <td><span id="dgAulas_ctl04_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl04_lblRecursos"></span></td>
  </tr>
</table>
"""


def test_parser_output_feeds_session_extractor():
    syllabus = parse_html_schedule(FULL_FIXTURE)
    sessions = extract_timeline_session_signals(syllabus)

    dates = {s["date"] for s in sessions}
    assert "2026-03-30" in dates
    assert "2026-04-01" in dates
    assert "2026-04-20" not in dates

    labels = " | ".join(str(s["label"]) for s in sessions)
    assert "provas por inducao" in labels
