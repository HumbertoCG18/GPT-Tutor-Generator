"""#63: salvar matéria existente no Gerenciador de Matérias preserva feature_flags.

Chama o `_save` real do diálogo com um `self` mínimo (sem Tk): formulário preenchido
como `_on_select` faz, store em memória e messagebox neutralizado.
"""
from types import SimpleNamespace

import src.ui.dialogs as dialogs
from src.models.core import SubjectProfile

_FORM_KEYS = (
    "name", "slug", "professor", "institution", "semester", "schedule", "default_mode",
    "default_ocr_lang", "default_backend", "default_datalab_mode", "repo_root", "stash_folder",
    "github_url", "preferred_llm", "processing_profile",
)


class _Store:
    def __init__(self, *profiles):
        self.data = {p.name: p for p in profiles}

    def get(self, name):
        return self.data.get(name)

    def add(self, profile):
        self.data[profile.name] = profile


def _save_form(store, profile, monkeypatch):
    monkeypatch.setattr(dialogs.messagebox, "showinfo", lambda *a, **k: None)
    text = lambda value: SimpleNamespace(get=lambda *_a, _v=value: _v)  # noqa: E731
    fake = SimpleNamespace(
        _vars={k: SimpleNamespace(get=lambda _v=str(getattr(profile, k, "")): _v) for k in _FORM_KEYS},
        _syllabus_text=text(profile.syllabus),
        _teaching_plan_text=text(profile.teaching_plan),
        _imported_schedule_url="",
        _store=store,
        _refresh_list=lambda: None,
    )
    dialogs.SubjectManagerDialog._save(fake)
    return store.get(profile.name)


def test_save_existing_subject_keeps_feature_flags_identical(monkeypatch):
    flags = {"use_anchor_engine": True, "use_llm_voter": False, "compile_vocabulary": True}
    existing = SubjectProfile(name="MF", slug="mf", feature_flags=dict(flags))
    store = _Store(existing)

    saved = _save_form(store, existing, monkeypatch)

    assert saved is not existing
    assert saved.feature_flags == flags


def test_save_new_subject_gets_only_d9(monkeypatch):
    """#65: matéria nova nasce com o D9 explícito e nada mais (sem votador, vocabulário, resíduo)."""
    store = _Store()

    saved = _save_form(store, SubjectProfile(name="Nova", slug="nova"), monkeypatch)

    assert saved.feature_flags == {"use_anchor_engine": True}


def test_save_existing_subject_is_not_migrated_to_d9(monkeypatch):
    """#65: perfis existentes com {} ou False explícito ficam como estão."""
    for flags in ({}, {"use_anchor_engine": False}):
        existing = SubjectProfile(name="Velha", slug="velha", feature_flags=dict(flags))
        saved = _save_form(_Store(existing), existing, monkeypatch)
        assert saved.feature_flags == flags
