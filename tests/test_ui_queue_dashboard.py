from pathlib import Path

from src.ui.dialogs import HELP_SECTIONS
from src.ui.curator_studio import (
    _curator_studio_layout_mode,
    _curator_review_paths,
    _preview_page_indices,
    _read_curator_source_text,
)


def test_help_sections_do_not_reference_quick_import():
    joined = "\n".join(body for _title, body in HELP_SECTIONS)
    assert "Importação rápida" not in joined


def test_app_no_longer_declares_quick_import_toggle():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "_quick_import" not in text
    assert "Importação rápida" not in text


def test_readme_mentions_repo_tasks_and_dashboard():
    text = Path("README.md").read_text(encoding="utf-8")
    lower = text.lower()
    assert "Tasks de Repositório" in text
    assert "Dashboard" in text
    assert "desligar ao concluir build/fila" in lower or "fila é persistente" in lower


def test_curator_studio_layout_mode_changes_by_width():
    assert _curator_studio_layout_mode(1500) == "wide"
    assert _curator_studio_layout_mode(1100) == "medium"
    assert _curator_studio_layout_mode(820) == "stacked"


def test_curator_review_paths_excludes_code_manual_review(tmp_path):
    repo = tmp_path / "repo"
    (repo / "manual-review" / "pdfs").mkdir(parents=True)
    (repo / "manual-review" / "images").mkdir(parents=True)
    (repo / "manual-review" / "code").mkdir(parents=True)

    pdf_review = repo / "manual-review" / "pdfs" / "a.md"
    img_review = repo / "manual-review" / "images" / "b.md"
    code_review = repo / "manual-review" / "code" / "c.md"
    pdf_review.write_text("x", encoding="utf-8")
    img_review.write_text("x", encoding="utf-8")
    code_review.write_text("x", encoding="utf-8")

    result = _curator_review_paths(repo)

    assert pdf_review in result
    assert img_review in result
    assert code_review not in result


def test_curator_review_paths_excludes_legacy_url_fetcher_reviews_in_pdfs(tmp_path):
    repo = tmp_path / "repo"
    (repo / "manual-review" / "pdfs").mkdir(parents=True)

    legacy_url_review = repo / "manual-review" / "pdfs" / "url-item.md"
    legacy_url_review.write_text(
        """---
id: url-item
title: Example
type: manual_pdf_review
base_backend: url_fetcher
source_pdf: null
---
""",
        encoding="utf-8",
    )

    real_pdf_review = repo / "manual-review" / "pdfs" / "pdf-item.md"
    real_pdf_review.write_text(
        """---
id: pdf-item
title: PDF
type: manual_pdf_review
base_backend: pymupdf4llm
source_pdf: raw/pdfs/aula.pdf
---
""",
        encoding="utf-8",
    )

    result = _curator_review_paths(repo)

    assert real_pdf_review in result
    assert legacy_url_review not in result


def test_preview_page_indices_limits_large_pdf_previews():
    assert _preview_page_indices(0) == []
    assert _preview_page_indices(3) == [0, 1, 2]
    assert _preview_page_indices(10) == [0, 1, 2, 3, 4, 5]


def test_read_curator_source_text_truncates_large_markdown(tmp_path):
    source = tmp_path / "large.md"
    source.write_text("A" * 20, encoding="utf-8")

    content, truncated = _read_curator_source_text(source, max_bytes=8)

    assert content == "A" * 8
    assert truncated is True


def test_app_source_no_longer_contains_dead_duplicate_action():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "def duplicate_selected(" not in text


def test_dialogs_source_no_longer_contains_unused_markdown_preview_window():
    text = Path("src/ui/dialogs.py").read_text(encoding="utf-8")
    assert "class MarkdownPreviewWindow" not in text


def test_file_entry_dialog_keeps_profile_and_tags_on_separate_rows():
    text = Path("src/ui/dialogs.py").read_text(encoding="utf-8")
    profile_idx = text.index('lbl_profile = ttk.Label(outer, text="Perfil")')
    tags_idx = text.index('lbl_tags = ttk.Label(outer, text="Tags")')
    layout_slice = text[profile_idx:tags_idx]

    assert 'combo_profile.grid(row=row, column=1, sticky="ew")' in layout_slice
    assert "row += 1" in layout_slice


def test_single_processing_pause_button_uses_grid_not_pack():
    text = Path("src/ui/app.py").read_text(encoding="utf-8")
    state_slice = text[text.index("def _set_processing_state"):text.index("def _cancel_single")]

    assert 'self._btn_pause.grid(row=1, column=1, sticky="ew", padx=4, pady=4)' in state_slice
    assert "self._btn_pause.grid_remove()" in state_slice
    assert "self._btn_pause.pack(" not in state_slice
    assert "self._btn_pause.pack_forget()" not in state_slice
