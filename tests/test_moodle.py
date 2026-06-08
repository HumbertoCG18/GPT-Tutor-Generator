from src.builder.sources.moodle import sanitize_folder_name, iter_section_files, SectionFile, MoodleClient


def test_sanitize_removes_invalid_windows_chars():
    assert sanitize_folder_name("Avisos | Dúvidas | Notícias") == "Avisos Dúvidas Notícias"
    assert sanitize_folder_name("Revisão - Lógica/Especificação") == "Revisão - Lógica Especificação"
    assert sanitize_folder_name("  Provas por Indução. ") == "Provas por Indução"
    assert sanitize_folder_name("") == "sem-secao"


def test_iter_section_files_extracts_files_by_section():
    contents = [
        {"name": "Plano de Ensino", "modules": [
            {"contents": [{"type": "file", "filename": "plano.pdf", "fileurl": "https://m/pluginfile.php/1/plano.pdf"}]},
        ]},
        {"name": "Vazia", "modules": []},
        {"name": "Verificação de Programas", "modules": [
            {"contents": [
                {"type": "file", "filename": "hoare.pdf", "fileurl": "https://m/pluginfile.php/2/hoare.pdf"},
                {"type": "url", "filename": "link", "fileurl": "https://x"},  # ignora não-file
            ]},
        ]},
    ]
    files = iter_section_files(contents)
    assert SectionFile("Plano de Ensino", "plano.pdf", "https://m/pluginfile.php/1/plano.pdf") in files
    assert any(f.section == "Verificação de Programas" and f.filename == "hoare.pdf" for f in files)
    assert all(f.filename != "link" for f in files)   # url ignorado
    assert len(files) == 2


def test_download_url_appends_token():
    c = MoodleClient("https://moodle.pucrs.br/", "TOK")
    u1 = c._download_url("https://moodle.pucrs.br/webservice/pluginfile.php/1/a.pdf")
    assert "token=TOK" in u1
    # preserva query existente
    u2 = c._download_url("https://moodle.pucrs.br/webservice/pluginfile.php/1/a.pdf?forcedownload=1")
    assert "token=TOK" in u2 and "forcedownload=1" in u2


def test_save_load_token_roundtrip_preserves_url(tmp_path):
    from src.builder.sources.moodle import save_moodle_token, load_moodle_token
    env = tmp_path / ".env"
    env.write_text("MOODLE_URL=https://moodle.pucrs.br\nMOODLE_TOKEN=old\n", encoding="utf-8")
    save_moodle_token("newtok", dotenv_path=env)
    url, tok = load_moodle_token(dotenv_path=env)
    assert tok == "newtok"
    assert url == "https://moodle.pucrs.br"


def test_save_token_creates_file_when_missing(tmp_path):
    from src.builder.sources.moodle import save_moodle_token, load_moodle_token
    env = tmp_path / "sub" / ".env"
    save_moodle_token("t1", dotenv_path=env)
    url, tok = load_moodle_token(dotenv_path=env)
    assert tok == "t1"
    assert url == "https://moodle.pucrs.br"


def test_login_posts_credentials_and_returns_token(monkeypatch):
    from src.builder.sources import moodle
    captured = {}
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"token":"abc123"}'
    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return _Resp()
    monkeypatch.setattr(moodle.urllib.request, "urlopen", fake_urlopen)
    tok = moodle.MoodleClient.login("https://moodle.pucrs.br", "matricula", "senha")
    assert tok == "abc123"
    assert "login/token.php" in captured["url"]
    assert b"matricula" in captured["data"]


def test_login_raises_on_error(monkeypatch):
    from src.builder.sources import moodle
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"error":"Invalid login"}'
    monkeypatch.setattr(moodle.urllib.request, "urlopen", lambda req, timeout=0: _Resp())
    import pytest
    with pytest.raises(RuntimeError):
        moodle.MoodleClient.login("https://moodle.pucrs.br", "x", "y")


