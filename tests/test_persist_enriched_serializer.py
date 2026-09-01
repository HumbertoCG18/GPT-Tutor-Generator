"""Serializador UNICO de producao (persist_enriched_timeline_index).

Cutover passo 3 (2026-08-17): o fantasma _serialize_timeline_index (v4,
filtrava admin, so-testes) foi DELETADO e a versao unificou em 4 (item 8a) —
mesma do schema (validate_timeline, const 4) e de TIMELINE_INDEX_VERSION.
O guard abaixo impede reintroducao do fantasma.
"""
import ast
from pathlib import Path

from src.builder.core.core_utils import persist_enriched_timeline_index


def test_producao_preserva_blocos_admin_e_versao_4():
    idx = {"version": 3, "blocks": [
        {"id": "bloco-01", "kind": "class", "rows": [1], "unit_slug": "u1"},
        {"id": "bloco-02", "kind": "assessment", "rows": [2], "unit_slug": ""},
        {"id": "bloco-03", "kind": "holiday", "rows": [3], "unit_slug": ""},
    ]}
    out = persist_enriched_timeline_index(idx)
    assert out["version"] == 4  # bump 8a: unificado com o schema v4
    assert [b["id"] for b in out["blocks"]] == ["bloco-01", "bloco-02", "bloco-03"]  # admin NAO filtrado
    assert all("rows" not in b for b in out["blocks"])  # rows removidas
    assert out["blocks"][0]["unit_slug"] == "u1"        # kind/unit passthrough (sem reclassificar)


def test_fantasma_morto_nao_reintroduzido():
    """_serialize_timeline_index morreu no cutover passo 3 — nenhuma referencia
    pode voltar em src/."""
    offenders = []
    for py in Path("src").rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Name) and n.id == "_serialize_timeline_index" for n in ast.walk(tree)):
            offenders.append(py.as_posix())
    assert offenders == [], f"serializador fantasma reintroduzido: {offenders}"
