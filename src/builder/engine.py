from __future__ import annotations
import csv
import difflib
import html as html_lib
import importlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.builder.datalab_client import (
    convert_document_to_markdown,
    get_datalab_base_url,
    has_datalab_api_key,
)
from src.builder.image_markdown import (
    _IMAGE_DESC_BLOCK_RE,
    _image_curation_heading as _image_curation_heading_label,
    _low_token_inject_image_descriptions,
)
from src.builder.prompt_generation import (
    generate_claude_project_instructions,
    generate_gemini_instructions,
    generate_gpt_instructions,
)
from src.builder import student_state as student_state_v2
from src.builder.pedagogical_prompts import (
    _code_review_profile,
    modes_md,
    output_templates_md,
    pedagogy_md,
    tutor_policy_md,
)
from src.builder.navigation_artifacts import (
    _clean_extraction_noise,
    _entry_markdown_path_for_file_map,
    _entry_markdown_text_for_file_map,
    _entry_priority_label,
    _entry_usage_hint,
    _extract_section_headers,
    _file_map_markdown_cell,
    _get_entry_sections,
    _inject_executive_summary,
    _infer_unit_confidence,
    render_low_token_course_map_md,
    render_low_token_course_map_md_v2,
    render_low_token_file_map_md,
)
from src.builder import content_taxonomy as _content_taxonomy
from src.builder.semantic_config import (
    infer_semantic_profile,
    merge_semantic_profile,
    resolve_semantic_profile,
    write_internal_semantic_profile,
)
from src.builder.timeline_index import (
    TopicMatchResult,
    _assign_timeline_block_to_topic,
    _build_timeline_candidate_rows,
    _build_timeline_block_topic_signals,
    _build_timeline_index,
    _derive_unit_from_topic_match,
    _empty_timeline_index,
    _iter_content_taxonomy_topics,
    _infer_timeline_keys,
    _parse_syllabus_timeline,
    _parse_timeline_date_value,
    _parse_timeline_period_bounds,
    _row_looks_like_continuation,
    _rows_belong_to_same_thematic_block,
    _score_entry_against_taxonomy_topic,
    _score_timeline_block_against_taxonomy_topic,
    _score_timeline_row_against_unit,
    _score_timeline_unit_phrase,
    _serialize_timeline_index,
    _timeline_block_is_administrative_only,
    _timeline_block_is_noninstructional,
    _timeline_block_is_soft_continuation,
    _timeline_core_text,
    _timeline_period_label,
    _timeline_row_is_review_or_assessment,
    _timeline_unit_number_from_text,
    _timeline_unit_number_from_unit,
    _TIMELINE_UNIT_NEUTRAL_TOKENS,
    _timeline_row_is_unit_anchor_only,
    _timeline_specific_tokens,
    _timeline_text_is_administrative,
    _extract_timeline_topics,
    _assign_timeline_block_to_unit,
    _write_internal_timeline_index,
)
from src.builder.timeline_signals import (
    extract_date_range_signal,
    extract_timeline_session_signals,
)
from src.models.core import (
    BackendRunResult, DocumentProfileReport, FileEntry,
    PipelineDecision, StudentProfile, SubjectProfile
)
from src.utils.helpers import (
    APP_NAME, DEFAULT_OCR_LANGUAGE, DOCLING_CLI, EXAM_CATEGORIES, EXERCISE_CATEGORIES,
    HAS_PDFPLUMBER, HAS_PYMUPDF, HAS_PYMUPDF4LLM, IMAGE_CATEGORIES, MARKER_CLI,
    CODE_EXTENSIONS, LANG_MAP, CODE_CATEGORIES, ASSIGNMENT_CATEGORIES,
    WHITEBOARD_CATEGORIES, STUDENT_BRANCHES,
    ensure_dir, json_str, pages_to_marker_range,
    normalize_document_profile, parse_page_range, safe_rel, slugify, write_text,
)
from src.utils.power import prevent_system_sleep

if HAS_PYMUPDF:
    import pymupdf
if HAS_PYMUPDF4LLM:
    import pymupdf4llm
if HAS_PDFPLUMBER:
    import pdfplumber

logger = logging.getLogger(__name__)

_DOCLING_PYTHON_API_CACHE = None


def _effective_document_profile(entry_profile: str | None, suggested_profile: str | None) -> str:
    if normalize_document_profile(entry_profile) != "auto":
        return normalize_document_profile(entry_profile)
    return normalize_document_profile(suggested_profile)


def _persist_enriched_timeline_index(timeline_index: dict) -> dict:
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


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _strip_topic_prefix(text: str) -> str:
    cleaned = _collapse_ws(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned)
    cleaned = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(especificacao|especificação)\s+de\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -:\t")


def _looks_like_tool_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    known_tools = list(effective_profile.get("known_tools") or [])
    return any(tool in normalized for tool in known_tools)


def _looks_like_bibliography_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    markers = list(effective_profile.get("bibliography_markers") or [])
    if any(marker in normalized for marker in markers):
        return True
    if re.search(r"\b(19|20)\d{2}\b", normalized):
        return True
    if normalized.count(" ") >= 9:
        return True
    if normalized.count("-") >= 2:
        return True
    if len(re.findall(r"\b[a-z]\b", normalized)) >= 3:
        return True
    return False


def _looks_like_goal_or_section_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    structural_headings = set(effective_profile.get("tag_structural_headings") or [])
    if normalized in structural_headings:
        return True
    if normalized.startswith(("entender ", "aprender ", "adquirir ", "julgar ", "compreender ")):
        return True
    if normalized.endswith((" software", " sistemas", " programas")) and normalized.count(" ") >= 5:
        return True
    return False


def _looks_like_weak_heading_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    if normalized in {"revisao", "exercicios", "atividade assincrona"}:
        return True
    effective_profile = merge_semantic_profile(semantic_profile)
    weak_heading_starters = tuple(effective_profile.get("weak_heading_starters") or [])
    if normalized.startswith(weak_heading_starters):
        return True
    if len(normalized.split()) > 6:
        return True
    return False


