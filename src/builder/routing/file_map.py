from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

from src.builder.routing.dates import extract_dates
from src.builder.text.normalize import normalize_match_text as _normalize_text
from src.builder.text.normalize import split_camel_case
from src.builder.routing.thresholds import (
    DATE_STRONG_BOOST,
    DATE_WEAK_BOOST,
    T,
    relative_margin_confidence,
)
from src.builder.text.stopwords import UNIT_GENERIC_TOKENS


@dataclass
class UnitMatchResult:
    slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)


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
    winning_unit_slug: str = "",
    collect_entry_unit_signals: Callable[[dict, str], dict],
    iter_content_taxonomy_topics: Callable[[dict], List[dict]],
    score_entry_against_taxonomy_topic: Callable[[dict, dict], float],
    topic_match_result_factory,
):
    topic_index = iter_content_taxonomy_topics(taxonomy)
    if winning_unit_slug:
        topic_index = [t for t in topic_index if str(t.get("unit_slug", "") or "") == winning_unit_slug]
    if not topic_index:
        return topic_match_result_factory(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=[f"sem-topicos-para-unidade:{winning_unit_slug}" if winning_unit_slug else "sem-taxonomia"],
        )

    signals = collect_entry_unit_signals(entry, markdown_text)
    scored = [(topic, score_entry_against_taxonomy_topic(signals, topic)) for topic in topic_index]
    scored.sort(key=lambda item: item[1], reverse=True)

    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    margin = winner_score - runner_up_score
    rel_margin = margin / max(winner_score, 1e-6)
    # Sem sinal ou empate EXATO: nao ha vencedor real — o sort estavel elegeria
    # um slug arbitrario (menor indice na taxonomia) e o surfacaria com conf
    # 0.0 no editor (12 entries codigo-professor do repo real, 12/06). Slug
    # vazio e a resposta honesta; a reason preserva o diagnostico.
    if winner_score <= 0.0:
        return topic_match_result_factory(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=["sem-sinal (winner_score=0)"],
        )
    if len(scored) > 1 and margin == 0.0:
        tied = sum(1 for _, score in scored if score == winner_score)
        return topic_match_result_factory(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=[f"empate-exato {tied}x score={winner_score:.2f}"],
        )
    if len(scored) == 1:
        confidence = 0.72
        ambiguous = False
    else:
        confidence = max(0.0, min(1.0, rel_margin))
        ambiguous = rel_margin < 0.15
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
    timeline_unit_neutral_tokens: set[str], unit_tag_boost = 0.0,
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
    if unit_tag_boost > 0.0:
        score += unit_tag_boost * 0.85
    return score


