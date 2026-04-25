from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class UnitMatchResult:
    slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)


UNIT_GENERIC_TOKENS = {
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


def strip_outline_prefix(text: str) -> str:
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


def score_entry_against_timeline_row(
    signals: dict,
    row_text: str,
    *,
    normalize_match_text: Callable[[str], str],
    score_text_against_row: Callable[[str, List[str]], float],
) -> float:
    row_norm = normalize_match_text(row_text)
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
        score += score_text_against_row(source, row_tokens, weight=weight)
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


def score_card_evidence_against_entry(
    signals: dict,
    card_items: List[Dict[str, str]],
    *,
    normalize_match_text: Callable[[str], str],
) -> float:
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
    entry_norm = normalize_match_text(entry_text)
    if not entry_norm:
        return 0.0

    entry_tokens = {tok for tok in entry_norm.split() if len(tok) >= 4}
    if not entry_tokens:
        return 0.0

    score = 0.0
    for item in card_items:
        normalized_title = normalize_match_text(str(item.get("normalized_title", "") or ""))
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


def timeline_block_rows_for_scoring(block: Dict[str, object]) -> list:
    rows = list(block.get("rows", []) or [])
    return [row for row in rows if not bool(row.get("ignored"))]


def score_timeline_block(
    signals: dict,
    block: Dict[str, object],
    *,
    normalize_match_text: Callable[[str], str],
    score_card_evidence_against_entry: Callable[[dict, List[Dict[str, str]]], float],
) -> float:
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
            row_text = normalize_match_text(str(row.get("content", "")))
            if any(term in row_text for term in ["exercicio", "exercicios", "lista", "listas", "gabarito", "respostas"]):
                generic_exercise_bonus += 0.22

    card_bonus = score_card_evidence_against_entry(signals, block.get("card_evidence", []) or [])

    return anchor_score * 1.15 + support_bonus + min(generic_exercise_bonus, 0.66) + min(card_bonus, 0.45)


def timeline_block_matches_preferred_topic(block: Dict[str, object], preferred_topic_slug: str) -> bool:
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


def score_entry_against_timeline_block(
    signals: dict,
    block: Dict[str, object],
    *,
    normalize_match_text: Callable[[str], str],
    score_text_against_row: Callable[[str, List[str]], float],
    score_card_evidence_against_entry_fn: Callable[[dict, List[Dict[str, str]]], float],
    preferred_unit_slug: str = "",
    preferred_topic_slug: str = "",
) -> float:
    rows = timeline_block_rows_for_scoring(block)
    if not rows:
        return 0.0
    row_scores = [
        score_entry_against_timeline_row(
            signals,
            str(row.get("content", "")),
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
        )
        for row in rows
    ]
    runtime_block = dict(block)
    runtime_block["rows"] = rows
    runtime_block["scores"] = row_scores
    score = score_timeline_block(
        signals,
        runtime_block,
        normalize_match_text=normalize_match_text,
        score_card_evidence_against_entry=score_card_evidence_against_entry_fn,
    )

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
        elif timeline_block_matches_preferred_topic(block, preferred_topic_slug):
            score += 0.48
        elif block_topic_slug:
            score -= 0.18

    topic_text = normalize_match_text(str(block.get("topic_text", "")))
    if topic_text:
        topic_tokens = [tok for tok in topic_text.split() if len(tok) >= 4]
        score += score_text_against_row(signals.get("manual_tags_text", ""), topic_tokens, weight=0.35)
        score += score_text_against_row(signals.get("auto_tags_text", ""), topic_tokens, weight=0.12)
        score += score_text_against_row(signals.get("legacy_tags_text", ""), topic_tokens, weight=0.05)

    score += min(score_card_evidence_against_entry_fn(signals, block.get("card_evidence", []) or []), 0.45)
    return score


def collect_entry_temporal_signals(
    entry: dict,
    markdown_text: str,
    *,
    collapse_ws: Callable[[str], str],
    normalize_match_text: Callable[[str], str],
    extract_date_range_signal: Callable[[str], dict],
    extract_timeline_session_signals: Callable[[str], List[dict]],
) -> dict:
    raw_parts = [
        str(entry.get("title", "") or ""),
        str(entry.get("raw_target", "") or ""),
        str(entry.get("category", "") or ""),
        str(entry.get("tags", "") or ""),
        markdown_text or "",
    ]
    combined_text = "\n".join(part for part in raw_parts if collapse_ws(part))
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
        "combined_text": normalize_match_text(combined_text),
        "date_range": date_range,
        "date_values": sorted(date_values),
        "session_signals": session_signals,
    }


