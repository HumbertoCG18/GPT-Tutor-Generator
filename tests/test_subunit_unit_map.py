from src.ui.dialogs import _subunit_unit_map_from_plan
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan


# Texto no formato que _parse_units_from_teaching_plan realmente reconhece:
# cabeçalho genérico "Unidade N - Título" + tópicos numerados "N.N. Texto".
PLAN = """\
Unidade 1 - Fundamentos
1.1. Introducao aos sistemas
1.2. Conceitos basicos

Unidade 2 - Algoritmos
2.1. Ordenacao
2.2. Busca binaria
"""


def test_maps_each_topic_to_its_unit():
    parsed = _parse_units_from_teaching_plan(PLAN)
    assert len(parsed) == 2
    unit_title_1, _ = parsed[0]
    unit_title_2, _ = parsed[1]

    unit_label_to_slug = {unit_title_1: "unidade-1", unit_title_2: "unidade-2"}
    out = _subunit_unit_map_from_plan(PLAN, unit_label_to_slug)

    # slugify do tópico (sem prefixo numérico) mapeia para o slug da sua unidade
    from src.utils.helpers import slugify
    assert out[slugify("Introducao aos sistemas")] == "unidade-1"
    assert out[slugify("Conceitos basicos")] == "unidade-1"
    assert out[slugify("Ordenacao")] == "unidade-2"
    assert out[slugify("Busca binaria")] == "unidade-2"


def test_falls_back_to_slugify_when_title_unknown():
    parsed = _parse_units_from_teaching_plan(PLAN)
    unit_title_1, _ = parsed[0]
    from src.utils.helpers import slugify

    # sem mapa de labels -> usa slugify(titulo) como unit_slug
    out = _subunit_unit_map_from_plan(PLAN, {})
    assert out[slugify("Introducao aos sistemas")] == slugify(unit_title_1)
