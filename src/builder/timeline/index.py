from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.builder.vision.card_evidence import extract_card_evidence
from src.builder.timeline.signals import extract_timeline_session_signals
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind
from src.builder.timeline.curation import apply_block_curation
from src.builder.timeline.unit_matcher import assign_units_positional
from src.builder.text.normalize import (
    normalize_match_text as _normalize_match_text,
    signal_token_set as _signal_token_set,
)
from src.builder.routing.thresholds import margin_confidence, T
from src.builder.routing.file_map import UNIT_GENERIC_TOKENS
from src.builder.extraction.teaching_plan import _normalize_unit_slug
from src.builder.text.stopwords import (
    TIMELINE_GENERIC_TOKENS as _TIMELINE_GENERIC_TOKENS,
    TIMELINE_UNIT_NEUTRAL_TOKENS as _TIMELINE_UNIT_NEUTRAL_TOKENS,
)
from src.utils.helpers import slugify, ATIVIDADE_KIND_MAP, norm_ascii_lower, collapse_ws as _collapse_ws


TIMELINE_INDEX_VERSION = 4


def ensure_block_kind(block: dict) -> dict:
    """Lazy backfill: garante `kind` no bloco. Idempotente."""
    if not isinstance(block, dict):
        return block
    if not block.get("kind"):
        block["kind"] = classify_block(block).value
    return block


def finalize_block(block: dict) -> dict:
    """Garante `kind` e limpa unidade de blocos nao-aula.

    Provas/feriados/revisoes/etc nao tem unidade pedagogica. Override manual de
    unidade (`block_manual_unit_slug`) sempre preservado. Idempotente.
    """
    if not isinstance(block, dict):
        return block
    ensure_block_kind(block)
    if block.get("kind") != BlockKind.CLASS.value and not block.get("block_manual_unit_slug"):
        block["unit_slug"] = ""
        block["unit_confidence"] = 0.0
    return block


def _backfill_timeline_index(timeline_index: dict) -> dict:
    """Lazy upgrade v3->v4: bump version, popula `kind` em cada bloco. In-place."""
    if not isinstance(timeline_index, dict):
        return timeline_index
    for block in timeline_index.get("blocks") or []:
        finalize_block(block)
    timeline_index["version"] = TIMELINE_INDEX_VERSION
    return timeline_index


def _apply_curation_overrides(timeline_index: dict, course_dir: Path) -> int:
    """Merge da curation manual + re-derivacao de kind/topic. In-place.

    `apply_block_curation` so injeta os campos crus `manual_*`; aqui re-derivamos
    o que depende deles: `kind` (classifier honra `manual_kind_override`) e o
    label/source de topico (camada `manual` vence em `_resolve_block_topic_label`).
    """
    if not isinstance(timeline_index, dict):
        return 0
    blocks = timeline_index.get("blocks") or []
    touched = apply_block_curation(blocks, course_dir)
    if not touched:
        return 0
    for block in blocks:
        if block.get("manual_kind_override"):
            block["kind"] = ""  # forca re-derivacao limpa
            finalize_block(block)
            # source_kind (hint de linha do SARC) NAO e re-derivado aqui: e
            # row-level; o override manual ja vence o source_kind em classify_block.
        if block.get("manual_topic_label"):
            label, slug, source = _resolve_block_topic_label(block)
            if label:
                block["primary_topic_label"] = label
                block["topic_source"] = source
                if slug:
                    block["primary_topic_slug"] = slug
        manual_unit = block.get("block_manual_unit_slug")
        if isinstance(manual_unit, str) and manual_unit.strip():
            block["unit_slug"] = manual_unit.strip()
            block["unit_confidence"] = 1.0
    return touched


def _matches_normalized_phrase(signal_text: str, phrase: str) -> bool:
    normalized_signal = _normalize_match_text(signal_text)
    normalized_phrase = _normalize_match_text(phrase)
    if not normalized_signal or not normalized_phrase:
        return False
    if " " not in normalized_phrase:
        return normalized_phrase in _signal_token_set(normalized_signal)
    return normalized_phrase in normalized_signal


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


