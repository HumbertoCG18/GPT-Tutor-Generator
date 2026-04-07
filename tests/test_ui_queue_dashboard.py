from pathlib import Path

from src.ui.dialogs import HELP_SECTIONS
from src.ui.curator_studio import _curator_studio_layout_mode


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
