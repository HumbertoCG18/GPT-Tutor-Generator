"""D3/F7: U<n>/"Unidade N" explicito no card/titulo/arquivo decide a unidade (1a classe).

Caso real: Fund. Redes 2026/2 — cards "U1 - Redes de Computadores", "U2 - Camada de
Aplicacao"; arquivos "Lista de exercicios - Unidade 1". Numeracao do plano = autoridade."""
from src.builder.engine import _auto_map_entry_unit
from src.builder.routing.file_map import explicit_unit_number

UNITS = [
    ("Unidade 01: Redes de Computadores", ["tipos de redes", "protocolos de redes"]),
    ("Unidade 02: Camada de Aplicacao", ["dhcp", "dns", "http"]),
]


def test_card_u1_decide_unidade_1():
    m = _auto_map_entry_unit({"source_section": "U1 - Redes de Computadores",
                              "title": "Tipos de Redes (Slides)"}, UNITS, "")
    assert m.slug.startswith("unidade-01") and not m.ambiguous
    assert m.confidence >= 0.9 and "unidade-explicita=u1" in m.reasons


def test_titulo_unidade_2_decide_unidade_2():
    m = _auto_map_entry_unit({"source_section": "Materiais",
                              "title": "Lista de exercicios - Unidade 2"}, UNITS, "")
    assert m.slug.startswith("unidade-02") and "unidade-explicita=u2" in m.reasons


def test_numero_sem_unidade_correspondente_cai_no_scorer():
    m = _auto_map_entry_unit({"source_section": "U7 - Topicos Avancados", "title": "x"}, UNITS, "")
    assert "unidade-explicita=u7" not in m.reasons


def test_falsos_positivos_nao_casam():
    assert explicit_unit_number({"title": "aula01 - historia"}) is None
    assert explicit_unit_number({"title": "qemu 2 na pratica"}) is None
    assert explicit_unit_number({"title": "exemplo de socket UDP 1"}) is None
    assert explicit_unit_number({"source_path": "C:/x/U03 - Roteamento.pdf"}) == 3
    assert explicit_unit_number({"source_section": "Unidade de Aprendizagem 04"}) == 4