def _is_valid_topic_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    slug = slugify(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    generic_slugs = set(effective_profile.get("tag_generic_slugs") or [])
    if not slug or slug in generic_slugs:
        return False
    if len(slug) < 4:
        return False
    if _looks_like_weak_heading_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_tool_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_bibliography_candidate(text, semantic_profile=semantic_profile):
        return False
    if _looks_like_goal_or_section_candidate(text, semantic_profile=semantic_profile):
        return False
    return True


def _extract_topic_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
    candidates: List[str] = []
    seen = set()
    for source in sources:
        for raw_line in (source or "").splitlines():
            line = _collapse_ws(raw_line)
            if not line:
                continue
            if line.startswith("## "):
                line = line[3:].strip()
            elif line.startswith("- [ ] "):
                line = line[6:].strip()
            elif line.startswith("- "):
                line = line[2:].strip()
            elif not re.match(r"^(?:\d+(?:\.\d+)*\.?|unidade\s+\d+)", line, flags=re.IGNORECASE):
                continue
            line = _strip_topic_prefix(line)
            slug = slugify(line)
            if not _is_valid_topic_candidate(line, semantic_profile=semantic_profile) or slug in seen:
                continue
            seen.add(slug)
            candidates.append(line)
    return candidates


def _extract_tool_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
    found: List[str] = []
    seen = set()
    effective_profile = merge_semantic_profile(semantic_profile)
    known_tools = sorted(
        list(effective_profile.get("known_tools") or []),
        key=len,
        reverse=True,
    )
    for source in sources:
        normalized = _normalize_match_text(source or "")
        for tool in known_tools:
            tool_norm = _normalize_match_text(tool)
            if tool_norm and tool_norm in normalized and tool_norm not in seen:
                seen.add(tool_norm)
                found.append(tool)
    return found


def _topic_support_tokens(text: str) -> set:
    normalized = _normalize_match_text(_strip_topic_prefix(text))
    return {
        token[:5] if len(token) >= 5 else token
        for token in normalized.split()
        if len(token) >= 4 and token not in {"sobre", "para", "com", "sem", "entre"}
    }


def _select_supported_taxonomy_topic(
    candidate: str,
    topic_records: List[dict],
    semantic_profile: Optional[dict] = None,
) -> Optional[dict]:
    candidate_norm = _normalize_match_text(candidate)
    candidate_tokens = _topic_support_tokens(candidate)
    if not candidate_norm or not candidate_tokens:
        return None

    best_topic: Optional[dict] = None
    best_score = 0.0
    for topic in topic_records or []:
        base_label = _collapse_ws(str(topic.get("label", "") or ""))
        base_norm = _normalize_match_text(base_label)
        base_tokens = _topic_support_tokens(base_label)
        if not base_norm or not base_tokens:
            continue

        overlap = candidate_tokens & base_tokens
        score = 0.0
        if candidate_norm == base_norm:
            score = 10.0
        elif candidate_norm in base_norm or base_norm in candidate_norm:
            score = 8.0
        elif len(overlap) >= 2:
            score = 5.5 + (0.4 * len(overlap))
        elif len(overlap) == 1 and 2 <= len(candidate_tokens) <= 6:
            effective_profile = merge_semantic_profile(semantic_profile)
            overlap_cues = tuple(effective_profile.get("heading_single_overlap_cues") or [])
            if any(cue in candidate_norm for cue in overlap_cues):
                score = 3.4
            elif any(
                cue in candidate_norm
                for cue in ("recursiv", "indutiv", "predicad", "isabelle", "kripke", "modelo")
            ):
                score = 2.8
        if str(topic.get("kind", "") or "") == "subtopic":
            score += 0.08
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic if best_score >= 2.8 else None


def _heading_topic_has_vocab_support(
    candidate: str,
    base_topics: List[str],
    semantic_profile: Optional[dict] = None,
) -> bool:
    candidate_norm = _normalize_match_text(candidate)
    candidate_tokens = _topic_support_tokens(candidate)
    if not candidate_tokens:
        return False
    for base_topic in base_topics or []:
        base_norm = _normalize_match_text(base_topic)
        base_tokens = _topic_support_tokens(base_topic)
        if not base_tokens:
            continue
        if candidate_norm == base_norm or candidate_norm in base_norm or base_norm in candidate_norm:
            return True
        overlap = candidate_tokens & base_tokens
        if len(overlap) < 2:
            if len(overlap) == 1 and 2 <= len(candidate_tokens) <= 4:
                effective_profile = merge_semantic_profile(semantic_profile)
                overlap_cues = tuple(effective_profile.get("heading_single_overlap_cues") or [])
                if any(cue in candidate_norm for cue in overlap_cues):
                    return True
            continue
        candidate_extra = candidate_tokens - base_tokens
        base_extra = base_tokens - candidate_tokens
        # Intermediate mode: allow only close variants of an official topic.
        # Either the heading is a short refinement of the official topic
        # ("funcoes recursivas" -> "funcoes recursivas sobre arvores"),
        # or it is a short, faithful shortening of the official topic
        # ("fundamentos de logica de primeira ordem" -> "logica de primeira ordem").
        if overlap == base_tokens and len(candidate_extra) <= 1:
            return True
        if overlap == candidate_tokens and len(base_extra) <= 1:
            return True
    return False


def _build_tag_catalog(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
) -> dict:
    return _content_taxonomy.build_tag_catalog(
        teaching_plan=teaching_plan,
        course_map_md=course_map_md,
        glossary_md=glossary_md,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
    )


def _extract_topic_code(text: str) -> str:
    match = re.match(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+", _collapse_ws(text))
    return match.group(1) if match else ""


def _strip_topic_code(text: str) -> str:
    cleaned = _collapse_ws(text)
    if not cleaned:
        return ""
    return re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", cleaned).strip()


def _parse_glossary_terms(glossary_md: str) -> List[Dict[str, object]]:
    terms: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None

    def _flush() -> None:
        nonlocal current
        if current and current.get("term"):
            current["synonyms"] = sorted(
                dict.fromkeys(
                    _collapse_ws(item)
                    for item in current.get("synonyms", [])
                    if _collapse_ws(item)
                )
            )
            terms.append(current)
        current = None

    for raw_line in (glossary_md or "").splitlines():
        line = _collapse_ws(raw_line)
        if not line:
            continue
        if line.startswith("## "):
            _flush()
            current = {
                "term": _collapse_ws(line[3:]),
                "unit_hint": "",
                "synonyms": [],
                "definition": "",
            }
            continue
        if current is None:
            continue

        match = re.match(r"^\*\*Sin[ôo]nimos aceitos:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            values = [item.strip() for item in re.split(r"[,;/|]", match.group(1)) if item.strip()]
            current.setdefault("synonyms", []).extend(values)
            continue

        match = re.match(r"^\*\*Aparece em:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            current["unit_hint"] = _collapse_ws(match.group(1))
            continue

        match = re.match(r"^\*\*Defini[çc][ãa]o:\*\*\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            current["definition"] = _collapse_ws(match.group(1))
            continue

    _flush()
    return terms


def _glossary_aliases_for_topic(topic_label: str, unit_title: str, glossary_terms: List[Dict[str, object]]) -> List[str]:
    topic_norm = _normalize_match_text(topic_label)
    unit_norm = _normalize_match_text(unit_title)
    aliases: List[str] = []
    seen = set()

    for term in glossary_terms or []:
        term_text = _collapse_ws(str(term.get("term", "")))
        if not term_text:
            continue
        term_norm = _normalize_match_text(term_text)
        if not term_norm:
            continue

        unit_hint = _normalize_match_text(str(term.get("unit_hint", "")))
        if unit_hint and unit_hint not in unit_norm and unit_norm not in unit_hint:
            continue

        if term_norm == topic_norm or term_norm in topic_norm or topic_norm in term_norm:
            for candidate in [term_text, *list(term.get("synonyms", []) or [])]:
                candidate_text = _collapse_ws(candidate)
                candidate_slug = slugify(candidate_text)
                if not candidate_text or not candidate_slug or candidate_slug in seen:
                    continue
                seen.add(candidate_slug)
                aliases.append(candidate_text)

    return aliases


def _dedupe_taxonomy_topics(topics: List[dict]) -> List[dict]:
    merged: Dict[str, dict] = {}
    for topic in topics or []:
        slug = _normalize_match_text(str(topic.get("slug", "") or ""))
        if not slug:
            continue
        current = merged.setdefault(slug, {
            "code": str(topic.get("code", "") or ""),
            "slug": str(topic.get("slug", "") or ""),
            "label": _collapse_ws(str(topic.get("label", "") or "")),
            "aliases": [],
            "kind": str(topic.get("kind", "") or "topic"),
            "unit_slug": str(topic.get("unit_slug", "") or ""),
        })
        current["code"] = current["code"] or str(topic.get("code", "") or "")
        current["label"] = current["label"] or _collapse_ws(str(topic.get("label", "") or ""))
        current["kind"] = current["kind"] or str(topic.get("kind", "") or "topic")
        current["unit_slug"] = current["unit_slug"] or str(topic.get("unit_slug", "") or "")
        for alias in topic.get("aliases", []) or []:
            alias_text = _collapse_ws(str(alias))
            alias_slug = slugify(alias_text)
            if alias_text and alias_slug and alias_slug not in {slugify(item) for item in current["aliases"]}:
                current["aliases"].append(alias_text)
    for topic in merged.values():
        topic["aliases"] = sorted(dict.fromkeys(alias for alias in topic.get("aliases", []) if _collapse_ws(alias)))
    return list(merged.values())


def _infer_course_slug_from_units(units: List[tuple]) -> str:
    if not units:
        return ""
    first_title = _strip_outline_prefix(units[0][0] if isinstance(units[0], tuple) else str(units[0].get("title", "")))
    return slugify(first_title)


def _build_content_taxonomy(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
) -> dict:
    return _content_taxonomy.build_content_taxonomy(
        teaching_plan=teaching_plan,
        course_map_md=course_map_md,
        glossary_md=glossary_md,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text,
        normalize_unit_slug=_normalize_unit_slug,
    )


def _write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
    write_text(
        root_dir / "course" / ".content_taxonomy.json",
        json.dumps(taxonomy, ensure_ascii=False, indent=2),
    )


def _extract_markdown_lead_text(markdown_text: str, max_chars: int = 2600) -> str:
    stripped = _strip_frontmatter_block(markdown_text or "")
    compact = _collapse_ws(stripped)
    if len(compact) <= max_chars:
        return compact
    clipped = compact[:max_chars]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.strip()


def _collect_strong_heading_candidates(root_dir: Optional[Path], manifest_entries: Optional[List[dict]]) -> List[str]:
    return _content_taxonomy.collect_strong_heading_candidates(root_dir, manifest_entries)


def _entry_tag_signal_text(entry: dict, markdown_text: str) -> str:
    parts = [
        entry.get("title", ""),
        entry.get("category", ""),
        entry.get("notes", ""),
        entry.get("professor_signal", ""),
        entry.get("raw_target", ""),
        markdown_text,
    ]
    return _normalize_match_text(" ".join(part for part in parts if part))


def _signal_token_set(signal_text: str) -> set:
    return {
        token
        for token in _normalize_match_text(signal_text).split()
        if len(token) >= 4
    }


def _matches_tag_slug(signal_text: str, tag_slug: str) -> bool:
    normalized_signal = _normalize_match_text(signal_text)
    normalized_slug = _normalize_match_text(tag_slug.replace("-", " "))
    if not normalized_slug or not normalized_signal:
        return False
    if normalized_slug in normalized_signal:
        return True
    tokens = [tok for tok in normalized_slug.split() if len(tok) >= 4]
    if not tokens:
        return False
    signal_tokens = _signal_token_set(normalized_signal)
    direct_hits = sum(1 for token in tokens if token in signal_tokens)
    if len(tokens) == 1:
        token = tokens[0]
        if len(token) < 5:
            return False
        return direct_hits == 1
    if direct_hits == len(tokens):
        return True
    return False


def _infer_entry_auto_tags(entry: dict, markdown_text: str, vocabulary: dict) -> List[str]:
    return _content_taxonomy.infer_entry_auto_tags(entry, markdown_text, vocabulary)


def _write_tag_catalog(
    root_dir: Path,
    subject_profile: Optional[SubjectProfile],
    manifest_entries: Optional[List[dict]],
    *,
    course_map_text: str,
    glossary_text: str,
) -> dict:
    return _content_taxonomy.write_tag_catalog(
        root_dir,
        course_name=(subject_profile.name if subject_profile and subject_profile.name else root_dir.name),
        teaching_plan=getattr(subject_profile, "teaching_plan", "") or "",
        course_map_text=course_map_text,
        glossary_text=glossary_text,
        manifest_entries=manifest_entries,
    )


def _refresh_manifest_auto_tags(root_dir: Path, manifest_entries: List[dict], vocabulary: dict) -> List[dict]:
    return _content_taxonomy.refresh_manifest_auto_tags(
        root_dir,
        manifest_entries,
        vocabulary,
        entry_markdown_text_for_file_map=_entry_markdown_text_for_file_map,
    )


def _merge_manual_and_auto_tags(
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


def _strip_frontmatter_block(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text or "", flags=re.DOTALL)


def _rewrite_markdown_asset_paths(markdown: str, source_dir: Path, target_dir: Path) -> str:
    """Rewrite relative markdown asset links from one directory base to another."""
    pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def _replace(match):
        alt = match.group(1)
        raw_path = match.group(2)
        if re.match(r"^[a-z]+://", raw_path, re.IGNORECASE):
            return match.group(0)
        if raw_path.startswith("/"):
            return match.group(0)
        source_path = (source_dir / raw_path).resolve()
        try:
            rel = os.path.relpath(source_path, target_dir)
        except Exception:
            rel = raw_path
        return f"![{alt}]({str(rel).replace(os.sep, '/')})"

    return pattern.sub(_replace, markdown)


def _strip_markdown_image_refs(markdown: str) -> str:
    if not markdown:
        return markdown
    stripped = re.sub(r"(?m)^[ \t]*!\[[^\]]*\]\([^)]+\)[ \t]*\n?", "", markdown)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    normalized = stripped.strip()
    return normalized + ("\n" if normalized else "")


def _build_page_chunks(pages: Optional[List[int]], page_count: int, chunk_size: int = 20) -> List[List[int]]:
    selected = sorted(pages if pages is not None else list(range(page_count)))
    if not selected:
        return []
    return [selected[i:i + chunk_size] for i in range(0, len(selected), chunk_size)]


def _build_marker_page_chunks(pages: Optional[List[int]], page_count: int, chunk_size: int = 20) -> List[List[int]]:
    """Split marker work into smaller page chunks to reduce long silent stalls."""
    return _build_page_chunks(pages, page_count, chunk_size=chunk_size)


def _selected_page_count(ctx: "BackendContext") -> int:
    if ctx.pages is not None:
        return len(ctx.pages)
    return max(int(ctx.report.page_count or 0), 0)


def _prepare_docling_python_source_pdf(ctx: "BackendContext", out_dir: Path) -> tuple[Path, bool]:
    if not ctx.pages:
        return ctx.raw_target, False
    if not HAS_PYMUPDF:
        logger.warning(
            "  [docling_python] page_range solicitado, mas PyMuPDF nao esta disponivel; usando o PDF inteiro."
        )
        return ctx.raw_target, False

    sliced_pdf = out_dir / f"{ctx.entry_id}--selected-pages.pdf"
    src_doc = pymupdf.open(str(ctx.raw_target))
    dst_doc = pymupdf.open()
    try:
        valid_pages = [page for page in ctx.pages if 0 <= page < src_doc.page_count]
        if not valid_pages:
            logger.warning(
                "  [docling_python] page_range=%s nao gerou paginas validas; usando o PDF inteiro.",
                ctx.entry.page_range or "all",
            )
            return ctx.raw_target, False
        for page in valid_pages:
            dst_doc.insert_pdf(src_doc, from_page=page, to_page=page)
        dst_doc.save(str(sliced_pdf))
    finally:
        dst_doc.close()
        src_doc.close()

    return sliced_pdf, True


def _configure_docling_python_standard_gpu(api: dict, pipeline_options) -> dict:
    accelerator_options_cls = api.get("AcceleratorOptions")
    accelerator_device = api.get("AcceleratorDevice")
    rapid_ocr_options_cls = api.get("RapidOcrOptions")
    settings_obj = api.get("settings")

    gpu_config = {
        "enabled": False,
        "device": "auto",
        "ocr_batch_size": None,
        "layout_batch_size": None,
        "table_batch_size": None,
        "page_batch_size": None,
        "ocr_backend": None,
        "previous_page_batch_size": None,
    }

    if accelerator_options_cls and accelerator_device and hasattr(pipeline_options, "accelerator_options"):
        pipeline_options.accelerator_options = accelerator_options_cls(device=accelerator_device.CUDA)
        gpu_config["enabled"] = True
        gpu_config["device"] = str(accelerator_device.CUDA.value)

    if hasattr(pipeline_options, "ocr_batch_size"):
        pipeline_options.ocr_batch_size = 8
        gpu_config["ocr_batch_size"] = 8
    if hasattr(pipeline_options, "layout_batch_size"):
        pipeline_options.layout_batch_size = 8
        gpu_config["layout_batch_size"] = 8
    if hasattr(pipeline_options, "table_batch_size"):
        pipeline_options.table_batch_size = 4
        gpu_config["table_batch_size"] = 4

    if rapid_ocr_options_cls and hasattr(pipeline_options, "ocr_options"):
        pipeline_options.ocr_options = rapid_ocr_options_cls(backend="torch")
        gpu_config["ocr_backend"] = "torch"

    if settings_obj is not None and hasattr(settings_obj, "perf") and hasattr(settings_obj.perf, "page_batch_size"):
        gpu_config["previous_page_batch_size"] = int(settings_obj.perf.page_batch_size)
        settings_obj.perf.page_batch_size = max(int(settings_obj.perf.page_batch_size), 8)
        gpu_config["page_batch_size"] = int(settings_obj.perf.page_batch_size)

    return gpu_config


def _marker_chunk_size_for_workload(ctx: "BackendContext") -> int:
    effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = _selected_page_count(ctx)
    if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 80:
        return 10
    return 20


def _datalab_chunk_size_for_workload(ctx: "BackendContext") -> int:
    effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = _selected_page_count(ctx)
    if effective_profile == "math_heavy":
        return 15 if selected_pages >= 120 else 20
    if effective_profile in {"diagram_heavy", "scanned"}:
        return 20
    return 25


def _datalab_should_chunk(ctx: "BackendContext") -> bool:
    selected_pages = _selected_page_count(ctx)
    if selected_pages < 50:
        return False
    return selected_pages > _datalab_chunk_size_for_workload(ctx)


def _merge_numeric_dicts(items: List[Dict[str, object]]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for item in items:
        for key, value in (item or {}).items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                merged[key] = float(merged.get(key, 0) or 0) + value
    return merged


def _should_force_ocr_for_marker(ctx: "BackendContext") -> bool:
    return bool(ctx.entry.force_ocr) or bool(ctx.report.suspected_scan)


def _marker_should_use_llm(ctx: "BackendContext") -> bool:
    return bool(getattr(ctx, "marker_use_llm", False))


def _marker_ollama_model(ctx: "BackendContext") -> str:
    return str(getattr(ctx, "marker_llm_model", "") or "").strip()


def _marker_torch_device(ctx: "BackendContext") -> str:
    return str(getattr(ctx, "marker_torch_device", "") or "").strip().lower()


def _marker_effective_torch_device(ctx: "BackendContext") -> str:
    configured = _marker_torch_device(ctx)
    if configured and configured != "auto":
        return configured
    return "mps" if sys.platform == "darwin" else "cuda"


def _marker_model_slug(model: str) -> str:
    return str(model or "").strip().lower()


def _marker_model_is_qwen3_vl_8b(model: str) -> bool:
    slug = _marker_model_slug(model)
    return slug.startswith("qwen3-vl:8b") or slug == "qwen3-vl:8b"


def _marker_model_is_cloud_variant(model: str) -> bool:
    return "cloud" in _marker_model_slug(model)


def _marker_model_is_probably_vision(model: str) -> bool:
    slug = _marker_model_slug(model)
    return any(token in slug for token in ("-vl", "vision", "gemma3", "gemma4"))


def _marker_should_redo_inline_math(ctx: "BackendContext") -> bool:
    suggested_profile = str(getattr(ctx.report, "suggested_profile", "") or "").strip().lower()
    return bool(getattr(ctx.entry, "formula_priority", False)) or suggested_profile == "math_heavy"


def _marker_progress_hints(line: str, previous_phase: Optional[str]) -> tuple[Optional[str], list[str]]:
    phase = None
    hints: list[str] = []

    if ":" in line:
        phase = line.split(":", 1)[0].strip() or None
    if not phase:
        return previous_phase, hints

    if previous_phase != phase:
        hints.append(f"Fase detectada: {phase}")

    if "0it [00:00" in line.lower():
        hints.append(f"Fase '{phase}' concluída sem itens para processar.")

    return phase, hints


def _load_docling_python_api():
    global _DOCLING_PYTHON_API_CACHE

    if _DOCLING_PYTHON_API_CACHE is not None:
        return _DOCLING_PYTHON_API_CACHE

    try:
        document_converter = importlib.import_module("docling.document_converter")
        pipeline_options = importlib.import_module("docling.datamodel.pipeline_options")
        base_models = importlib.import_module("docling.datamodel.base_models")
        accelerator_options = importlib.import_module("docling.datamodel.accelerator_options")
        settings_module = importlib.import_module("docling.datamodel.settings")
        _DOCLING_PYTHON_API_CACHE = {
            "DocumentConverter": document_converter.DocumentConverter,
            "PdfFormatOption": document_converter.PdfFormatOption,
            "PdfPipelineOptions": pipeline_options.PdfPipelineOptions,
            "ThreadedPdfPipelineOptions": getattr(pipeline_options, "ThreadedPdfPipelineOptions", pipeline_options.PdfPipelineOptions),
            "RapidOcrOptions": getattr(pipeline_options, "RapidOcrOptions", None),
            "AcceleratorOptions": accelerator_options.AcceleratorOptions,
            "AcceleratorDevice": accelerator_options.AcceleratorDevice,
            "settings": settings_module.settings,
            "InputFormat": base_models.InputFormat,
        }
    except Exception:
        _DOCLING_PYTHON_API_CACHE = None

    return _DOCLING_PYTHON_API_CACHE


def has_docling_python_api() -> bool:
    return bool(_load_docling_python_api())


def _advanced_cli_stall_timeout(backend_name: str, ctx: "BackendContext") -> int:
    base_timeout = int(ctx.stall_timeout or 300)
    effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = _selected_page_count(ctx)
    heavy_profiles = {"math_heavy", "diagram_heavy", "scanned"}

    if backend_name == "marker":
        marker_model = _marker_ollama_model(ctx)
        marker_llm_active = _marker_should_use_llm(ctx) and bool(marker_model)
        if marker_llm_active and _marker_model_is_qwen3_vl_8b(marker_model):
            if effective_profile in heavy_profiles and selected_pages >= 80:
                return max(base_timeout, 3600)
            if effective_profile in heavy_profiles and selected_pages >= 40:
                return max(base_timeout, 2700)
            return max(base_timeout, 1200)
        if marker_llm_active:
            if effective_profile in heavy_profiles and selected_pages >= 80:
                return max(base_timeout, 3600)
            if effective_profile in heavy_profiles and selected_pages >= 40:
                return max(base_timeout, 2700)
            return max(base_timeout, 900)
        if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 80:
            return max(base_timeout, 2700)
        if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 40:
            return max(base_timeout, 1800)
        return base_timeout

    if backend_name == "docling":
        if effective_profile in heavy_profiles and (selected_pages >= 80 or ctx.report.images_count >= 200):
            return max(base_timeout, 1800)
        if effective_profile in heavy_profiles and selected_pages >= 40:
            return max(base_timeout, 1200)
        return base_timeout

    return base_timeout


def _pdf_image_extraction_policy(ctx: "BackendContext") -> Dict[str, object]:
    effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
    if effective_profile in {"math_heavy", "scanned"} or ctx.report.suspected_scan:
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
        "min_bytes": RepoBuilder._MIN_IMG_BYTES,
        "min_dimension": RepoBuilder._MIN_IMG_DIMENSION,
        "max_aspect_ratio": RepoBuilder._MAX_ASPECT_RATIO,
        "keep_low_color": False,
    }
def _truncate_markdown_blocks(blocks: List[str], max_chars: int = 15000) -> str:
    if not blocks:
        return ""
    out: List[str] = []
    size = 0
    for block in blocks:
        if not block:
            continue
        next_size = size + len(block) + 2
        if next_size <= max_chars:
            out.append(block)
            size = next_size
            continue
        remaining = max_chars - size
        if remaining > 160:
            clipped = block[:remaining].rstrip()
            out.append(clipped + "\n\n> Conteúdo truncado.")
        else:
            out.append("> Conteúdo truncado.")
        break
    return "\n\n".join(out).strip()


def _compact_notebook_markdown(raw_text: str, max_cells: int = 24, max_output_chars: int = 6000) -> Tuple[str, str]:
    try:
        notebook = json.loads(raw_text)
    except Exception:
        return "json", raw_text

    cells = notebook.get("cells") or []
    rendered: List[str] = []
    output_budget = 0

    for idx, cell in enumerate(cells[:max_cells], start=1):
        cell_type = (cell.get("cell_type") or "").strip().lower()
        source = "".join(cell.get("source") or []).strip()
        if not source and cell_type != "code":
            continue

        if cell_type == "markdown":
            rendered.append(f"## Célula {idx} — Markdown\n\n{source}")
            continue

        if cell_type == "code":
            rendered.append(f"## Célula {idx} — Código\n\n```python\n{source}\n```")
            outputs = cell.get("outputs") or []
            output_lines: List[str] = []
            for output in outputs[:3]:
                text = "".join(output.get("text") or output.get("data", {}).get("text/plain", []) or []).strip()
                if not text:
                    continue
                remaining = max_output_chars - output_budget
                if remaining <= 0:
                    break
                text = text[:remaining].rstrip()
                output_budget += len(text)
                output_lines.append(text)
            if output_lines:
                rendered.append("**Saída:**\n\n```text\n" + "\n\n".join(output_lines) + "\n```")

    if len(cells) > max_cells:
        rendered.append(f"> Notebook truncado: exibindo {max_cells} de {len(cells)} células.")

    return "jupyter", "\n\n".join(block for block in rendered if block).strip() or raw_text


def _generated_repo_gitignore_text() -> str:
    return "\n".join([
        "# === Não essencial para o Tutor ===",
        "# Cache de build (assets, markdowns intermediários)",
        "staging/",
        "# Fontes originais (tutor lê os markdowns convertidos)",
        "raw/",
        "# Artefatos de build",
        "build/",
        "# Backups de consolidação e migração",
        "build/consolidation-backup/",
        "build/migration-v1-backup/",
        "# Workspace de revisão manual",
        "manual-review/",
        "# Scripts utilitários locais",
        "scripts/",
        "# Índices internos derivados do app (regeneráveis)",
        "course/.content_taxonomy.json",
        "course/.timeline_index.json",
        "course/.assessment_context.json",
        "course/.tag_catalog.json",
        "course/.semantic_profile.generated.json",
        "# Exportações operacionais de prompt (copiadas para a plataforma, não lidas pelo tutor)",
        "setup/",
        "",
        "# === Sistema ===",
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
        "Thumbs.db",
        "",
    ])


def _extract_url_page_metadata(soup) -> Dict[str, str]:
    title = ""
    description = ""

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = _collapse_ws(html_lib.unescape(og_title["content"]))

    if not title and soup.title and soup.title.string:
        title = _collapse_ws(html_lib.unescape(soup.title.string))

    desc_tag = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    if desc_tag and desc_tag.get("content"):
        description = _collapse_ws(html_lib.unescape(desc_tag["content"]))

    return {"title": title, "description": description}


def _is_probably_noise_container(tag) -> bool:
    attrs = " ".join(
        str(v) for key, v in tag.attrs.items()
        if key in {"id", "class", "role", "aria-label"}
    ).lower()
    noise_tokens = {
        "nav", "menu", "sidebar", "aside", "footer", "header", "breadcrumb",
        "cookie", "consent", "banner", "popup", "modal", "share", "social",
        "related", "recommend", "newsletter", "comment", "advert", "ads",
        "pagination", "toolbar",
    }
    return any(token in attrs for token in noise_tokens)


def _content_score(tag) -> int:
    text_len = len(tag.get_text(" ", strip=True))
    p_count = len(tag.find_all("p"))
    li_count = len(tag.find_all("li"))
    heading_count = len(tag.find_all(re.compile(r"^h[1-6]$")))
    table_count = len(tag.find_all("table"))
    article_bonus = 0
    attrs = " ".join(
        str(v) for key, v in tag.attrs.items()
        if key in {"id", "class", "role"}
    ).lower()
    if tag.name in {"article", "main"}:
        article_bonus += 600
    if any(token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"}):
        article_bonus += 400
    if _is_probably_noise_container(tag):
        article_bonus -= 900
    return text_len + p_count * 180 + li_count * 40 + heading_count * 120 + table_count * 160 + article_bonus


def _pick_best_content_root(soup):
    direct = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
    )
    if direct and not _is_probably_noise_container(direct):
        return direct

    candidates = []
    for tag in soup.find_all(["article", "main", "section", "div"]):
        text_len = len(tag.get_text(" ", strip=True))
        attrs = " ".join(
            str(v) for key, v in tag.attrs.items()
            if key in {"id", "class", "role"}
        ).lower()
        has_content_hint = any(token in attrs for token in {"content", "article", "post", "entry", "main", "markdown", "doc"})
        if text_len < 80:
            continue
        if text_len < 250 and not has_content_hint and tag.name not in {"article", "main"}:
            continue
        score = _content_score(tag)
        candidates.append((score, text_len, tag))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2]

    return soup.body or soup


def _inline_html_to_markdown(node) -> str:
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()
    if name == "br":
        return "\n"

    content = "".join(_inline_html_to_markdown(child) for child in node.children)
    content = html_lib.unescape(content)

    if name == "a":
        text = _collapse_ws(content)
        href = (node.get("href") or "").strip()
        if text and href and href != text:
            return f"[{text}]({href})"
        return text or href
    if name in {"strong", "b"}:
        text = _collapse_ws(content)
        return f"**{text}**" if text else ""
    if name in {"em", "i"}:
        text = _collapse_ws(content)
        return f"*{text}*" if text else ""
    if name == "code":
        text = _collapse_ws(content)
        return f"`{text}`" if text else ""

    return content


def _render_html_block_to_markdown(tag) -> str:
    name = tag.name.lower()

    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = min(int(name[1]), 6)
        text = _collapse_ws(_inline_html_to_markdown(tag))
        return f"{'#' * level} {text}" if text else ""

    if name == "p":
        return _collapse_ws(_inline_html_to_markdown(tag))

    if name in {"ul", "ol"}:
        lines: List[str] = []
        for idx, li in enumerate(tag.find_all("li", recursive=False), start=1):
            text = _collapse_ws(_inline_html_to_markdown(li))
            if not text:
                continue
            prefix = f"{idx}." if name == "ol" else "-"
            lines.append(f"{prefix} {text}")
        return "\n".join(lines)

    if name == "blockquote":
        text = "\n".join(_collapse_ws(line) for line in tag.get_text("\n").splitlines() if _collapse_ws(line))
        return "\n".join(f"> {line}" for line in text.splitlines()) if text else ""

    if name == "pre":
        text = tag.get_text("\n", strip=True)
        if not text:
            return ""
        return f"```text\n{text}\n```"

    if name == "table":
        rows: List[List[str]] = []
        for tr in tag.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            row = [_collapse_ws(cell.get_text(" ", strip=True)) for cell in cells]
            if any(row):
                rows.append(row)
        return rows_to_markdown_table(rows)

    return ""


def _html_to_structured_markdown(html: str, url: str, title: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for unwanted in soup(["script", "style", "noscript", "svg"]):
        unwanted.extract()
    for selector in ("nav", "header", "footer", "aside", "form"):
        for node in soup.find_all(selector):
            node.decompose()
    for node in soup.find_all(attrs={"hidden": True}):
        node.decompose()
    for node in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)):
        node.decompose()

    meta = _extract_url_page_metadata(soup)
    page_title = title or meta["title"] or url
    description = meta["description"]
    content_root = _pick_best_content_root(soup)

    blocks: List[str] = []
    seen: set = set()
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "pre", "table"]
    for tag in content_root.find_all(block_tags):
        if any(parent.name in block_tags for parent in tag.parents if getattr(parent, "name", None)):
            continue
        block = _render_html_block_to_markdown(tag).strip()
        normalized = _collapse_ws(block.replace("\n", " "))
        if not block or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        blocks.append(block)

    if not blocks:
        text = content_root.get_text("\n", strip=True)
        paragraphs = [_collapse_ws(part) for part in text.splitlines() if _collapse_ws(part)]
        blocks.extend(paragraphs)

    host = ""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
    except Exception:
        pass

    header_lines = [f"# {page_title}", ""]
    if description:
        header_lines.extend([description, ""])
    header_lines.extend([
        f"- URL: [{url}]({url})",
        f"- Domínio: `{host or 'desconhecido'}`",
        f"- Capturado em: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Conteúdo Extraído",
        "",
    ])

    body = _truncate_markdown_blocks(blocks)
    if not body:
        body = "> Nenhum conteúdo textual relevante foi extraído."
    return "\n".join(header_lines) + body + "\n"

# ---------------------------------------------------------------------------
# Unicode math → LaTeX normalization
# ---------------------------------------------------------------------------

# Mapa de símbolos Unicode matemáticos → comandos LaTeX.
# Aplicado pós-extração para normalizar output de OCR/backends.
_UNICODE_MATH_TO_LATEX = {
    # Quantificadores e lógica
    "∃": r"\exists", "∄": r"\nexists", "∀": r"\forall",
    "∧": r"\land", "∨": r"\lor", "¬": r"\neg", "⊻": r"\oplus",
    "⊢": r"\vdash", "⊣": r"\dashv", "⊨": r"\models",
    "⊤": r"\top", "⊥": r"\bot",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow",
    "↔": r"\leftrightarrow", "↦": r"\mapsto",
    # Teoria dos conjuntos
    "∈": r"\in", "∉": r"\notin", "∋": r"\ni",
    "⊂": r"\subset", "⊃": r"\supset",
    "⊆": r"\subseteq", "⊇": r"\supseteq",
    "⊄": r"\not\subset", "⊅": r"\not\supset",
    "∪": r"\cup", "∩": r"\cap",
    "∅": r"\emptyset", "∖": r"\setminus",
    # Relações
    "≤": r"\leq", "≥": r"\geq", "≠": r"\neq",
    "≈": r"\approx", "≡": r"\equiv", "≅": r"\cong",
    "∼": r"\sim", "≺": r"\prec", "≻": r"\succ",
    "≪": r"\ll", "≫": r"\gg",
    "≜": r"\triangleq", "≐": r"\doteq",
    # Operadores
    "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp",
    "∘": r"\circ", "⊕": r"\oplus", "⊗": r"\otimes",
    "⊙": r"\odot", "†": r"\dagger", "‡": r"\ddagger",
    # Cálculo e análise
    "∫": r"\int", "∬": r"\iint", "∭": r"\iiint",
    "∂": r"\partial", "∇": r"\nabla",
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod",
    "∞": r"\infty", "√": r"\sqrt",
    "ℓ": r"\ell", "ℏ": r"\hbar", "ℜ": r"\Re", "ℑ": r"\Im",
    # Letras gregas minúsculas
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu",
    "ν": r"\nu", "ξ": r"\xi", "ρ": r"\rho", "σ": r"\sigma",
    "τ": r"\tau", "υ": r"\upsilon", "φ": r"\phi", "χ": r"\chi",
    "ψ": r"\psi", "ω": r"\omega", "ϵ": r"\varepsilon", "ϕ": r"\varphi",
    "ϑ": r"\vartheta", "ϱ": r"\varrho", "ς": r"\varsigma",
    # Letras gregas maiúsculas
    "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda",
    "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Ψ": r"\Psi", "Ω": r"\Omega",
    # Setas (apenas as inambíguas)
    "⟶": r"\longrightarrow", "⟵": r"\longleftarrow",
    "⟹": r"\Longrightarrow", "⟸": r"\Longleftarrow",
    "↑": r"\uparrow", "↓": r"\downarrow",
    "⟨": r"\langle", "⟩": r"\rangle",
    # Miscelânea
    "□": r"\square", "◇": r"\diamond", "△": r"\triangle",
    "▽": r"\triangledown", "★": r"\star", "⋆": r"\star",
    "⋅": r"\cdot", "…": r"\ldots", "⋯": r"\cdots", "⋮": r"\vdots",
    "ℕ": r"\mathbb{N}", "ℤ": r"\mathbb{Z}", "ℚ": r"\mathbb{Q}",
    "ℝ": r"\mathbb{R}", "ℂ": r"\mathbb{C}",
}

# Regex para encontrar regiões de math (inline e display)
_MATH_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
_MATH_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_MATH_PAREN_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_MATH_BRACKET_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)

# Build regex para substituição — escapar caracteres regex-special
_UNICODE_MATH_PATTERN = re.compile(
    "|".join(re.escape(ch) for ch in sorted(_UNICODE_MATH_TO_LATEX.keys(), key=len, reverse=True))
)
_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "�")
_TEX_SIMPLE_ACCENT_RE = re.compile(r"""\\(?P<accent>['`^"~])(?:\{(?P<braced>[A-Za-z])\}|(?P<plain>[A-Za-z]))""")
_TEX_CEDILLA_RE = re.compile(r"""\\c(?:\{(?P<braced>[A-Za-z])\}|(?P<plain>[A-Za-z]))""")

_TEX_ACCENT_TO_UNICODE = {
    ("'", "A"): "Á", ("'", "E"): "É", ("'", "I"): "Í", ("'", "O"): "Ó", ("'", "U"): "Ú",
    ("'", "a"): "á", ("'", "e"): "é", ("'", "i"): "í", ("'", "o"): "ó", ("'", "u"): "ú",
    ("`", "A"): "À", ("`", "E"): "È", ("`", "I"): "Ì", ("`", "O"): "Ò", ("`", "U"): "Ù",
    ("`", "a"): "à", ("`", "e"): "è", ("`", "i"): "ì", ("`", "o"): "ò", ("`", "u"): "ù",
    ("^", "A"): "Â", ("^", "E"): "Ê", ("^", "I"): "Î", ("^", "O"): "Ô", ("^", "U"): "Û",
    ("^", "a"): "â", ("^", "e"): "ê", ("^", "i"): "î", ("^", "o"): "ô", ("^", "u"): "û",
    ('"', "A"): "Ä", ('"', "E"): "Ë", ('"', "I"): "Ï", ('"', "O"): "Ö", ('"', "U"): "Ü",
    ('"', "a"): "ä", ('"', "e"): "ë", ('"', "i"): "ï", ('"', "o"): "ö", ('"', "u"): "ü",
    ("~", "A"): "Ã", ("~", "N"): "Ñ", ("~", "O"): "Õ",
    ("~", "a"): "ã", ("~", "n"): "ñ", ("~", "o"): "õ",
}
_TEX_CEDILLA_TO_UNICODE = {"C": "Ç", "c": "ç"}


def _normalize_tex_accents_in_math(text: str) -> str:
    """Convert common TeX accent escapes into Unicode inside math regions.

    Marker/OCR sometimes emits natural-language fragments inside display math as
    TeX accent commands, e.g. ``somat\\'orio``. This pass normalizes those
    escapes back to plain Unicode text without touching regular math commands
    such as ``\\hat{o}``.
    """
    if not text or "\\" not in text:
        return text

    def _replace_simple(match: re.Match) -> str:
        accent = match.group("accent")
        letter = match.group("braced") or match.group("plain") or ""
        return _TEX_ACCENT_TO_UNICODE.get((accent, letter), match.group(0))

    def _replace_cedilla(match: re.Match) -> str:
        letter = match.group("braced") or match.group("plain") or ""
        return _TEX_CEDILLA_TO_UNICODE.get(letter, match.group(0))

    text = _TEX_SIMPLE_ACCENT_RE.sub(_replace_simple, text)
    text = _TEX_CEDILLA_RE.sub(_replace_cedilla, text)
    return text


def _normalize_unicode_math(text: str) -> str:
    """Replace Unicode math symbols with LaTeX commands in a markdown string.

    Strategy:
    - Inside math delimiters ($...$, $$...$$, \\(...\\), \\[...\\]):
      replace Unicode symbols with LaTeX commands (e.g., ∀ → \\forall)
    - Outside math: wrap isolated Unicode math symbols with $...$
    """
    if not text:
        return text

    # Phase 1: Replace inside existing math regions
    def _replace_in_math(m):
        content = m.group(0)
        content = _normalize_tex_accents_in_math(content)
        return _UNICODE_MATH_PATTERN.sub(
            lambda sym: _UNICODE_MATH_TO_LATEX.get(sym.group(0), sym.group(0)),
            content,
        )

    for pattern in (_MATH_DISPLAY_RE, _MATH_INLINE_RE, _MATH_PAREN_RE, _MATH_BRACKET_RE):
        text = pattern.sub(_replace_in_math, text)

    # Phase 2: Wrap remaining Unicode math symbols outside of math delimiters.
    # We split by math regions, process only non-math parts.
    def _wrap_outside_math(text_str: str) -> str:
        # Split on all math delimiters to identify non-math segments
        math_regions = re.compile(
            r"(\$\$.+?\$\$"          # display $$...$$
            r"|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)"  # inline $...$
            r"|\\\(.+?\\\)"          # \(...\)
            r"|\\\[.+?\\\])",        # \[...\]
            re.DOTALL,
        )
        parts = math_regions.split(text_str)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This is a math region — keep as-is
                result.append(part)
            else:
                # Non-math — wrap isolated Unicode math symbols
                part = _UNICODE_MATH_PATTERN.sub(
                    lambda sym: f"${_UNICODE_MATH_TO_LATEX[sym.group(0)]}$",
                    part,
                )
                result.append(part)
        return "".join(result)

    text = _wrap_outside_math(text)
    return text


def _mojibake_score(text: str) -> int:
    if not text:
        return 0
    return sum(text.count(marker) for marker in _MOJIBAKE_MARKERS)


def _repair_mojibake_text(text: str) -> str:
    """Repair common UTF-8 mojibake introduced by external CLIs."""
    if not text:
        return text

    original_score = _mojibake_score(text)
    if original_score == 0:
        return text

    candidates = [text]
    for source_encoding in ("latin-1", "cp1252"):
        try:
            candidates.append(text.encode(source_encoding).decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    best = min(candidates, key=_mojibake_score)
    return best if _mojibake_score(best) < original_score else text


def _sanitize_external_markdown_text(text: str) -> str:
    repaired = _repair_mojibake_text(text)
    return repaired.replace("\r\n", "\n").replace("\r", "\n")


def _detect_latex_corruption(content: str) -> dict:
    """
    Analisa um markdown e detecta padrões de LaTeX provavelmente corrompido.

    Retorna:
        {
            "corrupted": bool,
            "score": int,
            "signals": list[str],
        }

    A função apenas detecta e sinaliza; não tenta corrigir.
    Blocos de código e inline code são ignorados.
    """
    import re
    from collections import Counter

    if not content:
        return {"corrupted": False, "score": 0, "signals": []}

    clean = str(content).replace("\r\n", "\n").replace("\r", "\n")
    clean = re.sub(r"^---\n.*?\n---\n?", "", clean, flags=re.DOTALL)
    clean = re.sub(r"```.*?```", "", clean, flags=re.DOTALL)
    clean = re.sub(r"`[^`\n]+`", "", clean)

    signals: List[str] = []
    score = 0

    def _add_signal(message: str, weight: int) -> None:
        nonlocal score
        signals.append(message)
        score += weight

    single_dollars = re.findall(r"(?<![\\$])\$(?!\$)", clean)
    if len(single_dollars) % 2 != 0:
        _add_signal("delimitadores $ desbalanceados", 30)

    begin_counter = Counter(re.findall(r"\\begin\{([^}]+)\}", clean))
    end_counter = Counter(re.findall(r"\\end\{([^}]+)\}", clean))
    unmatched_envs = []
    for env_name, count in begin_counter.items():
        if count > end_counter.get(env_name, 0):
            unmatched_envs.append(env_name)
    if unmatched_envs:
        sample = ", ".join(sorted(set(unmatched_envs))[:3])
        _add_signal(f"\\begin sem \\end: {sample}", min(len(unmatched_envs) * 15, 30))

    unicode_math_chars = re.findall(r"[∀∃∈∉∅∧∨¬→↔⇒⇔≤≥≠⊆⊂⊇⊃∪∩ℕℤℚℝℂ⊢⊨⊥⊤]", clean)
    latex_markers = re.findall(r"\$|\\[a-zA-Z]+", clean)
    if len(unicode_math_chars) >= 4 and len(latex_markers) < max(2, len(unicode_math_chars) // 2):
        _add_signal(
            f"{len(unicode_math_chars)} símbolos unicode sem estrutura LaTeX",
            min(len(unicode_math_chars) * 2, 20),
        )

    brace_issue_lines = 0
    brace_hint_lines = 0
    raw_command_lines = 0
    orphan_escapes = 0
    mathish_line_re = re.compile(r"\\[a-zA-Z]+|[$∀∃∈∉∧∨¬→↔⇒⇔≤≥≠⊆⊂⊇⊃∪∩ℕℤℚℝℂ⊢⊨⊥⊤]|^\s*\{")

    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.count("{") != stripped.count("}") and mathish_line_re.search(stripped):
            brace_issue_lines += 1
        if stripped.startswith("{") and stripped.count("{") > stripped.count("}"):
            brace_hint_lines += 1

        command_count = len(re.findall(r"\\[a-zA-Z]+", stripped))
        has_math_delimiter = bool(re.search(r"\$|\\\(|\\\[|\\begin\{", stripped))
        if command_count >= 2 and not has_math_delimiter:
            raw_command_lines += 1

        if re.search(r"(?<!\\)\\\s*$", stripped):
            orphan_escapes += 1

    if brace_issue_lines:
        _add_signal(
            f"{brace_issue_lines} linha(s) com chaves desbalanceadas em contexto matemático",
            min(brace_issue_lines * 10, 25),
        )
    if brace_hint_lines:
        _add_signal(
            f"{brace_hint_lines} possível(is) tripla(s) de Hoare incompleta(s)",
            min(brace_hint_lines * 8, 16),
        )
    if raw_command_lines:
        _add_signal(
            f"{raw_command_lines} linha(s) com comandos LaTeX fora de delimitadores",
            min(raw_command_lines * 10, 20),
        )
    if orphan_escapes:
        _add_signal(
            f"{orphan_escapes} escape(s) órfão(s) no fim de linha",
            min(orphan_escapes * 6, 12),
        )

    return {
        "corrupted": score >= 25,
        "score": min(score, 100),
        "signals": signals,
    }


_PORTUGUESE_ACCENT_CHARS = set("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ")


def _split_markdown_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    end += len("\n---\n")
    return text[:end], text[end:]


def _is_plain_text_recovery_candidate(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 24:
        return False
    if not re.search(r"[A-Za-zÀ-ÿ]", stripped):
        return False
    if stripped.startswith(("```", "#", ">", "-", "*", "|", "<!--")):
        return False
    if stripped.startswith(tuple(f"{n}." for n in range(1, 10))):
        return False
    if any(token in stripped for token in ("![", "](", "<math", "</math>", "$$", "\\(", "\\)", "\\[", "\\]")):
        return False
    if stripped.count("|") >= 2:
        return False
    if sum(stripped.count(ch) for ch in "=^_{}\\") >= 3:
        return False
    return True


def _normalize_recovery_line(line: str) -> str:
    normalized = unicodedata.normalize("NFKD", line)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[`*_>#\[\](){}|~]+", " ", normalized)
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def _accent_quality_score(line: str) -> int:
    accent_count = sum(1 for ch in line if ch in _PORTUGUESE_ACCENT_CHARS)
    return accent_count * 2 - _mojibake_score(line)


def _hybridize_marker_markdown_with_base(base_markdown: str, marker_markdown: str) -> tuple[str, Dict[str, int]]:
    base_prefix, base_body = _split_markdown_frontmatter(_sanitize_external_markdown_text(base_markdown))
    marker_prefix, marker_body = _split_markdown_frontmatter(_sanitize_external_markdown_text(marker_markdown))
    del base_prefix  # only the Marker frontmatter should be preserved

    base_lines = base_body.split("\n")
    marker_lines = marker_body.split("\n")
    replacements = 0
    matched_candidates = 0

    base_candidates = []
    for idx, line in enumerate(base_lines):
        if not _is_plain_text_recovery_candidate(line):
            continue
        normalized = _normalize_recovery_line(line)
        if normalized:
            base_candidates.append((idx, line, normalized))

    search_cursor = 0
    repaired_lines: List[str] = []
    for line in marker_lines:
        if not _is_plain_text_recovery_candidate(line):
            repaired_lines.append(line)
            continue

        normalized_marker = _normalize_recovery_line(line)
        if not normalized_marker:
            repaired_lines.append(line)
            continue

        best_match = None
        best_ratio = 0.0
        window_start = max(0, search_cursor - 2)
        window_end = min(len(base_candidates), search_cursor + 12)
        for idx in range(window_start, window_end):
            _, base_line, normalized_base = base_candidates[idx]
            ratio = difflib.SequenceMatcher(None, normalized_marker, normalized_base).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (idx, base_line)

        if best_match and best_ratio >= 0.88:
            matched_candidates += 1
            candidate_idx, candidate_line = best_match
            if (
                _accent_quality_score(candidate_line) > _accent_quality_score(line)
                and _normalize_recovery_line(candidate_line) == normalized_marker
            ):
                repaired_lines.append(candidate_line)
                replacements += 1
            else:
                repaired_lines.append(line)
            search_cursor = candidate_idx + 1
        else:
            repaired_lines.append(line)

    merged_body = "\n".join(repaired_lines)
    return marker_prefix + merged_body, {
        "candidate_matches": matched_candidates,
        "replacements": replacements,
        "base_candidates": len(base_candidates),
    }


# ---------------------------------------------------------------------------
# Backend architecture
# ---------------------------------------------------------------------------

class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport,
                 cancel_check=None, stall_timeout: int = 300, marker_chunking_mode: str = "fallback",
                 marker_use_llm: bool = False, marker_llm_model: str = "", marker_torch_device: str = "auto", ollama_base_url: str = "",
                 vision_model: str = ""):
        self.root_dir = root_dir
        self.raw_target = raw_target
        self.entry = entry
        self.report = report
        self.entry_id = entry.id()
        self.pages = parse_page_range(entry.page_range)
        self.cancel_check = cancel_check    # callable que levanta InterruptedError se cancelado
        self.stall_timeout = stall_timeout  # segundos sem output antes de matar o processo
        self.marker_chunking_mode = str(marker_chunking_mode or "fallback").strip().lower()
        self.marker_use_llm = bool(marker_use_llm)
        self.marker_llm_model = str(marker_llm_model or "").strip()
        self.marker_torch_device = str(marker_torch_device or "auto").strip().lower() or "auto"
        self.ollama_base_url = str(ollama_base_url or "").strip()
        self.vision_model = str(vision_model or "").strip()

    def page_label(self) -> str:
        return self.entry.page_range.strip() or "all"


class ExtractionBackend:
    name = "base"
    layer = "base"

    def available(self) -> bool:
        return False

    def run(self, ctx: BackendContext) -> BackendRunResult:
        raise NotImplementedError


class PyMuPDF4LLMBackend(ExtractionBackend):
    name = "pymupdf4llm"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF4LLM

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf4llm"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        # Nota: NÃO usar force_ocr=True — pymupdf4llm tem um bug onde chama
        # ocr_function(page) sem verificar se é None quando force_ocr=True.
        # Em vez disso, usamos use_ocr=True (default) que detecta páginas
        # scaneadas automaticamente e usa o OCR embutido do pymupdf (pdfocr_tobytes).
        wants_ocr = bool(ctx.entry.force_ocr) or ctx.report.suspected_scan
        kwargs = {
            "pages": ctx.pages,
            "write_images": bool(ctx.entry.preserve_pdf_images_in_markdown),
            "image_path": str((ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id).resolve()),
            "use_ocr": wants_ocr,
            "page_separators": True,
        }
        if wants_ocr:
            kwargs["ocr_language"] = ctx.entry.ocr_language.replace(",", "+")
        if not ctx.entry.preserve_pdf_images_in_markdown:
            kwargs["write_images"] = False
            kwargs.pop("image_path", None)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        md = pymupdf4llm.to_markdown(str(ctx.raw_target), **kwargs)
        if isinstance(md, list):
            body = "\n\n".join(chunk.get("text", "") for chunk in md)
        else:
            body = md

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id, ctx.root_dir) if ctx.entry.preserve_pdf_images_in_markdown else None,
            notes=["Markdown gerado com PyMuPDF4LLM."],
        )


class PyMuPDFBackend(ExtractionBackend):
    name = "pymupdf"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        doc = pymupdf.open(str(ctx.raw_target))
        try:
            target_pages = ctx.pages or list(range(doc.page_count))
            pieces = [f"# {ctx.entry.title}", ""]
            for i in target_pages:
                if i < 0 or i >= doc.page_count:
                    continue
                page = doc[i]
                pieces.append(f"## Página {i + 1}")
                pieces.append("")
                text = page.get_text("text")
                text = re.sub(r"[ \t]+\n", "\n", text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                pieces.append(text.strip())
                pieces.append("")
            body = "\n".join(pieces).strip() + "\n"
        finally:
            doc.close()

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            notes=["Markdown bruto gerado com PyMuPDF."],
        )


def _run_cli_with_timeout(cmd: list, backend_name: str, ctx: "BackendContext", stall_timeout: Optional[int] = None):
    """Run an external CLI process with stall timeout and cancel support.

    Returns (returncode, stdout_lines, stderr_lines).
    Raises InterruptedError if cancelled, TimeoutError if stalled.
    """
    import threading as _th
    import time as _time

    stdout_lines: list = []
    stderr_lines: list = []
    last_output_time = _time.monotonic()
    effective_stall_timeout = stall_timeout if stall_timeout is not None else ctx.stall_timeout
    lock = _th.Lock()
    killed_by_cancel = _th.Event()
    killed_by_stall = _th.Event()
    last_marker_phase = {"name": None}
    process_env = None

    if backend_name == "marker":
        process_env = os.environ.copy()
        process_env["TORCH_DEVICE"] = _marker_effective_torch_device(ctx)

    def _log_marker_progress_hint(line: str):
        if backend_name != "marker":
            return
        phase, hints = _marker_progress_hints(line, last_marker_phase["name"])
        last_marker_phase["name"] = phase
        for hint in hints:
            logger.info("  [marker] %s", hint)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=process_env,
    )
    logger.info("  [%s] PID=%d — aguardando saída...", backend_name, proc.pid)

    def _read_stderr():
        nonlocal last_output_time
        for line in proc.stderr:
            line = line.rstrip()
            if line:
                with lock:
                    stderr_lines.append(line)
                    last_output_time = _time.monotonic()
                _log_marker_progress_hint(line)
                logger.info("  [%s stderr] %s", backend_name, line)

    stderr_thread = _th.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    def _watchdog():
        """Mata o processo se parar de produzir output ou se cancelado."""
        while proc.poll() is None:
            _time.sleep(2)
            # Check cancel
            if ctx.cancel_check:
                try:
                    ctx.cancel_check()
                except InterruptedError:
                    logger.warning("  [%s] Cancelado pelo usuário — matando PID %d",
                                   backend_name, proc.pid)
                    killed_by_cancel.set()
                    proc.kill()
                    return
            # Check stall
            with lock:
                elapsed = _time.monotonic() - last_output_time
            phase_stall_timeout = effective_stall_timeout
            if backend_name == "marker" and _marker_should_use_llm(ctx) and _marker_ollama_model(ctx):
                phase_name = str(last_marker_phase.get("name") or "")
                if phase_name.startswith("LLM processors running"):
                    if _marker_model_is_qwen3_vl_8b(_marker_ollama_model(ctx)):
                        phase_stall_timeout = max(phase_stall_timeout, 1800)
                    else:
                        phase_stall_timeout = max(phase_stall_timeout, 1200)
            if elapsed > phase_stall_timeout:
                logger.error("  [%s] Sem output por %ds — matando PID %d (stall timeout)",
                             backend_name, phase_stall_timeout, proc.pid)
                killed_by_stall.set()
                proc.kill()
                return

    watchdog_thread = _th.Thread(target=_watchdog, daemon=True)
    watchdog_thread.start()

    for line in proc.stdout:
        line = line.rstrip()
        if line:
            stdout_lines.append(line)
            with lock:
                last_output_time = _time.monotonic()
            _log_marker_progress_hint(line)
            logger.info("  [%s stdout] %s", backend_name, line)

    proc.wait()
    stderr_thread.join(timeout=5)
    watchdog_thread.join(timeout=2)

    if killed_by_cancel.is_set():
        raise InterruptedError(f"{backend_name} cancelado pelo usuário.")

    if killed_by_stall.is_set():
        last_line = (stderr_lines or stdout_lines or ["(nenhum)"])[-1]
        phase_stall_timeout = effective_stall_timeout
        if backend_name == "marker" and _marker_should_use_llm(ctx) and _marker_ollama_model(ctx):
            phase_name = str(last_marker_phase.get("name") or "")
            if phase_name.startswith("LLM processors running"):
                if _marker_model_is_qwen3_vl_8b(_marker_ollama_model(ctx)):
                    phase_stall_timeout = max(phase_stall_timeout, 1800)
                else:
                    phase_stall_timeout = max(phase_stall_timeout, 1200)
        raise TimeoutError(
            f"{backend_name} travou (sem output por {phase_stall_timeout}s). "
            f"Último output:\n{last_line}"
        )

    returncode = proc.returncode
    logger.info("  [%s] Processo finalizado com código %d", backend_name, returncode)
    return returncode, stdout_lines, stderr_lines


_MARKER_CAPABILITIES_CACHE = None
MARKER_OLLAMA_SERVICE = "marker.services.ollama.OllamaService"


def _default_marker_capabilities() -> Dict[str, object]:
    return {
        "page_range_flag": "--page_range",
        "force_ocr_flag": "--force_ocr",
        "use_llm_flag": "--use_llm",
        "llm_service_flag": "--llm_service",
        "ollama_base_url_flag": "--OllamaService_ollama_base_url",
        "ollama_model_flag": "--OllamaService_ollama_model",
        "ollama_timeout_flag": "--OllamaService_timeout",
        "redo_inline_math_flag": "--redo_inline_math",
        "disable_image_extraction_flag": "--disable_image_extraction",
    }


def _detect_marker_capabilities() -> Dict[str, object]:
    """
    Detecta quais flags a versão instalada do Marker suporta.

    Resultado esperado:
    {
        "page_range_flag": "--page_range" | "--page-range" | None,
        "force_ocr_flag": "--force_ocr" | "--force-ocr" | None,
        "use_llm_flag": "--use_llm" | "--use-llm" | None,
        "llm_service_flag": "--llm_service" | "--llm-service" | None,
        "ollama_base_url_flag": "--ollama_base_url" | "--ollama-base-url" | "--ollamaservice_ollama_base_url" | "--OllamaService_ollama_base_url" | None,
        "ollama_model_flag": "--ollama_model" | "--ollama-model" | "--ollamaservice_ollama_model" | "--OllamaService_ollama_model" | None,
        "redo_inline_math_flag": "--redo_inline_math" | "--redo-inline-math" | None,
    }
    """
    global _MARKER_CAPABILITIES_CACHE

    if _MARKER_CAPABILITIES_CACHE is not None:
        return dict(_MARKER_CAPABILITIES_CACHE)

    caps = _default_marker_capabilities()

    if not MARKER_CLI:
        caps = {k: None for k in caps}
        _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    try:
        proc = subprocess.run(
            [MARKER_CLI, "--help"],
            capture_output=True,
            text=True,
            timeout=45,
        )
        help_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
    except Exception as e:
        logger.warning(
            "  [marker] Não foi possível inspecionar --help: %s. "
            "Usando fallback otimista com as flags atuais conhecidas do Marker.",
            e,
        )
        _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    # Page range
    if "--page-range" in help_text:
        caps["page_range_flag"] = "--page-range"
    elif "--page_range" in help_text:
        caps["page_range_flag"] = "--page_range"
    else:
        caps["page_range_flag"] = None

    # Force OCR
    if "--force-ocr" in help_text:
        caps["force_ocr_flag"] = "--force-ocr"
    elif "--force_ocr" in help_text:
        caps["force_ocr_flag"] = "--force_ocr"
    else:
        caps["force_ocr_flag"] = None

    for candidate in ("--use-llm", "--use_llm"):
        if candidate in help_text:
            caps["use_llm_flag"] = candidate
            break

    for candidate in ("--llm-service", "--llm_service"):
        if candidate in help_text:
            caps["llm_service_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_ollama_base_url",
        "--ollama-base-url",
        "--ollama_base_url",
        "--ollamaservice-ollama-base-url",
        "--ollamaservice_ollama_base_url",
    ):
        if candidate.lower() in help_text:
            caps["ollama_base_url_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_ollama_model",
        "--ollama-model",
        "--ollama_model",
        "--ollamaservice-ollama-model",
        "--ollamaservice_ollama_model",
    ):
        if candidate.lower() in help_text:
            caps["ollama_model_flag"] = candidate
            break

    for candidate in ("--redo_inline_math", "--redo-inline-math"):
        if candidate in help_text:
            caps["redo_inline_math_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_timeout",
        "--ollamaservice-timeout",
        "--ollamaservice_timeout",
    ):
        if candidate.lower() in help_text:
            caps["ollama_timeout_flag"] = candidate
            break

    for candidate in ("--disable_image_extraction", "--disable-image-extraction"):
        if candidate in help_text:
            caps["disable_image_extraction_flag"] = candidate
            break

    _MARKER_CAPABILITIES_CACHE = dict(caps)
    logger.info("  [marker] Capabilities detectadas: %s", caps)
    return dict(caps)

class DoclingCLIBackend(ExtractionBackend):
    name = "docling"
    layer = "advanced"

    def available(self) -> bool:
        return bool(DOCLING_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling" / ctx.entry_id
        ensure_dir(out_dir)
        stall_timeout = _advanced_cli_stall_timeout("docling", ctx)

        cmd = [
            DOCLING_CLI,
            str(ctx.raw_target),
            "--to", "md",
            "--output", str(out_dir),
            "--image-export-mode", "referenced",
            "--tables",
            "--ocr",
            "--ocr-lang", ctx.entry.ocr_language,
            "--table-mode", "accurate",
            "-vv",
        ]

        if ctx.entry.force_ocr or ctx.report.suspected_scan:
            cmd.append("--force-ocr")
        suggested_profile = normalize_document_profile(ctx.report.suggested_profile)
        if ctx.entry.formula_priority or suggested_profile == "math_heavy":
            cmd.append("--enrich-formula")
        if suggested_profile == "diagram_heavy":
            cmd.append("--enrich-picture-classes")

        logger.info("  [docling] Comando: %s", " ".join(cmd))
        logger.info(
            "  [docling] Stall timeout efetivo: %ss para %d páginas selecionadas.",
            stall_timeout,
            _selected_page_count(ctx),
        )
        logger.info("  [docling] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(
                cmd,
                "docling",
                ctx,
                stall_timeout=stall_timeout,
            )
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [docling] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Docling CLI falhou")[-4000:]
            logger.error("  [docling] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "docling-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
            "stall_timeout": stall_timeout,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Docling CLI."],
        )


class DoclingPythonBackend(ExtractionBackend):
    name = "docling_python"
    layer = "advanced"

    def available(self) -> bool:
        return has_docling_python_api()

    def run(self, ctx: BackendContext) -> BackendRunResult:
        api = _load_docling_python_api()
        if not api:
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error="Docling Python API não está disponível no ambiente atual.",
            )

        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling-python" / ctx.entry_id
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        DocumentConverter = api["DocumentConverter"]
        PdfFormatOption = api["PdfFormatOption"]
        PdfPipelineOptions = api["PdfPipelineOptions"]
        ThreadedPdfPipelineOptions = api.get("ThreadedPdfPipelineOptions", PdfPipelineOptions)
        InputFormat = api["InputFormat"]
        settings_obj = api.get("settings")

        pipeline_options = ThreadedPdfPipelineOptions()
        suggested_profile = normalize_document_profile(ctx.report.suggested_profile)
        formula_enrichment = bool(ctx.entry.formula_priority or suggested_profile == "math_heavy")
        if hasattr(pipeline_options, "do_formula_enrichment"):
            pipeline_options.do_formula_enrichment = formula_enrichment
        gpu_config = _configure_docling_python_standard_gpu(api, pipeline_options)

        logger.info(
            "  [docling_python] Iniciando API Python com do_formula_enrichment=%s para %s (gpu_standard=%s, device=%s).",
            formula_enrichment,
            ctx.entry_id,
            gpu_config["enabled"],
            gpu_config["device"],
        )
        source_pdf, page_range_applied = _prepare_docling_python_source_pdf(ctx, out_dir)
        if page_range_applied:
            logger.info(
                "  [docling_python] Aplicando page_range=%s via PDF temporario com %d paginas selecionadas.",
                ctx.entry.page_range or "all",
                len(ctx.pages or []),
            )
        if ctx.pages and not page_range_applied:
            logger.info(
                "  [docling_python] A API Python será testada sem page_range; processando o documento inteiro."
            )

        previous_page_batch_size = gpu_config.get("previous_page_batch_size")
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            result = converter.convert(str(source_pdf))
            body = result.document.export_to_markdown()
        except Exception as e:
            logger.error("  [docling_python] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )
        finally:
            if settings_obj is not None and previous_page_batch_size is not None:
                settings_obj.perf.page_batch_size = previous_page_batch_size

        write_text(out_path, body)
        metadata_path = out_dir / "docling-python-run.json"
        write_text(metadata_path, json.dumps({
            "source_pdf": str(ctx.raw_target),
            "effective_source_pdf": str(source_pdf),
            "formula_enrichment": formula_enrichment,
            "gpu_standard": gpu_config,
            "page_range_requested": ctx.entry.page_range,
            "page_range_applied": page_range_applied,
            "selected_pages_count": len(ctx.pages or []) if page_range_applied else None,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=["Saída avançada gerada com Docling Python API."],
        )


class DatalabCloudBackend(ExtractionBackend):
    name = "datalab"
    layer = "advanced"

    def available(self) -> bool:
        return has_datalab_api_key()

    def _convert_range(
        self,
        ctx: BackendContext,
        *,
        mode: str,
        page_range: Optional[str],
        max_wait_seconds: int,
    ):
        result = convert_document_to_markdown(
            ctx.raw_target,
            output_format="markdown",
            mode=mode,
            page_range=page_range,
            disable_image_captions=True,
            disable_image_extraction=True,
            paginate=False,
            token_efficient_markdown=False,
            request_timeout=60,
            poll_interval=2.0,
            max_wait_seconds=max_wait_seconds,
        )
        markdown = _sanitize_external_markdown_text(result.markdown)
        markdown = _strip_markdown_image_refs(markdown)
        return result, markdown

    def _run_single_datalab(
        self,
        ctx: BackendContext,
        out_dir: Path,
        *,
        mode: str,
        page_range: Optional[str],
        max_wait_seconds: int,
    ) -> BackendRunResult:
        out_path = out_dir / f"{ctx.entry_id}.md"

        logger.info(
            "  [datalab] Enviando documento para a API (mode=%s, page_range=%s, max_wait=%ss).",
            mode,
            page_range or "all",
            max_wait_seconds,
        )

        try:
            result, markdown = self._convert_range(
                ctx,
                mode=mode,
                page_range=page_range,
                max_wait_seconds=max_wait_seconds,
            )
        except Exception as e:
            logger.error("  [datalab] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )

        write_text(out_path, markdown)

        metadata_path = out_dir / "datalab-run.json"
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "chunked": False,
            "request_id": result.request_id,
            "request_check_url": result.request_check_url,
            "mode": mode,
            "page_range": page_range,
            "selected_pages_count": _selected_page_count(ctx),
            "page_count": result.page_count,
            "parse_quality_score": result.parse_quality_score,
            "cost_breakdown": result.cost_breakdown,
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "metadata": result.metadata,
            "raw_response_tail": {
                "status": result.raw_response.get("status"),
                "success": result.raw_response.get("success"),
                "error": result.raw_response.get("error"),
            },
        }, indent=2, ensure_ascii=False))

        notes = [
            "SaÃ­da avanÃ§ada gerada com Datalab Document Conversion API.",
            f"Modo: {mode}.",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if result.parse_quality_score is not None:
            notes.append(f"parse_quality_score={result.parse_quality_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )

    def _run_chunked_datalab(
        self,
        ctx: BackendContext,
        out_dir: Path,
        *,
        mode: str,
        max_wait_seconds: int,
    ) -> BackendRunResult:
        chunk_size = _datalab_chunk_size_for_workload(ctx)
        chunks = _build_page_chunks(ctx.pages, ctx.report.page_count, chunk_size=chunk_size)
        if len(chunks) <= 1:
            return self._run_single_datalab(
                ctx,
                out_dir,
                mode=mode,
                page_range=pages_to_marker_range(ctx.pages),
                max_wait_seconds=max_wait_seconds,
            )

        logger.info(
            "  [datalab] Documento longo; processando em %d chunks de atÃ© %d pÃ¡ginas.",
            len(chunks),
            chunk_size,
        )

        out_path = out_dir / f"{ctx.entry_id}.md"
        chunks_dir = out_dir / "chunks"
        ensure_dir(chunks_dir)
        combined_parts: List[str] = []
        chunk_meta: List[Dict[str, object]] = []
        parse_scores: List[float] = []
        cost_breakdowns: List[Dict[str, object]] = []
        total_pages = 0

        for idx, chunk_pages in enumerate(chunks, start=1):
            chunk_range = pages_to_marker_range(chunk_pages)
            logger.info(
                "  [datalab] Chunk %d/%d â€” pÃ¡ginas %d-%d",
                idx,
                len(chunks),
                chunk_pages[0] + 1,
                chunk_pages[-1] + 1,
            )
            try:
                result, markdown = self._convert_range(
                    ctx,
                    mode=mode,
                    page_range=chunk_range,
                    max_wait_seconds=max_wait_seconds,
                )
            except Exception as e:
                logger.error("  [datalab] Erro no chunk %d/%d: %s", idx, len(chunks), e)
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    error=f"Chunk {idx}/{len(chunks)} falhou: {e}",
                )

            chunk_path = chunks_dir / f"chunk-{idx:03d}.md"
            write_text(chunk_path, markdown)

            chunk_body = _strip_frontmatter_block(markdown).strip()
            if chunk_body:
                combined_parts.append(
                    f"<!-- DATALAB_CHUNK {idx}: pages {chunk_pages[0] + 1}-{chunk_pages[-1] + 1} -->\n\n{chunk_body}"
                )

            if result.parse_quality_score is not None:
                parse_scores.append(float(result.parse_quality_score))
            cost_breakdowns.append(dict(result.cost_breakdown or {}))
            total_pages += int(result.page_count or 0)
            chunk_meta.append({
                "chunk_index": idx,
                "page_range": chunk_range,
                "page_count": result.page_count,
                "request_id": result.request_id,
                "request_check_url": result.request_check_url,
                "parse_quality_score": result.parse_quality_score,
                "cost_breakdown": result.cost_breakdown,
                "markdown_path": safe_rel(chunk_path, ctx.root_dir),
                "raw_response_tail": {
                    "status": result.raw_response.get("status"),
                    "success": result.raw_response.get("success"),
                    "error": result.raw_response.get("error"),
                },
            })

        combined_markdown = "\n\n".join(part for part in combined_parts if part).strip()
        if combined_markdown:
            combined_markdown += "\n"
        write_text(out_path, combined_markdown)

        metadata_path = out_dir / "datalab-run.json"
        average_score = round(sum(parse_scores) / len(parse_scores), 4) if parse_scores else None
        effective_page_range = pages_to_marker_range(ctx.pages)
        if not effective_page_range:
            flattened_pages = [page for chunk_pages in chunks for page in chunk_pages]
            effective_page_range = pages_to_marker_range(flattened_pages)
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "chunked": True,
            "chunk_size": chunk_size,
            "mode": mode,
            "page_range": effective_page_range,
            "selected_pages_count": _selected_page_count(ctx),
            "page_count": total_pages,
            "parse_quality_score": average_score,
            "cost_breakdown": _merge_numeric_dicts(cost_breakdowns),
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "chunks": chunk_meta,
        }, indent=2, ensure_ascii=False))

        notes = [
            "SaÃ­da avanÃ§ada gerada com Datalab Document Conversion API em chunks.",
            f"Modo: {mode}.",
            f"Chunking aplicado para documento longo ({len(chunks)} chunks de atÃ© {chunk_size} pÃ¡ginas).",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if average_score is not None:
            notes.append(f"parse_quality_score={average_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "datalab" / ctx.entry_id
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        effective_profile = _effective_document_profile(ctx.entry.document_profile, ctx.report.suggested_profile)
        page_range = pages_to_marker_range(ctx.pages)
        requested_mode = str(getattr(ctx.entry, "datalab_mode", "") or "").strip().lower()
        mode = requested_mode if requested_mode in {"fast", "balanced", "accurate"} else ("accurate" if effective_profile == "math_heavy" else "balanced")
        max_wait_seconds = _advanced_cli_stall_timeout("docling", ctx)
        should_chunk = _datalab_should_chunk(ctx)

        logger.info(
            "  [datalab] Long-doc policy: should_chunk=%s (selected_pages=%d, chunk_size=%d).",
            should_chunk,
            _selected_page_count(ctx),
            _datalab_chunk_size_for_workload(ctx),
        )
        if should_chunk:
            return self._run_chunked_datalab(
                ctx,
                out_dir,
                mode=mode,
                max_wait_seconds=max_wait_seconds,
            )
        return self._run_single_datalab(
            ctx,
            out_dir,
            mode=mode,
            page_range=page_range,
            max_wait_seconds=max_wait_seconds,
        )

        logger.info(
            "  [datalab] Enviando documento para a API (mode=%s, page_range=%s, max_wait=%ss).",
            mode,
            page_range or "all",
            max_wait_seconds,
        )

        try:
            result = convert_document_to_markdown(
                ctx.raw_target,
                output_format="markdown",
                mode=mode,
                page_range=page_range,
                disable_image_captions=True,
                disable_image_extraction=True,
                paginate=False,
                token_efficient_markdown=False,
                request_timeout=60,
                poll_interval=2.0,
                max_wait_seconds=max_wait_seconds,
            )
        except Exception as e:
            logger.error("  [datalab] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                error=str(e),
            )

        markdown = _sanitize_external_markdown_text(result.markdown)
        markdown = _strip_markdown_image_refs(markdown)
        write_text(out_path, markdown)

        metadata_path = out_dir / "datalab-run.json"
        write_text(metadata_path, json.dumps({
            "backend": "datalab",
            "base_url": get_datalab_base_url(),
            "request_id": result.request_id,
            "request_check_url": result.request_check_url,
            "mode": mode,
            "page_range": page_range,
            "page_count": result.page_count,
            "parse_quality_score": result.parse_quality_score,
            "cost_breakdown": result.cost_breakdown,
            "disable_image_extraction": True,
            "disable_image_captions": True,
            "images_saved": [],
            "metadata": result.metadata,
            "raw_response_tail": {
                "status": result.raw_response.get("status"),
                "success": result.raw_response.get("success"),
                "error": result.raw_response.get("error"),
            },
        }, indent=2, ensure_ascii=False))

        notes = [
            "Saída avançada gerada com Datalab Document Conversion API.",
            f"Modo: {mode}.",
            "Imagens e descricoes sinteticas do Datalab desativadas; a curadoria de imagens permanece app-side.",
        ]
        if result.parse_quality_score is not None:
            notes.append(f"parse_quality_score={result.parse_quality_score}.")

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=notes,
        )


class MarkerCLIBackend(ExtractionBackend):
    name = "marker"
    layer = "advanced"

    def available(self) -> bool:
        return bool(MARKER_CLI)

    def _run_single_marker(
        self,
        ctx: BackendContext,
        out_dir: Path,
        caps: Dict[str, object],
        pages: Optional[List[int]],
        stall_timeout: int,
    ) -> BackendRunResult:
        ensure_dir(out_dir)

        cmd = [
            MARKER_CLI,
            str(ctx.raw_target),
            "--output_format", "markdown",
            "--output_dir", str(out_dir),
        ]

        marker_range = pages_to_marker_range(pages)
        page_range_flag = caps.get("page_range_flag")
        if marker_range and page_range_flag:
            cmd.extend([page_range_flag, marker_range])
        elif marker_range:
            logger.info("  [marker] Versão atual não suporta page_range; processando o documento inteiro.")

        wants_force_ocr = _should_force_ocr_for_marker(ctx)
        force_ocr_flag = caps.get("force_ocr_flag")
        if wants_force_ocr and force_ocr_flag:
            cmd.append(force_ocr_flag)
        elif wants_force_ocr:
            logger.info("  [marker] Versão atual não suporta force_ocr; prosseguindo sem essa flag.")

        marker_llm_active = False
        marker_model = ""
        marker_ollama_url = str(getattr(ctx, "ollama_base_url", "") or "").strip()
        marker_torch_device = _marker_effective_torch_device(ctx)

        if _marker_should_use_llm(ctx):
            use_llm_flag = caps.get("use_llm_flag")
            llm_service_flag = caps.get("llm_service_flag")
            ollama_base_url_flag = caps.get("ollama_base_url_flag")
            ollama_model_flag = caps.get("ollama_model_flag")
            redo_inline_math_flag = caps.get("redo_inline_math_flag")
            marker_model = _marker_ollama_model(ctx)

            if not marker_model:
                logger.warning(
                    "  [marker] LLM habilitado, mas nenhum modelo do Marker foi configurado. "
                    "Defina 'Modelo Ollama do Marker' nas configurações para ativar --use_llm."
                )
            elif use_llm_flag:
                cmd.append(use_llm_flag)
                marker_llm_active = True
            else:
                logger.info("  [marker] Versão atual não suporta use_llm; prosseguindo sem LLM.")

            if marker_model and llm_service_flag:
                cmd.extend([llm_service_flag, MARKER_OLLAMA_SERVICE])
            elif marker_model and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta llm_service; mantendo serviço padrão.")

            if marker_model and ollama_base_url_flag and marker_ollama_url:
                cmd.extend([ollama_base_url_flag, marker_ollama_url])
            elif marker_model and marker_ollama_url and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta ollama_base_url; usando URL padrão do Marker.")

            if marker_model and ollama_model_flag:
                cmd.extend([ollama_model_flag, marker_model])
            elif marker_model and use_llm_flag:
                logger.info("  [marker] Versão atual não suporta ollama_model; usando modelo padrão do Marker.")

            if marker_model and redo_inline_math_flag and _marker_should_redo_inline_math(ctx):
                cmd.append(redo_inline_math_flag)

            # Desativar LLM em processors visuais quando o modelo não é vision.
            # Modelos texto-only (gemma3, llama3.1, etc) alucinam ao "descrever"
            # imagens que não conseguem ver. O Image Curator com qwen3-vl
            # cuida das descrições separadamente.
            if marker_model and not _marker_model_is_probably_vision(marker_model):
                _visual_overrides = {
                    "LLMImageDescriptionProcessor_use_llm": False,
                    "LLMComplexRegionProcessor_use_llm": False,
                    "LLMHandwritingProcessor_use_llm": False,
                }
                config_json_path = out_dir / "marker-llm-config.json"
                write_text(config_json_path, json.dumps(_visual_overrides, indent=2))
                cmd.extend(["--config_json", str(config_json_path)])
                logger.info(
                    "  [marker] Processors visuais desativados via config_json "
                    "(modelo '%s' não é vision). Imagens serão tratadas pelo Image Curator.",
                    marker_model,
                )

            # Aumentar timeout do OllamaService para modelos locais (default=30s
            # é insuficiente quando GPU é compartilhada com layout models).
            ollama_timeout_flag = caps.get("ollama_timeout_flag")
            if marker_model and ollama_timeout_flag:
                cmd.extend([ollama_timeout_flag, "120"])

        if marker_llm_active:
            if _marker_model_is_cloud_variant(marker_model):
                logger.warning(
                    "  [marker] O modelo '%s' parece ser variante cloud. Para estabilidade no Marker, prefira um modelo local como gemma3:4b.",
                    marker_model,
                )
            elif not _marker_model_is_probably_vision(marker_model):
                logger.info(
                    "  [marker] Modelo texto-only '%s' detectado. Extração de imagens desabilitada automaticamente; "
                    "LLM será usado apenas para math, tabelas e headers.",
                    marker_model,
                )
            logger.info(
                "  [marker] LLM ativo: service=%s model=%s base_url=%s redo_inline_math=%s torch_device=%s",
                MARKER_OLLAMA_SERVICE,
                marker_model,
                marker_ollama_url or "(padrão do Marker)",
                "sim" if "--redo_inline_math" in cmd or "--redo-inline-math" in cmd else "não",
                marker_torch_device,
            )
        else:
            logger.info("  [marker] LLM inativo para esta execução. TORCH_DEVICE=%s", marker_torch_device)

        llm_metadata = {
            "enabled": marker_llm_active,
            "service": MARKER_OLLAMA_SERVICE if marker_llm_active else None,
            "model": marker_model or None,
            "base_url": marker_ollama_url or None,
            "redo_inline_math": bool("--redo_inline_math" in cmd or "--redo-inline-math" in cmd),
            "recommended_model": _marker_model_is_qwen3_vl_8b(marker_model) if marker_model else False,
            "is_cloud_variant": _marker_model_is_cloud_variant(marker_model) if marker_model else False,
            "is_probably_vision": _marker_model_is_probably_vision(marker_model) if marker_model else False,
            "visual_processors_disabled": bool(marker_model and not _marker_model_is_probably_vision(marker_model)),
        }

        logger.info("  [marker] Comando: %s", " ".join(cmd))
        logger.info("  [marker] Iniciando processo...")

        try:
            returncode, stdout_lines, stderr_lines = _run_cli_with_timeout(
                cmd, "marker", ctx, stall_timeout=stall_timeout
            )
        except (InterruptedError, TimeoutError) as e:
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )
        except Exception as e:
            logger.error("  [marker] Erro ao executar: %s", e)
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=str(e),
            )

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)
        ollama_failures = [line for line in stderr_lines if "Ollama inference failed:" in line]

        if ollama_failures:
            logger.warning(
                "  [marker] O modelo '%s' retornou uma resposta inválida para o Marker. "
                "O serviço Ollama respondeu, mas o conteúdo não pôde ser interpretado como JSON estruturado. "
                "Teste outro modelo em 'Modelo Ollama do Marker' ou desative o LLM do Marker.",
                _marker_ollama_model(ctx) or "(não configurado)",
            )

        if returncode != 0:
            error_msg = (stderr_text or stdout_text or "Marker CLI falhou")[-4000:]
            logger.error("  [marker] Falhou: %s", error_msg[:500])
            return BackendRunResult(
                name=self.name, layer=self.layer, status="error",
                command=cmd, error=error_msg,
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        if md_path and md_path.exists():
            try:
                marker_text = _sanitize_external_markdown_text(md_path.read_text(encoding="utf-8", errors="replace"))
                md_path.write_text(marker_text, encoding="utf-8")
            except Exception as e:
                logger.warning("  [marker] Falha ao sanitizar markdown gerado: %s", e)
        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": stdout_text[-2000:],
            "stderr_tail": stderr_text[-2000:],
            "capabilities": caps,
            "page_range": marker_range,
            "stall_timeout": stall_timeout,
            "torch_device": {
                "configured": _marker_torch_device(ctx) or "auto",
                "effective": marker_torch_device,
            },
            "llm": llm_metadata,
            "ollama_failures": ollama_failures[-20:],
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Marker CLI."],
        )

    def _run_chunked_marker(
        self,
        ctx: BackendContext,
        out_dir: Path,
        caps: Dict[str, object],
        stall_timeout: int,
    ) -> BackendRunResult:
        chunk_size = _marker_chunk_size_for_workload(ctx)
        chunks = _build_marker_page_chunks(ctx.pages, ctx.report.page_count, chunk_size=chunk_size)
        if len(chunks) <= 1:
            return self._run_single_marker(ctx, out_dir, caps, ctx.pages, stall_timeout)

        logger.info(
            "  [marker] Documento grande/pesado; processando em %d chunks de até %d páginas.",
            len(chunks),
            chunk_size,
        )
        logger.info(
            "  [marker] Chunk policy: %d páginas por chunk para %d páginas selecionadas.",
            chunk_size,
            _selected_page_count(ctx),
        )
        combined_path = out_dir / f"{ctx.entry_id}.md"
        combined_parts: List[str] = []
        chunk_meta = []

        for idx, chunk_pages in enumerate(chunks, start=1):
            chunk_dir = out_dir / f"chunk-{idx:03d}"
            logger.info(
                "  [marker] Chunk %d/%d — páginas %d-%d",
                idx, len(chunks), chunk_pages[0] + 1, chunk_pages[-1] + 1,
            )
            result = self._run_single_marker(ctx, chunk_dir, caps, chunk_pages, stall_timeout)
            if result.status != "ok" or not result.markdown_path:
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    command=result.command,
                    error=f"Chunk {idx}/{len(chunks)} falhou: {result.error or 'sem markdown gerado'}",
                )

            md_abs = ctx.root_dir / result.markdown_path
            try:
                chunk_text = _sanitize_external_markdown_text(
                    md_abs.read_text(encoding="utf-8", errors="replace")
                )
            except Exception as e:
                return BackendRunResult(
                    name=self.name,
                    layer=self.layer,
                    status="error",
                    error=f"Falha ao ler markdown do chunk {idx}: {e}",
                )

            chunk_body = _strip_frontmatter_block(chunk_text).strip()
            chunk_body = _rewrite_markdown_asset_paths(chunk_body, md_abs.parent, combined_path.parent)
            combined_parts.append(
                f"<!-- MARKER_CHUNK {idx}: pages {chunk_pages[0] + 1}-{chunk_pages[-1] + 1} -->\n\n{chunk_body}"
            )
            chunk_meta.append({
                "chunk_index": idx,
                "page_range": pages_to_marker_range(chunk_pages),
                "markdown_path": result.markdown_path,
                "metadata_path": result.metadata_path,
            })

        write_text(combined_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, "\n\n".join(part for part in combined_parts if part).strip() + "\n"))

        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "capabilities": caps,
            "stall_timeout": stall_timeout,
            "chunked": True,
            "chunks": chunk_meta,
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(combined_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            notes=["Saída avançada gerada com Marker CLI em chunks."],
        )

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "marker" / ctx.entry_id
        ensure_dir(out_dir)

        caps = _detect_marker_capabilities()
        stall_timeout = _advanced_cli_stall_timeout("marker", ctx)
        effective_profile = (
            ctx.entry.document_profile
            if ctx.entry.document_profile != "auto"
            else ctx.report.suggested_profile
        )
        supports_chunking = bool(caps.get("page_range_flag"))
        selected_page_count = _selected_page_count(ctx)
        chunk_size = _marker_chunk_size_for_workload(ctx)
        chunking_mode = getattr(ctx, "marker_chunking_mode", "fallback")
        chunking_would_help = (
            effective_profile in {"math_heavy", "diagram_heavy"}
            and selected_page_count > chunk_size
            and supports_chunking
        )
        should_chunk = chunking_mode == "always" and chunking_would_help
        logger.info(
            "  [marker] Stall timeout efetivo: %ss para %d páginas selecionadas.",
            stall_timeout,
            selected_page_count,
        )

        logger.info(
            "  [marker] Chunking mode=%s (supports_chunking=%s, policy_match=%s).",
            chunking_mode,
            supports_chunking,
            chunking_would_help,
        )
        if should_chunk:
            result = self._run_chunked_marker(ctx, out_dir, caps, stall_timeout)
        else:
            result = self._run_single_marker(ctx, out_dir, caps, ctx.pages, stall_timeout)
            if (
                result.status == "error"
                and chunking_mode == "fallback"
                and chunking_would_help
                and result.error
                and "travou (sem output por" in result.error
            ):
                logger.warning("  [marker] Timeout detectado; repetindo em chunks como fallback.")
                result = self._run_chunked_marker(ctx, out_dir, caps, stall_timeout)

        if result.status == "ok":
            return result

        if DOCLING_CLI:
            logger.warning("  [marker] Falhou; tentando fallback para docling: %s", result.error)
            fallback = DoclingCLIBackend().run(ctx)
            if fallback.status == "ok":
                fallback.notes.append("Fallback automático após falha do Marker.")
            return fallback

        return result


# ---------------------------------------------------------------------------
# Selection / profiling
# ---------------------------------------------------------------------------

class BackendSelector:
    def __init__(self):
        self.backends: Dict[str, ExtractionBackend] = {
            "pymupdf4llm": PyMuPDF4LLMBackend(),
            "pymupdf": PyMuPDFBackend(),
            "datalab": DatalabCloudBackend(),
            "docling": DoclingCLIBackend(),
            "docling_python": DoclingPythonBackend(),
            "marker": MarkerCLIBackend(),
        }

    def available_backends(self) -> Dict[str, bool]:
        return {name: backend.available() for name, backend in self.backends.items()}

    def decide(self, entry: FileEntry, report: DocumentProfileReport) -> PipelineDecision:
        mode = entry.processing_mode or "auto"
        effective_profile = _effective_document_profile(entry.document_profile, report.suggested_profile)
        reasons: List[str] = []

        available = self.available_backends()

        def pick_first(names: Iterable[str]) -> Optional[str]:
            for name in names:
                if available.get(name):
                    return name
            return None

        def pick_advanced_for_profile(profile: str) -> Optional[str]:
            if profile == "math_heavy":
                return pick_first(["datalab", "marker", "docling"])
            if profile == "diagram_heavy":
                return pick_first(["docling", "marker"])
            return pick_first(["docling", "marker"])

        base_backend: Optional[str] = None
        advanced_backend: Optional[str] = None

        if entry.preferred_backend != "auto" and available.get(entry.preferred_backend):
            preferred = entry.preferred_backend
            if preferred in {"datalab", "docling", "docling_python", "marker"}:
                advanced_backend = preferred
                base_backend = pick_first(["pymupdf4llm", "pymupdf"])
                reasons.append(f"Backend preferido manualmente: {preferred}.")
            else:
                base_backend = preferred
                reasons.append(f"Backend base preferido manualmente: {preferred}.")

        if mode == "quick":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            reasons.append("Modo quick prioriza velocidade e baixo custo.")

        elif mode == "manual_assisted":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
            reasons.append("Modo manual_assisted gera base automática e exige revisão humana guiada.")

        elif mode == "high_fidelity":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile == "math_heavy":
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append("Documento math_heavy pede backend avançado com enrich-formula.")
            elif effective_profile in {"diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append("Documento visual/scanned pede backend avançado.")
            else:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                if advanced_backend:
                    reasons.append("Modo high_fidelity tenta saída avançada além da base.")

        else:  # auto
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "diagram_heavy", "scanned"}:
                advanced_backend = advanced_backend or pick_advanced_for_profile(effective_profile)
                reasons.append(f"Modo auto detectou perfil {effective_profile} e ativou camada avançada.")
            else:
                reasons.append("Modo auto detectou documento comum; saída base é suficiente.")

        if entry.formula_priority and not advanced_backend:
            advanced_backend = pick_advanced_for_profile(effective_profile)
            if advanced_backend:
                reasons.append("formula_priority ativou backend avançado.")

        if not base_backend and advanced_backend:
            reasons.append("Sem backend base disponível; usando apenas backend avançado.")

        return PipelineDecision(
            entry_id=entry.id(),
            processing_mode=mode,
            effective_profile=effective_profile,
            base_backend=base_backend,
            advanced_backend=advanced_backend,
            reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Repo builder
# ---------------------------------------------------------------------------

class RepoBuilder:
    def __init__(self, root_dir: Path, course_meta: Dict[str, str], entries: List[FileEntry],
                 options: Dict[str, object], *,
                 student_profile: Optional[StudentProfile] = None,
                 subject_profile: Optional[SubjectProfile] = None,
                 progress_callback=None):
        self.root_dir = root_dir
        self.course_meta = course_meta
        self.entries = entries
        self.options = options
        self.student_profile = student_profile
        self.subject_profile = subject_profile
        self.progress_callback = progress_callback  # Callable[[int, int, str], None] | None
        self.logs: List[Dict[str, object]] = []
        self.selector = BackendSelector()

    def _effective_course_meta(self, manifest: Optional[Dict[str, object]] = None) -> Dict[str, str]:
        course_meta = dict(self.course_meta or {})
        manifest_course = {}
        if manifest:
            raw_course = manifest.get("course")
            if isinstance(raw_course, dict):
                manifest_course = dict(raw_course)

        for key in ("course_name", "course_slug", "semester", "professor", "institution"):
            if not str(course_meta.get(key, "") or "").strip() and str(manifest_course.get(key, "") or "").strip():
                course_meta[key] = manifest_course[key]

        course_name = str(course_meta.get("course_name", "") or "").strip() or self.root_dir.name
        course_slug = str(course_meta.get("course_slug", "") or "").strip() or slugify(course_name) or slugify(self.root_dir.name) or "curso"
        course_meta["course_name"] = course_name
        course_meta["course_slug"] = course_slug
        course_meta["semester"] = str(course_meta.get("semester", "") or "").strip()
        course_meta["professor"] = str(course_meta.get("professor", "") or "").strip()
        course_meta["institution"] = str(course_meta.get("institution", "") or "").strip() or "PUCRS"
        return course_meta

    def _sleep_guard(self, reason: str):
        return prevent_system_sleep(
            enabled=bool(self.options.get("prevent_sleep_during_build", True)),
            reason=reason,
        )

    def build(self) -> None:
        with self._sleep_guard("build do repositorio"):
            self._build_impl()

    def _build_impl(self) -> None:
        logger.info("Building repository at %s", self.root_dir)
        logger.info("Creating directory structure...")
        self._create_structure()
        logger.info("Writing root/pedagogical files...")
        self._write_root_files()
        logger.info("Root files written. Starting entry processing...")

        manifest = {
            "app": APP_NAME,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "course": self.course_meta,
            "options": self.options,
            "environment": {
                "python": sys.version.split()[0],
                "pymupdf": HAS_PYMUPDF,
                "pymupdf4llm": HAS_PYMUPDF4LLM,
                "pdfplumber": HAS_PDFPLUMBER,
                "datalab_api": has_datalab_api_key(),
                "docling_cli": bool(DOCLING_CLI),
                "docling_python": has_docling_python_api(),
                "marker_cli": bool(MARKER_CLI),
            },
            "entries": [],
        }

        manifest_path = self.root_dir / "manifest.json"
        active_entries = [e for e in self.entries if getattr(e, "enabled", True)]
        skipped = len(self.entries) - len(active_entries)
        if skipped:
            logger.info("Pulando %d entries desabilitados.", skipped)
        total = len(active_entries)
        for i, entry in enumerate(active_entries):
            logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
            if self.progress_callback:
                self.progress_callback(i, total, entry.title)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)
            # Salva manifest após cada entry para não perder progresso
            manifest["logs"] = self.logs
            manifest = self._compact_manifest(manifest)
            write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
            logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
        if self.progress_callback:
            self.progress_callback(total, total, "")

        manifest["logs"] = self.logs
        manifest = self._compact_manifest(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

        # FILE_MAP — generated after all entries are processed
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(
                       {**self.course_meta, "_repo_root": self.root_dir},
                       manifest["entries"],
                       self.subject_profile,
                   ))

        # Resolve image references in markdowns → content/images/
        self._resolve_content_images()
        self._inject_all_image_descriptions()
        self._regenerate_pedagogical_files(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

        logger.info("Repository built successfully at %s", self.root_dir)

    def _create_structure(self) -> None:
        dirs = [
            "system",
            "course",
            "content/units",
            "content/concepts",
            "content/summaries",
            "content/references",
            "content/curated",
            "content/images",
            "exercises/lists",
            "exercises/solved",
            "exercises/index",
            "exams/past-exams",
            "exams/answer-keys",
            "exams/exam-index",
            "student",
            "scripts",
            "raw/pdfs/material-de-aula",
            "raw/pdfs/provas",
            "raw/pdfs/listas",
            "raw/pdfs/gabaritos",
            "raw/pdfs/cronograma",
            "raw/pdfs/referencias",
            "raw/pdfs/bibliografia",
            "raw/pdfs/fotos-de-prova",
            "raw/pdfs/outros",
            "raw/images/fotos-de-prova",
            "raw/images/provas",
            "raw/images/material-de-aula",
            "raw/images/outros",
            "code/professor", "code/student",
            "raw/code/professor", "raw/code/student",
            "raw/zip", "raw/repos",
            "assignments/enunciados", "assignments/entregas",
            "raw/pdfs/trabalhos",
            "whiteboard/raw", "whiteboard/transcriptions",
            "raw/images/quadro-branco",
            "staging/markdown-auto/pymupdf4llm",
            "staging/markdown-auto/pymupdf",
            "staging/markdown-auto/docling",
            "staging/markdown-auto/marker",
            "staging/markdown-auto/scanned",
            "staging/markdown-auto/code", "staging/zip-extract",
            "manual-review/code",
            "manual-review/web",
            "staging/assets/images",
            "staging/assets/inline-images",
            "staging/assets/tables",
            "staging/assets/table-detections",
            "manual-review/pdfs",
            "manual-review/images",
            "build/claude-knowledge",
        ]
        for d in dirs:
            ensure_dir(self.root_dir / d)

    def _write_root_files(self) -> None:
        course_slug = self.course_meta["course_slug"]

        # ── COURSE_IDENTITY ──────────────────────────────────────────
        write_text(
            self.root_dir / "course" / "COURSE_IDENTITY.md",
            f"""---
course_slug: {course_slug}
course_name: {self.course_meta['course_name']}
semester: {self.course_meta['semester']}
professor: {self.course_meta['professor']}
institution: {self.course_meta['institution']}
created_at: {datetime.now().isoformat(timespec='seconds')}
---

# COURSE_IDENTITY

## Disciplina
- Nome: {self.course_meta['course_name']}
- Slug: {course_slug}
- Semestre: {self.course_meta['semester']}
- Professor: {self.course_meta['professor']}
- Instituição: {self.course_meta['institution']}

## Objetivo
Este repositório organiza o conhecimento da disciplina em formato rastreável,
curado e reutilizável para um tutor acadêmico baseado no Claude.
""",
        )

        # ── System files ─────────────────────────────────────────────
        write_text(self.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "system" / "PEDAGOGY.md", pedagogy_md())
        write_text(self.root_dir / "system" / "MODES.md", modes_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md(self.course_meta, self.subject_profile))

        # ── Documentação interna do app — fica em build/, não no repo do tutor
        write_text(self.root_dir / "build" / "PDF_CURATION_GUIDE.md", pdf_curation_guide())
        write_text(self.root_dir / "build" / "BACKEND_ARCHITECTURE.md", backend_architecture_md())
        write_text(self.root_dir / "build" / "BACKEND_POLICY.yaml", backend_policy_yaml(self.options))

        # ── Course files ─────────────────────────────────────────────
        write_text(self.root_dir / "course" / "COURSE_MAP.md",
                   course_map_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "course" / "GLOSSARY.md",
                   glossary_md(
                       self.course_meta,
                       self.subject_profile,
                       root_dir=self.root_dir,
                       manifest_entries=[e.to_dict() for e in self.entries],
                   ))

        # ── Student files ─────────────────────────────────────────────
        write_text(self.root_dir / "student" / "STUDENT_STATE.md",
                   student_state_md(self.course_meta, self.student_profile))
        write_text(self.root_dir / "build" / "PROGRESS_SCHEMA.md", progress_schema_md())

        # ── Student profile ───────────────────────────────────────────
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))

        # ── Syllabus ──────────────────────────────────────────────────
        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        # ── Bibliography ──────────────────────────────────────────────
        bib_entries = [e for e in self.entries if e.category == "bibliografia"]
        write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                   bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # ── Exam & Exercise indexes ───────────────────────────────────
        exam_entries = [e for e in self.entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))

        exercise_entries = [e for e in self.entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # ── Assignment, Code & Whiteboard indexes ─────────────────────
        assignment_entries = [e for e in self.entries if e.category in ASSIGNMENT_CATEGORIES]
        if assignment_entries:
            write_text(self.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
                       assignment_index_md(self.course_meta, assignment_entries))

        code_entries = [e for e in self.entries if e.category in CODE_CATEGORIES]
        if code_entries:
            write_text(self.root_dir / "code" / "CODE_INDEX.md",
                       code_index_md(self.course_meta, code_entries, self.subject_profile))

        wb_entries = [e for e in self.entries if e.category in WHITEBOARD_CATEGORIES]
        if wb_entries:
            write_text(self.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md",
                       whiteboard_index_md(self.course_meta, wb_entries))

        # ── Root files ────────────────────────────────────────────────
        write_text(self.root_dir / "README.md", root_readme(self.course_meta))
        write_text(self.root_dir / ".gitignore", _generated_repo_gitignore_text())

        # ── Claude Project instructions (replaces INSTRUCOES_DO_GPT.txt)
        # Note: flags are False here because entries haven't been processed yet.
        # _regenerate_pedagogical_files() re-generates this with real flags.
        instructions = generate_claude_project_instructions(
            self.course_meta, self.student_profile, self.subject_profile,
            has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in self.entries),
            has_code=any(e.category in CODE_CATEGORIES for e in self.entries),
            has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in self.entries),
        )
        write_text(self.root_dir / "setup" / "INSTRUCOES_CLAUDE_PROJETO.md", instructions)

        # Instruções para outras plataformas
        _common_flags = dict(
            has_assignments=any(e.category in ASSIGNMENT_CATEGORIES for e in self.entries),
            has_code=any(e.category in CODE_CATEGORIES for e in self.entries),
            has_whiteboard=any(e.category in WHITEBOARD_CATEGORIES for e in self.entries),
        )
        write_text(self.root_dir / "setup" / "INSTRUCOES_GPT_PROJETO.md",
                   generate_gpt_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "setup" / "INSTRUCOES_GEMINI_PROJETO.md",
                   generate_gemini_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))

    # ------------------------------------------------------------------
    # Image resolution — copies referenced images into content/images/
    # ------------------------------------------------------------------

    _IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def _resolve_content_images(self) -> None:
        """Scan markdowns under content/ and staging/markdown-auto/ for image
        references.  Copy each referenced image into ``content/images/`` with a
        short, deterministic name and rewrite the markdown link to a relative
        path.  This keeps the repo uploadable to Claude Projects without
        thousands of staging assets.

        Incremental: keeps existing images and only copies new ones.
        Stale images (from removed entries) are cleaned up at the end.
        """
        images_dir = self.root_dir / "content" / "images"
        ensure_dir(images_dir)

        # Track existing files for stale cleanup later
        existing_files = {f for f in images_dir.iterdir() if f.is_file()} if images_dir.exists() else set()
        referenced_files: set = set()

        # Directories to scan for markdowns that the tutor will read
        scan_dirs = [
            self.root_dir / "content",
            self.root_dir / "staging" / "markdown-auto",
        ]

        target_ext = f".{self._image_format}" if self._image_format != "jpeg" else ".jpg"
        seen: Dict[str, Path] = {}  # original_path -> new_path (dedup)
        copied = 0

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for md_file in scan_dir.rglob("*.md"):
                # Skip markdowns inside content/images/ itself
                if images_dir in md_file.parents:
                    continue
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                replacements: List[tuple] = []
                for match in self._IMG_RE.finditer(text):
                    alt = match.group(1)
                    raw_path = match.group(2)

                    # Skip references already pointing to content/images/
                    if "content/images/" in raw_path.replace("\\", "/"):
                        # Track the file as referenced so it doesn't get cleaned up
                        ref_path = self._find_image(raw_path, md_file)
                        if ref_path and ref_path.exists():
                            referenced_files.add(ref_path)
                        continue

                    # Resolve the image file
                    img_path = self._find_image(raw_path, md_file)
                    if img_path is None or not img_path.exists():
                        continue

                    # Skip noise images (too small or solid color)
                    if img_path.stat().st_size < self._MIN_IMG_BYTES:
                        continue
                    if self._is_noise_image(img_path.read_bytes()):
                        continue

                    img_key = str(img_path)
                    if img_key in seen:
                        new_path = seen[img_key]
                    else:
                        # Build a short name: <parent-slug>-<filename>
                        parent_slug = slugify(img_path.parent.name) if img_path.parent.name else ""
                        short_name = f"{parent_slug}-{img_path.name}" if parent_slug else img_path.name
                        new_path = images_dir / short_name

                        # Handle collisions
                        if new_path.exists() and new_path.stat().st_size != img_path.stat().st_size:
                            stem = new_path.stem
                            suffix = new_path.suffix
                            counter = 2
                            while new_path.exists():
                                new_path = images_dir / f"{stem}-{counter}{suffix}"
                                counter += 1

                        if not new_path.exists():
                            shutil.copy2(str(img_path), str(new_path))
                            new_path = self._convert_image_format(new_path)
                            copied += 1
                        elif new_path.suffix.lower() not in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
                            # Existing file in wrong format — convert
                            new_path = self._convert_image_format(new_path)
                        seen[img_key] = new_path

                    referenced_files.add(new_path)

                    # Build relative path from this markdown to the image
                    try:
                        rel = Path(new_path).relative_to(md_file.parent)
                    except ValueError:
                        # Different directory trees — use repo-relative path
                        rel = Path(new_path).relative_to(self.root_dir)

                    rel_str = str(rel).replace("\\", "/")
                    old_ref = match.group(0)
                    new_ref = f"![{alt}]({rel_str})"
                    if old_ref != new_ref:
                        replacements.append((old_ref, new_ref))

                if replacements:
                    for old, new in replacements:
                        text = text.replace(old, new)
                    md_file.write_text(text, encoding="utf-8")

        # Clean up stale images (from removed entries)
        stale = existing_files - referenced_files
        for f in stale:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        if stale:
            logger.info("Cleaned up %d stale images from content/images/", len(stale))

        if copied:
            logger.info("Resolved %d new images into content/images/", copied)

    def _find_image(self, raw_path: str, md_file: Path) -> Optional[Path]:
        """Try to locate an image file from a markdown reference path."""
        # Normalize separators
        normalized = raw_path.replace("\\", "/")

        # 1) Absolute path — use directly
        p = Path(normalized)
        if p.is_absolute() and p.exists():
            return p

        # 2) Try relative to the markdown file's directory
        rel_to_md = md_file.parent / normalized
        if rel_to_md.exists():
            return rel_to_md

        # 3) Try relative to repo root
        rel_to_root = self.root_dir / normalized
        if rel_to_root.exists():
            return rel_to_root

        # 4) Extract the staging-relative portion from absolute paths
        # Pattern: .../staging/assets/... or .../staging/markdown-auto/...
        for marker in ("staging/assets/", "staging/markdown-auto/"):
            idx = normalized.find(marker)
            if idx >= 0:
                staging_rel = normalized[idx:]
                candidate = self.root_dir / staging_rel
                if candidate.exists():
                    return candidate

        return None

    _IMG_DESC_BLOCK_RE = _IMAGE_DESC_BLOCK_RE
    _image_curation_heading = staticmethod(_image_curation_heading_label)

    @staticmethod
    def inject_image_descriptions(markdown: str, image_curation: dict) -> str:
        return _low_token_inject_image_descriptions(
            markdown,
            image_curation,
            desc_block_re=RepoBuilder._IMG_DESC_BLOCK_RE,
            image_heading=RepoBuilder._image_curation_heading,
        )

    def _inject_all_image_descriptions(self) -> None:
        """Inject image descriptions into the most relevant markdowns for each entry."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return

        entries = manifest.get("entries", [])

        injected_count = 0
        for entry_data in entries:
            curation = entry_data.get("image_curation")
            if not curation:
                continue

            status = (curation.get("status") or "").strip().lower()
            if status not in {"described", "curated"} and not curation.get("pages"):
                continue

            target_markdowns = self._resolve_entry_markdown_targets(entry_data)

            if not target_markdowns:
                content_dir = self.root_dir / "content"
                if not content_dir.exists():
                    continue
                target_markdowns = list(content_dir.rglob("*.md"))

            for md_file in target_markdowns:
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                new_text = self.inject_image_descriptions(text, curation)
                if new_text != text:
                    md_file.write_text(new_text, encoding="utf-8")
                    injected_count += 1
                    try:
                        rel_md = safe_rel(md_file, self.root_dir)
                    except Exception:
                        rel_md = str(md_file)
                    logger.info(
                        "Injected image descriptions into %s for entry %s.",
                        rel_md,
                        entry_data.get("id") or entry_data.get("title") or "<unknown>",
                    )

        if injected_count:
            logger.info("Injected image descriptions into %d markdown files.", injected_count)

    def _resolve_entry_markdown_targets(self, entry_data: dict) -> List[Path]:
        target_markdowns: List[Path] = []
        seen_targets = set()

        def _is_allowed_rel_path(rel_path: str) -> bool:
            rel_posix = str(rel_path).replace("\\", "/").lower()
            return (
                rel_posix.startswith("content/")
                or rel_posix.startswith("exercises/")
                or rel_posix.startswith("exams/")
                or rel_posix.startswith("assignments/")
                or rel_posix.startswith("code/")
                or rel_posix.startswith("whiteboard/")
                or rel_posix.startswith("staging/markdown-auto/")
            )

        for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
            rel_path = entry_data.get(key)
            if not rel_path or not str(rel_path).lower().endswith(".md"):
                continue
            md_file = self.root_dir / rel_path
            if not md_file.exists() or not md_file.is_file():
                continue
            if not _is_allowed_rel_path(rel_path):
                continue
            if md_file in seen_targets:
                continue
            seen_targets.add(md_file)
            target_markdowns.append(md_file)

        if target_markdowns:
            return target_markdowns

        entry_id = (entry_data.get("id") or "").strip()
        if not entry_id:
            return target_markdowns

        # Fallback for stale manifest paths: locate markdowns that declare this entry_id.
        search_roots = [
            self.root_dir / "content",
            self.root_dir / "exercises",
            self.root_dir / "exams",
            self.root_dir / "assignments",
            self.root_dir / "code",
            self.root_dir / "whiteboard",
            self.root_dir / "staging" / "markdown-auto",
        ]
        frontmatter_mark = f'entry_id: "{entry_id}"'
        for root in search_roots:
            if not root.exists():
                continue
            for md_file in root.rglob("*.md"):
                if md_file in seen_targets:
                    continue
                try:
                    text = md_file.read_text(encoding="utf-8")
                except Exception:
                    continue
                if frontmatter_mark not in text:
                    continue
                seen_targets.add(md_file)
                target_markdowns.append(md_file)

        return target_markdowns

    def _heal_manifest_markdown_paths(self, manifest: dict) -> dict:
        entries = manifest.get("entries", []) or []
        healed = 0
        for entry_data in entries:
            if not isinstance(entry_data, dict):
                continue

            live_targets: List[Tuple[str, Path]] = []
            for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
                rel_path = entry_data.get(key)
                if not rel_path or not str(rel_path).lower().endswith(".md"):
                    continue
                md_file = self.root_dir / rel_path
                if md_file.exists() and md_file.is_file():
                    live_targets.append((key, md_file))

            if live_targets:
                # If a final tutor-facing markdown exists, normalize manifest to use it explicitly.
                final_targets = []
                for key, md_file in live_targets:
                    rel_md = safe_rel(md_file, self.root_dir).replace("\\", "/")
                    if (
                        rel_md.startswith("content/curated/")
                        or rel_md.startswith("exercises/lists/")
                        or rel_md.startswith("exams/past-exams/")
                        or rel_md.startswith("assignments/")
                        or rel_md.startswith("code/")
                        or rel_md.startswith("whiteboard/")
                    ):
                        final_targets.append(rel_md)
                if final_targets:
                    preferred = final_targets[0]
                    if entry_data.get("approved_markdown") != preferred:
                        entry_data["approved_markdown"] = preferred
                        healed += 1
                    if entry_data.get("curated_markdown") != preferred:
                        entry_data["curated_markdown"] = preferred
                        healed += 1
                    if entry_data.get("base_markdown") != preferred:
                        entry_data["base_markdown"] = preferred
                        healed += 1
                continue

            resolved_targets = self._resolve_entry_markdown_targets(entry_data)
            if not resolved_targets:
                continue

            preferred = safe_rel(resolved_targets[0], self.root_dir)
            if entry_data.get("base_markdown") != preferred:
                entry_data["base_markdown"] = preferred
                healed += 1
            if (
                preferred.startswith("content/curated/")
                or preferred.startswith("exercises/lists/")
                or preferred.startswith("exams/past-exams/")
                or preferred.startswith("assignments/")
                or preferred.startswith("code/")
                or preferred.startswith("whiteboard/")
            ):
                if entry_data.get("approved_markdown") != preferred:
                    entry_data["approved_markdown"] = preferred
                    healed += 1
                if entry_data.get("curated_markdown") != preferred:
                    entry_data["curated_markdown"] = preferred
                    healed += 1

        if healed:
            logger.info("Healed markdown targets for %d manifest entries.", healed)
        manifest["entries"] = entries
        return manifest

    def _write_source_registry(self, manifest: Dict[str, object]) -> None:
        lines = [
            f"generated_at: {manifest['generated_at']}",
            "sources:",
        ]
        for item in manifest["entries"]:
            lines.extend(
                [
                    f"  - id: {item['id']}",
                    f"    title: {json_str(item['title'])}",
                    f"    category: {item['category']}",
                    f"    file_type: {item['file_type']}",
                    f"    source_path: {json_str(item['source_path'])}",
                    f"    raw_target: {json_str(item.get('raw_target'))}",
                    f"    processing_mode: {item.get('processing_mode', 'auto')}",
                    f"    effective_profile: {item.get('effective_profile', 'auto')}",
                    f"    include_in_bundle: {str(item.get('include_in_bundle', True)).lower()}",
                    f"    professor_signal: {json_str(item.get('professor_signal', ''))}",
                ]
            )
        write_text(self.root_dir / "course" / "SOURCE_REGISTRY.yaml", "\n".join(lines) + "\n")

    def _write_bundle_seed(self, manifest: Dict[str, object]) -> None:
        course_meta = self._effective_course_meta(manifest)
        selected = []
        for entry in manifest["entries"]:
            score = _bundle_priority_score(entry)
            if score < 30:
                continue
            chosen_markdown = (
                entry.get("approved_markdown")
                or entry.get("curated_markdown")
                or entry.get("advanced_markdown")
                or entry.get("base_markdown")
            )
            if not chosen_markdown:
                continue
            selected.append((score, entry))

        selected.sort(
            key=lambda item: (
                -item[0],
                (item[1].get("category") or ""),
                (item[1].get("title") or ""),
            )
        )
        seed = {
            "generated_at": manifest["generated_at"],
            "course_slug": course_meta["course_slug"],
            "target_platform": "claude-projects",
            "selection_policy": {
                "min_score": 30,
                "goal": "baixo-custo-alto-sinal",
                "routing_first": True,
                "exclude_full_text": True,
                "metadata_only": True,
            },
                "bundle_candidates": [
                _bundle_seed_candidate(e, score)
                for score, e in selected
            ],
        }
        write_text(
            self.root_dir / "build" / "claude-knowledge" / "bundle.seed.json",
            json.dumps(seed, indent=2, ensure_ascii=False)
        )

    def _write_build_report(self, manifest: Dict[str, object]) -> None:
        platform = (
            getattr(self, "_selected_platform", None)
            or getattr(self.subject_profile, "preferred_llm", "claude")
            or "claude"
        )
        platform_map = {
            "claude": ("setup/INSTRUCOES_CLAUDE_PROJETO.md",
                       "Cole no campo 'Instructions' do Projeto Claude"),
            "gpt":    ("setup/INSTRUCOES_GPT_PROJETO.md",
                       "Cole no campo 'Instructions' do GPT / Custom GPT"),
            "gemini": ("setup/INSTRUCOES_GEMINI_PROJETO.md",
                       "Cole no campo de instruções do Gem no Google AI Studio"),
        }
        filename, instruction = platform_map.get(platform, platform_map["claude"])

        report = [
            "# BUILD_REPORT",
            "",
            f"- generated_at: {manifest['generated_at']}",
            f"- preferred_platform: {platform}",
            f"- pymupdf: {HAS_PYMUPDF}",
            f"- pymupdf4llm: {HAS_PYMUPDF4LLM}",
            f"- pdfplumber: {HAS_PDFPLUMBER}",
            f"- datalab_api: {has_datalab_api_key()}",
            f"- docling_cli: {bool(DOCLING_CLI)}",
            f"- docling_python: {has_docling_python_api()}",
            f"- marker_cli: {bool(MARKER_CLI)}",
            "",
            f"## Plataforma principal: {platform.upper()}",
            "",
            f"> Copie o conteúdo de `{filename}`",
            f"> {instruction}",
            "",
            "Os três arquivos de instruções foram gerados:",
        ]
        for k, (f, _) in platform_map.items():
            marker = " **<< atual**" if k == platform else ""
            report.append(f"- `{f}`{marker}")

        report.extend([
            "",
            "## Regras práticas de curadoria",
            "- PDFs simples: camada base costuma bastar.",
            "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
            "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido.",
            "- Atualizar `student/STUDENT_STATE.md` após cada sessão de estudo.",
        ])
        write_text(self.root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")

    def _remove_entry_consolidated_images(self, entry_id: str) -> int:
        """Remove consolidated content/images assets that belong to one entry."""
        if not entry_id:
            return 0

        removed_count = 0
        images_dir = self.root_dir / "content" / "images"
        if not images_dir.exists():
            return 0

        entry_prefix = entry_id.lower()
        for img_path in images_dir.iterdir():
            if not img_path.is_file():
                continue
            lower_name = img_path.name.lower()
            if not (
                lower_name == entry_prefix
                or lower_name.startswith(entry_prefix + "-")
                or lower_name.startswith(entry_prefix + "_")
            ):
                continue
            try:
                img_path.unlink()
                removed_count += 1
            except Exception as e:
                logger.warning("Could not remove consolidated image %s: %s", img_path, e)

        scanned_dir = images_dir / "scanned" / entry_id
        if scanned_dir.exists():
            try:
                shutil.rmtree(scanned_dir)
                removed_count += 1
            except Exception as e:
                logger.warning("Could not remove scanned image dir %s: %s", scanned_dir, e)

        return removed_count

    def _process_entry(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "id": entry.id(),
            "title": entry.title,
            "category": entry.category,
            "file_type": entry.file_type,
            "source_path": entry.source_path,
            "tags": entry.tags,
            "manual_tags": list(entry.manual_tags or []),
            "auto_tags": list(entry.auto_tags or []),
            "manual_unit_slug": entry.manual_unit_slug,
            "manual_timeline_block_id": entry.manual_timeline_block_id,
            "notes": entry.notes,
            "professor_signal": entry.professor_signal,
            "include_in_bundle": entry.include_in_bundle,
            "relevant_for_exam": entry.relevant_for_exam,
            "processing_mode": entry.processing_mode,
            "document_profile": entry.document_profile,
            "preferred_backend": entry.preferred_backend,
            "datalab_mode": entry.datalab_mode,
            "formula_priority": entry.formula_priority,
            "preserve_pdf_images_in_markdown": entry.preserve_pdf_images_in_markdown,
            "force_ocr": entry.force_ocr,
            "extract_images": entry.extract_images,
            "extract_tables": entry.extract_tables,
            "page_range": entry.page_range,
            "ocr_language": entry.ocr_language,
        }

        src = Path(entry.source_path)
        if entry.file_type not in ("url", "github-repo") and not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        if entry.file_type == "url":
            item.update(self._process_url(entry))
            return item

        if entry.file_type == "github-repo":
            item.update(self._process_github_repo(entry))
            return item

        safe_name = f"{entry.id()}{src.suffix.lower()}"

        if entry.file_type == "code":
            code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
            raw_target  = self.root_dir / "raw" / "code" / code_subdir / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_code(entry, raw_target))
            return item

        if entry.file_type == "zip":
            raw_target = self.root_dir / "raw" / "zip" / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_zip(entry, raw_target))
            return item

        if entry.file_type == "pdf":
            raw_target = self.root_dir / "raw" / "pdfs" / entry.category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_pdf(entry, raw_target))
        else:
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "outros"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_url(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None, "pipeline_decision": None,
            "base_markdown": None, "advanced_markdown": None,
            "advanced_backend": None, "base_backend": "url_fetcher",
            "manual_review": None,
        }
        url_dest = self.root_dir / "staging" / "markdown-auto" / "url_fetcher"
        ensure_dir(url_dest)
        md_file = url_dest / f"{entry.id()}.md"
        url = entry.source_path
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                charset = response.info().get_content_charset('utf-8')
                html = response.read().decode(charset, errors='replace')
            try:
                markdown_content = _html_to_structured_markdown(html, url, entry.title)
            except ImportError:
                markdown_content = (
                    f"# {entry.title}\n\n"
                    f"- URL: [{url}]({url})\n\n"
                    "> BeautifulSoup não instalado. Conteúdo HTML não foi convertido para Markdown estruturado.\n"
                )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "ok"})
        except Exception as e:
            logger.warning(f"Failed to fetch content from URL {url}: {e}")
            markdown_content = (
                f"# {entry.title}\n\n"
                f"- URL: [{url}]({url})\n\n"
                f"> Não foi possível carregar o conteúdo: {e}\n"
            )
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "error", "error": str(e)})
        write_text(md_file, markdown_content)
        item["base_markdown"] = safe_rel(md_file, self.root_dir)
        manual = self.root_dir / "manual-review" / "web" / f"{entry.id()}.md"
        write_text(manual, manual_url_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _check_cancel(self):
        """Levanta InterruptedError se o build foi cancelado."""
        if self.progress_callback:
            # O progress_callback da UI verifica o cancel_event e levanta InterruptedError
            try:
                self.progress_callback(-1, -1, "")
            except InterruptedError:
                raise

    @staticmethod
    def _quick_page_count(pdf_path: Path) -> int:
        if not HAS_PYMUPDF:
            return 0
        try:
            doc = pymupdf.open(str(pdf_path))
            n = doc.page_count
            doc.close()
            return n
        except Exception:
            return 0

    def _apply_math_normalization(self, md_rel_path: Optional[str]) -> None:
        """Read a generated markdown file and normalize Unicode math → LaTeX."""
        if not md_rel_path:
            return
        try:
            md_path = self.root_dir / md_rel_path
            if not md_path.exists():
                return
            original = md_path.read_text(encoding="utf-8")
            normalized = _normalize_unicode_math(original)
            if normalized != original:
                write_text(md_path, normalized)
                logger.info("  [math-norm] Normalizado símbolos Unicode → LaTeX em %s", md_rel_path)
        except Exception as e:
            logger.warning("  [math-norm] Falha ao normalizar %s: %s", md_rel_path, e)

    
    def _render_scanned_pdf_as_images(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        """
        Para PDFs escaneados:
        - renderiza cada página como imagem
        - cria um markdown base que referencia essas imagens
        - usa JPG / JPEG para reduzir peso
        """
        if not HAS_PYMUPDF:
            raise RuntimeError("PyMuPDF é obrigatório para tratar PDFs scanned como imagens.")

        from PIL import Image as PILImage

        entry_id = entry.id()
        images_dir = self.root_dir / "content" / "images" / "scanned" / entry_id
        md_dir = self.root_dir / "staging" / "markdown-auto" / "scanned"

        ensure_dir(md_dir)
        if images_dir.exists():
            shutil.rmtree(images_dir)
        ensure_dir(images_dir)

        md_path = md_dir / f"{entry_id}.md"

        doc = pymupdf.open(str(raw_target))
        refs = []
        try:
            pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
            pages = [p for p in pages if 0 <= p < doc.page_count]

            for page_num in pages:
                page = doc[page_num]
                pix = page.get_pixmap(matrix=pymupdf.Matrix(1.35, 1.35), alpha=False)

                pil_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
                img_path = images_dir / f"page-{page_num + 1:03d}.jpg"
                pil_img.save(img_path, format="JPEG", quality=82, optimize=True)

                rel = os.path.relpath(str(img_path), str(md_path.parent)).replace("\\", "/")
                refs.append(
                    f"## Página {page_num + 1}\n\n"
                    f"![Página {page_num + 1}]({rel})\n"
                )
        finally:
            doc.close()

        body = (
            f"# {entry.title}\n\n"
            "> Documento tratado como **imagem** porque o perfil efetivo foi `scanned`.\n"
            "> Cada página foi convertida em imagem para leitura visual.\n\n"
            + "\n".join(refs)
        )

        write_text(md_path, wrap_frontmatter({
            "entry_id": entry_id,
            "title": entry.title,
            "backend": "scanned-pages",
            "source_pdf": safe_rel(raw_target, self.root_dir),
            "page_range": entry.page_range,
            "effective_profile": "scanned",
        }, body))

        return {
            "base_markdown": safe_rel(md_path, self.root_dir),
            "base_backend": "scanned-pages",
            "advanced_markdown": None,
            "advanced_backend": None,
            "rendered_pages_dir": safe_rel(images_dir, self.root_dir),
        }
        



    def _process_pdf(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        import time
        item: Dict[str, object] = {
            "document_report": None,
            "pipeline_decision": None,
            "base_markdown": None,
            "advanced_markdown": None,
            "advanced_backend": None,
            "base_backend": None,
            "images_dir": None,
            "tables_dir": None,
            "table_detection_dir": None,
            "manual_review": None,
            "raw_target": safe_rel(raw_target, self.root_dir),
        }
        t0 = time.time()

        logger.info(
            "  [1/6] Profiling PDF: %s (%d págs, %.1f MB)",
            entry.title,
            self._quick_page_count(raw_target),
            raw_target.stat().st_size / 1048576,
        )
        report = self._profile_pdf(raw_target, entry)
        decision = self.selector.decide(entry, report)
        logger.info(
            "  [1/6] Profile=%s, Paginas=%d, Texto=%d chars, Imagens=%d, Scan=%s",
            decision.effective_profile,
            report.page_count,
            report.text_chars,
            report.images_count,
            report.suspected_scan,
        )

        item["document_report"] = asdict(report)
        item["pipeline_decision"] = asdict(decision)
        item["effective_profile"] = decision.effective_profile
        item["base_backend"] = decision.base_backend
        item["advanced_backend"] = decision.advanced_backend

        stall_timeout = int(self.options.get("stall_timeout", 300))
        ctx = BackendContext(
            self.root_dir,
            raw_target,
            entry,
            report,
            cancel_check=self._check_cancel,
            stall_timeout=stall_timeout,
            marker_chunking_mode=str(self.options.get("marker_chunking_mode", "fallback")),
            marker_use_llm=bool(self.options.get("marker_use_llm", False)),
            marker_llm_model=str(self.options.get("marker_llm_model", "") or ""),
            marker_torch_device=str(self.options.get("marker_torch_device", "auto") or "auto"),
            ollama_base_url=str(self.options.get("ollama_base_url", "") or ""),
            vision_model=str(self.options.get("vision_model", "") or ""),
        )

        self._check_cancel()

        # PDFs scanned: 1 página = 1 imagem
        if decision.effective_profile == "scanned":
            logger.info("  [2/6] Perfil scanned detectado → convertendo páginas em imagens.")
            try:
                scanned_result = self._render_scanned_pdf_as_images(entry, raw_target)
                item.update(scanned_result)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "ok",
                    "rendered_pages_dir": scanned_result.get("rendered_pages_dir"),
                })
            except Exception as e:
                logger.error("  [2/6] Falha ao tratar scanned como imagens: %s", e)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "error",
                    "error": str(e),
                })
                raise

            manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
            write_text(manual, manual_pdf_review_template(entry, item))
            item["manual_review"] = safe_rel(manual, self.root_dir)

            logger.info("  ✓ PDF scanned concluído como páginas-imagem: %s", entry.title)
            return item

        if decision.base_backend:
            logger.info("  [2/6] Backend base: %s → iniciando...", decision.base_backend)
            t1 = time.time()
            backend = self.selector.backends[decision.base_backend]
            result = backend.run(ctx)
            logger.info(
                "  [2/6] Backend base: %s → %s (%.1fs)",
                decision.base_backend,
                result.status,
                time.time() - t1,
            )
            self._log_backend_result(entry.id(), result)

            if result.status == "ok":
                item["base_markdown"] = result.markdown_path
                self._apply_math_normalization(result.markdown_path)
            else:
                logger.warning("  Base backend %s failed: %s", decision.base_backend, result.error)
                item.setdefault("backend_errors", []).append({decision.base_backend: result.error})
        else:
            logger.info("  [2/6] Backend base: nenhum selecionado")

        self._check_cancel()

        if decision.advanced_backend:
            logger.info("  [3/6] Backend avançado: %s → iniciando...", decision.advanced_backend)
            t1 = time.time()
            backend = self.selector.backends[decision.advanced_backend]
            result = backend.run(ctx)
            logger.info(
                "  [3/6] Backend avançado: %s → %s (%.1fs)",
                decision.advanced_backend,
                result.status,
                time.time() - t1,
            )
            self._log_backend_result(entry.id(), result)

            if result.status == "ok":
                item["advanced_backend"] = result.name
                item["advanced_markdown"] = result.markdown_path
                item["advanced_asset_dir"] = result.asset_dir
                item["advanced_metadata_path"] = result.metadata_path
                self._apply_math_normalization(result.markdown_path)
                if (
                    result.name == "marker"
                    and not ctx.marker_use_llm
                    and item.get("base_markdown")
                    and item.get("advanced_markdown")
                    and not ctx.report.suspected_scan
                ):
                    try:
                        base_path = self.root_dir / str(item["base_markdown"])
                        advanced_path = self.root_dir / str(item["advanced_markdown"])
                        if base_path.exists() and advanced_path.exists():
                            fused_text, fusion_stats = _hybridize_marker_markdown_with_base(
                                base_path.read_text(encoding="utf-8", errors="replace"),
                                advanced_path.read_text(encoding="utf-8", errors="replace"),
                            )
                            if fusion_stats["replacements"] > 0:
                                hybrid_dir = self.root_dir / "staging" / "markdown-auto" / "marker-hybrid"
                                ensure_dir(hybrid_dir)
                                hybrid_path = hybrid_dir / f"{entry.id()}.md"
                                write_text(hybrid_path, fused_text)
                                item["advanced_markdown_raw"] = item["advanced_markdown"]
                                item["advanced_markdown"] = safe_rel(hybrid_path, self.root_dir)
                                item["advanced_hybrid"] = {
                                    "source": "marker+base-text-rescue",
                                    "replacements": fusion_stats["replacements"],
                                    "candidate_matches": fusion_stats["candidate_matches"],
                                }
                                logger.info(
                                    "  [3/6] Marker híbrido aplicado: %d linhas recuperadas do markdown base.",
                                    fusion_stats["replacements"],
                                )
                    except Exception as e:
                        logger.warning("  [3/6] Falha ao aplicar híbrido Marker+base: %s", e)
            else:
                logger.warning("  Advanced backend %s failed: %s", decision.advanced_backend, result.error)
                item.setdefault("backend_errors", []).append({decision.advanced_backend: result.error})
        else:
            logger.info("  [3/6] Backend avançado: nenhum selecionado")

        self._check_cancel()

        if HAS_PYMUPDF and entry.extract_images:
            logger.info("  [4/6] Extraindo imagens...")
            try:
                images_dir = self.root_dir / "staging" / "assets" / "images" / entry.id()
                image_policy = _pdf_image_extraction_policy(ctx)
                count = self._extract_pdf_images(
                    raw_target,
                    images_dir,
                    pages=parse_page_range(entry.page_range),
                    ctx=ctx,
                )
                item["images_dir"] = safe_rel(images_dir, self.root_dir)
                item["image_extraction"] = {
                    "source": "pymupdf-pdf-images",
                    "mode": image_policy["mode"],
                    "count": count,
                }
                logger.info("  [4/6] %d imagens extraídas", count)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "extract_images",
                    "status": "ok",
                    "count": count,
                })
            except Exception as e:
                logger.error("  [4/6] Falha na extração de imagens: %s", e)
                self.logs.append({
                    "entry": entry.id(),
                    "step": "extract_images",
                    "status": "error",
                    "error": str(e),
                })
        else:
            logger.info("  [4/6] Extração de imagens: pulado")

        self._check_cancel()

        if entry.extract_tables:
            logger.info("  [6/6] Extraindo tabelas...")

            if HAS_PDFPLUMBER:
                try:
                    tables_dir = self.root_dir / "staging" / "assets" / "tables" / entry.id()
                    count = self._extract_tables_pdfplumber(
                        raw_target,
                        tables_dir,
                        pages=parse_page_range(entry.page_range),
                    )
                    item["tables_dir"] = safe_rel(tables_dir, self.root_dir)
                    logger.info("  [6/6] pdfplumber: %d tabelas extraídas", count)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "ok",
                        "count": count,
                    })
                except Exception as e:
                    logger.error("  [6/6] pdfplumber falhou: %s", e)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "error",
                        "error": str(e),
                    })

            if HAS_PYMUPDF:
                try:
                    det_dir = self.root_dir / "staging" / "assets" / "table-detections" / entry.id()
                    count = self._detect_tables_pymupdf(
                        raw_target,
                        det_dir,
                        pages=parse_page_range(entry.page_range),
                    )
                    item["table_detection_dir"] = safe_rel(det_dir, self.root_dir)
                    logger.info("  [6/6] pymupdf: %d detecções de tabela", count)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "ok",
                        "count": count,
                    })
                except Exception as e:
                    logger.error("  [6/6] pymupdf table detection falhou: %s", e)
                    self.logs.append({
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "error",
                        "error": str(e),
                    })
        else:
            logger.info("  [6/6] Tabelas: pulado")

        active_markdown_rel = str(item.get("advanced_markdown") or item.get("base_markdown") or "").strip()
        latex_check = {"corrupted": False, "score": 0, "signals": []}
        if active_markdown_rel:
            try:
                active_markdown_path = self.root_dir / active_markdown_rel
                if active_markdown_path.exists():
                    latex_check = _detect_latex_corruption(
                        active_markdown_path.read_text(encoding="utf-8", errors="replace")
                    )
            except Exception as e:
                logger.warning("  [latex-check] Falha ao analisar %s: %s", active_markdown_rel, e)

        item["latex_corruption"] = {
            "detected": bool(latex_check.get("corrupted")),
            "score": int(latex_check.get("score", 0) or 0),
            "signals": list(latex_check.get("signals") or []),
            "markdown_path": active_markdown_rel or None,
        }
        if item["latex_corruption"]["detected"]:
            logger.warning(
                "  [latex-check] LaTeX possivelmente corrompido em %s (score: %s/100).",
                entry.title,
                item["latex_corruption"]["score"],
            )
            self.logs.append({
                "entry": entry.id(),
                "step": "latex_check",
                "status": "warning",
                "message": (
                    f"LaTeX possivelmente corrompido "
                    f"(score: {item['latex_corruption']['score']}/100) — "
                    f"sinais: {'; '.join(item['latex_corruption']['signals'])}"
                ),
            })

        logger.info("  ✓ PDF concluído em %.1fs: %s", time.time() - t0, entry.title)

        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _process_image(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {"manual_review": None}
        manual = self.root_dir / "manual-review" / "images" / f"{entry.id()}.md"
        write_text(manual, manual_image_review_template(entry, raw_target, self.root_dir))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        self.logs.append({"entry": entry.id(), "step": "image_import", "status": "ok"})
        return item

    def _process_code(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {"manual_review": None, "base_markdown": None}
        ext  = raw_target.suffix.lower().lstrip(".")
        lang = LANG_MAP.get(ext, ext)
        try:
            code_content = raw_target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Could not read code file %s: %s", raw_target, e)
            code_content = f"[Erro ao ler arquivo: {e}]"

        body_content = code_content
        if ext == "ipynb":
            lang, body_content = _compact_notebook_markdown(code_content)

        curated_subdir = "student" if entry.category == "codigo-aluno" else "professor"
        curated_dir    = self.root_dir / "code" / curated_subdir
        ensure_dir(curated_dir)
        curated_path   = curated_dir / f"{entry.id()}.md"

        body  = f"# {entry.title}\n\n"
        body += f"> **Linguagem:** {lang}"
        if entry.tags:
            body += f"  |  **Unidade:** {entry.tags}"
        if entry.notes:
            body += f"\n> {entry.notes}"
        if ext == "ipynb":
            body += "\n\n" + body_content.rstrip() + "\n"
        else:
            body += f"\n\n```{lang}\n{body_content}\n```\n"

        write_text(curated_path, wrap_frontmatter({
            "entry_id": entry.id(), "title": entry.title,
            "language": lang, "category": entry.category,
            "unit": entry.tags, "source": safe_rel(raw_target, self.root_dir),
        }, body))

        item["base_markdown"] = safe_rel(curated_path, self.root_dir)
        item["language"]      = lang

        manual = self.root_dir / "manual-review" / "code" / f"{entry.id()}.md"
        write_text(manual, f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_code_review
category: {entry.category}
language: {lang}
unit: {entry.tags}
---

# Revisão — {entry.title}

## Checklist
- [ ] Código compila/executa sem erros
- [ ] Anotar padrões de estilo do professor
- [ ] Identificar conceitos demonstrados

## Destino
`{safe_rel(curated_path, self.root_dir)}`
""")
        item["manual_review"] = safe_rel(manual, self.root_dir)
        self.logs.append({"entry": entry.id(), "step": "code_import",
                          "status": "ok", "language": lang})
        return item

    def _process_zip(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        import zipfile
        item: Dict[str, object] = {"extracted_files": [], "base_markdown": None,
                                    "extraction_error": None}
        extract_dir = self.root_dir / "staging" / "zip-extract" / entry.id()
        ensure_dir(extract_dir)
        try:
            with zipfile.ZipFile(raw_target, "r") as zf:
                zf.extractall(extract_dir)
        except Exception as e:
            item["extraction_error"] = str(e)
            self.logs.append({"entry": entry.id(), "step": "zip_extract",
                              "status": "error", "error": str(e)})
            return item

        processed = []
        for code_path in sorted(extract_dir.rglob("*")):
            if not code_path.is_file():
                continue
            parts = code_path.relative_to(extract_dir).parts
            if any(p.startswith(".") or p in {
                "__pycache__", "node_modules", "dist", "build", ".git"
            } for p in parts):
                continue
            if code_path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if code_path.stat().st_size > 500_000:
                continue

            relative_name = str(code_path.relative_to(extract_dir))
            sub_entry = FileEntry(
                source_path=str(code_path), file_type="code",
                category=entry.category, title=relative_name,
                tags=entry.tags, notes=f"Extraído de: {entry.title}",
                professor_signal=entry.professor_signal,
                include_in_bundle=entry.include_in_bundle,
            )
            code_subdir  = "student" if entry.category == "codigo-aluno" else "professor"
            safe_name_c  = f"{sub_entry.id()}{code_path.suffix.lower()}"
            raw_target_c = self.root_dir / "raw" / "code" / code_subdir / safe_name_c
            ensure_dir(raw_target_c.parent)
            shutil.copy2(code_path, raw_target_c)

            sub_result = self._process_code(sub_entry, raw_target_c)
            sub_result["title"] = relative_name
            processed.append(sub_result)

        item["extracted_files"] = processed
        item["file_count"]      = len(processed)
        self.logs.append({"entry": entry.id(), "step": "zip_extract",
                          "status": "ok", "file_count": len(processed)})
        return item

    def _process_github_repo(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {"extracted_files": [], "base_markdown": None,
                                    "clone_error": None}
        url    = entry.source_path
        branch = entry.tags.strip() or "main"
        slug   = entry.id()
        clone_dir = self.root_dir / "raw" / "repos" / slug / branch
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        ensure_dir(clone_dir.parent)

        cmd = ["git", "clone", "--depth", "1", "--branch", branch,
               "--single-branch", url, str(clone_dir)]
        try:
            proc = subprocess.run(cmd, check=False, capture_output=True,
                                  text=True, timeout=120)
        except FileNotFoundError:
            err = "git não encontrado no PATH."
            item["clone_error"] = err
            self.logs.append({"entry": slug, "step": "github_clone",
                              "status": "error", "error": err})
            return item

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "git clone falhou")[-2000:]
            item["clone_error"] = err
            self.logs.append({"entry": slug, "step": "github_clone",
                              "status": "error", "error": err})
            return item

        category  = "codigo-aluno" if branch.lower() in STUDENT_BRANCHES \
                    else "codigo-professor"
        processed = []
        for code_path in sorted(clone_dir.rglob("*")):
            if not code_path.is_file():
                continue
            parts = code_path.relative_to(clone_dir).parts
            if any(p.startswith(".") or p in {
                "__pycache__", "node_modules", "dist", "build", ".git"
            } for p in parts):
                continue
            if code_path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if code_path.stat().st_size > 500_000:
                continue

            relative_name = str(code_path.relative_to(clone_dir))
            sub_entry = FileEntry(
                source_path=str(code_path), file_type="code",
                category=category, title=relative_name,
                tags=entry.tags, notes=f"Branch: {branch} — {url}",
                professor_signal=entry.professor_signal,
                include_in_bundle=entry.include_in_bundle,
            )
            code_subdir  = "student" if category == "codigo-aluno" else "professor"
            safe_name_c  = f"{sub_entry.id()}{code_path.suffix.lower()}"
            raw_target_c = self.root_dir / "raw" / "code" / code_subdir / safe_name_c
            ensure_dir(raw_target_c.parent)
            shutil.copy2(code_path, raw_target_c)

            sub_result = self._process_code(sub_entry, raw_target_c)
            sub_result["title"]  = relative_name
            sub_result["branch"] = branch
            processed.append(sub_result)

        item["extracted_files"] = processed
        item["file_count"]      = len(processed)
        item["category"]        = category
        self.logs.append({"entry": slug, "step": "github_clone",
                          "status": "ok", "file_count": len(processed)})
        return item

    def _profile_pdf(self, pdf_path: Path, entry: FileEntry) -> DocumentProfileReport:
        report = DocumentProfileReport()
        if not HAS_PYMUPDF:
            report.suggested_profile = normalize_document_profile(entry.document_profile)
            report.notes.append("PyMuPDF não disponível; perfil automático limitado.")
            return report
        doc = pymupdf.open(str(pdf_path))
        try:
            pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
            pages = [p for p in pages if 0 <= p < doc.page_count]
            report.page_count = len(pages)
            total_text = 0
            total_images = 0
            table_candidates = 0
            low_text_pages = 0
            for page_num in pages:
                page = doc[page_num]
                text = page.get_text("text") or ""
                total_text += len(text.strip())
                images = page.get_images(full=True) or []
                total_images += len(images)
                try:
                    tables = page.find_tables()
                    table_candidates += len(getattr(tables, "tables", []) or [])
                except Exception:
                    pass
                if len(text.strip()) < 60 and len(images) > 0:
                    low_text_pages += 1
            report.text_chars = total_text
            report.images_count = total_images
            report.table_candidates = table_candidates
            report.text_density = round(total_text / max(report.page_count, 1), 2)
            report.suspected_scan = (low_text_pages / max(report.page_count, 1)) >= 0.5 and total_images > 0
        finally:
            doc.close()
        if entry.document_profile != "auto":
            report.suggested_profile = normalize_document_profile(entry.document_profile)
            report.notes.append("Perfil definido manualmente pelo usuário.")
            return report
        name_hint = f"{entry.title} {entry.tags} {entry.notes}".lower()
        if report.suspected_scan:
            report.suggested_profile = "scanned"
            report.notes.append("Muitas páginas com pouco texto e imagens presentes: provável scan.")
        elif entry.category == "provas" or "prova" in name_hint or "questão" in name_hint or "questao" in name_hint:
            report.suggested_profile = "diagram_heavy"
            report.notes.append("Detectado como material de prova/exame.")
        elif entry.formula_priority or re.search(r"\b(latex|equação|equation|fórmula|teorema|prova formal|indução)\b", name_hint):
            report.suggested_profile = "math_heavy"
            report.notes.append("Sinais de conteúdo matemático/formal.")
        elif report.table_candidates >= 2 or report.images_count >= max(3, report.page_count):
            report.suggested_profile = "diagram_heavy"
            report.notes.append("Layout com tabelas/imagens relevantes.")
        else:
            report.suggested_profile = "auto"
            report.notes.append("Documento geral detectado.")
        return report

    def _log_backend_result(self, entry_id: str, result: BackendRunResult) -> None:
        payload = {
            "entry": entry_id, "step": result.name, "layer": result.layer,
            "status": result.status, "markdown_path": result.markdown_path,
            "asset_dir": result.asset_dir, "metadata_path": result.metadata_path,
            "notes": result.notes,
        }
        if result.command:
            payload["command"] = result.command
        if result.error:
            payload["error"] = result.error
        self.logs.append(payload)

    # Minimum thresholds to skip noise images (tiny icons, solid-color rects, etc.)
    _MIN_IMG_BYTES = 2000     # < 2 KB is almost always an artifact
    _MIN_IMG_DIMENSION = 20   # width or height < 20px
    _MAX_ASPECT_RATIO = 8.0   # extreme aspect ratios are banners/bars (e.g. 1500x74)
    _MAX_NOISE_COLORS = 4     # images with ≤4 unique colors are decorative

    @staticmethod
    def _is_noise_image(data: bytes) -> bool:
        """Return True if image is noise: solid color, near-solid, or extreme aspect ratio."""
        try:
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(data))
            w, h = img.size

            # Extreme aspect ratio — banners, header/footer bars
            if w > 0 and h > 0:
                ratio = max(w / h, h / w)
                if ratio > RepoBuilder._MAX_ASPECT_RATIO:
                    return True

            # Very few unique colors — solid or near-solid (decorative elements)
            colors = img.getcolors(maxcolors=RepoBuilder._MAX_NOISE_COLORS + 1)
            if colors is not None and len(colors) <= RepoBuilder._MAX_NOISE_COLORS:
                return True

            return False
        except Exception:
            return False

    @staticmethod
    def _should_keep_extracted_pdf_image(
        *,
        data: bytes,
        width: int,
        height: int,
        policy: Dict[str, object],
    ) -> bool:
        if len(data) < int(policy["min_bytes"]):
            return False
        if width < int(policy["min_dimension"]) or height < int(policy["min_dimension"]):
            return False

        ratio = max(width / max(height, 1), height / max(width, 1))
        if ratio > float(policy["max_aspect_ratio"]):
            return False

        if policy.get("keep_low_color"):
            return True
        return not RepoBuilder._is_noise_image(data)

    @property
    def _image_format(self) -> str:
        """Return the configured image format ('png' or 'jpeg')."""
        fmt = self.options.get("image_format", "png")
        return fmt if fmt in ("png", "jpeg") else "png"

    def _convert_image_format(self, src: Path) -> Path:
        """Convert image at *src* to the configured format. Returns new path (or src if already correct)."""
        target_ext = f".{self._image_format}" if self._image_format != "jpeg" else ".jpg"
        if src.suffix.lower() in (target_ext, ".jpeg" if target_ext == ".jpg" else ""):
            return src
        try:
            from PIL import Image as PILImage
            img = PILImage.open(src)
            if self._image_format == "jpeg" and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            new_path = src.with_suffix(target_ext)
            save_kwargs = {"quality": 90} if self._image_format == "jpeg" else {}
            img.save(new_path, **save_kwargs)
            if new_path != src:
                src.unlink(missing_ok=True)
            return new_path
        except Exception:
            return src

    def _extract_pdf_images(
        self,
        pdf_path: Path,
        out_dir: Path,
        pages: Optional[List[int]] = None,
        ctx: Optional[BackendContext] = None,
    ) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        policy = _pdf_image_extraction_policy(ctx) if ctx is not None else {
            "mode": "standard",
            "min_bytes": self._MIN_IMG_BYTES,
            "min_dimension": self._MIN_IMG_DIMENSION,
            "max_aspect_ratio": self._MAX_ASPECT_RATIO,
            "keep_low_color": False,
        }
        seen_xrefs: set = set()  # deduplicate images that appear on multiple pages
        try:
            target_pages = pages or list(range(doc.page_count))
            count = 0
            for page_num in target_pages:
                if not (0 <= page_num < doc.page_count):
                    continue
                page = doc[page_num]
                for img_idx, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)

                    image = doc.extract_image(xref)
                    if not image or "image" not in image:
                        continue

                    data = image["image"]
                    w = image.get("width", 0)
                    h = image.get("height", 0)

                    if not self._should_keep_extracted_pdf_image(
                        data=data,
                        width=w,
                        height=h,
                        policy=policy,
                    ):
                        continue

                    ext = image.get("ext", "png")
                    fname = out_dir / f"page-{page_num + 1:03d}-img-{img_idx:02d}.{ext}"
                    fname.write_bytes(data)
                    # Conversão de formato acontece na consolidação final
                    count += 1
            return count
        finally:
            doc.close()

    def _extract_tables_pdfplumber(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        count = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            selected = pages or list(range(len(pdf.pages)))
            for page_num in selected:
                if not (0 <= page_num < len(pdf.pages)):
                    continue
                page = pdf.pages[page_num]
                tables = page.extract_tables() or []
                for table_idx, table in enumerate(tables, start=1):
                    normalized = [
                        [("" if cell is None else str(cell).strip()) for cell in row]
                        for row in table if row and any(cell not in (None, "", " ") for cell in row)
                    ]
                    if not normalized:
                        continue
                    csv_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.csv"
                    ensure_dir(csv_path.parent)
                    with csv_path.open("w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(normalized)
                    md_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.md"
                    write_text(md_path, rows_to_markdown_table(normalized))
                    count += 1
        return count

    def _detect_tables_pymupdf(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        try:
            selected = pages or list(range(doc.page_count))
            count = 0
            for page_num in selected:
                if not (0 <= page_num < doc.page_count):
                    continue
                page = doc[page_num]
                try:
                    tables = page.find_tables()
                    found = getattr(tables, "tables", []) or []
                    if not found:
                        continue
                    serializable = []
                    for idx, tbl in enumerate(found, start=1):
                        bbox = getattr(tbl, "bbox", None)
                        rows = []
                        try:
                            extracted = tbl.extract() or []
                            rows = [["" if cell is None else str(cell) for cell in row] for row in extracted]
                        except Exception:
                            pass
                        serializable.append({"table_index": idx, "bbox": list(bbox) if bbox else None, "rows": rows})
                    meta_path = out_dir / f"page-{page_num + 1:03d}.json"
                    write_text(meta_path, json.dumps(serializable, indent=2, ensure_ascii=False))
                    count += len(serializable)
                except Exception:
                    continue
            return count
        finally:
            doc.close()

    def _compact_manifest(self, manifest: dict) -> dict:
        entries = manifest.get("entries", []) or []
        live_entries = _filter_live_manifest_entries(self.root_dir, entries)
        removed = len(entries) - len(live_entries)
        if removed > 0:
            logger.info("Removidas %d entries órfãs do manifest antes de regenerar artefatos.", removed)
        manifest["entries"] = live_entries
        manifest = self._heal_manifest_markdown_paths(manifest)

        logs = manifest.get("logs", [])
        if isinstance(logs, list) and len(logs) > _MANIFEST_LOG_LIMIT:
            manifest["logs"] = logs[-_MANIFEST_LOG_LIMIT:]
        return manifest

    def incremental_build(self) -> None:
        with self._sleep_guard("build incremental do repositorio"):
            self._incremental_build_impl()

    def _incremental_build_impl(self) -> None:
        """Adiciona novos arquivos a um repositório existente sem recriar do zero."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.info("No existing manifest found, falling back to full build.")
            self.build()
            return

        logger.info("Incremental build at %s", self.root_dir)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest = self._compact_manifest(manifest)

        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        new_entries = [e for e in self.entries
                       if e.source_path not in existing_sources and getattr(e, "enabled", True)]

        if not new_entries:
            logger.info("No new entries to process — regenerating pedagogical files only.")
        else:
            logger.info("Processing %d new entries (skipping %d existing).",
                         len(new_entries), len(self.entries) - len(new_entries))

            self._create_structure()

            total = len(new_entries)
            for i, entry in enumerate(new_entries):
                logger.info("[%d/%d] Processing: %s (%s)", i + 1, total, entry.title, entry.file_type)
                if self.progress_callback:
                    self.progress_callback(i, total, entry.title)
                item_result = self._process_entry(entry)
                manifest["entries"].append(item_result)
                # Salva manifest após cada entry para não perder progresso
                manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
                manifest.setdefault("logs", []).extend(self.logs)
                self.logs = []
                manifest = self._compact_manifest(manifest)
                write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
                logger.info("[%d/%d] Concluído e salvo: %s", i + 1, total, entry.title)
            if self.progress_callback:
                self.progress_callback(total, total, "")

        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)
        manifest = self._compact_manifest(manifest)

        # Regenera todos os arquivos pedagógicos (indexes, course map, glossary, etc.)
        # Nota: _regenerate_pedagogical_files já escreve STUDENT_PROFILE.md
        self._regenerate_pedagogical_files(manifest)

        # Atualiza ou cria student state / progress schema
        state_path = self.root_dir / "student" / "STUDENT_STATE.md"
        if state_path.exists():
            content = state_path.read_text(encoding="utf-8")
            today = datetime.now().strftime('%Y-%m-%d')
            content = re.sub(r"^updated:.*$", f"updated: {today}",
                             content, flags=re.MULTILINE)
            state_path.write_text(content, encoding="utf-8")
        else:
            write_text(state_path,
                       student_state_md(self.course_meta, self.student_profile))
        progress_path = self.root_dir / "build" / "PROGRESS_SCHEMA.md"
        if not progress_path.exists():
            write_text(progress_path, progress_schema_md())

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Incremental build completed. %d new entries added.", len(new_entries))

    def _derive_active_unit_slug_from_state(self) -> str:
        state = self.root_dir / "student" / "STUDENT_STATE.md"
        if not state.exists():
            return ""
        text = state.read_text(encoding="utf-8")
        m = re.search(r"active:\s*\n(?:.*\n)*?\s*unit:\s*(\S+)", text)
        return m.group(1).strip() if m else ""

    def _regenerate_pedagogical_files(self, manifest: dict) -> None:
        """Regenera todos os arquivos pedagógicos a partir do manifest atual.

        Chamado por process_single() e pode ser reutilizado em outros contextos.
        Garante que COURSE_MAP, GLOSSARY, indexes e system prompt estejam
        sincronizados com o conjunto atual de entries.
        """
        # Limpa arquivos internos que foram movidos para build/ em versões anteriores
        _stale_files = [
            self.root_dir / "system" / "PDF_CURATION_GUIDE.md",
            self.root_dir / "system" / "BACKEND_ARCHITECTURE.md",
            self.root_dir / "system" / "BACKEND_POLICY.yaml",
            self.root_dir / "student" / "PROGRESS_SCHEMA.md",
        ]
        for stale in _stale_files:
            if stale.exists():
                try:
                    stale.unlink()
                    logger.info("Removido arquivo obsoleto: %s", stale)
                except Exception as e:
                    logger.warning("Falha ao remover %s: %s", stale, e)

        live_manifest_entries = _filter_live_manifest_entries(self.root_dir, manifest.get("entries", []))
        manifest["entries"] = live_manifest_entries
        runtime_course_meta = {**self.course_meta, "_repo_root": self.root_dir}
        content_taxonomy = _build_file_map_content_taxonomy_from_course(
            runtime_course_meta,
            self.subject_profile,
            live_manifest_entries,
        )
        runtime_course_meta["_content_taxonomy"] = content_taxonomy
        _write_internal_content_taxonomy(self.root_dir, content_taxonomy)

        timeline_context = _build_file_map_timeline_context_from_course(
            runtime_course_meta,
            self.subject_profile,
            content_taxonomy=content_taxonomy,
        )
        runtime_course_meta["_timeline_context"] = timeline_context
        enriched_timeline_index = _persist_enriched_timeline_index(
            timeline_context.get("timeline_index", _empty_timeline_index()),
        )
        write_text(
            self.root_dir / "course" / ".timeline_index.json",
            json.dumps(enriched_timeline_index, indent=2, ensure_ascii=False),
        )
        assessment_context = _build_assessment_context_from_course(
            runtime_course_meta,
            self.subject_profile,
            timeline_context=timeline_context,
        )
        runtime_course_meta["_assessment_context"] = assessment_context
        _write_internal_assessment_context(self.root_dir, assessment_context)

        # System prompt (with conditional file references)
        _common_flags = dict(
            has_assignments=any((e.get("category") in ASSIGNMENT_CATEGORIES) for e in live_manifest_entries),
            has_code=any((e.get("category") in CODE_CATEGORIES) for e in live_manifest_entries),
            has_whiteboard=any((e.get("category") in WHITEBOARD_CATEGORIES) for e in live_manifest_entries),
        )
        write_text(self.root_dir / "setup" / "INSTRUCOES_CLAUDE_PROJETO.md",
                   generate_claude_project_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "setup" / "INSTRUCOES_GPT_PROJETO.md",
                   generate_gpt_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "setup" / "INSTRUCOES_GEMINI_PROJETO.md",
                   generate_gemini_instructions(
                       self.course_meta, self.student_profile, self.subject_profile,
                       **_common_flags))
        write_text(self.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "system" / "PEDAGOGY.md", pedagogy_md())
        write_text(self.root_dir / "system" / "MODES.md", modes_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "README.md", root_readme(self.course_meta))
        write_text(self.root_dir / ".gitignore", _generated_repo_gitignore_text())

        # Course map (com timeline cronograma × unidades)
        course_map_text = course_map_md(runtime_course_meta, self.subject_profile)
        write_text(self.root_dir / "course" / "COURSE_MAP.md", course_map_text)

        # Glossary
        glossary_text = glossary_md(
            self.course_meta,
            self.subject_profile,
            root_dir=self.root_dir,
            manifest_entries=live_manifest_entries,
        )
        write_text(self.root_dir / "course" / "GLOSSARY.md", glossary_text)

        # Controlled auto-tagging infrastructure
        tag_catalog = _write_tag_catalog(
            self.root_dir,
            self.subject_profile,
            live_manifest_entries,
            course_map_text=course_map_text,
            glossary_text=glossary_text,
        )
        live_manifest_entries = _refresh_manifest_auto_tags(self.root_dir, live_manifest_entries, tag_catalog)
        manifest["entries"] = live_manifest_entries

        try:
            all_entries = [FileEntry.from_dict(e) for e in live_manifest_entries]
        except Exception:
            all_entries = []

        # Syllabus
        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        # Exam index
        exam_entries = [e for e in all_entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))

        # Exercise index
        exercise_entries = [e for e in all_entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # Bibliography
        bib_entries = [e for e in all_entries if e.category == "bibliografia"]
        if bib_entries or getattr(self.subject_profile, "teaching_plan", ""):
            write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                       bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # Assignment index
        assignment_entries = [e for e in all_entries if e.category in ASSIGNMENT_CATEGORIES]
        if assignment_entries:
            write_text(self.root_dir / "assignments" / "ASSIGNMENT_INDEX.md",
                       assignment_index_md(self.course_meta, assignment_entries))

        # Code index
        code_entries = [e for e in all_entries if e.category in CODE_CATEGORIES]
        if code_entries:
            write_text(self.root_dir / "code" / "CODE_INDEX.md",
                       code_index_md(self.course_meta, code_entries, self.subject_profile))

        # Whiteboard index
        wb_entries = [e for e in all_entries if e.category in WHITEBOARD_CATEGORIES]
        if wb_entries:
            write_text(self.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md",
                       whiteboard_index_md(self.course_meta, wb_entries))

        # FILE_MAP
        write_text(self.root_dir / "course" / "FILE_MAP.md",
                   file_map_md(
                       runtime_course_meta,
                       live_manifest_entries,
                       self.subject_profile,
                   ))

        # Student files
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))
        state_path = self.root_dir / "student" / "STUDENT_STATE.md"
        if not state_path.exists():
            write_text(state_path, student_state_md(self.course_meta, self.student_profile))
        progress_path = self.root_dir / "build" / "PROGRESS_SCHEMA.md"
        if not progress_path.exists():
            write_text(progress_path, progress_schema_md())

        active_unit = self._derive_active_unit_slug_from_state()
        if active_unit:
            teaching_plan = getattr(self.subject_profile, "teaching_plan", "") or ""
            parsed_units = _parse_units_from_teaching_plan(teaching_plan)
            course_topics_by_unit = {
                slugify(title): [(slugify(_topic_text(t)), _topic_text(t)) for t in topics]
                for title, topics in parsed_units
            }
            topics = course_topics_by_unit.get(active_unit, [])
            if topics:
                try:
                    student_state_v2.refresh_active_unit_progress(
                        root_dir=self.root_dir,
                        active_unit_slug=active_unit,
                        course_map_topics=topics,
                    )
                except Exception as exc:
                    logger.warning("refresh_active_unit_progress falhou: %s", exc)

        # Resolve image references in markdowns → content/images/
        self._resolve_content_images()
        self._inject_all_image_descriptions()
        content_dir = self.root_dir / "content"
        if content_dir.exists():
            for md in content_dir.rglob("*.md"):
                if md.name.endswith("_INDEX.md"):
                    continue
                if md.name in {"BIBLIOGRAPHY.md", "FILE_MAP.md", "COURSE_MAP.md"}:
                    continue
                try:
                    _inject_executive_summary(md)
                except Exception as exc:
                    logger.warning("Falha ao atualizar sumário executivo de %s: %s", md, exc)

    def process_single(self, entry: "FileEntry", force: bool = False) -> str:
        with self._sleep_guard(f"processamento de {entry.title}"):
            return self._process_single_impl(entry, force=force)

    def _process_single_impl(self, entry: "FileEntry", force: bool = False) -> str:
        """
        Processa um único FileEntry e adiciona ao repositório existente.
        Chamado pelo botão '⚡ Processar' da UI para processar item a item.
        Se o repositório ainda não existir, cria a estrutura primeiro.

        Returns:
            "ok" — processado com sucesso
            "already_exists" — já existia no manifest (quando force=False)
        """
        manifest_path = self.root_dir / "manifest.json"

        # Garante estrutura mínima existente
        self._create_structure()

        # Carrega ou inicializa manifest
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest = self._compact_manifest(manifest)
        else:
            # Primeiro item — cria manifest + arquivos raiz
            self._write_root_files()
            manifest = {
                "app": APP_NAME,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "course": self.course_meta,
                "options": self.options,
                "environment": {
                    "python": sys.version.split()[0],
                    "pymupdf": HAS_PYMUPDF,
                    "pymupdf4llm": HAS_PYMUPDF4LLM,
                    "pdfplumber": HAS_PDFPLUMBER,
                    "datalab_api": has_datalab_api_key(),
                    "docling_cli": bool(DOCLING_CLI),
                    "docling_python": has_docling_python_api(),
                    "marker_cli": bool(MARKER_CLI),
                },
                "entries": [],
                "logs": [],
            }

        # Verifica duplicata por source_path
        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        if entry.source_path in existing_sources:
            if not force:
                logger.info("Entry already processed: %s", entry.source_path)
                return "already_exists"
            # force=True: remove a entrada antiga antes de reprocessar
            old_id = entry.id()
            logger.info("Reprocessing (force): removing old entry %s", old_id)
            self.unprocess(old_id)
            # Reload manifest after unprocess
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        logger.info("Processing single entry: %s (%s)", entry.title, entry.file_type)
        item_result = self._process_entry(entry)
        # TODO(token-optimization): adicionar etapa de limpeza pós-extração
        # para remover ruído do pymupdf4llm (cabeçalhos repetidos, rodapés,
        # numeração de página, linhas em branco excessivas).
        # Estimativa: redução de ~25% no tamanho dos arquivos de content/.
        manifest["entries"].append(item_result)
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)
        self.logs = []  # reset para próxima chamada
        manifest = self._compact_manifest(manifest)

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

        # Regenera arquivos pedagógicos que dependem do conjunto completo de entries
        self._regenerate_pedagogical_files(manifest)
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

        logger.info("Single entry processed: %s", entry.id())
        return "ok"

    def unprocess(self, entry_id: str) -> bool:
        """
        Remove todos os arquivos gerados para um entry_id e o retira do manifest.
        Chamado pelo botão '🗑 Limpar Processamento' da UI.
        Retorna True se removeu com sucesso, False caso contrário.
        """
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("No manifest found at %s", manifest_path)
            return False

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.course_meta = self._effective_course_meta(manifest)

        target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
        if not target:
            logger.warning("Entry not found in manifest: %s", entry_id)
            return False

        paths_to_remove: List[str] = []
        for key in ["raw_target", "base_markdown", "advanced_markdown", "advanced_markdown_raw", "manual_review",
                    "images_dir", "tables_dir", "table_detection_dir",
                    "advanced_asset_dir", "advanced_metadata_path",
                    "approved_markdown", "curated_markdown", "rendered_pages_dir"]:
            val = target.get(key)
            if val:
                paths_to_remove.append(val)

        removed_count = 0
        for rel_path in paths_to_remove:
            full = self.root_dir / rel_path
            try:
                if full.is_dir():
                    shutil.rmtree(full)
                    removed_count += 1
                elif full.is_file():
                    full.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning("Could not remove %s: %s", full, e)

        removed_count += self._remove_entry_consolidated_images(entry_id)

        manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest = self._compact_manifest(manifest)

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)

        # Re-resolve content/images/ — clears stale images from removed entry
        self._resolve_content_images()

        logger.info("Unprocessed entry %s (%d files removed)", entry_id, removed_count)
        return True

    def reject(self, entry_id: str) -> Optional[Dict[str, object]]:
        """
        Reprova um entry: remove arquivos gerados mas preserva o raw PDF.
        Retorna os dados do manifest entry (para reconstruir FileEntry na fila)
        ou None se não encontrou.
        """
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("reject: manifest não encontrado em %s", manifest_path)
            return None

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
        if not target:
            logger.warning("reject: entry %s não encontrada no manifest", entry_id)
            return None

        # Preservar dados para reconstruir FileEntry
        entry_data = dict(target)

        # Remover apenas arquivos gerados (NÃO raw_target)
        keys_to_clean = [
            "base_markdown", "advanced_markdown", "advanced_markdown_raw", "manual_review",
            "images_dir", "tables_dir", "table_detection_dir",
            "advanced_asset_dir", "advanced_metadata_path",
            "approved_markdown", "curated_markdown",
            "rendered_pages_dir",
        ]
        removed_count = 0
        for key in keys_to_clean:
            val = target.get(key)
            if not val:
                continue
            full = self.root_dir / val
            try:
                if full.is_dir():
                    shutil.rmtree(full)
                    removed_count += 1
                elif full.is_file():
                    full.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning("reject: não foi possível remover %s: %s", full, e)

        removed_count += self._remove_entry_consolidated_images(entry_id)

        # Remover entry do manifest
        manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).append({
            "entry": entry_id,
            "step": "curator_reject",
            "status": "ok",
        })
        manifest = self._compact_manifest(manifest)

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)

        # Re-resolve content/images/ — limpa imagens órfãs
        self._resolve_content_images()

        logger.info("Rejected entry %s (%d files removed, raw preserved)", entry_id, removed_count)
        return entry_data


# ---------------------------------------------------------------------------
# Free functions — Pedagogical file generators
# ---------------------------------------------------------------------------

_TEACHING_PLAN_SECTION_STOP = re.compile(
    r'^(?:PROCEDIMENTOS|AVALIA[ÇC][AÃ]O|BIBLIOGRAFIA|METODOLOGIA)',
    re.IGNORECASE,
)

_TEACHING_PLAN_ASSESSMENT_START = re.compile(r'^(?:AVALIA[ÇC][AÃ]O|AVALIACAO)\b', re.IGNORECASE)
_TEACHING_PLAN_ASSESSMENT_STOP = re.compile(
    r'^(?:PROCEDIMENTOS|BIBLIOGRAFIA|METODOLOGIA)',
    re.IGNORECASE,
)
_ASSESSMENT_LINE_RE = re.compile(
    r'^(?P<label>(?:p\s*\d+|pf|prova\s+final|exame(?:\s+final)?))\b'
    r'(?:\s*[:\-–—]\s*|\s+)?(?P<desc>.*)$',
    re.IGNORECASE,
)


def _normalize_teaching_plan_heading(line: str) -> str:
    """Normalize markdown-heavy headings before parser checks."""
    normalized = (line or "").strip()
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = normalized.replace("*", "").strip()
    return normalized

def _parse_units_from_teaching_plan(text: str):
    """
    Extrai (título_da_unidade, [tópicos]) do texto livre do plano de ensino.

    Suporta dois formatos:
      Formato PUCRS:  "N°. DA UNIDADE: N" seguido de "CONTEÚDO: Título"
                      Tópicos numerados como "1.1.", "1.2.1." etc.
      Formato genérico: "Unidade N – Título" / "UNIDADE N: Título"
                        Tópicos com marcadores (-, •, *) ou numerados (1.1)

    Para quando encontra seções pós-conteúdo (PROCEDIMENTOS, AVALIAÇÃO, BIBLIOGRAFIA).

    Cada tópico é uma tupla (texto, depth):
      - depth 0 → tópico principal (1.1., 1.2.)
      - depth 1 → sub-tópico (1.2.1., 1.2.2.)
      - depth 2+ → sub-sub-tópico (1.2.1.1.)
      - marcadores (-, •) → depth 0

    Retorna lista de (str, List[tuple[str, int]]).

    Para compatibilidade, tópicos como strings simples ainda funcionam
    nos consumidores que fazem ``for t in topics`` — eles verão tuplas.
    """
    units: list = []
    current_title: Optional[str] = None
    current_unit_num: Optional[str] = None
    current_topics: list = []
    current_style: Optional[str] = None

    pucrs_unit_re = re.compile(r'N[°º]?\.\s*DA\s+UNIDADE\s*:\s*(\d+)', re.IGNORECASE)
    pucrs_content_re = re.compile(r'CONTE[ÚU]DO\s*:\s*(.+)', re.IGNORECASE)
    generic_unit_re = re.compile(
        r'^(?:#{0,4}\s*)?(unidade(?:\s+de\s+aprendizagem)?\s+(?:\d+|[ivxlcdm]+))\s*[-–:—]\s*(.+)',
        re.IGNORECASE,
    )
    numbered_topic_re = re.compile(r'^(\d+\.\d+(?:\.\d+)*)\.\s+(.+)')
    bullet_topic_re = re.compile(r'^[-•*]\s+(.+)')

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized_line = _normalize_teaching_plan_heading(line)
        if _TEACHING_PLAN_SECTION_STOP.match(normalized_line):
            break

        # PUCRS: "N°. DA UNIDADE: N"
        m = pucrs_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_unit_num = m.group(1)
            current_title = None
            current_topics = []
            current_style = "pucrs"
            continue

        # PUCRS: "CONTEÚDO: Título" — título da unidade atual
        if current_unit_num is not None and current_title is None:
            m = pucrs_content_re.match(line)
            if m:
                current_title = f"Unidade {current_unit_num} — {m.group(1).strip()}"
                continue

        # Genérico: "Unidade N – Título" ou "### Unidade N – Título"
        m = generic_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_title = f"{m.group(1).strip()} — {m.group(2).strip()}"
            current_unit_num = None
            current_topics = []
            current_style = "learning_unit" if "aprendizagem" in m.group(1).lower() else "generic"
            continue

        # Tópicos numerados (1.1., 1.2.1.) ou com marcador (-, •)
        if current_title is not None:
            m = numbered_topic_re.match(line)
            if m:
                numbering = m.group(1)  # e.g. "1.2.1"
                # depth = number of dots minus 1 (1.1 → 0, 1.2.1 → 1, 1.2.1.1 → 2)
                depth = numbering.count(".") - 1
                current_topics.append((m.group(2).strip(), max(depth, 0)))
                continue
            m = bullet_topic_re.match(line)
            if m:
                current_topics.append((m.group(1).strip(), 0))
                continue
            if current_style == "learning_unit" and not normalized_line.endswith(":"):
                current_topics.append((line, 0))

    if current_title is not None:
        units.append((current_title, current_topics))

    return units


def _topic_text(topic) -> str:
    """Extrai o texto de um tópico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[0]
    return str(topic)


def _topic_depth(topic) -> int:
    """Extrai a profundidade de um tópico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[1]
    return 0


def _match_timeline_to_units(
    timeline: List[Dict[str, str]],
    units: list,
) -> List[Dict[str, str]]:
    """
    Cruza linhas do cronograma com unidades do plano de ensino.

    Para cada unidade, tenta encontrar a(s) linha(s) do cronograma que
    mencionam o título ou número da unidade. Retorna lista de dicts:
        [{"unit_title": str, "unit_slug": str, "period": str, "dates": str}, ...]

    O matching usa heurísticas:
      - Busca "unidade N", "unid N", "un N" no texto do conteúdo
      - Busca o título da unidade (ou parte dele) no conteúdo
      - Usa overlap semântico leve do nome da unidade
    """
    if not timeline or not units:
        return []

    content_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["conteúdo", "conteudo", "assunto", "tema", "descrição",
                                  "descricao", "atividade", "tópico", "topico", "content"]):
            content_keys.append(key)
    if not content_keys:
        avg_lens = {}
        for key in timeline[0].keys():
            avg_lens[key] = sum(len(row.get(key, "")) for row in timeline) / max(len(timeline), 1)
        if avg_lens:
            content_keys = [max(avg_lens, key=avg_lens.get)]

    preferred_date_keys = []
    fallback_date_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["data", "date"]):
            preferred_date_keys.append(key)
        elif any(k in key for k in ["semana", "week", "sem", "aula"]):
            fallback_date_keys.append(key)
    date_keys = preferred_date_keys or fallback_date_keys
    if not date_keys:
        date_keys = [list(timeline[0].keys())[0]] if timeline[0] else []

    def _normalize_token_text(text: str) -> str:
        text = unicodedata.normalize("NFKD", text or "")
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    generic_tokens = {
        "unidade", "introducao", "introdução", "fundamentos", "softwares", "suporte",
        "formal", "formais", "verificacao", "verificação", "programas", "programa",
        "modelos", "modelo", "logica", "lógica", "temporal", "sistemas", "sistema",
    }

    result = []
    for unit_title, topics in units:
        unit_num_match = re.search(r"(\d+)", unit_title)
        unit_num = unit_num_match.group(1) if unit_num_match else ""
        unit_num_int = str(int(unit_num)) if unit_num else ""

        desc_match = re.search(r"[—–\-:]\s*(.+)", unit_title)
        unit_desc = desc_match.group(1).strip() if desc_match else ""
        unit_desc_norm = _normalize_token_text(unit_desc)
        desc_words = [w for w in unit_desc_norm.split() if len(w) > 3][:4]
        topic_phrases = []
        topic_keywords = set()
        for topic in topics or []:
            topic_text = _topic_text(topic)
            topic_norm = _normalize_token_text(topic_text)
            if not topic_norm:
                continue
            topic_phrases.append(topic_norm)
            for token in topic_norm.split():
                if len(token) >= 5 and token not in generic_tokens:
                    topic_keywords.add(token)

        matched_dates = []
        for row in timeline:
            content = " ".join(row.get(k, "") for k in content_keys)
            content_norm = _normalize_token_text(content)
            if not content_norm:
                continue

            matched = False
            if unit_num:
                patterns = [
                    rf"\bunidade\s*{unit_num}\b",
                    rf"\bunidade\s*{unit_num_int}\b",
                    rf"\bunid\.?\s*{unit_num_int}\b",
                    rf"\bun\.?\s*{unit_num_int}\b",
                ]
                for pat in patterns:
                    if re.search(pat, content_norm, re.IGNORECASE):
                        matched = True
                        break

            if not matched and desc_words:
                if unit_desc_norm and unit_desc_norm in content_norm:
                    matched = True
                else:
                    matches = sum(1 for w in desc_words if re.search(rf"\b{re.escape(w)}\b", content_norm))
                    threshold = 1 if len(desc_words) == 1 else 2
                    if matches >= threshold:
                        matched = True

            if not matched and topic_phrases:
                for phrase in topic_phrases:
                    if phrase in content_norm:
                        matched = True
                        break

            if not matched and topic_keywords:
                keyword_hits = sum(1 for kw in topic_keywords if re.search(rf"\b{re.escape(kw)}\b", content_norm))
                if keyword_hits >= 1:
                    matched = True

            if matched:
                date_str = " / ".join(row.get(k, "") for k in date_keys if row.get(k, "")).strip()
                if date_str:
                    matched_dates.append(date_str)

        matched_dates = list(dict.fromkeys(matched_dates))
        if len(matched_dates) > 1:
            period = f"{matched_dates[0]} a {matched_dates[-1]}"
        else:
            period = matched_dates[0] if matched_dates else ""

        result.append({
            "unit_title": unit_title,
            "unit_slug": _normalize_unit_slug(unit_title),
            "period": period,
            "dates": ", ".join(matched_dates),
        })

    return result


def _match_timeline_to_units_generic(
    timeline: List[Dict[str, str]],
    units: list,
) -> List[Dict[str, str]]:
    """
    Versão genérica do matcher de timeline.

    Em vez de depender de nomes hardcoded, aprende sinais do próprio plano:
    títulos, tópicos e tokens distintivos por frequência. O matching também
    normaliza acentos para funcionar melhor em português.
    """
    if not timeline or not units:
        return []

    content_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["conteúdo", "conteudo", "assunto", "tema", "descrição",
                                  "descricao", "atividade", "tópico", "topico", "content"]):
            content_keys.append(key)
    if not content_keys:
        avg_lens = {}
        for key in timeline[0].keys():
            avg_lens[key] = sum(len(row.get(key, "")) for row in timeline) / max(len(timeline), 1)
        if avg_lens:
            content_keys = [max(avg_lens, key=avg_lens.get)]

    preferred_date_keys = []
    fallback_date_keys = []
    for key in timeline[0].keys():
        if any(k in key for k in ["data", "date"]):
            preferred_date_keys.append(key)
        elif any(k in key for k in ["semana", "week", "sem", "aula"]):
            fallback_date_keys.append(key)
    date_keys = preferred_date_keys or fallback_date_keys
    if not date_keys:
        date_keys = [list(timeline[0].keys())[0]] if timeline[0] else []

    def _normalize_token_text(text: str) -> str:
        text = unicodedata.normalize("NFKD", text or "")
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    def _tokenize_signal(text: str) -> List[str]:
        return [
            token
            for token in _normalize_token_text(text).split()
            if len(token) >= 4 and not token.isdigit()
        ]

    descriptors = []
    token_frequency: Dict[str, int] = {}
    for unit_title, topics in units:
        unit_num_match = re.search(r"(\d+)", unit_title)
        unit_num = unit_num_match.group(1) if unit_num_match else ""
        unit_num_int = str(int(unit_num)) if unit_num else ""

        desc_match = re.search(r"[—–\-:]\s*(.+)", unit_title)
        unit_desc = desc_match.group(1).strip() if desc_match else unit_title
        unit_desc_norm = _normalize_token_text(unit_desc)
        title_tokens = _tokenize_signal(unit_desc_norm)
        topic_phrases = []
        topic_tokens = []

        for topic in topics or []:
            topic_norm = _normalize_token_text(_topic_text(topic))
            if not topic_norm:
                continue
            topic_phrases.append(topic_norm)
            topic_tokens.extend(_tokenize_signal(topic_norm))

        all_tokens = title_tokens + topic_tokens
        descriptor = {
            "unit_title": unit_title,
            "unit_num": unit_num,
            "unit_num_int": unit_num_int,
            "unit_desc_norm": unit_desc_norm,
            "title_tokens": title_tokens,
            "topic_phrases": topic_phrases,
            "all_tokens": all_tokens,
        }
        descriptors.append(descriptor)
        for token in set(all_tokens):
            token_frequency[token] = token_frequency.get(token, 0) + 1

    for descriptor in descriptors:
        descriptor["distinctive_tokens"] = sorted({
            token
            for token in descriptor["all_tokens"]
            if token_frequency.get(token, 0) == 1 or (token_frequency.get(token, 0) <= 2 and len(token) >= 6)
        })

    row_dates = []
    for row in timeline:
        row_dates.append(" / ".join(row.get(k, "") for k in date_keys if row.get(k, "")).strip())

    anchor_indexes_by_unit = []
    for descriptor in descriptors:
        anchors = []
        for idx, row in enumerate(timeline):
            content_norm = _normalize_token_text(" ".join(row.get(k, "") for k in content_keys))
            if not content_norm:
                continue

            score = 0
            unit_num = descriptor["unit_num"]
            unit_num_int = descriptor["unit_num_int"]
            if unit_num:
                patterns = [
                    rf"\bunidade\s*{unit_num}\b",
                    rf"\bunidade\s*{unit_num_int}\b",
                    rf"\bunid\.?\s*{unit_num_int}\b",
                    rf"\bun\.?\s*{unit_num_int}\b",
                ]
                for pat in patterns:
                    if re.search(pat, content_norm, re.IGNORECASE):
                        score += 10
                        break

            unit_desc_norm = descriptor["unit_desc_norm"]
            if unit_desc_norm and unit_desc_norm in content_norm:
                score += 8

            title_hits = sum(
                1 for token in set(descriptor["title_tokens"])
                if re.search(rf"\b{re.escape(token)}\b", content_norm)
            )
            if title_hits >= max(1, min(2, len(set(descriptor["title_tokens"])))):
                score += 4

            for phrase in descriptor["topic_phrases"]:
                if phrase in content_norm:
                    score += 8
                    break

            distinct_hits = sum(
                1
                for token in descriptor["distinctive_tokens"]
                if re.search(rf"\b{re.escape(token)}\b", content_norm)
            )
            if distinct_hits:
                score += min(6, distinct_hits * 3)

            if score >= 4:
                anchors.append(idx)
        anchor_indexes_by_unit.append(anchors)

    result = []
    next_anchor_starts = [
        anchors[0] if anchors else None
        for anchors in anchor_indexes_by_unit
    ]

    for unit_idx, descriptor in enumerate(descriptors):
        anchors = anchor_indexes_by_unit[unit_idx]
        matched_dates = []
        if anchors:
            start_idx = anchors[0]
            next_start_idx = None
            for later_idx in range(unit_idx + 1, len(descriptors)):
                later_anchors = anchor_indexes_by_unit[later_idx]
                if later_anchors:
                    next_start_idx = later_anchors[0]
                    break
            end_idx = (next_start_idx - 1) if next_start_idx is not None else anchors[-1]
            if end_idx < start_idx:
                end_idx = anchors[-1]
            matched_dates = [d for d in row_dates[start_idx:end_idx + 1] if d]

        matched_dates = list(dict.fromkeys(matched_dates))
        period = f"{matched_dates[0]} a {matched_dates[-1]}" if len(matched_dates) > 1 else (matched_dates[0] if matched_dates else "")
        result.append({
            "unit_title": descriptor["unit_title"],
            "unit_slug": _normalize_unit_slug(descriptor["unit_title"]),
            "period": period,
            "dates": ", ".join(matched_dates),
        })

    return result


_match_timeline_to_units = _match_timeline_to_units_generic


def _score_text_against_row(source_text: str, row_tokens: List[str], *, weight: float = 1.0) -> float:
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


def _score_entry_against_timeline_row(signals: dict, row_text: str) -> float:
    row_norm = _normalize_match_text(row_text)
    if not row_norm:
        return 0.0

    row_tokens = [tok for tok in row_norm.split() if len(tok) >= 4]
    title_text = signals.get("title_text", "")
    markdown_text = signals.get("markdown_text", "")
    category_text = signals.get("category_text", "")
    tags_text = signals.get("tags_text", "")
    raw_text = signals.get("raw_text", "")
    entry_norm = " ".join(filter(None, [title_text, markdown_text, category_text, tags_text, raw_text]))
    is_exercise_entry = any(term in entry_norm for term in [
        "exercicio",
        "exercicios",
        "lista",
        "listas",
        "gabarito",
        "respostas",
    ])

    score = 0.0
    for source, weight in [
        (title_text, 1.25),
        (markdown_text, 1.0),
        (raw_text, 0.65),
        (tags_text, 0.35),
        (category_text, 0.2),
    ]:
        score += _score_text_against_row(source, row_tokens, weight=weight)
        if source and source in row_norm:
            score += min(1.5, max(0.35, len(source) / 18.0)) * weight

    if any(term in row_norm for term in ["exercicio", "exercicios", "lista", "listas", "gabarito", "respostas"]):
        score += 0.25
        if is_exercise_entry:
            score += 1.25
    elif is_exercise_entry:
        score -= 0.2
    if any(term in row_norm for term in ["atividade assincrona", "atividade assíncrona", "complementar os estudos", "leituras recomendadas"]):
        score += 0.15
    if is_exercise_entry and "estudo de caso" in row_norm:
        score += 0.35

    return score


def _score_card_evidence_against_entry(signals: dict, card_items: List[Dict[str, str]]) -> float:
    if not card_items:
        return 0.0

    entry_text = str(signals.get("combined_text", "") or "").strip()
    if not entry_text:
        entry_text = " ".join(
            filter(
                None,
                [
                    signals.get("title_text", ""),
                    signals.get("markdown_text", ""),
                    signals.get("category_text", ""),
                    signals.get("tags_text", ""),
                    signals.get("raw_text", ""),
                ],
            )
        )
    entry_norm = _normalize_match_text(entry_text)
    if not entry_norm:
        return 0.0

    entry_tokens = {tok for tok in entry_norm.split() if len(tok) >= 4}
    if not entry_tokens:
        return 0.0

    score = 0.0
    for item in card_items:
        normalized_title = _normalize_match_text(str(item.get("normalized_title", "") or ""))
        if not normalized_title:
            continue
        title_tokens = [tok for tok in normalized_title.split() if len(tok) >= 4]
        if not title_tokens:
            continue

        item_score = 0.0
        overlap = len(set(title_tokens) & entry_tokens)
        if normalized_title in entry_norm:
            item_score = 0.5
        elif overlap >= 2:
            item_score = 0.34
        elif overlap == 1:
            item_score = 0.16

        if not item_score:
            continue

        source_kind = str(item.get("source_kind", "") or "")
        if source_kind == "topic-title":
            item_score += 0.05
        elif source_kind == "card-title":
            item_score += 0.03

        score += item_score

    return min(0.7, score)


def _timeline_block_rows_for_scoring(block: Dict[str, object]) -> list:
    rows = list(block.get("rows", []) or [])
    return [row for row in rows if not bool(row.get("ignored"))]


def _score_timeline_block(signals: dict, block: Dict[str, object]) -> float:
    rows = list(block.get("rows", []) or [])
    scores = list(block.get("scores", []) or [])
    filtered_pairs = [
        (row, float(scores[idx]) if idx < len(scores) else 0.0)
        for idx, row in enumerate(rows)
        if not bool(row.get("ignored"))
    ]
    rows = [row for row, _ in filtered_pairs]
    scores = [score for _, score in filtered_pairs]
    if not rows or not scores:
        return 0.0

    anchor_score = float(scores[0]) if scores else 0.0
    support_scores = [max(0.0, float(score)) for score in scores[1:]]
    support_bonus = min(2.25, sum(support_scores) * 0.18)
    generic_exercise_bonus = 0.0

    entry_norm = " ".join(
        filter(
            None,
            [
                signals.get("title_text", ""),
                signals.get("markdown_text", ""),
                signals.get("category_text", ""),
                signals.get("tags_text", ""),
                signals.get("raw_text", ""),
            ],
        )
    )
    is_exercise_entry = any(term in entry_norm for term in ["exercicio", "exercicios", "lista", "listas", "gabarito", "respostas"])
    if is_exercise_entry:
        for row in rows[1:]:
            row_text = _normalize_match_text(str(row.get("content", "")))
            if any(term in row_text for term in ["exercicio", "exercicios", "lista", "listas", "gabarito", "respostas"]):
                generic_exercise_bonus += 0.22

    card_bonus = _score_card_evidence_against_entry(signals, block.get("card_evidence", []) or [])

    return anchor_score * 1.15 + support_bonus + min(generic_exercise_bonus, 0.66) + min(card_bonus, 0.45)


def _timeline_block_matches_preferred_topic(block: Dict[str, object], preferred_topic_slug: str) -> bool:
    preferred_topic_slug = str(preferred_topic_slug or "").strip()
    if not preferred_topic_slug:
        return False

    block_topic_slug = str(block.get("primary_topic_slug", "") or "").strip()
    if block_topic_slug == preferred_topic_slug:
        return True

    for candidate in block.get("topic_candidates", []) or []:
        if str(candidate.get("topic_slug", "") or "").strip() == preferred_topic_slug:
            return True

    return False


def _score_entry_against_timeline_block(
    signals: dict,
    block: Dict[str, object],
    preferred_unit_slug: str = "",
    preferred_topic_slug: str = "",
) -> float:
    rows = _timeline_block_rows_for_scoring(block)
    if not rows:
        return 0.0
    row_scores = [
        _score_entry_against_timeline_row(signals, str(row.get("content", "")))
        for row in rows
    ]
    runtime_block = dict(block)
    runtime_block["rows"] = rows
    runtime_block["scores"] = row_scores
    score = _score_timeline_block(signals, runtime_block)

    block_unit_slug = str(block.get("unit_slug", "") or "")
    block_unit_confidence = float(block.get("unit_confidence", 0.0) or 0.0)
    if preferred_unit_slug:
        if block_unit_slug == preferred_unit_slug:
            score += 0.35 + (block_unit_confidence * 0.25)
        elif block_unit_slug:
            score -= 0.45

    preferred_topic_slug = str(preferred_topic_slug or "").strip()
    if preferred_topic_slug:
        block_topic_slug = str(block.get("primary_topic_slug", "") or "").strip()
        block_topic_confidence = float(block.get("primary_topic_confidence", 0.0) or 0.0)
        if block_topic_slug == preferred_topic_slug:
            score += 0.8 + (block_topic_confidence * 0.35)
        elif _timeline_block_matches_preferred_topic(block, preferred_topic_slug):
            score += 0.48
        elif block_topic_slug:
            score -= 0.18

    topic_text = _normalize_match_text(str(block.get("topic_text", "")))
    if topic_text:
        topic_tokens = [tok for tok in topic_text.split() if len(tok) >= 4]
        score += _score_text_against_row(signals.get("manual_tags_text", ""), topic_tokens, weight=0.35)
        score += _score_text_against_row(signals.get("auto_tags_text", ""), topic_tokens, weight=0.12)
        score += _score_text_against_row(signals.get("legacy_tags_text", ""), topic_tokens, weight=0.05)

    score += min(_score_card_evidence_against_entry(signals, block.get("card_evidence", []) or []), 0.45)

    return score


def _collect_entry_temporal_signals(entry: dict, markdown_text: str) -> dict:
    raw_parts = [
        str(entry.get("title", "") or ""),
        str(entry.get("raw_target", "") or ""),
        str(entry.get("category", "") or ""),
        str(entry.get("tags", "") or ""),
        markdown_text or "",
    ]
    combined_text = "\n".join(part for part in raw_parts if _collapse_ws(part))
    date_range = extract_date_range_signal(combined_text)
    session_signals = extract_timeline_session_signals(combined_text)
    date_values = set()
    for session in session_signals:
        session_date = str(session.get("date", "") or "").strip()
        if session_date:
            date_values.add(session_date)
    if date_range.get("start"):
        date_values.add(str(date_range.get("start", "")).strip())
    if date_range.get("end"):
        date_values.add(str(date_range.get("end", "")).strip())
    return {
        "combined_text": _normalize_match_text(combined_text),
        "date_range": date_range,
        "date_values": sorted(date_values),
        "session_signals": session_signals,
    }


def _entry_temporal_range_contains(date_text: str, date_range: dict) -> bool:
    if not date_text or not date_range:
        return False
    session_dt = _parse_timeline_date_value(date_text)
    start_dt = _parse_timeline_date_value(str(date_range.get("start", "") or ""))
    end_dt = _parse_timeline_date_value(str(date_range.get("end", "") or ""))
    if not session_dt or not start_dt or not end_dt:
        return False
    return start_dt <= session_dt <= end_dt


def _score_entry_against_timeline_session(entry_temporal_signals: dict, session: Dict[str, object]) -> tuple[float, float]:
    if not session:
        return 0.0, 0.0

    entry_text = str(entry_temporal_signals.get("combined_text", "") or "")
    if not entry_text:
        return 0.0, 0.0

    session_label = _normalize_match_text(str(session.get("label", "") or ""))
    session_signals = [
        _normalize_match_text(str(signal))
        for signal in (session.get("signals", []) or [])
        if _normalize_match_text(str(signal))
    ]
    session_text = " ".join(filter(None, [session_label, " ".join(session_signals)]))
    session_tokens = [tok for tok in session_text.split() if len(tok) >= 4]
    score = _score_text_against_row(entry_text, session_tokens, weight=1.1)

    session_date = str(session.get("date", "") or "").strip()
    date_values = {
        str(value).strip()
        for value in (entry_temporal_signals.get("date_values") or [])
        if str(value).strip()
    }
    if session_date:
        if session_date in date_values:
            score += 3.0
        elif _entry_temporal_range_contains(session_date, entry_temporal_signals.get("date_range") or {}):
            score += 2.2

    kind = str(session.get("kind", "") or "").strip()
    if kind == "async":
        if any(
            term in entry_text
            for term in [
                "atividade assincrona",
                "atividade assíncrona",
                "assincrona",
                "assincrono",
                "async",
            ]
        ):
            score += 0.9
    elif kind == "class" and session_date:
        if any(term in entry_text for term in ["aula", "semana", "dia"]):
            score += 0.15

    card_bonus = min(
        0.55,
        _score_card_evidence_against_entry(entry_temporal_signals, session.get("card_evidence", []) or []),
    )
    if card_bonus > 0:
        score += card_bonus

    return score, card_bonus


def _score_entry_against_timeline_sessions(entry_temporal_signals: dict, block: Dict[str, object]) -> tuple[float, Optional[Dict[str, object]], float]:
    best_score = 0.0
    best_session: Optional[Dict[str, object]] = None
    best_card_bonus = 0.0
    for session in block.get("sessions", []) or []:
        score, card_bonus = _score_entry_against_timeline_session(entry_temporal_signals, session)
        if score > best_score:
            best_score = score
            best_session = session
            best_card_bonus = card_bonus
    return best_score, best_session, best_card_bonus


def _select_probable_period_for_entry(
    entry: dict,
    unit: dict,
    candidate_rows: List[Dict[str, object]],
    markdown_text: str,
    preferred_topic_slug: str = "",
) -> tuple[str, float, bool, List[str]]:
    if not candidate_rows:
        return "", 0.0, True, ["sem-linhas-candidato"]

    signals = _collect_entry_unit_signals(entry, markdown_text)
    if candidate_rows and "rows" in candidate_rows[0]:
        blocks = list(candidate_rows)
    else:
        timeline_index = _build_timeline_index(candidate_rows, unit_index=[unit] if unit else [])
        blocks = list(timeline_index.get("blocks", []) or [])
    if not blocks:
        return "", 0.0, True, ["sem-blocos-candidato"]

    preferred_unit_slug = str(unit.get("slug", "") or "")
    preferred_topic_slug = str(preferred_topic_slug or "").strip()
    temporal_signals = _collect_entry_temporal_signals(entry, markdown_text)
    topic_filtered_blocks = [
        block for block in blocks if _timeline_block_matches_preferred_topic(block, preferred_topic_slug)
    ]
    scored_source_blocks = topic_filtered_blocks if topic_filtered_blocks else blocks
    session_scored_blocks = []
    for block in scored_source_blocks:
        block_score = _score_entry_against_timeline_block(
            signals,
            block,
            preferred_unit_slug=preferred_unit_slug,
            preferred_topic_slug=preferred_topic_slug,
        )
        session_score, matched_session, session_card_bonus = _score_entry_against_timeline_sessions(temporal_signals, block)
        if session_score >= 1.0:
            session_scored_blocks.append((block, session_score, block_score, matched_session, session_card_bonus))

    if session_scored_blocks:
        session_scored_blocks.sort(key=lambda item: (item[1], item[2], item[4]), reverse=True)
        best_block, best_score, best_block_score, best_session, best_session_card_bonus = session_scored_blocks[0]
        runner_up_score = session_scored_blocks[1][1] if len(session_scored_blocks) > 1 else 0.0
        if best_score < 1.0:
            return "", best_score, True, [f"best={best_score:.2f}", "score-baixo"]
        selected_rows = list(best_block.get("rows", []) or [])
        period = str(best_block.get("period_label", "")).strip()
        if not period:
            selected_dates = [
                str(row.get("date_text", "")).strip()
                for row in selected_rows
                if str(row.get("date_text", "")).strip()
            ]
            if selected_dates:
                period = _timeline_period_label(selected_dates[0], selected_dates[-1])
        if not period:
            return "", best_score, True, [f"best={best_score:.2f}", "sem-datas"]

        confidence = min(1.0, max(0.0, (best_score - runner_up_score) + (best_score * 0.18)))
        ambiguous = best_score < 1.0 or abs(best_score - runner_up_score) < 0.35
        if len(session_scored_blocks) == 1 and not ambiguous:
            confidence = max(confidence, 0.72)
        reasons = [
            f"best={best_score:.2f}",
            f"runner_up={runner_up_score:.2f}",
            f"session_block={best_block_score:.2f}",
            f"selected_rows={len(selected_rows)}",
            f"selected_block_rows={len(selected_rows)}",
            "session-first",
        ]
        if best_session and best_session.get("id"):
            reasons.append(f"session={best_session.get('id')}")
        if best_session_card_bonus >= 0.15:
            reasons.append("card-evidence")
        if preferred_topic_slug:
            reasons.append(f"topic={preferred_topic_slug}")
            if topic_filtered_blocks:
                reasons.append("topic-filtered")
        if ambiguous:
            reasons.append("ambiguous")
        return period, confidence, ambiguous, reasons

    scored_blocks = [
        (
            block,
            _score_entry_against_timeline_block(
                signals,
                block,
                preferred_unit_slug=preferred_unit_slug,
                preferred_topic_slug=preferred_topic_slug,
            ),
        )
        for block in scored_source_blocks
    ]
    scored_blocks.sort(key=lambda item: item[1], reverse=True)

    best_block, best_score = scored_blocks[0]
    runner_up_score = scored_blocks[1][1] if len(scored_blocks) > 1 else 0.0
    if best_score < 0.95:
        return "", best_score, True, [f"best={best_score:.2f}", "score-baixo"]
    selected_rows = list(best_block.get("rows", []) or [])
    period = str(best_block.get("period_label", "")).strip()
    if not period:
        selected_dates = [
            str(row.get("date_text", "")).strip()
            for row in selected_rows
            if str(row.get("date_text", "")).strip()
        ]
        if selected_dates:
            period = _timeline_period_label(selected_dates[0], selected_dates[-1])
    if not period:
        return "", best_score, True, [f"best={best_score:.2f}", "sem-datas"]

    confidence = min(1.0, max(0.0, (best_score - runner_up_score) + (best_score * 0.18)))
    ambiguous = best_score < 1.0 or abs(best_score - runner_up_score) < 0.35
    best_block_card_bonus = min(
        0.45,
        _score_card_evidence_against_entry(signals, best_block.get("card_evidence", []) or []),
    )
    reasons = [
        f"best={best_score:.2f}",
        f"runner_up={runner_up_score:.2f}",
        f"selected_rows={len(selected_rows)}",
        f"selected_block_rows={len(selected_rows)}",
    ]
    if best_block_card_bonus >= 0.15:
        reasons.append("card-evidence")
    if preferred_topic_slug:
        reasons.append(f"topic={preferred_topic_slug}")
        if topic_filtered_blocks:
            reasons.append("topic-filtered")
    if ambiguous:
        reasons.append("ambiguous")
    return period, confidence, ambiguous, reasons


def _aggregate_unit_periods_from_blocks(blocks_by_unit: Dict[str, List[Dict[str, object]]]) -> Dict[str, str]:
    period_map: Dict[str, str] = {}
    for slug, blocks in (blocks_by_unit or {}).items():
        if not slug or not blocks:
            continue
        start_dates = []
        end_dates = []
        for block in blocks:
            start = _parse_timeline_date_value(str(block.get("period_start", "") or ""))
            end = _parse_timeline_date_value(str(block.get("period_end", "") or ""))
            if start:
                start_dates.append(start)
            if end:
                end_dates.append(end)
        if start_dates and end_dates:
            sorted_blocks = sorted(
                blocks,
                key=lambda item: (
                    _parse_timeline_date_value(str(item.get("period_start", "") or "")) or datetime.max
                ),
            )
            edge_dates = []
            for block in (sorted_blocks[0], sorted_blocks[-1]):
                edge_dates.extend(
                    re.findall(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}", str(block.get("period_label", "")))
                )
            if edge_dates:
                start_label = edge_dates[0]
                end_label = edge_dates[-1] if len(edge_dates) > 1 else edge_dates[0]
                period_map[slug] = _timeline_period_label(start_label, end_label)
                continue
            period_map[slug] = _timeline_period_label(
                min(start_dates).strftime("%Y-%m-%d"),
                max(end_dates).strftime("%Y-%m-%d"),
            )
            continue
        labels = [str(block.get("period_label", "")).strip() for block in blocks if str(block.get("period_label", "")).strip()]
        if labels:
            period_map[slug] = labels[0] if len(labels) == 1 else _timeline_period_label(labels[0], labels[-1])
    return period_map


def _build_file_map_timeline_context_from_course(
    course_meta: dict,
    subject_profile=None,
    content_taxonomy: Optional[dict] = None,
) -> dict:
    test_context = course_meta.get("_timeline_context") or course_meta.get("_timeline_context_for_tests")
    if test_context:
        return dict(test_context)

    unit_index = _build_file_map_unit_index_from_course(course_meta, subject_profile)
    content_taxonomy = content_taxonomy or _build_file_map_content_taxonomy_from_course(course_meta, subject_profile)
    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    timeline = _parse_syllabus_timeline(syllabus) if syllabus else []
    candidate_rows = _build_timeline_candidate_rows(timeline)
    timeline_index = (
        _build_timeline_index(candidate_rows, unit_index=unit_index, content_taxonomy=content_taxonomy)
        if candidate_rows
        else _empty_timeline_index()
    )

    blocks_by_unit: Dict[str, List[Dict[str, object]]] = {}
    rows_by_unit: Dict[str, List[Dict[str, object]]] = {}
    unassigned_blocks: List[Dict[str, object]] = []
    for block in timeline_index.get("blocks", []) or []:
        slug = str(block.get("unit_slug", "") or "")
        if slug:
            blocks_by_unit.setdefault(slug, []).append(block)
            rows_by_unit.setdefault(slug, []).extend(list(block.get("rows", []) or []))
        else:
            unassigned_blocks.append(block)

    unit_periods = _aggregate_unit_periods_from_blocks(blocks_by_unit)
    unit_period_bounds = {
        slug: _parse_timeline_period_bounds(period)
        for slug, period in unit_periods.items()
        if period
    }

    return {
        "timeline": timeline,
        "timeline_index": timeline_index,
        "unit_periods": unit_periods,
        "unit_period_bounds": unit_period_bounds,
        "unit_index": unit_index,
        "rows_by_unit": rows_by_unit,
        "blocks_by_unit": blocks_by_unit,
        "unassigned_blocks": unassigned_blocks,
    }


def _parse_bibliography_from_teaching_plan(text: str) -> dict:
    """
    Extrai referências bibliográficas do texto do plano de ensino.
    Detecta seção BIBLIOGRAFIA com sub-seções BÁSICA e COMPLEMENTAR.
    Retorna {"basica": [str, ...], "complementar": [str, ...]}.
    """
    result: dict = {"basica": [], "complementar": []}

    bib_match = re.search(r'^BIBLIOGRAFIA', text, re.MULTILINE | re.IGNORECASE)
    if not bib_match:
        return result

    bib_text = text[bib_match.start():]
    current_section: Optional[str] = None
    current_ref: Optional[str] = None
    ref_start_re = re.compile(r'^\d+\.\s+(.+)')

    def _flush():
        if current_ref and current_section:
            result[current_section].append(current_ref.strip())

    for raw in bib_text.splitlines():
        line = raw.strip()

        if re.match(r'^B[ÁA]SICA\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "basica"
            continue

        if re.match(r'^COMPLEMENTAR\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "complementar"
            continue

        if not current_section:
            continue

        if not line:
            _flush()
            current_ref = None
            continue

        m = ref_start_re.match(line)
        if m:
            _flush()
            current_ref = m.group(1).strip()
        elif current_ref is not None:
            current_ref += " " + line

    _flush()
    return result


def _canonical_assessment_label(raw_label: str) -> str:
    normalized = _normalize_match_text(raw_label)
    if not normalized:
        return ""
    normalized = normalized.replace("final", "final").strip()
    match = re.match(r"^p\s*(\d+)$", normalized)
    if match:
        return f"P{int(match.group(1))}"
    if normalized in {"pf", "p final", "prova final", "exame final"}:
        return "PF"
    if normalized.startswith("exame"):
        return "EXAME"
    if normalized.startswith("prova"):
        return _collapse_ws(normalized).upper()
    return _collapse_ws(normalized).upper()


def _assessment_label_aliases(label_slug: str) -> List[str]:
    normalized = _normalize_match_text(label_slug)
    aliases = set()
    if not normalized:
        return []
    if normalized == "pf":
        aliases.update({"pf", "prova final", "exame final"})
    else:
        p_match = re.match(r"^(?:p|prova)\s*(\d+)$", normalized)
        if p_match:
            num = int(p_match.group(1))
            aliases.add(f"p{num}")
            aliases.add(f"p {num}")
            aliases.add(f"prova {num}")
            aliases.add(f"prova {num:02d}")
        aliases.add(normalized)
    return sorted(aliases)


def _extract_declared_unit_numbers(text: str, label_slug: str = "") -> List[int]:
    normalized = _normalize_match_text(text)
    if not normalized:
        return []
    scope_text = normalized
    scope_match = re.search(
        r"\b(?:unidade(?:s)?(?: de aprendizagem)?|conteudo(?:s)?|abrangendo|abrange|cobre|cobrindo|inclui|incluindo)\b(.+)",
        normalized,
    )
    if scope_match:
        scope_text = scope_match.group(1).strip()
    numbers = []
    for raw_num in re.findall(r"\b0*(\d+)\b", scope_text):
        try:
            value = int(raw_num)
        except ValueError:
            continue
        if 1 <= value <= 20:
            numbers.append(value)
    if scope_match:
        return list(dict.fromkeys(numbers))
    label_match = re.match(r"^(?:p|prova)\s*(\d+)$", _normalize_match_text(label_slug))
    if label_match:
        try:
            label_number = int(label_match.group(1))
        except ValueError:
            label_number = None
        else:
            if label_number in numbers:
                numbers.remove(label_number)
    return list(dict.fromkeys(numbers))


def _parse_assessments_from_teaching_plan(text: str) -> List[dict]:
    assessments: List[dict] = []
    if not text:
        return assessments

    in_section = False
    current: Optional[dict] = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized = _normalize_teaching_plan_heading(line)
        cleaned = re.sub(r"^[\-•*]\s*", "", normalized).strip()
        if not cleaned:
            continue

        if not in_section and _TEACHING_PLAN_ASSESSMENT_START.match(cleaned):
            in_section = True
            current = None
            continue

        if in_section and _TEACHING_PLAN_ASSESSMENT_STOP.match(cleaned):
            break

        if not in_section:
            continue

        match = _ASSESSMENT_LINE_RE.match(cleaned)
        if match:
            if current:
                assessments.append(current)
            label_slug = _canonical_assessment_label(match.group("label"))
            if not label_slug:
                continue
            desc = _collapse_ws(match.group("desc"))
            current = {
                "label": label_slug,
                "label_slug": _normalize_match_text(label_slug),
                "description": desc,
                "raw_lines": [cleaned],
            }
            continue

        if current:
            current["description"] = _collapse_ws(f"{current.get('description', '')} {cleaned}")
            current.setdefault("raw_lines", []).append(cleaned)

    if current:
        assessments.append(current)

    for item in assessments:
        description = str(item.get("description", "") or "").strip()
        label_slug = str(item.get("label_slug", "") or "").strip()
        item["label"] = _canonical_assessment_label(item.get("label", label_slug))
        item["label_slug"] = _normalize_match_text(label_slug or item["label"])
        item["declared_unit_numbers"] = _extract_declared_unit_numbers(description, item["label_slug"])
        item["raw_lines"] = list(dict.fromkeys(item.get("raw_lines", []) or []))

    return assessments


def _assessment_match_row_text(row: dict) -> str:
    return _normalize_match_text(" ".join(str(value) for value in row.values() if str(value).strip()))


def _assessment_date_from_timeline_rows(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return ""
    for row in rows:
        for key in row.keys():
            if any(token in key for token in ["data", "date"]):
                value = str(row.get(key, "") or "").strip()
                if value:
                    return value
    for row in rows:
        for value in row.values():
            value = str(value or "").strip()
            if _parse_timeline_date_value(value):
                return value
    return ""


def _assessment_scope_unit_slugs(declared_unit_numbers: List[int], unit_index: list) -> List[str]:
    if not declared_unit_numbers or not unit_index:
        return []
    slugs = []
    for unit in unit_index:
        slug = str(unit.get("slug", "") or "").strip()
        if not slug:
            continue
        unit_number = _timeline_unit_number_from_unit(unit)
        if unit_number is None:
            unit_number = _timeline_unit_number_from_text(str(unit.get("title", "") or ""))
        if unit_number and unit_number in declared_unit_numbers:
            slugs.append(slug)
    return slugs


def _assessment_conflict_observation(
    assessment_label: str,
    assessment_date: str,
    unit_slug: str,
    unit_title: str,
    unit_period: str,
) -> str:
    if not assessment_date or not unit_period:
        return ""
    if unit_title:
        return (
            f"{assessment_label} em {assessment_date} antecede {unit_title} "
            f"(previsto para {unit_period})."
        )
    return f"{assessment_label} em {assessment_date} antecede {unit_slug} (previsto para {unit_period})."


def _build_assessment_context_from_course(
    course_meta: dict,
    subject_profile=None,
    timeline_context: Optional[dict] = None,
) -> dict:
    test_context = course_meta.get("_assessment_context") or course_meta.get("_assessment_context_for_tests")
    if test_context:
        return dict(test_context)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    if not teaching_plan and not syllabus:
        return {"version": 1, "assessments": [], "conflicts": []}

    timeline_rows = _parse_syllabus_timeline(syllabus) if syllabus else []
    unit_index = _build_file_map_unit_index_from_course(course_meta, subject_profile)
    if timeline_context is None:
        timeline_context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    unit_period_bounds = (timeline_context or {}).get("unit_period_bounds", {}) or {}
    unit_periods = (timeline_context or {}).get("unit_periods", {}) or {}
    unit_by_slug = {str(unit.get("slug", "") or ""): unit for unit in unit_index if str(unit.get("slug", "") or "").strip()}

    assessments = _parse_assessments_from_teaching_plan(teaching_plan)
    if not assessments:
        return {
            "version": 1,
            "assessments": [],
            "conflicts": [],
            "unit_periods": unit_periods,
        }

    enriched_assessments = []
    conflicts = []
    for assessment in assessments:
        label = str(assessment.get("label", "") or "").strip()
        label_slug = str(assessment.get("label_slug", "") or "").strip()
        aliases = _assessment_label_aliases(label_slug)
        matched_rows = [
            row
            for row in timeline_rows
            if any(alias and re.search(rf"\b{re.escape(alias)}\b", _assessment_match_row_text(row)) for alias in aliases)
        ]
        assessment_date = _assessment_date_from_timeline_rows(matched_rows)
        declared_unit_numbers = list(assessment.get("declared_unit_numbers") or [])
        declared_unit_slugs = _assessment_scope_unit_slugs(declared_unit_numbers, unit_index)
        observation_lines = []
        conflict_lines = []
        if assessment_date and declared_unit_slugs:
            assessment_dt = _parse_timeline_date_value(assessment_date)
            if assessment_dt:
                for unit_slug in declared_unit_slugs:
                    start_dt, end_dt = unit_period_bounds.get(unit_slug, (None, None))
                    unit = unit_by_slug.get(unit_slug, {})
                    unit_title = str(unit.get("title", "") or "").strip()
                    unit_period = str(unit_periods.get(unit_slug, "") or "").strip()
                    if start_dt and assessment_dt < start_dt:
                        conflict_text = _assessment_conflict_observation(
                            label,
                            assessment_date,
                            unit_slug,
                            unit_title,
                            unit_period,
                        )
                        if conflict_text:
                            conflict_lines.append(conflict_text)
        if declared_unit_numbers and not assessment_date:
            observation_lines.append(f"{label}: escopo por unidade encontrado, mas a data não foi localizada no cronograma.")
        if assessment_date and not declared_unit_numbers:
            observation_lines.append(f"{label}: data encontrada ({assessment_date}), mas sem escopo de unidade explícito.")

        enriched = {
            **assessment,
            "aliases": aliases,
            "assessment_date": assessment_date,
            "matched_row_count": len(matched_rows),
            "declared_unit_slugs": declared_unit_slugs,
            "observations": observation_lines,
            "conflicts": conflict_lines,
        }
        enriched_assessments.append(enriched)
        if conflict_lines:
            conflicts.append({
                "label": label,
                "label_slug": label_slug,
                "assessment_date": assessment_date,
                "declared_unit_numbers": declared_unit_numbers,
                "declared_unit_slugs": declared_unit_slugs,
                "conflicts": conflict_lines,
            })

    return {
        "version": 1,
        "assessments": enriched_assessments,
        "conflicts": conflicts,
        "unit_periods": unit_periods,
    }


def _write_internal_assessment_context(root_dir: Path, assessment_context: dict) -> None:
    write_text(
        root_dir / "course" / ".assessment_context.json",
        json.dumps(assessment_context or {"version": 1, "assessments": [], "conflicts": []}, ensure_ascii=False, indent=2),
    )


def _assessment_conflict_section_lines(assessment_context: Optional[dict], compact: bool = False) -> List[str]:
    conflicts = list((assessment_context or {}).get("conflicts", []) or [])
    if not conflicts:
        return []

    lines = [
        "## Conflitos de avaliação x cronograma",
        "",
    ]
    if compact:
        lines += [
            "| Avaliação | Data | Escopo | Observação |",
            "|---|---|---|---|",
        ]
        for item in conflicts:
            declared_units = item.get("declared_unit_numbers", []) or []
            scope = ", ".join(f"U{num}" for num in declared_units) if declared_units else "—"
            note = " ".join(item.get("conflicts", []) or [])
            lines.append(
                f"| {item.get('label', '')} | {item.get('assessment_date', '') or '—'} | {scope} | {note or '—'} |"
            )
    else:
        lines.append("**Resumo das inconsistências detectadas**")
        lines.append("")
        for item in conflicts:
            declared_units = item.get("declared_unit_numbers", []) or []
            scope = ", ".join(f"U{num}" for num in declared_units) if declared_units else "escopo não explicitado"
            note = " ".join(item.get("conflicts", []) or [])
            lines.append(
                f"- {item.get('label', '')}"
                f" ({item.get('assessment_date', '') or 'data não localizada'})"
                f" -> {scope}: {note or 'observação estrutural'}"
            )
    lines.append("")
    return lines


def syllabus_md(subject_profile) -> str:
    """Gera o conteúdo de course/SYLLABUS.md a partir do SubjectProfile."""
    subj = subject_profile
    return f"""---
course: {subj.name}
professor: {subj.professor}
schedule: {subj.schedule}
---

# Cronograma — {subj.name}

**Horário:** {subj.schedule}

{subj.syllabus}
"""


def student_profile_md(student_profile) -> str:
    """Gera o conteúdo de student/STUDENT_PROFILE.md a partir do StudentProfile."""
    sp = student_profile
    return f"""---
nickname: {sp.nickname or sp.full_name}
---

# Perfil do Aluno

- **Nome:** {sp.full_name}
- **Apelido:** {sp.nickname or sp.full_name}

## Estilo de aprendizado preferido

{sp.personality}
"""


def glossary_md(
    course_meta: dict,
    subject_profile=None,
    *,
    root_dir: Optional[Path] = None,
    manifest_entries: Optional[List[dict]] = None,
) -> str:
    course_name = course_meta.get("course_name", "Curso")

    lines = [
        f"# GLOSSARY — {course_name}",
        "",
        "> **Como usar:** Terminologia oficial da disciplina.",
        "> O tutor consulta este arquivo para usar os mesmos termos que o professor.",
        "> Inconsistência terminológica é fonte de confusão em provas.",
        "",
        "## Formato de entrada",
        "",
        "```",
        "## [Termo]",
        "**Definição:** [definição precisa usada nesta disciplina]",
        "**Sinônimos aceitos:** [outros nomes para o mesmo conceito]",
        "**Não confundir com:** [termo similar mas diferente]",
        "**Aparece em:** [unidades / tópicos onde é usado]",
        "```",
        "",
        "---",
        "",
        "## Termos",
        "",
    ]

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []
    evidence_docs = _collect_glossary_evidence(root_dir, manifest_entries=manifest_entries) if root_dir else []

    # Collect all topics as candidate terms, preserving unit association
    candidates = []  # List of (term_text, unit_title)
    for unit_title, topics in units:
        for topic in topics:
            candidates.append((_topic_text(topic), unit_title))

    if candidates:
        lines.append("> Termos extraídos automaticamente do plano de ensino.")
        lines.append("> Definições iniciais curtas são geradas no build para reduzir custo de contexto no tutor web.")
        lines.append("")
        for term, unit_title in candidates:
            evidence = _find_glossary_evidence(term, unit_title, evidence_docs)
            definition, synonyms, not_confuse = _seed_glossary_fields(term, unit_title, evidence=evidence)
            lines += [
                f"## {term}",
                f"**Definição:** {definition}",
                f"**Sinônimos aceitos:** {synonyms}",
                f"**Não confundir com:** {not_confuse}",
                f"**Aparece em:** {unit_title}",
                "",
            ]
    else:
        lines.append("> ⏳ **Termos serão adicionados pelo tutor na primeira sessão.**")
        lines.append("")

    return _clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def _clamp_navigation_artifact(text: str, *, max_chars: int, label: str) -> str:
    compact = (text or "").strip()
    if len(compact) <= max_chars:
        return compact

    note = f"> Conteúdo truncado para manter {label} compacto e roteável."
    cutoff = max(0, max_chars - len(note) - 4)
    clipped = compact[:cutoff].rstrip()
    if "\n" in clipped:
        clipped = clipped.rsplit("\n", 1)[0].rstrip()
    return f"{clipped}\n\n{note}"


def _extract_markdown_headings(raw_markdown: str, limit: int = 8) -> List[str]:
    headings: List[str] = []
    for line in (raw_markdown or "").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = _collapse_ws(match.group(1))
        if not heading:
            continue
        headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def _collect_glossary_evidence(
    root_dir: Optional[Path],
    manifest_entries: Optional[List[dict]] = None,
) -> List[Dict[str, str]]:
    if not root_dir:
        return []
    curated_dir = root_dir / "content" / "curated"
    if not curated_dir.exists():
        return []

    manifest_by_markdown: Dict[str, str] = {}
    for entry in manifest_entries or []:
        markdown_path = (
            entry.get("approved_markdown")
            or entry.get("curated_markdown")
            or entry.get("advanced_markdown")
            or entry.get("base_markdown")
            or ""
        )
        if markdown_path:
            manifest_by_markdown[Path(markdown_path).name.lower()] = _collapse_ws(
                entry.get("title") or entry.get("name") or ""
            )

    docs: List[Dict[str, str]] = []
    for md_path in sorted(curated_dir.glob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        body = _collapse_ws(_strip_frontmatter_block(raw))
        if not body:
            continue
        stripped = _strip_frontmatter_block(raw)
        title_match = re.search(r"^#\s+(.+)$", stripped, flags=re.MULTILINE)
        title = _collapse_ws(title_match.group(1)) if title_match else md_path.stem.replace("-", " ")
        docs.append({
            "title": title,
            "manifest_title": manifest_by_markdown.get(md_path.name.lower(), ""),
            "headings": _extract_markdown_headings(stripped),
            "text": body[:4000],
        })
    return docs


def _glossary_tokens(text: str) -> List[str]:
    words = re.findall(r"[a-zà-ÿ0-9]+", (text or "").lower())
    stopwords = {
        "de", "da", "do", "das", "dos", "e", "em", "para", "com", "por", "na",
        "no", "nas", "nos", "um", "uma", "as", "os", "o", "a", "ou", "ao", "à",
        "ii", "iii", "iv", "v", "unidade", "aprendizagem",
    }
    return [word for word in words if len(word) > 2 and word not in stopwords]


def _trim_glossary_prefix(text: str, prefixes: List[str]) -> str:
    cleaned = _collapse_ws(text)
    if not cleaned:
        return ""
    for prefix in prefixes:
        prefix = _collapse_ws(prefix)
        if not prefix:
            continue
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].lstrip(" -:|#")
    return _collapse_ws(cleaned)


def _shorten_glossary_sentence(sentence: str, max_chars: int = 180) -> str:
    sent = _collapse_ws(sentence)
    if len(sent) <= max_chars:
        return sent
    truncated = sent[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" ,;:") + "..."


def _is_bad_glossary_evidence(sentence: str) -> bool:
    sent = _collapse_ws(sentence)
    if not sent or len(sent) < 40:
        return True
    if sent.count("**") >= 2:
        return True
    if sent.lower().startswith("exemplo:"):
        return True
    if re.match(r"^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][\wÁÀÂÃÉÊÍÓÔÕÚÇáàâãéêíóôõúç-]+\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]", sent):
        if re.search(r"\d", sent) and len(sent) <= 80:
            return True
    return False


def _find_glossary_evidence(term: str, unit_title: str, docs: List[Dict[str, str]]) -> str:
    if not docs:
        return ""

    term_lower = (term or "").lower()
    tokens = _glossary_tokens(term) + _glossary_tokens(unit_title)
    best_score = 0
    best_text = ""

    for doc in docs:
        haystack = " ".join([
            doc.get("manifest_title", ""),
            doc.get("title", ""),
            " ".join(doc.get("headings", [])),
            doc.get("text", ""),
        ]).lower()
        score = 0
        if term_lower and term_lower in haystack:
            score += 8
        score += sum(1 for token in dict.fromkeys(tokens) if token in haystack)
        if score < 3 or score <= best_score:
            continue
        best_score = score
        best_text = _best_glossary_sentence(term, unit_title, doc)

    return best_text[:600]


def _best_glossary_sentence(term: str, unit_title: str, doc: Dict[str, str]) -> str:
    prefixes = [
        doc.get("manifest_title", ""),
        doc.get("title", ""),
        *doc.get("headings", []),
    ]
    sources = [
        doc.get("manifest_title", ""),
        doc.get("title", ""),
        " ".join(doc.get("headings", [])),
        _trim_glossary_prefix(doc.get("text", ""), prefixes),
    ]
    term_tokens = _glossary_tokens(term) + _glossary_tokens(unit_title)
    candidate_sentences: List[str] = []
    for source in sources:
        if not source:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", _collapse_ws(source)):
            sent = _collapse_ws(sentence)
            if len(sent) < 40 or len(sent) > 220:
                continue
            if _is_bad_glossary_evidence(sent):
                continue
            candidate_sentences.append(sent)
    best_sentence = ""
    best_score = 0
    for sent in candidate_sentences:
        sent = _normalize_glossary_sentence(term, unit_title, sent)
        sent_lower = sent.lower()
        score = 0
        if term.lower() in sent_lower:
            score += 6
        score += sum(1 for token in dict.fromkeys(term_tokens) if token in sent_lower)
        if score > best_score:
            best_score = score
            best_sentence = sent
    fallback = _trim_glossary_prefix(doc.get("text", ""), prefixes)
    return best_sentence or _shorten_glossary_sentence(fallback or _collapse_ws(doc.get("text", "")), 180)


def _normalize_glossary_sentence(term: str, unit_title: str, sentence: str) -> str:
    sent = _collapse_ws(sentence)
    if not sent:
        return ""
    sent = re.sub(r"^(?:#+\s*)+", "", sent)
    for prefix in [term, unit_title]:
        prefix = _collapse_ws(prefix)
        if not prefix:
            continue
        if sent.lower().startswith(prefix.lower()):
            sent = sent[len(prefix):].lstrip(" -:|#")
    sent = _collapse_ws(sent)
    if not sent:
        return _shorten_glossary_sentence(term, 120)
    if len(sent) > 180:
        sent = _shorten_glossary_sentence(sent, 180)
    return sent


def _seed_glossary_fields(term: str, unit_title: str, evidence: str = "") -> tuple[str, str, str]:
    text = _collapse_ws(term)
    lower = text.lower()
    unit_lower = (unit_title or "").lower()

    def _unit_hint() -> str:
        if "visão geral" in unit_lower or "visao geral" in unit_lower:
            return "visão geral"
        if "aprendizado de máquina" in unit_lower or "machine" in unit_lower:
            return "aprendizado de máquina"
        if "incerteza" in unit_lower or "probabilidade" in unit_lower:
            return "raciocínio sob incerteza"
        if "planejamento" in unit_lower:
            return "planejamento e representação de conhecimento"
        if "problemas" in unit_lower or "busca" in unit_lower:
            return "solução de problemas"
        if "verificação de programas" in unit_lower:
            return "verificação de programas"
        if "verificação de modelos" in unit_lower:
            return "verificação de modelos"
        if "métodos formais" in unit_lower:
            return "métodos formais"
        return "esta unidade"

    def _generic_definition() -> str:
        return _refine_glossary_definition_from_evidence(text, _unit_hint(), evidence)

    if "lógica de hoare" in lower:
        return (
            "Formalismo para especificar e verificar programas com pré-condições, pós-condições e invariantes.",
            "tripla de Hoare",
            "lógica temporal",
        )
    if "model checking" in lower or "verificação de modelos" in lower:
        return (
            "Técnica automática que checa se um modelo de sistema satisfaz propriedades formais.",
            "checagem de modelos",
            "prova de teoremas",
        )
    if "provadores de teoremas" in lower or "prova interativa de teoremas" in lower:
        return (
            "Ferramentas e técnicas usadas para construir provas formais com assistência mecânica.",
            "assistentes de prova",
            "model checking",
        )
    if "métodos formais" in lower:
        return (
            "Conjunto de técnicas matemáticas para especificar, modelar e verificar sistemas de software.",
            "formal methods",
            "testes informais",
        )
    if "máquinas de estado" in lower:
        return (
            "Modelo que representa um sistema por estados e transições entre eles.",
            "state machines",
            "árvores de derivação",
        )
    if "modelos de kripke" in lower:
        return (
            "Estruturas de estados rotulados usadas para interpretar propriedades em lógica temporal.",
            "estruturas de Kripke",
            "máquina de Turing",
        )
    if "lógica temporal linear" in lower:
        return (
            "Lógica temporal que descreve propriedades ao longo de sequências lineares de estados.",
            "LTL",
            "CTL",
        )
    if "lógica temporal ramificada" in lower:
        return (
            "Lógica temporal que considera múltiplos futuros possíveis a partir de um estado.",
            "CTL",
            "LTL",
        )
    if "pré e pós" in lower:
        return (
            "Condições que descrevem o que deve valer antes e depois da execução de um programa.",
            "precondições e pós-condições",
            "invariantes de laço",
        )
    if "invariante e variante de laço" in lower:
        return (
            "Propriedades usadas para demonstrar correção parcial e terminação de laços.",
            "invariante de laço",
            "pré-condições",
        )
    if "planejamento clássico" in lower or lower == "planejamento":
        return (
            "Abordagem que busca sequências de ações para atingir objetivos em um modelo explícito de estados.",
            "planning",
            "busca adversária",
        )
    if "agentes em lógica" in lower or "introdução a agentes" in lower:
        return (
            "Modelo de agente que percebe o ambiente e escolhe ações segundo uma representação formal.",
            "agentes racionais",
            "classificadores supervisionados",
        )
    if "busca informada" in lower:
        return (
            "Busca guiada por heurísticas para explorar primeiro estados mais promissores.",
            "busca heurística",
            "busca cega",
        )
    if "algoritmos de busca" in lower:
        return (
            "Procedimentos para explorar espaços de estados e encontrar soluções para problemas modelados.",
            "search algorithms",
            "métodos de otimização contínua",
        )
    if "busca adversária" in lower:
        return (
            "Estratégia de decisão para problemas competitivos em que as ações dependem do oponente.",
            "jogos adversariais",
            "busca heurística simples",
        )
    if "representação de problemas" in lower:
        return (
            "Forma de modelar estados, ações, restrições e objetivos para permitir resolução algorítmica.",
            "modelagem do problema",
            "pré-processamento de dados",
        )
    if "probabilidade" in lower or "regra de bayes" in lower or "independência e permutabilidade" in lower:
        return (
            "Conceito central de raciocínio sob incerteza usado para modelar crenças e atualizar evidências.",
            "inferência probabilística",
            "lógica determinística",
        )
    if "aprendizado de máquina" in lower:
        return (
            "Área da IA que aprende padrões a partir de dados para descrever ou prever comportamentos.",
            "machine learning",
            "planejamento clássico",
        )
    if "paradigmas de aprendizado" in lower:
        return (
            "Categorias de estratégias de aprendizado, como supervisionado, não supervisionado e por reforço.",
            "tipos de aprendizado",
            "métricas de avaliação",
        )
    if "modelos preditivos" in lower:
        return (
            "Modelos voltados a prever saídas, classes ou valores a partir de exemplos observados.",
            "modelos supervisionados",
            "modelos descritivos",
        )
    if "modelos descritivos" in lower:
        return (
            "Modelos usados para revelar estrutura, agrupamentos ou relações presentes nos dados.",
            "modelos exploratórios",
            "modelos preditivos",
        )
    if "métricas de avaliação" in lower:
        return (
            "Critérios quantitativos usados para comparar desempenho e qualidade de modelos.",
            "medidas de desempenho",
            "função objetivo do problema",
        )
    if "k-means" in lower:
        return (
            "Algoritmo de agrupamento que particiona exemplos em grupos definidos por centróides.",
            "agrupamento k-means",
            "k-NN",
        )
    if "k-nn" in lower:
        return (
            "Método que classifica ou estima saídas com base nos vizinhos mais próximos no espaço de atributos.",
            "k nearest neighbors",
            "k-means",
        )
    if "árvores de decisão" in lower:
        return (
            "Modelo que organiza decisões em divisões sucessivas sobre atributos dos dados.",
            "decision trees",
            "grafos de busca",
        )
    if "mlp" in lower or "rede neural" in lower or "perceptron" in lower:
        return (
            "Família de modelos conexionistas que aprende transformações por camadas a partir de exemplos.",
            "redes neurais artificiais",
            "árvore de decisão",
        )
    if "conceituação" in lower:
        return (
            _refine_glossary_definition_from_evidence(text, _unit_hint(), evidence),
            "visão geral",
            "detalhamento técnico",
        )
    if "histórico" in lower:
        return (
            _refine_glossary_definition_from_evidence(text, _unit_hint(), evidence),
            "contexto histórico",
            "estado da arte detalhado",
        )

    return (
        _generic_definition(),
        "—",
        "—",
    )


def _refine_glossary_definition_from_evidence(term: str, unit_hint: str, evidence: str) -> str:
    compact = _collapse_ws(evidence)
    if compact:
        sentences = re.split(r"(?<=[.!?])\s+", compact)
        term_tokens = _glossary_tokens(term)
        for sentence in sentences:
            sent = _normalize_glossary_sentence(term, unit_hint, sentence)
            sent_lower = sent.lower()
            if len(sent) < 40:
                continue
            if term.lower() in sent_lower or sum(1 for token in term_tokens if token in sent_lower) >= 2:
                cleaned = re.sub(r"^[^A-Za-zÀ-ÿ0-9]*", "", sent).rstrip(" .")
                cleaned = _shorten_glossary_sentence(cleaned, 180)
                if not cleaned.endswith("."):
                    cleaned += "."
                return cleaned
    return f"Conceito central de {unit_hint} que deve ser reconhecido e usado corretamente nas respostas e revisões."


_NO_UNIT_CATEGORIES = {"cronograma", "bibliografia", "referencias"}


def _bundle_priority_score(entry: dict) -> int:
    score = 0
    category = (entry.get("category") or "").strip().lower()
    title = (entry.get("title") or "").strip().lower()
    profile = normalize_document_profile(entry.get("effective_profile"))

    if entry.get("include_in_bundle"):
        score += 30
    if entry.get("relevant_for_exam"):
        score += 40
    if category in EXAM_CATEGORIES:
        score += 45
    elif category in EXERCISE_CATEGORIES:
        score += 35
    elif category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
        score += 20
    elif category in {"bibliografia", "referencias", "cronograma"}:
        score += 5

    if profile in {"math_heavy", "diagram_heavy"}:
        score += 10

    if "resumo" in title or "summary" in title:
        score += 10
    if "lista" in title or "exerc" in title:
        score += 8
    return score


def _bundle_reason_labels(entry: dict) -> List[str]:
    reasons: List[str] = []
    category = (entry.get("category") or "").strip().lower()
    profile = normalize_document_profile(entry.get("effective_profile"))
    if entry.get("include_in_bundle"):
        reasons.append("marcado-manualmente")
    if entry.get("relevant_for_exam"):
        reasons.append("relevante-para-prova")
    if category in EXAM_CATEGORIES:
        reasons.append("categoria-prova")
    elif category in EXERCISE_CATEGORIES:
        reasons.append("categoria-exercicio")
    elif category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
        reasons.append("material-base")
    if profile in {"math_heavy", "diagram_heavy"}:
        reasons.append(f"perfil-{profile}")
    return reasons or ["prioridade-geral"]


_MANIFEST_LOG_LIMIT = 200


def _entry_image_source_dirs(root_dir: Path, entry: dict) -> List[Path]:
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


def _entry_existing_reference_count(root_dir: Path, entry: dict) -> int:
    refs: List[Path] = []
    for key in [
        "raw_target",
        "base_markdown",
        "advanced_markdown",
        "manual_review",
        "tables_dir",
        "table_detection_dir",
        "advanced_asset_dir",
        "advanced_metadata_path",
        "approved_markdown",
        "curated_markdown",
    ]:
        value = entry.get(key)
        if value:
            refs.append(root_dir / value)
    refs.extend(_entry_image_source_dirs(root_dir, entry))
    return sum(1 for path in refs if path.exists())


def _filter_live_manifest_entries(root_dir: Optional[Path], manifest_entries: list) -> list:
    if not root_dir:
        return list(manifest_entries or [])

    live_entries = []
    for entry in manifest_entries or []:
        if not isinstance(entry, dict):
            continue

        ref_count = _entry_existing_reference_count(root_dir, entry)
        if ref_count > 0:
            live_entries.append(entry)
            continue

        has_any_reference = any(
            entry.get(key)
            for key in [
                "raw_target",
                "base_markdown",
                "advanced_markdown",
                "manual_review",
                "images_dir",
                "tables_dir",
                "table_detection_dir",
                "advanced_asset_dir",
                "advanced_metadata_path",
                "approved_markdown",
                "curated_markdown",
                "rendered_pages_dir",
            ]
        )
        if not has_any_reference:
            live_entries.append(entry)

    return live_entries


def _bundle_seed_candidate(entry: dict, score: int) -> dict:
    """Return a strict metadata-only payload for bundle.seed.json."""
    return {
        "id": entry["id"],
        "title": entry["title"],
        "category": entry["category"],
        "preferred_manual_review": entry.get("manual_review"),
        "approved_markdown": entry.get("approved_markdown"),
        "curated_markdown": entry.get("curated_markdown"),
        "advanced_markdown": entry.get("advanced_markdown"),
        "base_markdown": entry.get("base_markdown"),
        "effective_profile": entry.get("effective_profile"),
        "relevant_for_exam": bool(entry.get("relevant_for_exam")),
        "bundle_priority_score": score,
        "bundle_reasons": _bundle_reason_labels(entry),
    }


@dataclass
class UnitMatchResult:
    slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)


def _normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("propocional", "proposicional")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_outline_prefix(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    text = re.sub(
        r"^\s*unidade(?:\s+de\s+aprendizagem)?\s*\d+\s*[-—:.)]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-—:.)]?\s*", "", text)
    return text.strip()


_UNIT_GENERIC_TOKENS = {
    "metodos",
    "formais",
    "formal",
    "logica",
    "logicas",
    "especificacao",
    "especificacoes",
    "verificacao",
    "verificacoes",
    "programas",
    "programa",
    "modelos",
    "modelo",
    "fundamentos",
    "sistemas",
    "software",
    "softwares",
    "suporte",
    "propriedades",
    "aplicacoes",
    "sequenciais",
    "concorrentes",
    "linguagens",
}


def _normalize_unit_slug(title: str) -> str:
    slug = slugify((title or "").replace("—", "-"))
    match = re.match(r"^(unidade(?:-de-aprendizagem)?-)(\d+)(-.+)?$", slug)
    if not match:
        return slug
    prefix, number, suffix = match.groups()
    suffix = suffix or ""
    return f"{prefix}{int(number):02d}{suffix}"


def _build_file_map_unit_index(units: list) -> list:
    indexed = []
    for unit in units or []:
        if isinstance(unit, dict):
            title = unit.get("title", "")
            topics = unit.get("topics", []) or []
            extra_signals = unit.get("extra_signals", []) or []
        else:
            title, topics = unit
            extra_signals = []
        clean_title = _strip_outline_prefix(title)
        topic_phrases = []
        topic_tokens = []
        seen_topic_tokens = set()
        topic_signal_sources = list(topics) + list(extra_signals)
        for topic in topic_signal_sources:
            topic_norm = _normalize_match_text(_strip_outline_prefix(_topic_text(topic)))
            if not topic_norm:
                continue
            topic_phrases.append(topic_norm)
            if topic_norm not in seen_topic_tokens:
                topic_tokens.append(topic_norm)
                seen_topic_tokens.add(topic_norm)
            for token in topic_norm.split():
                if (
                    len(token) >= 4
                    and token not in seen_topic_tokens
                    and token not in _UNIT_GENERIC_TOKENS
                ):
                    topic_tokens.append(token)
                    seen_topic_tokens.add(token)
        indexed.append({
            "title": title,
            "slug": _normalize_unit_slug(title),
            "normalized_title": _normalize_match_text(clean_title),
            "topics": topics,
            "extra_signals": extra_signals,
            "topic_phrases": topic_phrases,
            "topic_tokens": topic_tokens,
            "title_anchor_tokens": [
                token
                for token in _normalize_match_text(clean_title).split()
                if len(token) >= 4 and token not in {"unidade", "aprendizagem", "verificacao"}
            ],
            "topic_anchor_tokens": [
                token
                for token in {
                    token
                    for text in topic_phrases
                    for token in text.split()
                }
                if len(token) >= 4 and token not in {"de", "para", "com", "sem", "sobre", "entre"}
            ],
            "distinctive_tokens": [],
        })

    token_frequency = {}
    for unit in indexed:
        unit_tokens = set()
        for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
            for token in text.split():
                if len(token) >= 4 and not token.isdigit() and token not in _UNIT_GENERIC_TOKENS:
                    unit_tokens.add(token)
        for token in unit_tokens:
            token_frequency[token] = token_frequency.get(token, 0) + 1

    for unit in indexed:
        unit_tokens = set()
        for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
            for token in text.split():
                if len(token) >= 4 and not token.isdigit() and token not in _UNIT_GENERIC_TOKENS:
                    unit_tokens.add(token)
        unit["token_weights"] = {
            token: 1.0 / token_frequency[token]
            for token in unit_tokens
            if token_frequency.get(token)
        }
        unit["distinctive_tokens"] = sorted(
            token for token, freq in token_frequency.items()
            if freq == 1 and token in unit_tokens and len(token) >= 5
        )
    return indexed


def _collect_entry_unit_signals(entry: dict, markdown_text: str) -> dict:
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
        "title_text": _normalize_match_text(entry.get("title", "")),
        "markdown_headings_text": _normalize_match_text(" ".join(_extract_markdown_headings(markdown_text))),
        "markdown_lead_text": _normalize_match_text(_extract_markdown_lead_text(markdown_text)),
        "category_text": _normalize_match_text(entry.get("category", "")),
        "manual_tags_text": _normalize_match_text("; ".join(manual_tags)),
        "auto_tags_text": _normalize_match_text("; ".join(auto_tags)),
        "legacy_tags_text": _normalize_match_text("; ".join(legacy_tags)),
        "tags_text": _normalize_match_text(merged_tags),
        "raw_text": _normalize_match_text(entry.get("raw_target", "")),
        "markdown_text": _normalize_match_text(markdown_text),
    }


def _build_file_map_content_taxonomy_from_course(
    course_meta: dict,
    subject_profile=None,
    manifest_entries: Optional[List[dict]] = None,
) -> dict:
    test_taxonomy = course_meta.get("_content_taxonomy") or course_meta.get("_content_taxonomy_for_tests")
    if test_taxonomy:
        return dict(test_taxonomy)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    if not teaching_plan:
        return {"version": 1, "course_slug": "", "units": []}

    root_dir = course_meta.get("_repo_root")
    course_name = course_meta.get("course_name", "Curso")
    parsed_units = _parse_units_from_teaching_plan(teaching_plan)
    course_map_lines = [f"# COURSE_MAP â€” {course_name}", ""]
    if parsed_units:
        for unit_title, topics in parsed_units:
            course_map_lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    course_map_lines.append(f"- [ ] {_topic_text(topic)}")
            else:
                course_map_lines.append("- [ ] [tópicos a preencher]")
            course_map_lines.append("")
    else:
        course_map_lines.append(teaching_plan)
    course_map_text = "\n".join(course_map_lines)
    glossary_text = ""
    if subject_profile:
        try:
            glossary_text = glossary_md(
                course_meta,
                subject_profile,
                root_dir=root_dir,
                manifest_entries=manifest_entries,
            )
        except Exception:
            glossary_text = ""
    strong_headings = _collect_strong_heading_candidates(root_dir, manifest_entries)
    semantic_profile = resolve_semantic_profile(
        root_dir=root_dir,
        course_name=course_name,
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
    )
    return _build_content_taxonomy(
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
    )


def _auto_map_entry_subtopic(entry: dict, taxonomy: dict, markdown_text: str) -> TopicMatchResult:
    topic_index = _iter_content_taxonomy_topics(taxonomy)
    if not topic_index:
        return TopicMatchResult(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=["sem-taxonomia"],
        )

    signals = _collect_entry_unit_signals(entry, markdown_text)
    scored = [
        (topic, _score_entry_against_taxonomy_topic(signals, topic))
        for topic in topic_index
    ]
    scored.sort(key=lambda item: item[1], reverse=True)

    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.2)))
    if len(scored) == 1:
        ambiguous = winner_score <= 0.0
        if not ambiguous:
            confidence = max(confidence, 0.72)
    else:
        ambiguous = winner_score <= 0.0 or abs(winner_score - runner_up_score) < 0.65
    if ambiguous:
        confidence = min(confidence, 0.45)

    reasons = [f"winner_score={winner_score:.2f}"]
    if ambiguous:
        reasons.append("ambiguous")

    return TopicMatchResult(
        topic_slug=str(winner.get("topic_slug", "") or ""),
        topic_label=str(winner.get("topic_label", "") or ""),
        unit_slug=str(winner.get("unit_slug", "") or ""),
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=reasons,
    )


