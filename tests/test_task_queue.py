from pathlib import Path

from src.builder.ops.task_queue_runner import TaskQueueRunner
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


def test_repo_task_keeps_entry_payload_snapshot():
    payload = {"source_path": "raw/pdfs/lista1.pdf", "title": "Lista 1", "nested": {"page": 1}}
    task = RepoTask(
        task_id="task-snapshot",
        subject_name="Métodos Formais",
        repo_root="C:/Repos/metodos-formais",
        action="process_selected",
        entry_payloads=[payload],
    )

    payload["title"] = "Lista alterada"
    payload["nested"]["page"] = 99

    assert task.entry_payloads[0]["title"] == "Lista 1"
    assert task.entry_payloads[0]["nested"]["page"] == 1


def test_runner_executes_tasks_in_fifo_order():
    executed = []

    def fake_executor(task):
        executed.append(task.task_id)

    runner = TaskQueueRunner(fake_executor)
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo"),
    ]

    runner.run_pending(tasks)

    assert executed == ["task-a", "task-b"]
    assert tasks[0].status == "completed"
    assert tasks[1].status == "completed"
    assert tasks[0].started_at
    assert tasks[1].finished_at


def test_runner_marks_failure_and_continues():
    executed = []

    def fake_executor(task):
        executed.append(task.task_id)
        if task.task_id == "task-a":
            raise RuntimeError("boom")

    runner = TaskQueueRunner(fake_executor)
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo"),
    ]

    runner.run_pending(tasks)

    assert executed == ["task-a", "task-b"]
    assert tasks[0].status == "failed"
    assert "boom" in tasks[0].notes
    assert tasks[1].status == "completed"


def test_shutdown_is_requested_only_after_last_completed_task():
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo", shutdown_after_completion=True),
    ]

    runner = TaskQueueRunner(lambda task: None)
    runner.run_pending(tasks)

    assert TaskQueueRunner.should_request_shutdown(tasks) is True


def test_runner_cancels_current_task_and_keeps_remaining_pending():
    def before_task(task):
        return None

    def fake_executor(task):
        raise InterruptedError("cancelado")

    runner = TaskQueueRunner(fake_executor, before_task=before_task)
    tasks = [
        RepoTask(task_id="task-a", subject_name="A", repo_root="A", action="build_repo"),
        RepoTask(task_id="task-b", subject_name="B", repo_root="B", action="build_repo"),
    ]

    runner.run_pending(tasks)

    assert tasks[0].status == "cancelled"
    assert "cancelado" in tasks[0].notes
    assert tasks[1].status == "pending"