def test_parse_moodle_course_full_pattern():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 92717, "shortname": "4646M-04031261",
         "fullname": "4646M-04 - Métodos Formais para Computação - Turma 031 - 2026/1 - Prof. Julio Henrique A P Machado"}
    r = parse_moodle_course(c)
    assert r["moodle_course_id"] == "92717"
    assert r["name"] == "Métodos Formais para Computação"
    assert r["professor"] == "Julio Henrique A P Machado"
    assert r["semester"] == "2026/1"
    assert r["slug"]


def test_parse_moodle_course_name_with_dashes():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 5, "fullname": "98H00-04 - Lógica - Fundamentos - Aplicações - Turma 031 - 2026/1 - Prof. X"}
    r = parse_moodle_course(c)
    assert r["name"] == "Lógica - Fundamentos - Aplicações"
    assert r["professor"] == "X"
    assert r["semester"] == "2026/1"


def test_parse_moodle_course_degraded_no_prof():
    from src.builder.sources.moodle import parse_moodle_course
    r = parse_moodle_course({"id": 1, "fullname": "Curso de Ciência da Computação"})
    assert r["moodle_course_id"] == "1"
    assert r["name"] == "Curso de Ciência da Computação"
    assert r["professor"] == ""
    assert r["semester"] == ""


