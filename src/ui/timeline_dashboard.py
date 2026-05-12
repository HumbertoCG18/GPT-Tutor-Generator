from __future__ import annotations

import json
import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.models.core import SubjectProfile
from src.ui.theme import apply_theme_to_toplevel

logger = logging.getLogger(__name__)

_DATE_PREFIX_RE = re.compile(r"^(\d{1,2})\.(\d{2})\s+")


def load_timeline_data(
    manifest_path: Path,
    timeline_index_path: Path,
) -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    """Returns (blocks, entries_by_block_id, unmapped_entries)."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_index_path.read_text(encoding="utf-8"))

    blocks: list[dict] = list(timeline.get("blocks") or [])
    entries: list[dict] = list(manifest.get("entries") or [])

    block_ids = {b["id"] for b in blocks if b.get("id")}
    entries_by_block_id: dict[str, list[dict]] = {b["id"]: [] for b in blocks if b.get("id")}
    unmapped: list[dict] = []

    for entry in entries:
        manual_id = str(entry.get("manual_timeline_block_id") or "").strip()
        auto_tags = list(entry.get("auto_tags") or [])
        auto_block_id = next(
            (t[len("bloco:"):] for t in auto_tags if t.startswith("bloco:")),
            "",
        )
        assigned_id = manual_id or auto_block_id
        if assigned_id and assigned_id in block_ids:
            entries_by_block_id[assigned_id].append(entry)
        else:
            unmapped.append(entry)

    return blocks, entries_by_block_id, unmapped


def save_block_assignment(
    manifest_path: Path,
    entry_id: str,
    block_id: Optional[str],
) -> None:
    """Persiste manual_timeline_block_id no manifest. block_id=None remove o campo."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("entries") or []:
        if entry.get("id") == entry_id:
            if block_id:
                entry["manual_timeline_block_id"] = block_id
            else:
                entry.pop("manual_timeline_block_id", None)
            break
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
