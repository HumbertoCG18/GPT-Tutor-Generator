from datetime import date
from src.builder.extraction.entry_signals import extract_date_prefix_signal


def test_extract_date_prefix_signal_parses_dd_mm():
    result = extract_date_prefix_signal("12.03 Processos.pdf", year=2026)
    assert result == date(2026, 3, 12)


def test_extract_date_prefix_signal_parses_single_digit_day():
    result = extract_date_prefix_signal("5.09 Slides aula.pdf", year=2026)
    assert result == date(2026, 9, 5)


def test_extract_date_prefix_signal_returns_none_when_no_pattern():
    assert extract_date_prefix_signal("Processos.pdf", year=2026) is None
    assert extract_date_prefix_signal("cap01-introducao.pdf", year=2026) is None


def test_extract_date_prefix_signal_returns_none_on_invalid_date():
    assert extract_date_prefix_signal("32.13 arquivo.pdf", year=2026) is None


def test_extract_date_prefix_signal_uses_stem_not_full_name():
    result = extract_date_prefix_signal("15.04 Listas.pdf", year=2026)
    assert result == date(2026, 4, 15)
