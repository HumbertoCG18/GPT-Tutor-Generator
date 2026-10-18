import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore, SubjectProfile


def _store_with(tmp_path, repo_root: str) -> SubjectStore:
    store = SubjectStore.__new__(SubjectStore)
    sp = SubjectProfile(name="Metodos Formais")
    sp.repo_root = repo_root
    store._data = {"Metodos Formais": sp}
    return store


def test_find_by_repo_root_casefold_e_separadores(tmp_path):
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    store = _store_with(tmp_path, str(repo).replace("\\", "/").upper() + "/")
    found = store.find_by_repo_root(repo)
    assert found is not None and found.name == "Metodos Formais"


def test_find_by_repo_root_sem_match_devolve_none(tmp_path):
    repo = tmp_path / "Outro-Tutor"
    repo.mkdir()
    store = _store_with(tmp_path, str(tmp_path / "MF-Tutor"))
    assert store.find_by_repo_root(repo) is None


def test_reprocess_passa_subject_profile_ao_builder(tmp_path, monkeypatch):
    import scripts.reprocess_assignments as ra
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    (repo / "manifest.json").write_text(json.dumps({"course": {}, "options": {}, "entries": []}), encoding="utf-8")
    sp = SubjectProfile(name="Metodos Formais")
    sp.repo_root = str(repo)
    store = SubjectStore.__new__(SubjectStore)
    store._data = {"Metodos Formais": sp}
    captured = {}

    class FakeBuilder:
        def __init__(self, **kw):
            captured.update(kw)
        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", FakeBuilder)
    ra.reprocess(repo, flags=[], store=store)
    assert captured.get("subject_profile") is sp


def test_reprocess_sem_perfil_builder_recebe_none(tmp_path, monkeypatch):
    import scripts.reprocess_assignments as ra
    repo = tmp_path / "Solto-Tutor"
    repo.mkdir()
    (repo / "manifest.json").write_text(json.dumps({"course": {}, "options": {}, "entries": []}), encoding="utf-8")
    store = SubjectStore.__new__(SubjectStore)
    store._data = {}
    captured = {}

    class FakeBuilder:
        def __init__(self, **kw):
            captured.update(kw)
        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", FakeBuilder)
    ra.reprocess(repo, flags=[], store=store)
    assert captured.get("subject_profile") is None