def entry_temporal_range_contains(
    date_text: str,
    date_range: dict,
    *,
    parse_timeline_date_value: Callable[[str], object],
) -> bool:
    if not date_text or not date_range:
        return False
    session_dt = parse_timeline_date_value(date_text)
    start_dt = parse_timeline_date_value(str(date_range.get("start", "") or ""))
    end_dt = parse_timeline_date_value(str(date_range.get("end", "") or ""))
    if not session_dt or not start_dt or not end_dt:
        return False
    return start_dt <= session_dt <= end_dt


def score_entry_against_timeline_session(
    entry_temporal_signals: dict,
    session: Dict[str, object],
    *,
    normalize_match_text: Callable[[str], str],
    score_text_against_row: Callable[[str, List[str]], float],
    score_card_evidence_against_entry_fn: Callable[[dict, List[Dict[str, str]]], float],
    entry_temporal_range_contains_fn: Callable[[str, dict], bool],
) -> tuple[float, float]:
    if not session:
        return 0.0, 0.0

    entry_text = str(entry_temporal_signals.get("combined_text", "") or "")
    if not entry_text:
        return 0.0, 0.0

    session_label = normalize_match_text(str(session.get("label", "") or ""))
    session_signals = [
        normalize_match_text(str(signal))
        for signal in (session.get("signals", []) or [])
        if normalize_match_text(str(signal))
    ]
    session_text = " ".join(filter(None, [session_label, " ".join(session_signals)]))
    session_tokens = [tok for tok in session_text.split() if len(tok) >= 4]
    score = score_text_against_row(entry_text, session_tokens, weight=1.1)

    session_date = str(session.get("date", "") or "").strip()
    date_values = {
        str(value).strip()
        for value in (entry_temporal_signals.get("date_values") or [])
        if str(value).strip()
    }
    if session_date:
        if session_date in date_values:
            score += 3.0
        elif entry_temporal_range_contains_fn(session_date, entry_temporal_signals.get("date_range") or {}):
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
        score_card_evidence_against_entry_fn(entry_temporal_signals, session.get("card_evidence", []) or []),
    )
    if card_bonus > 0:
        score += card_bonus

    return score, card_bonus


def score_entry_against_timeline_sessions(
    entry_temporal_signals: dict,
    block: Dict[str, object],
    *,
    normalize_match_text: Callable[[str], str],
    score_text_against_row: Callable[[str, List[str]], float],
    score_card_evidence_against_entry_fn: Callable[[dict, List[Dict[str, str]]], float],
    entry_temporal_range_contains_fn: Callable[[str, dict], bool],
) -> tuple[float, Optional[Dict[str, object]], float]:
    best_score = 0.0
    best_session: Optional[Dict[str, object]] = None
    best_card_bonus = 0.0
    for session in block.get("sessions", []) or []:
        score, card_bonus = score_entry_against_timeline_session(
            entry_temporal_signals,
            session,
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=score_card_evidence_against_entry_fn,
            entry_temporal_range_contains_fn=entry_temporal_range_contains_fn,
        )
        if score > best_score:
            best_score = score
            best_session = session
            best_card_bonus = card_bonus
    return best_score, best_session, best_card_bonus


