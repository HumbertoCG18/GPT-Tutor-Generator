"""`revisar` — campo DERIVADO do manifest (Fase 0 do plano 02/09, decisao B).

enum {duvida, llm, ok}: duvida = camada 1 (aberta), llm = camada 2 (colapsada,
"decidido por LLM — confira"), ok = nao aparece. Funcao pura sobre o entry
gravado; `apply_unit_subunit_fields` grava o campo em TODO material.
"""
from types import SimpleNamespace

from src.builder.routing.resolver_apply import apply_unit_subunit_fields
from src.builder.routing.revisar import revisar_de
from src.models.core import FileEntry


def _mat(**kw):
    e = {"id": "e1", "file_type": "pdf", "category": "aulas", "temporal_block_id": "u-1",
         "temporal_block_method": "janela-1", "temporal_block_flag": False,
         "unit_block_conflict": {}, "subunit_match_reasons": ["winner_score=0.80"]}
    e.update(kw)
    return e


# --- funcao pura -----------------------------------------------------------

def test_material_limpo_e_ok():
    assert revisar_de(_mat()) == "ok"


def test_sem_bloco_em_escopo_e_duvida():
    assert revisar_de(_mat(temporal_block_id="")) == "duvida"


def test_bibliografia_sem_bloco_e_ok():
    # _NO_TIMELINE_CATEGORIES: limpas do bloco de proposito, nao e duvida.
    assert revisar_de(_mat(temporal_block_id="", category="bibliografia")) == "ok"


def test_tde_sem_bloco_e_ok():
    # secao TDE e fora de escopo do motor (is_out_of_disamb_scope).
    assert revisar_de(_mat(temporal_block_id="", source_section="TDE 1")) == "ok"


def test_pino_manual_sem_temporal_e_ok():
    # pino valido: motor REMOVE os temporal_* (apply._clear_temporal).
    e = _mat(temporal_block_id="", manual_timeline_block_id="bloco-03")
    e.pop("temporal_block_method")
    e.pop("temporal_block_flag")
    assert revisar_de(e) == "ok"


def test_bloco_flagado_e_duvida():
    assert revisar_de(_mat(temporal_block_flag=True, temporal_block_method="disamb")) == "duvida"


def test_llm_funil_e_duvida():
    # resolve_funnel grava flag=True de proposito (50% e honesto).
    assert revisar_de(_mat(temporal_block_flag=True, temporal_block_method="llm-funil")) == "duvida"


def test_llm_na_janela_e_camada_llm():
    assert revisar_de(_mat(temporal_block_method="llm")) == "llm"


def test_conflito_unidade_bloco_e_duvida():
    conflito = {"unit": "u1", "block_unit": "u2", "block_id": "bloco-02"}
    assert revisar_de(_mat(unit_block_conflict=conflito)) == "duvida"


def test_subunidade_ambigua_e_duvida():
    assert revisar_de(_mat(subunit_match_reasons=["winner_score=0.40", "ambiguous"])) == "duvida"


def test_subunidade_empate_e_duvida():
    assert revisar_de(_mat(subunit_match_reasons=["empate-exato 2x score=0.30"])) == "duvida"


def test_subunidade_sem_sinal_e_ok():
    # decisao 4 do user: nem todo material precisa de subunidade.
    assert revisar_de(_mat(subunit_match_reasons=["sem-sinal (winner_score=0)"])) == "ok"


def test_subunidade_manual_e_ok():
    assert revisar_de(_mat(manual_subunit_slug="x", subunit_match_reasons=["manual"])) == "ok"


def test_duvida_vence_llm():
    assert revisar_de(_mat(temporal_block_method="llm", unit_block_conflict={"unit": "u1"})) == "duvida"


# --- gravacao no apply -------------------------------------------------------

BLOCKS = [
    {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
    {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
]


def _fns(unit_match):
    return dict(
        auto_map_entry_unit_fn=lambda e, ui, md, ti, learned_unit_boosts=None: unit_match,
        auto_map_entry_subtopic_fn=lambda e, tax, md, winning_unit_slug="": SimpleNamespace(
            topic_slug="", topic_label="", unit_slug="", confidence=0.0, ambiguous=False, reasons=[]),
        build_file_map_unit_index_from_course_fn=lambda cm, sp: [{"slug": "u1"}, {"slug": "u2"}],
        iter_content_taxonomy_topics_fn=lambda tax: [],
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )


def test_apply_grava_ok_no_material_com_bloco():
    e = {"id": "e1", "file_type": "pdf", "temporal_block_id": "u-2", "temporal_block_flag": False,
         "temporal_block_method": "janela-1", "auto_tags": []}
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["revisar"] == "ok"


def test_apply_grava_duvida_no_material_sem_bloco():
    # o loop de unidade PULA material sem bloco; o campo tem que nascer mesmo assim.
    e = {"id": "e2", "file_type": "pdf", "category": "aulas", "auto_tags": []}
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["revisar"] == "duvida"


def test_apply_nao_grava_em_nao_material():
    e = {"id": "e3", "file_type": "url", "category": "", "revisar": "ok", "auto_tags": []}
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert "revisar" not in out[0]


# --- round-trip do manifest -------------------------------------------------

def test_file_entry_round_trip_preserva_revisar():
    d = {"source_path": "a.pdf", "file_type": "pdf", "category": "aulas", "title": "A", "revisar": "duvida"}
    assert FileEntry.from_dict(d).to_dict()["revisar"] == "duvida"


def test_file_entry_omite_revisar_vazio():
    e = FileEntry(source_path="a.pdf", file_type="pdf", category="aulas", title="A")
    assert "revisar" not in e.to_dict()


# --- motivos (anatomia da fila: censo e UI mostram POR QUE) ---------------

def test_motivos_lista_cada_gatilho_disparado():
    from src.builder.routing.revisar import motivos_de
    e = _mat(temporal_block_flag=True, temporal_block_method="llm-funil",
             unit_block_conflict={"unit": "u1"}, subunit_match_reasons=["empate-exato 2x score=0.30"])
    assert motivos_de(e) == ["flag:llm-funil", "conflito", "sub-empate"]


def test_motivos_vazio_no_material_limpo():
    from src.builder.routing.revisar import motivos_de
    assert motivos_de(_mat()) == []
