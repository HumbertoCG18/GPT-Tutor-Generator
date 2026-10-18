"""Índice de referências mapeadas por âncora (unidade / unidade+tópico).

Junta references_curation.json (computed_ref_unit/topics, ref_concepts) com os
entries do manifest (title, source_path, file_type) para alimentar as linhas de
apoio do COURSE_MAP. Puro: sem I/O, sem rede, saída determinística.
"""
from __future__ import annotations

from src.builder.text.normalize import normalize_match_text
from src.builder.routing.file_map import strip_outline_prefix

_REF_CAP_PER_ANCHOR = 2


def _topic_key(label: str) -> str:
    """Chave canônica de tópico: mesma normalização que produz computed_ref_topics
    (topic_phrases via normalize_match_text(strip_outline_prefix(...)) em
    routing/file_map.py:88). Idempotente sobre valores já normalizados."""
    return normalize_match_text(strip_outline_prefix(label or ""))


def _ref_type(source_path: str, file_type: str) -> str:
    if file_type == "github-repo" or "github.com" in (source_path or ""):
        return "repo"
    return "doc"


def _ref_support_line(ref: dict) -> str:
    concepts = ", ".join(ref["concepts"][:3])
    tail = f" — {concepts}" if concepts else ""
    return f"📖 Apoio: {ref['title']} ({ref['type']}){tail} → content/BIBLIOGRAPHY.md"



def _ancoras(rec: dict) -> list:
    """[(unit_slug, topics)] de UMA referencia — N ancoras, nao uma.

    `coverage_units` (N:N) e a fonte; `computed_ref_unit` e o espelho single-winner
    do primeiro item, mantido por compatibilidade. Ate 2026-08-19 este modulo lia SO
    o espelho, entao uma referencia que cobria duas unidades aparecia sob uma: o
    campo N:N era escrito e nunca lido (`reference_summary.py:135` era a unica
    ocorrencia em `src/`). Fallback para o espelho quando a lista nao existir —
    curation antiga segue funcionando.
    """
    cobertura = rec.get("coverage_units")
    if isinstance(cobertura, list) and cobertura:
        saida = []
        for item in cobertura:
            if not isinstance(item, dict):
                continue
            slug = str(item.get("unit_slug") or "").strip()
            if slug:
                saida.append((slug, [t for t in (item.get("topics") or []) if t]))
        if saida:
            return saida
    slug = str(rec.get("computed_ref_unit") or "").strip()
    if not slug:
        return []
    return [(slug, [t for t in (rec.get("computed_ref_topics") or []) if t])]



def _cobertura_extra(entry: dict) -> list:
    """Unidades que o MATERIAL cobre mas nao habita (o eixo 1:1 aponta outra).

    `computed_unit_slug` responde *onde o arquivo mora* e ja aparece no FILE_MAP
    e na timeline; repetir isso aqui so incharia o COURSE_MAP ("mapa pedagogico
    curto"). Saem so as EXTRAS — a lista da P1 que cobre u01..u03 morando em u03.
    Sem isto a informacao N:N nao existia em lugar nenhum do material: ate
    2026-08-19 `coverage_units` era escrito em `resolver_apply.py:273` e lido por
    ninguem (medido: 213 entries com cobertura nos 5 cursos, 23 multi-unidade,
    todas as 23 com ao menos uma unidade que o vencedor 1:1 nao nomeia).
    """
    # Meta (plano de ensino/cronograma) cobre TODAS as unidades por regra — e
    # verdade no eixo de cobertura (`coverage_units` no manifest mantem, a busca
    # continua achando), mas como linha de COURSE_MAP e so repeticao: medido
    # 2026-08-19, `cronograma` sozinho gerava 16 das 49 linhas nos 5 cursos,
    # sempre o mesmo arquivo sob cada unidade.
    from src.builder.routing.coverage_rules import META_CATEGORIES
    if str(entry.get("category") or "").strip().lower() in META_CATEGORIES:
        return []
    cobertura = entry.get("coverage_units")
    if not isinstance(cobertura, list) or len(cobertura) < 2:
        return []
    dono = str(entry.get("manual_unit_slug") or entry.get("computed_unit_slug") or "").strip()
    return [
        slug
        for item in cobertura
        if isinstance(item, dict)
        and (slug := str(item.get("unit_slug") or "").strip())
        and slug != dono
    ]


def build_unit_topic_reference_index(manifest_entries: list, reference_curation: dict) -> dict:
    """Agrupa refs mapeadas por âncora. Só inclui refs com computed_ref_unit não-vazio
    e com entry correspondente no manifest. Listas ordenadas por entry_id (estável)."""
    by_id = {}
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        if eid:
            by_id[eid] = e

    cur_entries = (reference_curation or {}).get("entries", {}) or {}
    refs = []
    for eid, rec in cur_entries.items():
        entry = by_id.get(eid)
        if entry is None:
            continue
        source_path = str(entry.get("source_path") or "")
        base = {
            "entry_id": eid,
            "title": str(entry.get("title") or eid),
            "source_path": source_path,
            "type": _ref_type(source_path, str(entry.get("file_type") or "")),
            "concepts": [c for c in (rec.get("ref_concepts") or []) if c][:3],
        }
        for unit_slug, topics in _ancoras(rec):
            refs.append({**base, "topics": topics, "unit_slug": unit_slug})

    refs.sort(key=lambda r: r["entry_id"])

    by_unit: dict = {}
    by_topic: dict = {}
    for ref in refs:
        by_unit.setdefault(ref["unit_slug"], []).append(ref)
        for topic_label in ref["topics"]:
            key = (ref["unit_slug"], _topic_key(topic_label))
            by_topic.setdefault(key, []).append(ref)
    material_by_unit: dict = {}
    for eid, entry in by_id.items():
        extras = _cobertura_extra(entry)
        if not extras:
            continue
        item = {"entry_id": eid, "title": str(entry.get("title") or eid),
                "category": str(entry.get("category") or "")}
        for slug in extras:
            material_by_unit.setdefault(slug, []).append(item)
    for bucket in material_by_unit.values():
        bucket.sort(key=lambda m: m["entry_id"])

    return {"by_unit": by_unit, "by_topic": by_topic, "material_by_unit": material_by_unit}
