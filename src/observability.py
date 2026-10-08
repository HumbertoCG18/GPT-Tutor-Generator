from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from importlib import metadata
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Iterator, Optional


LOGGER_NAME = "gpt_tutor.observability"
_ALLOWED_OPERATIONS = {"build", "incremental_build", "process_single"}
_SAFE_IDENTIFIER = re.compile(r"[^a-zA-Z0-9_.-]")
_current_run_id: ContextVar[Optional[str]] = ContextVar("observability_run_id", default=None)
# Operacao publica que o usuario pediu; um build aninhado no fallback do incremental nao conta como build direto.
_current_entry_point: ContextVar[Optional[str]] = ContextVar("observability_entry_point", default=None)


class _JsonEventFormatter(logging.Formatter):
    def __init__(self, version: str):
        super().__init__()
        self.version = _sanitize_identifier(version)

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "run_id": record.run_id,
            "operation": record.operation,
            "entry_point": record.entry_point,
            "status": record.status,
            "duration_ms": record.duration_ms,
            "version": self.version,
        }
        if record.error_type:
            payload["error_type"] = record.error_type
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def _sanitize_identifier(value: str) -> str:
    return _SAFE_IDENTIFIER.sub("_", str(value))[:80] or "unknown"


def product_version() -> str:
    try:
        return metadata.version("academic-tutor-repo-builder")
    except metadata.PackageNotFoundError:
        return "dev"


def default_log_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "GPT-Tutor-Generator" / "logs"
    return Path.home() / ".gpt-tutor-generator" / "logs"


def configure_local_observability(
    log_dir: Path,
    *,
    version: Optional[str] = None,
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 5,
) -> Path:
    log_path = Path(log_dir) / "operations.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    resolved_path = log_path.resolve()
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == resolved_path:
            return log_path

    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(_JsonEventFormatter(version or product_version()))
    logger.addHandler(handler)
    return log_path


def _emit(operation: str, run_id: str, status: str, duration_ms: int, error_type: str = "") -> None:
    logging.getLogger(LOGGER_NAME).info(
        "operation_event",
        extra={
            "run_id": run_id,
            "operation": operation,
            "entry_point": _current_entry_point.get() or operation,
            "status": status,
            "duration_ms": duration_ms,
            "error_type": error_type,
        },
    )


@contextmanager
def operation_scope(
    operation: str, failure_count: Optional[Callable[[], int]] = None
) -> Iterator[str]:
    if operation not in _ALLOWED_OPERATIONS:
        raise ValueError("unsupported observable operation")
    run_id = _current_run_id.get() or str(uuid.uuid4())
    token = _current_run_id.set(run_id)
    entry_token = _current_entry_point.set(_current_entry_point.get() or operation)
    failures_before = failure_count() if failure_count else 0
    started = time.perf_counter()
    _emit(operation, run_id, "started", 0)
    try:
        yield run_id
    except InterruptedError as exc:
        _emit(
            operation,
            run_id,
            "cancelled",
            round((time.perf_counter() - started) * 1000),
            _sanitize_identifier(type(exc).__name__),
        )
        raise
    except Exception as exc:
        _emit(
            operation,
            run_id,
            "error",
            round((time.perf_counter() - started) * 1000),
            _sanitize_identifier(type(exc).__name__),
        )
        raise
    else:
        partial = failure_count is not None and failure_count() > failures_before
        _emit(
            operation,
            run_id,
            "partial" if partial else "success",
            round((time.perf_counter() - started) * 1000),
        )
    finally:
        _current_entry_point.reset(entry_token)
        _current_run_id.reset(token)
