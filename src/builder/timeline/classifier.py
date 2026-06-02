"""Classificador unico de blocos do cronograma.

`classify_block(block) -> BlockKind` consolida toda heuristica de deteccao
(antes espalhada em `_timeline_row_is_review_or_assessment` + audit script + UI).

Determinista: keywords + regex em ordem de prioridade. Sem LLM.
Mais especifico bate primeiro. Excecao critica: bloco de apresentacao do
plano de ensino NUNCA cai em assessment mesmo contendo "avaliacao".
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Mapping, Pattern, Tuple, Union

from .kinds import BlockKind


def _norm(text: str) -> str:
    """NFKD + lower + so [a-z0-9 ]. Match comportamento do index.py."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Excecao: se qualquer um destes termos aparecer, kind=CLASS mesmo se
# bater keyword de outro tipo. Pega caso "apresentacao do plano de ensino +
# avaliacao do curso" (IA bloco-01) e similares.
CLASS_INTRO_TERMS: Tuple[str, ...] = (
    "apresentacao",
    "plano de ensino",
    "plano ensino",
    "cronograma da disciplina",
    "ementa",
)


KeywordSpec = Union[str, Pattern[str]]


def _phrase_match(needle: str, hay: str, hay_tokens: set) -> bool:
    """Substring se multi-palavra, token-exato se 1 palavra (>=4 chars)."""
    needle = needle.strip()
    if not needle or not hay:
        return False
    if " " in needle:
        return needle in hay
    if len(needle) < 4:
        return needle in hay_tokens
    return needle in hay_tokens


KIND_KEYWORDS: List[Tuple[BlockKind, List[KeywordSpec]]] = [
    (BlockKind.HOLIDAY, [
        "feriado", "carnaval", "natal", "pascoa", "corpus",
        "tiradentes", "independencia", "finados", "consciencia negra",
        "aparecida", "nossa senhora",
    ]),
    (BlockKind.SUSPENDED, [
        "suspensao", "suspenso", "suspensa", "greve",
        "paralisacao", "assembleia",
    ]),
    (BlockKind.MAKEUP, [
        "substituicao", "reposicao",
    ]),
    (BlockKind.ACADEMIC_EVENT, [
        "evento academico", "semana academica", "semana cientifica",
        "simposio", "congresso", "jornada", "ciclo de palestras",
        "seminario integrador",
    ]),
    (BlockKind.RESULTS, [
        "divulgacao", "devolucao", "devolutiva",
    ]),
    (BlockKind.DELIVERABLE, [
        "entrega trabalho", "entrega final", "entrega do trabalho",
        "submissao final",
    ]),
    (BlockKind.WORKSHOP, [
        "oficina", "lancamento", "kick off", "kickoff",
    ]),
    (BlockKind.OFFICE_HOURS, [
        "atendimento", "duvidas", "plantao", "monitoria",
    ]),
    (BlockKind.PLANNING, [
        "planejamento", "reuniao", "conselho",
    ]),
    (BlockKind.RESERVED, [
        "reserva tecnica", "reserva",
    ]),
    (BlockKind.ASSESSMENT, [
        re.compile(r"\bp[1-4]\b"),
        re.compile(r"\bpf\b"),
        "prova", "avaliacao", "exame", "recuperacao",
        "substitutiva", "teste",
    ]),
    (BlockKind.REVIEW, [
        "revisao",
    ]),
]


def _text_of(block: Mapping[str, object]) -> str:
    """Campos a inspecionar para classificacao."""
    parts: List[str] = []
    for key in ("topic_text", "primary_topic_label", "period_label"):
        val = block.get(key)
        if isinstance(val, str) and val:
            parts.append(val)
    topics = block.get("topics")
    if isinstance(topics, list):
        parts.extend(str(t) for t in topics if t)
    return " ".join(parts)


def classify_block(block: Mapping[str, object]) -> BlockKind:
    """Retorna BlockKind. Manual override sempre vence."""
    override = block.get("manual_kind_override")
    if isinstance(override, str):
        try:
            return BlockKind(override)
        except ValueError:
            pass

    raw_text = _text_of(block)
    hay = _norm(raw_text)
    has_unit = bool(block.get("unit_slug"))
    has_topic = bool(block.get("primary_topic_label"))

    if not hay:
        if has_unit:
            return BlockKind.CLASS
        return BlockKind.UNKNOWN

    if any(term in hay for term in CLASS_INTRO_TERMS):
        return BlockKind.CLASS

    hay_tokens = set(hay.split())

    for kind, specs in KIND_KEYWORDS:
        for spec in specs:
            if isinstance(spec, re.Pattern):
                if spec.search(hay):
                    return kind
            else:
                if _phrase_match(spec, hay, hay_tokens):
                    return kind

    if has_unit or has_topic:
        return BlockKind.CLASS
    # Topic_text com substancia (>=8 chars OU >=2 tokens) sugere aula real
    # sem unit/topic mapeados ainda. Phase 3/4 resolve unit/topic depois.
    # UNKNOWN reservado pra fragmento (1 token curto) ou vazio.
    if len(hay) >= 8 or len(hay_tokens) >= 2:
        return BlockKind.CLASS
    return BlockKind.UNKNOWN
