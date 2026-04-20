from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.builder.core.semantic_config import (
    infer_semantic_profile,
    merge_semantic_profile,
    resolve_semantic_profile,
    write_internal_semantic_profile,
)
from src.utils.helpers import slugify, write_text


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _normalize_match_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = normalized.replace("—", "-").replace("–", "-")
    normalized = re.sub(r"[^a-z0-9+\-./\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _strip_outline_prefix(text: str) -> str:
    cleaned = _collapse_ws(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", cleaned)
    return cleaned.strip()


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
    known_tools = sorted(list(effective_profile.get("known_tools") or []), key=len, reverse=True)
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
        if overlap == base_tokens and len(candidate_extra) <= 1:
            return True
        if overlap == candidate_tokens and len(base_extra) <= 1:
            return True
    return False


def build_tag_catalog(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
) -> dict:
    tags = set()
    heading_text = "\n".join(f"## {heading}" for heading in (strong_headings or []))
    base_topic_candidates = _extract_topic_candidates(
        teaching_plan, course_map_md, glossary_md, semantic_profile=semantic_profile
    )
    heading_topic_candidates = _extract_topic_candidates(heading_text, semantic_profile=semantic_profile)

    for raw_topic in base_topic_candidates:
        slug = slugify(raw_topic)
        if slug and _is_valid_topic_candidate(raw_topic, semantic_profile=semantic_profile):
            tags.add(f"topico:{slug}")

    for raw_topic in heading_topic_candidates:
        slug = slugify(raw_topic)
        if not slug or not _is_valid_topic_candidate(raw_topic, semantic_profile=semantic_profile):
            continue
        if base_topic_candidates and not _heading_topic_has_vocab_support(
            raw_topic, base_topic_candidates, semantic_profile=semantic_profile
        ):
            continue
        tags.add(f"topico:{slug}")

    for tool_name in _extract_tool_candidates(heading_text, semantic_profile=semantic_profile):
        slug = slugify(tool_name)
        if slug:
            tags.add(f"ferramenta:{slug}")

    return {"version": 1, "tags": sorted(tags)}


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
                dict.fromkeys(_collapse_ws(item) for item in current.get("synonyms", []) if _collapse_ws(item))
            )
            terms.append(current)
        current = None

    for raw_line in (glossary_md or "").splitlines():
        line = _collapse_ws(raw_line)
        if not line:
            continue
        if line.startswith("## "):
            _flush()
            current = {"term": _collapse_ws(line[3:]), "unit_hint": "", "synonyms": [], "definition": ""}
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
        current = merged.setdefault(
            slug,
            {
                "code": str(topic.get("code", "") or ""),
                "slug": str(topic.get("slug", "") or ""),
                "label": _collapse_ws(str(topic.get("label", "") or "")),
                "aliases": [],
                "kind": str(topic.get("kind", "") or "topic"),
                "unit_slug": str(topic.get("unit_slug", "") or ""),
            },
        )
        current["code"] = current["code"] or str(topic.get("code", "") or "")
        current["label"] = current["label"] or _collapse_ws(str(topic.get("label", "") or ""))
        current["kind"] = current["kind"] or str(topic.get("kind", "") or "topic")
        current["unit_slug"] = current["unit_slug"] or str(topic.get("unit_slug", "") or "")
        existing_aliases = {slugify(item) for item in current["aliases"]}
        for alias in topic.get("aliases", []) or []:
            alias_text = _collapse_ws(str(alias))
            alias_slug = slugify(alias_text)
            if alias_text and alias_slug and alias_slug not in existing_aliases:
                current["aliases"].append(alias_text)
                existing_aliases.add(alias_slug)
    for topic in merged.values():
        topic["aliases"] = sorted(dict.fromkeys(alias for alias in topic.get("aliases", []) if _collapse_ws(alias)))
    return list(merged.values())


def _infer_course_slug_from_units(units: List[tuple]) -> str:
    if not units:
        return ""
    first_title = _strip_outline_prefix(units[0][0] if isinstance(units[0], tuple) else str(units[0].get("title", "")))
    first_title = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", first_title, flags=re.IGNORECASE)
    return slugify(first_title)


def build_content_taxonomy(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[List[str]] = None,
    semantic_profile: Optional[dict] = None,
    *,
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    normalize_unit_slug: Callable[[str], str],
) -> dict:
    units = parse_units_from_teaching_plan(teaching_plan or "")
    if not units and course_map_md:
        units = parse_units_from_teaching_plan(course_map_md)

    glossary_terms = _parse_glossary_terms(glossary_md or "")
    heading_sources = [heading for heading in (strong_headings or []) if _collapse_ws(heading)]

    result_units = []
    for unit_title, topics in units:
        unit_slug = normalize_unit_slug(unit_title)
        topic_records = []
        for topic in topics or []:
            current_topic_text = _collapse_ws(_strip_topic_code(topic_text(topic)))
            if not current_topic_text:
                continue
            topic_code = _extract_topic_code(topic_text(topic))
            topic_slug = slugify(current_topic_text)
            aliases = _glossary_aliases_for_topic(current_topic_text, unit_title, glossary_terms)
            topic_kind = "subtopic" if topic_code.count(".") >= 2 else "topic"
            topic_records.append(
                {
                    "code": topic_code,
                    "slug": topic_slug,
                    "label": current_topic_text,
                    "aliases": aliases,
                    "kind": topic_kind,
                    "unit_slug": unit_slug,
                }
            )

        result_units.append({"slug": unit_slug, "title": unit_title, "topics": _dedupe_taxonomy_topics(topic_records)})

    for heading in heading_sources:
        heading_text = _collapse_ws(_strip_topic_code(heading))
        heading_slug = slugify(heading_text)
        if not heading_text or not heading_slug:
            continue
        best_unit: Optional[dict] = None
        best_topic: Optional[dict] = None
        best_score = 0.0
        for unit in result_units:
            candidate_topic = _select_supported_taxonomy_topic(
                heading_text,
                unit.get("topics", []) or [],
                semantic_profile=semantic_profile,
            )
            if not candidate_topic:
                continue
            topic_score = 0.0
            base_norm = _normalize_match_text(str(candidate_topic.get("label", "") or ""))
            heading_norm = _normalize_match_text(heading_text)
            if heading_norm == base_norm:
                topic_score = 10.0
            elif heading_norm in base_norm or base_norm in heading_norm:
                topic_score = 8.0
            else:
                overlap = _topic_support_tokens(heading_text) & _topic_support_tokens(str(candidate_topic.get("label", "") or ""))
                topic_score = 5.0 + (0.4 * len(overlap))
            if topic_score > best_score:
                best_score = topic_score
                best_unit = unit
                best_topic = candidate_topic
        if best_topic and best_unit:
            aliases = list(best_topic.get("aliases", []) or [])
            if heading_text not in aliases and slugify(heading_text) != slugify(str(best_topic.get("label", "") or "")):
                aliases.append(heading_text)
            best_topic["aliases"] = aliases
            best_unit["topics"] = _dedupe_taxonomy_topics(list(best_unit.get("topics", []) or []))

    return {"version": 1, "course_slug": _infer_course_slug_from_units(units), "units": result_units}


def write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
    write_text(root_dir / "course" / ".content_taxonomy.json", json.dumps(taxonomy, ensure_ascii=False, indent=2))


def extract_markdown_lead_text(markdown_text: str, max_chars: int = 2600) -> str:
    stripped = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", markdown_text or "", flags=re.DOTALL)
    compact = _collapse_ws(stripped)
    if len(compact) <= max_chars:
        return compact
    clipped = compact[:max_chars]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.strip()


def collect_strong_heading_candidates(root_dir: Optional[Path], manifest_entries: Optional[List[dict]]) -> List[str]:
    if not root_dir:
        return []
    headings: List[str] = []
    seen = set()
    for entry in manifest_entries or []:
        for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
            rel_path = (entry.get(key) or "").replace("\\", "/")
            if not rel_path or rel_path.startswith("staging/"):
                continue
            md_path = root_dir / rel_path
            if not md_path.exists() or not md_path.is_file():
                continue
            try:
                file_headings = _extract_markdown_headings(md_path.read_text(encoding="utf-8"))
            except Exception:
                file_headings = []
            for heading in file_headings[:4]:
                heading_slug = slugify(heading)
                if heading_slug and heading_slug not in seen:
                    seen.add(heading_slug)
                    headings.append(heading)
            break
    return headings


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
    return {token for token in _normalize_match_text(signal_text).split() if len(token) >= 4}


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


def _is_exam_review_signal(signal_text: str) -> bool:
    normalized = _normalize_match_text(signal_text)
    if not normalized:
        return False

    review_cues = (
        "revisao",
        "revisao para prova",
        "revisao de prova",
        "preparacao para prova",
        "preparacao de prova",
        "preparatorio para prova",
        "simulado",
    )
    exam_cues = (
        "prova",
        "exame",
        "avaliacao",
        "teste",
        "p1",
        "p2",
        "p3",
        "pf",
        "av1",
        "av2",
        "n1",
        "n2",
    )

    has_review = any(cue in normalized for cue in review_cues)
    has_exam = any(re.search(rf"(?<![a-z0-9]){re.escape(cue)}(?![a-z0-9])", normalized) for cue in exam_cues)
    return has_review and has_exam


def infer_entry_auto_tags(entry: dict, markdown_text: str, vocabulary: dict) -> List[str]:
    title_text = _normalize_match_text(entry.get("title", ""))
    raw_target_text = _normalize_match_text(entry.get("raw_target", ""))
    markdown_headings_text = _normalize_match_text(" ".join(_extract_markdown_headings(markdown_text)))
    strong_signal_text = " ".join(part for part in [title_text, markdown_headings_text] if part)
    review_signal_text = " ".join(part for part in [title_text, raw_target_text, markdown_headings_text] if part)
    catalog_tags = list(vocabulary.get("tags") or [])
    inferred: List[str] = []
    seen = set()

    def _append(tag: str) -> None:
        if tag and tag not in seen:
            inferred.append(tag)
            seen.add(tag)

    for tag in catalog_tags:
        if not isinstance(tag, str) or ":" not in tag:
            continue
        prefix, slug = tag.split(":", 1)
        if prefix not in {"topico", "ferramenta"}:
            continue
        normalized_slug = _normalize_match_text(slug.replace("-", " "))
        slug_tokens = [tok for tok in normalized_slug.split() if len(tok) >= 4]
        if prefix == "topico" and len(slug_tokens) == 1:
            if len(slug_tokens[0]) < 5:
                continue
            strong_hits = slug_tokens[0] in _signal_token_set(strong_signal_text)
            if not strong_hits:
                continue
        if _matches_tag_slug(strong_signal_text, slug):
            _append(tag)

    category = _normalize_match_text(entry.get("category", ""))
    category_type_map = {
        "listas": "tipo:lista",
        "gabaritos": "tipo:gabarito",
        "provas": "tipo:prova",
        "material de aula": "tipo:material-base",
        "material-de-aula": "tipo:material-base",
        "codigo professor": "tipo:codigo",
        "codigo-professor": "tipo:codigo",
        "codigo aluno": "tipo:codigo",
        "codigo-aluno": "tipo:codigo",
    }
    for key, tag in category_type_map.items():
        if key in category:
            _append(tag)
            break

    if _is_exam_review_signal(review_signal_text):
        _append("uso:revisao-prova")

    return inferred[:6]


def write_tag_catalog(
    root_dir: Path,
    *,
    course_name: str,
    teaching_plan: str,
    course_map_text: str,
    glossary_text: str,
    manifest_entries: Optional[List[dict]],
) -> dict:
    catalog_path = root_dir / "course" / ".tag_catalog.json"
    strong_headings = collect_strong_heading_candidates(root_dir, manifest_entries)
    semantic_profile = resolve_semantic_profile(
        root_dir=root_dir,
        course_name=course_name,
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
    )
    write_internal_semantic_profile(
        root_dir,
        infer_semantic_profile(
            course_name=course_name,
            teaching_plan=teaching_plan,
            course_map_md=course_map_text,
            glossary_md=glossary_text,
            strong_headings=strong_headings,
        ),
    )

    existing_manual_tags: List[str] = []
    if catalog_path.exists():
        try:
            existing_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            existing_manual_tags = [
                str(tag).strip()
                for tag in (existing_payload.get("manual_tags") or [])
                if str(tag).strip()
            ]
        except Exception:
            existing_manual_tags = []

    generated = build_tag_catalog(
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
    )
    auto_tags = list(generated.get("tags") or [])
    merged: List[str] = []
    seen = set()
    for tag in existing_manual_tags + auto_tags:
        value = str(tag).strip()
        if not value or value in seen:
            continue
        merged.append(value)
        seen.add(value)

    catalog = {
        "version": 2,
        "scope": {
            "course_name": course_name or root_dir.name,
            "course_slug": slugify(course_name or root_dir.name),
        },
        "manual_tags": existing_manual_tags,
        "auto_tags": auto_tags,
        "tags": merged,
    }
    write_text(catalog_path, json.dumps(catalog, indent=2, ensure_ascii=False))
    return catalog


def refresh_manifest_auto_tags(
    root_dir: Path,
    manifest_entries: List[dict],
    vocabulary: dict,
    *,
    entry_markdown_text_for_file_map: Callable[[Path, dict], str],
) -> List[dict]:
    refreshed: List[dict] = []
    for entry in manifest_entries or []:
        item = dict(entry)
        manual_tags = item.get("manual_tags") or []
        if not manual_tags:
            raw_tags = str(item.get("tags", "") or "").strip()
            if raw_tags and ":" in raw_tags:
                manual_tags = [part.strip() for part in raw_tags.replace(",", ";").split(";") if part.strip()]
        item["manual_tags"] = list(manual_tags)
        markdown_text = entry_markdown_text_for_file_map(root_dir, item)
        item["auto_tags"] = infer_entry_auto_tags(item, markdown_text, vocabulary)
        refreshed.append(item)
    return refreshed
