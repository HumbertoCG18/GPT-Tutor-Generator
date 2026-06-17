from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, TypedDict, Union

from src.builder.routing.thresholds import IDF_WEIGHT
from src.builder.text.normalize import normalize_match_text
from src.builder.text.stopwords import TIMELINE_GENERIC_TOKENS, UNIT_GENERIC_TOKENS

_STOPWORDS = TIMELINE_GENERIC_TOKENS | UNIT_GENERIC_TOKENS

# Extensoes de arquivo-fonte: sinal de FORMATO, uniforme na unidade -> nao
# discrimina bloco (par do down-weight de ferramenta no escopo de bloco).
FORMAT_TOKENS: frozenset = frozenset({
    "thy", "dfy", "smv", "als", "coq", "lean",
    "zip", "pdf", "md", "py", "txt", "json", "csv", "ipynb",
})

# Piso do peso de ferramenta/formato no escopo de bloco: ~0 (nao negativo).
_BLOCK_TOOL_FLOOR: float = 0.0


def _concept_text(item: object) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item or "")
    parts: List[str] = []
    # BLOCO (.timeline_index.json)
    if "topic_text" in item or "sessions" in item:
        parts.append(str(item.get("topic_text", "") or ""))
        parts.append(str(item.get("primary_topic_label", "") or ""))
        for topic in item.get("topics") or []:
            parts.append(str(topic or ""))
        for session in item.get("sessions") or []:
            if isinstance(session, dict):
                parts.append(str(session.get("label", "") or ""))
        for alias in item.get("aliases") or []:
            parts.append(str(alias or ""))
        return " ".join(p for p in parts if p)
    # UNIDADE (.content_taxonomy.json)
    if "title" in item or "topics" in item:
        parts.append(str(item.get("title", "") or ""))
        for topic in item.get("topics") or []:
            if isinstance(topic, dict):
                parts.append(str(topic.get("label", "") or ""))
                for alias in topic.get("aliases") or []:
                    parts.append(str(alias or ""))
            else:
                parts.append(str(topic or ""))
        return " ".join(p for p in parts if p)
    # ENTRY / texto cru com concepts do Gemini
    for key in ("title", "markdown", "source_section", "text"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    for concept in item.get("concepts") or []:
        parts.append(str(concept or ""))
    return " ".join(p for p in parts if p)


def _concept_tokens(text: str, normalize: Callable[[str], str]) -> set:
    return {
        token
        for token in normalize(text).split()
        if len(token) >= 4 and token not in _STOPWORDS
    }


def concept_token_weights(
    corpus: Sequence[object],
    *,
    scope: str,
    tool_tokens: Optional[set] = None,
    normalize: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    norm = normalize or normalize_match_text
    tools = {t for t in (tool_tokens or set()) if t}
    frequency: Dict[str, int] = {}
    for item in corpus or []:
        for token in _concept_tokens(_concept_text(item), norm):
            frequency[token] = frequency.get(token, 0) + 1

    weights: Dict[str, float] = {}
    for token, freq in frequency.items():
        rarity = 0.0 if token in UNIT_GENERIC_TOKENS else (1.0 / freq)
        weight = 1.0 + IDF_WEIGHT * (rarity - 1.0)
        if scope == "block" and (token in tools or token in FORMAT_TOKENS):
            weight = min(weight, _BLOCK_TOOL_FLOOR)
        weights[token] = weight
    return weights


def concept_vector(
    item: object,
    weights: Dict[str, float],
    *,
    normalize: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    norm = normalize or normalize_match_text
    return {
        token: weights[token]
        for token in _concept_tokens(_concept_text(item), norm)
        if token in weights
    }


class Assignment(TypedDict):
    block_id: str
    unit_slug: str
    confidence: float
    band: str
    method: str
    signals: dict
    conflict: Optional[dict]


def resolve_material_assignment(
    entry: dict,
    blocks: List[dict],
    units: List[dict],
    *,
    signals: dict,
    llm_curation: Optional[dict] = None,
) -> Assignment:
    raise NotImplementedError("Task 2.2: fusao de sinais + tiers de precedencia")
