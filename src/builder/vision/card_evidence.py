"""Pure helpers to extract lightweight card evidence from text."""

from __future__ import annotations

import re
import unicodedata

_CARD_RE = re.compile(r"(?im)(?:^|[\n;]\s*)\s*card\s*[:\-]\s*(?P<title>[^;\n]+)")
_TOPICO_RE = re.compile(r"(?im)(?:^|[\n;]\s*)\s*(?:topico|t[oó]pico)\s*[:\-]\s*(?P<title>[^;\n]+)")


def _normalize_match_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "")).strip(" \t\r\n-:;,.")


def _build_item(title: str, source_kind: str) -> dict[str, str]:
    cleaned = _clean_title(title)
    if not cleaned:
        return {}
    return {
        "title": cleaned,
        "normalized_title": _normalize_match_text(cleaned),
        "date": "",
        "source_kind": source_kind,
    }


def extract_card_evidence(text: str) -> list[dict[str, str]]:
    """Extract lightweight card evidence from linearized text.

    Recognizes the conservative forms:
    - ``Card: <title>``
    - ``Topico: <title>`` / ``Tópico: <title>``
    """

    if not text:
        return []

    items: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for match in _CARD_RE.finditer(text):
        item = _build_item(match.group("title"), "card-title")
        if not item:
            continue
        key = (item["source_kind"], item["normalized_title"])
        if key in seen:
            continue
        seen.add(key)
        items.append(item)

    for match in _TOPICO_RE.finditer(text):
        item = _build_item(match.group("title"), "topic-title")
        if not item:
            continue
        key = (item["source_kind"], item["normalized_title"])
        if key in seen:
            continue
        seen.add(key)
        items.append(item)

    return items