def _score_entry_against_unit(signals: dict, unit: dict) -> float:
    title_text = signals.get("title_text", "")
    markdown_headings_text = signals.get("markdown_headings_text", "")
    markdown_lead_text = signals.get("markdown_lead_text", "")
    markdown_text = signals.get("markdown_text", "")
    category_text = signals.get("category_text", "")
    manual_tags_text = signals.get("manual_tags_text", "")
    auto_tags_text = signals.get("auto_tags_text", "")
    legacy_tags_text = signals.get("legacy_tags_text", "")
    tags_text = signals.get("tags_text", "")
    raw_text = signals.get("raw_text", "")
    title_tokens = set(tok for tok in title_text.split() if len(tok) >= 4)
    markdown_headings_tokens = set(tok for tok in markdown_headings_text.split() if len(tok) >= 4)
    markdown_lead_tokens = set(tok for tok in markdown_lead_text.split() if len(tok) >= 4)
    markdown_tokens = set(tok for tok in markdown_text.split() if len(tok) >= 4)
    manual_tags_tokens = set(tok for tok in manual_tags_text.split() if len(tok) >= 4)
    auto_tags_tokens = set(tok for tok in auto_tags_text.split() if len(tok) >= 4)
    legacy_tags_tokens = set(tok for tok in legacy_tags_text.split() if len(tok) >= 4)
    tags_tokens = set(tok for tok in tags_text.split() if len(tok) >= 4)
    raw_tokens = set(tok for tok in raw_text.split() if len(tok) >= 4)

    unit_title = unit.get("normalized_title", "")
    topic_phrases = unit.get("topic_phrases", []) or []
    topic_tokens = unit.get("topic_tokens", []) or []
    distinctive_tokens = unit.get("distinctive_tokens", []) or []
    token_weights = unit.get("token_weights", {}) or {}

    score = 0.0
    exact_topic_hits = 0
    matched_specific_tokens = set()
    title_words = [tok for tok in unit_title.split() if len(tok) >= 5]
    if unit_title and len(title_words) >= 3:
        if unit_title in markdown_text:
            score += 1.1
        if unit_title in markdown_lead_text:
            score += 1.6
        if unit_title in markdown_headings_text:
            score += 1.8
        if unit_title in title_text:
            score += 1.0

    for topic_phrase in topic_phrases:
        if not topic_phrase:
            continue
        if topic_phrase in markdown_headings_text:
            score += 3.0
            exact_topic_hits += 1
            continue
        if topic_phrase in markdown_lead_text:
            score += 2.8
            exact_topic_hits += 1
            continue
        if topic_phrase in title_text:
            score += 2.7
            exact_topic_hits += 1
            continue
        if topic_phrase in markdown_text:
            score += 1.4
            exact_topic_hits += 1
            continue
        if topic_phrase in manual_tags_text:
            score += 1.6
            exact_topic_hits += 1
            continue
        if topic_phrase in auto_tags_text:
            score += 0.18
            exact_topic_hits += 1
            continue
        if topic_phrase in legacy_tags_text:
            score += 0.24
            exact_topic_hits += 1
            continue
        score += _score_timeline_unit_phrase(markdown_headings_text, markdown_headings_tokens, topic_phrase, token_weights) * 0.55
        score += _score_timeline_unit_phrase(markdown_lead_text, markdown_lead_tokens, topic_phrase, token_weights) * 0.48
        score += _score_timeline_unit_phrase(markdown_text, markdown_tokens, topic_phrase, token_weights) * 0.18
        score += _score_timeline_unit_phrase(title_text, title_tokens, topic_phrase, token_weights) * 0.45
        score += _score_timeline_unit_phrase(manual_tags_text, manual_tags_tokens, topic_phrase, token_weights) * 0.35
        score += _score_timeline_unit_phrase(auto_tags_text, auto_tags_tokens, topic_phrase, token_weights) * 0.04
        score += _score_timeline_unit_phrase(legacy_tags_text, legacy_tags_tokens, topic_phrase, token_weights) * 0.02
        score += _score_timeline_unit_phrase(raw_text, raw_tokens, topic_phrase, token_weights) * 0.18

    for topic_token in topic_tokens:
        if not topic_token or " " in topic_token:
            continue
        weight = token_weights.get(topic_token, 1.0)
        if topic_token in _TIMELINE_UNIT_NEUTRAL_TOKENS:
            weight *= 0.2
        if topic_token in markdown_tokens:
            score += 0.32 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in markdown_lead_tokens:
            score += 0.7 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in markdown_headings_tokens:
            score += 0.8 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in title_tokens:
            score += 0.55 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in manual_tags_tokens:
            score += 0.45 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in auto_tags_tokens:
            score += 0.05 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in legacy_tags_tokens:
            score += 0.02 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)
        if topic_token in raw_tokens:
            score += 0.2 * weight
            if topic_token not in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                matched_specific_tokens.add(topic_token)

    for token in distinctive_tokens:
        if token in markdown_tokens:
            score += 0.25 if token in matched_specific_tokens else 0.7
            matched_specific_tokens.add(token)
        if token in title_tokens:
            score += 0.15 if token in matched_specific_tokens else 0.35
            matched_specific_tokens.add(token)
        if token in tags_tokens:
            score += 0.12 if token in matched_specific_tokens else 0.3
            matched_specific_tokens.add(token)
        if token in raw_tokens:
            score += 0.06 if token in matched_specific_tokens else 0.15
            matched_specific_tokens.add(token)

    if category_text in {"listas", "gabaritos"}:
        score += 0.15
    if manual_tags_text:
        score += 0.06
    elif auto_tags_text:
        score += 0.01
    elif legacy_tags_text:
        score += 0.01

    if exact_topic_hits == 0 and not matched_specific_tokens and score > 0.0:
        score *= 0.55
    if exact_topic_hits == 0 and len(matched_specific_tokens) == 1:
        score *= 0.45

    return score


