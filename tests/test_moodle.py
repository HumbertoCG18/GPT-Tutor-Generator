import pytest
from src.builder.sources.moodle import (
    sanitize_folder_name, iter_section_files, SectionFile, MoodleClient,
    backfill_posting_date_from_api, posting_date_iso
)


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
    assert any(f.section == "Plano de Ensino" and f.filename == "plano.pdf"
               and f.fileurl == "https://m/pluginfile.php/1/plano.pdf" for f in files)
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


import json
from pathlib import Path
from src.builder.sources.moodle import (
    backfill_repo_signals_additive, backfill_repo_signals_consumed,
)

def _fake_repo(tmp_path, entries):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": [{"id": "bloco-01", "period_start": "2026-02-20",
                                "period_end": "2026-02-28", "unit_slug": "u1"}]}),
        encoding="utf-8")
    return repo

_CONTENTS = [{"name": "Semana 1", "modules": [
    {"name": "Exemplos (Hoare)", "contents": [
        {"type": "file", "filename": "main.pdf", "fileurl": "u",
         "timemodified": 1739361600, "timecreated": 1739000000}]}]}]

def test_additive_sets_posting_and_label_not_section(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf",
                                  "source_section": "OLD", "moodle_label": ""}])
    backfill_repo_signals_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1",
                                                     "turma": "031", "schedule_url": ""}, write=True)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    e = m["entries"][0]
    assert e["posting_date"] == "2025-02-12"
    assert e["moodle_label"] == "Exemplos (Hoare)"
    assert e["source_section"] == "OLD"          # additive NAO toca source_section
    assert m["turma"] == "031"

