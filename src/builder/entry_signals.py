from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Dict, List

from src.builder.content_taxonomy import extract_markdown_lead_text


def normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("propocional", "proposicional")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score_text_against_row(source_text: str, row_tokens: List[str], *, weight: float = 1.0) -> float:
    if not source_text or not row_tokens:
        return 0.0

    source_tokens = [tok for tok in source_text.split() if len(tok) >= 4]
    score = 0.0
    for source_token in source_tokens:
        for row_token in row_tokens:
            if source_token == row_token:
                score += 1.0 * weight
            elif source_token in row_token or row_token in source_token:
                score += 0.45 * weight
            elif len(source_token) >= 5 and len(row_token) >= 5 and source_token[:5] == row_token[:5]:
                score += 0.2 * weight
    return score


def entry_image_source_dirs(root_dir: Path, entry: dict) -> List[Path]:
    dirs: List[Path] = []
    entry_id = str(entry.get("id") or "").strip()
    if entry_id:
        dirs.append(root_dir / "staging" / "assets" / "inline-images" / entry_id)
    images_dir = entry.get("images_dir")
    if images_dir:
        dirs.append(root_dir / images_dir)
    rendered_pages_dir = entry.get("rendered_pages_dir")
    if rendered_pages_dir:
        dirs.append(root_dir / rendered_pages_dir)
    return dirs


def _extract_markdown_headings(raw_markdown: str, limit: int = 8) -> List[str]:
    headings: List[str] = []
    for line in (raw_markdown or "").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = re.sub(r"\s+", " ", match.group(1)).strip()
        if not heading:
            continue
        headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def _merge_manual_and_auto_tags(
    manual_tags: List[str],
    auto_tags: List[str],
    *,
    fallback_tags: str = "",
    limit: int = 6,
) -> str:
    fallback_parts = [part.strip() for part in str(fallback_tags or "").replace(",", ";").split(";") if part.strip()]
    merged: List[str] = []
    seen = set()
    for tag in [*manual_tags, *auto_tags, *fallback_parts]:
        cleaned = str(tag or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        merged.append(cleaned)
        if len(merged) >= limit:
            break
    return "; ".join(merged)


def collect_entry_unit_signals(entry: dict, markdown_text: str) -> Dict[str, str]:
    manual_tags = [str(tag).strip() for tag in (entry.get("manual_tags") or []) if str(tag).strip()]
    auto_tags = [str(tag).strip() for tag in (entry.get("auto_tags") or []) if str(tag).strip()]
    legacy_tags = [
        part.strip()
        for part in str(entry.get("tags", "") or "").replace(",", ";").split(";")
        if part.strip()
    ]
    merged_tags = _merge_manual_and_auto_tags(
        manual_tags,
        auto_tags,
        fallback_tags="; ".join(legacy_tags),
        limit=6,
    )
    return {
        "title_text": normalize_match_text(entry.get("title", "")),
        "markdown_headings_text": normalize_match_text(" ".join(_extract_markdown_headings(markdown_text))),
        "markdown_lead_text": normalize_match_text(extract_markdown_lead_text(markdown_text)),
        "category_text": normalize_match_text(entry.get("category", "")),
        "manual_tags_text": normalize_match_text("; ".join(manual_tags)),
        "auto_tags_text": normalize_match_text("; ".join(auto_tags)),
        "legacy_tags_text": normalize_match_text("; ".join(legacy_tags)),
        "tags_text": normalize_match_text(merged_tags),
        "raw_text": normalize_match_text(entry.get("raw_target", "")),
        "markdown_text": normalize_match_text(markdown_text),
    }
