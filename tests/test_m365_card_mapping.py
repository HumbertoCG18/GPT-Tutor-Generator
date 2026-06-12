"""Testes do mapeamento de card M365 pela API Moodle (spec 2026-06-11)."""
from src.builder.sources.moodle import section_file_index_strict

def _contents(*secs):
    """secs: (nome_secao, [filenames]) -> payload core_course_get_contents."""
    return [
        {"name": nome, "modules": [
            {"name": f"mod {f}", "contents": [
                {"type": "file", "filename": f, "fileurl": f"https://x/{f}"}]}
            for f in files]}
        for nome, files in secs
    ]

def test_strict_index_maps_unique_basenames():
    idx, amb = section_file_index_strict(_contents(
        ("Verificação de Programas", ["LogicaDeHoare.pdf", "hoare.zip"]),
        ("Provas por Indução", ["intro.thy"]),
    ))
    assert idx["logicadehoare.pdf"] == "Verificação de Programas"
    assert idx["intro.thy"] == "Provas por Indução"
    assert amb == set()

def test_strict_index_excludes_ambiguous_basenames():
    idx, amb = section_file_index_strict(_contents(
        ("Seção A", ["Respostas.pdf"]),
        ("Seção B", ["Respostas.pdf"]),
    ))
    assert "respostas.pdf" not in idx
    assert amb == {"respostas.pdf"}

def test_strict_index_same_section_twice_is_not_ambiguous():
    idx, amb = section_file_index_strict(_contents(
        ("Seção A", ["x.pdf", "x.pdf"]),
    ))
    assert idx["x.pdf"] == "Seção A"
    assert amb == set()

def test_strict_index_case_variants_across_sections_are_ambiguous():
    idx, amb = section_file_index_strict(_contents(
        ("Seção A", ["File.pdf"]),
        ("Seção B", ["file.pdf"]),
    ))
    assert "file.pdf" not in idx
    assert amb == {"file.pdf"}

def test_strict_index_empty_contents():
    idx, amb = section_file_index_strict(None)
    assert idx == {} and amb == set()
