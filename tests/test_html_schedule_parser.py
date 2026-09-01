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
    assert "(20/04/2026) SEG — Suspensão de aulas [Aula] {kind=suspension} ⊘" in result


def test_aspnet_row_with_resource_appends_at_marker():
    result = parse_html_schedule(ASPNET_WITH_RESOURCE)
    assert "@Laboratório 409/412" in result
    assert "— Prova Interativa de Teoremas - Isabelle [Aula]" in result


from src.builder.timeline.signals import extract_timeline_session_signals


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


ASPNET_COLOR_SAMPLES = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr style="background-color:#FFA500;">
    <td><span id="dgAulas_ctl10_lblAula">15</span></td>
    <td><span id="dgAulas_ctl10_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl10_lblData">22/04/2026</span></td>
    <td><span id="dgAulas_ctl10_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl10_lblDescricao">Prova P1</span></td>
    <td><span id="dgAulas_ctl10_lblAtividade">Prova</span></td>
    <td><span id="dgAulas_ctl10_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#FF8C00;">
    <td><span id="dgAulas_ctl37_lblAula">37</span></td>
    <td><span id="dgAulas_ctl37_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl37_lblData">08/07/2026</span></td>
    <td><span id="dgAulas_ctl37_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl37_lblDescricao">Prova PS</span></td>
    <td><span id="dgAulas_ctl37_lblAtividade">Prova de Substituição</span></td>
    <td><span id="dgAulas_ctl37_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#8B0000;">
    <td><span id="dgAulas_ctl25_lblAula">25</span></td>
    <td><span id="dgAulas_ctl25_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl25_lblData">27/05/2026</span></td>
    <td><span id="dgAulas_ctl25_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl25_lblDescricao">SE Day</span></td>
    <td><span id="dgAulas_ctl25_lblAtividade">Evento Acadêmico</span></td>
    <td><span id="dgAulas_ctl25_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#FFFF00;">
    <td><span id="dgAulas_ctl20_lblAula">20</span></td>
    <td><span id="dgAulas_ctl20_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl20_lblData">10/06/2026</span></td>
    <td><span id="dgAulas_ctl20_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl20_lblDescricao">Apresentação de trabalho</span></td>
    <td><span id="dgAulas_ctl20_lblAtividade">Trabalho</span></td>
    <td><span id="dgAulas_ctl20_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:LightGrey;">
    <td><span id="dgAulas_ctl39_lblAula"></span></td>
    <td><span id="dgAulas_ctl39_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl39_lblData">15/07/2026</span></td>
    <td><span id="dgAulas_ctl39_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl39_lblDescricao">Prova G2</span></td>
    <td><span id="dgAulas_ctl39_lblAtividade">Prova de G2</span></td>
    <td><span id="dgAulas_ctl39_lblRecursos"></span></td>
  </tr>
