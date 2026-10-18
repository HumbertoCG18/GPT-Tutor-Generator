import json

from src.builder.engine import RepoBuilder, modes_md, output_templates_md
from src.models.core import SubjectProfile


def test_code_review_defaults_to_generic_vocabulary():
    text = modes_md({"course_name": "Estruturas de Dados"})

    assert "## code_review — Revisão de código" in text
    assert "código do professor" in text
    assert "não consigo provar este lema" not in text
    assert "tática escolhida" not in text


def test_code_review_specializes_for_formal_methods():
    profile = SubjectProfile(
        name="Métodos Formais",
        slug="metodos-formais",
        teaching_plan="Provadores de teoremas com Isabelle",
    )

    modes_text = modes_md({"course_name": "Métodos Formais"}, profile)
    template_text = output_templates_md({"course_name": "Métodos Formais"}, profile)

    assert "não consigo provar este lema" in modes_text
    assert "tática escolhida" in modes_text
    assert "material do professor" in modes_text
    assert '``` [linguagem ou "isabelle"]' in template_text
    assert "exercício/trabalho/lema" in template_text


def test_regenerate_pedagogical_files_rewrites_system_files_with_course_specific_profile(tmp_path):
    repo = tmp_path / "repo"
    for rel in [
        "system",
        "course",
        "content",
        "build",
        "student",
    ]:
        (repo / rel).mkdir(parents=True, exist_ok=True)

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder.course_meta = {
        "course_name": "Métodos Formais",
        "course_slug": "metodos-formais",
        "professor": "Prof",
        "institution": "PUCRS",
        "semester": "2026/1",
    }
    builder.student_profile = None
    builder.subject_profile = SubjectProfile(
        name="Métodos Formais",
        slug="metodos-formais",
        teaching_plan="Provadores de teoremas com Isabelle",
    )
    builder.logs = []
    builder.progress_callback = None
    builder.entries = []
    builder.options = {}

    manifest = {"entries": [], "logs": []}
    builder._regenerate_pedagogical_files(manifest)

    modes_text = (repo / "system" / "MODES.md").read_text(encoding="utf-8")
    templates_text = (repo / "system" / "OUTPUT_TEMPLATES.md").read_text(encoding="utf-8")
    policy_text = (repo / "system" / "TUTOR_POLICY.md").read_text(encoding="utf-8")

    assert "não consigo provar este lema" in modes_text
    assert "tática escolhida" in modes_text
    assert "material do professor" in templates_text
    assert "código ou prova formal do aluno" in policy_text
    updated_manifest = json.loads((repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
    assert updated_manifest["version"] == 1
