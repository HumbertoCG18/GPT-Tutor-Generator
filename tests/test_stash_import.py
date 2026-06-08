from pathlib import Path
from src.builder.core.stash_import import scan_stash_cards, StashItem, build_stash_entries, filter_already_processed
from src.models.core import FileEntry


def _make_tree(root: Path):
    (root / "Verificacao de Programas").mkdir(parents=True)
    (root / "Verificacao de Programas" / "hoare.pdf").write_text("x", encoding="utf-8")
    (root / "Verificacao de Programas" / "hoare.zip").write_bytes(b"PK\x03\x04")
    (root / "Introducao").mkdir()
    (root / "Introducao" / "slides.pdf").write_text("x", encoding="utf-8")
    (root / "Introducao" / "foto.png").write_bytes(b"\x89PNG")
    (root / "solto.pdf").write_text("x", encoding="utf-8")
    (root / "leiame.txt").write_text("x", encoding="utf-8")  # ext desconhecida


def test_scan_groups_files_by_immediate_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}

    assert by_name["hoare.pdf"].card_name == "Verificacao de Programas"
    assert by_name["hoare.pdf"].file_type == "pdf"
    assert by_name["hoare.zip"].card_name == "Verificacao de Programas"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["slides.pdf"].card_name == "Introducao"
    assert by_name["foto.png"].file_type == "image"
    assert by_name["foto.png"].category == "fotos-de-prova"


def test_scan_root_level_file_has_empty_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["solto.pdf"].card_name == ""


def test_scan_skips_unknown_extensions(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    names = {Path(i.source_path).name for i in res.items}
    assert "leiame.txt" not in names
    assert any(Path(p).name == "leiame.txt" for p in res.skipped)


def test_scan_missing_root_returns_empty(tmp_path):
    res = scan_stash_cards(tmp_path / "nao-existe")
    assert res.items == []
    assert res.skipped == []


def test_build_entries_stamps_source_section_and_category(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    entries = build_stash_entries(scan, existing_source_paths=set(),
                                  defaults={"processing_mode": "auto", "ocr_language": "por"})
    by_name = {Path(e.source_path).name: e for e in entries}
    assert by_name["hoare.zip"].source_section == "Verificacao de Programas"
    assert by_name["hoare.zip"].category == "codigo-professor"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["hoare.zip"].title == "hoare"
    assert by_name["hoare.zip"].processing_mode == "auto"
    assert by_name["hoare.zip"].ocr_language == "por"
    assert all(isinstance(e, FileEntry) for e in entries)


def test_build_entries_is_idempotent_by_source_path(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    already = {i.source_path for i in scan.items if Path(i.source_path).name == "hoare.pdf"}
    entries = build_stash_entries(scan, existing_source_paths=already, defaults={})
    names = {Path(e.source_path).name for e in entries}
    assert "hoare.pdf" not in names      # já existia -> pulado
    assert "hoare.zip" in names          # novo -> incluído


def test_filter_already_processed_drops_known_basenames(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, {"hoare.pdf", "slides.pdf"})
    names = {Path(i.source_path).name for i in filtered.items}
    assert "hoare.pdf" not in names
    assert "slides.pdf" not in names
    assert "hoare.zip" in names
    assert filtered.skipped == scan.skipped


def test_filter_already_processed_empty_backlog_is_noop(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    filtered = filter_already_processed(scan, set())
    assert len(filtered.items) == len(scan.items)


def test_scan_nested_file_uses_top_level_card(tmp_path):
    deep = tmp_path / "Provas por Inducao" / "resolucoes"
    deep.mkdir(parents=True)
    (deep / "q1.pdf").write_text("x", encoding="utf-8")
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["q1.pdf"].card_name == "Provas por Inducao"