def _auto_map_entry_unit(
    entry: dict,
    units: list,
    markdown_text: str,
    topic_index: Optional[List[dict]] = None,
) -> UnitMatchResult:
    indexed_units = _build_file_map_unit_index(units)
    if not indexed_units:
        return UnitMatchResult(slug="", confidence=0.0, ambiguous=True, reasons=["sem-unidades"])

    signals = _collect_entry_unit_signals(entry, markdown_text)
    scored = []
    normalized_topic_index = list(topic_index or [])
    for unit in indexed_units:
        score = _score_entry_against_unit(signals, unit)
        best_topic_score = 0.0
        if normalized_topic_index:
            unit_slug = _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
            for topic in normalized_topic_index:
                if _normalize_unit_slug(str(topic.get("unit_slug", "") or "")) != unit_slug:
                    continue
                topic_score = _score_entry_against_taxonomy_topic(signals, topic)
                if topic_score > best_topic_score:
                    best_topic_score = topic_score
            if best_topic_score >= 0.25:
                score += best_topic_score * 0.85
        scored.append((unit, score, best_topic_score))
    scored.sort(key=lambda item: item[1], reverse=True)

    winner, winner_score, winner_topic_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    runner_up_topic_score = scored[1][2] if len(scored) > 1 else 0.0
    confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.18)))
    if len(scored) == 1:
        ambiguous = winner_score <= 0.0
        if not ambiguous:
            confidence = max(confidence, 0.7)
    else:
        ambiguous = winner_score <= 0.0 or abs(winner_score - runner_up_score) < 0.8
        if (
            normalized_topic_index
            and winner_topic_score >= 0.55
            and (winner_topic_score - runner_up_topic_score) >= 0.01
        ):
            ambiguous = False
            confidence = max(confidence, min(0.95, winner_topic_score))
    if ambiguous:
        confidence = min(confidence, 0.4)
    reasons = [f"winner_score={winner_score:.2f}"]
    if normalized_topic_index:
        reasons.append(f"topic_score={winner_topic_score:.2f}")
    if ambiguous:
        reasons.append("ambiguous")
    return UnitMatchResult(
        slug=winner["slug"],
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=reasons,
    )


