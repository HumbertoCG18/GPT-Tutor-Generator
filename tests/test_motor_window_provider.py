from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import (
    provider_manual,
    provider_labels,
    resolve_window,
)

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
