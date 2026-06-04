"""Índice de referências mapeadas por âncora (unidade / unidade+tópico).

Junta references_curation.json (computed_ref_unit/topics, ref_concepts) com os
entries do manifest (title, source_path, file_type) para alimentar as linhas de
apoio do COURSE_MAP. Puro: sem I/O, sem rede, saída determinística.
"""
from __future__ import annotations

_REF_CAP_PER_ANCHOR = 2


def _norm_topic(s: str) -> str:
    """Normalizador trivial de label de tópico, idêntico nos dois lados do match."""
    return " ".join((s or "").lower().split())


def _ref_type(source_path: str, file_type: str) -> str:
    if file_type == "github-repo" or "github.com" in (source_path or ""):
        return "repo"
    return "doc"


def _ref_support_line(ref: dict) -> str:
    concepts = ", ".join(ref["concepts"][:3])
    tail = f" — {concepts}" if concepts else ""
    return f"📖 Apoio: {ref['title']} ({ref['type']}){tail} → content/BIBLIOGRAPHY.md"


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
        unit_slug = str(rec.get("computed_ref_unit") or "").strip()
        if not unit_slug:
            continue
        source_path = str(entry.get("source_path") or "")
        topics = [t for t in (rec.get("computed_ref_topics") or []) if t]
        refs.append({
            "entry_id": eid,
            "title": str(entry.get("title") or eid),
            "source_path": source_path,
            "type": _ref_type(source_path, str(entry.get("file_type") or "")),
            "concepts": [c for c in (rec.get("ref_concepts") or []) if c][:3],
            "topics": topics,
            "unit_slug": unit_slug,
        })

    refs.sort(key=lambda r: r["entry_id"])

    by_unit: dict = {}
    by_topic: dict = {}
    for ref in refs:
        by_unit.setdefault(ref["unit_slug"], []).append(ref)
        for topic_label in ref["topics"]:
            key = (ref["unit_slug"], _norm_topic(topic_label))
            by_topic.setdefault(key, []).append(ref)
    return {"by_unit": by_unit, "by_topic": by_topic}