def test_import_moodle_courses_upserts_and_downloads(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses

    class FakeStore:
        def __init__(self): self.data = {}
        def names(self): return list(self.data.keys())
        def get(self, n): return self.data.get(n)
        def add(self, p): self.data[p.name] = p

    class FakeClient:
        def __init__(self): self.calls = []
        def download_course(self, cid, dest, skip_existing=True):
            self.calls.append((str(cid), str(dest)))
            return {"total": 3, "downloaded": 3, "skipped": 0}

    store, client = FakeStore(), FakeClient()
    courses = [{"id": 92717, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. Julio"}]
    base = tmp_path / "Moodle"

    rep = import_moodle_courses(courses, base, store, client)
    assert len(store.names()) == 1
    sp = store.data["Métodos Formais"]
    assert sp.moodle_course_id == "92717"
    assert sp.stash_folder == str(base / sp.slug)
    assert client.calls == [("92717", str(base / sp.slug))]
    assert rep["created"] == 1 and rep["downloaded_files"] == 3

    rep2 = import_moodle_courses(courses, base, store, client)
    assert len(store.names()) == 1
    assert rep2["updated"] == 1 and rep2["created"] == 0


def test_latest_semester_picks_most_recent():
    from src.builder.sources.moodle import latest_semester
    courses = [
        {"id": 1, "fullname": "A - X - Turma 1 - 2025/2 - Prof. P"},
        {"id": 2, "fullname": "B - Y - Turma 1 - 2026/1 - Prof. Q"},
        {"id": 3, "fullname": "C - Z - 2024/1"},
        {"id": 4, "fullname": "Curso sem semestre"},
    ]
    assert latest_semester(courses) == "2026/1"


def test_latest_semester_empty_when_none():
    from src.builder.sources.moodle import latest_semester
    assert latest_semester([{"id": 9, "fullname": "Sem data"}]) == ""


def test_filter_courses_by_semester():
    from src.builder.sources.moodle import filter_courses_by_semester
    courses = [
        {"id": 1, "fullname": "A - X - Turma 1 - 2025/2 - Prof. P"},
        {"id": 2, "fullname": "B - Y - Turma 1 - 2026/1 - Prof. Q"},
    ]
    out = filter_courses_by_semester(courses, "2026/1")
    assert [c["id"] for c in out] == [2]


def test_section_file_index_maps_filename_to_section():
    from src.builder.sources.moodle import section_file_index
    contents = [
        {"name": "Plano de Ensino", "modules": [
            {"contents": [{"type": "file", "filename": "plano.pdf", "fileurl": "https://m/pluginfile.php/1/plano.pdf"}]}]},
        {"name": "Verificação de Programas", "modules": [
            {"contents": [{"type": "file", "filename": "Hoare.pdf", "fileurl": "https://m/x/Hoare.pdf"}]}]},
    ]
    idx = section_file_index(contents)
    assert idx["plano.pdf"] == "Plano de Ensino"
    assert idx["hoare.pdf"] == "Verificação de Programas"   # casefold


def test_backfill_source_section_from_api_matches_by_basename():
    from src.builder.sources.moodle import backfill_source_section_from_api
    contents = [
        {"name": "Introdução", "modules": [
            {"contents": [{"type": "file", "filename": "intro.pdf", "fileurl": "https://m/a/intro.pdf"}]}]},
        {"name": "Provas", "modules": [
            {"contents": [{"type": "file", "filename": "p.pdf", "fileurl": "https://m/b/p.pdf"}]}]},
    ]
    entries = [
        {"id": "intro", "source_path": "C:/old/INTRO.pdf"},  # case-insensitive
        {"id": "ghost", "source_path": "X:/none/ghost.pdf"},
    ]
    assignments, unmatched, ambiguous = backfill_source_section_from_api(entries, contents)
    assert assignments["intro"] == "Introdução"
    assert "ghost" in unmatched


def test_download_course_skips_html_and_json_error_responses(tmp_path, monkeypatch):
    from src.builder.sources import moodle
    # contents: 2 arquivos
    def fake_contents(self, courseid):
        return [{"name": "S", "modules": [{"contents": [
            {"type": "file", "filename": "good.pdf", "fileurl": "https://m/pluginfile.php/1/good.pdf"},
            {"type": "file", "filename": "bad.pdf", "fileurl": "https://m/pluginfile.php/2/bad.pdf"},
        ]}]}]
    monkeypatch.setattr(moodle.MoodleClient, "get_course_contents", fake_contents)
    class _Resp:
        def __init__(self, ct, data): self._ct=ct; self._d=data; self.headers={"content-type":ct}
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def read(self): return self._d
    def fake_urlopen(u, timeout=0):
        if "good.pdf" in u: return _Resp("application/pdf", b"%PDF-1.7 ok")
        return _Resp("text/html; charset=utf-8", b"<!DOCTYPE html> redirect")
    monkeypatch.setattr(moodle.urllib.request, "urlopen", fake_urlopen)
    c = moodle.MoodleClient("https://m", "tok")
    rep = c.download_course("1", tmp_path)
    assert rep["downloaded"] == 1
    assert "bad.pdf" in rep["failed"]
    assert (tmp_path / "S" / "good.pdf").exists()
    assert not (tmp_path / "S" / "bad.pdf").exists()   # NÃO salvou o HTML


def test_import_links_existing_subject_by_slug_keeping_repo(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses
    from src.models.core import SubjectProfile

    class FakeStore:
        def __init__(self): self.data = {}
        def names(self): return list(self.data.keys())
        def get(self, n): return self.data.get(n)
        def add(self, p): self.data[p.name] = p

    class FakeClient:
        def download_course(self, cid, dest, skip_existing=True):
            return {"total": 1, "downloaded": 1, "skipped": 0}

    store = FakeStore()
    # matéria pré-existente, criada manualmente: tem repo_root, SEM moodle_course_id
    existing = SubjectProfile(name="Métodos Formais", slug="metodos-formais",
                              repo_root="C:/repos/Metodos-Formais-Tutor")
    store.add(existing)

    courses = [{"id": 92717, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. Julio"}]
    rep = import_moodle_courses(courses, tmp_path / "Moodle", store, FakeClient())

    assert rep["created"] == 0
    assert rep["linked"] == 1
    sp = store.data["Métodos Formais"]
    assert sp.moodle_course_id == "92717"                       # ligou
    assert sp.repo_root == "C:/repos/Metodos-Formais-Tutor"     # PRESERVOU o repo
    assert sp.stash_folder == str((tmp_path / "Moodle") / sp.slug)
