"""Mapa de relevância de uma referência -> unidade/tópico (NÃO bloco).

Espelha code_summarization.assign_code_to_block, mas o alvo é a unidade: faz
overlap dos tokens de concept (ou, sem concepts, do texto) contra o "bag" de
tokens de cada unidade do índice. Determinístico, sem rede, sem Gemini.
"""
from __future__ import annotations

from typing import List

from src.builder.core.code_summarization import _normalize, _stem, _expand_concept_tokens


def _unit_bag(unit: dict) -> set[str]:
    bag: set[str] = set()
    fields: List[str] = []
    fields.append(unit.get("normalized_title", "") or "")
    fields.extend(unit.get("topic_phrases", []) or [])
    fields.extend(unit.get("topic_tokens", []) or [])
    fields.extend(unit.get("distinctive_tokens", []) or [])
    for f in fields:
        for tok in _normalize(f).split():
            if len(tok) >= 4:
                bag.add(tok)
                bag.add(_stem(tok))
    bag.discard("")
    return bag


def assign_concepts_to_unit(
    concepts: List[str],
    fallback_text: str,
    units: List[dict],
    *,
    primary_threshold: float = 0.34,
    margin_threshold: float = 0.10,
) -> dict:
    """Retorna {"unit_slug": str, "topics": list[str], "confidence": float}.

    Usa `concepts` (do Gemini); sem concepts cai para tokens de `fallback_text`.
    Vazio quando nada casa acima do threshold.
    """
    terms = [c for c in (concepts or []) if c]
    if not terms and fallback_text:
        terms = [t for t in fallback_text.split() if len(t) >= 4]
    terms_norm = [_normalize(t) for t in terms]
    terms_norm = [t for t in terms_norm if t]
    if not terms_norm or not units:
        return {"unit_slug": "", "topics": [], "confidence": 0.0}

    term_token_sets = [_expand_concept_tokens(t) for t in terms_norm]

    scores: list[tuple[str, float, list]] = []
    for unit in units:
        bag = _unit_bag(unit)
        if not bag:
            scores.append((unit.get("slug", ""), 0.0, unit.get("topic_phrases", []) or []))
            continue
        overlap = sum(1 for toks in term_token_sets if toks & bag)
        scores.append((unit.get("slug", ""), overlap / len(term_token_sets), unit.get("topic_phrases", []) or []))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_slug, top_score, top_topics = scores[0]
    second = scores[1][1] if len(scores) > 1 else 0.0
    if top_score >= primary_threshold and (top_score - second) >= margin_threshold:
        return {"unit_slug": top_slug, "topics": list(top_topics)[:3], "confidence": round(top_score, 3)}
    return {"unit_slug": "", "topics": [], "confidence": round(top_score, 3)}
