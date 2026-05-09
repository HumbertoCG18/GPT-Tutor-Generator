from src.models.tag_profile import (
    SubjectTagProfile,
    LearnedCorrection,
    load_tag_profile,
    save_tag_profile,
)


def test_tag_profile_round_trip(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()

    profile = SubjectTagProfile(subject_slug="metodos-formais", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-01",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )
    save_tag_profile(course_dir, profile)
    loaded = load_tag_profile(course_dir)

    assert loaded is not None
    assert loaded.subject_slug == "metodos-formais"
    assert len(loaded.learned_corrections) == 1
    assert loaded.learned_corrections[0].entry_id == "lista-1"
    assert "hoare" in loaded.learned_corrections[0].learned_terms


def test_load_tag_profile_returns_none_when_missing(tmp_path):
    result = load_tag_profile(tmp_path / "course")
    assert result is None


from src.models.tag_profile import extract_entry_learned_terms, record_correction


def test_extract_learned_terms_from_title_and_auto_tags():
    entry = {
        "id": "lista-1",
        "title": "Lista de Exercícios sobre Lógica de Hoare",
        "auto_tags": ["topico:logica-de-hoare", "tipo:lista"],
        "raw_target": "raw/pdfs/listas/exercicios-logica-hoare.pdf",
    }
    terms = extract_entry_learned_terms(entry)

    assert "logica-de-hoare" in terms
    assert len(terms) <= 12


def test_record_correction_stores_entry_and_removes_previous():
    from src.models.tag_profile import SubjectTagProfile
    profile = SubjectTagProfile(subject_slug="metodos-formais", generated_at="2026-05-09T00:00:00")
    entry = {
        "id": "lista-1",
        "title": "Lista Lógica de Hoare",
        "auto_tags": ["topico:logica-de-hoare"],
        "raw_target": "raw/listas/lista.pdf",
    }

    record_correction(profile, entry, corrected_unit_slug="unidade-02", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 1
    assert profile.learned_corrections[0].corrected_unit_slug == "unidade-02"

    # Overwrite with new correction for same entry
    record_correction(profile, entry, corrected_unit_slug="unidade-01", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 1
    assert profile.learned_corrections[0].corrected_unit_slug == "unidade-01"


def test_record_correction_skipped_when_no_unit_or_subunit():
    from src.models.tag_profile import SubjectTagProfile
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    entry = {"id": "x", "title": "Algo", "auto_tags": []}
    record_correction(profile, entry, corrected_unit_slug="", corrected_subunit_slug="")
    assert len(profile.learned_corrections) == 0


from src.models.tag_profile import build_learned_unit_boosts, SubjectTagProfile, LearnedCorrection


def test_learned_unit_boosts_returns_boost_when_terms_overlap():
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )

    entry = {
        "id": "lista-2",
        "title": "Exercícios Verificação Lógica de Hoare",
        "auto_tags": [],
        "raw_target": "raw/lista-2.pdf",
    }
    boosts = build_learned_unit_boosts(profile, entry)

    assert "unidade-02" in boosts
    assert boosts["unidade-02"] > 0.0


def test_learned_unit_boosts_returns_empty_when_no_overlap():
    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="lista-1",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["hoare", "logica", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )

    entry = {
        "id": "lista-2",
        "title": "Ponteiros e Alocação de Memória",
        "auto_tags": [],
        "raw_target": "raw/lista-2.pdf",
    }
    boosts = build_learned_unit_boosts(profile, entry)

    assert boosts.get("unidade-02", 0.0) == 0.0


def test_learned_unit_boosts_returns_empty_for_none_profile():
    entry = {"id": "x", "title": "Algo", "auto_tags": []}
    boosts = build_learned_unit_boosts(None, entry)
    assert boosts == {}


from src.models.tag_profile import format_unit_explanation_text, format_subunit_explanation_text


def test_format_unit_explanation_high_confidence():
    reasons = ["winner_score=4.20", "topic_score=0.85", "tag_boost=2.00"]
    text = format_unit_explanation_text(reasons, confidence=0.90, unit_slug="unidade-02")

    assert "unidade-02" in text
    assert "alta" in text
    assert "4.20" in text


def test_format_unit_explanation_shows_ambiguous():
    reasons = ["winner_score=0.50", "ambiguous"]
    text = format_unit_explanation_text(reasons, confidence=0.30)

    assert "ambíguo" in text or "ambiguo" in text or "ambiguous" in text.lower() or "similar" in text
    assert "muito baixa" in text


def test_format_subunit_explanation_includes_unit():
    reasons = ["winner_score=2.10"]
    text = format_subunit_explanation_text(
        reasons, confidence=0.70, unit_slug="unidade-02", subunit_slug="logica-de-hoare"
    )

    assert "logica-de-hoare" in text
    assert "unidade-02" in text
    assert "média" in text or "media" in text


def test_format_unit_explanation_manual_assignment():
    reasons = ["manual"]
    text = format_unit_explanation_text(reasons, confidence=1.0, unit_slug="unidade-01")

    assert "manual" in text


from src.builder.engine import (
    _build_file_map_unit_index,
    _auto_map_entry_unit,
)


def test_auto_map_entry_unit_applies_learned_unit_boosts():
    units = [
        {"title": "Unidade 01 — Lógica de Hoare", "topics": ["1.1 Pré e pós condições"], "extra_signals": []},
        {"title": "Unidade 02 — Redes Neurais", "topics": ["2.1 Backpropagation"], "extra_signals": []},
    ]
    entry = {
        "id": "doc-xyz",
        "title": "Documento genérico",
        "category": "material-de-aula",
        "auto_tags": [],
        "manual_tags": [],
        "tags": "",
        "raw_target": "",
        "notes": "",
        "professor_signal": "",
    }
    markdown_text = ""

    result_with_boost = _auto_map_entry_unit(
        entry, units, markdown_text, learned_unit_boosts={"unidade-02-redes-neurais": 6.0}
    )

    assert result_with_boost.slug == "unidade-02-redes-neurais"


from src.builder.extraction.content_taxonomy import resolve_unit_block_tags
from src.builder.routing.file_map import UnitMatchResult


def _make_resolve_kwargs(unit_slug="unidade-01", unit_confidence=0.80, unit_ambiguous=False):
    """Minimal stubs for resolve_unit_block_tags injected callables."""

    class FakeTopicMatch:
        topic_slug = ""
        topic_label = ""
        unit_slug = ""
        confidence = 0.0
        ambiguous = True
        reasons = ["sem-taxonomia"]

    return dict(
        build_file_map_unit_index_from_course_fn=lambda meta, profile: [],
        build_file_map_timeline_context_from_course_fn=lambda meta, profile: {
            "blocks_by_unit": {}, "unassigned_blocks": [], "timeline_index": {"blocks": []}
        },
        iter_content_taxonomy_topics_fn=lambda taxonomy: [],
        auto_map_entry_subtopic_fn=lambda entry, taxonomy, md: FakeTopicMatch(),
        auto_map_entry_unit_fn=lambda entry, units, md, topics, learned_unit_boosts=None: UnitMatchResult(
            slug=unit_slug, confidence=unit_confidence, ambiguous=unit_ambiguous, reasons=["winner_score=3.50"]
        ),
        select_probable_period_for_entry_fn=lambda **kw: ("", 0.0, True, ""),
        resolve_entry_manual_timeline_block_fn=lambda entry, ctx: None,
        entry_markdown_text_for_file_map_fn=lambda root, entry: "",
    )


def test_resolve_unit_block_tags_stores_match_reasons_in_entry():
    entries = [{"id": "item-1", "category": "listas", "auto_tags": [], "manual_tags": []}]
    course_meta = {"_repo_root": None}

    result = resolve_unit_block_tags(entries, course_meta, **_make_resolve_kwargs())

    item = result[0]
    assert "unit_match_reasons" in item
    assert "unit_match_confidence" in item
    assert item["unit_match_confidence"] == 0.80
    assert "winner_score=3.50" in item["unit_match_reasons"]


def test_resolve_unit_block_tags_loads_tag_profile_and_passes_learned_boosts(tmp_path):
    course_dir = tmp_path / "course"
    course_dir.mkdir()

    profile = SubjectTagProfile(subject_slug="test", generated_at="2026-05-09T00:00:00")
    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id="old-entry",
            corrected_unit_slug="unidade-02",
            corrected_subunit_slug="",
            learned_terms=["logica", "hoare", "verificacao"],
            created_at="2026-05-09T00:00:00",
        )
    )
    save_tag_profile(course_dir, profile)

    received_boosts = {}

    def capturing_unit_fn(entry, units, md, topics, learned_unit_boosts=None):
        received_boosts.update(learned_unit_boosts or {})
        return UnitMatchResult(slug="unidade-01", confidence=0.75, ambiguous=False, reasons=["winner_score=2.00"])

    kwargs = _make_resolve_kwargs()
    kwargs["auto_map_entry_unit_fn"] = capturing_unit_fn

    entries = [{
        "id": "lista-nova",
        "title": "Lista de Lógica de Hoare verificacao",
        "category": "listas",
        "auto_tags": [],
        "manual_tags": [],
    }]
    course_meta = {"_repo_root": tmp_path}

    resolve_unit_block_tags(entries, course_meta, **kwargs)

    assert "unidade-02" in received_boosts
    assert received_boosts["unidade-02"] > 0.0