def auto_map_entry_unit(
    entry: dict,
    units: list,
    markdown_text: str,
    *,
    topic_index: Optional[List[dict]] = None,
    unit_tag_index: Optional[Dict[str, float]] = None,
    learned_unit_boosts: Optional[Dict[str, float]] = None,
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
    unit_tag_boosts: Dict[str, float] = {}
    if unit_tag_index:
        for tag in [str(t) for t in (entry.get("auto_tags") or []) if t]:
            mapping = unit_tag_index.get(tag)
            if not mapping:
                continue
            u_slug = str(mapping.get("unit_slug", "") or "").strip()
            w = float(mapping.get("weight", 1.0))
            if u_slug:
                unit_tag_boosts[u_slug] = unit_tag_boosts.get(u_slug, 0.0) + w
    if learned_unit_boosts:
        for slug, w in learned_unit_boosts.items():
            if slug and w:
                unit_tag_boosts[str(slug)] = unit_tag_boosts.get(str(slug), 0.0) + float(w)
    scored = []
    normalized_topic_index = list(topic_index or [])
    for unit in indexed_units:
        tag_boost = unit_tag_boosts.get(str(unit.get("slug", "") or ""), 0.0)
        score = score_entry_against_unit(signals, unit, unit_tag_boost=tag_boost)
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
    margin = winner_score - runner_up_score
    rel_margin = margin / max(winner_score, 1e-6)
    if winner_score <= 0.0:
        confidence = 0.0
        ambiguous = True
    elif len(scored) == 1:
        confidence = 0.7
        ambiguous = False
    else:
        # relative_margin_confidence (idea 1: mesma fórmula do bloco, P2): margem
        # RELATIVA escalada pela força absoluta. Mata a saturação do margin_confidence
        # aditivo, cujo termo winner*k clampava em 1.0 com winner_score alto → unidade
        # confiante-ERRADA (ex.: "exemplos" casando o subtópico de OUTRA unidade dava
        # conf 1.0 e ainda vencia o bloco na reconciliação). O piso absoluto de
        # ambiguidade abaixo (UNIT_MATCH_MIN_WINNER) segue valendo.
        confidence = relative_margin_confidence(winner_score, runner_up_score)
        # Ambiguo por margem RELATIVA fraca OU por score ABSOLUTO baixo: sem o
        # piso absoluto, um winner fraco com runner_up ~0 (rel_margin ~1.0)
        # passaria por confiante (caso do token "estado" acidental).
        ambiguous = (
            rel_margin < T.UNIT_MATCH_REL_MARGIN
            or winner_score < T.UNIT_MATCH_MIN_WINNER
        )
    if (
        len(scored) > 1
        and normalized_topic_index
        and winner_topic_score >= 0.55
        and (winner_topic_score - runner_up_topic_score) >= 0.01
    ):
        topic_rel_margin = (winner_topic_score - runner_up_topic_score) / max(winner_topic_score, 1e-6)
        if topic_rel_margin >= 0.15:
            ambiguous = False
            confidence = max(confidence, min(0.95, topic_rel_margin))
    if ambiguous:
        confidence = min(confidence, 0.4)
    reasons = [f"winner_score={winner_score:.2f}"]
    if normalized_topic_index:
        reasons.append(f"topic_score={winner_topic_score:.2f}")
    winner_tag_boost = unit_tag_boosts.get(str(winner.get("slug", "") or ""), 0.0)
    if winner_tag_boost > 0.0:
        reasons.append(f"tag_boost={winner_tag_boost:.2f}")
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


def _block_by_migrated_ref(raw: str, blocks: list) -> Optional[Dict[str, object]]:
    """Casa uma ref de chave migrada (Fase 1) ao bloco: uuid-first, fallback bloco-NN.

    Helper ÚNICO da classe "leitor de verdade-humana migrada": a Fase 1 migrou as
    chaves (manual_timeline_block_id etc.) pra block_uuid, mas leitores que casavam
    só block.id (bloco-NN) deixavam o uuid sem casar → verdade-humana invisível.
    """
    raw = str(raw or "").strip()
    if not raw:
        return None
    for block in blocks:
        if str(block.get("block_uuid") or "").strip() == raw:
            return block
    for block in blocks:
        if str(block.get("id", "")).strip() == raw:
            return block
    return None


def resolve_entry_manual_timeline_block(entry: dict, timeline_context: dict) -> Optional[Dict[str, object]]:
    raw = str(entry.get("manual_timeline_block_id") or "").strip()
    if not raw:
        return None
    blocks = list(((timeline_context or {}).get("timeline_index") or {}).get("blocks", []) or [])
    hit = _block_by_migrated_ref(raw, blocks)
    if hit is not None:
        return hit
    match = re.fullmatch(r"bloco-(\d+)", raw, flags=re.IGNORECASE)
    if match:
        ordinal = int(match.group(1))
        entry_unit = str(entry.get("unit_slug") or entry.get("manual_unit_slug") or "").strip()
        # D2: blocks vem do timeline_context runtime (_build_timeline_index) ->
        # admin presente sem a chave; o key-lookup antigo era no-op e contava blocos
        # admin no ordinal de "bloco-N". Lazy import: timeline.index importa este modulo.
        from src.builder.timeline.index import timeline_block_is_administrative_only
        instructional_blocks = [
            block
            for block in blocks
            if not timeline_block_is_administrative_only(block)
            and (not entry_unit or str(block.get("unit_slug", "")).strip() == entry_unit)
        ]
        if 1 <= ordinal <= len(instructional_blocks):
            return instructional_blocks[ordinal - 1]
    return None


class EffectiveBlock(NamedTuple):
    """Resultado de resolve_effective_block: id do bloco vencedor + de onde veio.

    source ∈ {"manual", "auto", ""}: "manual" quando o override do entry venceu,
    "auto" quando caiu no computed_block_id (espelhado em auto_tags["bloco:"]),
    "" quando nada resolveu (curso sem bloco / entry sem atribuição).
    """

    block_id: str
    source: str


_logger = logging.getLogger(__name__)


def _entry_computed_block_id(entry: dict) -> str:
    """computed_block_id (Fase 1) com fallback para o espelho auto_tags["bloco:"].

    O campo computed_block_id e a fonte; auto_tags["bloco:"] e o espelho. Dicts
    crus vindos de manifest antigo podem ter so a tag — por isso lemos ambos.
    """
    cid = str(entry.get("computed_block_id") or "").strip()
    if cid:
        return cid
    for tag in entry.get("auto_tags") or []:
        t = str(tag)
        if t.startswith("bloco:"):
            return t[len("bloco:"):].strip()
    return ""


def resolve_effective_block(
    entry: dict,
    blocks: Optional[List[Dict[str, object]]] = None,
) -> EffectiveBlock:
    """FONTE ÚNICA da precedência material→bloco (spec Fase 4, linhas 138-146).

    Precedência, definida AQUI e em lugar nenhum mais:
        manual_timeline_block_id (entry)  >  computed_block_id (auto).
    auto_tags["bloco:"] e apenas espelho do computed (Fase 1), nunca contradiz.

    Resolução do manual reusa resolve_entry_manual_timeline_block (id exato +
    fallback ordinal "bloco-N"). Manual apontando para id inexistente que nem o
    ordinal resolve → trata como sem-override e cai no computed (logado), per
    spec linhas 195-197.

    `blocks` (lista do timeline_index) é opcional: quando ausente não há como
    validar o manual id, então confiamos no valor cru (caminho UI que já tem a
    lista usa-a; caminhos sem ela degradam graciosamente).
    """
    manual_raw = str(entry.get("manual_timeline_block_id") or "").strip()
    computed = _entry_computed_block_id(entry)

    if manual_raw:
        if blocks is None:
            # Sem timeline para validar: confia no id cru do override.
            return EffectiveBlock(manual_raw, "manual")
        resolved = resolve_entry_manual_timeline_block(
            entry, {"timeline_index": {"blocks": blocks}}
        )
        if resolved is not None:
            return EffectiveBlock(str(resolved.get("id", "")).strip(), "manual")
        _logger.info(
            "manual_timeline_block_id %r não resolve (nem ordinal); usando computed %r",
            manual_raw,
            computed,
        )

    if computed:
        return EffectiveBlock(computed, "auto")
    return EffectiveBlock("", "")


def resolve_temporal_block(
    entry: dict,
    blocks: Optional[List[Dict[str, object]]] = None,
) -> str:
    """Bloco TEMPORAL (cronograma) efetivo do material.

    Precedência: `temporal_block_id` (âncora cronograma-validada, escrito só com
    a flag use_anchor_placement) sobrepõe; ausente → cai na FONTE ÚNICA
    compartilhada `resolve_effective_block` (manual > computed). Com a flag OFF
    o campo nunca existe → este helper é byte-idêntico ao resolve_effective_block
    de hoje. Disjunto de KB: NÃO chama reconcile_unit_with_block.

    O fallback é `resolve_effective_block` (NÃO computed_block_id cru) de
    propósito: os consumidores temporais honram manual_timeline_block_id stale-safe
    via essa fonte; trocar pelo computed cru perderia o manual com a flag OFF.

    review F4 C1: o producer (_write_temporal, motor/apply.py) grava
    block_uuid cru em temporal_block_id; os leitores (dashboard, cronograma_health)
    casam contra display id (block["id"]). Sem resolução aqui, flag-ON vira
    "unmapped" em cascata. Quando `blocks` está disponível, casa o uuid contra
    block_uuid e devolve o display id do mesmo bloco (reusa _block_by_migrated_ref,
    que também aceita um valor já-display e o devolve intacto). uuid que não
    resolve (blocks ausente/desatualizado) cai no valor cru — sem crash.
    """
    temporal = str(entry.get("temporal_block_id") or "").strip()
    if temporal:
        if blocks:
            hit = _block_by_migrated_ref(temporal, blocks)
            if hit is not None:
                return str(hit.get("id", "")).strip() or temporal
        return temporal
    return resolve_effective_block(entry, blocks).block_id


def reconcile_unit_with_block(
    *,
    computed_unit_slug: str,
    unit_confidence: float,
    computed_block_id: str,
    block_confidence: float,
    block_unit_slug: str,
    block_is_manual: bool,
    has_manual_unit: bool,
) -> Tuple[str, List[str], Dict[str, str]]:
    """Reconcilia a unidade efetiva com o bloco atribuído (F1, spec linhas 36-52).

    Precedência:
      1. Bloco MANUAL com unidade -> unidade do bloco (autoritativo, vence até
         manual_unit). reason "unidade_do_bloco_manual".
      2. manual_unit presente (sem bloco manual) -> mantém computed_unit_slug.
      3. Auto:
         - sem bloco / bloco sem unidade -> mantém computed_unit_slug.
         - computed_unit_slug vazio -> herda do bloco ("herdada_do_bloco=<id>").
         - concordam -> mantém.
         - discordam: block_confidence >= unit_confidence -> unidade do bloco
           ("reconciliada_do_bloco=<id>"); senão mantém a unidade forte e devolve
           conflict {unit, block_unit, block_id}.

    conflict é {} exceto no último caso (unidade forte venceu bloco discordante).
    """
    if block_is_manual and block_unit_slug:
        return block_unit_slug, ["unidade_do_bloco_manual"], {}
    if has_manual_unit:
        return computed_unit_slug, [], {}
    if not computed_block_id or not block_unit_slug:
        return computed_unit_slug, [], {}
    if not computed_unit_slug:
        return block_unit_slug, [f"herdada_do_bloco={computed_block_id}"], {}
    if block_unit_slug == computed_unit_slug:
        return computed_unit_slug, [], {}
    if block_confidence >= unit_confidence:
        return block_unit_slug, [f"reconciliada_do_bloco={computed_block_id}"], {}
    return (
        computed_unit_slug,
        [],
        {"unit": computed_unit_slug, "block_unit": block_unit_slug, "block_id": computed_block_id},
    )


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
        # normalized_title já sai normalizado da extração (card_evidence._build_item,
        # canônico [a-z0-9 ]); renormalizar aqui era no-op pago O(entries×blocos×cards)
        # — provado por probe nos 5 índices vivos (auditoria 2.8).
        normalized_title = str(item.get("normalized_title", "") or "")
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
    if not rows:
        # Bloco PERSISTIDO (.timeline_index.json) não tem 'rows' — sintetiza
        # linhas pontuáveis de source_rows/sessions (bug B3, 2º call site:
        # sem isso o score é 0.0 e o ranking degenera pro 1º bloco).
        for sr in block.get("source_rows", []) or []:
            if isinstance(sr, dict):
                content = " ".join(str(sr.get(k) or "") for k in ("date", "description"))
                rows.append({"content": content.strip()})
        if not rows:
            for sess in block.get("sessions", []) or []:
                if isinstance(sess, dict):
                    content = " ".join(str(sess.get(k) or "") for k in ("date", "label"))
                    rows.append({"content": content.strip()})
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


def _block_period_bounds(block: Dict[str, object]) -> tuple[Optional[date], Optional[date]]:
    """Range do bloco como (date, date). Usa period_start/period_end (ISO) e
    cai para os date_text das rows quando os campos de período faltam."""
    candidates: List[date] = []
    for key in ("period_start", "period_end"):
        for dt in extract_dates(str(block.get(key, "") or "")):
            candidates.append(dt)
    if not candidates:
        for row in block.get("rows") or []:
            for dt in extract_dates(str(row.get("date_text", "") or "")):
                candidates.append(dt)
    if not candidates:
        return None, None
    return min(candidates), max(candidates)


def _score_block_date_match(signals: dict, block: Dict[str, object]) -> float:
    start, end = _block_period_bounds(block)
    if not start or not end:
        return 0.0

    # Datas year-less do material assumem o ano do período do bloco. Extraímos
    # POR fonte (não num join): os signals chegam JÁ normalizados, então uma data
    # year-less separada por espaço ("12 03 ...") só é aceita ANCORADA no início
    # do texto (cf. dates.py). Juntar os campos jogaria a data real para o meio
    # da string e mataria o match — por isso rodamos extract_dates em cada fonte.
    material_dates: list[date] = []
    for key in ("raw_text", "title_text", "markdown_text"):
        material_dates.extend(
            extract_dates(str(signals.get(key, "") or ""), default_year=start.year)
        )
    if not material_dates:
        return 0.0

    for dt in material_dates:
        if start <= dt <= end:
            return DATE_STRONG_BOOST
    for dt in material_dates:
        if start.month <= dt.month <= end.month and dt.year == start.year:
            return DATE_WEAK_BOOST
    return 0.0


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
        # S1 (P4): camelCase do título separado também no caminho temporal
        # (combined_text alimenta card_evidence e match de sessão por bloco).
        split_camel_case(str(entry.get("title", "") or "")),
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
        _logger.warning("sem teaching_plan no perfil — content_taxonomy vazia (curso perde estrutura de unidades)")
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
    _logger.warning(
        "unidades derivadas do repo gerado, nao do plano de ensino — fallback"
    )
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
        _logger.warning(
            "sem teaching_plan — unit_index cai pro fallback repo-derived (%d specs)", len(unit_specs)
        )
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