def test_additive_does_not_write_card_block_map(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf"}])
    backfill_repo_signals_additive(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    assert not (repo / "course" / ".card_block_map.json").exists()

def test_consumed_overwrites_section(tmp_path):
    repo = _fake_repo(tmp_path, [{"id": "e1", "source_path": "main.pdf", "source_section": "OLD"}])
    backfill_repo_signals_consumed(repo, _CONTENTS, {"name": "MF", "semester": "2026/1"}, write=True)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert m["entries"][0]["source_section"] == "Semana 1"   # consumed overwrita


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
        def get_course_contents(self, cid): return []
        def download_course(self, cid, dest, skip_existing=True):
            self.calls.append((str(cid), str(dest)))
            return {"total": 3, "downloaded": 3, "skipped": 0}

    store, client = FakeStore(), FakeClient()
    courses = [{"id": 92717, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. Julio"}]
    base = tmp_path / "Moodle"

    # download=False por default — não chama download_course
    rep = import_moodle_courses(courses, base, store, client)
    assert len(store.names()) == 1
    sp = store.data["Métodos Formais"]
    assert sp.moodle_course_id == "92717"
    assert sp.stash_folder == str(base / sp.slug)
    assert client.calls == []          # sem download por default
    assert rep["created"] == 1 and rep["downloaded"] == 0

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


def test_backfill_moodle_label_from_api_matches_by_basename():
    # alavanca 1: captura mod.get("name") (label do recurso) por basename, igual
    # ao source_section. Vem do payload da API -> antes do redirect SharePoint.
    from src.builder.sources.moodle import backfill_moodle_label_from_api
    contents = [
        {"name": "Verificacao de Programas", "modules": [
            {"name": "Exemplos (Logica de Floyd-Hoare)",
             "contents": [{"type": "file", "filename": "hoare.zip",
                           "fileurl": "https://m/a/hoare.zip"}]}]},
    ]
    entries = [
        {"id": "hoare", "source_path": "C:/x/HOARE.zip"},   # case-insensitive
        {"id": "ghost", "source_path": "X:/none/ghost.pdf"},
    ]
    out = backfill_moodle_label_from_api(entries, contents)
    assert out["hoare"] == "Exemplos (Logica de Floyd-Hoare)"
    assert "ghost" not in out


def test_iter_section_files_disambiguates_by_module_name():
    # professor nomeia todo PDF "main.pdf"; o nome do módulo distingue as aulas.
    contents = [{"name": "Semana 2", "modules": [
        {"name": "Aula 03 - Funções Recursivas", "contents": [
            {"type": "file", "filename": "main.pdf", "fileurl": "https://m/pluginfile.php/1/main.pdf"}]},
        {"name": "Aula 04 - Composição", "contents": [
            {"type": "file", "filename": "main.pdf", "fileurl": "https://m/pluginfile.php/2/main.pdf"}]},
    ]}]
    files = iter_section_files(contents)
    disk = sorted(f.disk_name for f in files)
    assert disk == ["Aula 03 - Funções Recursivas.pdf", "Aula 04 - Composição.pdf"]
    # filename ORIGINAL preservado (backfill casa por basename da API)
    assert all(f.filename == "main.pdf" for f in files)


def test_download_course_no_silent_collision_loss(tmp_path, monkeypatch):
    from src.builder.sources import moodle
    def fake_contents(self, courseid):
        return [{"name": "Semana 2", "modules": [
            {"name": "Aula 03", "contents": [
                {"type": "file", "filename": "main.pdf", "fileurl": "https://m/pluginfile.php/1/main.pdf"}]},
            {"name": "Aula 04", "contents": [
                {"type": "file", "filename": "main.pdf", "fileurl": "https://m/pluginfile.php/2/main.pdf"}]},
        ]}]
    monkeypatch.setattr(moodle.MoodleClient, "get_course_contents", fake_contents)
    class _Resp:
        def __init__(self, ct, data): self.headers={"content-type":ct}; self._d=data
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def read(self): return self._d
    monkeypatch.setattr(moodle.urllib.request, "urlopen",
                        lambda u, timeout=0: _Resp("application/pdf", b"%PDF-1.7 x"))
    c = moodle.MoodleClient("https://m", "tok")
    rep = c.download_course("1", tmp_path)
    assert rep["downloaded"] == 2 and rep["skipped"] == 0     # nada perdido
    assert (tmp_path / "Semana 2" / "Aula 03.pdf").exists()
    assert (tmp_path / "Semana 2" / "Aula 04.pdf").exists()


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


def test_download_course_rejects_wrong_magic_bytes_despite_content_type(tmp_path, monkeypatch):
    """Servidor mente o content-type (application/pdf) mas o corpo não é PDF.

    Defesa em profundidade: valida a assinatura do arquivo antes de gravar.
    Causa-raiz histórica: token inválido -> página de erro salva como .pdf.
    """
    from src.builder.sources import moodle
    def fake_contents(self, courseid):
        return [{"name": "S", "modules": [{"contents": [
            {"type": "file", "filename": "good.pdf", "fileurl": "https://m/pluginfile.php/1/good.pdf"},
            {"type": "file", "filename": "fake.pdf", "fileurl": "https://m/pluginfile.php/2/fake.pdf"},
            {"type": "file", "filename": "slides.pptx", "fileurl": "https://m/pluginfile.php/3/slides.pptx"},
        ]}]}]
    monkeypatch.setattr(moodle.MoodleClient, "get_course_contents", fake_contents)
    class _Resp:
        def __init__(self, ct, data): self.headers={"content-type":ct}; self._d=data
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def read(self): return self._d
    def fake_urlopen(u, timeout=0):
        if "good.pdf" in u:   return _Resp("application/pdf", b"%PDF-1.7 ok")
        if "fake.pdf" in u:   return _Resp("application/pdf", b'{"error":"invalidtoken"}')  # mente ct
        return _Resp("application/octet-stream", b"PK\x03\x04zipdata")                       # pptx = zip
    monkeypatch.setattr(moodle.urllib.request, "urlopen", fake_urlopen)
    c = moodle.MoodleClient("https://m", "tok")
    rep = c.download_course("1", tmp_path)
    assert (tmp_path / "S" / "good.pdf").exists()
    assert (tmp_path / "S" / "slides.pptx").exists()         # PK = assinatura zip válida p/ pptx
    assert not (tmp_path / "S" / "fake.pdf").exists()        # magic byte errado -> NÃO grava
    assert "fake.pdf" in rep["failed"]
    assert rep["downloaded"] == 2


def test_build_card_structure_creates_folders_and_listing(tmp_path):
    from src.builder.sources.moodle import build_card_structure
    contents = [
        {"name": "Plano de Ensino", "modules": [
            {"contents": [{"type": "file", "filename": "plano.pdf", "fileurl": "https://m/a/plano.pdf"}]}]},
        {"name": "Verificação de Programas", "modules": [
            {"contents": [
                {"type": "file", "filename": "Hoare.pdf", "fileurl": "https://m/b/Hoare.pdf"},
                {"type": "file", "filename": "Dafny.pdf", "fileurl": "https://m/b/Dafny.pdf"}]}]},
        {"name": "Vazia", "modules": []},
    ]
    rep = build_card_structure(tmp_path, contents)
    assert (tmp_path / "Plano de Ensino").is_dir()
    assert (tmp_path / "Verificação de Programas").is_dir()
    assert not (tmp_path / "Vazia").exists()          # seção sem arquivo: não cria
    listing = (tmp_path / "Verificação de Programas" / "_ARQUIVOS_DO_CARD.txt").read_text(encoding="utf-8")
    assert "Hoare.pdf" in listing and "Dafny.pdf" in listing
    assert rep["folders"] == 2
    assert rep["expected_files"] == 3


def test_import_moodle_courses_builds_structure_and_backfills(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses
    from src.models.core import SubjectProfile
    import json

    # repo da matéria existente com manifest (pra backfill)
    repo = tmp_path / "repo"
    (repo).mkdir()
    (repo / "manifest.json").write_text(json.dumps({"entries": [
        {"id": "plano", "source_path": "C:/x/plano.pdf"}]}), encoding="utf-8")

    class FakeStore:
        def __init__(self): self.data = {}
        def names(self): return list(self.data.keys())
        def get(self, n): return self.data.get(n)
        def add(self, p): self.data[p.name] = p
    store = FakeStore()
    store.add(SubjectProfile(name="Métodos Formais", slug="metodos-formais", repo_root=str(repo)))

    contents = [{"name": "Plano de Ensino", "modules": [
        {"contents": [{"type": "file", "filename": "plano.pdf", "fileurl": "https://m/a/plano.pdf"}]}]}]

    class FakeClient:
        def get_course_contents(self, cid): return contents
        def download_course(self, cid, dest, skip_existing=True):
            return {"total": 1, "downloaded": 0, "skipped": 0, "failed": ["plano.pdf"]}

    base = tmp_path / "Moodle"
    courses = [{"id": 92717, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. J"}]
    rep = import_moodle_courses(courses, base, store, FakeClient(), download=False)

    assert rep["linked"] == 1
    assert (base / "metodos-formais" / "Plano de Ensino").is_dir()   # estrutura criada
    # backfill aplicado no manifest do repo
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    assert man["entries"][0]["source_section"] == "Plano de Ensino"
    assert rep["backfilled"] == 1


def test_import_links_existing_subject_by_slug_keeping_repo(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses
    from src.models.core import SubjectProfile

    class FakeStore:
        def __init__(self): self.data = {}
        def names(self): return list(self.data.keys())
        def get(self, n): return self.data.get(n)
        def add(self, p): self.data[p.name] = p

    class FakeClient:
        def get_course_contents(self, cid): return []
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


def test_iter_section_files_captures_timestamps():
    contents = [{"name": "Semana 1", "modules": [
        {"name": "Aula", "contents": [
            {"type": "file", "filename": "a.pdf", "fileurl": "http://x/a.pdf",
             "timemodified": 1739361600, "timecreated": 1739000000}]}]}]
    sf = iter_section_files(contents)[0]
    assert sf.timemodified == 1739361600
    assert sf.timecreated == 1739000000


def test_posting_date_iso_utc():
    assert posting_date_iso(1739361600) == "2025-02-12"   # 12:00 UTC
    assert posting_date_iso(0) == ""
    assert posting_date_iso(None) == ""


def test_backfill_posting_date_unique_match():
    contents = [{"name": "S1", "modules": [
        {"name": "Aula", "contents": [
            {"type": "file", "filename": "main.pdf", "fileurl": "u",
             "timemodified": 1739361600, "timecreated": 1739000000}]}]}]
    entries = [{"id": "e1", "source_path": "C:/x/main.pdf"}]
    out = backfill_posting_date_from_api(entries, contents)
    assert out["e1"] == {"timemodified": 1739361600, "timecreated": 1739000000}


def test_backfill_posting_date_skips_ambiguous_basename():
    contents = [{"name": "S1", "modules": [
        {"name": "A", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u",
                                     "timemodified": 1, "timecreated": 1}]},
        {"name": "B", "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u2",
                                     "timemodified": 2, "timecreated": 2}]}]}]
    entries = [{"id": "e1", "source_path": "main.pdf"}]
    assert backfill_posting_date_from_api(entries, contents) == {}


def test_parse_turma_single():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 1, "fullname": "4646M-04 - Métodos Formais - Turma 031 - 2026/1 - Prof. X"}
    assert parse_moodle_course(c)["turma"] == "031"


def test_parse_turma_multiple():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 2, "fullname": "98702-04 - Prática em Pesquisa - Turmas 010 - 011 - 012 - 2026/1 - Profs. Y"}
    assert parse_moodle_course(c)["turma"] == "010 - 011 - 012"


def test_parse_turma_absent():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 3, "fullname": "Curso de Ciência da Computação"}
    assert parse_moodle_course(c)["turma"] == ""


def test_sanitize_preserves_date_slash_as_dot():
    from src.builder.sources.moodle import sanitize_folder_name
    assert sanitize_folder_name("18/06 exemplo") == "18.06 exemplo"
    assert sanitize_folder_name("Aula 18/06/2026") == "Aula 18.06.2026"
    assert "/" not in sanitize_folder_name("a/b")   # slash entre letras vira espaco


@pytest.mark.parametrize("raw, expected", [
    ("20/04 a 24/4", "20.04 a 24.04"),   # zero-pad do mês de 1 dígito
    ("24/4", "24.04"),
    ("06/12/2026", "06.12.2026"),         # data completa, ano preservado
    ("18/06", "18.06"),                    # ja 2-digito: no-op (preserva atual)
    ("1/2", "01.02"),
    ("12/2025", "12.2025"),                # mes/ano: cai no passe generico, sem pad
    ("versao 1.2", "versao 1.2"),          # separador '.' (versao) intacto
    ("2.10.1", "2.10.1"),                  # versao 3-partes intacta
    ("Seção A/B", "Seção A B"),            # '/' nao-data vira espaco (atual)
])
def test_sanitize_folder_name_date_padding(raw, expected):
    assert sanitize_folder_name(raw) == expected
