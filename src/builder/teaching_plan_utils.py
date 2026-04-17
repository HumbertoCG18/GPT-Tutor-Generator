from __future__ import annotations

import re

from src.utils.helpers import slugify

_EM_DASH = "\u2014"
_EN_DASH = "\u2013"
_BULLET = "\u2022"
_DEGREE = "\u00b0"
_MASC_ORD = "\u00ba"
_C_CEDILLA_UPPER = "\u00c7"
_A_TILDE_UPPER = "\u00c3"
_U_ACUTE_UPPER = "\u00da"

_TEACHING_PLAN_SECTION_STOP = re.compile(
    rf"^(?:PROCEDIMENTOS|AVALIA[{_C_CEDILLA_UPPER}C][A{_A_TILDE_UPPER}]O|BIBLIOGRAFIA|METODOLOGIA)",
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
    Extrai (titulo_da_unidade, [topicos]) do texto livre do plano de ensino.

    Cada topico retorna como `(texto, depth)`:
    - depth 0 -> topico principal
    - depth 1+ -> subtopicos numerados
    """
    units: list = []
    current_title = None
    current_unit_num = None
    current_topics: list = []
    current_style = None

    pucrs_unit_re = re.compile(
        rf"N[{_DEGREE}{_MASC_ORD}]?\.\s*DA\s+UNIDADE\s*:\s*(\d+)",
        re.IGNORECASE,
    )
    pucrs_content_re = re.compile(
        rf"CONTE[{_U_ACUTE_UPPER}U]DO\s*:\s*(.+)",
        re.IGNORECASE,
    )
    generic_unit_re = re.compile(
        rf"^(?:#{{0,4}}\s*)?(unidade(?:\s+de\s+aprendizagem)?\s+(?:\d+|[ivxlcdm]+))\s*[-{_EN_DASH}:{_EM_DASH}]\s*(.+)",
        re.IGNORECASE,
    )
    numbered_topic_re = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\.\s+(.+)")
    bullet_topic_re = re.compile(rf"^[-{_BULLET}*]\s+(.+)")

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized_line = _normalize_teaching_plan_heading(line)
        if _TEACHING_PLAN_SECTION_STOP.match(normalized_line):
            break

        m = pucrs_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_unit_num = m.group(1)
            current_title = None
            current_topics = []
            current_style = "pucrs"
            continue

        if current_unit_num is not None and current_title is None:
            m = pucrs_content_re.match(line)
            if m:
                current_title = f"Unidade {current_unit_num} {_EM_DASH} {m.group(1).strip()}"
                continue

        m = generic_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_title = f"{m.group(1).strip()} {_EM_DASH} {m.group(2).strip()}"
            current_unit_num = None
            current_topics = []
            current_style = "learning_unit" if "aprendizagem" in m.group(1).lower() else "generic"
            continue

        if current_title is not None:
            m = numbered_topic_re.match(line)
            if m:
                numbering = m.group(1)
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
    """Extrai o texto de um topico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[0]
    return str(topic)


def _topic_depth(topic) -> int:
    """Extrai a profundidade de um topico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[1]
    return 0


def _normalize_unit_slug(title: str) -> str:
    slug = slugify((title or "").replace(_EM_DASH, "-"))
    match = re.match(r"^(unidade(?:-de-aprendizagem)?-)(\d+)(-.+)?$", slug)
    if not match:
        return slug
    prefix, number, suffix = match.groups()
    suffix = suffix or ""
    return f"{prefix}{int(number):02d}{suffix}"
