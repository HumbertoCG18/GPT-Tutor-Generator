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
