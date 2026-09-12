"""`find_by_repo_root` tem que casar caminho RELATIVO com o repo_root absoluto do
subjects.json (02/09: `reprocess_assignments.py ../X-Tutor` nao achava o perfil,
o plano parseava 0 unidades e o guard UnitsShrinkError abortava a rodada)."""
import os

from src.models.core import SubjectProfile, SubjectStore


def _store_com(repo_root: str) -> SubjectStore:
    store = SubjectStore.__new__(SubjectStore)  # sem load() do subjects.json real
    store._data = {"X": SubjectProfile(name="X", repo_root=repo_root)}
    return store


def test_find_by_repo_root_aceita_caminho_relativo(tmp_path, monkeypatch):
    repo = tmp_path / "X-Tutor"
    repo.mkdir()
    store = _store_com(str(repo))
    monkeypatch.chdir(tmp_path)
    assert store.find_by_repo_root(os.path.join("..", tmp_path.name, "X-Tutor")) is store._data["X"]


def test_find_by_repo_root_sem_match_devolve_none(tmp_path):
    store = _store_com(str(tmp_path / "X-Tutor"))
    assert store.find_by_repo_root(tmp_path / "Y-Tutor") is None
