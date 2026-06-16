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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(
            slug="regra-da-cadeia", confidence=0.75, ambiguous=False
        ),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "subunit:regra-da-cadeia" in tags


def test_resolve_unit_block_tags_enriches_subunit_input_with_code_curation(tmp_path):
    """GERAL: entry de código sem markdown recebe o texto do code_curation.json
    no input do scorer de SUBUNIDADE (não no de bloco)."""
    import json

    entry = _make_minimal_entry("hoare", "hoare", category="codigo-professor")
    entry["file_type"] = "zip"

    curation = {
        "version": 1,
        "entries": {
            "hoare": {
                "content_hash": "x",
                "summary": {
                    "inferred_title": "Verificação com Tripla de Hoare",
                    "language": "dafny",
                    "concepts": ["Tripla de Hoare"],
                    "summary": "Exemplo em Dafny.",
                },
            }
        },
    }
    (tmp_path / "code_curation.json").write_text(
        json.dumps(curation, ensure_ascii=False), encoding="utf-8"
    )

    seen = {}

    def _capture_subtopic(e, t, m, winning_unit_slug=""):
        seen["subunit_md"] = m
        return _stub_topic_match()

    def _capture_unit(e, u, m, ti, learned_unit_boosts=None):
        seen["unit_md"] = m
        return _stub_unit_match("", 0.0, True)

    resolve_unit_block_tags(
        [entry],
        course_meta={"_repo_root": str(tmp_path)},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=_capture_subtopic,
        auto_map_entry_unit_fn=_capture_unit,
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    # subunit recebe o texto de curadoria; unidade/bloco continuam com markdown vazio
    assert "Tripla de Hoare" in seen["subunit_md"]
    assert "dafny" in seen["subunit_md"]
    assert seen["unit_md"] == ""


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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match("", 0.0, True),
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

    def counting_unit_fn(e, u, m, ti, learned_unit_boosts=None):
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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "topico:calculo-diferencial" in tags
    assert "tipo:material-base" in tags


def test_reconcile_manual_block_overrides_unit():
    """Bloco manual com unit_slug é autoritativo: a unidade do bloco vence o
    que o matcher auto teria escolhido, e sem marcar conflito."""
    entries = [_make_minimal_entry("e1", "Lista")]
    entries[0]["manual_timeline_block_id"] = "bloco-07"

    fake_block = {"id": "bloco-07", "period_label": "10/04/2026", "unit_slug": "unidade-2"}

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": [fake_block]},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        # Sem o override, este entry cairia em unidade-1.
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-1", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: fake_block,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    out_entry = result[0]
    assert out_entry["computed_unit_slug"] == "unidade-2"
    assert out_entry.get("unit_block_conflict", {}) == {}
    assert "unit:unidade-2" in out_entry["auto_tags"]


def test_reconcile_conflict_unit_stronger_sets_flag():
    """Auto: unidade forte (unidade-1, >=0.65) vs bloco auto fraco apontando
    unidade-2 com block_confidence < unit_confidence -> mantém a unidade forte
    e marca o conflito."""
    entries = [_make_minimal_entry("e1", "Slides")]

    # Bloco auto fraco, pertencente a unidade-2; selecionado pelo scorer (via o
    # *_fn injetado) com confiança baixa.
    weak_block = {
        "id": "bloco-04",
        "period_label": "P4",
        "unit_slug": "unidade-2",
        "administrative_only": False,
    }

    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": [weak_block]},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-1", confidence=0.80, ambiguous=False
        ),
        # Scorer real (injetado) seleciona o bloco fraco com confiança < unidade.
        select_probable_period_for_entry_fn=lambda **kw: ("P4", 0.30, False, ["best=0.30"]),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    out_entry = result[0]
    assert out_entry["computed_unit_slug"] == "unidade-1"
    assert out_entry["unit_block_conflict"] == {
        "unit": "unidade-1",
        "block_unit": "unidade-2",
        "block_id": "bloco-04",
    }
    assert "unit:unidade-1" in out_entry["auto_tags"]


def test_resolve_unit_block_tags_loads_taxonomy_from_repo_when_absent(tmp_path):
    """Dívida #5: sem _content_taxonomy no course_meta (ex.: retag), a taxonomia
    é carregada de course/.content_taxonomy.json do _repo_root — senão o scorer
    de subunidade rodaria com taxonomia vazia e LIMPARIA os slugs persistidos."""
    import json

    taxonomy = {
        "version": 1,
        "units": [{"slug": "u1", "topics": [{"slug": "t1", "label": "Tópico 1"}]}],
    }
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    (course_dir / ".content_taxonomy.json").write_text(
        json.dumps(taxonomy, ensure_ascii=False), encoding="utf-8"
    )

    seen = {}

    def _capture_iter(t):
        seen["taxonomy"] = t
        return []

    resolve_unit_block_tags(
        [_make_minimal_entry("e1", "Slides")],
        course_meta={"_repo_root": str(tmp_path)},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=_capture_iter,
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert seen["taxonomy"] == taxonomy


def test_resolve_unit_block_tags_prefers_in_memory_taxonomy_over_disk(tmp_path):
    """In-memory _content_taxonomy (pipeline completo) tem precedência sobre o
    arquivo em disco — o fallback é só para quem não passa a taxonomia."""
    import json

    disk = {"version": 1, "units": [{"slug": "from-disk"}]}
    mem = {"version": 1, "units": [{"slug": "from-memory"}]}
    course_dir = tmp_path / "course"
    course_dir.mkdir()
    (course_dir / ".content_taxonomy.json").write_text(
        json.dumps(disk, ensure_ascii=False), encoding="utf-8"
    )

    seen = {}

    def _capture_iter(t):
        seen["taxonomy"] = t
        return []

    resolve_unit_block_tags(
        [_make_minimal_entry("e1", "Slides")],
        course_meta={"_repo_root": str(tmp_path), "_content_taxonomy": mem},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=_capture_iter,
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match("", 0.0, True),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert seen["taxonomy"] == mem


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
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-01", 0.90, False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    tags = result[0]["auto_tags"]
    assert "unit:unidade-99-manual" in tags
    assert "unit:unidade-01" not in tags


def test_subtopic_matcher_receives_resolved_unit_as_winning_unit_slug():
    captured = {}

    def _capture_subtopic(e, t, m, winning_unit_slug=""):
        captured["winning_unit_slug"] = winning_unit_slug
        return _stub_topic_match()

    resolve_unit_block_tags(
        [_make_minimal_entry("e1", "Slides")],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=_capture_subtopic,
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-02", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert captured["winning_unit_slug"] == "unidade-02"


def test_manual_unit_feeds_winning_unit_slug():
    captured = {}

    def _capture_subtopic(e, t, m, winning_unit_slug=""):
        captured["winning_unit_slug"] = winning_unit_slug
        return _stub_topic_match()

    resolve_unit_block_tags(
        [{**_make_minimal_entry("e1", "Slides"), "manual_unit_slug": "unidade-manual"}],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=_capture_subtopic,
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-auto", confidence=0.80, ambiguous=False
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, []),
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

    assert captured["winning_unit_slug"] == "unidade-manual"