</table>
"""


def test_aspnet_color_exam_emits_kind_exam_no_ignore():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "— Prova P1 [Prova] {kind=assessment}" in result
    assert "Prova P1 [Prova] {kind=assessment} ⊘" not in result


def test_aspnet_color_ps_emits_kind_ps_ignored():
    # D1 (ruling 28/08): PS = substitutiva, cobre o semestre inteiro — nao e
    # prova principal nem marco. Cor propria #FF8C00 em 6/6 cronogramas.
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "Prova PS" in result
    assert "{kind=ps} ⊘" in result


def test_aspnet_color_event_emits_kind_event_ignored():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "— SE Day [Evento Acadêmico] {kind=event} ⊘" in result


def test_aspnet_color_assignment_emits_kind_assignment_no_ignore():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "{kind=deliverable}" in result
    assert "{kind=deliverable} ⊘" not in result


def test_aspnet_color_g2_emits_kind_g2_ignored():
    # D1 (ruling 28/08): G2 = recuperacao condicional, cobre o semestre — nao e
    # N-esima prova. LightGrey com Atividade de prova (devolucao segue results).
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "Prova G2" in result
    assert "{kind=g2} ⊘" in result


def test_aspnet_class_row_omits_kind_token():
    # Row sem cor especial não deve poluir syllabus com {kind=class}
    result = parse_html_schedule(ASPNET_SAMPLE)
    assert "{kind=" not in result


ASPNET_BGCOLOR_2026_2 = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr bgcolor="#FFA500">
    <td><span id="dgAulas_ctl10_lblAula">10</span></td>
    <td><span id="dgAulas_ctl10_lblDia">TER</span></td>
    <td><span id="dgAulas_ctl10_lblData">24/09/2026</span></td>
    <td><span id="dgAulas_ctl10_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl10_lblDescricao">Prova P1</span></td>
    <td><span id="dgAulas_ctl10_lblAtividade">Prova</span></td>
    <td><span id="dgAulas_ctl10_lblRecursos"></span></td>
  </tr>
  <tr bgcolor="#FF8C00">
    <td><span id="dgAulas_ctl34_lblAula">34</span></td>
    <td><span id="dgAulas_ctl34_lblDia">TER</span></td>
    <td><span id="dgAulas_ctl34_lblData">01/12/2026</span></td>
    <td><span id="dgAulas_ctl34_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl34_lblDescricao">Prova PS</span></td>
    <td><span id="dgAulas_ctl34_lblAtividade">Prova de Substituição</span></td>
    <td><span id="dgAulas_ctl34_lblRecursos"></span></td>
  </tr>
  <tr bgcolor="DarkBlue">
    <td><span id="dgAulas_ctl05_lblAula">5</span></td>
    <td><span id="dgAulas_ctl05_lblDia">TER</span></td>
    <td><span id="dgAulas_ctl05_lblData">01/09/2026</span></td>
    <td><span id="dgAulas_ctl05_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl05_lblDescricao">Protocolos de Aplicação</span></td>
    <td><span id="dgAulas_ctl05_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl05_lblRecursos"></span></td>
  </tr>
</table>
"""


def test_aspnet_bgcolor_attr_do_export_2026_2_e_lido():
    # Exports 2026/2 (FR/Lab Redes/Lab SO) trocaram style="background-color:X"
    # pelo ATRIBUTO bgcolor= — o parser de cor era cego a eles (medido nos .bin
    # de Desktop/claude-tutor/sarc em 31/08).
    result = parse_html_schedule(ASPNET_BGCOLOR_2026_2)
    assert "— Prova P1 [Prova] {kind=assessment}" in result
    assert "{kind=ps} ⊘" in result


def test_aspnet_bgcolor_darkblue_e_aula_normal():
    # DarkBlue = highlight de "proxima aula" do SARC, nao e kind.
    result = parse_html_schedule(ASPNET_BGCOLOR_2026_2)
    assert "Protocolos de Aplicação [Aula]" in result
    assert "Protocolos de Aplicação [Aula] {kind=" not in result


def test_aspnet_ff4500_e_suspensao():
    # #FF4500 (orangered) aparece no export do IA como feriado/suspensao
    # (censo D2 28/08) e nao estava no mapa — caia em aula.
    html = ASPNET_BGCOLOR_2026_2.replace('bgcolor="DarkBlue"', 'bgcolor="#FF4500"')
    result = parse_html_schedule(html)
    assert "Protocolos de Aplicação [Aula] {kind=suspension} ⊘" in result


def test_aspnet_lightgrey_devolucao_na_descricao_vira_results():
    # Caso real MF 13/07: LightGrey, Atividade "Aula", Descricao "Devolução das
    # provas" — o teste de "devolu" so olhava a Atividade e a linha virava g2.
    html = ASPNET_COLOR_SAMPLES.replace(
        '<td><span id="dgAulas_ctl39_lblDescricao">Prova G2</span></td>',
        '<td><span id="dgAulas_ctl39_lblDescricao">Devolução das provas</span></td>',
    ).replace(
        '<td><span id="dgAulas_ctl39_lblAtividade">Prova de G2</span></td>',
        '<td><span id="dgAulas_ctl39_lblAtividade">Aula</span></td>',
    )
    result = parse_html_schedule(html)
    assert "Devolução das provas [Aula] {kind=results} ⊘" in result
