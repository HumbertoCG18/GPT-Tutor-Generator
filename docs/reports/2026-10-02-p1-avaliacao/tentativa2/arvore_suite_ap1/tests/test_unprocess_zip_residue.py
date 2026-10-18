"""unprocess de um ZIP deve limpar também os assets dos filhos (extracted_files),
sem deixar resíduo em disco. Testa o coletor de paths _entry_asset_paths."""
from src.builder.ops.lifecycle_ops import _entry_asset_paths


def test_inclui_paths_do_proprio_entry():
    e = {"raw_target": "raw/zip/x.zip", "base_markdown": "code/professor/x.md"}
    paths = _entry_asset_paths(e)
    assert "raw/zip/x.zip" in paths
    assert "code/professor/x.md" in paths


def test_inclui_filhos_de_zip():
    e = {
        "raw_target": "raw/zip/pacote.zip",
        "extracted_files": [
            {
                "base_markdown": "code/professor/a.md",
                "raw_target": "raw/code/professor/a.py",
                "manual_review": "manual-review/code/a.md",
            },
            {"base_markdown": "code/professor/b.md"},
        ],
    }
    paths = _entry_asset_paths(e)
    for p in (
        "raw/zip/pacote.zip",
        "code/professor/a.md",
        "raw/code/professor/a.py",
        "manual-review/code/a.md",
        "code/professor/b.md",
    ):
        assert p in paths, p


def test_ignora_extracted_files_nao_dict():
    e = {"raw_target": "raw/zip/x.zip", "extracted_files": ["lixo", None, 3]}
    assert _entry_asset_paths(e) == ["raw/zip/x.zip"]


def test_sem_extracted_files():
    assert _entry_asset_paths({"raw_target": "raw/pdf/y.pdf"}) == ["raw/pdf/y.pdf"]
