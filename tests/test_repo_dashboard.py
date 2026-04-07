import json
from pathlib import Path

from src.models.core import SubjectProfile
from src.models.task_queue import RepoTask
from src.ui.repo_dashboard import collect_repo_metrics


def test_collect_repo_metrics_counts_manifest_manual_review_and_tasks(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "manifest.json").write_text(
        json.dumps({"entries": [{"id": "a"}, {"id": "b"}]}),
        encoding="utf-8",
    )
    manual_review = repo_root / "manual-review"
    manual_review.mkdir()
    (manual_review / "item.md").write_text("x", encoding="utf-8")

    subject = SubjectProfile(
        name="Métodos Formais",
        repo_root=str(repo_root),
        queue=[],
    )
    tasks = [
        RepoTask(task_id="task-1", subject_name="Métodos Formais", repo_root=str(repo_root), action="build_repo"),
        RepoTask(
            task_id="task-2",
            subject_name="Métodos Formais",
            repo_root=str(repo_root),
            action="refresh_repo",
            status="completed",
            finished_at="2026-04-03T10:00:00",
        ),
    ]

    rows = collect_repo_metrics([subject], tasks)

    assert len(rows) == 1
    row = rows[0]
    assert row.subject_name == "Métodos Formais"
    assert row.repo_status == "Manifest pronto"
    assert row.manifest_entries == 2
    assert row.manual_review_items == 1
    assert row.pending_repo_tasks == 1
    assert row.last_task_status == "completed @ 2026-04-03T10:00:00"


def test_collect_repo_metrics_handles_missing_repo():
    subject = SubjectProfile(name="IA", repo_root="", queue=[])

    rows = collect_repo_metrics([subject], [])

    assert len(rows) == 1
    row = rows[0]
    assert row.repo_status == "Sem repositório"
    assert row.manifest_entries == 0
    assert row.pending_repo_tasks == 0
