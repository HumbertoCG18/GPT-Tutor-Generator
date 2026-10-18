"""Tests for the SARC cronograma URL import feature (Phase 1).

Covers the new helpers `fetch_schedule_html` and `is_sarc_url` plus an
integration check that a SARC ASP.NET fixture flows through
`fetch_schedule_html` -> `parse_html_schedule` and produces non-error markdown.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.utils.helpers import (
    decide_schedule_source,
    fetch_schedule_html,
    is_sarc_url,
    parse_html_schedule,
)


# --- fetch_schedule_html ---------------------------------------------------


def test_fetch_schedule_html_returns_response_text():
    fake_response = MagicMock()
    fake_response.text = "<html>ok</html>"
    fake_response.raise_for_status.return_value = None

    with patch("src.utils.helpers.requests.get", return_value=fake_response) as mock_get:
        result = fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")

    assert result == "<html>ok</html>"
    mock_get.assert_called_once()


def test_fetch_schedule_html_propagates_timeout():
    with patch(
        "src.utils.helpers.requests.get",
        side_effect=requests.exceptions.Timeout("timed out"),
    ):
        with pytest.raises(requests.exceptions.Timeout):
            fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")


def test_fetch_schedule_html_propagates_connection_error():
    with patch(
        "src.utils.helpers.requests.get",
        side_effect=requests.exceptions.ConnectionError("no route"),
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")


def test_fetch_schedule_html_propagates_http_error():
    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

    with patch("src.utils.helpers.requests.get", return_value=fake_response):
        with pytest.raises(requests.exceptions.HTTPError):
            fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")


def test_fetch_schedule_html_uses_tuple_timeout():
    fake_response = MagicMock()
    fake_response.text = "<html></html>"
    fake_response.raise_for_status.return_value = None

    with patch("src.utils.helpers.requests.get", return_value=fake_response) as mock_get:
        fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")

    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == (10, 30)


# --- integration: fetch -> parse ------------------------------------------


# Minimal SARC ASP.NET fixture. The parser detects the ASP.NET path by the
# table id="dgAulas" and reads spans whose id ends with _lblData / _lblDescricao
# / _lblDia / _lblAtividade / _lblRecursos (see _parse_aspnet_schedule).
SARC_FIXTURE_HTML = """
<html>
  <body>
    <table id="dgAulas">
      <tr>
        <td><span id="dgAulas_ctl02_lblData">10/03/2026</span></td>
        <td><span id="dgAulas_ctl02_lblDia">Ter</span></td>
        <td><span id="dgAulas_ctl02_lblDescricao">Introducao ao curso</span></td>
        <td><span id="dgAulas_ctl02_lblAtividade">Aula</span></td>
        <td><span id="dgAulas_ctl02_lblRecursos">Slides cap 1</span></td>
      </tr>
      <tr>
        <td><span id="dgAulas_ctl03_lblData">12/03/2026</span></td>
        <td><span id="dgAulas_ctl03_lblDia">Qui</span></td>
        <td><span id="dgAulas_ctl03_lblDescricao">Estruturas de dados</span></td>
        <td><span id="dgAulas_ctl03_lblAtividade">Aula</span></td>
        <td><span id="dgAulas_ctl03_lblRecursos"></span></td>
      </tr>
    </table>
  </body>
</html>
"""


def test_sarc_fixture_flows_from_fetch_to_parse():
    fake_response = MagicMock()
    fake_response.text = SARC_FIXTURE_HTML
    fake_response.raise_for_status.return_value = None

    with patch("src.utils.helpers.requests.get", return_value=fake_response):
        html = fetch_schedule_html("https://sarc.pucrs.br/Default/Export.aspx?id=1")

    markdown = parse_html_schedule(html)

    assert not markdown.startswith("Erro")
    assert "## Cronograma de Aulas" in markdown
    assert "10/03/2026" in markdown
    assert "Introducao ao curso" in markdown
    assert "12/03/2026" in markdown
    assert "Estruturas de dados" in markdown


# --- is_sarc_url -----------------------------------------------------------


def test_is_sarc_url_accepts_https_with_subpath_and_query():
    assert is_sarc_url(
        "https://sarc.pucrs.br/Default/Export.aspx?id=123&ano=2026&sem=1"
    )


def test_is_sarc_url_accepts_http():
    assert is_sarc_url("http://sarc.pucrs.br/Default/Export.aspx?id=1")


def test_is_sarc_url_rejects_other_domain():
    assert not is_sarc_url("https://evil.com/Default/Export.aspx?id=1")


def test_is_sarc_url_rejects_suffix_spoof():
    assert not is_sarc_url("https://sarc.pucrs.br.evil.com/Default/Export.aspx?id=1")


def test_is_sarc_url_rejects_empty_string():
    assert not is_sarc_url("")


def test_is_sarc_url_rejects_whitespace():
    assert not is_sarc_url("   ")


def test_is_sarc_url_rejects_malformed():
    assert not is_sarc_url("not-a-url")


def test_is_sarc_url_rejects_non_http_scheme():
    assert not is_sarc_url("ftp://sarc.pucrs.br/x")


# --- decide_schedule_source (Phase 2 pure decision helper) -----------------


def test_decide_source_valid_url_takes_precedence_over_html():
    decision = decide_schedule_source(
        "https://sarc.pucrs.br/Default/Export.aspx?id=1",
        "<table>pasted</table>",
    )
    assert decision == {
        "action": "fetch",
        "url": "https://sarc.pucrs.br/Default/Export.aspx?id=1",
    }


def test_decide_source_invalid_url_returns_error():
    decision = decide_schedule_source("https://evil.com/x", "<table></table>")
    assert decision["action"] == "error"
    assert "sarc.pucrs.br" in decision["message"]


def test_decide_source_empty_url_uses_pasted_html():
    decision = decide_schedule_source("", "<table>x</table>")
    assert decision == {"action": "parse", "html": "<table>x</table>"}


def test_decide_source_whitespace_url_uses_pasted_html():
    decision = decide_schedule_source("   ", "  <table>x</table>  ")
    assert decision == {"action": "parse", "html": "<table>x</table>"}


def test_decide_source_both_empty_cancels():
    assert decide_schedule_source("", "") == {"action": "cancel"}


def test_decide_source_handles_none_inputs():
    assert decide_schedule_source(None, None) == {"action": "cancel"}


# --- parse_sarc_turma_key ---------------------------------------------------


def test_parse_sarc_turma_key():
    from src.utils.helpers import parse_sarc_turma_key
    url = "https://sarc.pucrs.br/Default/Export.aspx?id=9b679f12-aaaa&ano=2026&sem=1"
    assert parse_sarc_turma_key(url) == {"guid": "9b679f12-aaaa", "ano": "2026", "sem": "1"}


def test_parse_sarc_turma_key_malformed():
    from src.utils.helpers import parse_sarc_turma_key
    assert parse_sarc_turma_key("not a url") == {"guid": "", "ano": "", "sem": ""}
