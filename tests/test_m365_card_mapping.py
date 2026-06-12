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


from pathlib import Path
from src.builder.sources.m365 import download_subject_m365, filter_in_path

_BASE = "https://brpucrs-my.sharepoint.com/personal/p/Documents/Documentos/metodosformais"

class _FakeM365:
    """Client M365 fake: items de list_shared + bytes por nome."""
    def __init__(self, items, blobs):
        self._items, self._blobs = items, blobs
    def list_shared(self, top=200): return self._items
    def resolve(self, iid):
        it = next(i for i in self._items if i["id"] == iid)
        return {"name": it["title"], "id": iid, "parentReference": {"driveId": "D"}}
    def download(self, item): return self._blobs[item["name"]]

def _item(iid, title, sub=""):
    url = f"{_BASE}/{sub}/{title}" if sub else f"{_BASE}/{title}"
    return {"id": iid, "title": title, "type": "Pdf", "web_url": url}

def test_index_hit_beats_onedrive_folder(tmp_path):
    """O caso real do bug: pasta OneDrive 'logica' mas seção API = Verificação."""
    client = _FakeM365([_item("1", "LogicaDeHoare.pdf", "logica")],
                       {"LogicaDeHoare.pdf": b"%PDF-1.7 ok"})
    idx = {"logicadehoare.pdf": "Verificação de Programas"}
    rep = download_subject_m365(client, "metodosformais", idx, tmp_path)
    assert (tmp_path / "Verificação de Programas" / "LogicaDeHoare.pdf").exists()
    assert not (tmp_path / "logica").exists()
    assert rep["mapping"] == [("LogicaDeHoare.pdf", "Verificação de Programas", "moodle_api")]
    assert rep["name_to_section"]["logicadehoare.pdf"] == "Verificação de Programas"

def test_index_miss_falls_back_to_literal_folder(tmp_path):
    client = _FakeM365([_item("1", "extra.pdf", "dafny")], {"extra.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {"outro.pdf": "X"}, tmp_path)
    assert (tmp_path / "dafny" / "extra.pdf").exists()
    assert rep["mapping"] == [("extra.pdf", "dafny", "fallback_pasta")]
    assert rep["name_to_section"] == {}          # chute NUNCA vira source_section

def test_empty_index_means_all_fallback_with_warning(tmp_path):
    client = _FakeM365([_item("1", "a.pdf", "dafny")], {"a.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {}, tmp_path)
    assert (tmp_path / "dafny" / "a.pdf").exists()
    assert rep["name_to_section"] == {}
    assert any("Moodle" in w for w in rep["warnings"])

def test_zero_items_aborts_with_warning(tmp_path):
    client = _FakeM365([], {})
    rep = download_subject_m365(client, "naoexiste", {}, tmp_path)
    assert rep["total"] == 0 and rep["downloaded"] == 0
    assert any("filtro" in w for w in rep["warnings"])

def test_filter_not_in_path_majority_warns(tmp_path):
    items = [_item("1", "a.pdf", "dafny"),
             {"id": "2", "title": "b.pdf", "type": "Pdf",
              "web_url": "https://x/y/metodosformais.pdf"}]   # filtro só no NOME
    client = _FakeM365(items, {"a.pdf": b"%PDF-1.7 ok", "b.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {}, tmp_path)
    # 1 de 2 com filtro fora do caminho de pastas: 50% não dispara (>50% dispara)
    assert not any("caminho" in w for w in rep["warnings"])

def test_filter_in_path():
    assert filter_in_path(f"{_BASE}/dafny/a.pdf", "metodosformais") is True
    assert filter_in_path("https://x/y/z.pdf", "metodosformais") is False

def test_lexical_matching_is_dead():
    import src.builder.sources.m365 as m
    for nome in ("match_card", "_token_affinity", "_norm_tokens", "_DEFAULT_ALIASES"):
        assert not hasattr(m, nome), f"{nome} deveria ter sido removido"
