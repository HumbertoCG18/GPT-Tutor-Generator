"""Serializador de PRODUCAO (persist_enriched_timeline_index) ganha cobertura
propria; o fantasma (_serialize_timeline_index, v4, filtra admin) fica
CONDENADO por guard ate a delecao no cutover. Contratos conferidos em
core_utils.py:14-37 e index.py:813-866 (2026-08-06)."""
import ast
from pathlib import Path

from src.builder.core.core_utils import persist_enriched_timeline_index


def test_producao_preserva_blocos_admin_e_versao_3():
    idx = {"version": 4, "blocks": [
        {"id": "bloco-01", "kind": "class", "rows": [1], "unit_slug": "u1"},
        {"id": "bloco-02", "kind": "assessment", "rows": [2], "unit_slug": ""},
        {"id": "bloco-03", "kind": "holiday", "rows": [3], "unit_slug": ""},
    ]}
    out = persist_enriched_timeline_index(idx)
    assert out["version"] == 3  # hardcode documentado (core_utils.py:35); mudanca so com varredura de leitores
    assert [b["id"] for b in out["blocks"]] == ["bloco-01", "bloco-02", "bloco-03"]  # admin NAO filtrado
    assert all("rows" not in b for b in out["blocks"])  # rows removidas
    assert out["blocks"][0]["unit_slug"] == "u1"        # kind/unit passthrough (sem reclassificar)


def test_fantasma_condenado_sem_caller_de_producao():
    """_serialize_timeline_index morre no cutover; ate la, nenhum caller novo em src/."""
    offenders = []
    for py in Path("src").rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Name) and n.id == "_serialize_timeline_index" for n in ast.walk(tree)):
            offenders.append(py.as_posix())
    allowed = {"src/builder/timeline/index.py", "src/builder/engine.py"}  # def + re-export historico
    assert set(offenders) <= allowed, f"caller novo do serializador condenado: {offenders}"
