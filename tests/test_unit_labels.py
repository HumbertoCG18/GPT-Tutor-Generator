"""Rótulo curto e nome de unidade a partir de slugs canônicos."""

from src.builder.timeline.unit_labels import (
    unit_short_label,
    unit_name_from_slug,
    unit_number,
)


def test_unit_short_label():
    assert unit_short_label("unidade-01-limites") == "U1"
    assert unit_short_label("unidade-10-series") == "U10"
    assert unit_short_label("unidade_02_derivadas") == "U2"
    assert unit_short_label("topico-avulso") == "topico-avulso"  # fora do padrão
    assert unit_short_label("") == ""
    assert unit_short_label(None) == ""


def test_unit_name_from_slug():
    assert unit_name_from_slug("unidade-01-limites") == "Limites"
    assert unit_name_from_slug("unidade-02-derivadas-parciais") == "Derivadas parciais"
    assert unit_name_from_slug("unidade-03") == "unidade-03"  # sem sufixo -> slug
    assert unit_name_from_slug("topico-avulso") == "topico-avulso"
    assert unit_name_from_slug("") == ""


def test_unit_number():
    assert unit_number("unidade-01-limites") == 1
    assert unit_number("unidade-10-series") == 10
    assert unit_number("topico-avulso") is None
    assert unit_number("") is None