def _format_file_map_unit_cell(slug: str, confidence: float, ambiguous: bool) -> str:
    if not slug:
        return ""
    if ambiguous:
        return f"{slug} _(ambíguo)_"
    if confidence < 0.45:
        return f"{slug} _(baixa confiança)_"
    return slug


def _resolve_entry_manual_unit_slug(entry: dict, unit_index: list) -> str:
    raw = str(entry.get("manual_unit_slug") or "").strip()
    if not raw:
        return ""
    normalized = _normalize_unit_slug(raw)
    valid_slugs = {str(unit.get("slug", "")).strip() for unit in unit_index if str(unit.get("slug", "")).strip()}
    return normalized if normalized in valid_slugs else ""


def _resolve_entry_manual_timeline_block(entry: dict, timeline_context: dict) -> Optional[Dict[str, object]]:
    raw = str(entry.get("manual_timeline_block_id") or "").strip()
    if not raw:
        return None
    blocks = list(((timeline_context or {}).get("timeline_index") or {}).get("blocks", []) or [])
    for block in blocks:
        if str(block.get("id", "")).strip() == raw:
            return block
    match = re.fullmatch(r"bloco-(\d+)", raw, flags=re.IGNORECASE)
    if match:
        ordinal = int(match.group(1))
        entry_unit = str(entry.get("unit_slug") or entry.get("manual_unit_slug") or "").strip()
        instructional_blocks = [
            block
            for block in blocks
            if not bool(block.get("administrative_only"))
            and (not entry_unit or str(block.get("unit_slug", "")).strip() == entry_unit)
        ]
        if 1 <= ordinal <= len(instructional_blocks):
            return instructional_blocks[ordinal - 1]
    return None


