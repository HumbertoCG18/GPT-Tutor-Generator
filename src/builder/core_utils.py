from __future__ import annotations

import re
from typing import Dict, List

from src.utils.helpers import normalize_document_profile


def effective_document_profile(entry_profile: str | None, suggested_profile: str | None) -> str:
    if normalize_document_profile(entry_profile) != "auto":
        return normalize_document_profile(entry_profile)
    return normalize_document_profile(suggested_profile)


def persist_enriched_timeline_index(timeline_index: dict) -> dict:
    payload = {
        key: value
        for key, value in dict(timeline_index or {}).items()
        if key not in {"version", "blocks"}
    }
    blocks = []
    for block in (timeline_index or {}).get("blocks", []) or []:
        if not isinstance(block, dict):
            continue
        block_payload = dict(block)
        block_payload.pop("rows", None)
        for key in ("topics", "aliases", "topic_candidates", "source_rows", "sessions", "card_evidence"):
            value = block_payload.get(key, [])
            if value is None:
                block_payload[key] = []
            elif isinstance(value, list):
                block_payload[key] = list(value)
            else:
                block_payload[key] = [value]
        blocks.append(block_payload)
    payload["version"] = 3
    payload["blocks"] = blocks
    return payload


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def strip_topic_prefix(text: str) -> str:
    cleaned = collapse_ws(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned)
    cleaned = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(especificacao|especificação)\s+de\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -:\t")


def topic_support_tokens(text: str, *, normalize_match_text_fn) -> set:
    normalized = normalize_match_text_fn(strip_topic_prefix(text))
    return {
        token[:5] if len(token) >= 5 else token
        for token in normalized.split()
        if len(token) >= 4 and token not in {"sobre", "para", "com", "sem", "entre"}
    }


def merge_manual_and_auto_tags(
    manual_tags: List[str],
    auto_tags: List[str],
    *,
    fallback_tags: str = "",
    limit: int = 3,
) -> str:
    fallback_parts = [part.strip() for part in str(fallback_tags or "").replace(",", ";").split(";") if part.strip()]
    merged: List[str] = []
    seen = set()
    for tag in list(manual_tags or []) + list(auto_tags or []):
        cleaned = str(tag).strip()
        if not cleaned or cleaned in seen:
            continue
        merged.append(cleaned)
        seen.add(cleaned)
        if len(merged) >= limit:
            return "; ".join(merged)
    for tag in fallback_parts:
        if tag not in seen:
            merged.append(tag)
            seen.add(tag)
            if len(merged) >= limit:
                break
    return "; ".join(merged)


def pdf_image_extraction_policy(
    *,
    entry_profile: str | None,
    suggested_profile: str | None,
    suspected_scan: bool,
    default_min_bytes: int,
    default_min_dimension: int,
    default_max_aspect_ratio: float,
) -> Dict[str, object]:
    effective_profile = effective_document_profile(entry_profile, suggested_profile)
    if effective_profile in {"math_heavy", "scanned"} or suspected_scan:
        return {
            "mode": "permissive",
            "min_bytes": 512,
            "min_dimension": 8,
            "max_aspect_ratio": 20.0,
            "keep_low_color": True,
        }
    if effective_profile == "diagram_heavy":
        return {
            "mode": "balanced",
            "min_bytes": 1200,
            "min_dimension": 16,
            "max_aspect_ratio": 12.0,
            "keep_low_color": True,
        }
    return {
        "mode": "standard",
        "min_bytes": default_min_bytes,
        "min_dimension": default_min_dimension,
        "max_aspect_ratio": default_max_aspect_ratio,
        "keep_low_color": False,
    }
