"""Backfill de source_section via METADADOS da API Moodle (sem baixar bytes).

Casa os entries do manifest com as seções (= cards) do curso por nome de arquivo.

Uso:
    python -m scripts.moodle_backfill_sections <repo_root> --course <id>           # dry-run
    python -m scripts.moodle_backfill_sections <repo_root> --course <id> --write   # grava
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.builder.sources.moodle import (
    MoodleClient, load_moodle_token, backfill_source_section_from_api,
)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    course = ""
    if "--course" in argv:
        i = argv.index("--course")
        if i + 1 < len(argv):
            course = argv[i + 1]
    pos = [a for a in argv if not a.startswith("-") and a != course]
    if not pos or not course:
        print("uso: python -m scripts.moodle_backfill_sections <repo_root> --course <id> [--write]")
        return 2
    repo = Path(pos[0])
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN (.env raiz ou moddle/.env).")
        return 2
    manifest_path = repo / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    contents = MoodleClient(url, tok).get_course_contents(course)
    assignments, unmatched, ambiguous = backfill_source_section_from_api(entries, contents)
    print(f"Entries: {len(entries)}  casados: {len(assignments)}  "
          f"ambiguos: {len(ambiguous)}  sem-secao: {len(unmatched)}")
    if not write:
        print("\nDry-run. Use --write para gravar.")
        return 0
    changed = 0
    for e in entries:
        eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
        if eid in assignments:
            e["source_section"] = assignments[eid]
            changed += 1
    backup = manifest_path.with_suffix(".json.apibak")
    backup.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado: {changed} entries. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
