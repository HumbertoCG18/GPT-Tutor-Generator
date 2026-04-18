from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class UnitMatchResult:
    slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)


def build_file_map_unit_index(
    units: list,
    *,
    normalize_match_text: Callable[[str], str],
    normalize_unit_slug: Callable[[str], str],
    strip_outline_prefix: Callable[[str], str],
    topic_text: Callable[[object], str],
    unit_generic_tokens: set[str],
) -> list:
    indexed = []
    for unit in units or []:
        if isinstance(unit, dict):
            title = unit.get("title", "")
            topics = unit.get("topics", []) or []
            extra_signals = unit.get("extra_signals", []) or []
        else:
            title, topics = unit
            extra_signals = []
        clean_title = strip_outline_prefix(title)
        topic_phrases = []
        topic_tokens = []
        seen_topic_tokens = set()
        for topic in list(topics) + list(extra_signals):
            topic_norm = normalize_match_text(strip_outline_prefix(topic_text(topic)))
            if not topic_norm:
                continue
            topic_phrases.append(topic_norm)
            if topic_norm not in seen_topic_tokens:
                topic_tokens.append(topic_norm)
                seen_topic_tokens.add(topic_norm)
            for token in topic_norm.split():
                if len(token) >= 4 and token not in seen_topic_tokens and token not in unit_generic_tokens:
                    topic_tokens.append(token)
                    seen_topic_tokens.add(token)
        indexed.append({
            "title": title,
            "slug": normalize_unit_slug(title),
            "normalized_title": normalize_match_text(clean_title),
            "topics": topics,
            "extra_signals": extra_signals,
            "topic_phrases": topic_phrases,
            "topic_tokens": topic_tokens,
            "title_anchor_tokens": [
                token
                for token in normalize_match_text(clean_title).split()
                if len(token) >= 4 and token not in {"unidade", "aprendizagem", "verificacao"}
            ],
            "topic_anchor_tokens": [
                token
                for token in {token for text in topic_phrases for token in text.split()}
                if len(token) >= 4 and token not in {"de", "para", "com", "sem", "sobre", "entre"}
            ],
            "distinctive_tokens": [],
        })

    token_frequency = {}
    for unit in indexed:
        unit_tokens = set()
        for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
            for token in text.split():
                if len(token) >= 4 and not token.isdigit() and token not in unit_generic_tokens:
                    unit_tokens.add(token)
        for token in unit_tokens:
            token_frequency[token] = token_frequency.get(token, 0) + 1

    for unit in indexed:
        unit_tokens = set()
        for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
            for token in text.split():
                if len(token) >= 4 and not token.isdigit() and token not in unit_generic_tokens:
                    unit_tokens.add(token)
        unit["token_weights"] = {
            token: 1.0 / token_frequency[token]
            for token in unit_tokens
            if token_frequency.get(token)
        }
        unit["distinctive_tokens"] = sorted(
            token
            for token, freq in token_frequency.items()
            if freq == 1 and token in unit_tokens and len(token) >= 5
        )
    return indexed


def auto_map_entry_subtopic(
    entry: dict,
    taxonomy: dict,
    markdown_text: str,
    *,
    collect_entry_unit_signals: Callable[[dict, str], dict],
    iter_content_taxonomy_topics: Callable[[dict], List[dict]],
    score_entry_against_taxonomy_topic: Callable[[dict, dict], float],
    topic_match_result_factory,
):
    topic_index = iter_content_taxonomy_topics(taxonomy)
    if not topic_index:
        return topic_match_result_factory(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=["sem-taxonomia"],
        )

    signals = collect_entry_unit_signals(entry, markdown_text)
    scored = [(topic, score_entry_against_taxonomy_topic(signals, topic)) for topic in topic_index]
    scored.sort(key=lambda item: item[1], reverse=True)

    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.2)))
    ambiguous = winner_score <= 0.0 if len(scored) == 1 else winner_score <= 0.0 or abs(winner_score - runner_up_score) < 0.65
    if len(scored) == 1 and not ambiguous:
        confidence = max(confidence, 0.72)
    if ambiguous:
        confidence = min(confidence, 0.45)

    reasons = [f"winner_score={winner_score:.2f}"] + (["ambiguous"] if ambiguous else [])
    return topic_match_result_factory(
        topic_slug=str(winner.get("topic_slug", "") or ""),
        topic_label=str(winner.get("topic_label", "") or ""),
        unit_slug=str(winner.get("unit_slug", "") or ""),
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=reasons,
    )