_KIND_TOKEN_RE = re.compile(r"\{kind=(\w+)\}")
_IGNORED_KINDS = {"suspension", "g2", "ps", "event"}
_VALID_KIND_VALUES = {k.value for k in BlockKind}

# Prioridade ao agregar kinds das linhas num hint de bloco (mais forte vence).
# class/overview/unknown nunca viram hint (sao o fallback de texto).
_SOURCE_KIND_PRIORITY = [
    "assessment", "deliverable", "review", "holiday", "makeup",
    "suspended", "academic_event", "results", "workshop",
    "office_hours", "planning", "reserved",
]


def _aggregate_source_kind(rows: List[Dict[str, object]]) -> str:
    """Maior-prioridade kind nao-class entre as linhas do bloco; '' se nenhum."""
    present = {str(r.get("kind", "")) for r in (rows or [])}
    for kind in _SOURCE_KIND_PRIORITY:
        if kind in present:
            return kind
    return ""


def _row_atividade(row: Dict[str, str]) -> str:
    """Valor da coluna 'Atividade' da row do cronograma (qualquer header que a contenha)."""
    for key in row or {}:
        if "atividade" in str(key).lower():
            return str(row.get(key) or "")
    return ""


def _build_timeline_candidate_rows(timeline: List[Dict[str, str]]) -> List[Dict[str, object]]:
    content_keys, date_keys = _infer_timeline_keys(timeline)
    candidate_rows: List[Dict[str, object]] = []
    for index, row in enumerate(timeline or []):
        content = " ".join(row.get(key, "") for key in content_keys).strip()
        date_text = " / ".join(row.get(key, "") for key in date_keys if row.get(key, "")).strip()
        kind = "class"
        match = _KIND_TOKEN_RE.search(content)
        if match:
            raw = match.group(1).strip().lower() or "class"
            # token deve ser um BlockKind valido OU um token ignorado conhecido;
            # qualquer outra coisa cai em class (defensivo).
            kind = raw if (raw in _VALID_KIND_VALUES or raw in _IGNORED_KINDS) else "class"
            content = _collapse_ws(_KIND_TOKEN_RE.sub("", content))
        else:
            # Sem marcador {kind=}: a coluna Atividade do SARC é o sinal autoritativo.
            # Nota: ps/g2 so se distinguem pela COR (caminho SARC-HTML). Aqui, sem
            # cor, "prova de substituicao/g2" colapsa em assessment (direcao segura).
            atividade = norm_ascii_lower(_row_atividade(row))
            for needle, mapped in ATIVIDADE_KIND_MAP.items():
                if needle in atividade:
                    kind = mapped
                    break
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




def _empty_timeline_index() -> dict:
    return {"version": TIMELINE_INDEX_VERSION, "blocks": []}


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


def _timeline_period_label(
    start_text: str,
    end_text: str,
    count: Optional[int] = None,
    unit_singular: str = "dia",
    unit_plural: str = "dias",
) -> str:
    start = _collapse_ws(start_text)
    end = _collapse_ws(end_text)
    if not start:
        base = end
    elif not end or end == start:
        base = start
    else:
        base = f"{start} a {end}"
    if count is None or count <= 0 or not base:
        return base
    unit = unit_singular if count == 1 else unit_plural
    return f"{count} {unit} · {base}"


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


def _row_is_standalone_kind(row: Dict[str, object]) -> bool:
    """Linha com kind nao-aula (prova/trabalho/feriado/... via Atividade) e um
    bloco proprio: nao funde com vizinhos. '' e 'class' agrupam normalmente."""
    kind = str(row.get("kind") or "")
    return bool(kind) and kind != "class"


