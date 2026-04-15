"""Pure temporal signal extraction helpers.

These helpers only inspect text. They do not depend on UI objects or repo
state, so they can be reused by timeline builders and tests.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime

_DATE_RE = r"\d{2}/\d{2}/\d{4}"
_DATE_RANGE_RE = re.compile(
    rf"\b(?:semana\s+)?(?P<start>{_DATE_RE})\s*(?:a|ate|-)\s*(?P<end>{_DATE_RE})\b",
    re.IGNORECASE,
)
_SESSION_RE = re.compile(
    rf"(?:^|[\n;]\s*|:\s*)\s*(?:[-*•]\s*)?\(?\s*(?P<label>(?:{_DATE_RE})|(?:atividade\s+assincrona|assincrona|atividade\s+async|async))\s*\)?\s*(?:[a-z]{{3}}\s+)?\s*[:\-–—]\s*(?P<body>[^;\n]*)",
    re.IGNORECASE,
)
_PREFIXED_SESSION_RE = re.compile(
    rf"(?:^|[\n;]\s*|:\s*)\s*(?:[-*•]\s*)?(?P<prefix>(?:aula|encontro|reuniao|atividade(?:\s+assincrona|(?:\s+async)?)?))\s+"
    rf"(?P<date>{_DATE_RE})(?:\s*(?:[:\-–—]\s*)?(?P<body>[^;\n]*))?",
    re.IGNORECASE,
)


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_match_text(text: str) -> str:
    text = _strip_accents(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_timeline_text(text: str) -> str:
    return _strip_accents(text or "").lower().strip()


def _parse_date(raw: str) -> str:
    try:
        return datetime.strptime(raw, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _build_signal_terms(text: str) -> list[str]:
    normalized = _normalize_match_text(text)
    if not normalized:
        return []

    tokens = normalized.split()
    seen: set[str] = set()
    terms: list[str] = []

    def add(value: str) -> None:
        value = value.strip()
        if not value or value in seen:
            return
        seen.add(value)
        terms.append(value)

    add(normalized)
    for token in tokens:
        add(token)
    for size in range(2, min(4, len(tokens)) + 1):
        for idx in range(len(tokens) - size + 1):
            add(" ".join(tokens[idx : idx + size]))

    return terms


def extract_date_range_signal(text: str) -> dict[str, str]:
    """Extract a weekly date range from free text.

    Returns an empty dict when no range is found.
    """

    normalized = _normalize_timeline_text(text)
    match = _DATE_RANGE_RE.search(normalized)
    if not match:
        return {}

    start = _parse_date(match.group("start"))
    end = _parse_date(match.group("end"))
    if not start or not end:
        return {}

    return {
        "start": start,
        "end": end,
        "label": f"{match.group('start')} a {match.group('end')}",
    }


def extract_timeline_session_signals(text: str) -> list[dict[str, object]]:
    """Extract session-like temporal cues from free text.

    The extractor recognizes:
    - inline class dates like ``(30/03/2026): Text``
    - plain class dates like ``30/03/2026: Text``
    - async markers like ``(atividade assíncrona): Text``
    - linearized HTML text like ``Aula 30/03/2026 Text``
    """

    normalized = _normalize_timeline_text(text)
    if not normalized:
        return []

    sessions: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for match in _PREFIXED_SESSION_RE.finditer(normalized):
        prefix_raw = match.group("prefix").strip()
        raw_body = match.group("body") or ""
        if "⊘" in raw_body:
            continue
        body_raw = raw_body.strip(" \t-:;.,")
        prefix_norm = _normalize_match_text(prefix_raw)
        body_norm = _normalize_match_text(body_raw)
        date = _parse_date(match.group("date"))

        if "assincr" in prefix_norm or "async" in prefix_norm:
            kind = "async"
        else:
            kind = "class"
        label = body_norm or prefix_norm

        signals = []
        if date:
            signals.append(date)
        signals.extend(_build_signal_terms(prefix_raw))
        signals.extend(_build_signal_terms(body_raw))

        dedupe_key = (kind, date, label, body_norm)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        sessions.append(
            {
                "kind": kind,
                "date": date,
                "label": label,
                "signals": signals,
            }
        )

    for match in _SESSION_RE.finditer(normalized):
        label_raw = match.group("label").strip()
        raw_body = match.group("body") or ""
        if "⊘" in raw_body:
            continue
        body_raw = raw_body.strip(" \t-:;.,")
        label_norm = _normalize_match_text(label_raw)
        body_norm = _normalize_match_text(body_raw)

        if "assincr" in label_norm or "async" in label_norm:
            kind = "async"
            date = ""
            label = body_norm or label_norm
        else:
            kind = "class"
            date = _parse_date(label_raw)
            label = body_norm or label_norm

        signals = []
        if date:
            signals.append(date)
        signals.extend(_build_signal_terms(label_raw))
        signals.extend(_build_signal_terms(body_raw))

        dedupe_key = (kind, date, label, body_norm)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        sessions.append(
            {
                "kind": kind,
                "date": date,
                "label": label,
                "signals": signals,
            }
        )

    return sessions
