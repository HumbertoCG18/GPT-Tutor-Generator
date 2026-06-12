from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.builder.extraction.content_taxonomy import (
    _extract_markdown_headings,
    extract_markdown_lead_text,
)
from src.builder.text.normalize import (  # noqa: F401  (re-export)
    normalize_match_text,
    split_camel_case,
)


def score_text_against_row(
    source_text: str,
    row_tokens: List[str],
    *,
    weight: float = 1.0,
    token_weights: Dict[str, float] | None = None,
) -> float:
    # S2 (P4): token_weights (token -> peso efetivo, cf.
    # file_map.block_token_weights) multiplica a contribuição POR row_token —
    # tokens raros entre os candidatos pesam mais. None = peso 1.0 para todos
    # (comportamento anterior EXATO).
    if not source_text or not row_tokens:
        return 0.0

    source_tokens = [tok for tok in source_text.split() if len(tok) >= 4]
    score = 0.0
    for source_token in source_tokens:
        for row_token in row_tokens:
            token_weight = 1.0 if token_weights is None else float(token_weights.get(row_token, 1.0))
            if source_token == row_token:
                score += 1.0 * weight * token_weight
            elif source_token in row_token or row_token in source_token:
                score += 0.45 * weight * token_weight
            elif len(source_token) >= 5 and len(row_token) >= 5 and source_token[:5] == row_token[:5]:
                score += 0.2 * weight * token_weight
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
    # S4 (P4): valores das auto_tags `ferramenta:` em campo próprio — o scorer
    # de bloco (file_map, TOOL_TOKENS) filtra quais são ferramentas de verdade.
    tool_values = [
        tag.split(":", 1)[1].strip()
        for tag in auto_tags
        if tag.lower().startswith("ferramenta:")
    ]
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
    image_description = str(entry.get("image_description", "") or "")
    extra_parts = [markdown_text or ""]
    notes = str(entry.get("notes", "") or "")
    if notes:
        extra_parts.append(notes)
    if image_description and image_description not in " ".join(extra_parts):
        extra_parts.append(image_description)
    effective_markdown = "\n".join(p for p in extra_parts if p).strip()
    return {
        # S1 (P4): split camelCase SÓ no título — "LogicaDeHoare2" vira
        # "logica de hoare 2" e casa com o topic do bloco. Markdown/tags intactos.
        "title_text": normalize_match_text(split_camel_case(entry.get("title", ""))),
        "markdown_headings_text": normalize_match_text(" ".join(_extract_markdown_headings(markdown_text))),
        "markdown_lead_text": normalize_match_text(extract_markdown_lead_text(markdown_text)),
        "category_text": normalize_match_text(entry.get("category", "")),
        "manual_tags_text": normalize_match_text("; ".join(manual_tags)),
        "auto_tags_text": normalize_match_text("; ".join(auto_tags)),
        "tool_tags_text": normalize_match_text(" ".join(tool_values)),
        "legacy_tags_text": normalize_match_text("; ".join(legacy_tags)),
        "tags_text": normalize_match_text(merged_tags),
        "raw_text": normalize_match_text(entry.get("raw_target", "")),
        "image_description_text": normalize_match_text(image_description),
        "markdown_text": normalize_match_text(effective_markdown),
    }

