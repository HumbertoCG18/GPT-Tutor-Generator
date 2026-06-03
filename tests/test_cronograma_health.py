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
