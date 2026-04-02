from pathlib import Path

from src.models.task_queue import RepoTask, RepoTaskStore


def test_task_queue_store_roundtrip(tmp_path: Path):
    store = RepoTaskStore(tmp_path / "repo_tasks.json")
    task = RepoTask(
        task_id="task-001",
        subject_name="Métodos Formais",
        repo_root="C:/Repos/metodos-formais",
        action="build_repo",
        status="pending",
    )

    store.save_all([task])
    loaded = store.load_all()

    assert len(loaded) == 1
    assert loaded[0].task_id == "task-001"
    assert loaded[0].subject_name == "Métodos Formais"
    assert loaded[0].action == "build_repo"
    assert loaded[0].status == "pending"


def test_repo_task_status_transition_updates_timestamps(tmp_path: Path):
    store = RepoTaskStore(tmp_path / "repo_tasks.json")
    task = RepoTask(
        task_id="task-002",
        subject_name="EDA",
        repo_root="C:/Repos/eda",
        action="build_repo",
    )
    task.status = "running"
    task.started_at = "2026-03-31T01:00:00"
    task.status = "completed"
    task.finished_at = "2026-03-31T01:10:00"

    store.save_all([task])
    loaded = store.load_all()[0]

    assert loaded.status == "completed"
    assert loaded.started_at == "2026-03-31T01:00:00"
    assert loaded.finished_at == "2026-03-31T01:10:00"
