from pathlib import Path

from src.builder.semantic_config import (
    infer_semantic_profile,
    merge_semantic_profile,
    resolve_semantic_profile,
    write_internal_semantic_profile,
    read_internal_semantic_profile,
)


def test_infer_semantic_profile_uses_course_corpus():
    profile = infer_semantic_profile(
        course_name="Compiladores",
        teaching_plan="## Análise Léxica\n## Análise Sintática\nFerramenta ANTLR\n",
        course_map_md="### Unidade 1\n- [ ] Análise Léxica\n- [ ] Parser com ANTLR\n",
        glossary_md="## ANTLR\n**Definição:** Ferramenta para gerar parsers.\n",
        strong_headings=["ANTLR", "Análise Léxica"],
    )

    assert profile["course_slug"] == "compiladores"
    assert "compiladores" in profile["tag_generic_slugs"]
    assert "antlr" in profile["known_tools"]


def test_internal_semantic_profile_roundtrip(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    profile = merge_semantic_profile(
        {"course_slug": "teste", "known_tools": ["antlr"]},
    )

    write_internal_semantic_profile(repo, profile)
    loaded = read_internal_semantic_profile(repo)

    assert loaded["course_slug"] == "teste"
    assert "antlr" in loaded["known_tools"]


def test_resolve_semantic_profile_applies_optional_override(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".semantic_profile.override.json").write_text(
        """
{
  "known_tools": ["antlr4"],
  "structural_stop_headings": ["visao geral"],
  "generic_slug_blacklist": ["compiladores-2026"]
}
""".strip(),
        encoding="utf-8",
    )

    profile = resolve_semantic_profile(
        root_dir=repo,
        course_name="Compiladores 2026",
        teaching_plan="## Análise Léxica",
        course_map_md="",
        glossary_md="",
        strong_headings=["Visão Geral", "ANTLR4"],
    )

    assert "antlr4" in profile["known_tools"]
    assert "visao geral" in profile["structural_stop_headings"]
    assert "compiladores-2026" in profile["generic_slug_blacklist"]