def score_entry_against_unit(
    signals: dict,
    unit: dict,
    *,
    score_timeline_unit_phrase: Callable[[str, set[str], str, dict], float],
    timeline_unit_neutral_tokens: set[str],
) -> float:
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
    title_tokens = {tok for tok in title_text.split() if len(tok) >= 4}
    markdown_headings_tokens = {tok for tok in markdown_headings_text.split() if len(tok) >= 4}
    markdown_lead_tokens = {tok for tok in markdown_lead_text.split() if len(tok) >= 4}
    markdown_tokens = {tok for tok in markdown_text.split() if len(tok) >= 4}
    manual_tags_tokens = {tok for tok in manual_tags_text.split() if len(tok) >= 4}
    auto_tags_tokens = {tok for tok in auto_tags_text.split() if len(tok) >= 4}
    legacy_tags_tokens = {tok for tok in legacy_tags_text.split() if len(tok) >= 4}
    tags_tokens = {tok for tok in tags_text.split() if len(tok) >= 4}
    raw_tokens = {tok for tok in raw_text.split() if len(tok) >= 4}

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
        score += score_timeline_unit_phrase(markdown_headings_text, markdown_headings_tokens, topic_phrase, token_weights) * 0.55
        score += score_timeline_unit_phrase(markdown_lead_text, markdown_lead_tokens, topic_phrase, token_weights) * 0.48
        score += score_timeline_unit_phrase(markdown_text, markdown_tokens, topic_phrase, token_weights) * 0.18
        score += score_timeline_unit_phrase(title_text, title_tokens, topic_phrase, token_weights) * 0.45
        score += score_timeline_unit_phrase(manual_tags_text, manual_tags_tokens, topic_phrase, token_weights) * 0.35
        score += score_timeline_unit_phrase(auto_tags_text, auto_tags_tokens, topic_phrase, token_weights) * 0.04
        score += score_timeline_unit_phrase(legacy_tags_text, legacy_tags_tokens, topic_phrase, token_weights) * 0.02
        score += score_timeline_unit_phrase(raw_text, raw_tokens, topic_phrase, token_weights) * 0.18

    for topic_token in topic_tokens:
        if not topic_token or " " in topic_token:
            continue
        weight = token_weights.get(topic_token, 1.0)
        if topic_token in timeline_unit_neutral_tokens:
            weight *= 0.2
        if topic_token in markdown_tokens:
            score += 0.32 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in markdown_lead_tokens:
            score += 0.7 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in markdown_headings_tokens:
            score += 0.8 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in title_tokens:
            score += 0.55 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in manual_tags_tokens:
            score += 0.45 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in auto_tags_tokens:
            score += 0.05 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in legacy_tags_tokens:
            score += 0.02 * weight
            if topic_token not in timeline_unit_neutral_tokens:
                matched_specific_tokens.add(topic_token)
        if topic_token in raw_tokens:
            score += 0.2 * weight
            if topic_token not in timeline_unit_neutral_tokens:
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


def auto_map_entry_unit(
    entry: dict,
    units: list,
    markdown_text: str,
    *,
    topic_index: Optional[List[dict]] = None,
    build_file_map_unit_index: Callable[[list], list],
    collect_entry_unit_signals: Callable[[dict, str], dict],
    score_entry_against_unit: Callable[[dict, dict], float],
    normalize_unit_slug: Callable[[str], str],
    score_entry_against_taxonomy_topic: Callable[[dict, dict], float],
    unit_match_result_factory=UnitMatchResult,
) -> UnitMatchResult:
    indexed_units = build_file_map_unit_index(units)
    if not indexed_units:
        return unit_match_result_factory(slug="", confidence=0.0, ambiguous=True, reasons=["sem-unidades"])

    signals = collect_entry_unit_signals(entry, markdown_text)
    scored = []
    normalized_topic_index = list(topic_index or [])
    for unit in indexed_units:
        score = score_entry_against_unit(signals, unit)
        best_topic_score = 0.0
        if normalized_topic_index:
            unit_slug = normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
            for topic in normalized_topic_index:
                if normalize_unit_slug(str(topic.get("unit_slug", "") or "")) != unit_slug:
                    continue
                topic_score = score_entry_against_taxonomy_topic(signals, topic)
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
    ambiguous = winner_score <= 0.0 if len(scored) == 1 else winner_score <= 0.0 or abs(winner_score - runner_up_score) < 0.8
    if len(scored) == 1 and not ambiguous:
        confidence = max(confidence, 0.7)
    if (
        len(scored) > 1
        and normalized_topic_index
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
    return unit_match_result_factory(
        slug=winner["slug"],
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=reasons,
    )


def format_file_map_unit_cell(slug: str, confidence: float, ambiguous: bool) -> str:
    if not slug:
        return ""
    if ambiguous:
        return f"{slug} _(ambíguo)_"
    if confidence < 0.45:
        return f"{slug} _(baixa confiança)_"
    return slug


def resolve_entry_manual_unit_slug(
    entry: dict,
    unit_index: list,
    *,
    normalize_unit_slug: Callable[[str], str],
) -> str:
    raw = str(entry.get("manual_unit_slug") or "").strip()
    if not raw:
        return ""
    normalized = normalize_unit_slug(raw)
    valid_slugs = {str(unit.get("slug", "")).strip() for unit in unit_index if str(unit.get("slug", "")).strip()}
    return normalized if normalized in valid_slugs else ""


def resolve_entry_manual_timeline_block(entry: dict, timeline_context: dict) -> Optional[Dict[str, object]]:
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