# Cap de span temporal (interino, degrau 2): blocos temáticos não fundem
# através de um intervalo maior que isto, mesmo com overlap de tokens —
# quebra os blocos over-merged (ex.: IA 29 dias). Conservador (21d): mantém
# blocos legítimos de até ~2 semanas. Substituído pelo agrupamento por slug
# igual no degrau 3.
MAX_THEMATIC_BLOCK_SPAN_DAYS = 21


def _rows_belong_to_same_thematic_block(
    previous_row: Dict[str, object],
    current_row: Dict[str, object],
    current_rows: Optional[List[Dict[str, object]]] = None,
) -> bool:
    if _row_is_standalone_kind(current_row) or _row_is_standalone_kind(previous_row):
        return False

    previous_text = str(previous_row.get("content", ""))
    current_text = str(current_row.get("content", ""))
    if not previous_text or not current_text:
        return False

    if _timeline_row_is_review_or_assessment(current_text):
        return False

    block_start_dt = (current_rows[0].get("date_dt") if current_rows else previous_row.get("date_dt"))
    current_dt = current_row.get("date_dt")
    if block_start_dt and current_dt:
        if (current_dt - block_start_dt).days > MAX_THEMATIC_BLOCK_SPAN_DAYS:
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


def timeline_block_is_administrative_only(block: Dict[str, object]) -> bool:
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
    if winner_score < T.BLOCK_UNIT_MIN_WINNER or abs(winner_score - runner_up_score) < T.BLOCK_UNIT_MIN_GAP:
        return "", 0.0

    confidence = margin_confidence(winner_score, runner_up_score, k=T.MARGIN_K)
    return winner.get("slug", ""), confidence


