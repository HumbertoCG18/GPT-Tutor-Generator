"""TDD — Task 5: persist gate.

Gate: _build_file_map_timeline_context_from_course(persist=False) never writes.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

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
    """persist=False + bloco stale (ledger vazio, mint necessário) → uuid in-memory, WARNING, sem escrita."""
    _write_syllabus(tmp_path)
    _make_ledger(tmp_path, [])

    course_dir = tmp_path / "course"
    before_mtimes = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    stale_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    stale_block = {"id": "bloco-01", "block_uuid": stale_uuid}

    def _fake_reattach(blocks, ledger, *, has_existing_refs, **kw):
        for b in blocks:
            b["block_uuid"] = stale_uuid
        return blocks, ledger, [f"no-date:mint:{stale_uuid}:bloco-01"]

    with caplog.at_level(logging.WARNING, logger="src.builder.timeline.index"):
        with patch(
            "src.builder.timeline.index.reattach_block_uuids",
            side_effect=_fake_reattach,
        ):
            result = _build_file_map_timeline_context_from_course(
                {"_repo_root": tmp_path},
                persist=False,
                **_DUMMY_KWARG,
            )

    # (a) uuid presente in-memory
    blocks = (result or {}).get("timeline_index", {}).get("blocks") or []
    for b in blocks:
        assert b.get("block_uuid"), f"bloco sem uuid in-memory: {b}"

    # (b) WARNING "ledger stale" logado
    stale_warnings = [r for r in caplog.records if r.levelno >= logging.WARNING and "stale" in r.message.lower()]
    assert stale_warnings, (
        f"Esperava WARNING 'ledger stale' mas nenhum foi logado. "
        f"Records: {[r.message for r in caplog.records]}"
    )

    # (c) nenhum arquivo escrito
    after_mtimes = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}
    new_files = set(after_mtimes) - set(before_mtimes)
    modified = {p for p in set(before_mtimes) & set(after_mtimes) if after_mtimes[p] != before_mtimes[p]}
    assert not new_files, f"Novos arquivos em persist=False: {[str(p) for p in new_files]}"
    assert not modified, f"Arquivos modificados em persist=False: {[str(p) for p in modified]}"


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


# ---------------------------------------------------------------------------
# T5-5: engine facade threads persist=False (does not write)
# ---------------------------------------------------------------------------


def test_facade_threads_persist_false(tmp_path):
    """engine._build_file_map_timeline_context_from_course passa persist=False p/ index."""
    _write_syllabus(tmp_path)
    course_dir = tmp_path / "course"

    import src.builder.engine as engine
    engine._build_file_map_timeline_context_from_course(
        {"_repo_root": tmp_path},
        persist=False,
    )

    assert not (course_dir / ".block_identity.json").exists(), (
        "engine facade com persist=False nao deve escrever ledger"
    )


# ---------------------------------------------------------------------------
# T5-6: rebuild_diff-style call writes nothing (strong acceptance criterion)
# ---------------------------------------------------------------------------


def test_rebuild_diff_style_call_writes_nothing(tmp_path):
    """Simula exatamente o que rebuild_diff.py faz; nenhum arquivo criado ou modificado."""
    import src.builder.engine as engine

    course_dir = tmp_path / "course"
    course_dir.mkdir()
    (course_dir / "SYLLABUS.md").write_text(
        "## Semana 1 (01/03/2026 - 07/03/2026)\nIntroducao\n", encoding="utf-8"
    )
    ledger = [
        {
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "anchor": {
                "period_start": "2026-03-01",
                "period_end": "2026-03-07",
                "topic_tokens": ["introducao"],
            },
            "display_id_last": "bloco-01",
            "first_seen": "2026-03-01",
            "last_seen": "2026-03-01",
        }
    ]
    save_identity_ledger(course_dir, ledger)

    before_files = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    cm = {}
    engine._build_file_map_timeline_context_from_course(
        {**cm, "_repo_root": tmp_path}, None, content_taxonomy=None, persist=False
    )

    after_files = {p: p.stat().st_mtime for p in course_dir.rglob("*") if p.is_file()}

    new_files = set(after_files) - set(before_files)
    modified_files = {p for p in set(before_files) & set(after_files) if after_files[p] != before_files[p]}

    assert not new_files, f"rebuild_diff-style criou arquivos: {[str(p) for p in new_files]}"
    assert not modified_files, f"rebuild_diff-style modificou arquivos: {[str(p) for p in modified_files]}"
