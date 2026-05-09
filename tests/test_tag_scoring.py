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
