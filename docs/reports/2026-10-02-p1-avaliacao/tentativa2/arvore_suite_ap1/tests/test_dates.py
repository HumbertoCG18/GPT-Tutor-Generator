from datetime import date

import pytest

from src.builder.routing.dates import extract_dates


# Tabela: cada caso é (texto, default_year, datas_esperadas).
# Cobre DD.MM, DD/MM, DD-MM, DD.MM.YYYY, DD/MM/YYYY, ISO YYYY-MM-DD,
# data no meio do texto, data no título, e ano ausente -> ano do curso.
_DATE_TABLE = [
    # nome, texto, default_year, esperado
    ("dd.mm_year_absent", "12.03 Processos", 2026, [date(2026, 3, 12)]),
    ("dd/mm_year_absent", "12/03 Processos", 2026, [date(2026, 3, 12)]),
    ("dd-mm_year_absent", "12-03 Processos", 2026, [date(2026, 3, 12)]),
    ("dd.mm.yyyy", "12.03.2025 Processos", 2026, [date(2025, 3, 12)]),
    ("dd/mm/yyyy", "12/03/2025 Processos", 2026, [date(2025, 3, 12)]),
    ("iso_yyyy_mm_dd", "2025-03-12 Processos", 2026, [date(2025, 3, 12)]),
    (
        "date_in_middle",
        "Slides da aula em 12/03/2025 sobre processos",
        2026,
        [date(2025, 3, 12)],
    ),
    (
        "date_in_title",
        "12.03 - Introducao aos processos sequenciais",
        2026,
        [date(2026, 3, 12)],
    ),
    ("single_digit_day_year_absent", "5.09 Slides", 2026, [date(2026, 9, 5)]),
]


@pytest.mark.parametrize(
    "label,text,default_year,expected",
    _DATE_TABLE,
    ids=[row[0] for row in _DATE_TABLE],
)
def test_extract_dates_table(label, text, default_year, expected):
    assert extract_dates(text, default_year=default_year) == expected


def test_extract_dates_skips_invalid_date():
    # 32.13 não é data válida -> ignorada, não levanta.
    assert extract_dates("32.13 arquivo", default_year=2026) == []


def test_extract_dates_space_pair_in_prose_is_not_a_date():
    # Texto JÁ normalizado: "Capitulo 5.12 - Introducao" -> "capitulo 5 12 ...".
    # O par de números no MEIO da prosa é subcapítulo, NÃO data: a forma year-less
    # separada por espaço só casa ancorada no início do texto.
    assert extract_dates("capitulo 5 12 introducao", default_year=2026) == []
    assert extract_dates("exercicio 3 04", default_year=2026) == []


def test_extract_dates_three_part_version_is_not_a_date():
    # "versao 2.10.1" não tem ano de 4 dígitos; o tail ".1" bloqueia o year-less
    # "2.10" (análogo ao span-consume do DMY). Normalizado vira "versao 2 10 1",
    # par no meio da prosa -> também []. Ambas as formas: nenhuma data fantasma.
    assert extract_dates("versao 2.10.1", default_year=2026) == []
    assert extract_dates("versao 2 10 1", default_year=2026) == []


def test_extract_dates_returns_multiple_dates():
    text = "Periodo de 10/03/2025 a 24/03/2025"
    assert extract_dates(text, default_year=2026) == [
        date(2025, 3, 10),
        date(2025, 3, 24),
    ]


def test_extract_dates_year_absent_without_default_year_is_skipped():
    # Sem ano no texto e sem default_year -> match year-less é pulado
    # (decisão documentada em dates.py); ISO com ano ainda é reconhecida.
    assert extract_dates("12.03 Processos") == []
    assert extract_dates("2025-03-12 Processos") == [date(2025, 3, 12)]


def test_extract_dates_empty_text():
    assert extract_dates("") == []
    assert extract_dates(None) == []  # type: ignore[arg-type]


def test_extract_dates_dedupes_and_preserves_order():
    text = "12/03/2025 ... e novamente 12/03/2025 ... depois 13/03/2025"
    assert extract_dates(text, default_year=2026) == [
        date(2025, 3, 12),
        date(2025, 3, 13),
    ]
