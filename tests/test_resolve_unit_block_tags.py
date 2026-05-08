from src.builder.extraction.content_taxonomy import resolve_unit_block_tags


def _make_minimal_entry(entry_id: str, title: str, category: str = "material-de-aula") -> dict:
    return {
        "id": entry_id,
        "title": title,
        "category": category,
        "file_type": "pdf",
        "source_path": f"/tmp/{entry_id}.pdf",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
    }


def _stub_unit_match(slug, confidence, ambiguous=False):
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def _stub_topic_match(slug="", confidence=0.0, ambiguous=True):
    class M:
        pass
    m = M()
    m.topic_slug = slug
    m.topic_label = slug
    m.unit_slug = ""
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def test_resolve_unit_block_tags_adds_unit_tag_when_high_confidence():
    entries = [_make_minimal_entry("e1", "Slides Unidade 2")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "unit:unidade-02" in tags


def test_resolve_unit_block_tags_skips_unit_tag_when_low_confidence():
    entries = [_make_minimal_entry("e1", "Slides")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.40, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert not any(t.startswith("unit:") for t in tags)


def test_resolve_unit_block_tags_skips_unit_tag_when_ambiguous():
    entries = [_make_minimal_entry("e1", "Slides")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=True
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert not any(t.startswith("unit:") for t in tags)


def test_resolve_unit_block_tags_adds_subunit_tag():
    entries = [_make_minimal_entry("e1", "Regra da Cadeia")]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(
            slug="regra-da-cadeia", confidence=0.75, ambiguous=False
        ),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "subunit:regra-da-cadeia" in tags


def test_resolve_unit_block_tags_adds_bloco_tag_via_manual_override():
    entries = [_make_minimal_entry("e1", "Lista")]
    entries[0]["manual_timeline_block_id"] = "bloco-03"

    fake_block = {"id": "bloco-03", "period_label": "10/04/2026"}

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: fake_block,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "bloco:bloco-03" in tags


def test_resolve_unit_block_tags_skips_special_categories():
    entries = [
        _make_minimal_entry("e1", "Cronograma", category="cronograma"),
        _make_minimal_entry("e2", "Bibliografia", category="bibliografia"),
        _make_minimal_entry("e3", "Referências", category="referencias"),
    ]

    call_count = {"n": 0}

    def counting_unit_fn(e, u, m, ti):
        call_count["n"] += 1
        return _stub_unit_match("unidade-01", 0.90, False)

    resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=counting_unit_fn,
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert call_count["n"] == 0, "Categorias especiais não devem chamar o unit matcher"


def test_resolve_unit_block_tags_preserves_existing_non_managed_auto_tags():
    entries = [_make_minimal_entry("e1", "Slides")]
    entries[0]["auto_tags"] = ["topico:calculo-diferencial", "tipo:material-base"]

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "topico:calculo-diferencial" in tags
    assert "tipo:material-base" in tags


def test_resolve_unit_block_tags_manual_unit_slug_takes_precedence():
    entries = [_make_minimal_entry("e1", "Slides")]
    entries[0]["manual_unit_slug"] = "unidade-99-manual"

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti: _stub_unit_match(
            "unidade-01", 0.90, False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "unit:unidade-99-manual" in tags
    assert "unit:unidade-01" not in tags
