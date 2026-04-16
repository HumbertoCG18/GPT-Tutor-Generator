from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Optional

from src.utils.helpers import slugify, write_text

_DEFAULTS_PATH = Path(__file__).with_name("semantic_defaults.json")
_PROFILE_LIST_KEYS = (
    "known_tools",
    "generic_slug_blacklist",
    "structural_stop_headings",
    "bibliography_markers",
    "weak_heading_starters",
    "heading_single_overlap_cues",
)
_PROFILE_DICT_KEYS = (
    "tool_aliases",
    "domain_cues",
)
_PROFILE_ALIASES = {
    "tag_generic_slugs": "generic_slug_blacklist",
    "tag_structural_headings": "structural_stop_headings",
}

_SEMANTIC_TOKEN_STOPWORDS = {
    "curso",
    "disciplina",
    "aula",
    "aulas",
    "material",
    "materiais",
    "conteudo",
    "conteudos",
    "introducao",
    "fundamentos",
    "teoria",
    "pratica",
    "revisao",
    "exercicios",
    "atividade",
    "atividades",
    "lista",
    "listas",
    "prova",
    "provas",
    "projeto",
    "projetos",
    "sistema",
    "sistemas",
    "analise",
    "estudo",
}

_TOOL_CANDIDATE_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9.+#-]{1,24}\b")
_TOOL_CONTEXT_CUES = (
    "ferramenta",
    "solver",
    "proof assistant",
    "assistente de prova",
    "framework",
    "biblioteca",
    "library",
    "parser",
    "parsers",
    "linguagem",
)


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _normalize_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    cleaned = cleaned.lower()
    cleaned = re.sub(r"[^a-z0-9#+.\-\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _ordered_unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen = set()
    for value in values:
        cleaned = _collapse_ws(str(value))
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _ordered_unique_map(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for raw_key, raw_values in value.items():
        key = _collapse_ws(str(raw_key))
        if not key:
            continue
        if isinstance(raw_values, str):
            values = [raw_values]
        else:
            values = list(raw_values or [])
        cleaned = _ordered_unique(values)
        if cleaned:
            normalized[key] = cleaned
    return normalized


def _normalize_profile_input(profile: Optional[dict]) -> dict:
    if not profile:
        return {}
    normalized = dict(profile)
    for legacy_key, canonical_key in _PROFILE_ALIASES.items():
        if canonical_key not in normalized and legacy_key in normalized:
            normalized[canonical_key] = normalized.get(legacy_key)
    return normalized


def _with_compat_aliases(profile: dict) -> dict:
    materialized = dict(profile or {})
    materialized["tag_generic_slugs"] = list(materialized.get("generic_slug_blacklist") or [])
    materialized["tag_structural_headings"] = list(materialized.get("structural_stop_headings") or [])
    return materialized


def load_semantic_defaults() -> dict:
    try:
        payload = json.loads(_DEFAULTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        payload = {"version": 1}

    defaults = {"version": int(payload.get("version") or 1), "course_slug": ""}
    normalized = _normalize_profile_input(payload)
    for key in _PROFILE_LIST_KEYS:
        defaults[key] = _ordered_unique(normalized.get(key) or [])
    for key in _PROFILE_DICT_KEYS:
        defaults[key] = _ordered_unique_map(normalized.get(key))
    defaults.setdefault("generated_from", {})
    return _with_compat_aliases(defaults)


def _extract_topicish_lines(*sources: str) -> list[str]:
    candidates: list[str] = []
    seen = set()
    for source in sources:
        for raw_line in (source or "").splitlines():
            line = _collapse_ws(raw_line)
            if not line:
                continue
            if line.startswith("### "):
                line = line[4:].strip()
            elif line.startswith("## "):
                line = line[3:].strip()
            elif line.startswith("- [ ] "):
                line = line[6:].strip()
            elif line.startswith("- "):
                line = line[2:].strip()
            else:
                continue
            line = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", line)
            line = re.sub(r"^(unidade|tema|topico)\s+\d+\s*[-—:]?\s*", "", line, flags=re.IGNORECASE)
            slug = slugify(line)
            if not slug or slug in seen:
                continue
            seen.add(slug)
            candidates.append(line)
    return candidates


def _infer_heading_overlap_cues(*sources: str) -> list[str]:
    counts: Counter[str] = Counter()
    for candidate in _extract_topicish_lines(*sources):
        normalized = _normalize_text(candidate)
        for token in normalized.split():
            if len(token) < 5:
                continue
            if token in _SEMANTIC_TOKEN_STOPWORDS:
                continue
            counts[token] += 1
    ranked = sorted(
        (
            token
            for token, count in counts.items()
            if count >= 1
        ),
        key=lambda token: (-counts[token], token),
    )
    return ranked[:24]


def _infer_tool_candidates(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
    strong_headings: Optional[list[str]] = None,
) -> list[str]:
    totals: Counter[str] = Counter()
    heading_hits: Counter[str] = Counter()
    context_hits: Counter[str] = Counter()
    display: dict[str, str] = {}
    heading_text = "\n".join(str(item) for item in (strong_headings or []) if _collapse_ws(str(item)))
    sources = [
        (teaching_plan or "", False),
        (course_map_md or "", False),
        (glossary_md or "", False),
        (heading_text, True),
    ]

    for text, is_heading in sources:
        seen_in_source = set()
        for raw_line in (text or "").splitlines():
            normalized_line = _normalize_text(raw_line)
            has_tool_context = any(cue in normalized_line for cue in _TOOL_CONTEXT_CUES)
            for match in _TOOL_CANDIDATE_RE.finditer(raw_line):
                raw = match.group(0)
                normalized = _normalize_text(raw)
                if len(normalized) < 2:
                    continue
                if normalized in _SEMANTIC_TOKEN_STOPWORDS:
                    continue
                if normalized in seen_in_source:
                    continue
                seen_in_source.add(normalized)
                totals[normalized] += 1
                if is_heading:
                    heading_hits[normalized] += 1
                if has_tool_context:
                    context_hits[normalized] += 1
                display.setdefault(normalized, raw)

    accepted: list[str] = []
    default_tools = {
        _normalize_text(tool)
        for tool in (load_semantic_defaults().get("known_tools") or [])
    }
    for normalized, count in totals.items():
        raw = display.get(normalized, normalized)
        has_special_shape = (
            any(ch in raw for ch in "+#.")
            or any(ch.isdigit() for ch in raw)
            or any(ch.isupper() for ch in raw[1:])
        )
        if normalized in default_tools:
            accepted.append(normalized)
            continue
        if has_special_shape and count >= 1:
            accepted.append(normalized)
            continue
        if context_hits.get(normalized, 0) >= 1 and count >= 2 and len(normalized) >= 3:
            accepted.append(normalized)
            continue
        if context_hits.get(normalized, 0) >= 2 and count >= 3 and 3 <= len(normalized) <= 18:
            accepted.append(normalized)

    return sorted(_ordered_unique(accepted))


def infer_semantic_profile(
    *,
    course_name: str = "",
    teaching_plan: str = "",
    course_map_md: str = "",
    glossary_md: str = "",
    strong_headings: Optional[list[str]] = None,
) -> dict:
    course_slug = slugify(course_name or "")
    generated_slugs = [course_slug] if course_slug else []
    generated_cues = _infer_heading_overlap_cues(
        teaching_plan or "",
        course_map_md or "",
        glossary_md or "",
        *list(strong_headings or []),
    )
    known_tools = _infer_tool_candidates(
        teaching_plan=teaching_plan or "",
        course_map_md=course_map_md or "",
        glossary_md=glossary_md or "",
        strong_headings=strong_headings,
    )

    return _with_compat_aliases({
        "version": 1,
        "course_slug": course_slug,
        "generated_from": {
            "strong_heading_count": len(strong_headings or []),
        },
        "known_tools": known_tools,
        "generic_slug_blacklist": _ordered_unique(generated_slugs),
        "heading_single_overlap_cues": _ordered_unique(generated_cues),
    })


def merge_semantic_profile(*profiles: Optional[dict]) -> dict:
    merged = load_semantic_defaults()
    for profile in profiles:
        if not profile:
            continue
        normalized = _normalize_profile_input(profile)
        if normalized.get("course_slug"):
            merged["course_slug"] = str(normalized.get("course_slug") or "").strip()
        if isinstance(normalized.get("generated_from"), dict):
            merged["generated_from"] = {
                **dict(merged.get("generated_from") or {}),
                **dict(normalized.get("generated_from") or {}),
            }
        for key in _PROFILE_LIST_KEYS:
            merged[key] = _ordered_unique(list(merged.get(key) or []) + list(normalized.get(key) or []))
        for key in _PROFILE_DICT_KEYS:
            current_map = dict(merged.get(key) or {})
            for item_key, item_values in _ordered_unique_map(normalized.get(key)).items():
                current_map[item_key] = _ordered_unique(list(current_map.get(item_key) or []) + list(item_values or []))
            merged[key] = current_map
    return _with_compat_aliases(merged)


def read_internal_semantic_profile(root_dir: Optional[Path]) -> dict:
    if not root_dir:
        return {}
    profile_path = root_dir / "course" / ".semantic_profile.generated.json"
    if not profile_path.exists():
        return {}
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_semantic_profile_override(root_dir: Optional[Path]) -> dict:
    if not root_dir:
        return {}
    profile_path = root_dir / "course" / ".semantic_profile.override.json"
    if not profile_path.exists():
        return {}
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_internal_semantic_profile(root_dir: Path, profile: dict) -> None:
    normalized = _normalize_profile_input(profile)
    persisted = {
        "version": int(normalized.get("version") or 1),
        "course_slug": str(normalized.get("course_slug") or "").strip(),
        "generated_from": dict(normalized.get("generated_from") or {}),
        "known_tools": _ordered_unique(normalized.get("known_tools") or []),
        "generic_slug_blacklist": _ordered_unique(normalized.get("generic_slug_blacklist") or []),
        "heading_single_overlap_cues": _ordered_unique(normalized.get("heading_single_overlap_cues") or []),
    }
    write_text(
        root_dir / "course" / ".semantic_profile.generated.json",
        json.dumps(persisted, ensure_ascii=False, indent=2),
    )


def resolve_semantic_profile(
    *,
    root_dir: Optional[Path],
    course_name: str = "",
    teaching_plan: str = "",
    course_map_md: str = "",
    glossary_md: str = "",
    strong_headings: Optional[list[str]] = None,
) -> dict:
    cached = read_internal_semantic_profile(root_dir)
    override = read_semantic_profile_override(root_dir)
    inferred = infer_semantic_profile(
        course_name=course_name,
        teaching_plan=teaching_plan,
        course_map_md=course_map_md,
        glossary_md=glossary_md,
        strong_headings=strong_headings,
    )
    return merge_semantic_profile(cached, inferred, override)
