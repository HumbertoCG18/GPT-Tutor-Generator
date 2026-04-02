import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


RepoTaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
RepoTaskAction = Literal["build_repo", "process_selected", "refresh_repo"]


@dataclass
class RepoTask:
    task_id: str
    subject_name: str
    repo_root: str
    action: RepoTaskAction
    status: RepoTaskStatus = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    shutdown_after_completion: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RepoTask":
        return cls(**data)


class RepoTaskStore:
    def __init__(self, path: Path):
        self._path = path

    def load_all(self) -> List[RepoTask]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [RepoTask.from_dict(item) for item in raw]

    def save_all(self, tasks: List[RepoTask]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([task.to_dict() for task in tasks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
