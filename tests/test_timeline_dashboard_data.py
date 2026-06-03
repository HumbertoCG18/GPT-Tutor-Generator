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


def test_load_data_manual_wins_divergent(tmp_path):
    """Manual e auto divergem: dashboard usa resolve_effective_block -> manual."""
    manifest = {
        "entries": [
            {
                "id": "e1",
                "manual_timeline_block_id": "blk-01",
                "computed_block_id": "blk-02",
                "auto_tags": ["bloco:blk-02"],
            },
        ]
    }
    timeline = {
        "version": 3,
        "blocks": [
            {"id": "blk-01", "period_label": "S1", "unit_slug": "u1"},
            {"id": "blk-02", "period_label": "S2", "unit_slug": "u1"},
        ],
    }
    _write(tmp_path / "manifest.json", manifest)
    _write(tmp_path / "course" / ".timeline_index.json", timeline)

    _blocks, by_block, unmapped = load_timeline_data(
        tmp_path / "manifest.json",
        tmp_path / "course" / ".timeline_index.json",
    )
    assert len(by_block["blk-01"]) == 1  # manual venceu
    assert len(by_block["blk-02"]) == 0
    assert unmapped == []


def test_load_data_agrees_with_health(tmp_path):
    """resolve_effective_block é fonte única: dashboard e health concordam."""
    from src.builder.artifacts.cronograma_health import _entry_block_id

    entry = {
        "id": "e1",
        "manual_timeline_block_id": "blk-01",
        "computed_block_id": "blk-02",
        "auto_tags": ["bloco:blk-02"],
        "category": "material-de-aula",
    }
    manifest = {"entries": [entry]}
    timeline = {
        "version": 3,
        "blocks": [
            {"id": "blk-01", "period_label": "S1"},
            {"id": "blk-02", "period_label": "S2"},
        ],
    }
    _write(tmp_path / "manifest.json", manifest)
    _write(tmp_path / "course" / ".timeline_index.json", timeline)

    _blocks, by_block, _unmapped = load_timeline_data(
        tmp_path / "manifest.json",
        tmp_path / "course" / ".timeline_index.json",
    )
    dashboard_block = next(bid for bid, es in by_block.items() if es)
    # health resolve sem a lista de blocos -> id cru do manual (mesmo vencedor)
    health_block = _entry_block_id(entry)
    assert dashboard_block == health_block == "blk-01"


def test_load_data_agrees_with_health_on_stale_manual(tmp_path):
    """Manual id STALE (não existe nos blocks): health e dashboard devem cair
    no MESMO fallback computed via resolve_effective_block — não no id cru.

    Antes do fix, health resolvia sem a lista de blocos e confiava no manual cru
    (blk-99), enquanto o dashboard validava e caía em blk-02: divergência que
    quebra a garantia de fonte única (spec linhas 138-146, 213-215).
    """
    from src.builder.artifacts.cronograma_health import _entry_block_id

    entry = {
        "id": "e1",
        "manual_timeline_block_id": "blk-99",  # stale: não existe na timeline
        "computed_block_id": "blk-02",
        "auto_tags": ["bloco:blk-02"],
        "category": "material-de-aula",
    }
    manifest = {"entries": [entry]}
    timeline = {
        "version": 3,
        "blocks": [
            {"id": "blk-01", "period_label": "S1"},
            {"id": "blk-02", "period_label": "S2"},
        ],
    }
    _write(tmp_path / "manifest.json", manifest)
    _write(tmp_path / "course" / ".timeline_index.json", timeline)

    blocks, by_block, unmapped = load_timeline_data(
        tmp_path / "manifest.json",
        tmp_path / "course" / ".timeline_index.json",
    )
    dashboard_block = next(bid for bid, es in by_block.items() if es)
    health_block = _entry_block_id(entry, blocks)
    assert dashboard_block == health_block == "blk-02"


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
