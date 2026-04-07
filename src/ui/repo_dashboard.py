from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable, List, Optional

from src.models.core import SubjectProfile
from src.models.task_queue import RepoTask


def _normalized_source_key(raw_path: str) -> str:
    value = str(raw_path or "").strip()
    if not value:
        return ""
    if "://" in value:
        return value.casefold()
    try:
        normalized = Path(value).expanduser().resolve()
    except Exception:
        normalized = Path(value).expanduser()
    return str(normalized).replace("\\", "/").casefold()


@dataclass
class RepoDashboardRow:
    subject_name: str
    repo_root: str
    repo_status: str
    queued_files: int
    manifest_entries: int
    manual_review_items: int
    pending_repo_tasks: int
    last_task_status: str


def collect_repo_metrics(subjects: Iterable[SubjectProfile], tasks: Iterable[RepoTask]) -> List[RepoDashboardRow]:
    task_list = list(tasks)
    rows: List[RepoDashboardRow] = []
    for subject in subjects:
        repo_root = (subject.repo_root or "").strip()
        repo_path = Path(repo_root) if repo_root else None
        repo_status = "Sem repositório"
        manifest_entries = 0
        manual_review_items = 0
        processed_sources: set[str] = set()
        if repo_path and repo_path.exists():
            repo_status = "Estrutura pronta"
            manifest_path = repo_path / "manifest.json"
            if manifest_path.exists():
                repo_status = "Manifest pronto"
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest_entries = len(manifest.get("entries", []))
                    processed_sources = {
                        _normalized_source_key(entry.get("source_path", ""))
                        for entry in manifest.get("entries", [])
                        if entry.get("source_path")
                    }
                except Exception:
                    repo_status = "Manifest inválido"
            manual_review_dir = repo_path / "manual-review"
            if manual_review_dir.exists():
                manual_review_items = sum(1 for item in manual_review_dir.rglob("*") if item.is_file())

        subject_tasks = [
            task for task in task_list
            if task.subject_name == subject.name or (repo_root and task.repo_root == repo_root)
        ]
        pending_repo_tasks = sum(1 for task in subject_tasks if task.status in {"pending", "running"})
        last_task_status = "—"
        if subject_tasks:
            def _task_sort_key(item: RepoTask):
                status_rank = {
                    "completed": 3,
                    "failed": 2,
                    "cancelled": 1,
                    "running": 0,
                    "pending": 0,
                }.get(item.status, 0)
                timestamp = item.finished_at or item.started_at or item.created_at or ""
                return (status_rank, timestamp)

            last_task = max(subject_tasks, key=_task_sort_key)
            finished = f" @ {last_task.finished_at}" if last_task.finished_at else ""
            last_task_status = f"{last_task.status}{finished}"

        rows.append(
            RepoDashboardRow(
                subject_name=subject.name,
                repo_root=repo_root or "—",
                repo_status=repo_status,
                queued_files=sum(
                    1
                    for entry in subject.queue
                    if _normalized_source_key(getattr(entry, "source_path", "")) not in processed_sources
                ),
                manifest_entries=manifest_entries,
                manual_review_items=manual_review_items,
                pending_repo_tasks=pending_repo_tasks,
                last_task_status=last_task_status,
            )
        )
    return rows


class RepoDashboard(ttk.Frame):
    def __init__(self, parent, on_refresh: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self._on_refresh = on_refresh

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=(6, 4))
        ttk.Button(toolbar, text="🔄 Atualizar Dashboard", command=self._handle_refresh).pack(side="left")

        columns = (
            "subject",
            "repo_status",
            "queued_files",
            "manifest_entries",
            "manual_review",
            "pending_tasks",
            "last_task",
            "repo_root",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        self.tree.heading("subject", text="Matéria")
        self.tree.heading("repo_status", text="Repo")
        self.tree.heading("queued_files", text="Fila")
        self.tree.heading("manifest_entries", text="Entries")
        self.tree.heading("manual_review", text="Manual Review")
        self.tree.heading("pending_tasks", text="Tasks")
        self.tree.heading("last_task", text="Última Task")
        self.tree.heading("repo_root", text="Repositório")
        self.tree.column("subject", width=180)
        self.tree.column("repo_status", width=120, anchor="center")
        self.tree.column("queued_files", width=60, anchor="center")
        self.tree.column("manifest_entries", width=70, anchor="center")
        self.tree.column("manual_review", width=100, anchor="center")
        self.tree.column("pending_tasks", width=70, anchor="center")
        self.tree.column("last_task", width=180)
        self.tree.column("repo_root", width=360)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y", pady=(0, 8))

    def set_rows(self, rows: Iterable[RepoDashboardRow]) -> None:
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(rows):
            self.tree.insert(
                "",
                "end",
                iid=f"dashboard_{idx}",
                values=(
                    row.subject_name,
                    row.repo_status,
                    row.queued_files,
                    row.manifest_entries,
                    row.manual_review_items,
                    row.pending_repo_tasks,
                    row.last_task_status,
                    row.repo_root,
                ),
            )

    def _handle_refresh(self) -> None:
        if self._on_refresh:
            self._on_refresh()
