"""Probe READ-ONLY do posting_date (S0): mede, por curso, o cluster de inicio-de-semestre
(batch), a fracao off-batch (sinal informativo p/ A2) e contagem stale (ano anterior).

Uso:
    python -m scripts.posting_date_probe --course <id> [--year 2026]
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone

from src.builder.sources.moodle import MoodleClient, load_moodle_token, iter_section_files


def summarize_posting_dates(contents, semester_year: int) -> dict:
    months = []
    stale = 0
    for sf in iter_section_files(contents):
        if not sf.timemodified:
            continue
        d = datetime.fromtimestamp(sf.timemodified, tz=timezone.utc)
        months.append(f"{d.year}-{d.month:02d}")
        if semester_year and d.year < semester_year:
            stale += 1
    by_month = Counter(months)
    batch_month = by_month.most_common(1)[0][0] if by_month else ""
    off_batch = sum(c for m, c in by_month.items() if m != batch_month)
    return {"total": len(months), "stale": stale, "by_month": dict(sorted(by_month.items())),
            "batch_month": batch_month, "off_batch": off_batch}


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    course = year = ""
    if "--course" in argv:
        i = argv.index("--course"); course = argv[i + 1] if i + 1 < len(argv) else ""
    if "--year" in argv:
        i = argv.index("--year"); year = argv[i + 1] if i + 1 < len(argv) else ""
    if not course:
        print("uso: python -m scripts.posting_date_probe --course <id> [--year 2026]")
        return 2
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN."); return 2
    contents = MoodleClient(url, tok).get_course_contents(course)
    r = summarize_posting_dates(contents, int(year or 0))
    print(f"total={r['total']}  stale={r['stale']}  batch={r['batch_month']}  off_batch={r['off_batch']}")
    print(f"por mes: {r['by_month']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
