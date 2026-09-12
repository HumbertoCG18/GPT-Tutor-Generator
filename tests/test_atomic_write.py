"""Tests for atomic file writes (write_text) and atomic manifest writes
(write_json_manifest) — protect against torn/corrupt files on crash."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from src.utils.helpers import write_text, write_json_manifest


# ---------------------------------------------------------------------------
# write_text — atomic
# ---------------------------------------------------------------------------

def test_write_text_writes_content(tmp_path: Path):
    target = tmp_path / "out.txt"
    write_text(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def test_write_text_creates_parent_dirs(tmp_path: Path):
    target = tmp_path / "a" / "b" / "out.txt"
    write_text(target, "x")
    assert target.read_text(encoding="utf-8") == "x"


def test_write_text_leaves_no_tmp_after_success(tmp_path: Path):
    target = tmp_path / "out.txt"
    write_text(target, "data")
    siblings = [p.name for p in tmp_path.iterdir()]
    assert siblings == ["out.txt"]  # no out.txt.tmp residue


def test_write_text_preserves_original_when_tmp_write_fails(tmp_path: Path):
    target = tmp_path / "out.txt"
    target.write_text("ORIGINAL", encoding="utf-8")
    # Make the tmp write blow up after the original already exists.
    with mock.patch.object(Path, "write_text", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            write_text(target, "NEW")
    # Original must be intact (never truncated).
    assert target.read_text(encoding="utf-8") == "ORIGINAL"


# ---------------------------------------------------------------------------
# write_json_manifest — atomic + .bak backup
# ---------------------------------------------------------------------------

def test_write_json_manifest_writes_json(tmp_path: Path):
    target = tmp_path / "manifest.json"
    data = {"entries": [{"id": "x", "título": "ção"}]}
    write_json_manifest(target, data)
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == data


def test_write_json_manifest_uses_canonical_formatting(tmp_path: Path):
    target = tmp_path / "manifest.json"
    write_json_manifest(target, {"a": "ção"})
    raw = target.read_text(encoding="utf-8")
    assert "ção" in raw  # ensure_ascii=False
    assert "\n  " in raw  # indent=2


def test_write_json_manifest_no_bak_on_first_write(tmp_path: Path):
    target = tmp_path / "manifest.json"
    write_json_manifest(target, {"v": 1})
    assert not (tmp_path / "manifest.json.bak").exists()


def test_write_json_manifest_creates_bak_with_previous_content(tmp_path: Path):
    target = tmp_path / "manifest.json"
    write_json_manifest(target, {"v": 1})
    write_json_manifest(target, {"v": 2})
    bak = tmp_path / "manifest.json.bak"
    assert json.loads(bak.read_text(encoding="utf-8")) == {"v": 1}
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 2}


def test_write_json_manifest_leaves_no_tmp_after_success(tmp_path: Path):
    target = tmp_path / "manifest.json"
    write_json_manifest(target, {"v": 1})
    write_json_manifest(target, {"v": 2})
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["manifest.json", "manifest.json.bak"]  # no .tmp residue


def test_write_json_manifest_backup_failure_does_not_block_write(tmp_path: Path):
    target = tmp_path / "manifest.json"
    write_json_manifest(target, {"v": 1})
    real_write_text = Path.write_text

    def selective_fail(self: Path, *args, **kwargs):
        if self.name.endswith(".bak"):
            raise OSError("cannot back up")
        return real_write_text(self, *args, **kwargs)

    with mock.patch.object(Path, "write_text", selective_fail):
        write_json_manifest(target, {"v": 2})  # must not raise
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 2}
