import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest  # noqa: E402

import reprocess_assignments as ra  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_config_real(tmp_path, monkeypatch):
    """AppConfig le ~/.gpt_tutor_config.json; nenhum teste daqui depende da config do usuario."""
    monkeypatch.setattr("src.ui.theme.CONFIG_PATH", tmp_path / "sem_config.json")


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
    """Duck-type de SubjectStore (.names()/.get()/.find_by_repo_root()) sem tocar o filesystem real."""

    def __init__(self, profiles):
        self._data = {p.name: p for p in profiles}

    def names(self):
        return list(self._data.keys())

    def get(self, name):
        return self._data.get(name)

    def find_by_repo_root(self, repo_root):
        target = str(repo_root).replace("\\", "/").rstrip("/").casefold()
        for name in self.names():
            sp = self.get(name)
            rr = str(getattr(sp, "repo_root", "") or "").replace("\\", "/").rstrip("/").casefold()
            if rr and rr == target:
                return sp
        return None


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
        def __init__(self, root_dir, course_meta, entries, options, **kwargs):
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
        def __init__(self, root_dir, course_meta, entries, options, **kwargs):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    store = _FakeStore([_FakeProfile("MF", str(repo), {"use_anchor_engine": False})])

    ra.reprocess(repo, ["use_anchor_engine"], store=store)

    assert captured["options"]["use_anchor_engine"] is True


def test_reprocess_options_do_manifest_reproduz_derivacao_antiga(tmp_path, monkeypatch):
    """#64: a base manifest["options"] so vale com pedido explicito (from_manifest=True).
    Sem subjects.json (SubjectStore real, app-data-dir vazio): options ficam exatamente
    como manifest.json + --flags, a derivacao de antes."""
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    manifest_path = repo / "manifest.json"
    manifest_path.write_text('{"course": {}, "options": {"image_format": "png"}, "entries": []}', encoding="utf-8")

    captured = {}

    class _StubBuilder:
        def __init__(self, root_dir, course_meta, entries, options, **kwargs):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    empty_app_data_dir = tmp_path / "app_data_empty"
    empty_app_data_dir.mkdir()
    monkeypatch.setattr("src.models.core.get_app_data_dir", lambda: empty_app_data_dir)

    ra.reprocess(repo, [], store=None, from_manifest=True)

    assert captured["options"] == {"image_format": "png"}


def _capture_reprocess(tmp_path, monkeypatch, manifest_options, profile, **kwargs):
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    (repo / "manifest.json").write_text(
        json.dumps({"course": {}, "options": manifest_options, "entries": []}), encoding="utf-8")
    profile.repo_root = str(repo)
    captured = {}

    class _StubBuilder:
        def __init__(self, root_dir, course_meta, entries, options, **kw):
            captured["options"] = options

        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", _StubBuilder)
    ra.reprocess(repo, [], store=_FakeStore([profile]), **kwargs)
    return captured["options"]


def test_reprocess_default_nao_herda_flags_do_manifest(tmp_path, monkeypatch):
    """#64: options historicas do manifest (D9/voter ligados no build original) nao
    religam nada quando o perfil vivo nao pede."""
    profile = _FakeProfile("MF", "", {})
    opts = _capture_reprocess(tmp_path, monkeypatch, {"use_anchor_engine": True, "use_llm_voter": True}, profile)
    assert "use_anchor_engine" not in opts and "use_llm_voter" not in opts


def test_app_build_options_igual_ao_script_para_o_mesmo_perfil(tmp_path, monkeypatch):
    """#64: App._build_options (metodo real) == options do script para o mesmo perfil + repo.
    Matéria do repo ativa: a ativacao preenche modo/OCR com os defaults dela. Outra matéria
    ativa: flags e modo/OCR seguem o perfil do repo, nao os controles da ativa."""
    from types import SimpleNamespace
    from src.models.core import SubjectProfile
    from src.ui.app import App
    from src.ui.theme import AppConfig

    sp = SubjectProfile(name="MF", default_mode="manual_assisted", default_ocr_lang="por",
                        feature_flags={"use_anchor_engine": True, "use_llm_voter": False})
    script = _capture_reprocess(tmp_path, monkeypatch, {"use_llm_voter": True}, sp)
    assert script["use_llm_voter"] is False

    def _ui(active, mode, ocr):
        var = lambda v: SimpleNamespace(get=lambda: v)  # noqa: E731
        return SimpleNamespace(var_default_mode=var(mode), var_default_ocr_language=var(ocr),
                               config_obj=AppConfig(), _var_active_subject=var(active))

    assert App._build_options(_ui("MF", sp.default_mode, sp.default_ocr_lang), sp) == script
    assert App._build_options(_ui("SO", "auto", "eng"), sp) == script


def test_reprocess_respeita_patch_de_merge_profile_flags(tmp_path, monkeypatch):
    """scripts/motor_puro.py desliga o voter trocando ra._merge_profile_flags; a derivacao
    nova tem de continuar passando por ele (senao o voter religa por efeito colateral)."""
    original = ra._merge_profile_flags

    def _sem_voter(options, profile):
        original(options, profile)
        options["use_llm_voter"] = False

    monkeypatch.setattr(ra, "_merge_profile_flags", _sem_voter)
    profile = _FakeProfile("MF", "", {"use_anchor_engine": True, "use_llm_voter": True})
    opts = _capture_reprocess(tmp_path, monkeypatch, {}, profile)
    assert opts["use_anchor_engine"] is True and opts["use_llm_voter"] is False
