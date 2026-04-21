from __future__ import annotations

from functools import partial


def build_glossary_aliases(
    *,
    repo_artifacts_module,
    course_meta_clamp_navigation_artifact,
    collapse_ws,
    strip_frontmatter_block,
    parse_units_from_teaching_plan,
    topic_text,
):
    clamp_navigation_artifact = repo_artifacts_module.clamp_navigation_artifact
    glossary_tokens = repo_artifacts_module.glossary_tokens

    extract_markdown_headings = partial(
        repo_artifacts_module.extract_markdown_headings,
        collapse_ws=collapse_ws,
    )
    trim_glossary_prefix = partial(
        repo_artifacts_module.trim_glossary_prefix,
        collapse_ws=collapse_ws,
    )

    def shorten_glossary_sentence(sentence, max_chars=180):
        return repo_artifacts_module.shorten_glossary_sentence(
            sentence,
            collapse_ws=collapse_ws,
            max_chars=max_chars,
        )

    is_bad_glossary_evidence = partial(
        repo_artifacts_module.is_bad_glossary_evidence,
        collapse_ws=collapse_ws,
    )

    def collect_glossary_evidence(root_dir, manifest_entries=None):
        return repo_artifacts_module.collect_glossary_evidence(
            root_dir,
            manifest_entries=manifest_entries,
            collapse_ws=collapse_ws,
            strip_frontmatter_block=strip_frontmatter_block,
            extract_markdown_headings_fn=extract_markdown_headings,
        )

    def normalize_glossary_sentence(term, unit_title, sentence):
        return repo_artifacts_module.normalize_glossary_sentence(
            term,
            unit_title,
            sentence,
            collapse_ws=collapse_ws,
            shorten_glossary_sentence_fn=shorten_glossary_sentence,
        )

    best_glossary_sentence = partial(
        repo_artifacts_module.best_glossary_sentence,
        collapse_ws=collapse_ws,
        glossary_tokens_fn=glossary_tokens,
        trim_glossary_prefix_fn=trim_glossary_prefix,
        is_bad_glossary_evidence_fn=is_bad_glossary_evidence,
        normalize_glossary_sentence_fn=lambda term, unit_title, sentence: normalize_glossary_sentence(term, unit_title, sentence),
        shorten_glossary_sentence_fn=shorten_glossary_sentence,
    )
    find_glossary_evidence = partial(
        repo_artifacts_module.find_glossary_evidence,
        glossary_tokens_fn=glossary_tokens,
        best_glossary_sentence_fn=lambda term, unit_title, doc: best_glossary_sentence(term, unit_title, doc),
    )

    def refine_glossary_definition_from_evidence(term, unit_hint, evidence):
        return repo_artifacts_module.refine_glossary_definition_from_evidence(
            term,
            unit_hint,
            evidence,
            collapse_ws=collapse_ws,
            glossary_tokens_fn=glossary_tokens,
            normalize_glossary_sentence_fn=lambda _term, unit_title, sentence: normalize_glossary_sentence(_term, unit_title, sentence),
            shorten_glossary_sentence_fn=shorten_glossary_sentence,
        )

    seed_glossary_fields = partial(
        repo_artifacts_module.seed_glossary_fields,
        collapse_ws=collapse_ws,
        refine_glossary_definition_from_evidence_fn=lambda term, unit_hint, evidence: refine_glossary_definition_from_evidence(term, unit_hint, evidence),
    )

    def glossary_md(course_meta, subject_profile=None, *, root_dir=None, manifest_entries=None):
        return repo_artifacts_module.glossary_md(
            course_meta,
            subject_profile,
            root_dir=root_dir,
            manifest_entries=manifest_entries,
            parse_units_from_teaching_plan_fn=parse_units_from_teaching_plan,
            topic_text_fn=topic_text,
            collect_glossary_evidence_fn=collect_glossary_evidence,
            find_glossary_evidence_fn=find_glossary_evidence,
            seed_glossary_fields_fn=lambda term, unit_title, evidence="": seed_glossary_fields(
                term,
                unit_title,
                evidence=evidence,
            ),
            clamp_navigation_artifact_fn=course_meta_clamp_navigation_artifact,
        )

    return {
        "glossary_md": glossary_md,
        "_clamp_navigation_artifact": clamp_navigation_artifact,
        "_glossary_tokens": glossary_tokens,
        "_extract_markdown_headings": extract_markdown_headings,
        "_trim_glossary_prefix": trim_glossary_prefix,
        "_shorten_glossary_sentence": shorten_glossary_sentence,
        "_is_bad_glossary_evidence": is_bad_glossary_evidence,
        "_collect_glossary_evidence": collect_glossary_evidence,
        "_find_glossary_evidence": find_glossary_evidence,
        "_best_glossary_sentence": best_glossary_sentence,
        "_normalize_glossary_sentence": normalize_glossary_sentence,
        "_seed_glossary_fields": seed_glossary_fields,
        "_refine_glossary_definition_from_evidence": refine_glossary_definition_from_evidence,
    }

