"""Migrador ADITIVO de sinais (S0): aplica posting_date/moodle_label/lessons_index/turma
aos repos ja gerados via API Moodle. NAO toca source_section nem card_block_map (= S0b).

Uso:
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>]          # dry-run
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] --write  # grava (.apibak)
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.builder.sources.moodle import (
    MoodleClient, load_moodle_token, backfill_repo_signals_additive,
)
from src.utils.helpers import parse_sarc_turma_key


def migrate_repo_additive(repo_root, contents, info, write: bool = False) -> dict:
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if write and mpath.is_file():
        (mpath.with_suffix(".json.apibak")).write_text(
            mpath.read_text(encoding="utf-8"), encoding="utf-8")
    return backfill_repo_signals_additive(repo, contents, info, write=write)


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    course = sarc = ""
    if "--course" in argv:
        i = argv.index("--course"); course = argv[i + 1] if i + 1 < len(argv) else ""
    if "--sarc" in argv:
        i = argv.index("--sarc"); sarc = argv[i + 1] if i + 1 < len(argv) else ""
    pos = [a for a in argv if not a.startswith("-") and a not in (course, sarc)]
    if not pos or not course:
        print("uso: python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] [--write]")
        return 2
    repo = Path(pos[0])
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN (.env raiz ou moddle/.env).")
        return 2
    contents = MoodleClient(url, tok).get_course_contents(course)
    info = {"name": repo.name, "semester": "", "schedule_url": sarc}
    if sarc:
        key = parse_sarc_turma_key(sarc)
        info["semester"] = f"{key['ano']}/{key['sem']}" if key["ano"] else ""
    res = migrate_repo_additive(repo, contents, info, write=write)
    print(f"posting={res['posting']}  labels={res['labels']}  lessons={res['lessons']}")
    print("Gravado (.apibak feito)." if write else "Dry-run. Use --write para gravar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
