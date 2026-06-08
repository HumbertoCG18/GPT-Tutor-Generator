from pathlib import Path
from src.builder.core.stash_import import scan_stash_cards
from src.builder.core.stash_backfill import match_entries_to_cards


def _make_tree(root: Path):
    (root / "Verificacao de Programas").mkdir(parents=True)
    (root / "Verificacao de Programas" / "hoare.pdf").write_text("x", encoding="utf-8")
    (root / "Introducao").mkdir()
    (root / "Introducao" / "slides.pdf").write_text("x", encoding="utf-8")
    (root / "Bibliografia").mkdir()
    (root / "Bibliografia" / "hoare.pdf").write_text("x", encoding="utf-8")  # dup basename


def test_match_assigns_unique_basenames(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    entries = [
        {"id": "slides", "source_path": "C:/old/slides.pdf"},
        {"id": "hoare", "source_path": "D:/whatever/hoare.pdf"},
        {"id": "ghost", "source_path": "X:/none/ghost.pdf"},
    ]
    assignments, unmatched, ambiguous = match_entries_to_cards(entries, scan)
    assert assignments["slides"] == "Introducao"
    assert "hoare" in ambiguous
    assert "hoare" not in assignments
    assert "ghost" in unmatched
