import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reprocess_assignments as ra  # noqa: E402


def test_apply_flags_marca_true_e_preserva_options():
    opts = {"image_format": "png"}
    ra._apply_flags(opts, ["use_anchor_engine", "use_llm_voter"])
    assert opts["use_anchor_engine"] is True
    assert opts["use_llm_voter"] is True
    assert opts["image_format"] == "png"


def test_apply_flags_vazio_nao_muda_nada():
    opts = {"a": 1}
    ra._apply_flags(opts, [])
    assert opts == {"a": 1}


def test_parse_argv_com_flags():
    flags, pats = ra._parse_argv(["--flags", "use_anchor_engine,use_llm_voter", "C:/x"])
    assert flags == ["use_anchor_engine", "use_llm_voter"]
    assert pats == ["C:/x"]


def test_parse_argv_sem_flags_e_retrocompativel():
    flags, pats = ra._parse_argv(["C:/x", "C:/y"])
    assert flags == []
    assert pats == ["C:/x", "C:/y"]


class _FakeProfile:
    def __init__(self, name, repo_root, feature_flags):
        self.name = name
        self.repo_root = repo_root
        self.feature_flags = feature_flags


class _FakeStore:
    """Duck-type de SubjectStore (.names()/.get()) sem tocar o filesystem real."""

    def __init__(self, profiles):
        self._data = {p.name: p for p in profiles}

    def names(self):
        return list(self._data.keys())

    def get(self, name):
        return self._data.get(name)


def test_find_subject_profile_by_resolved_repo_root(tmp_path):
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    profile = _FakeProfile("MF", str(repo), {"use_anchor_engine": True})
    store = _FakeStore([profile])
    found = ra._find_subject_profile(repo, store)
    assert found is profile


def test_find_subject_profile_no_match_returns_none(tmp_path):
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    other = tmp_path / "SO-Tutor"
    other.mkdir()
    store = _FakeStore([_FakeProfile("SO", str(other), {"use_anchor_engine": True})])
    assert ra._find_subject_profile(repo, store) is None


def test_reprocess_profile_on_injects_flags_when_no_cli_flags(tmp_path, monkeypatch):
    """Perfil vivo com feature_flags ON injeta nas options quando --flags nao foi passado
    (a armadilha operacional do handoff: reprocess sem --flags nao cai mais em flag-OFF)."""
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    manifest_path = repo / "manifest.json"
    manifest_path.write_text('{"course": {}, "options": {}, "entries": []}', encoding="utf-8")

    captured = {}

    class _StubBuilder:
        def __init__(self, root_dir, course_meta, entries, options):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    store = _FakeStore([_FakeProfile("MF", str(repo), {"use_anchor_engine": True, "use_llm_voter": True})])

    ra.reprocess(repo, [], store=store)

    assert captured["options"]["use_anchor_engine"] is True
    assert captured["options"]["use_llm_voter"] is True


def test_reprocess_cli_flags_override_profile(tmp_path, monkeypatch):
    """CLI --flags continua vencendo mesmo com perfil ON (perfil desliga a flag,
    CLI liga; ordem de aplicacao: perfil primeiro, CLI depois)."""
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    manifest_path = repo / "manifest.json"
    manifest_path.write_text('{"course": {}, "options": {}, "entries": []}', encoding="utf-8")

    captured = {}

    class _StubBuilder:
        def __init__(self, root_dir, course_meta, entries, options):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    store = _FakeStore([_FakeProfile("MF", str(repo), {"use_anchor_engine": False})])

    ra.reprocess(repo, ["use_anchor_engine"], store=store)

    assert captured["options"]["use_anchor_engine"] is True


def test_reprocess_no_subjects_json_behaves_like_today(tmp_path, monkeypatch):
    """Sem subjects.json (SubjectStore real, app-data-dir vazio): options ficam
    exatamente como manifest.json + --flags, igual ao comportamento pre-T18."""
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    manifest_path = repo / "manifest.json"
    manifest_path.write_text('{"course": {}, "options": {"image_format": "png"}, "entries": []}', encoding="utf-8")

    captured = {}

    class _StubBuilder:
        def __init__(self, root_dir, course_meta, entries, options):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    empty_app_data_dir = tmp_path / "app_data_empty"
    empty_app_data_dir.mkdir()
    monkeypatch.setattr("src.models.core.get_app_data_dir", lambda: empty_app_data_dir)

    ra.reprocess(repo, [], store=None)

    assert captured["options"] == {"image_format": "png"}
