"""Migrador ADITIVO de sinais (S0): aplica posting_date/moodle_label/lessons_index/turma
aos repos ja gerados via API Moodle. NAO toca source_section nem card_block_map (= S0b).

Uso:
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] [--year YYYY]   # dry-run
    python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] [--year YYYY] --write
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.builder.sources.moodle import (
    MoodleClient, load_moodle_token, backfill_repo_signals_additive,
    parse_moodle_course,
)
from src.utils.helpers import parse_sarc_turma_key


def _resolve_year(client, course: str, sarc: str, year_arg: str) -> str:
    """Resolve o ano "YYYY" com precedência: sarc > year_arg > auto-derive > "".

    Auto-derive consulta o Moodle; qualquer falha retorna "" sem crashar o migrador.
    """
    if sarc:
        ano = parse_sarc_turma_key(sarc).get("ano", "")
        if ano:
            return ano
    if year_arg:
        return year_arg
    try:
        userid = client.site_info().get("userid")
        courses = client.get_users_courses(userid)
        for c in courses:
            if str(c.get("id")) == str(course):
                sem = parse_moodle_course(c).get("semester", "")
                # "2026/1" -> "2026"
                return sem.split("/")[0] if "/" in sem else sem
    except Exception:
        pass
    return ""


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
    course = sarc = year_arg = ""
    if "--course" in argv:
        i = argv.index("--course"); course = argv[i + 1] if i + 1 < len(argv) else ""
    if "--sarc" in argv:
        i = argv.index("--sarc"); sarc = argv[i + 1] if i + 1 < len(argv) else ""
    if "--year" in argv:
        i = argv.index("--year"); year_arg = argv[i + 1] if i + 1 < len(argv) else ""
    pos = [a for a in argv if not a.startswith("-") and a not in (course, sarc, year_arg)]
    if not pos or not course:
        print("uso: python -m scripts.migrate_signals <repo_root> --course <id> [--sarc <url>] [--year YYYY] [--write]")
        return 2
    repo = Path(pos[0])
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN (.env raiz ou moddle/.env).")
        return 2
    client = MoodleClient(url, tok)
    contents = client.get_course_contents(course)
    year = _resolve_year(client, course, sarc, year_arg)
    if not year:
        print("AVISO: ano nao resolvido (use --year ou --sarc) -> lessons_index NAO sera capturado.")
    info = {
        "name": repo.name,
        "semester": f"{year}/1" if year else "",
        "schedule_url": sarc,
    }
    res = migrate_repo_additive(repo, contents, info, write=write)
    print(f"posting={res['posting']}  labels={res['labels']}  lessons={res['lessons']}  (ano={year or '?'})")
    print("Gravado (.apibak feito)." if write else "Dry-run. Use --write para gravar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
