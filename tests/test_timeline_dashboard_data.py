from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.timeline_dashboard import load_timeline_data, save_block_assignment


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_data_separates_mapped_and_unmapped(tmp_path):
    manifest = {
        "entries": [
            {"id": "e1", "auto_tags": ["bloco:blk-01"], "unit_match_confidence": 0.9},
            {"id": "e2", "manual_timeline_block_id": "blk-01", "auto_tags": []},
            {"id": "e3", "auto_tags": []},
        ]
    }
    timeline = {
        "version": 3,
        "blocks": [{"id": "blk-01", "period_label": "Semana 01", "unit_slug": "u1"}],
    }
    _write(tmp_path / "manifest.json", manifest)
    _write(tmp_path / "course" / ".timeline_index.json", timeline)

    blocks, by_block, unmapped = load_timeline_data(
        tmp_path / "manifest.json",
        tmp_path / "course" / ".timeline_index.json",
    )

    assert len(blocks) == 1
    assert len(by_block["blk-01"]) == 2  # e1 (auto_tags) + e2 (manual)
    assert len(unmapped) == 1
    assert unmapped[0]["id"] == "e3"


def test_save_block_assignment_writes_manifest(tmp_path):
    manifest = {"entries": [{"id": "e1"}]}
    mp = tmp_path / "manifest.json"
    _write(mp, manifest)

    save_block_assignment(mp, "e1", "blk-01")

    data = json.loads(mp.read_text(encoding="utf-8"))
    assert data["entries"][0]["manual_timeline_block_id"] == "blk-01"


def test_save_block_assignment_none_removes_field(tmp_path):
    manifest = {"entries": [{"id": "e1", "manual_timeline_block_id": "blk-01"}]}
    mp = tmp_path / "manifest.json"
    _write(mp, manifest)

    save_block_assignment(mp, "e1", None)

    data = json.loads(mp.read_text(encoding="utf-8"))
    assert "manual_timeline_block_id" not in data["entries"][0]