def select_probable_period_for_entry(
    entry: dict,
    unit: dict,
    candidate_rows: List[Dict[str, object]],
    markdown_text: str,
    *,
    preferred_topic_slug: str = "",
    collect_entry_unit_signals: Callable[[dict, str], dict],
    build_timeline_index: Callable[[List[Dict[str, object]], Optional[list]], dict],
    timeline_period_label: Callable[[str, str], str],
    collapse_ws: Callable[[str], str],
    normalize_match_text: Callable[[str], str],
    score_text_against_row: Callable[[str, List[str]], float],
    extract_date_range_signal: Callable[[str], dict],
    extract_timeline_session_signals: Callable[[str], List[dict]],
    parse_timeline_date_value: Callable[[str], object],
) -> tuple[str, float, bool, List[str]]:
    if not candidate_rows:
        return "", 0.0, True, ["sem-linhas-candidato"]

    signals = collect_entry_unit_signals(entry, markdown_text)
    if candidate_rows and "rows" in candidate_rows[0]:
        blocks = list(candidate_rows)
    else:
        timeline_index = build_timeline_index(candidate_rows, unit_index=[unit] if unit else [])
        blocks = list(timeline_index.get("blocks", []) or [])
    if not blocks:
        return "", 0.0, True, ["sem-blocos-candidato"]

    preferred_unit_slug = str(unit.get("slug", "") or "")
    preferred_topic_slug = str(preferred_topic_slug or "").strip()
    temporal_signals = collect_entry_temporal_signals(
        entry,
        markdown_text,
        collapse_ws=collapse_ws,
        normalize_match_text=normalize_match_text,
        extract_date_range_signal=extract_date_range_signal,
        extract_timeline_session_signals=extract_timeline_session_signals,
    )
    topic_filtered_blocks = [
        block for block in blocks if timeline_block_matches_preferred_topic(block, preferred_topic_slug)
    ]
    scored_source_blocks = topic_filtered_blocks if topic_filtered_blocks else blocks
    session_scored_blocks = []
    for block in scored_source_blocks:
        block_score = score_entry_against_timeline_block(
            signals,
            block,
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                s,
                items,
                normalize_match_text=normalize_match_text,
            ),
            preferred_unit_slug=preferred_unit_slug,
            preferred_topic_slug=preferred_topic_slug,
        )
        session_score, matched_session, session_card_bonus = score_entry_against_timeline_sessions(
            temporal_signals,
            block,
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                s,
                items,
                normalize_match_text=normalize_match_text,
            ),
            entry_temporal_range_contains_fn=lambda date_text, date_range: entry_temporal_range_contains(
                date_text,
                date_range,
                parse_timeline_date_value=parse_timeline_date_value,
            ),
        )
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
                period = timeline_period_label(selected_dates[0], selected_dates[-1])
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
            score_entry_against_timeline_block(
                signals,
                block,
                normalize_match_text=normalize_match_text,
                score_text_against_row=score_text_against_row,
                score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                    s,
                    items,
                    normalize_match_text=normalize_match_text,
                ),
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
            period = timeline_period_label(selected_dates[0], selected_dates[-1])
    if not period:
        return "", best_score, True, [f"best={best_score:.2f}", "sem-datas"]

    confidence = min(1.0, max(0.0, (best_score - runner_up_score) + (best_score * 0.18)))
    ambiguous = best_score < 1.0 or abs(best_score - runner_up_score) < 0.35
    best_block_card_bonus = min(
        0.45,
        score_card_evidence_against_entry(
            signals,
            best_block.get("card_evidence", []) or [],
            normalize_match_text=normalize_match_text,
        ),
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


def build_file_map_content_taxonomy_from_course(
    course_meta: dict,
    subject_profile=None,
    manifest_entries: Optional[List[dict]] = None,
    *,
    parse_units_from_teaching_plan: Callable[[str], list],
    topic_text: Callable[[object], str],
    glossary_md_fn: Callable[..., str],
    collect_strong_heading_candidates: Callable[[Optional[object], Optional[List[dict]]], List[str]],
    resolve_semantic_profile_fn: Callable[..., dict],
    build_content_taxonomy_fn: Callable[..., dict],
) -> dict:
    test_taxonomy = course_meta.get("_content_taxonomy") or course_meta.get("_content_taxonomy_for_tests")
    if test_taxonomy:
        return dict(test_taxonomy)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    if not teaching_plan:
        return {"version": 1, "course_slug": "", "units": []}

    root_dir = course_meta.get("_repo_root")
    course_name = course_meta.get("course_name", "Curso")
    parsed_units = parse_units_from_teaching_plan(teaching_plan)
    course_map_lines = [f"# COURSE_MAP --- {course_name}", ""]
    if parsed_units:
        for unit_title, topics in parsed_units:
            course_map_lines.append(f"### {unit_title}")
            if topics:
                for topic in topics:
                    course_map_lines.append(f"- [ ] {topic_text(topic)}")
            else:
                course_map_lines.append("- [ ] [topicos a preencher]")
            course_map_lines.append("")
    else:
        course_map_lines.append(teaching_plan)
    course_map_text = "\n".join(course_map_lines)

    glossary_text = ""
    if subject_profile:
        try:
            glossary_text = glossary_md_fn(
                course_meta,
                subject_profile,
                root_dir=root_dir,
                manifest_entries=manifest_entries,
            )
        except Exception:
            glossary_text = ""

    strong_headings = collect_strong_heading_candidates(root_dir, manifest_entries)
    semantic_profile = resolve_semantic_profile_fn(
        root_dir=root_dir,
        course_name=course_name,
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
    )
    return build_content_taxonomy_fn(
        teaching_plan=teaching_plan,
        course_map_md=course_map_text,
        glossary_md=glossary_text,
        strong_headings=strong_headings,
        semantic_profile=semantic_profile,
    )


def _derive_unit_specs_from_repo(course_meta: dict) -> list:
    """Fallback: deriva unit_specs do COURSE_MAP.md + .timeline_index.json do repo."""
    from src.builder.extraction.teaching_plan import _normalize_unit_slug as _slug_fn

    repo_root = course_meta.get("_repo_root")
    if not repo_root:
        return []
    repo_root = Path(repo_root)

    # 1. Carrega blocos do timeline_index para extrair sinais por unidade
    blocks_by_unit: Dict[str, list] = {}
    timeline_path = repo_root / "course" / ".timeline_index.json"
    if timeline_path.exists():
        try:
            payload = json.loads(timeline_path.read_text(encoding="utf-8"))
            for block in payload.get("blocks") or []:
                slug = str(block.get("unit_slug") or "").strip()
                if slug:
                    blocks_by_unit.setdefault(slug, []).append(block)
        except Exception:
            pass

    # 2. Lê COURSE_MAP.md para títulos humanos das unidades
    unit_titles: List[tuple] = []  # (title, slug)
    course_map_path = repo_root / "course" / "COURSE_MAP.md"
    if course_map_path.exists():
        try:
            for line in course_map_path.read_text(encoding="utf-8").splitlines():
                if not line.startswith("### "):
                    continue
                title = line[4:].strip()
                if not title or "[" in title:  # pula placeholders como "[Nome da unidade]"
                    continue
                slug = _slug_fn(title)
                if slug:
                    unit_titles.append((title, slug))
        except Exception:
            pass

    # 3. Se COURSE_MAP não ajudou, usa slugs do timeline_index como títulos
    if not unit_titles and blocks_by_unit:
        for slug in blocks_by_unit:
            title = slug.replace("-", " ").title()
            unit_titles.append((title, slug))

    if not unit_titles:
        return []

    # 4. Monta unit_specs combinando título do COURSE_MAP + sinais dos blocos
    unit_specs = []
    for title, slug in unit_titles:
        extra_signals: List[str] = []
        for block in blocks_by_unit.get(slug, []):
            extra_signals.extend(str(block.get("topic_text") or "").split())
            extra_signals.extend(str(t) for t in (block.get("topics") or []))
        unit_specs.append({"title": title, "topics": [], "extra_signals": extra_signals})
    return unit_specs


def build_file_map_unit_index_from_course(
    course_meta: dict,
    subject_profile=None,
    *,
    build_file_map_unit_index_fn: Callable[[list], list],
    parse_units_from_teaching_plan: Callable[[str], list],
    glossary_md_fn: Callable[..., str],
    parse_glossary_terms_fn: Callable[[str], List[Dict[str, object]]],
    normalize_match_text_fn: Callable[[str], str],
    collapse_ws_fn: Callable[[str], str],
    unit_generic_tokens: set[str],
    timeline_unit_neutral_tokens: set[str],
) -> list:
    test_index = course_meta.get("_unit_index_for_tests")
    if test_index:
        return build_file_map_unit_index_fn(test_index)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    if not teaching_plan:
        unit_specs = _derive_unit_specs_from_repo(course_meta)
        if unit_specs:
            return build_file_map_unit_index_fn(unit_specs)
        return []

    parsed_units = parse_units_from_teaching_plan(teaching_plan)
    root_dir = course_meta.get("_repo_root")
    glossary_text = ""
    try:
        glossary_text = glossary_md_fn(course_meta, subject_profile, root_dir=root_dir, manifest_entries=None)
    except Exception:
        glossary_text = ""

    glossary_terms = parse_glossary_terms_fn(glossary_text)
    unit_specs = []
    for title, topics in parsed_units:
        normalized_unit = normalize_match_text_fn(title)
        extra_signals = []
        seen_signals = set()
        for term in glossary_terms:
            unit_hint = normalize_match_text_fn(str(term.get("unit_hint", "") or ""))
            if unit_hint and unit_hint not in normalized_unit and normalized_unit not in unit_hint:
                continue
            for candidate in [
                str(term.get("term", "") or ""),
                *list(term.get("synonyms", []) or []),
            ]:
                cleaned = collapse_ws_fn(str(candidate))
                normalized = normalize_match_text_fn(cleaned)
                if not normalized or normalized in seen_signals:
                    continue
                seen_signals.add(normalized)
                extra_signals.append(cleaned)

            definition = normalize_match_text_fn(str(term.get("definition", "") or ""))
            for token in definition.split():
                if len(token) < 5 or token in unit_generic_tokens or token in timeline_unit_neutral_tokens:
                    continue
                if token in seen_signals:
                    continue
                seen_signals.add(token)
                extra_signals.append(token)

        unit_specs.append({"title": title, "topics": topics, "extra_signals": extra_signals})
    return build_file_map_unit_index_fn(unit_specs)
