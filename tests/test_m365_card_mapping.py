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


from src.builder.sources.moodle import find_subject_for_course

class _FakeProfile:
    def __init__(self, name, slug="", moodle_course_id=""):
        self.name = name; self.slug = slug; self.moodle_course_id = moodle_course_id

class _FakeStore:
    def __init__(self, *profiles):
        self._d = {p.name: p for p in profiles}
    def names(self): return sorted(self._d)
    def get(self, name): return self._d.get(name)

_COURSE = {"id": 92717, "fullname":
           "4646M-04 - Métodos Formais para Computação - Turma 031 - 2026/1 - Prof. Julio Machado"}

def test_find_subject_by_moodle_course_id_wins():
    a = _FakeProfile("Metodos-Formais", slug="metodos_formais", moodle_course_id="92717")
    b = _FakeProfile("Métodos Formais para Computação", slug="metodos-formais-para-computacao")
    assert find_subject_for_course(_FakeStore(a, b), _COURSE) is a

def test_find_subject_by_slug_when_no_id():
    b = _FakeProfile("Outro Nome", slug="metodos-formais-para-computacao")
    assert find_subject_for_course(_FakeStore(b), _COURSE) is b

def test_find_subject_falls_back_to_name():
    c = _FakeProfile("Métodos Formais para Computação")
    assert find_subject_for_course(_FakeStore(c), _COURSE) is c

def test_find_subject_none_when_no_match():
    assert find_subject_for_course(_FakeStore(_FakeProfile("X")), _COURSE) is None
