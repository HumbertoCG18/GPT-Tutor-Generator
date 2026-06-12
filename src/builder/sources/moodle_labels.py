"""Parser dos labels temporais dos cards Moodle — formatos A-D do catálogo.

Cf. docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md. Funções puras
(recebem o payload de core_course_get_contents); nunca inventam: seção sem
sinal temporal fica FORA do resultado (formato E = degradação honesta).
"""
from __future__ import annotations

import html
import re
from datetime import date

from src.builder.sources.moodle import sanitize_folder_name

_WEEK_FULL = re.compile(r"Semana\s+(\d{1,2}/\d{1,2}/\d{4})\s*a\s*(\d{1,2}/\d{1,2}/\d{4})")
_LESSON_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)\s*:\s*(.+)")
_LOOSE_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)")
_ASYNC = re.compile(r"\(atividade\s+ass[ií]ncrona\)", re.IGNORECASE)


def _strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", s or ""))


def _iso(raw: str, year: int | None = None) -> str:
    """DD/MM[/AAAA] -> ISO; '' se inválida (30/02 etc.)."""
    parts = raw.split("/")
    try:
        d, m = int(parts[0]), int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else int(year or 0)
        return date(y, m, d).isoformat()
    except (ValueError, IndexError):
        return ""


def _label_texts(sec: dict) -> list:
    return [_strip_html(m.get("description") or m.get("name") or "")
            for m in sec.get("modules", []) or [] if m.get("modname") == "label"]


def _parse_format_a(texts: list) -> dict | None:
    weeks, lessons, dates = [], [], []
    for txt in texts:
        for line in txt.splitlines():
            line = line.strip()
            if not line or _ASYNC.search(line):
                continue
            w = _WEEK_FULL.search(line)
            if w:
                a, b = _iso(w.group(1)), _iso(w.group(2))
                if a and b:
                    weeks.append((a, b))
                continue
            l = _LESSON_FULL.search(line)
            if l:
                d = _iso(l.group(1))
                if d:
                    lessons.append({"date": d, "text": l.group(2).strip().rstrip(";.")})
                    dates.append(d)
                continue
            for m in _LOOSE_FULL.finditer(line):
                d = _iso(m.group(1))
                if d:
                    dates.append(d)
    if not dates and not weeks:
        return None
    return {"format": "A", "dates": sorted(set(dates)), "weeks": weeks, "lessons": lessons}


def parse_card_dates(contents, year: int, week_anchor: str = "") -> dict:
    """{secao_sanitizada: {format, dates[iso], weeks[(ini,fim)], lessons}}.

    Cascata A -> B -> C -> D por seção (Tasks 1-2 implementam A; B-D na Task 2).
    Seção sem sinal -> fora do dict."""
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        texts = _label_texts(sec)
        parsed = _parse_format_a(texts)
        if parsed:
            out[name] = parsed
    return out
