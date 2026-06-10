"""Gera setup/CONTEXTO_TEMPORAL.md: cronograma compacto que o tutor LLM usa
para calcular, a cada sessão, a semana atual, a próxima avaliação e a
prontidão pré-prova. Datas ISO; rótulos de unidade curtos (U1) com legenda.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.builder.extraction.content_taxonomy import _exam_code_from_block
from src.builder.timeline.unit_labels import (
    unit_name_from_slug,
    unit_number,
    unit_short_label,
)

# kind do bloco -> rótulo curto pra coluna "tipo" (assessment é tratado à parte).
_KIND_TIPO = {
    "class": "aula",
    "review": "revisão",
    "holiday": "feriado",
    "suspended": "suspensão",
    "makeup": "reposição",
    "academic_event": "evento acadêmico",
    "office_hours": "atendimento",
    "workshop": "oficina",
    "deliverable": "entrega",
    "planning": "planejamento",
    "reserved": "reserva",
    "results": "resultados",
    "overview": "introdução",
    "unknown": "—",
}


def _tipo_label(block: dict) -> str:
    kind = str(block.get("kind") or "")
    if kind == "assessment":
        code = _exam_code_from_block(block)
        if code == "EXAME":
            return "exame"
        if code == "PF":
            return "prova final"
        return f"prova {code}" if code else "prova"
    return _KIND_TIPO.get(kind, kind or "—")


def build_temporal_context_rows(timeline_blocks: list) -> list:
    """Mapeia blocos do cronograma em linhas compactas. Blocos sem data ISO
    de início são omitidos (não dá pra localizá-los no tempo)."""
    rows = []
    for b in timeline_blocks or []:
        start = str(b.get("period_start") or "").strip()
        if not start:
            continue
        end = str(b.get("period_end") or "").strip() or start
        unit_slug = str(b.get("unit_slug") or "").strip()
        topics = [str(t).strip() for t in (b.get("topics") or []) if str(t).strip()]
        if topics:
            topico = "; ".join(topics)
        else:
            topico = str(b.get("primary_topic_label") or "").strip()
        scope_slugs = [str(s).strip() for s in (b.get("scope_unit_slugs") or []) if str(s).strip()]
        rows.append({
            "id": str(b.get("id") or ""),
            "inicio": start,
            "fim": end,
            "tipo": _tipo_label(b),
            "unidade": unit_short_label(unit_slug),
            "unidade_slug": unit_slug,
            "topico": topico,
            "escopo": [unit_short_label(s) for s in scope_slugs],
            "escopo_slugs": scope_slugs,
        })
    return rows


def build_unit_legend(rows: list) -> list:
    """Legenda U1/U2 -> slug + nome, só das unidades que aparecem nas linhas
    (em 'unidade_slug' ou no escopo). Ordenada por número da unidade."""
    seen = set()
    slugs = []
    for r in rows:
        candidates = []
        if r.get("unidade_slug"):
            candidates.append(r["unidade_slug"])
        candidates.extend(r.get("escopo_slugs") or [])
        for s in candidates:
            if s and s not in seen:
                seen.add(s)
                slugs.append(s)
    def _sort_key(s):
        n = unit_number(s)
        return (n if n is not None else 9999, s)
    slugs.sort(key=_sort_key)
    return [
        {"label": unit_short_label(s), "slug": s, "nome": unit_name_from_slug(s)}
        for s in slugs
    ]
