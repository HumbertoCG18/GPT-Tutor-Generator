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


def _md_cell(value: str) -> str:
    """Escapa conteúdo para uma célula de tabela markdown: pipe -> \\|,
    quebras de linha viram espaço."""
    s = str(value or "")
    return s.replace("\n", " ").replace("\r", " ").replace("|", "\\|")


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


def _parse_iso(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def current_block_for_date(rows: list, ref_date: date) -> Optional[dict]:
    """Primeira linha cujo intervalo [inicio, fim] contém ref_date. Bordas
    inclusivas. None se nenhuma janela contém a data."""
    for r in rows:
        start = _parse_iso(r.get("inicio"))
        end = _parse_iso(r.get("fim")) or start
        if start and end and start <= ref_date <= end:
            return r
    return None


def temporal_context_md(course_meta: dict, timeline_blocks: list) -> str:
    """Renderiza o artefato CONTEXTO_TEMPORAL.md (cabeçalho + legenda + tabela).
    Cronograma vazio -> nota de indisponível."""
    course_name = (course_meta or {}).get("course_name", "Curso")
    rows = build_temporal_context_rows(timeline_blocks)
    lines = [
        f"# CONTEXTO TEMPORAL — {course_name}",
        "",
        "> Cronograma compacto. Você (tutor) calcula a semana atual e a prontidão",
        "> pré-prova A CADA sessão comparando com a data de hoje. Datas ISO YYYY-MM-DD.",
        "",
    ]
    if not rows:
        lines += ["_Cronograma indisponível._", ""]
        return "\n".join(lines)

    legend = build_unit_legend(rows)
    if legend:
        lines += ["## Unidades", ""]
        for u in legend:
            nome = f" — {u['nome']}" if u["nome"] else ""
            lines.append(f"- **{u['label']}** = `{u['slug']}`{nome}")
        lines.append("")

    lines += [
        "## Cronograma",
        "",
        "| bloco | inicio | fim | tipo | unidade | topico | escopo |",
        "|-------|--------|-----|------|---------|--------|--------|",
    ]
    for r in rows:
        unidade = _md_cell(r["unidade"] or "—")
        topico = _md_cell(r["topico"] or "—")
        escopo = _md_cell(", ".join(r["escopo"]) if r["escopo"] else "—")
        lines.append(
            f"| {_md_cell(r['id'])} | {_md_cell(r['inicio'])} | {_md_cell(r['fim'])} | {_md_cell(r['tipo'])} | "
            f"{unidade} | {topico} | {escopo} |"
        )
    lines.append("")
    return "\n".join(lines)


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
