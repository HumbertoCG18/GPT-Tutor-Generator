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
