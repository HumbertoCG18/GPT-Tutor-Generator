from types import SimpleNamespace

from src.builder.routing.resolver_apply import apply_unit_subunit_fields

BLOCKS = [
    {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
    {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
]

def _entry(**kw):
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-2",
         "computed_block_confidence": 0.8, "computed_block_method": "concept-fused",
         "auto_tags": ["unit:velha", "outra:tag"]}
    e.update(kw)
    return e

def _fns(unit_match):
    return dict(
        auto_map_entry_unit_fn=lambda e, ui, md, ti, learned_unit_boosts=None: unit_match,
        auto_map_entry_subtopic_fn=lambda e, tax, md, winning_unit_slug="": SimpleNamespace(
            topic_slug="", topic_label="", unit_slug="", confidence=0.0, ambiguous=True, reasons=[]),
        build_file_map_unit_index_from_course_fn=lambda cm, sp: [{"slug": "u1"}, {"slug": "u2"}],
        iter_content_taxonomy_topics_fn=lambda tax: [],
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

def test_unit_reconciliada_contra_bloco_do_motor():
    # unidade auto (u1, conf 0.7) discorda do bloco NOVO (u-2 -> u2) com block_conf 0.8
    # block_conf >= unit_conf: reconcilia pro bloco, reason "reconciliada_do_bloco=u-2".
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.7, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "reconciliada_do_bloco=u-2" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}
    assert out[0]["unit_match_confidence"] == 0.7

def test_unit_forte_vence_e_flaga_conflito():
    e = _entry(computed_block_confidence=0.5)
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u1"
    assert out[0]["unit_block_conflict"] == {"unit": "u1", "block_unit": "u2", "block_id": "u-2"}

def test_gate_unit_tag_e_espelho_de_tags():
    # conf < T.UNIT_TAG (0.65) -> slug gated vazio -> herda a do bloco; tag unit: espelha o resultado
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.5, ambiguous=False, reasons=["fraca"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"          # herdada_do_bloco
    assert "unit:u2" in out[0]["auto_tags"]
    assert "unit:velha" not in out[0]["auto_tags"]
    assert "outra:tag" in out[0]["auto_tags"]            # prefixo não-gerenciado preservado

def test_manual_unit_tem_precedencia():
    e = _entry(manual_unit_slug="uman")
    m = SimpleNamespace(slug="u1", confidence=0.2, ambiguous=True, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "uman"
    assert out[0]["unit_match_reasons"] == ["manual"]
    assert out[0]["unit_match_confidence"] == 1.0

def test_nao_material_e_sem_bloco_ficam_intocados():
    sem_bloco = {"id": "e2", "file_type": "pdf", "computed_block_id": "", "auto_tags": []}
    nao_material = {"id": "e3", "file_type": "url", "auto_tags": []}
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([sem_bloco, nao_material], BLOCKS, {}, None, None, {}, **_fns(m))
    assert "computed_unit_slug" not in out[0]
    assert "computed_unit_slug" not in out[1]

def test_unit_fraca_nunca_vence_bloco_mesmo_com_block_conf_menor():
    # conf 0.5 < T.UNIT_TAG: gate zera o slug ANTES do reconcile -> herda a
    # unidade do bloco, sem conflito espurio (semantica do legado).
    e = _entry(computed_block_confidence=0.3)
    m = SimpleNamespace(slug="u1", confidence=0.5, ambiguous=False, reasons=["fraca"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "herdada_do_bloco=u-2" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}
