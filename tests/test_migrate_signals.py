import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.migrate_signals import migrate_repo_additive, _resolve_year


class _FakeClient:
    def __init__(self, courses): self._courses = courses
    def site_info(self): return {"userid": 7}
    def get_users_courses(self, userid): return self._courses


def test_resolve_year_sarc_wins():
    c = _FakeClient([])
    y = _resolve_year(c, "92717",
                      "https://sarc.pucrs.br/Default/Export.aspx?id=g&ano=2026&sem=1", "")
    assert y == "2026"

def test_resolve_year_arg_when_no_sarc():
    assert _resolve_year(_FakeClient([]), "92717", "", "2025") == "2025"

def test_resolve_year_autoderive_from_course():
    courses = [{"id": 92717, "fullname": "X - Metodos - Turma 031 - 2026/1 - Prof. Y"}]
    assert _resolve_year(_FakeClient(courses), "92717", "", "") == "2026"

def test_resolve_year_unresolved_empty():
    assert _resolve_year(_FakeClient([]), "99999", "", "") == ""

_CONTENTS = [{"name": "S1", "modules": [
    {"name": "L", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u",
                                "timemodified": 1739361600, "timecreated": 1739000000}]}]}]

def test_dry_run_does_not_write(tmp_path):
    repo = tmp_path / "r"; (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps(
        {"entries": [{"id": "e1", "source_path": "main.pdf"}]}), encoding="utf-8")
    migrate_repo_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=False)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert "posting_date" not in m["entries"][0]            # dry-run nao grava
    assert not (repo / "manifest.json.apibak").exists()

def test_write_makes_backup_and_sets_posting(tmp_path):
    repo = tmp_path / "r"; (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps(
        {"entries": [{"id": "e1", "source_path": "main.pdf"}]}), encoding="utf-8")
    migrate_repo_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    assert (repo / "manifest.json.apibak").exists()
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert m["entries"][0]["posting_date"] == "2025-02-12"