def _build_file_map_unit_index_from_course(course_meta: dict, subject_profile=None) -> list:
    test_index = course_meta.get("_unit_index_for_tests")
    if test_index:
        return _build_file_map_unit_index(test_index)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    if not teaching_plan:
        return []

    parsed_units = _parse_units_from_teaching_plan(teaching_plan)
    root_dir = course_meta.get("_repo_root")
    glossary_text = ""
    try:
        glossary_text = glossary_md(course_meta, subject_profile, root_dir=root_dir, manifest_entries=None)
    except Exception:
        glossary_text = ""

    glossary_terms = _parse_glossary_terms(glossary_text)
    unit_specs = []
    for title, topics in parsed_units:
        normalized_unit = _normalize_match_text(title)
        extra_signals = []
        seen_signals = set()
        for term in glossary_terms:
            unit_hint = _normalize_match_text(str(term.get("unit_hint", "") or ""))
            if unit_hint and unit_hint not in normalized_unit and normalized_unit not in unit_hint:
                continue
            for candidate in [
                str(term.get("term", "") or ""),
                *list(term.get("synonyms", []) or []),
            ]:
                cleaned = _collapse_ws(str(candidate))
                normalized = _normalize_match_text(cleaned)
                if not normalized or normalized in seen_signals:
                    continue
                seen_signals.add(normalized)
                extra_signals.append(cleaned)

            definition = _normalize_match_text(str(term.get("definition", "") or ""))
            for token in definition.split():
                if len(token) < 5 or token in _UNIT_GENERIC_TOKENS or token in _TIMELINE_UNIT_NEUTRAL_TOKENS:
                    continue
                if token in seen_signals:
                    continue
                seen_signals.add(token)
                extra_signals.append(token)

        unit_specs.append({"title": title, "topics": topics, "extra_signals": extra_signals})
    return _build_file_map_unit_index(unit_specs)


