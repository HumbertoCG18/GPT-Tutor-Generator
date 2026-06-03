"""Fase 3 — tabela de fronteiras do helper confidence_band.

Cutoffs centralizados em src.builder.routing.thresholds (BAND_HIGH/BAND_LOW).
Inclusividade documentada:
  - confidence >= BAND_HIGH            -> "alta"   (HIGH inclusivo)
  - BAND_LOW <= confidence < BAND_HIGH -> "media"  (LOW inclusivo, HIGH exclusivo)
  - confidence <  BAND_LOW             -> "baixa"
"""

from src.builder.routing.thresholds import BAND_HIGH, BAND_LOW, confidence_band


def test_band_above_high_is_alta():
    assert confidence_band(BAND_HIGH + 0.1) == "alta"
    assert confidence_band(1.0) == "alta"


def test_band_exact_high_is_alta_inclusive():
    # fronteira HIGH e inclusiva
    assert confidence_band(BAND_HIGH) == "alta"


def test_band_between_is_media():
    midpoint = (BAND_HIGH + BAND_LOW) / 2.0
    assert confidence_band(midpoint) == "media"


def test_band_exact_low_is_media_inclusive():
    # fronteira LOW e inclusiva -> cai em "media", nao "baixa"
    assert confidence_band(BAND_LOW) == "media"


def test_band_just_below_high_is_media():
    assert confidence_band(BAND_HIGH - 0.001) == "media"


def test_band_below_low_is_baixa():
    assert confidence_band(BAND_LOW - 0.001) == "baixa"
    assert confidence_band(0.0) == "baixa"


def test_band_ordering_is_coherent_with_scale():
    # HIGH deve ser estritamente maior que LOW (faixa media nao-vazia)
    assert BAND_LOW < BAND_HIGH
