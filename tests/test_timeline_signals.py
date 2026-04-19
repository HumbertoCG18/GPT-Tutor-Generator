from src.builder.timeline.signals import extract_date_range_signal
from src.builder.timeline.signals import extract_timeline_session_signals


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
    text = "- (30/03/2026) SEG - Provas por inducao [Aula]"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    s = sessions[0]
    assert s["kind"] == "class"
    assert s["date"] == "2026-03-30"
    assert "provas por inducao" in s["label"]


def test_session_extractor_still_accepts_legacy_colon_format():
    text = "(30/03/2026): Provas por inducao"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    assert sessions[0]["date"] == "2026-03-30"
    assert "provas por inducao" in sessions[0]["label"]


def test_session_extractor_skips_ignored_marker():
    text = (
        "- (20/04/2026) SEG - Suspensao de aulas [Aula] ⊘\n"
        "- (22/04/2026) QUA - Prova P1 [Prova]"
    )
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    assert sessions[0]["date"] == "2026-04-22"


def test_session_extractor_skips_ignored_kind_even_without_marker_and_strips_token():
    text = (
        "- (20/04/2026) SEG - Suspensao de aulas [Aula] {kind=suspension}\n"
        "- (08/07/2026) QUA - Prova PS [Prova de Substituicao] {kind=ps}\n"
        "- (15/07/2026) QUA - Prova G2 [Prova de G2] {kind=g2}\n"
        "- (27/05/2026) QUA - SE Day [Evento Academico] {kind=event}\n"
        "- (22/04/2026) QUA - Prova P1 [Prova] {kind=exam}\n"
        "- (30/03/2026) SEG - Provas por inducao [Aula]"
    )

    sessions = extract_timeline_session_signals(text)

    assert [item["date"] for item in sessions] == ["2026-04-22", "2026-03-30"]
    assert all("{kind=" not in item["label"] for item in sessions)
    assert all(
        all("{kind=" not in signal for signal in item["signals"])
        for item in sessions
    )


def test_session_extractor_parses_kind_and_skips_ignored_kinds():
    text = """
- (22/04/2026) QUA — Prova P1 [Prova] {kind=exam}
- (08/07/2026) QUA — Prova PS [Prova de Substituição] {kind=ps} ⊘
- (15/07/2026) QUA — Prova G2 [Prova de G2] {kind=g2} ⊘
- (27/05/2026) QUA — SE Day [Evento Acadêmico] {kind=event} ⊘
- (30/03/2026) SEG — Provas por indução [Aula]
"""
    sessions = extract_timeline_session_signals(text)
    dates = {s["date"] for s in sessions}
    # ignored kinds removidos
    assert "2026-07-08" not in dates
    assert "2026-07-15" not in dates
    assert "2026-05-27" not in dates
    # exam (não ignored) preservado
    assert "2026-04-22" in dates
    assert "2026-03-30" in dates
