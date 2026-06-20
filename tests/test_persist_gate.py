"""TDD — Task 5: persist gate.

Gate: _build_file_map_timeline_context_from_course(persist=False) never writes.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.builder.timeline.index import _build_file_map_timeline_context_from_course
from src.builder.timeline.block_identity import BlockIdentityError, save_identity_ledger

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_DUMMY_KWARG = dict(
    build_file_map_unit_index_from_course=lambda cm, sp: [],
    build_file_map_content_taxonomy_from_course=lambda cm, sp: {},
)

_MINIMAL_SYLLABUS = """\
## Semana 1 (01/03/2026 - 07/03/2026)
Introdução
"""


def _write_syllabus(repo_root: Path, text: str = _MINIMAL_SYLLABUS) -> None:
    (repo_root / "course").mkdir(parents=True, exist_ok=True)
    (repo_root / "course" / "SYLLABUS.md").write_text(text, encoding="utf-8")


def _make_ledger(repo_root: Path, records: list) -> None:
    course_dir = repo_root / "course"
    course_dir.mkdir(parents=True, exist_ok=True)
    save_identity_ledger(course_dir, records)


# ---------------------------------------------------------------------------
# T5-1: persist=False — ledger ausente + sem refs existentes → sem escrita
# ---------------------------------------------------------------------------


def test_persist_false_no_ledger_no_refs_does_not_write(tmp_path):
    """persist=False + ledger ausente + sem refs → in-memory ok, NENHUM arquivo escrito."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"
    before = set(p.name for p in course_dir.iterdir())

    _build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=False,
        **_DUMMY_KWARG,
    )

    after = set(p.name for p in course_dir.iterdir())
    new_files = after - before
    assert ".block_identity.json" not in new_files, f"Escreveu ledger em persist=False: {new_files}"
    assert not any(f.endswith(".json") and f != "SYLLABUS.md" for f in new_files), (
        f"Novos arquivos em persist=False: {new_files}"
    )


# ---------------------------------------------------------------------------
# T5-2: persist=False + ledger ausente + refs uuid existentes → hard fail
# ---------------------------------------------------------------------------


def test_persist_false_ledger_absent_but_refs_exist_raises(tmp_path):
    """persist=False + ledger ausente + refs uuid existentes → BlockIdentityError clara."""
    _write_syllabus(tmp_path)
    # Cria .timeline_curation.json com chave uuid (simula ref existente detectada por scan_existing_block_refs)
    curation = {"version": 1, "blocks": {"550e8400-e29b-41d4-a716-446655440000": {"kind": "aula"}}}
    (tmp_path / "course" / ".timeline_curation.json").write_text(
        json.dumps(curation, ensure_ascii=False), encoding="utf-8"
    )

    with pytest.raises(BlockIdentityError, match=r"(?i)ledger"):
        _build_file_map_timeline_context_from_course(
            {"_repo_root": tmp_path},
            persist=False,
            **_DUMMY_KWARG,
        )


# ---------------------------------------------------------------------------
# T5-3: persist=False + stale block → in-memory uuid, sem escrita
# ---------------------------------------------------------------------------


def test_persist_false_stale_block_in_memory_no_write(tmp_path, caplog):
    """persist=False + ledger vazio (sem refs) → minta in-memory, sem escrita."""
    _write_syllabus(tmp_path)
    _make_ledger(tmp_path, [])

    course_dir = tmp_path / "course"
    before_names = set(p.name for p in course_dir.iterdir())

    with caplog.at_level(logging.WARNING):
        _build_file_map_timeline_context_from_course(
            {"_repo_root": tmp_path},
            persist=False,
            **_DUMMY_KWARG,
        )

    after_names = set(p.name for p in course_dir.iterdir())
    ledger_path = course_dir / ".block_identity.json"
    if ledger_path.exists():
        ledger_after = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert ledger_after == [], "persist=False não deve ter escrito no ledger"

    new_files = after_names - before_names
    for f in new_files:
        assert not f.endswith(".json"), f"Arquivo escrito em persist=False: {f}"


# ---------------------------------------------------------------------------
# T5-4: persist=True (default) → ledger escrito (regression guard)
# ---------------------------------------------------------------------------


def test_persist_true_writes_ledger(tmp_path):
    """persist=True (default) → ledger escrito normalmente."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"

    _build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=True,
        **_DUMMY_KWARG,
    )

    assert (course_dir / ".block_identity.json").exists(), "persist=True deve escrever ledger"
