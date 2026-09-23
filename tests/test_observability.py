import json
import logging
from contextlib import nullcontext
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.__main__ as main_module
from src.builder.engine import RepoBuilder
from src.observability import configure_local_observability, operation_scope


LOGGER_NAME = "gpt_tutor.observability"


@pytest.fixture(autouse=True)
def _close_observability_handlers():
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    yield
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _events(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_operation_scope_correlates_complete_operation_without_sensitive_data(tmp_path):
    log_path = configure_local_observability(tmp_path, version="3.0.0")
    secret = "token-super-secreto"
    academic_content = "conteudo bruto da prova"

    with operation_scope("build") as run_id:
        assert run_id
        assert secret
        assert academic_content

    events = _events(log_path)
    assert [event["status"] for event in events] == ["started", "success"]
    assert {event["run_id"] for event in events} == {run_id}
    assert {event["operation"] for event in events} == {"build"}
    assert {event["version"] for event in events} == {"3.0.0"}
    assert events[1]["duration_ms"] >= 0
    assert set(events[0]) == {
        "timestamp",
        "run_id",
        "operation",
        "entry_point",
        "status",
        "duration_ms",
        "version",
    }
    raw = log_path.read_text(encoding="utf-8")
    assert secret not in raw
    assert academic_content not in raw


@pytest.mark.parametrize(
    ("error", "status"),
    [(RuntimeError("path=C:/privado token=abc"), "error"),
     (InterruptedError("conteudo academico"), "cancelled")],
)
def test_operation_scope_records_failure_type_and_rethrows_same_exception(tmp_path, error, status):
    log_path = configure_local_observability(tmp_path, version="dev")

    with pytest.raises(type(error)) as raised:
        with operation_scope("incremental_build"):
            raise error

    assert raised.value is error
    events = _events(log_path)
    terminal = events[-1]
    assert events[0]["run_id"] == terminal["run_id"]
    assert terminal["status"] == status
    assert terminal["error_type"] == type(error).__name__
    assert str(error) not in log_path.read_text(encoding="utf-8")


def test_configuration_is_idempotent_and_rotates_jsonl(tmp_path):
    external_handler = logging.NullHandler()
    logging.getLogger(LOGGER_NAME).addHandler(external_handler)
    log_path = configure_local_observability(
        tmp_path, version="dev", max_bytes=300, backup_count=1
    )
    assert configure_local_observability(
        tmp_path, version="dev", max_bytes=300, backup_count=1
    ) == log_path
    handlers = logging.getLogger(LOGGER_NAME).handlers
    assert external_handler in handlers
    assert len([
        handler for handler in handlers
        if isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename) == log_path.resolve()
    ]) == 1

    for _ in range(6):
        with operation_scope("process_single"):
            pass

    assert log_path.exists()
    assert log_path.with_name("operations.jsonl.1").exists()


@pytest.mark.parametrize(
    ("method_name", "impl_name", "operation", "args", "expected"),
    [
        ("build", "_build_impl", "build", (), None),
        ("incremental_build", "_incremental_build_impl", "incremental_build", (), None),
        (
            "process_single",
            "_process_single_impl",
            "process_single",
            (SimpleNamespace(title="material privado"),),
            "done",
        ),
    ],
)
def test_repo_builder_operations_are_observed_without_changing_behavior(
    tmp_path, method_name, impl_name, operation, args, expected
):
    log_path = configure_local_observability(tmp_path, version="test")
    builder = RepoBuilder.__new__(RepoBuilder)
    builder._sleep_guard = lambda _reason: nullcontext()
    calls = []
    if args:
        setattr(builder, impl_name, lambda entry, force=False: calls.append(entry) or "done")
    else:
        setattr(builder, impl_name, lambda: calls.append(operation))

    assert getattr(builder, method_name)(*args) == expected

    assert len(calls) == 1
    events = _events(log_path)
    assert [event["operation"] for event in events] == [operation, operation]
    assert [event["status"] for event in events] == ["started", "success"]


def test_startup_continues_when_local_log_is_unavailable(monkeypatch):
    calls = []

    def unavailable(_log_dir):
        raise OSError("disco indisponivel")

    class FakeApp:
        def mainloop(self):
            calls.append("mainloop")

    monkeypatch.setattr(main_module, "configure_local_observability", unavailable)
    monkeypatch.setattr(main_module, "App", FakeApp)

    main_module.main()

    assert calls == ["mainloop"]


def test_nested_fallback_keeps_outer_entry_point(tmp_path):
    log_path = configure_local_observability(tmp_path, version="test")

    with operation_scope("incremental_build"):
        with operation_scope("build"):
            pass

    events = _events(log_path)
    assert [event["operation"] for event in events] == [
        "incremental_build", "build", "build", "incremental_build",
    ]
    assert {event["entry_point"] for event in events} == {"incremental_build"}
    assert len({event["run_id"] for event in events}) == 1


def test_handled_entry_failures_report_partial_instead_of_success(tmp_path):
    log_path = configure_local_observability(tmp_path, version="test")
    builder = RepoBuilder.__new__(RepoBuilder)
    builder._sleep_guard = lambda _reason: nullcontext()
    builder.failed_entries = [{"title": "falha anterior"}]
    builder._build_impl = lambda: builder.failed_entries.append({"title": "fonte ausente"})

    builder.build()

    assert [event["status"] for event in _events(log_path)] == ["started", "partial"]
