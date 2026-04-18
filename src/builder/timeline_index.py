from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.builder.card_evidence import extract_card_evidence
from src.builder.timeline_signals import extract_timeline_session_signals
from src.utils.helpers import slugify, write_text


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("propocional", "proposicional")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _signal_token_set(signal_text: str) -> set:
    return {
        token
        for token in _normalize_match_text(signal_text).split()
        if len(token) >= 4
    }


def _matches_normalized_phrase(signal_text: str, phrase: str) -> bool:
    normalized_signal = _normalize_match_text(signal_text)
    normalized_phrase = _normalize_match_text(phrase)
    if not normalized_signal or not normalized_phrase:
        return False
    if " " not in normalized_phrase:
        return normalized_phrase in _signal_token_set(normalized_signal)
    return normalized_phrase in normalized_signal


def _normalize_unit_slug(title: str) -> str:
    slug = slugify((title or "").replace("—", "-"))
    match = re.match(r"^(unidade(?:-de-aprendizagem)?-)(\d+)(-.+)?$", slug)
    if not match:
        return slug
    prefix, number, suffix = match.groups()
    suffix = suffix or ""
    return f"{prefix}{int(number):02d}{suffix}"


@dataclass
class TopicMatchResult:
    topic_slug: str
    topic_label: str
    unit_slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)


def _parse_syllabus_timeline(syllabus: str) -> List[Dict[str, str]]:
    """
    Parseia o cronograma (Markdown table) e retorna lista de dicts.

    Cada dict tem chaves normalizadas das colunas do cronograma.
    Exemplo de retorno:
        [
            {"semana": "1", "data": "2026-03-02", "conteúdo": "Unidade 1: Métodos Formais"},
            {"semana": "2", "data": "2026-03-09", "conteúdo": "Continuação Unidade 1"},
            ...
        ]

    Suporta tabelas Markdown com qualquer nome de coluna — normaliza para minúsculas.
    """
    if not syllabus or not syllabus.strip():
        return []

    lines = [l.strip() for l in syllabus.strip().splitlines() if l.strip()]

    header_line = None
    data_start = 0
    for i, line in enumerate(lines):
        if "|" in line and not all(c in "|-: " for c in line):
            header_line = line
            data_start = i + 1
            break

    if not header_line:
        return []

    headers = [h.strip().lower() for h in header_line.split("|") if h.strip()]
    if not headers:
        return []

    result = []
    for line in lines[data_start:]:
        if not line.startswith("|"):
            continue
        if all(c in "-|: " for c in line):
            continue

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c or len(cells) > len(headers)]
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]

        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))

        row = {}
        for j, h in enumerate(headers):
            row[h] = cells[j].strip() if j < len(cells) else ""
        result.append(row)

    return result


def _infer_timeline_keys(timeline: List[Dict[str, str]]) -> tuple[List[str], List[str]]:
    if not timeline:
        return [], []

    sample = timeline[0]
    content_keys = []
    for key in sample.keys():
        if any(k in key for k in ["conteúdo", "conteudo", "assunto", "tema", "descrição",
                                  "descricao", "atividade", "tópico", "topico", "content"]):
            content_keys.append(key)
    if not content_keys:
        avg_lens = {}
        for key in sample.keys():
            avg_lens[key] = sum(len(row.get(key, "")) for row in timeline) / max(len(timeline), 1)
        if avg_lens:
            content_keys = [max(avg_lens, key=avg_lens.get)]

    preferred_date_keys = []
    fallback_date_keys = []
    for key in sample.keys():
        if any(k in key for k in ["data", "date"]):
            preferred_date_keys.append(key)
        elif any(k in key for k in ["semana", "week", "sem", "aula"]):
            fallback_date_keys.append(key)
    date_keys = preferred_date_keys or fallback_date_keys
    if not date_keys:
        date_keys = [list(sample.keys())[0]] if sample else []

    return content_keys, date_keys


