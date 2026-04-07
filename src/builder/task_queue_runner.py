from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, Optional

from src.models.task_queue import RepoTask


TaskExecutor = Callable[[RepoTask], None]
TaskEventCallback = Callable[[str, RepoTask, Optional[Exception]], None]
BeforeTaskCallback = Callable[[RepoTask], None]


class TaskQueueRunner:
    def __init__(
        self,
        executor: TaskExecutor,
        on_event: Optional[TaskEventCallback] = None,
        before_task: Optional[BeforeTaskCallback] = None,
    ):
        self._executor = executor
        self._on_event = on_event
        self._before_task = before_task

    def run_pending(self, tasks: Iterable[RepoTask]) -> None:
        for task in tasks:
            if task.status != "pending":
                continue
            if self._before_task:
                self._before_task(task)
            task.status = "running"
            task.started_at = datetime.now().isoformat(timespec="seconds")
            self._emit("started", task, None)
            try:
                self._executor(task)
            except InterruptedError as exc:
                task.status = "cancelled"
                task.finished_at = datetime.now().isoformat(timespec="seconds")
                self._append_note(task, f"Cancelada: {exc}")
                self._emit("cancelled", task, exc)
                self._emit("finished", task, exc)
                break
            except Exception as exc:
                task.status = "failed"
                task.finished_at = datetime.now().isoformat(timespec="seconds")
                self._append_note(task, f"Falha: {exc}")
                self._emit("failed", task, exc)
                self._emit("finished", task, exc)
                continue

            task.status = "completed"
            task.finished_at = datetime.now().isoformat(timespec="seconds")
            self._emit("completed", task, None)
            self._emit("finished", task, None)

    @staticmethod
    def should_request_shutdown(tasks: Iterable[RepoTask]) -> bool:
        relevant = [task for task in tasks if task.status != "cancelled"]
        if not relevant:
            return False
        if any(task.status in {"pending", "running"} for task in relevant):
            return False
        return any(task.shutdown_after_completion and task.status == "completed" for task in relevant)

    def _emit(self, event_name: str, task: RepoTask, error: Optional[Exception]) -> None:
        if self._on_event:
            self._on_event(event_name, task, error)

    @staticmethod
    def _append_note(task: RepoTask, message: str) -> None:
        note = (task.notes or "").strip()
        task.notes = f"{note}\n{message}".strip() if note else message
