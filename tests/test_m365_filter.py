"""effective_m365_filter: digitado > salvo; vazio se ambos vazios.

Bug 2026-07-01: campo do filtro M365 comeca vazio a cada import -> usuario
re-digita (ou esquece) -> select_for_subject retorna 0 -> arquivos "somem"
silenciosamente. O fallback pro filtro salvo + aviso alto (na UI) corrige.
"""
from src.builder.sources.m365 import effective_m365_filter


def test_typed_tem_precedencia():
    assert effective_m365_filter("engenhariadesoftware2", "old") == "engenhariadesoftware2"


def test_cai_no_salvo_quando_digitado_vazio():
    assert effective_m365_filter("", "metodosformais") == "metodosformais"
    assert effective_m365_filter("   ", "metodosformais") == "metodosformais"


def test_vazio_quando_ambos_vazios():
    assert effective_m365_filter("", "") == ""
    assert effective_m365_filter(None, None) == ""
    assert effective_m365_filter("  ", None) == ""
