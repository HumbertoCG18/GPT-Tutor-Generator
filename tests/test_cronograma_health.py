# tests/test_cronograma_health.py
from src.builder.artifacts.cronograma_health import material_coverage


def _entry(eid, auto_tags=None, ftype="pdf"):
    return {"id": eid, "auto_tags": auto_tags or [], "file_type": ftype, "category": "material-de-aula"}


def test_coverage_counts_blocked_vs_orphan():
    entries = [
        _entry("a", ["bloco:bloco-01"]),
        _entry("b", ["unit:u1"]),          # sem bloco -> orfao
        _entry("c", ["bloco:bloco-02"], ftype="image"),
    ]
    rep = material_coverage(entries)
    assert rep["total"] == 3
    assert rep["with_block"] == 2
    assert rep["orphans"] == 1
    assert round(rep["coverage"], 2) == 0.67
    assert rep["by_type"]["pdf"]["with_block"] == 1
    assert rep["by_type"]["image"]["with_block"] == 1


def test_coverage_manual_block_counts():
    entries = [{"id": "m", "manual_timeline_block_id": "bloco-03", "auto_tags": [], "file_type": "pdf"}]
    rep = material_coverage(entries)
    assert rep["with_block"] == 1


from src.builder.artifacts.cronograma_health import cronograma_health_md


def test_health_md_renders_metrics():
    entries = [
        {"id": "a", "auto_tags": ["bloco:bloco-01"], "file_type": "pdf", "category": "material-de-aula"},
        {"id": "b", "auto_tags": [], "file_type": "image", "category": "material-de-aula"},
    ]
    blocks = [{"id": "bloco-01"}, {"id": "bloco-02"}]
    md = cronograma_health_md({"name": "X"}, entries, blocks)
    assert "Cobertura" in md
    assert "50%" in md
    assert "bloco-02" in md  # bloco pobre (0 materiais) listado


from src.builder.artifacts.cronograma_health import band_distribution


def test_band_distribution_counts():
    entries = [
        {"id": "a", "computed_block_id": "b1", "computed_block_band": "alta", "category": "material-de-aula"},
        {"id": "b", "computed_block_id": "b1", "computed_block_band": "media", "category": "material-de-aula"},
        {"id": "c", "computed_block_id": "b2", "computed_block_band": "baixa", "category": "material-de-aula"},
        {"id": "d", "computed_block_id": "b2", "computed_block_band": "baixa", "category": "material-de-aula"},
        {"id": "e", "computed_block_id": "", "computed_block_band": "", "category": "material-de-aula"},  # orfao
    ]
    dist = band_distribution(entries)
    assert dist["alta"] == 1
    assert dist["media"] == 1
    assert dist["baixa"] == 2


def test_health_md_reports_band_distribution_and_low_confidence_list():
    entries = [
        {"id": "hi", "title": "Recursao", "computed_block_id": "bloco-01",
         "computed_block_band": "alta", "category": "material-de-aula", "file_type": "pdf"},
        {"id": "lo", "title": "Material generico", "computed_block_id": "bloco-01",
         "computed_block_confidence": 0.18, "computed_block_band": "baixa",
         "category": "material-de-aula", "file_type": "pdf",
         "raw_target": "raw/material.pdf"},
    ]
    blocks = [
        {"id": "bloco-01", "period_label": "Semana 01", "administrative_only": False,
         "rows": [{"index": 1, "content": "Aula sobre recursao"}]},
        {"id": "bloco-02", "period_label": "Semana 02", "administrative_only": False,
         "rows": [{"index": 1, "content": "Aula sobre inducao"}]},
    ]
    md = cronograma_health_md({"name": "X"}, entries, blocks)
    # distribuicao de faixas
    assert "alta" in md and "media" in md and "baixa" in md
    # lista de baixa-confianca acionavel: cita o material baixa
    assert "Material generico" in md
    # top-N candidatos: cita ao menos um id de bloco candidato com score
    assert "bloco-0" in md


def test_health_md_marks_manual_vs_auto():
    entries = [
        {"id": "m", "title": "Manual mat", "manual_timeline_block_id": "bloco-01",
         "computed_block_id": "bloco-02", "computed_block_band": "baixa",
         "computed_block_confidence": 0.1, "category": "material-de-aula", "file_type": "pdf"},
    ]
    blocks = [
        {"id": "bloco-01", "period_label": "S1", "administrative_only": False, "rows": [{"index": 1, "content": "x"}]},
        {"id": "bloco-02", "period_label": "S2", "administrative_only": False, "rows": [{"index": 1, "content": "y"}]},
    ]
    md = cronograma_health_md({"name": "X"}, entries, blocks)
    assert "manual" in md.lower()


import json
from scripts.validate_materials import coverage_gate_failures


def test_gate_flags_low_coverage():
    entries = [{"id": "a", "auto_tags": [], "file_type": "pdf", "category": "material-de-aula"}]
    fails = coverage_gate_failures(entries)
    assert any("cobertura" in f for f in fails)


def test_gate_passes_high_coverage():
    entries = [{"id": "a", "auto_tags": ["bloco:bloco-01"], "file_type": "pdf", "category": "material-de-aula"}]
    assert coverage_gate_failures(entries) == []
