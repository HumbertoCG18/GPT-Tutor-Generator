from pathlib import Path

from src.ui.app import (
    _end_progress_bar,
    _set_progress_bar_paused,
    _start_progress_bar,
    _step_progress_bar,
)
from src.ui.dialogs import HELP_SECTIONS
from src.ui.theme import AppConfig
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


class _FakeProgressbar:
    def __init__(self):
        self.values = {"mode": "determinate", "value": 0, "maximum": 100}
        self.calls = []

    def configure(self, **values):
        self.values.update(values)
        self.calls.append(("configure", values))

    def pack(self, **values):
        self.calls.append(("pack", values))

    def pack_forget(self):
        self.calls.append(("pack_forget", {}))

    def start(self, interval=None):
        self.calls.append(("start", interval))

    def stop(self):
        self.calls.append(("stop", {}))
        self.values["value"] = 0

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value


def test_unknown_progress_uses_native_indeterminate_for_slow_operation():
    progress_bar = _FakeProgressbar()

    _start_progress_bar(progress_bar, 0, reduce_motion=False)

    assert progress_bar["mode"] == "indeterminate"
    assert ("start", 50) in progress_bar.calls


def test_reduce_motion_keeps_unknown_progress_visible_but_static():
    progress_bar = _FakeProgressbar()

    _start_progress_bar(progress_bar, 0, reduce_motion=True)

    assert progress_bar["mode"] == "indeterminate"
    assert not any(call == "start" for call, _value in progress_bar.calls)
    assert any(call == "pack" for call, _value in progress_bar.calls)


def test_known_progress_is_determinate_and_updates_real_denominator():
    progress_bar = _FakeProgressbar()

    _start_progress_bar(progress_bar, 4, reduce_motion=False)
    _step_progress_bar(progress_bar, 1, 4)

    assert progress_bar["mode"] == "determinate"
    assert progress_bar["maximum"] == 4
    assert progress_bar["value"] == 2
    assert not any(call == "start" for call, _value in progress_bar.calls)


def test_success_error_or_cancellation_stops_and_hides_progress():
    progress_bar = _FakeProgressbar()
    _start_progress_bar(progress_bar, 0, reduce_motion=False)
    progress_bar.calls.clear()

    _end_progress_bar(progress_bar)

    assert progress_bar.calls == [("stop", {}), ("pack_forget", {})]
    assert progress_bar["value"] == 0


def test_indeterminate_progress_pause_and_resume_respects_reduce_motion():
    progress_bar = _FakeProgressbar()
    progress_bar.values["mode"] = "indeterminate"

    _set_progress_bar_paused(progress_bar, True, reduce_motion=False)
    _set_progress_bar_paused(progress_bar, False, reduce_motion=False)
    assert progress_bar.calls == [("stop", {}), ("stop", {}), ("start", 50)]

    reduced = _FakeProgressbar()
    reduced.values["mode"] = "indeterminate"
    _set_progress_bar_paused(reduced, False, reduce_motion=True)
    assert reduced.calls == [("stop", {})]
    assert reduced["value"] == 50


def test_reduce_motion_preference_persists(tmp_path, monkeypatch):
    import src.ui.theme as theme_module

    config_path = tmp_path / "config.json"
    monkeypatch.setattr(theme_module, "CONFIG_PATH", config_path)
    config = AppConfig()
    assert config.get("reduce_motion") is False

    config.set("reduce_motion", True)
    config.save()

    assert AppConfig().get("reduce_motion") is True


def test_settings_dialog_wires_reduce_motion_without_fake_after_loop():
    dialog_source = Path("src/ui/dialogs.py").read_text(encoding="utf-8")
    app_source = Path("src/ui/app.py").read_text(encoding="utf-8")

    assert "self._var_reduce_motion" in dialog_source
    assert 'self.config.set("reduce_motion"' in dialog_source
    assert "self.parent._apply_reduce_motion_preference()" in dialog_source
    assert "def _tick_fake_indeterminate" not in app_source
    assert "self.after(40, self._tick_fake_indeterminate)" not in app_source


def test_moodle_busy_progress_respects_reduce_motion():
    from src.ui.dialogs import _start_busy_progress

    animated = _FakeProgressbar()
    _start_busy_progress(animated, reduce_motion=False)
    assert animated["mode"] == "indeterminate"
    assert ("start", 12) in animated.calls

    static = _FakeProgressbar()
    _start_busy_progress(static, reduce_motion=True)
    assert static["mode"] == "indeterminate"
    assert static["value"] == 50
    assert not any(call == "start" for call, _value in static.calls)


def test_reduce_motion_read_from_app_root_config():
    from types import SimpleNamespace
    from src.ui.dialogs import _reduce_motion_enabled

    config = SimpleNamespace(get=lambda key, default=None: key == "reduce_motion")
    widget = SimpleNamespace(_root=lambda: SimpleNamespace(config_obj=config))
    assert _reduce_motion_enabled(widget) is True
    assert _reduce_motion_enabled(SimpleNamespace(_root=lambda: object())) is False


def test_theme_preview_keeps_unsaved_reduce_motion():
    from types import SimpleNamespace
    from src.ui.dialogs import _settings_rebuild_kwargs

    dialog = SimpleNamespace(_var_reduce_motion=SimpleNamespace(get=lambda: True))
    assert _settings_rebuild_kwargs(dialog) == {"reduce_motion": True}
