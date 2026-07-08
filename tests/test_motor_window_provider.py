from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import (
    provider_manual,
    provider_labels,
    resolve_window,
)
from src.builder.timeline.card_block import normalized_card_map

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02"},
    {"id": "bloco-02", "period_start": "2026-03-04"},
    {"id": "bloco-05", "period_start": "2026-04-06"},
    {"id": "bloco-06", "period_start": "2026-04-13"},
]

CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Introdução a Métodos Formais": {
        "block_ids": ["bloco-01", "bloco-02"], "source": "labels",
    },
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_p1_manual_returns_window_only_for_manual_source():
    ctx = _ctx()
    assert provider_manual({"source_section": "Provas por Indução"}, ctx) == ["bloco-05", "bloco-06"]
    # labels-source NÃO é P1:
    assert provider_manual({"source_section": "Introdução a Métodos Formais"}, ctx) == []


def test_p2_labels_returns_window_only_for_labels_source():
    ctx = _ctx()
    assert provider_labels({"source_section": "Introdução a Métodos Formais"}, ctx) == ["bloco-01", "bloco-02"]
    assert provider_labels({"source_section": "Provas por Indução"}, ctx) == []


def test_cascade_prefers_manual_then_labels():
    ctx = _ctx()
    win, prov = resolve_window({"source_section": "Provas por Indução"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")
    win, prov = resolve_window({"source_section": "Introdução a Métodos Formais"}, ctx)
    assert (win, prov) == (["bloco-01", "bloco-02"], "labels")


def test_empty_or_missing_card_yields_no_window():
    ctx = _ctx()
    assert resolve_window({"source_section": "Bibliografia-Livros"}, ctx) == ([], "")
    assert resolve_window({"source_section": "Card Inexistente"}, ctx) == ([], "")
    assert resolve_window({"source_section": ""}, ctx) == ([], "")


def test_card_lookup_is_accent_and_case_insensitive():
    ctx = _ctx()
    # "provas por inducao" (sem acento, minúsculo) casa "Provas por Indução"
    win, prov = resolve_window({"source_section": "provas por inducao"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")


def test_malformed_card_value_yields_no_window():
    """Card quebrado (valor não-dict) degrada para funil, não AttributeError."""
    malformed_cbm = {
        "Card Quebrado": ["bloco-01"],  # Lista em vez de dict
        "String Card": "Introdução",    # String em vez de dict
        "Valid Card": {"block_ids": ["bloco-02"], "source": "manual"},
    }
    blocks = [
        {"id": "bloco-01", "period_start": "2026-03-02"},
        {"id": "bloco-02", "period_start": "2026-03-04"},
    ]
    ctx = MotorContext.from_artifacts(
        blocks=blocks,
        card_block_map=malformed_cbm,
        lessons_index={}
    )
    # Malformed cards retornam janela vazia (funil) sem crash:
    assert resolve_window({"source_section": "Card Quebrado"}, ctx) == ([], "")
    assert resolve_window({"source_section": "String Card"}, ctx) == ([], "")
    # Card válido funciona normalmente:
    assert resolve_window({"source_section": "Valid Card"}, ctx) == (["bloco-02"], "manual")


def test_card_entry_usa_normalizacao_unica_do_card_block():
    # a MESMA chave com acento/caixa divergente resolve nos dois caminhos
    cbm = {"Verificação de Programas": {"source": "labels", "block_ids": ["bloco-10"]}}
    ctx = MotorContext.from_artifacts(blocks=[], card_block_map=cbm, lessons_index={})
    entry = {"source_section": "verificacao de programas"}
    win, provider = resolve_window(entry, ctx)
    assert win == ["bloco-10"] and provider == "labels"
    # e o índice público de card_block dá a mesma visão normalizada
    assert "verificacao de programas" in normalized_card_map(cbm)
