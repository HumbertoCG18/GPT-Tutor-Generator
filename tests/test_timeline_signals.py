from src.builder.timeline_signals import extract_date_range_signal
from src.builder.timeline_signals import extract_timeline_session_signals


def test_extract_timeline_session_signals_reads_inline_class_dates():
    text = """
    Semana 30/03/2026 a 03/04/2026:
    (30/03/2026): Especificacoes recursivas e provas por inducao;
    (atividade assincrona): Complementar os estudos com as leituras recomendadas.
    (01/04/2026): Especificacoes recursivas e provas por inducao;
    """.strip()

    sessions = extract_timeline_session_signals(text)

    assert [item["kind"] for item in sessions] == ["class", "async", "class"]
    assert sessions[0]["date"] == "2026-03-30"
    assert sessions[1]["date"] == ""
    assert "leituras recomendadas" in sessions[1]["signals"]
    assert sessions[2]["date"] == "2026-04-01"


def test_extract_date_range_signal_reads_week_range():
    signal = extract_date_range_signal("Semana 30/03/2026 a 03/04/2026")

    assert signal == {
        "start": "2026-03-30",
        "end": "2026-04-03",
        "label": "30/03/2026 a 03/04/2026",
    }


def test_extract_timeline_session_signals_returns_empty_for_plain_text():
    assert extract_timeline_session_signals("Logica de Hoare e verificacao parcial de programas") == []


def test_extract_timeline_session_signals_returns_empty_for_week_block_without_internal_sessions():
    text = "Semana 30/03/2026 a 03/04/2026: Especificacoes recursivas e provas por inducao"

    assert extract_timeline_session_signals(text) == []


def test_extract_timeline_session_signals_reads_linearized_html_anchor_text():
    text = "Aula 30/03/2026 Especificacoes recursivas e provas por inducao"

    sessions = extract_timeline_session_signals(text)

    assert len(sessions) == 1
    assert sessions[0]["kind"] == "class"
    assert sessions[0]["date"] == "2026-03-30"
    assert "especificacoes recursivas" in sessions[0]["signals"]
    assert "provas por inducao" in sessions[0]["signals"]


def test_session_extractor_accepts_em_dash_and_day_prefix():
    text = "- (30/03/2026) SEG — Provas por indução [Aula]"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    s = sessions[0]
    assert s["kind"] == "class"
    assert s["date"] == "2026-03-30"
    assert "provas por inducao" in s["label"]


def test_session_extractor_still_accepts_legacy_colon_format():
    text = "(30/03/2026): Provas por indução"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    assert sessions[0]["date"] == "2026-03-30"
    assert "provas por inducao" in sessions[0]["label"]