def _parse_timeline_date_value(value: str) -> Optional[datetime]:
    text = _collapse_ws(value)
    if not text:
        return None
    raw = text[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_timeline_period_bounds(period: str) -> tuple[Optional[datetime], Optional[datetime]]:
    text = _collapse_ws(period)
    if not text:
        return None, None
    candidates = re.findall(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}", text)
    if not candidates:
        return None, None
    start = _parse_timeline_date_value(candidates[0])
    end = _parse_timeline_date_value(candidates[1]) if len(candidates) > 1 else start
    if start and end and start > end:
        start, end = end, start
    return start, end


def _match_timeline_to_units_generic(
    timeline: List[Dict[str, str]],
    units: list,
    *,
    normalize_unit_slug: Callable[[str], str],
    topic_text: Callable[[object], str],
) -> list:
    if not timeline or not units:
        return []

    content_keys, date_keys = _infer_timeline_keys(timeline)
    if not content_keys:
        return []

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

        desc_match = re.search(r"[â€”â€“:\-]\s*(.+)", unit_title)
        unit_desc = desc_match.group(1).strip() if desc_match else unit_title
        unit_desc_norm = _normalize_token_text(unit_desc)
        title_tokens = _tokenize_signal(unit_desc_norm)
        topic_phrases = []
        topic_tokens = []

        for topic in topics or []:
            topic_norm = _normalize_token_text(topic_text(topic))
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

    resolved_anchor_starts: List[Optional[int]] = []
    previous_start = -1
    for anchors in anchor_indexes_by_unit:
        chosen_start = None
        for anchor_idx in anchors:
            if anchor_idx > previous_start:
                chosen_start = anchor_idx
                break
        if chosen_start is None and anchors:
            chosen_start = anchors[0]
        resolved_anchor_starts.append(chosen_start)
        if chosen_start is not None:
            previous_start = chosen_start

    result = []
    for unit_idx, descriptor in enumerate(descriptors):
        anchors = anchor_indexes_by_unit[unit_idx]
        matched_dates = []
        if anchors:
            start_idx = resolved_anchor_starts[unit_idx]
            if start_idx is None:
                start_idx = anchors[0]
            next_start_idx = None
            for later_idx in range(unit_idx + 1, len(descriptors)):
                later_start = resolved_anchor_starts[later_idx]
                if later_start is not None:
                    next_start_idx = later_start
                    break
            end_idx = (next_start_idx - 1) if next_start_idx is not None else anchors[-1]
            if end_idx < start_idx:
                end_idx = anchors[-1]
            matched_dates = [d for d in row_dates[start_idx:end_idx + 1] if d]

        matched_dates = list(dict.fromkeys(matched_dates))
        period = f"{matched_dates[0]} a {matched_dates[-1]}" if len(matched_dates) > 1 else (matched_dates[0] if matched_dates else "")
        result.append({
            "unit_title": descriptor["unit_title"],
            "unit_slug": normalize_unit_slug(descriptor["unit_title"]),
            "period": period,
            "dates": ", ".join(matched_dates),
        })

    return result


_KIND_TOKEN_RE = re.compile(r"\{kind=(\w+)\}")
_IGNORED_KINDS = {"suspension", "g2", "ps", "event"}


def _build_timeline_candidate_rows(timeline: List[Dict[str, str]]) -> List[Dict[str, object]]:
    content_keys, date_keys = _infer_timeline_keys(timeline)
    candidate_rows: List[Dict[str, object]] = []
    for index, row in enumerate(timeline or []):
        content = " ".join(row.get(key, "") for key in content_keys).strip()
        date_text = " / ".join(row.get(key, "") for key in date_keys if row.get(key, "")).strip()
        kind = "class"
        match = _KIND_TOKEN_RE.search(content)
        if match:
            kind = match.group(1).strip().lower() or "class"
            content = _collapse_ws(_KIND_TOKEN_RE.sub("", content))
        ignored = kind in _IGNORED_KINDS
        candidate_rows.append({
            "index": index,
            "row": row,
            "content": content,
            "content_norm": _normalize_match_text(content),
            "date_text": date_text,
            "date_dt": _parse_timeline_date_value(date_text),
            "kind": kind,
            "ignored": ignored,
        })
    return candidate_rows


_TIMELINE_GENERIC_TOKENS = {
    "atividade",
    "assincrona",
    "assincrono",
    "aula",
    "aulas",
    "caso",
    "complementar",
    "conteudo",
    "conteudos",
    "dia",
    "estudo",
    "estudos",
    "exercicio",
    "exercicios",
    "gabarito",
    "gabaritos",
    "hora",
    "leituras",
    "lista",
    "listas",
    "material",
    "materia",
    "pagina",
    "paginas",
    "recursos",
    "recomendadas",
    "revisao",
    "revisoes",
    "resposta",
    "respostas",
    "semana",
    "teorica",
    "teoricas",
    "pratica",
    "praticas",
    "apresentacao",
    "continuacao",
    "finalizacao",
    "prova",
    "provas",
    "unidade",
}


_TIMELINE_ADMIN_PHRASES = {
    "suspensao de aulas",
    "suspensao das aulas",
    "suspensao aulas",
    "suspensao da aula",
    "suspensao aula",
    "sem aula",
    "nao havera aula",
    "feriado",
    "recesso",
    "evento academico",
    "prova de substituicao",
    "evento institucional",
    "devolucao",
    "entrega de notas",
    "cancelamento",
    "aula cancelada",
    "aula cancelado",
    "substituicao",
}


_TIMELINE_UNIT_NEUTRAL_TOKENS = {
    "algoritmo",
    "algoritmos",
    "aplicacao",
    "aplicacoes",
    "computa",
    "computacao",
    "computacoes",
    "estado",
    "estados",
    "fundamentos",
    "formal",
    "formais",
    "logica",
    "logicas",
    "para",
    "passo",
    "passos",
    "sequencia",
    "sequencias",
    "metodos",
    "modelo",
    "modelos",
    "predicado",
    "predicados",
    "programa",
    "programas",
    "proposicional",
    "substituicao",
    "simplificacao",
    "software",
    "softwares",
    "suporte",
    "sistemas",
    "semantica",
    "sintaxe",
    "variavel",
    "variaveis",
    "verificacao",
    "verificacoes",
}


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


def _empty_timeline_index() -> dict:
    return {"version": 3, "blocks": []}


def _timeline_specific_tokens(text: str) -> List[str]:
    return [
        token
        for token in _normalize_match_text(text).split()
        if len(token) >= 4 and token not in _TIMELINE_GENERIC_TOKENS
    ]


def _timeline_core_text(text: str) -> str:
    raw = _collapse_ws(text)
    if not raw:
        return ""
    for pattern in (r"\s*:\s*", r"\s+[—–-]\s+"):
        parts = re.split(pattern, raw, maxsplit=1)
        if len(parts) == 2:
            head = _normalize_match_text(parts[0])
            if len(_timeline_specific_tokens(head)) >= 2:
                return head
    return _normalize_match_text(raw)


def _timeline_period_label(start_text: str, end_text: str) -> str:
    start = _collapse_ws(start_text)
    end = _collapse_ws(end_text)
    if not start:
        return end
    if not end or end == start:
        return start
    return f"{start} a {end}"


def _timeline_row_is_review_or_assessment(text: str) -> bool:
    normalized = _normalize_match_text(text)
    if not normalized:
        return False
    if normalized in {"p1", "p2", "p3", "pf"}:
        return True
    return any(token in normalized for token in [
        "revisao",
        "avaliacao",
        "prova 1",
        "prova 2",
        "prova final",
        "teste",
    ])


def _timeline_row_is_unit_anchor_only(text: str) -> bool:
    normalized = _normalize_match_text(text)
    if "unidade" not in normalized:
        return False
    return len(_timeline_specific_tokens(text)) <= 2


def _timeline_text_is_administrative(text: str) -> bool:
    normalized = _normalize_match_text(text)
    if not normalized:
        return False
    return any(phrase in normalized for phrase in _TIMELINE_ADMIN_PHRASES)


def _timeline_unit_number_from_text(text: str) -> Optional[int]:
    normalized = _normalize_match_text(text)
    if not normalized:
        return None
    match = re.search(r"\bunidade(?: de aprendizagem)?\s*0*(\d+)\b", normalized)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _timeline_unit_number_from_unit(unit: dict) -> Optional[int]:
    slug = str(unit.get("slug", "") or "")
    match = re.match(r"^unidade(?:-de-aprendizagem)?-(\d+)\b", slug)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _score_timeline_unit_phrase(row_norm: str, row_tokens: set[str], phrase: str, token_weights: dict) -> float:
    phrase_norm = _normalize_match_text(phrase)
    if not phrase_norm:
        return 0.0
    if phrase_norm in row_norm:
        return 3.8

    phrase_tokens = [
        token for token in phrase_norm.split()
        if len(token) >= 4 and token not in _TIMELINE_UNIT_NEUTRAL_TOKENS
    ]
    if not phrase_tokens:
        return 0.0

    hits = [token for token in phrase_tokens if token in row_tokens]
    if not hits:
        return 0.0

    if len(phrase_tokens) == 1:
        return 1.15 * token_weights.get(hits[0], 1.0)
    if len(hits) == len(phrase_tokens):
        return 1.15 + sum(0.95 * token_weights.get(token, 1.0) for token in hits)
    if len(hits) >= 2:
        return sum(0.85 * token_weights.get(token, 1.0) for token in hits)
    return 0.0


def _extract_timeline_topics(rows: List[Dict[str, object]]) -> tuple[List[str], List[str], str]:
    topics: List[str] = []
    aliases: List[str] = []
    seen_topics = set()
    seen_aliases = set()
    topic_tokens: List[str] = []

    for row in rows or []:
        text = _collapse_ws(str(row.get("content", "")))
        if not text:
            continue
        core = _timeline_core_text(text)
        core_tokens = _timeline_specific_tokens(core)
        if core_tokens:
            normalized_core = " ".join(core_tokens)
            if normalized_core not in seen_topics:
                seen_topics.add(normalized_core)
                topics.append(normalized_core)
            for token in core_tokens:
                if token not in seen_aliases and len(token) >= 5:
                    seen_aliases.add(token)
                    aliases.append(token)
        full_tokens = _timeline_specific_tokens(text)
        for token in full_tokens:
            if token not in topic_tokens:
                topic_tokens.append(token)

    return topics[:6], aliases[:6], " ".join(topic_tokens)


def _extract_block_card_evidence(rows: List[Dict[str, object]]) -> List[Dict[str, str]]:
    card_items: List[Dict[str, str]] = []
    seen = set()
    for row in rows or []:
        text = _collapse_ws(str(row.get("content", "") or ""))
        if not text:
            continue
        for item in extract_card_evidence(text):
            normalized_title = _collapse_ws(str(item.get("normalized_title", "") or ""))
            source_kind = _collapse_ws(str(item.get("source_kind", "") or ""))
            title = _collapse_ws(str(item.get("title", "") or ""))
            if not normalized_title:
                continue
            dedupe_key = (source_kind, normalized_title, title)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            card_items.append(item)
    return card_items


def _session_card_evidence(session: Dict[str, object], card_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not card_items:
        return []

    session_text = " ".join(
        _collapse_ws(str(part or ""))
        for part in [
            session.get("label", ""),
            " ".join(str(signal) for signal in (session.get("signals", []) or [])),
        ]
        if _collapse_ws(str(part or ""))
    ).strip()
    session_norm = _normalize_match_text(session_text)
    if not session_norm:
        return []

    session_tokens = {token for token in session_norm.split() if len(token) >= 4}
    matched: List[Dict[str, str]] = []
    seen = set()

    for item in card_items:
        normalized_title = _collapse_ws(str(item.get("normalized_title", "") or ""))
        if not normalized_title:
            continue
        title_tokens = [token for token in normalized_title.split() if len(token) >= 4]
        if not title_tokens:
            continue

        if normalized_title in session_norm:
            matches = True
        elif len(title_tokens) == 1:
            matches = title_tokens[0] in session_tokens
        else:
            matches = len(set(title_tokens) & session_tokens) >= 2

        if not matches:
            continue

        dedupe_key = (
            _collapse_ws(str(item.get("source_kind", "") or "")),
            normalized_title,
            _collapse_ws(str(item.get("title", "") or "")),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        matched.append(item)

    return matched


def _attach_card_evidence_to_sessions(
    sessions: List[Dict[str, object]],
    card_items: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    if not sessions:
        return []
    if not card_items:
        return [dict(session) for session in sessions]

    attached_sessions: List[Dict[str, object]] = []
    for session in sessions:
        payload = dict(session)
        matched = _session_card_evidence(payload, card_items)
        if matched:
            payload["card_evidence"] = matched
        attached_sessions.append(payload)
    return attached_sessions


def _extract_block_sessions(rows: List[Dict[str, object]], block_id: str) -> List[Dict[str, object]]:
    session_texts: List[str] = []
    for row in rows or []:
        content = _collapse_ws(str(row.get("content", "") or ""))
        date_text = _collapse_ws(str(row.get("date_text", "") or ""))
        if date_text and content:
            session_texts.append(f"{date_text}: {content}")
        elif date_text:
            session_texts.append(date_text)
        elif content:
            session_texts.append(content)

    extracted_sessions: List[Dict[str, object]] = []
    seen = set()
    async_counter = 0
    class_counter = 0

    for text in session_texts:
        for item in extract_timeline_session_signals(text):
            kind = str(item.get("kind", "") or "")
            date = str(item.get("date", "") or "")
            label = _collapse_ws(str(item.get("label", "") or ""))
            signals = [
                str(signal)
                for signal in (item.get("signals", []) or [])
                if _collapse_ws(str(signal))
            ]
            dedupe_key = (kind, date, label, tuple(signals))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            if kind == "async":
                async_counter += 1
                session_id = f"{block_id}-sessao-async-{async_counter:02d}"
            else:
                class_counter += 1
                session_id = f"{block_id}-sessao-{date or f'{class_counter:02d}'}"

            extracted_sessions.append(
                {
                    "id": session_id,
                    "date": date,
                    "kind": kind or "class",
                    "label": label,
                    "signals": signals,
                }
            )

    return extracted_sessions


def _row_looks_like_continuation(row_text: str) -> bool:
    text = _normalize_match_text(row_text)
    if not text:
        return False
    return any(term in text for term in [
        "atividade assincrona",
        "atividade assíncrona",
        "complementar os estudos",
        "leituras recomendadas",
        "estudo de caso",
        "revisao",
        "revisão",
        "exercicio",
        "exercicios",
        "lista",
        "listas",
        "gabarito",
        "respostas",
    ])


def _rows_belong_to_same_thematic_block(
    previous_row: Dict[str, object],
    current_row: Dict[str, object],
    current_rows: Optional[List[Dict[str, object]]] = None,
) -> bool:
    previous_text = str(previous_row.get("content", ""))
    current_text = str(current_row.get("content", ""))
    if not previous_text or not current_text:
        return False

    if _timeline_row_is_review_or_assessment(current_text):
        return False

    block_tokens = set()
    for row in current_rows or [previous_row]:
        block_tokens.update(_timeline_specific_tokens(str(row.get("content", ""))))

    if _row_looks_like_continuation(current_text):
        has_only_unit_anchors = all(
            _timeline_row_is_unit_anchor_only(str(row.get("content", "")))
            for row in current_rows or [previous_row]
        )
        return bool(block_tokens) and not has_only_unit_anchors

    previous_core = _timeline_core_text(previous_text)
    current_core = _timeline_core_text(current_text)
    previous_tokens = set(_timeline_specific_tokens(previous_core))
    current_tokens = set(_timeline_specific_tokens(current_core))
    if not current_tokens:
        return True
    if previous_core and current_core:
        if previous_core == current_core:
            return True
        if previous_core in current_core or current_core in previous_core:
            shorter = current_core if len(current_core) <= len(previous_core) else previous_core
            if len(_timeline_specific_tokens(shorter)) >= 2:
                return True

    overlap = current_tokens & block_tokens
    return len(overlap) >= 2


def _timeline_block_is_soft_continuation(block: Dict[str, object]) -> bool:
    rows = block.get("rows", []) or []
    if not rows:
        return False
    has_generic_continuation = False
    for row in rows:
        text = str(row.get("content", ""))
        if _timeline_row_is_review_or_assessment(text):
            return False
        if _row_looks_like_continuation(text):
            has_generic_continuation = True
            continue
        normalized = _normalize_match_text(text)
        if any(token in normalized for token in ["unidade", "continuacao", "finalizacao", "apresentacao"]):
            has_generic_continuation = True
            continue
        return False
    return has_generic_continuation


def _timeline_block_is_noninstructional(block: Dict[str, object]) -> bool:
    rows = block.get("rows", []) or []
    if not rows:
        return False
    has_content = False
    for row in rows:
        text = str(row.get("content", "")).strip()
        if not text:
            continue
        has_content = True
        if _timeline_text_is_administrative(text) or _timeline_row_is_review_or_assessment(text):
            continue
        if _row_looks_like_continuation(text) and len(_timeline_specific_tokens(text)) <= 1:
            continue
        return False
    return has_content


def _timeline_block_is_administrative_only(block: Dict[str, object]) -> bool:
    rows = block.get("rows", []) or []
    if not rows:
        return False
    if all(bool(row.get("ignored")) for row in rows):
        return True
    has_content = False
    for row in rows:
        if bool(row.get("ignored")):
            continue
        text = str(row.get("content", "")).strip()
        if not text:
            continue
        has_content = True
        if _timeline_text_is_administrative(text):
            continue
        return False
    return has_content


def _assign_timeline_block_to_unit(block: Dict[str, object], unit_index: list) -> tuple[str, float]:
    if not unit_index:
        return "", 0.0
    if _timeline_block_is_noninstructional(block):
        return "", 0.0

    full_text = " ".join(
        _normalize_match_text(str(row.get("content", "")))
        for row in block.get("rows", []) or []
        if str(row.get("content", "")).strip()
    ).strip()
    topic_text = str(block.get("topic_text", "")).strip()
    if not full_text and not topic_text:
        return "", 0.0
    if all(
        _timeline_text_is_administrative(text)
        for text in [full_text, topic_text]
        if text
    ):
        return "", 0.0

    scored = []
    for unit in unit_index:
        score = 0.0
        if full_text:
            score += _score_timeline_row_against_unit(full_text, unit)
        if topic_text and topic_text != full_text:
            score += _score_timeline_row_against_unit(topic_text, unit) * 0.7
        if score > 0:
            scored.append((unit, score))

    if not scored:
        return "", 0.0

    scored.sort(key=lambda item: item[1], reverse=True)
    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    if winner_score < 1.0 or abs(winner_score - runner_up_score) < 0.35:
        return "", 0.0

    confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.18)))
    return winner.get("slug", ""), confidence


def _serialize_timeline_index(timeline_index: dict) -> dict:
    blocks = []
    for block in (timeline_index or {}).get("blocks", []) or []:
        if _timeline_block_is_administrative_only(block):
            continue
        payload = {
            "id": block.get("id", ""),
            "period_start": block.get("period_start", ""),
            "period_end": block.get("period_end", ""),
            "period_label": block.get("period_label", ""),
            "unit_slug": block.get("unit_slug", ""),
            "unit_confidence": float(block.get("unit_confidence", 0.0) or 0.0),
            "primary_topic_slug": block.get("primary_topic_slug", ""),
            "primary_topic_label": block.get("primary_topic_label", ""),
            "primary_topic_confidence": float(block.get("primary_topic_confidence", 0.0) or 0.0),
            "topic_ambiguous": bool(block.get("topic_ambiguous", False)),
            "topic_candidates": list(block.get("topic_candidates", []) or []),
            "topic_text": block.get("topic_text", ""),
            "topics": list(block.get("topics", []) or []),
            "aliases": list(block.get("aliases", []) or []),
            "card_evidence": list(block.get("card_evidence", []) or []),
            "sessions": list(block.get("sessions", []) or []),
            "source_rows": list(block.get("source_rows", []) or []),
        }
        blocks.append(payload)
    return {"version": 3, "blocks": blocks}


def _write_internal_timeline_index(root_dir: Path, timeline_index: dict) -> None:
    write_text(
        root_dir / "course" / ".timeline_index.json",
        json.dumps(_serialize_timeline_index(timeline_index), ensure_ascii=False, indent=2),
    )


_TEACHING_PLAN_ASSESSMENT_START = re.compile(r"^(?:AVALIA[ÇC][AÃ]O|AVALIACAO)\b", re.IGNORECASE)
_TEACHING_PLAN_ASSESSMENT_STOP = re.compile(
    r"^(?:BIBLIOGRAFIA|METODOLOGIA|CRONOGRAMA|CONTEUDO PROGRAMATICO|CONTEUDO)\b",
    re.IGNORECASE,
)
_ASSESSMENT_LINE_RE = re.compile(
    r"^(?P<label>(?:P\s*\d+|PROVA\s*\d+|PF|PROVA\s+FINAL|EXAME\s+FINAL))\s*(?:[-:]\s*|\s+)(?P<desc>.+)$",
    re.IGNORECASE,
)


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


def _canonical_assessment_label(raw_label: str, *, normalize_match_text: Callable[[str], str]) -> str:
    normalized = normalize_match_text(raw_label)
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


def _assessment_label_aliases(label_slug: str, *, normalize_match_text: Callable[[str], str]) -> List[str]:
    normalized = normalize_match_text(label_slug)
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


def _extract_declared_unit_numbers(
    text: str,
    *,
    normalize_match_text: Callable[[str], str],
    label_slug: str = "",
) -> List[int]:
    normalized = normalize_match_text(text)
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
    label_match = re.match(r"^(?:p|prova)\s*(\d+)$", normalize_match_text(label_slug))
    if label_match:
        try:
            label_number = int(label_match.group(1))
        except ValueError:
            label_number = None
        else:
            if label_number in numbers:
                numbers.remove(label_number)
    return list(dict.fromkeys(numbers))


def _parse_assessments_from_teaching_plan(
    text: str,
    *,
    normalize_match_text: Callable[[str], str],
    normalize_teaching_plan_heading: Callable[[str], str],
) -> List[dict]:
    assessments: List[dict] = []
    if not text:
        return assessments

    in_section = False
    current: Optional[dict] = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized = normalize_teaching_plan_heading(line)
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
            label_slug = _canonical_assessment_label(
                match.group("label"),
                normalize_match_text=normalize_match_text,
            )
            if not label_slug:
                continue
            desc = _collapse_ws(match.group("desc"))
            current = {
                "label": label_slug,
                "label_slug": normalize_match_text(label_slug),
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
        item["label"] = _canonical_assessment_label(
            item.get("label", label_slug),
            normalize_match_text=normalize_match_text,
        )
        item["label_slug"] = normalize_match_text(label_slug or item["label"])
        item["declared_unit_numbers"] = _extract_declared_unit_numbers(
            description,
            normalize_match_text=normalize_match_text,
            label_slug=item["label_slug"],
        )
        item["raw_lines"] = list(dict.fromkeys(item.get("raw_lines", []) or []))

    return assessments


def _assessment_match_row_text(row: dict, *, normalize_match_text: Callable[[str], str]) -> str:
    return normalize_match_text(" ".join(str(value) for value in row.values() if str(value).strip()))


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


def _build_file_map_timeline_context_from_course(
    course_meta: dict,
    subject_profile=None,
    content_taxonomy: Optional[dict] = None,
    *,
    build_file_map_unit_index_from_course: Callable[[dict, object], list],
    build_file_map_content_taxonomy_from_course: Callable[[dict, object], dict],
) -> dict:
    test_context = course_meta.get("_timeline_context") or course_meta.get("_timeline_context_for_tests")
    if test_context:
        return dict(test_context)

    unit_index = build_file_map_unit_index_from_course(course_meta, subject_profile)
    content_taxonomy = content_taxonomy or build_file_map_content_taxonomy_from_course(course_meta, subject_profile)
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


def _build_assessment_context_from_course(
    course_meta: dict,
    subject_profile=None,
    timeline_context: Optional[dict] = None,
    *,
    build_file_map_unit_index_from_course: Callable[[dict, object], list],
    build_file_map_timeline_context_from_course: Callable[..., dict],
    normalize_match_text: Callable[[str], str],
    normalize_teaching_plan_heading: Callable[[str], str],
) -> dict:
    test_context = course_meta.get("_assessment_context") or course_meta.get("_assessment_context_for_tests")
    if test_context:
        return dict(test_context)

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    syllabus = getattr(subject_profile, "syllabus", "") if subject_profile else ""
    if not teaching_plan and not syllabus:
        return {"version": 1, "assessments": [], "conflicts": []}

    timeline_rows = _parse_syllabus_timeline(syllabus) if syllabus else []
    unit_index = build_file_map_unit_index_from_course(course_meta, subject_profile)
    if timeline_context is None:
        timeline_context = build_file_map_timeline_context_from_course(course_meta, subject_profile)
    unit_period_bounds = (timeline_context or {}).get("unit_period_bounds", {}) or {}
    unit_periods = (timeline_context or {}).get("unit_periods", {}) or {}
    unit_by_slug = {str(unit.get("slug", "") or ""): unit for unit in unit_index if str(unit.get("slug", "") or "").strip()}

    assessments = _parse_assessments_from_teaching_plan(
        teaching_plan,
        normalize_match_text=normalize_match_text,
        normalize_teaching_plan_heading=normalize_teaching_plan_heading,
    )
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
        aliases = _assessment_label_aliases(label_slug, normalize_match_text=normalize_match_text)
        matched_rows = [
            row
            for row in timeline_rows
            if any(
                alias and re.search(rf"\b{re.escape(alias)}\b", _assessment_match_row_text(row, normalize_match_text=normalize_match_text))
                for alias in aliases
            )
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
                    start_dt, _end_dt = unit_period_bounds.get(unit_slug, (None, None))
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


def _score_timeline_row_against_unit(row_text: str, unit: dict) -> float:
    row_norm = _normalize_match_text(row_text)
    if not row_norm or not unit:
        return 0.0
    if _timeline_text_is_administrative(row_norm):
        return 0.0

    row_tokens = [tok for tok in row_norm.split() if len(tok) >= 4]
    row_token_set = set(row_tokens)
    unit_title = unit.get("normalized_title", "")
    topic_phrases = unit.get("topic_phrases", []) or []
    topic_tokens = unit.get("topic_tokens", []) or []
    title_anchor_tokens = unit.get("title_anchor_tokens", []) or []
    topic_anchor_tokens = unit.get("topic_anchor_tokens", []) or []
    extra_signals = unit.get("extra_signals", []) or []
    distinctive_tokens = unit.get("distinctive_tokens", []) or []
    token_weights = unit.get("token_weights", {}) or {}

    score = 0.0
    exact_phrase_hits = 0
    matched_specific_tokens = set()
    distinctive_hits = 0
    composite_anchor_hits = 0

    explicit_unit_number = _timeline_unit_number_from_text(row_norm)
    unit_number = _timeline_unit_number_from_unit(unit)
    if explicit_unit_number is not None:
        if unit_number != explicit_unit_number:
            return 0.0
        score += 6.0

    if unit_title and unit_title in row_norm:
        score += 2.6
        exact_phrase_hits += 1
    elif unit_title:
        score += _score_timeline_unit_phrase(row_norm, row_token_set, unit_title, token_weights) * 0.55

    for topic_phrase in topic_phrases:
        phrase_score = _score_timeline_unit_phrase(row_norm, row_token_set, topic_phrase, token_weights)
        if phrase_score > 0.0:
            if _normalize_match_text(topic_phrase) in row_norm:
                exact_phrase_hits += 1
            score += phrase_score

    for topic_token in topic_tokens:
        if not topic_token or " " in topic_token or topic_token not in row_token_set:
            continue
        weight = token_weights.get(topic_token, 1.0)
        if topic_token in _TIMELINE_UNIT_NEUTRAL_TOKENS:
            weight *= 0.2
        else:
            matched_specific_tokens.add(topic_token)
        score += 0.95 * weight

    for token in distinctive_tokens:
        if token in row_token_set:
            score += 0.25 if token in matched_specific_tokens else 0.8
            matched_specific_tokens.add(token)
            distinctive_hits += 1

    title_anchor_hits = {token for token in title_anchor_tokens if token in row_token_set}
    topic_anchor_hits = {token for token in topic_anchor_tokens if token in row_token_set}
    if extra_signals and title_anchor_hits and topic_anchor_hits:
        shared_hits = title_anchor_hits & topic_anchor_hits
        score += 0.95 + (0.2 * len(title_anchor_hits | topic_anchor_hits))
        if shared_hits:
            score += 0.12 * len(shared_hits)
        composite_anchor_hits = len(title_anchor_hits | topic_anchor_hits)

    if (
        explicit_unit_number is None
        and exact_phrase_hits == 0
        and distinctive_hits == 0
        and not matched_specific_tokens
        and composite_anchor_hits == 0
    ):
        return 0.0
    if explicit_unit_number is None and exact_phrase_hits == 0 and len(matched_specific_tokens) == 1:
        score *= 0.35

    return score


def _iter_content_taxonomy_topics(taxonomy: dict) -> List[dict]:
    topics: List[dict] = []
    seen = set()
    for unit in (taxonomy or {}).get("units", []) or []:
        unit_slug = _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
        unit_title = _collapse_ws(str(unit.get("title", "") or ""))
        for topic in unit.get("topics", []) or []:
            topic_slug = slugify(str(topic.get("slug", "") or ""))
            topic_label = _collapse_ws(str(topic.get("label", "") or ""))
            if not topic_slug or not topic_label:
                continue
            dedupe_key = (unit_slug, topic_slug)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            topics.append(
                {
                    "unit_slug": unit_slug,
                    "unit_title": unit_title,
                    "topic_slug": topic_slug,
                    "topic_label": topic_label,
                    "topic_code": str(topic.get("code", "") or ""),
                    "kind": str(topic.get("kind", "") or "topic"),
                    "aliases": [str(alias) for alias in (topic.get("aliases", []) or []) if _collapse_ws(str(alias))],
                }
            )
    return topics


def _score_entry_against_taxonomy_topic(signals: dict, topic: dict) -> float:
    title_text = signals.get("title_text", "")
    markdown_headings_text = signals.get("markdown_headings_text", "")
    markdown_lead_text = signals.get("markdown_lead_text", "")
    markdown_text = signals.get("markdown_text", "")
    category_text = signals.get("category_text", "")
    manual_tags_text = signals.get("manual_tags_text", "")
    auto_tags_text = signals.get("auto_tags_text", "")
    legacy_tags_text = signals.get("legacy_tags_text", "")
    raw_text = signals.get("raw_text", "")
    label = _collapse_ws(str(topic.get("topic_label", "") or ""))
    topic_slug = _collapse_ws(str(topic.get("topic_slug", "") or ""))
    aliases = [str(alias) for alias in (topic.get("aliases", []) or []) if _collapse_ws(str(alias))]

    if not label and not topic_slug and not aliases:
        return 0.0

    score = 0.0
    exact_hits = 0
    for text, weight in [
        (markdown_headings_text, 4.4),
        (title_text, 3.8),
        (markdown_lead_text, 2.8),
        (manual_tags_text, 3.0),
        (markdown_text, 1.1),
        (auto_tags_text, 0.22),
        (legacy_tags_text, 0.15),
        (raw_text, 0.9),
    ]:
        if label and _matches_normalized_phrase(text, label):
            score += weight
            exact_hits += 1
        if topic_slug:
            slug_phrase = topic_slug.replace("-", " ")
            if slug_phrase and _matches_normalized_phrase(text, slug_phrase):
                score += weight * 0.65
                exact_hits += 1
        for alias in aliases:
            alias_norm = _normalize_match_text(alias)
            if not alias_norm:
                continue
            if _matches_normalized_phrase(text, alias_norm):
                score += weight * 0.82
                exact_hits += 1

    topic_tokens = {
        token
        for token in _normalize_match_text(label).split()
        if len(token) >= 4 and token not in _UNIT_GENERIC_TOKENS
    }
    if topic_slug:
        topic_tokens.update(
            token
            for token in _normalize_match_text(topic_slug.replace("-", " ")).split()
            if len(token) >= 4 and token not in _UNIT_GENERIC_TOKENS
        )
    for alias in aliases:
        topic_tokens.update(
            token
            for token in _normalize_match_text(alias).split()
            if len(token) >= 4 and token not in _UNIT_GENERIC_TOKENS
        )

    signal_tokens = {
        token
        for text, _weight in [
            (markdown_headings_text, 1.0),
            (title_text, 1.0),
            (markdown_lead_text, 1.0),
            (manual_tags_text, 1.0),
            (markdown_text, 1.0),
            (auto_tags_text, 1.0),
            (legacy_tags_text, 1.0),
            (raw_text, 1.0),
        ]
        for token in text.split()
        if len(token) >= 4
    }
    overlap = topic_tokens & signal_tokens
    if len(topic_tokens) == 1:
        if overlap:
            score += 0.9
    elif len(overlap) >= len(topic_tokens):
        score += 1.4 + (0.22 * len(overlap))
    elif len(overlap) >= 2:
        score += 0.9 + (0.18 * len(overlap))
    elif len(overlap) == 1:
        score += 0.25

    if category_text in {"listas", "gabaritos"} and overlap:
        score += 0.08
    if str(topic.get("kind", "") or "") == "subtopic":
        score += 0.04

    if exact_hits == 0 and score > 0.0:
        score *= 0.72
    if exact_hits == 0 and len(overlap) <= 1:
        score *= 0.68
    if auto_tags_text and exact_hits == 0 and len(overlap) <= 1:
        score *= 0.88
    if legacy_tags_text and exact_hits == 0:
        score *= 0.9
    return score


def _build_timeline_block_topic_signals(block: Dict[str, object]) -> dict:
    rows = block.get("rows", []) or []
    row_texts = []
    raw_texts = []
    for row in rows:
        text = _collapse_ws(str(row.get("content", "")))
        if not text:
            continue
        normalized = _normalize_match_text(text)
        if normalized:
            row_texts.append(normalized)
        raw_texts.append(text)

    topic_text = _normalize_match_text(str(block.get("topic_text", "") or ""))
    alias_text = _normalize_match_text(" ".join(str(alias) for alias in (block.get("aliases", []) or [])))
    combined_text = " ".join(row_texts)
    return {
        "title_text": topic_text,
        "markdown_text": combined_text,
        "category_text": "",
        "tags_text": alias_text,
        "raw_text": _normalize_match_text(" ".join(raw_texts)),
    }


def _score_timeline_block_against_taxonomy_topic(block: Dict[str, object], topic: dict) -> float:
    signals = _build_timeline_block_topic_signals(block)
    score = _score_entry_against_taxonomy_topic(signals, topic)
    kind = str(topic.get("kind", "") or "topic")
    if kind == "subtopic":
        score += 0.18
    return score


def _assign_timeline_block_to_topic(
    block: Dict[str, object],
    topic_index: List[dict],
    taxonomy: dict,
) -> tuple[List[dict], TopicMatchResult]:
    del taxonomy
    if not topic_index or _timeline_block_is_noninstructional(block):
        return [], TopicMatchResult(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=["sem-topicos"],
        )

    scored = []
    for topic in topic_index:
        score = _score_timeline_block_against_taxonomy_topic(block, topic)
        if score > 0:
            scored.append((topic, score))

    if not scored:
        return [], TopicMatchResult(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=0.0,
            ambiguous=True,
            reasons=["sem-candidatos"],
        )

    scored.sort(key=lambda item: item[1], reverse=True)
    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    winner_topic_text = _normalize_match_text(
        str(winner.get("topic_label", "") or winner.get("topic_slug", "") or "")
    )
    winner_topic_tokens = [tok for tok in winner_topic_text.split() if len(tok) >= 4]
    topic_token_count = len(winner_topic_tokens)

    confidence = min(1.0, max(0.0, (winner_score - runner_up_score) + (winner_score * 0.2)))
    if len(scored) == 1:
        ambiguous = winner_score <= 0.0
        if not ambiguous:
            confidence = max(confidence, 0.72)
    else:
        ambiguous = winner_score <= 0.0 or abs(winner_score - runner_up_score) < 0.7
    if topic_token_count <= 1:
        min_score = 1.85
        min_confidence = 0.8
    elif topic_token_count == 2:
        min_score = 1.75
        min_confidence = 0.9
    else:
        min_score = 1.35
        min_confidence = 0.72
    weak_topic = winner_score < min_score or confidence < min_confidence
    if weak_topic:
        ambiguous = True
    if ambiguous:
        confidence = min(confidence, 0.45)

    topic_candidates: List[dict] = []
    for topic, score in scored[:5]:
        relative_confidence = 0.0 if winner_score <= 0.0 else min(1.0, max(0.0, score / winner_score))
        topic_candidates.append(
            {
                "topic_slug": str(topic.get("topic_slug", "") or ""),
                "topic_label": str(topic.get("topic_label", "") or ""),
                "unit_slug": str(topic.get("unit_slug", "") or ""),
                "kind": str(topic.get("kind", "") or "topic"),
                "aliases": list(topic.get("aliases", []) or []),
                "score": round(float(score), 3),
                "confidence": round(relative_confidence, 3),
            }
        )

    if weak_topic:
        return topic_candidates, TopicMatchResult(
            topic_slug="",
            topic_label="",
            unit_slug="",
            confidence=confidence,
            ambiguous=True,
            reasons=[f"winner_score={winner_score:.2f}", "weak-topic", "ambiguous"],
        )

    primary = TopicMatchResult(
        topic_slug=str(winner.get("topic_slug", "") or ""),
        topic_label=str(winner.get("topic_label", "") or ""),
        unit_slug=str(winner.get("unit_slug", "") or ""),
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=[f"winner_score={winner_score:.2f}"] + (["ambiguous"] if ambiguous else []),
    )
    return topic_candidates, primary


def _derive_unit_from_topic_match(match: TopicMatchResult, taxonomy: dict) -> str:
    if not match or not match.topic_slug:
        return ""
    topic_slug = slugify(str(match.topic_slug or ""))
    if not topic_slug:
        return ""

    valid_units = {
        _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or "")): _normalize_unit_slug(
            str(unit.get("slug", "") or unit.get("title", "") or "")
        )
        for unit in (taxonomy or {}).get("units", []) or []
        if _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
    }

    candidate_unit = _normalize_unit_slug(match.unit_slug)
    if candidate_unit and candidate_unit in valid_units:
        return valid_units[candidate_unit]

    for unit in (taxonomy or {}).get("units", []) or []:
        unit_slug = _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
        for topic in unit.get("topics", []) or []:
            current_topic_slug = slugify(str(topic.get("slug", "") or ""))
            if current_topic_slug == topic_slug:
                return unit_slug
    return candidate_unit


def _build_timeline_index(
    candidate_rows: List[Dict[str, object]],
    unit_index: list,
    content_taxonomy: Optional[dict] = None,
) -> dict:
    if not candidate_rows:
        return _empty_timeline_index()

    blocks: List[Dict[str, object]] = []
    current_rows: List[Dict[str, object]] = []

    for row in candidate_rows:
        content = str(row.get("content", "")).strip()
        if not content:
            continue

        if not current_rows:
            current_rows = [row]
            continue

        if _rows_belong_to_same_thematic_block(current_rows[-1], row, current_rows=current_rows):
            current_rows.append(row)
            continue

        blocks.append({"rows": current_rows})
        current_rows = [row]

    if current_rows:
        blocks.append({"rows": current_rows})

    runtime_blocks: List[Dict[str, object]] = []
    topic_index = _iter_content_taxonomy_topics(content_taxonomy) if content_taxonomy else []
    for position, block in enumerate(blocks, start=1):
        rows = block.get("rows", []) or []
        if not rows:
            continue
        start_text = str(rows[0].get("date_text", "")).strip()
        end_text = str(rows[-1].get("date_text", "")).strip()
        topics, aliases, topic_text = _extract_timeline_topics(rows)
        runtime_block = {
            "id": f"bloco-{position:02d}",
            "period_start": rows[0].get("date_dt").strftime("%Y-%m-%d") if rows[0].get("date_dt") else "",
            "period_end": rows[-1].get("date_dt").strftime("%Y-%m-%d") if rows[-1].get("date_dt") else "",
            "period_label": _timeline_period_label(start_text, end_text),
            "unit_slug": "",
            "unit_confidence": 0.0,
            "primary_topic_slug": "",
            "primary_topic_label": "",
            "primary_topic_confidence": 0.0,
            "topic_ambiguous": True,
            "topic_candidates": [],
            "topic_text": topic_text,
            "topics": topics,
            "aliases": aliases,
            "card_evidence": _extract_block_card_evidence(rows),
            "sessions": [],
            "source_rows": [int(row.get("index", 0)) for row in rows],
            "rows": rows,
        }
        runtime_block["sessions"] = _attach_card_evidence_to_sessions(
            _extract_block_sessions(rows, f"bloco-{position:02d}"),
            runtime_block["card_evidence"],
        )
        topic_candidates, primary_topic = _assign_timeline_block_to_topic(runtime_block, topic_index, content_taxonomy or {})
        runtime_block["topic_candidates"] = topic_candidates
        runtime_block["primary_topic_slug"] = primary_topic.topic_slug
        runtime_block["primary_topic_label"] = primary_topic.topic_label
        runtime_block["primary_topic_confidence"] = primary_topic.confidence
        runtime_block["topic_ambiguous"] = primary_topic.ambiguous
        topic_unit_slug = ""
        if primary_topic.topic_slug and not primary_topic.ambiguous and primary_topic.confidence >= 0.65:
            topic_unit_slug = _derive_unit_from_topic_match(primary_topic, content_taxonomy or {})
        if topic_unit_slug:
            runtime_block["unit_slug"] = topic_unit_slug
            runtime_block["unit_confidence"] = primary_topic.confidence
        else:
            unit_slug, unit_confidence = _assign_timeline_block_to_unit(runtime_block, unit_index)
            runtime_block["unit_slug"] = unit_slug
            runtime_block["unit_confidence"] = unit_confidence
        runtime_blocks.append(runtime_block)

    for index, block in enumerate(runtime_blocks):
        if block.get("unit_slug") or not _timeline_block_is_soft_continuation(block):
            continue
        previous_slug = runtime_blocks[index - 1].get("unit_slug", "") if index > 0 else ""
        next_slug = runtime_blocks[index + 1].get("unit_slug", "") if index + 1 < len(runtime_blocks) else ""
        inherited_slug = previous_slug or next_slug
        if inherited_slug:
            block["unit_slug"] = inherited_slug
            block["unit_confidence"] = max(float(block.get("unit_confidence", 0.0) or 0.0), 0.51)

    return {"version": 3, "blocks": runtime_blocks}
