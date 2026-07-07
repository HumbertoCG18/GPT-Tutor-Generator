from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02", "topic_text": "introducao"},
    {"id": "bloco-02", "period_start": "2026-03-04", "topic_text": "logica predicados"},
    {"id": "bloco-05", "period_start": "2026-04-06", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-06", "label": "inducao estrutural"}]},
    {"id": "bloco-06", "period_start": "2026-04-13", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-13", "label": "inducao arvores"}]},
]
CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_bibliografia_routes_out_of_motor():
    assert is_out_of_disamb_scope({"category": "bibliografia"}) is True
    eng = AnchorEngine()
    assert eng.resolve({"category": "bibliografia", "source_section": "Bibliografia-Livros"}, _ctx()) is None


def test_d6_trabalho_prova_tde_out_of_disambiguator():
    assert is_out_of_disamb_scope({"category": "trabalhos"}) is True
    assert is_out_of_disamb_scope({"category": "provas"}) is True
    assert is_out_of_disamb_scope({"source_section": "TDE 3 - entrega"}) is True
    assert is_out_of_disamb_scope({"category": "material"}) is False


def test_no_window_returns_none_funil():
    eng = AnchorEngine()
    assert eng.resolve({"category": "material", "source_section": "Card Sem Janela"}, _ctx()) is None


def test_multiblock_window_runs_disambiguator_and_sets_provider():
    eng = AnchorEngine()
    d = eng.resolve(
        {"category": "material", "source_section": "Provas por Indução",
         "title": "Prova por indução em árvores"},
        _ctx(),
    )
    assert d is not None
    assert d.block_ref == "bloco-06"      # session-label 'arvores' discrimina
    assert d.provider == "manual"
    assert d.method == "disamb"
