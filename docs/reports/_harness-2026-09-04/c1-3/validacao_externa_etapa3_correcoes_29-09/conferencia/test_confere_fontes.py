"""CONF01: o resultado global da conferência tem de incorporar o selo do inventário. Árvore sintética, sem fontes reais."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confere_fontes as C  # noqa: E402


def sha(b):
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def lote(tmp_path, monkeypatch):
    fontes, e2, saida = tmp_path / "fontes", tmp_path / "e2", tmp_path / "saida"
    raiz = fontes / "c1"
    api = [{"section": 0, "name": "S", "modules": [{"id": 1, "modname": "resource", "contents": [{"type": "file", "filename": "a.txt"}]}]}]
    for rel, b in {"raw/moodle/contents.json": json.dumps(api).encode(), "stash/S/a.txt": b"aula"}.items():
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_bytes(b)
    inv = {"cursos": [{"id": "c1", "arquivos": [{"modulo_id": "1", "modname": "resource", "arquivo": "a.txt", "caminho": "stash/S/a.txt",
                                                "sha256": sha(b"aula"), "status": "ok", "tamanho_api": 4}]}], "parada": "fim"}
    e2.mkdir()
    (e2 / "inventario_downloads.json").write_text(json.dumps(inv), encoding="utf-8")
    arvore = {p.relative_to(raiz).as_posix(): sha(p.read_bytes()) for p in raiz.rglob("*") if p.is_file()}
    (e2 / "fontes_congeladas.json").write_text(json.dumps({"inventario_sha256": sha((e2 / "inventario_downloads.json").read_bytes()),
                                                           "cursos": {"c1": {"arvore": arvore}}}), encoding="utf-8")
    saida.mkdir()
    for nome, valor in (("E2", e2), ("FONTES", fontes), ("AQUI", saida)):
        monkeypatch.setattr(C, nome, valor)
    return e2, saida


def resumo(saida):
    return json.loads((saida / "conferencia_fontes.json").read_text(encoding="utf-8"))["resumo"]


def test_controle_integridade_global_verdadeira(lote):
    _, saida = lote
    C.main()
    assert resumo(saida)["integridade_global"] is True


def test_CONF01_inventario_alterado_derruba_o_resultado_global(lote):
    e2, saida = lote
    inv = json.loads((e2 / "inventario_downloads.json").read_text(encoding="utf-8"))
    inv["parada"] = "alterada depois do congelamento"   # só metadado; bytes e registros continuam certos
    (e2 / "inventario_downloads.json").write_text(json.dumps(inv), encoding="utf-8")
    C.main()
    r = resumo(saida)
    assert r["bytes_conferem"] is True and r["inventario_completo"] is True
    assert r["integridade_global"] is False and r["inventario_confere_com_congelamento"] is False