def _serialize_timeline_index(timeline_index: dict) -> dict:
    blocks = []
    for block in (timeline_index or {}).get("blocks", []) or []:
        if timeline_block_is_administrative_only(block):
            continue
        kind_value = classify_block(block).value
        unit_slug = block.get("unit_slug", "")
        unit_confidence = float(block.get("unit_confidence", 0.0) or 0.0)
        # Non-aula nao carrega unidade pedagogica (override manual preservado).
        if kind_value != BlockKind.CLASS.value and not block.get("block_manual_unit_slug"):
            unit_slug = ""
            unit_confidence = 0.0
        payload = {
            "id": block.get("id", ""),
            "period_start": block.get("period_start", ""),
            "period_end": block.get("period_end", ""),
            "period_label": block.get("period_label", ""),
            "kind": kind_value,
            "unit_slug": unit_slug,
            "unit_confidence": unit_confidence,
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
        manual_override = block.get("manual_kind_override")
        if manual_override:
            payload["manual_kind_override"] = manual_override
        topic_source = block.get("topic_source")
        if topic_source:
            payload["topic_source"] = topic_source
        manual_topic_label = block.get("manual_topic_label")
        if manual_topic_label:
            payload["manual_topic_label"] = manual_topic_label
        block_manual_unit_slug = block.get("block_manual_unit_slug")
        if block_manual_unit_slug:
            payload["block_manual_unit_slug"] = block_manual_unit_slug
        source_kind = block.get("source_kind")
        if source_kind:
            payload["source_kind"] = source_kind
        auto_unit_slug = block.get("auto_unit_slug")
        if auto_unit_slug:
            payload["auto_unit_slug"] = auto_unit_slug
        blocks.append(payload)
    _apply_timeline_post_transforms(blocks)
    return {"version": TIMELINE_INDEX_VERSION, "blocks": blocks}


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
            block_count = len(blocks)
            if edge_dates:
                start_label = edge_dates[0]
                end_label = edge_dates[-1] if len(edge_dates) > 1 else edge_dates[0]
                period_map[slug] = _timeline_period_label(
                    start_label,
                    end_label,
                    count=block_count,
                    unit_singular="bloco",
                    unit_plural="blocos",
                )
                continue
            period_map[slug] = _timeline_period_label(
                min(start_dates).strftime("%Y-%m-%d"),
                max(end_dates).strftime("%Y-%m-%d"),
                count=block_count,
                unit_singular="bloco",
                unit_plural="blocos",
            )
            continue
        def _strip_count_prefix(label: str) -> str:
            return label.split(" · ", 1)[1] if " · " in label else label
        labels = [_strip_count_prefix(str(block.get("period_label", "")).strip()) for block in blocks if str(block.get("period_label", "")).strip()]
        if labels:
            period_map[slug] = _timeline_period_label(
                labels[0],
                labels[-1],
                count=len(blocks),
                unit_singular="bloco",
                unit_plural="blocos",
            )
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
    if re.search(r"\bps\b", normalized):
        return "PS"
    if re.search(r"\bg2\b", normalized):
        return "G2"
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


def _assessment_block_label(block: Dict[str, object]) -> str:
    """Rótulo canônico (P1/P2/PS/G2/PF/EXAME) a partir do texto do bloco, ou ""."""
    # Só campos CRUS — NÃO incluir primary_topic_label: o serialize sobrescreve ele
    # com "Conteúdo: …" e isso corromperia o rótulo na re-serialização (idempotência).
    text = " ".join(
        str(block.get(k, "") or "")
        for k in ("topic_text", "period_label")
    )
    for sess in block.get("sessions", []) or []:
        if isinstance(sess, dict):
            text += " " + str(sess.get("label", "") or "")
    if not _normalize_match_text(text):
        return ""
    return _canonical_assessment_label(text, normalize_match_text=_normalize_match_text)


_FULL_SCOPE_LABELS = {"PS", "G2", "PF", "EXAME"}


def assessment_scope_by_date(blocks: List[Dict[str, object]]) -> Dict[str, List[str]]:
    """Escopo de unidades por prova, derivado das datas dos blocos.

    Prova regular (Pk): unidades das aulas (CLASS) na janela (data P(k-1), data Pk],
    EXCLUINDO unidades já cobertas por uma prova anterior (sem sobreposição —
    uma aula "atrasada" de U1 depois da P1 não polui o escopo da P2).
    PS/G2/PF/EXAME: semestre inteiro (todas as unidades vistas em aulas).
    Retorna {block_id: [unit_slug]} (ordem de aparição). Provas sem data: ignoradas.
    """
    class_units_dated = []
    all_units: List[str] = []
    for b in blocks:
        if str(b.get("kind") or "") != BlockKind.CLASS.value:
            continue
        slug = str(b.get("unit_slug") or "").strip()
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        if slug and slug not in all_units:
            all_units.append(slug)
        if slug and dt:
            class_units_dated.append((dt, slug))

    exams = []
    for b in blocks:
        if str(b.get("kind") or "") != BlockKind.ASSESSMENT.value:
            continue
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        if not dt:
            continue
        exams.append({"id": str(b.get("id") or ""), "dt": dt, "label": _assessment_block_label(b)})

    regular = sorted(
        [e for e in exams if e["label"] not in _FULL_SCOPE_LABELS],
        key=lambda e: e["dt"],
    )
    out: Dict[str, List[str]] = {}
    prev_dt = None
    seen: set = set()  # unidades ja cobertas por provas anteriores (sem sobreposicao)
    for e in regular:
        units = []
        for dt, slug in class_units_dated:
            if (prev_dt is None or dt > prev_dt) and dt <= e["dt"]:
                if slug not in units and slug not in seen:
                    units.append(slug)
        out[e["id"]] = units
        seen.update(units)
        prev_dt = e["dt"]

    for e in exams:
        if e["label"] in _FULL_SCOPE_LABELS:
            out[e["id"]] = list(all_units)
    return out


def link_review_scope(blocks: List[Dict[str, object]], exam_scope: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Cada bloco REVIEW herda o escopo da PRÓXIMA prova (ASSESSMENT) por data.

    Retorna {review_block_id: [unit_slug]} (vazio se não houver prova depois)."""
    dated = []
    for b in blocks:
        dt = _parse_timeline_date_value(str(b.get("period_start") or ""))
        dated.append((dt, b))
    out: Dict[str, List[str]] = {}
    for dt, b in dated:
        if str(b.get("kind") or "") != BlockKind.REVIEW.value or not dt:
            continue
        nxt = None
        for odt, ob in dated:
            if (str(ob.get("kind") or "") == BlockKind.ASSESSMENT.value
                    and odt and odt >= dt):
                if nxt is None or odt < nxt[0]:
                    nxt = (odt, ob)
        out[str(b.get("id") or "")] = list(exam_scope.get(str(nxt[1].get("id")), [])) if nxt else []
    return out


def _demote_non_preexam_reviews(blocks: List[Dict[str, object]]) -> None:
    """REVIEW que NÃO precede uma prova vira CLASS. In-place.

    Spec: "exercício de revisão é sempre a linha imediatamente anterior a uma
    prova". Um bloco "Revisão de [conteúdo]" no meio do semestre (ex.: "Revisão
    de lógica de predicados" longe de qualquer prova) é aula de conteúdo, não
    revisão pré-prova — vira CLASS e herda a unidade do vizinho. O elo segue a
    ordem CRONOLÓGICA (data; sem data preserva ordem da lista), pulando blocos de
    calendário (suspensão/feriado/evento/devolução) — igual ao link_review_scope.
    Override manual de kind é respeitado.
    """
    decisive = {BlockKind.CLASS.value, BlockKind.ASSESSMENT.value}
    n = len(blocks)
    # Ordem cronológica estável: data quando presente; sem data vai pro fim
    # mantendo a ordem original (datetime.max + índice como desempate).
    order = sorted(
        range(n),
        key=lambda i: (
            _parse_timeline_date_value(str(blocks[i].get("period_start") or "")) or datetime.max,
            i,
        ),
    )
    pos = {idx: p for p, idx in enumerate(order)}
    for idx in range(n):
        b = blocks[idx]
        if str(b.get("kind") or "") != BlockKind.REVIEW.value:
            continue
        if b.get("manual_kind_override"):
            continue
        p = pos[idx]
        preexam = False
        for q in range(p + 1, n):
            k = str(blocks[order[q]].get("kind") or "")
            if k in decisive:
                preexam = k == BlockKind.ASSESSMENT.value
                break
        if preexam:
            continue
        b["kind"] = BlockKind.CLASS.value
        if not b.get("unit_slug") and not b.get("block_manual_unit_slug"):
            prev_slug = ""
            for q in range(p - 1, -1, -1):
                slug = blocks[order[q]].get("unit_slug")
                if slug:
                    prev_slug = str(slug)
                    break
            next_slug = ""
            for q in range(p + 1, n):
                slug = blocks[order[q]].get("unit_slug")
                if slug:
                    next_slug = str(slug)
                    break
            inherited = prev_slug or next_slug
            if inherited:
                b["unit_slug"] = inherited
                b["unit_confidence"] = max(float(b.get("unit_confidence", 0.0) or 0.0), 0.51)
                b["auto_unit_slug"] = inherited


def apply_assessment_review_scope(blocks: List[Dict[str, object]]) -> None:
    """Aplica escopo de prova por data + revisão herda a próxima prova. In-place.

    Prova (ASSESSMENT): unidades por janela de data; PS/G2/PF = semestre inteiro.
    Revisão (REVIEW): herda o escopo da próxima prova. Grava `scope_unit_slugs` e,
    quando o label de tópico está vazio OU é o nosso próprio marcador, define um
    `primary_topic_label = "Conteúdo: …"` legível. Idempotente; label manual nunca
    é tocado. Provas/revisões sem data ficam sem escopo.
    Override manual: `block_manual_scope_slugs` não-vazio sobrepõe o escopo derivado
    por data (ASSESSMENT) ou herdado da próxima prova (REVIEW) — o manual sempre vence.
    """
    exam_scope = assessment_scope_by_date(blocks)
    review_scope = link_review_scope(blocks, exam_scope)
    for b in blocks:
        bid = b.get("id")
        scope = None
        manual = b.get("block_manual_scope_slugs")
        is_scopable = b.get("kind") in (
            BlockKind.ASSESSMENT.value,
            BlockKind.REVIEW.value,
        )
        if is_scopable and isinstance(manual, list) and manual:
            scope = [str(s) for s in manual]
        elif b.get("kind") == BlockKind.ASSESSMENT.value:
            scope = exam_scope.get(bid, [])
        elif b.get("kind") == BlockKind.REVIEW.value:
            scope = review_scope.get(bid, [])
        if scope is not None:
            b["scope_unit_slugs"] = list(scope)
            existing = str(b.get("primary_topic_label") or "")
            if scope and (not existing or existing.startswith("Conteúdo: ")):
                b["primary_topic_label"] = "Conteúdo: " + ", ".join(scope)


def _apply_timeline_post_transforms(blocks: List[Dict[str, object]]) -> None:
    """Transforms pós-classificação compartilhados por TODOS os caminhos de
    gravação do índice (GUI via build_file_map+persist; scripts/testes via
    _serialize_timeline_index). Fonte única para evitar divergência:
      1. revisão que não precede prova vira aula de conteúdo (herda unidade);
      2. escopo de prova por data + revisão herda a próxima prova.
    Idempotente.
    """
    _demote_non_preexam_reviews(blocks)
    apply_assessment_review_scope(blocks)


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
    if not syllabus:
        repo_root = course_meta.get("_repo_root")
        if repo_root:
            syllabus_file = Path(repo_root) / "course" / "SYLLABUS.md"
            if syllabus_file.exists():
                raw = syllabus_file.read_text(encoding="utf-8")
                # Remove YAML frontmatter (--- ... ---) antes de parsear
                if raw.startswith("---"):
                    end = raw.find("\n---", 3)
                    syllabus = raw[end + 4:].strip() if end != -1 else raw
                else:
                    syllabus = raw
    timeline = _parse_syllabus_timeline(syllabus) if syllabus else []
    candidate_rows = _build_timeline_candidate_rows(timeline)
    if candidate_rows:
        timeline_index = _build_timeline_index(
            candidate_rows, unit_index=unit_index, content_taxonomy=content_taxonomy
        )
    else:
        # Último fallback: usa o índice já salvo em disco para preservar atribuições anteriores
        repo_root = course_meta.get("_repo_root")
        cached_path = Path(repo_root) / "course" / ".timeline_index.json" if repo_root else None
        if cached_path and cached_path.exists():
            try:
                timeline_index = json.loads(cached_path.read_text(encoding="utf-8"))
                _backfill_timeline_index(timeline_index)
            except Exception:
                timeline_index = _empty_timeline_index()
        else:
            timeline_index = _empty_timeline_index()

    # Merge de overrides manuais (curation) por block_id. Sobrevive ao rebuild
    # from-syllabus porque mora num arquivo separado. Re-deriva kind/topic.
    _repo_root = course_meta.get("_repo_root")
    if _repo_root:
        _apply_curation_overrides(timeline_index, Path(_repo_root) / "course")

    # Transforms pós-classificação (demote revisão + escopo). Aplicado aqui (após
    # kinds/units finais via finalize_block + curation) porque o caminho real de
    # gravação (persist_enriched_timeline_index) não passa por
    # _serialize_timeline_index. Mesma função usada pelo _serialize → sem divergência.
    _apply_timeline_post_transforms(timeline_index.get("blocks", []) or [])

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
        if len(token) >= 4 and token not in UNIT_GENERIC_TOKENS
    }
    if topic_slug:
        topic_tokens.update(
            token
            for token in _normalize_match_text(topic_slug.replace("-", " ")).split()
            if len(token) >= 4 and token not in UNIT_GENERIC_TOKENS
        )
    for alias in aliases:
        topic_tokens.update(
            token
            for token in _normalize_match_text(alias).split()
            if len(token) >= 4 and token not in UNIT_GENERIC_TOKENS
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


# Stopwords PT-BR pra limpar fallback de topic_text. Conservador — só
# conectivos comuns que poluem o label, mantem termos tecnicos.
_TOPIC_FALLBACK_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das",
    "e", "ou", "em", "no", "na", "nos", "nas", "para", "por", "com",
    "sobre", "ao", "aos", "que", "se", "ate", "como",
}

_TOPIC_FALLBACK_MAX_LEN = 60


def _humanize_topic_text(text: str) -> str:
    """topic_text cru -> label apresentavel. Remove stopwords de borda,
    capitaliza, trunca em 60 chars. Determinista."""
    raw = _collapse_ws(text)
    if not raw:
        return ""
    tokens = raw.split()
    # remove stopwords só nas bordas (preserva ordem/sentido interno)
    while tokens and tokens[0].lower() in _TOPIC_FALLBACK_STOPWORDS:
        tokens.pop(0)
    while tokens and tokens[-1].lower() in _TOPIC_FALLBACK_STOPWORDS:
        tokens.pop()
    if not tokens:
        tokens = raw.split()
    label = " ".join(tokens)
    if len(label) > _TOPIC_FALLBACK_MAX_LEN:
        label = label[:_TOPIC_FALLBACK_MAX_LEN].rstrip() + "…"
    # capitaliza primeira letra; mantem resto (siglas tipo API, DevOps)
    return label[:1].upper() + label[1:]


def _resolve_block_topic_label(block: Dict[str, object]) -> tuple[str, str, str]:
    """Resolve label do topico em camadas. Retorna (label, slug, source).

    Ordem (primeira que casar vence):
      1. manual    — manual_topic_label em curation
      2. taxonomy  — primary_topic_label ja setado pelo matcher (inclui alias,
                     pois o scorer considera aliases internamente)
      3. topic_text_fallback — topic_text rico humanizado
      4. ""        — nada utilizavel
    """
    manual = block.get("manual_topic_label")
    if isinstance(manual, str) and manual.strip():
        return _collapse_ws(manual), slugify(manual), "manual"

    existing = block.get("primary_topic_label")
    if isinstance(existing, str) and existing.strip():
        return existing, str(block.get("primary_topic_slug", "") or ""), "taxonomy"

    topic_text = str(block.get("topic_text", "") or "")
    label = _humanize_topic_text(topic_text)
    if label:
        return label, slugify(topic_text), "topic_text_fallback"

    return "", "", ""


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

    confidence = margin_confidence(winner_score, runner_up_score, k=T.MARGIN_K_TOPIC)
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


def _vote_unit_from_topic_candidates(
    block: Dict[str, object],
    unit_index: list,
    *,
    top_k: int = 5,
    min_score: float = T.VOTE_MIN_SCORE,
    dominance_ratio: float = T.VOTE_DOMINANCE,
) -> tuple[str, float]:
    """Fallback de unit assignment: voto majoritario por topic_candidates.

    Quando _assign_timeline_block_to_unit retorna "" (score baixo, topic
    ambiguo), inspeciona topic_candidates do bloco. Se >=dominance_ratio dos
    top-K candidatos apontam pra mesma unit_slug, atribui essa unit com
    confidence reduzida.

    Resolve casos tipo ES2 bloco-06 ("microservicos spring circuit breaker"),
    onde todos topic_candidates apontam pra unidade-01-arquitetura mas o
    primary_topic e ambiguo.
    """
    candidates = block.get("topic_candidates") or []
    if not candidates or not unit_index:
        return "", 0.0
    valid_slugs = {
        _normalize_unit_slug(str(u.get("slug", "") or u.get("title", "") or ""))
        for u in unit_index
    }
    valid_slugs.discard("")

    votes: Dict[str, float] = {}
    counted = 0
    for cand in candidates[:top_k]:
        if not isinstance(cand, dict):
            continue
        score = float(cand.get("score") or 0.0)
        if score < min_score:
            continue
        slug = _normalize_unit_slug(str(cand.get("unit_slug") or ""))
        if not slug or slug not in valid_slugs:
            continue
        votes[slug] = votes.get(slug, 0.0) + score
        counted += 1
    if counted == 0 or not votes:
        return "", 0.0

    winner_slug, winner_weight = max(votes.items(), key=lambda kv: kv[1])
    total = sum(votes.values()) or 1.0
    if winner_weight / total < dominance_ratio:
        return "", 0.0
    confidence = min(0.55, max(0.30, winner_weight / total * 0.6))
    return winner_slug, confidence


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
            "period_label": _timeline_period_label(start_text, end_text, count=len(rows)),
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
        source_kind = _aggregate_source_kind(rows)
        if source_kind:
            runtime_block["source_kind"] = source_kind
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
        # Fallback em camadas: garante label quando matcher reprova mas
        # topic_text tem substancia. Marca topic_source pra UI badge.
        resolved_label, resolved_slug, topic_source = _resolve_block_topic_label(runtime_block)
        if resolved_label and not runtime_block["primary_topic_label"]:
            runtime_block["primary_topic_label"] = resolved_label
            # primary_topic_slug so vem de manual/taxonomy (vinculo real).
            # fallback humanizado e display-only: nunca popula slug.
            if topic_source != "topic_text_fallback" and resolved_slug \
                    and not runtime_block["primary_topic_slug"]:
                runtime_block["primary_topic_slug"] = resolved_slug
        runtime_block["topic_source"] = topic_source
        runtime_blocks.append(runtime_block)

    # Atribuicao de unidade ANTES da classificacao final de kind. Blocos com
    # source_kind nao-aula (provas/trabalhos/feriados via Atividade) ficam de fora;
    # o resto sao candidatos a aula. Assim, quando finalize_block classificar, o
    # has_unit ja reflete o posicional e o gate do classificador de sessao volta
    # a valer (aula de conteudo que cita "revisao" nao vira review).
    units_ordered = list((content_taxonomy or {}).get("units", []) or [])
    class_candidates = [b for b in runtime_blocks if not b.get("source_kind")]
    positional = assign_units_positional(class_candidates, units_ordered)
    if positional:
        for b, (slug, conf) in zip(class_candidates, positional):
            b["unit_slug"] = slug
            b["unit_confidence"] = conf
            if slug:
                b["auto_unit_slug"] = slug
    else:
        for b in class_candidates:
            us, uc = _assign_timeline_block_to_unit(b, unit_index)
            if not us:
                us, uc = _vote_unit_from_topic_candidates(b, unit_index)
            b["unit_slug"] = us
            b["unit_confidence"] = uc
            if us:
                b["auto_unit_slug"] = us

    for index, block in enumerate(runtime_blocks):
        if block.get("unit_slug") or not _timeline_block_is_soft_continuation(block):
            continue
        previous_slug = runtime_blocks[index - 1].get("unit_slug", "") if index > 0 else ""
        next_slug = runtime_blocks[index + 1].get("unit_slug", "") if index + 1 < len(runtime_blocks) else ""
        inherited_slug = previous_slug or next_slug
        if inherited_slug:
            block["unit_slug"] = inherited_slug
            block["unit_confidence"] = max(float(block.get("unit_confidence", 0.0) or 0.0), 0.51)

    for block in runtime_blocks:
        finalize_block(block)
    return {"version": TIMELINE_INDEX_VERSION, "blocks": runtime_blocks}
