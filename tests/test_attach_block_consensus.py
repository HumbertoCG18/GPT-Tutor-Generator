from src.builder.ops.pedagogical_regeneration import attach_block_summary_fields


def _curation(primary, method="llm_only", conf=0.6):
    return {"entries": {"c1": {"summary": {
        "primary_block_id": primary,
        "block_match_method": method,
        "block_match_confidence": conf,
    }}}}


def _code_entry(**over):
    e = {
        "id": "c1",
        "file_type": "zip",
        "category": "codigo-professor",
        "computed_block_id": "bloco-05",
        "computed_block_band": "baixa",
        "source_section": "",
    }
    e.update(over)
    return e


def test_weak_noncard_code_adopts_gemini_block():
    # sem card + band baixa + gemini primary -> adota o Gemini
    [out] = attach_block_summary_fields([_code_entry()], _curation("bloco-12"))
    assert out["computed_block_id"] == "bloco-12"
    assert out["computed_block_method"] in ("llm_only", "consensus")
    assert out["computed_block_band"] != "baixa"  # band reflete a conf do Gemini (0.6)


def test_carded_code_keeps_funnel_block():
    # com card -> NUNCA sobrescreve (card é autoritativo)
    [out] = attach_block_summary_fields(
        [_code_entry(source_section="aula-05", computed_block_id="bloco-05")],
        _curation("bloco-12"),
    )
    assert out["computed_block_id"] == "bloco-05"


def test_strong_funnel_code_keeps_funnel_block():
    # band alta -> funil forte vence, Gemini não desempata
    [out] = attach_block_summary_fields(
        [_code_entry(computed_block_band="alta", computed_block_id="bloco-05")],
        _curation("bloco-12"),
    )
    assert out["computed_block_id"] == "bloco-05"


def test_non_code_entry_untouched_by_consensus():
    e = {"id": "c1", "file_type": "pdf", "category": "material",
         "computed_block_id": "bloco-05", "computed_block_band": "baixa", "source_section": ""}
    [out] = attach_block_summary_fields([e], _curation("bloco-12"))
    assert out["computed_block_id"] == "bloco-05"


def test_no_gemini_primary_keeps_funnel_block():
    [out] = attach_block_summary_fields([_code_entry()], _curation(""))
    assert out["computed_block_id"] == "bloco-05"


def test_swap_d1_resincroniza_tag_bloco():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1"},
        {"id": "bloco-02", "block_uuid": "u-2"},
    ]
    e = {"id": "e1", "file_type": "code", "computed_block_id": "u-1",
         "computed_block_band": "baixa", "auto_tags": ["bloco:bloco-01", "outra:tag"]}
    curation = {"entries": {"e1": {"summary": {
        "primary_block_id": "u-2", "block_match_method": "llm_only",
        "block_match_confidence": 0.9}}}}
    out = attach_block_summary_fields([e], curation, blocks=blocks)
    assert out[0]["computed_block_id"] == "u-2"
    assert "bloco:bloco-02" in out[0]["auto_tags"]      # resync (era o drift 1.3)
    assert "bloco:bloco-01" not in out[0]["auto_tags"]
    assert "outra:tag" in out[0]["auto_tags"]
