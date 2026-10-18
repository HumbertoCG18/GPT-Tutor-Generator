"""Vocabulário integral do curso, anterior ao orçamento de apresentação."""
from __future__ import annotations

import re


def build_course_terms(
    subject_profile, *, root_dir=None, manifest_entries=None,
    parse_units_from_teaching_plan_fn, topic_text_fn, collect_glossary_evidence_fn,
    find_glossary_evidence_fn, seed_glossary_fields_fn, load_curation_fn,
    curation_key_fn, merge_synonyms_fn,
) -> list[dict]:
    plan = getattr(subject_profile, "teaching_plan", "") or ""
    units = parse_units_from_teaching_plan_fn(plan) if plan else []
    evidence_docs = collect_glossary_evidence_fn(
        root_dir, manifest_entries=manifest_entries, unit_titles=[title for title, _ in units],
    ) if root_dir else []
    curated = load_curation_fn(root_dir)
    entries = []
    for unit_title, topics in units:
        for topic in topics:
            term = topic_text_fn(topic)
            evidence = find_glossary_evidence_fn(term, unit_title, evidence_docs)
            definition, synonyms, not_confuse = seed_glossary_fields_fn(term, unit_title, evidence=evidence)
            merged = merge_synonyms_fn(synonyms, curated.get(curation_key_fn(term), []))
            entries.append({
                "term": " ".join(term.split()),
                "unit_hint": " ".join(unit_title.split()),
                "definition": " ".join(definition.split()),
                "synonyms": list(dict.fromkeys(
                    " ".join(item.split()) for item in re.split(r"[,;/|]", merged)
                    if item.strip() not in {"", "—", "–", "-", "--", "n/a", "N/A", "nenhum", "Nenhum"}
                )),
                "not_confuse": " ".join(not_confuse.split()),
            })
    return entries


def course_terms_text(terms: list[dict]) -> str:
    """Projeção integral para consumidores textuais legados, sem template nem teto."""
    return "\n".join(
        f"## {term['term']}\n"
        f"**Definição:** {term['definition']}\n"
        f"**Sinônimos aceitos:** {', '.join(term['synonyms']) or '—'}\n"
        f"**Não confundir com:** {term['not_confuse']}\n"
        f"**Aparece em:** {term['unit_hint']}\n"
        for term in terms
    )
