"""Carimba source_section em entries já no manifest, casando com o stash por nome.

Uso:
    python -m scripts.backfill_source_section <repo_root> <stash_folder>          # dry-run
    python -m scripts.backfill_source_section <repo_root> <stash_folder> --write  # grava
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.builder.core.stash_import import scan_stash_cards
from src.builder.core.stash_backfill import match_entries_to_cards


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    pos = [a for a in argv if not a.startswith("-")]
    if len(pos) < 2:
        print("uso: python -m scripts.backfill_source_section <repo_root> <stash_folder> [--write]")
        return 2
    repo_root, stash = Path(pos[0]), Path(pos[1])
    manifest_path = repo_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    scan = scan_stash_cards(stash)
    assignments, unmatched, ambiguous = match_entries_to_cards(entries, scan)

    print(f"Stash: {len(scan.items)} arquivos. Manifest: {len(entries)} entries.")
    print(f"Casados (vao receber source_section): {len(assignments)}")
    print(f"Ambiguos (basename em >1 card, pulados): {len(ambiguous)} -> {ambiguous}")
    print(f"Sem arquivo no stash (pulados): {len(unmatched)} -> {unmatched}")

    if not write:
        print("\nDry-run. Use --write para gravar.")
        return 0

    changed = 0
    for entry in entries:
        eid = str(entry.get("id") or "") or Path(str(entry.get("source_path") or "")).name
        if eid in assignments:
            entry["source_section"] = assignments[eid]
            changed += 1
    backup = manifest_path.with_suffix(".json.bak")
    backup.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado: {changed} entries atualizados. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
