import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.migrate_signals import migrate_repo_additive

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