def student_state_md(course_meta: dict, student_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name

    today = datetime.now().strftime("%Y-%m-%d")

    return student_state_v2.render_student_state_md(
        course_name=course_name,
        student_nickname=nick,
        today=today,
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )


def progress_schema_md() -> str:
    return """# PROGRESS_SCHEMA

## Schema do estado do aluno

Define a estrutura esperada de `STUDENT_STATE.md`.
Use este arquivo como referência ao atualizar o estado manualmente
ou ao pedir ao Claude para gerar uma atualização.

## Campos obrigatórios

```yaml
---
course: string          # Nome da disciplina
student: string         # Nome/apelido do aluno
last_updated: YYYY-MM-DD
---
```

## Status válidos para tópicos

| Status | Significado |
|---|---|
| `não iniciado` | Ainda não foi estudado |
| `em progresso` | Estudado mas não consolidado |
| `com dúvidas` | Estudado com pontos em aberto |
| `concluído` | Compreensão sólida demonstrada |
| `revisão` | Concluído mas precisa reforçar para prova |

## Ciclo de atualização recomendado

```
Sessão de estudo
    → Claude sugere bloco de atualização
    → Aluno revisa e ajusta
    → Aluno faz commit no GitHub
    → Na próxima sessão: Claude lê o estado atualizado
```

## Template de atualização (gerado pelo Claude ao final da sessão)

```markdown
## Atualização sugerida — [DATA]

**Tópico estudado:** [nome]
**Status:** [status válido acima]
**Dúvidas identificadas:** [lista ou "nenhuma"]
**Erros observados:** [lista ou "nenhum"]
**Próximo passo:** [próximo tópico sugerido]
```
"""


def bibliography_md(course_meta: dict, entries: List[FileEntry] = None, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# BIBLIOGRAPHY — {course_name}",
        "",
        "> **Como usar:** Links e referências da disciplina.",
        "> O tutor consulta este arquivo quando o aluno pede fontes",
        "> ou quando uma explicação pode ser aprofundada com leitura adicional.",
        "",
    ]

    # Referências extraídas do plano de ensino
    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    parsed = _parse_bibliography_from_teaching_plan(teaching_plan) if teaching_plan else {}
    basica = parsed.get("basica", [])
    complementar = parsed.get("complementar", [])

    if basica or complementar:
        lines.append("## Bibliografia do plano de ensino")
        lines.append("")
        if basica:
            lines.append("### Básica")
            lines.append("")
            for ref in basica:
                lines.append(f"- {ref}")
            lines.append("")
        if complementar:
            lines.append("### Complementar")
            lines.append("")
            for ref in complementar:
                lines.append(f"- {ref}")
            lines.append("")

    # Referências importadas manualmente via app (categoria "bibliografia")
    if entries:
        lines.append("## Referências importadas")
        lines.append("")
        for entry in entries:
            lines.append(f"### {entry.title}")
            lines.append(f"- **URL:** {entry.source_path}")
            if entry.tags:
                lines.append(f"- **Tags:** {entry.tags}")
            if entry.notes:
                lines.append(f"- **Nota:** {entry.notes}")
            if entry.professor_signal:
                lines.append(f"- **Indicação do professor:** {entry.professor_signal}")
            lines.append(f"- **Incluir no bundle:** {'sim' if entry.include_in_bundle else 'não'}")
            lines.append("")

    if not basica and not complementar and not entries:
        lines += [
            "## Referências",
            "",
            "<!-- Adicione referências aqui, importe links pelo app,",
            "     ou preencha o Plano de Ensino no Gerenciador de Matérias. -->",
            "",
        ]

    lines += [
        "## Mapa de relevância por tópico",
        "",
        "<!-- Preencha após organizar as referências -->",
        "",
        "| Tópico | Referência principal | Acessível | Incidência em prova |",
        "|---|---|---|---|",
        "| [a preencher] | | | |",
        "",
    ]

    return _clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def exam_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXAM_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de provas anteriores por tópico.",
        "> O tutor consulta este arquivo no modo `exam_prep` para identificar",
        "> quais tópicos têm maior incidência e quais padrões de questão se repetem.",
        "",
        "## Provas disponíveis",
        "",
    ]

    lines.append("| Arquivo | Tipo | Prova | Observação | Padrão do professor |")
    lines.append("|---|---|---|---|---|")
    for entry in entries:
        tipo = "foto" if entry.category == "fotos-de-prova" else "original"
        lines.append(
            f"| {Path(entry.source_path).name} | {tipo} | {entry.title} "
            f"| {entry.notes or ''} | {entry.professor_signal or ''} |"
        )

    lines += [
        "",
        "## Incidência de tópicos por prova",
        "",
        "> Preencha após revisar cada prova. O tutor usa esta tabela no modo `exam_prep`.",
        "",
        "| Tópico | P1 | P2 | P3 | Total | Peso estimado |",
        "|---|---|---|---|---|---|",
        "| [a preencher] | | | | | |",
        "",
        "## Padrões de questão observados",
        "",
        "<!-- Liste padrões recorrentes: tipos de enunciado, estrutura, pegadinhas comuns -->",
        "",
    ]

    return _clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def assignment_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# ASSIGNMENT_INDEX — {course_name}", "",
             "> **Como usar:** Índice de trabalhos e projetos.",
             "> Consulte antes de guiar o aluno — não entregue a solução.", "",
             "## Trabalhos", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} "
                         f"| {e.tags or ''} | pendente |")
    else:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|",
                  "| [a preencher] | | | |"]
    lines += ["", "## Padrões do professor", "",
              "- [a preencher]", ""]
    result = "\n".join(lines)
    return _clamp_navigation_artifact(
        result,
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def code_index_md(course_meta: dict, entries: List[FileEntry] = None, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    prof_entries = [e for e in entries if e.category == "codigo-professor"]
    profile = _code_review_profile(course_meta, subject_profile)
    lines = [
        f"# CODE_INDEX — {course_name}", "",
        profile["code_index_intro"],
        profile["code_index_review_line"], "",
    ]
    if prof_entries:
        lines += [
            profile["code_index_section"], "",
            "| Arquivo | Linguagem | Unidade | Conceito demonstrado | Notas |",
            "|---|---|---|---|---|",
        ]
        for e in prof_entries:
            conceito = e.professor_signal or "[a preencher]"
            unit_str = ""
            if e.notes and "Unidade:" in e.notes:
                try:
                    unit_str = e.notes.split("Unidade:")[1].strip()
                except (IndexError, AttributeError):
                    pass
            lines.append(
                f"| {Path(e.source_path).name} "
                f"| {e.tags or ''} "
                f"| {unit_str} "
                f"| {conceito} "
                f"| |"
            )
        lines.append("")
    else:
        lines += [profile["code_index_empty"], ""]
    lines += [
        profile["code_index_patterns"], "",
        "<!-- Preencha conforme analisar o código -->",
        "- [a preencher]", "",
    ]
    result = "\n".join(lines)
    return _clamp_navigation_artifact(
        result,
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def whiteboard_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# WHITEBOARD_INDEX — {course_name}", "",
             "> Fotos de quadro branco com explicações do professor.", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |",
                  "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} "
                         f"| {e.tags or ''} | {e.professor_signal or ''} |")
    else:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |",
                  "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões pedagógicos", "",
              "- [a preencher]", ""]
    result = "\n".join(lines)
    return _clamp_navigation_artifact(
        result,
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


# ---------------------------------------------------------------------------
# Free functions — existing templates (unchanged)
# ---------------------------------------------------------------------------

def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.
Plataforma alvo: **Claude Projects** (claude.ai)

## Como usar com Claude

1. Crie um **Projeto** no Claude.ai com o nome desta disciplina
2. Cole o conteúdo de `setup/INSTRUCOES_CLAUDE_PROJETO.md` no campo **Instructions** do Projeto
3. Conecte este repositório GitHub ao Projeto (aba Settings → GitHub)
4. Inicie uma conversa — o Claude lerá os arquivos automaticamente

## Estrutura
- `system/` — política do tutor, pedagogia, modos, templates
- `course/` — identidade, mapa, cronograma, glossário, bibliografia
- `student/` — estado atual, perfil, schema de progresso
- `content/` — material de aula curado
- `exercises/` — listas de exercícios
- `exams/` — provas anteriores e gabaritos
- `raw/` — materiais originais (PDFs, imagens)
- `staging/` — extração automática (para revisão)
- `manual-review/` — revisão humana guiada
- `build/claude-knowledge/` — bundle para upload manual se necessário

## Arquivos-chave para o tutor

| Arquivo | Função |
|---|---|
| `setup/INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto (não indexado pelo tutor) |
| `student/STUDENT_STATE.md` | Estado atual do aluno — atualizar após cada sessão |
| `course/COURSE_MAP.md` | Preencher com os tópicos em ordem |
| `course/GLOSSARY.md` | Preencher com terminologia da disciplina |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |

## Fluxo recomendado

1. Rodar extração automática no app
2. Revisar `manual-review/`
3. Promover conteúdo curado para `content/`, `exercises/`, `exams/`
4. Preencher `COURSE_MAP.md` e `GLOSSARY.md`
5. Conectar ao Projeto no Claude.ai
6. Após cada sessão de estudo: atualizar `student/STUDENT_STATE.md` e fazer push
"""


def wrap_frontmatter(meta: dict, body: str) -> str:
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str(v)}")
    header.append("---")
    header.append("")
    return "\n".join(header) + body.strip() + "\n"


def rows_to_markdown_table(rows: list) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    fixed = [r + [""] * (width - len(r)) for r in rows]
    header = fixed[0]
    sep = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in fixed[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def manual_pdf_review_template(entry: FileEntry, item: Dict[str, object]) -> str:
    report = item.get("document_report") or {}
    decision = item.get("pipeline_decision") or {}
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_pdf_review
category: {entry.category}
source_pdf: {json_str(item.get('raw_target'))}
processing_mode: {json_str(entry.processing_mode)}
document_profile: {json_str(entry.document_profile)}
page_range: {json_str(entry.page_range)}
effective_profile: {json_str(item.get('effective_profile'))}
base_backend: {json_str(item.get('base_backend'))}
advanced_backend: {json_str(item.get('advanced_backend'))}
base_markdown: {json_str(item.get('base_markdown'))}
advanced_markdown: {json_str(item.get('advanced_markdown'))}
---

# Revisão Manual — {entry.title}

## Perfil detectado
- Perfil efetivo: `{item.get('effective_profile')}`
- Páginas: `{report.get('page_count')}`
- Texto: `{report.get('text_chars')}` chars
- Imagens: `{report.get('images_count')}`
- Tabelas: `{report.get('table_candidates')}`
- Scan: `{report.get('suspected_scan')}`

## Pipeline
- Modo: `{decision.get('processing_mode')}`
- Base: `{decision.get('base_backend')}`
- Avançado: `{decision.get('advanced_backend')}`

## Checklist
- [ ] Conferir títulos e subtítulos
- [ ] Corrigir ordem de leitura
- [ ] Revisar fórmulas e converter para LaTeX
- [ ] Revisar tabelas exportadas
- [ ] Verificar imagens/figuras importantes
- [ ] Registrar pistas sobre o professor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `exercises/lists/`
- [ ] `exams/past-exams/`
"""


def manual_image_review_template(entry: FileEntry, raw_target: Path, root_dir: Path) -> str:
    image_path = safe_rel(raw_target, root_dir)
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_image_review
category: {entry.category}
source_image: {json_str(image_path)}
---

# Revisão Manual — Imagem

## Metadados
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Sinal do professor: `{entry.professor_signal}`

## Transcrição fiel
<!-- Escreva o texto da imagem aqui -->

## Destino curado sugerido
- [ ] `exams/past-exams/`
- [ ] `content/curated/`
"""


def manual_url_review_template(entry: FileEntry, item: Dict[str, object]) -> str:
    source_url = entry.source_path
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_url_review
category: {entry.category}
source_url: {json_str(source_url)}
processing_mode: {json_str(entry.processing_mode)}
base_backend: {json_str(item.get('base_backend'))}
base_markdown: {json_str(item.get('base_markdown'))}
---

# Revisão Manual — Página Web

## Origem
- URL: <{source_url}>
- Backend base: `{item.get('base_backend')}`

## Checklist
- [ ] Conferir se o conteúdo baixado corresponde à página correta
- [ ] Remover navegação, rodapé, anúncios e texto irrelevante
- [ ] Corrigir títulos e hierarquia de seções
- [ ] Verificar se links importantes foram preservados
- [ ] Destacar trechos úteis para o tutor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `course/references/`
"""


def migrate_legacy_url_manual_reviews(root_dir: Path) -> int:
    """Move legacy URL review templates from manual-review/pdfs to manual-review/web."""
    manual_pdfs_dir = root_dir / "manual-review" / "pdfs"
    manual_web_dir = root_dir / "manual-review" / "web"
    if not manual_pdfs_dir.exists():
        return 0

    ensure_dir(manual_web_dir)
    manifest_path = root_dir / "manifest.json"
    manifest = None
    manifest_changed = False
    moved = 0

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read manifest.json during URL review migration: %s", exc)
            manifest = None

    for review_path in manual_pdfs_dir.rglob("*.md"):
        try:
            content = review_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        fm = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split("\n"):
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip().strip('"').strip("'")

        if fm.get("type") != "manual_url_review" and fm.get("base_backend") != "url_fetcher":
            continue

        destination = manual_web_dir / review_path.name
        if destination.exists():
            try:
                review_path.unlink()
            except Exception as exc:
                logger.warning("Could not remove duplicate legacy URL review %s: %s", review_path, exc)
            else:
                moved += 1
            continue

        ensure_dir(destination.parent)
        try:
            shutil.move(str(review_path), str(destination))
        except Exception as exc:
            logger.warning("Could not migrate legacy URL review %s: %s", review_path, exc)
            continue

        moved += 1
        entry_id = fm.get("id") or destination.stem
        if manifest:
            for entry in manifest.get("entries", []):
                if entry.get("id") == entry_id and entry.get("manual_review"):
                    old_rel = safe_rel(review_path, root_dir)
                    if entry.get("manual_review") == old_rel:
                        entry["manual_review"] = safe_rel(destination, root_dir)
                        manifest_changed = True
                    break

    if manifest and manifest_changed:
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

    return moved


def pdf_curation_guide() -> str:
    return """# PDF_CURATION_GUIDE

## Regra central
PDF bruto não é conhecimento final.
Ele é insumo para:
1. extração automática
2. revisão manual
3. curadoria por função pedagógica

## Quando usar cada camada
- Base: PDFs simples, texto corrido, listas e cronogramas.
- Avançada: fórmulas, tabelas difíceis, layout complexo, scans, provas.
- Manual assisted: qualquer material que influencie a lógica de prova.

## Artefatos gerados
- `raw/`: arquivo original
- `staging/`: extração automática
- `manual-review/`: revisão humana guiada
- `content/` e `exams/`: conhecimento curado

## Destino final no Claude Project
Todo arquivo curado deve estar em formato Markdown limpo
para ser lido eficientemente pelo Claude via integração GitHub.
"""


def backend_architecture_md() -> str:
    return """# BACKEND_ARCHITECTURE

## Visão geral
A V3 usa arquitetura de backends em camadas.

```text
PDF bruto
 -> camada base
 -> camada avançada (quando necessário)
 -> extração de artefatos
 -> revisão manual guiada
 -> conteúdo curado
 -> Claude Project (via GitHub sync)
```

## Camada base
- `pymupdf4llm`: Markdown rápido para PDFs digitais.
- `pymupdf`: fallback bruto.

## Camada avançada
- `docling`: OCR, fórmulas, tabelas e imagens referenciadas.
- `marker`: equações, inline math, tabelas e imagens.

## Modos de processamento
- `quick`: só camada base.
- `high_fidelity`: base + avançada.
- `manual_assisted`: base + artefatos + revisão humana.
- `auto`: decide pelo perfil do documento.

## Regra de ouro
O tutor não deve consumir o PDF bruto como fonte final.
A fonte final deve ser o Markdown curado derivado da revisão manual,
sincronizado com o Claude Project via GitHub.
"""


def backend_policy_yaml(options: Dict[str, object]) -> str:
    return f"""version: 3
target_platform: claude-projects
policy:
  default_processing_mode: {options.get('default_processing_mode', 'auto')}
  default_ocr_language: {json_str(options.get('default_ocr_language', DEFAULT_OCR_LANGUAGE))}
  require_manual_review_for:
    - math_heavy
    - scanned
    - diagram_heavy
  base_layer_priority:
    - pymupdf4llm
    - pymupdf
  advanced_layer_priority:
    - docling
    - marker
  asset_pipeline:
    extract_images: true
    extract_tables: true
  promotion_rule: |
    Nenhum arquivo de staging é conhecimento final.
    O conhecimento final deve sair de manual-review/ e depois ser promovido
    para content/, exercises/ ou exams/, e então sincronizado com o Claude Project.
"""


def _low_token_course_map_md(course_meta: dict, subject_profile=None) -> str:
    return render_low_token_course_map_md(
        course_meta,
        subject_profile,
        build_file_map_timeline_context_from_course=_build_file_map_timeline_context_from_course,
        aggregate_unit_periods_from_blocks=_aggregate_unit_periods_from_blocks,
        normalize_unit_slug=_normalize_unit_slug,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text,
        topic_depth=_topic_depth,
        build_assessment_context_from_course=_build_assessment_context_from_course,
        assessment_conflict_section_lines=_assessment_conflict_section_lines,
        clamp_navigation_artifact=_clamp_navigation_artifact,
        logger=logger,
    )


def _low_token_file_map_md(course_meta: dict, manifest_entries: list, subject_profile=None) -> str:
    return render_low_token_file_map_md(
        course_meta,
        manifest_entries,
        subject_profile,
        build_file_map_content_taxonomy_from_course=_build_file_map_content_taxonomy_from_course,
        build_file_map_unit_index_from_course=_build_file_map_unit_index_from_course,
        build_file_map_timeline_context_from_course=_build_file_map_timeline_context_from_course,
        iter_content_taxonomy_topics=_iter_content_taxonomy_topics,
        merge_manual_and_auto_tags=_merge_manual_and_auto_tags,
        resolve_entry_manual_timeline_block=_resolve_entry_manual_timeline_block,
        entry_markdown_text_for_file_map=_entry_markdown_text_for_file_map,
        auto_map_entry_subtopic=_auto_map_entry_subtopic,
        resolve_entry_manual_unit_slug=_resolve_entry_manual_unit_slug,
        unit_match_result_factory=UnitMatchResult,
        derive_unit_from_topic_match=_derive_unit_from_topic_match,
        auto_map_entry_unit=lambda entry, unit_index, markdown_text, topic_index: _auto_map_entry_unit(
            entry,
            unit_index,
            markdown_text,
            topic_index=topic_index,
        ),
        select_probable_period_for_entry=_select_probable_period_for_entry,
        file_map_markdown_cell=_file_map_markdown_cell,
        entry_markdown_path_for_file_map=_entry_markdown_path_for_file_map,
        get_entry_sections=_get_entry_sections,
        infer_unit_confidence=_infer_unit_confidence,
        entry_usage_hint=_entry_usage_hint,
        entry_priority_label=_entry_priority_label,
        clamp_navigation_artifact=_clamp_navigation_artifact,
    )


def _budgeted_file_map_md(course_meta: dict, manifest_entries: list, subject_profile=None) -> str:
    return _clamp_navigation_artifact(
        _low_token_file_map_md(
            course_meta,
            _filter_live_manifest_entries(course_meta.get("_repo_root"), manifest_entries),
            subject_profile=subject_profile,
        ),
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def _low_token_course_map_md_v2(course_meta: dict, subject_profile=None) -> str:
    return render_low_token_course_map_md_v2(
        course_meta,
        subject_profile,
        render_low_token_course_map_md_fn=_low_token_course_map_md,
    )


def _exercise_index_md_v2(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [
        f"# EXERCISE_INDEX â€” {course_name}",
        "",
        "> **Como usar:** Índice operacional de prática da disciplina.",
        "> O tutor consulta este arquivo para localizar listas, provas antigas",
        "> e recursos de exercícios por unidade, prioridade e finalidade.",
        "",
        "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |",
        "|---|---|---|---|---|---|",
    ]
    if entries:
        for entry in entries:
            notes = _collapse_ws(entry.notes or "")
            tags = _collapse_ws(
                _merge_manual_and_auto_tags(
                    list(entry.manual_tags or []),
                    list(entry.auto_tags or []),
                    fallback_tags=entry.tags or "",
                    limit=3,
                )
            )
            category = _collapse_ws(entry.category or "")
            category_lower = category.lower()
            kind = "prova" if "prova" in category_lower else "lista" if "lista" in category_lower else "exercício"
            has_solution = "sim" if any(token in notes.lower() for token in ["gabarito", "resolu", "soluç"]) else "não"
            priority = "alta" if "prova" in category_lower or has_solution == "sim" else "média"
            usage = "revisão de prova" if "prova" in category_lower else "fixação por unidade"
            lines.append(
                f"| {entry.title} | {kind} | {tags or 'não mapeado'} | {has_solution} | {priority} | {usage} |"
            )
    else:
        lines.append("| [a preencher] | | | | | |")
        lines += [
            "",
            "> Adicione listas ou provas antigas para o tutor conseguir sugerir prática com baixo custo de contexto.",
        ]
    lines.append("")
    result = "\n".join(lines)
    return _clamp_navigation_artifact(
        result,
        max_chars=14000,
        label="exercises/EXERCISE_INDEX.md",
    )


def course_map_md(course_meta: dict, subject_profile=None) -> str:
    return _clamp_navigation_artifact(
        _low_token_course_map_md_v2(course_meta, subject_profile),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def file_map_md(course_meta: dict, manifest_entries: list, subject_profile=None) -> str:
    return _budgeted_file_map_md(course_meta, manifest_entries, subject_profile)


def exercise_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    return _exercise_index_md_v2(course_meta, entries)


