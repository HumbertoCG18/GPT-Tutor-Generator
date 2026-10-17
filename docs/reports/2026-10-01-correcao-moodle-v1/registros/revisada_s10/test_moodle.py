import io

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


# --- Orçamento de bytes do webservice (R-META, 29/09): bytes dos CORPOS HTTP lidos pela aplicação ---------------------
# Transporte falso: http.client.HTTPResponse real sobre BytesIO; nenhuma rede.

class _SocketFalso:
    def __init__(self, bruto):
        self.bruto = bruto

    def makefile(self, modo):
        import io
        return io.BytesIO(self.bruto)


def _resposta_http(corpo, content_length=True):
    import http.client
    cab = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
    if content_length is True:
        cab += f"Content-Length: {len(corpo)}\r\n"
    elif content_length:
        cab += f"Content-Length: {content_length}\r\n"
    else:
        cab += "Connection: close\r\n"
    r = http.client.HTTPResponse(_SocketFalso(cab.encode() + b"\r\n" + corpo))
    r.begin()
    return r


def _cliente_com_respostas(monkeypatch, respostas, limite=None):
    from src.builder.sources import moodle
    chamadas = []

    def fake_urlopen(req, timeout=0):
        chamadas.append(req)
        return respostas.pop(0)

    monkeypatch.setattr(moodle.urllib.request, "urlopen", fake_urlopen)
    c = moodle.MoodleClient("https://m", "tok")
    c.limite_bytes = limite
    return c, chamadas


def test_call_conta_bytes_do_corpo_e_mantem_resultado_sem_limite(monkeypatch):
    import json
    a = json.dumps({"userid": 7, "siteurl": "https://m"}, indent=3).encode()   # indentado: != tamanho reserializado
    b = json.dumps([{"id": 1, "fullname": "X"}]).encode()
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(a), _resposta_http(b, content_length=False)])
    assert c.site_info() == {"userid": 7, "siteurl": "https://m"}
    assert c.get_users_courses(7) == [{"id": 1, "fullname": "X"}]
    assert c.bytes_recebidos == len(a) + len(b)


def test_call_corpo_exatamente_no_limite_com_termino_confirmado(monkeypatch):
    corpo = b'{"ok": [1, 2, 3]}'
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(corpo)], limite=len(corpo))
    assert c.get_course_contents(1) == {"ok": [1, 2, 3]}
    assert c.bytes_recebidos == len(corpo)


@pytest.mark.parametrize("tamanho", [20, 30], ids=["exato-sem-content-length", "maior-sem-content-length"])
def test_call_termino_nao_confirmado_nao_ultrapassa_o_orcamento(monkeypatch, tamanho):
    from src.builder.sources import moodle
    corpo = b"[" + b"1," * ((tamanho - 3) // 2) + b"1]"
    corpo = corpo + b" " * (tamanho - len(corpo))
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(corpo, content_length=False)], limite=20)
    with pytest.raises(moodle.OrcamentoExcedido) as exc:
        c.get_course_contents(1)
    assert c.bytes_recebidos == 20 and exc.value.parcial == corpo[:20]


def test_call_content_length_acima_do_orcamento_nao_le_o_corpo(monkeypatch):
    from src.builder.sources import moodle
    corpo = b"x" * 30
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(corpo)], limite=20)
    with pytest.raises(moodle.OrcamentoExcedido):
        c.get_course_contents(1)
    assert c.bytes_recebidos == 0


@pytest.mark.parametrize("limite", [None, 100], ids=["sem-limite", "com-limite"])
def test_call_corpo_truncado_conta_e_preserva_o_parcial(monkeypatch, limite):
    import http.client
    corpo = b'{"trunc'
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(corpo, content_length=30)], limite=limite)
    with pytest.raises(http.client.IncompleteRead) as exc:
        c.get_course_contents(1)
    assert c.bytes_recebidos == len(corpo) and exc.value.partial == corpo and c.ultimo_corpo == corpo


def test_call_orcamento_esgotado_nao_abre_a_requisicao(monkeypatch):
    from src.builder.sources import moodle
    c, chamadas = _cliente_com_respostas(monkeypatch, [], limite=10)
    c.bytes_recebidos = 10
    with pytest.raises(moodle.OrcamentoExcedido):
        c.site_info()
    assert chamadas == []


def test_call_json_invalido_e_erro_da_api_contam_bytes(monkeypatch):
    import json
    ruim = b"{nao e json"
    erro = json.dumps({"exception": "x", "errorcode": "invalidtoken", "message": "m"}).encode()
    c, _ = _cliente_com_respostas(monkeypatch, [_resposta_http(ruim), _resposta_http(erro)])
    with pytest.raises(ValueError):
        c.site_info()
    assert c.bytes_recebidos == len(ruim) and c.ultimo_corpo == ruim
    with pytest.raises(RuntimeError, match="invalidtoken"):
        c.site_info()
    assert c.bytes_recebidos == len(ruim) + len(erro)


def test_call_interrupcao_preserva_a_contagem_dos_blocos_lidos(monkeypatch):
    from src.builder.sources import moodle

    class _Interrompe:
        headers = {}

        def __init__(self):
            self.leituras = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, amt=-1):
            self.leituras += 1
            if self.leituras == 2:
                raise KeyboardInterrupt
            return b"abcd"[:amt]

    monkeypatch.setattr(moodle, "_BLOCO_LEITURA", 4)
    c, _ = _cliente_com_respostas(monkeypatch, [_Interrompe()])
    with pytest.raises(KeyboardInterrupt):
        c.site_info()
    assert c.bytes_recebidos == 4 and c.ultimo_corpo == b"abcd"


# --- Contrato R1–R6 da leitura do corpo (correção V1, 01/10) ------------------------------------------------------------
# Casos dos reprodutores (C/M/A, 30/09–01/10) e casos novos, por comportamento. O corpo é uma sequência de segmentos:
# framing ("f"), payload ("p") ou proibido ("x": nada pode ser lido dali); o 3º item repete o segmento. "delta" diz o
# estado esperado no delta de 29/09 (defeito, controle, regra nova ou caso novo). O harness stdlib da noite
# (docs/reports/2026-10-01-correcao-moodle-v1/) extrai por AST estas definições, sem pytest, e roda nos três runtimes.
_CASOS_ORCAMENTO = [
    # M-01: payload de chunk interrompido é contado (R1)
    {"id": "M1a", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"5\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 3, "corpo": b"abc", "causa": True}},
    {"id": "M1b", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n5\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 5, "corpo": b"[]abc", "causa": True}},
    {"id": "M1c", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "limite": 10,
     "fio": ((b"5\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 3, "corpo": b"abc", "causa": True}},
    {"id": "M1d", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "bloco": 4,
     "fio": ((b"4\r\n", "f"), (b"[]  ", "p"), (b"\r\n5\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 7, "corpo": b"[]  abc", "causa": True}},
    {"id": "A07", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "limite": 5,
     "fio": ((b"A\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 3, "corpo": b"abc", "causa": True}},
    {"id": "A08", "grupo": "M-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "limite": 12,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n1\r\n", "f"), (b" ", "p"), (b"\r\n9\r\n", "f"), (b"abc", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 6, "corpo": b"[] abc", "causa": True}},
    # M-02: o Content-Length não governa resposta chunked (R4)
    {"id": "M2a", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "M2b", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 2\r\n",
     "limite": 2, "fio": ((b"5\r\n", "f"), (b"[]xxx", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    {"id": "M2c", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "limite": 3, "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A02", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "limite": 3, "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\nX-Test: ok\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A03", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 2\r\n",
     "limite": 2, "fio": ((b"2;x=y\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\nX: y\r\n\r\n", "f")),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    {"id": "A12", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "limite": 3, "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A16", "grupo": "M-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "limite": 3, "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\nX-Test: incompleto", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    # P-01: payload contado antes de falha de framing (LineTooLong, timeout)
    {"id": "A18", "grupo": "P-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n", "f"), (b"F", "f", 65537)),
     "esp": {"tipo": "LineTooLong", "bytes": 2, "corpo": b"[]"}},
    {"id": "A19", "grupo": "P-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\nX: ", "f"), (b"x", "f", 65537)),
     "esp": {"tipo": "LineTooLong", "bytes": 2, "corpo": b"[]"}},
    {"id": "A20", "grupo": "P-01", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n", "bloco": 2,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n", "f"), (b"F", "f", 65537)),
     "esp": {"tipo": "LineTooLong", "bytes": 2, "corpo": b"[]"}},
    {"id": "A33", "grupo": "P-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "corte": 7,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "TimeoutError", "bytes": 2, "corpo": b"[]"}},
    {"id": "A34", "grupo": "P-01", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "corte": 10,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "TimeoutError", "bytes": 2, "corpo": b"[]"}},
    # P-02: tamanho de chunk negativo recusado antes de qualquer leitura de payload (R2), com ou sem CL
    {"id": "A21", "grupo": "P-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"-1\r\n", "f"), (b"[] ", "x")),
     "esp": {"tipo": "IncompleteRead", "bytes": 0, "corpo": b"", "validou_tamanho": True}},
    {"id": "A22", "grupo": "P-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\n", "limite": 2,
     "fio": ((b"-1\r\n", "f"), (b"[]", "x"), (b" ", "x", 21)),
     "esp": {"tipo": "IncompleteRead", "bytes": 0, "corpo": b"", "validou_tamanho": True}},
    {"id": "A35", "grupo": "P-02", "delta": "defeito", "cab": "Transfer-Encoding: chunked\r\nContent-Length: 999\r\n",
     "limite": 2, "fio": ((b"-1\r\n", "f"), (b"[]", "x"), (b" ", "x", 21)),
     "esp": {"tipo": "IncompleteRead", "bytes": 0, "corpo": b"", "validou_tamanho": True}},
    # R5: Transfer-Encoding diferente de `chunked` (lista, outro coding, repetido) recusado antes do corpo
    {"id": "A23", "grupo": "R5", "delta": "regra_nova", "cab": "Transfer-Encoding: gzip\r\nContent-Length: 2\r\n",
     "limite": 2, "fio": ((b"[]xxx", "x"),),
     "esp": {"tipo": "UnknownTransferEncoding", "bytes": 0, "corpo": b"", "sem_leitura": True}},
    {"id": "A24", "grupo": "R5", "delta": "regra_nova", "cab": "Transfer-Encoding: gzip, chunked\r\n",
     "fio": ((b"2\r\n[]\r\n0\r\n\r\n", "x"),),
     "esp": {"tipo": "UnknownTransferEncoding", "bytes": 0, "corpo": b"", "sem_leitura": True}},
    {"id": "TE-REPETIDO", "grupo": "R5", "delta": "regra_nova",
     "cab": "Transfer-Encoding: chunked\r\nTransfer-Encoding: chunked\r\n", "fio": ((b"2\r\n[]\r\n0\r\n\r\n", "x"),),
     "esp": {"tipo": "UnknownTransferEncoding", "bytes": 0, "corpo": b"", "sem_leitura": True}},
    {"id": "TE-IDENTITY", "grupo": "R5", "delta": "regra_nova",
     "cab": "Transfer-Encoding: identity\r\nContent-Length: 2\r\n", "fio": ((b"[]", "x"),),
     "esp": {"tipo": "UnknownTransferEncoding", "bytes": 0, "corpo": b"", "sem_leitura": True}},
    {"id": "TE-CAIXA", "grupo": "R5", "delta": "controle", "cab": "Transfer-Encoding: Chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    # chunk terminal: pendente, transição e fim distinguidos; só o chunk zero dá corpo vazio
    {"id": "C02", "grupo": "terminal", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A01", "grupo": "terminal", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n", "limite": 3,
     "fio": ((b"2;foo=bar\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "SO-ZERO", "grupo": "terminal", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"0\r\n\r\n", "f"),),
     "esp": {"tipo": "JSONDecodeError", "bytes": 0, "corpo": b""}},
    {"id": "SO-ZERO-LIMITE", "grupo": "terminal", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "limite": 5, "fio": ((b"0\r\n\r\n", "f"),),
     "esp": {"tipo": "JSONDecodeError", "bytes": 0, "corpo": b""}},
    # parcial de CRLF não é payload (R3)
    {"id": "C16", "grupo": "crlf", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r", "f")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    {"id": "C17", "grupo": "crlf", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"", "f")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    {"id": "A09", "grupo": "crlf", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n", "bloco": 2,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r", "f")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    # read1 curto: continua, conta o tamanho real uma vez, mantém o resto do chunk
    {"id": "C09", "grupo": "read1-curto", "delta": "controle", "cab": "Content-Length: 5\r\n", "limite": 5,
     "read1_max": 1, "fio": ((b"[1,2]", "p"),),
     "esp": {"tipo": "sucesso", "retorno": [1, 2], "bytes": 5, "corpo": b"[1,2]"}},
    {"id": "CHUNK-CURTO", "grupo": "read1-curto", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "limite": 6, "read1_max": 1, "fio": ((b"5\r\n", "f"), (b"[1,2]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [1, 2], "bytes": 5, "corpo": b"[1,2]"}},
    {"id": "CHUNK-MAIOR-QUE-BLOCO", "grupo": "read1-curto", "delta": "controle",
     "cab": "Transfer-Encoding: chunked\r\n", "bloco": 4,
     "fio": ((b"A\r\n", "f"), (b"[1,2,3,4] ", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [1, 2, 3, 4], "bytes": 10, "corpo": b"[1,2,3,4] "}},
    # timeout no meio do payload: retém exatamente os fragmentos entregues, sem zerar nem duplicar
    {"id": "TIMEOUT-PAYLOAD", "grupo": "timeout-payload", "delta": "novo", "cab": "Transfer-Encoding: chunked\r\n",
     "corte": 5, "fio": ((b"5\r\n", "f"), (b"[1,2]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "TimeoutError", "bytes": 2, "corpo": b"[1"}},
    # sem Content-Length, não chunked: lê até o fim; no saldo exato recusa sem sondar
    {"id": "C04", "grupo": "sem-CL", "delta": "controle", "cab": "Connection: close\r\n", "limite": 2,
     "fio": ((b"[]", "p"),), "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    {"id": "C05", "grupo": "sem-CL", "delta": "controle", "cab": "Connection: close\r\n", "limite": 2,
     "fio": ((b"[]xxx", "p"),), "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    {"id": "C10", "grupo": "sem-CL", "delta": "controle", "cab": "Connection: close\r\n", "limite": 6,
     "read1_max": 1, "fio": ((b"[1,2]", "p"),),
     "esp": {"tipo": "sucesso", "retorno": [1, 2], "bytes": 5, "corpo": b"[1,2]"}},
    {"id": "C12", "grupo": "sem-CL", "delta": "controle", "cab": "Content-Length: lixo\r\n",
     "fio": ((b"[]", "p"),), "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    # Content-Length válido, não chunked: prova a completude
    {"id": "C01", "grupo": "CL", "delta": "controle", "cab": "Content-Length: 2\r\n", "limite": 9, "anterior": 7,
     "fio": ((b"[]", "p"),), "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "C11", "grupo": "CL", "delta": "controle", "cab": "Content-Length: 5\r\n",
     "fio": ((b"[]", "p"),), "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]"}},
    {"id": "C19", "grupo": "CL", "delta": "controle", "cab": "Content-Length: 65536\r\n", "limite": 65536,
     "fio": ((b"[]", "p"), (b" ", "p", 65534)),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 65536, "corpo": b"[]" + b" " * 65534}},
    {"id": "C20", "grupo": "CL", "delta": "controle", "cab": "Content-Length: 65539\r\n", "limite": 65539,
     "fio": ((b"[]", "p"), (b" ", "p", 65537)),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 65539, "corpo": b"[]" + b" " * 65537}},
    # saldo exato em chunked: recusa sem ler o framing seguinte (ordem saldo → framing)
    {"id": "C03", "grupo": "saldo-exato", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n", "limite": 2,
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n\r\n", "f")),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    {"id": "A31", "grupo": "saldo-exato", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n", "limite": 2,
     "fio": ((b"2\r\n", "f"), (b"[]", "p")),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 2, "corpo": b"[]"}},
    # controles de saldo, leitura e erros (A25≡C07, A26≡C08, A27≡C05, A28≡C13, A29≡C14, A30≡C15, A10≡C16)
    {"id": "C06", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 2\r\n", "limite": 1,
     "fio": ((b"[]", "p"),), "esp": {"tipo": "OrcamentoExcedido", "bytes": 0, "corpo": b"", "sem_leitura": True}},
    {"id": "C07", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 2\r\n", "limite": 2,
     "anterior": 2, "fio": ((b"[]", "p"),),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 0, "corpo": b"", "aberturas": 0, "sem_leitura": True}},
    {"id": "C08", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 2\r\n", "limite": 2,
     "anterior": 3, "fio": ((b"[]", "p"),),
     "esp": {"tipo": "OrcamentoExcedido", "bytes": 0, "corpo": b"", "aberturas": 0, "sem_leitura": True}},
    {"id": "C13", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 5\r\n",
     "fio": ((b"[]xxx", "p"),), "esp": {"tipo": "JSONDecodeError", "bytes": 5, "corpo": b"[]xxx"}},
    {"id": "C14", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 1\r\n",
     "fio": ((b"\xff", "p"),), "esp": {"tipo": "UnicodeDecodeError", "bytes": 1, "corpo": b"\xff"}},
    {"id": "C15", "grupo": "controles", "delta": "controle", "cab": "Content-Length: 58\r\n",
     "fio": ((b'{"exception":"x","errorcode":"synthetic","message":"test"}', "p"),),
     "esp": {"tipo": "RuntimeError", "bytes": 58,
             "corpo": b'{"exception":"x","errorcode":"synthetic","message":"test"}'}},
    {"id": "C18", "grupo": "controles", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\nZZ\r\n", "f")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    {"id": "A04", "grupo": "controles", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"5", "f"), (b"", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 0, "corpo": b"", "causa": True}},
    {"id": "A05", "grupo": "controles", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n5", "f"), (b"", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    {"id": "A06", "grupo": "controles", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"5\r\n", "f"), (b"", "p")),
     "esp": {"tipo": "IncompleteRead", "bytes": 0, "corpo": b"", "causa": True}},
    {"id": "A17", "grupo": "controles", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n", "f")),
     "esp": {"tipo": "IncompleteRead", "bytes": 2, "corpo": b"[]", "causa": True}},
    # tolerâncias de framing da stdlib mantidas pela V1 (R6; declaradas, não endurecidas)
    {"id": "A11", "grupo": "tolerancias", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A13", "grupo": "tolerancias", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A14", "grupo": "tolerancias", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A15", "grupo": "tolerancias", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"\r\n0\r\nX-Test: incompleto", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
    {"id": "A32", "grupo": "tolerancias", "delta": "controle", "cab": "Transfer-Encoding: chunked\r\n",
     "fio": ((b"2\r\n", "f"), (b"[]", "p"), (b"XX0\r\n\r\n", "f")),
     "esp": {"tipo": "sucesso", "retorno": [], "bytes": 2, "corpo": b"[]"}},
]

# R02: o último corpo só muda quando uma resposta nova começa a ser lida.
_R02_ESPERADO = [("sucesso", 2, b"[]"), ("OSError", 2, b"[]"), ("OrcamentoExcedido", 2, b"[]"),
                 ("OrcamentoExcedido", 2, b"")]


class _FioCorpo(io.BytesIO):
    """Corpo HTTP instrumentado: registra cada operação depois do cabeçalho (pedido, posição no corpo, dados, erro),
    inclusive as que lançam exceção. `corte`: posição do corpo a partir da qual nada chega (timeout do socket; o que
    passaria do corte não é entregue). `read1_max`: retorno curto do read1, como num socket."""

    def __init__(self, bruto, inicio, corte=None, read1_max=None):
        super().__init__(bruto)
        self.inicio, self.read1_max, self.ops, self.gravando = inicio, read1_max, [], False
        self.corte = None if corte is None else inicio + corte

    def _registra(self, op, pedido, fazer):
        pos = self.tell()
        try:
            dado = fazer(pos)
        except BaseException as exc:
            if self.gravando:
                self.ops.append({"op": op, "pedido": pedido, "pos": pos - self.inicio, "dado": b"",
                                 "erro": type(exc).__name__})
            raise
        if self.gravando:
            self.ops.append({"op": op, "pedido": pedido, "pos": pos - self.inicio, "dado": bytes(dado), "erro": None})
        return dado

    def _ate_o_corte(self, pos, dado):
        if self.corte is not None and pos + len(dado) > self.corte:
            self.seek(pos)
            raise TimeoutError("timeout sintético do socket")
        return dado

    def read(self, n=-1):
        return self._registra("read", n, lambda pos: self._ate_o_corte(pos, io.BytesIO.read(self, n)))

    def readline(self, limite=-1):
        return self._registra("readline", limite, lambda pos: self._ate_o_corte(pos, io.BytesIO.readline(self, limite)))

    def read1(self, n=-1):
        def fazer(pos):
            m = len(self.getvalue()) - pos if n is None or n < 0 else n
            if self.read1_max is not None:
                m = min(m, self.read1_max)
            if self.corte is not None and m > 0:
                if pos >= self.corte:
                    raise TimeoutError("timeout sintético do socket")
                m = min(m, self.corte - pos)
            return io.BytesIO.read1(self, m)
        return self._registra("read1", n, fazer)

    def readinto(self, b):
        raise AssertionError("readinto não instrumentado")


def _monta_fio(fio):
    corpo, mapa = b"", []
    for seg in fio:
        dado = seg[0] * (seg[2] if len(seg) > 2 else 1)
        mapa.append((len(corpo), len(corpo) + len(dado), seg[1]))
        corpo += dado
    return corpo, mapa


def _tipo_em(mapa, pos):
    return next((t for ini, fim, t in mapa if ini <= pos < fim), mapa[-1][2])


def _executa_caso(caso, moodle, troca):
    """Roda o caso no cliente real sobre `http.client.HTTPResponse` real. `troca(obj, nome, valor)` é o
    monkeypatch.setattr (no harness, um equivalente que desfaz ao fim)."""
    import http.client
    import types
    corpo, _ = _monta_fio(caso["fio"])
    cab = ("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n" + caso["cab"] + "\r\n").encode()
    fio = _FioCorpo(cab + corpo, len(cab), caso.get("corte"), caso.get("read1_max"))
    aberturas = []

    def urlopen_falso(req, timeout=0):
        aberturas.append(req)
        r = http.client.HTTPResponse(types.SimpleNamespace(makefile=lambda modo: fio))
        r.begin()
        fio.gravando = True
        return r

    troca(moodle.urllib.request, "urlopen", urlopen_falso)
    if "bloco" in caso:
        troca(moodle, "_BLOCO_LEITURA", caso["bloco"])
    c = moodle.MoodleClient("https://m", "tok")
    c.limite_bytes, c.bytes_recebidos = caso.get("limite"), caso.get("anterior", 0)
    retorno, exc = None, None
    try:
        retorno = c.get_course_contents(1)
    except Exception as e:  # o oráculo compara o tipo
        exc = e
    return {"tipo": "sucesso" if exc is None else type(exc).__name__, "retorno": retorno, "exc": exc,
            "bytes": c.bytes_recebidos - caso.get("anterior", 0), "corpo": c.ultimo_corpo,
            "aberturas": len(aberturas), "ops": fio.ops}


def _confere_caso(caso, res):
    """Falhas do caso: ("historico", ...) nos observáveis dos reprodutores; ("novo", ...) nas asserções da V1 —
    R1/R3 (contador e corpo = payload entregue pelo fio), R2 (pedido de payload ≤ saldo; nada lido do trecho
    proibido), causa encadeada, R6 (sem limite, corpo = r.read()), sem leitura e validação do tamanho."""
    esp, falhas = caso["esp"], []

    def confere(cat, nome, esperado, obtido):
        if esperado != obtido:
            falhas.append((cat, nome, esperado, obtido))

    confere("historico", "tipo", esp["tipo"], res["tipo"])
    if esp["tipo"] == "sucesso":
        confere("historico", "retorno", esp["retorno"], res["retorno"])
    confere("historico", "bytes", esp["bytes"], res["bytes"])
    confere("historico", "corpo", esp["corpo"], res["corpo"])
    if esp["tipo"] == "IncompleteRead" and res["tipo"] == "IncompleteRead":
        confere("historico", "partial", esp["corpo"], res["exc"].partial)
    confere("historico", "aberturas", esp.get("aberturas", 1), res["aberturas"])

    corpo_fio, mapa = _monta_fio(caso["fio"])
    teto = None if caso.get("limite") is None else caso["limite"] - caso.get("anterior", 0)
    entregue = {"f": b"", "p": b"", "x": b""}
    for op in res["ops"]:
        inicio = _tipo_em(mapa, op["pos"])
        resumo = (op["op"], op["pedido"], op["pos"], len(op["dado"]), op["erro"])
        if inicio == "x":
            falhas.append(("novo", "R2: operação no trecho proibido", None, resumo))
        if teto is not None and op["op"] != "readline" and inicio != "f":
            pedido = op["pedido"] if op["pedido"] is not None and op["pedido"] >= 0 else float("inf")
            if pedido > teto - len(entregue["p"]):
                falhas.append(("novo", "R2: pedido de payload acima do saldo", teto - len(entregue["p"]), resumo))
        for ini, fim, t in mapa:
            a, b = max(ini, op["pos"]), min(fim, op["pos"] + len(op["dado"]))
            if a < b:
                entregue[t] += op["dado"][a - op["pos"]:b - op["pos"]]
    confere("novo", "R2: bytes entregues do trecho proibido", b"", entregue["x"])
    confere("novo", "R1/R3: contador = payload entregue pelo fio", len(entregue["p"]), res["bytes"])
    confere("novo", "R1/R3: corpo = payload entregue pelo fio", entregue["p"], res["corpo"])
    if "causa" in esp and res["exc"] is not None:
        confere("novo", "causa encadeada", esp["causa"], res["exc"].__cause__ is not None)
    if esp.get("sem_leitura"):
        confere("novo", "nenhuma operação no corpo", [], [op["op"] for op in res["ops"]])
    if esp.get("validou_tamanho"):
        ult = res["ops"][-1] if res["ops"] else {"op": None, "dado": b""}
        confere("novo", "tamanho negativo lido e nada depois", True,
                ult["op"] == "readline" and ult["dado"].lstrip().startswith(b"-"))
    if caso.get("limite") is None and esp["tipo"] == "sucesso":
        import http.client
        import types
        bruto = ("HTTP/1.1 200 OK\r\n" + caso["cab"] + "\r\n").encode() + corpo_fio
        r = http.client.HTTPResponse(types.SimpleNamespace(makefile=lambda modo: io.BytesIO(bruto)))
        r.begin()
        confere("novo", "R6: corpo = r.read() sem limite", r.read(), res["corpo"])
    return falhas


def _sequencia_r02(moodle, troca):
    import http.client
    import types

    def resposta(req, timeout=0):
        bruto = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n[]"
        r = http.client.HTTPResponse(types.SimpleNamespace(makefile=lambda modo: io.BytesIO(bruto)))
        r.begin()
        return r

    def falha(req, timeout=0):
        raise OSError("rede indisponível")

    c, obs = moodle.MoodleClient("https://m", "tok"), []
    for urlopen, limite in ((resposta, None), (falha, None), (resposta, 2), (resposta, 3)):
        troca(moodle.urllib.request, "urlopen", urlopen)
        c.limite_bytes = limite
        try:
            c.get_course_contents(1)
            tipo = "sucesso"
        except Exception as e:  # o oráculo compara o tipo
            tipo = type(e).__name__
        obs.append((tipo, c.bytes_recebidos, c.ultimo_corpo))
    return obs


_GRUPOS_TESTADOS = set()


def _casos(grupo):
    _GRUPOS_TESTADOS.add(grupo)
    return [pytest.param(c, id=c["id"]) for c in _CASOS_ORCAMENTO if c["grupo"] == grupo]


def _confere(monkeypatch, caso):
    from src.builder.sources import moodle
    falhas = _confere_caso(caso, _executa_caso(caso, moodle, monkeypatch.setattr))
    assert not falhas, falhas


@pytest.mark.parametrize("caso", _casos("M-01"))
def test_contrato_payload_de_chunk_interrompido_e_contado(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("M-02"))
def test_contrato_content_length_nao_governa_resposta_chunked(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("P-01"))
def test_contrato_payload_contado_antes_de_falha_de_framing(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("P-02"))
def test_contrato_tamanho_negativo_recusado_antes_do_payload(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("R5"))
def test_contrato_transfer_encoding_nao_suportado_recusado_antes_do_corpo(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("terminal"))
def test_contrato_chunk_terminal_confirma_o_fim(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("crlf"))
def test_contrato_parcial_de_crlf_nao_e_payload(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("read1-curto"))
def test_contrato_leitura_curta_continua_e_conta_uma_vez(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("timeout-payload"))
def test_contrato_timeout_no_payload_retem_os_fragmentos_entregues(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("sem-CL"))
def test_contrato_sem_content_length_le_ate_o_fim_ou_recusa_no_saldo(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("CL"))
def test_contrato_content_length_valido_prova_a_completude(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("saldo-exato"))
def test_contrato_saldo_exato_em_chunked_recusa_sem_ler_o_framing(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("controles"))
def test_contrato_controles_de_saldo_leitura_e_erros(monkeypatch, caso):
    _confere(monkeypatch, caso)


@pytest.mark.parametrize("caso", _casos("tolerancias"))
def test_contrato_tolerancias_de_framing_da_stdlib_mantidas(monkeypatch, caso):
    _confere(monkeypatch, caso)


def test_contrato_todo_caso_pertence_a_um_teste():
    ids = [c["id"] for c in _CASOS_ORCAMENTO]
    assert len(ids) == len(set(ids))
    assert {c["grupo"] for c in _CASOS_ORCAMENTO} == _GRUPOS_TESTADOS


def test_call_retencao_do_ultimo_corpo_entre_chamadas(monkeypatch):
    from src.builder.sources import moodle
    assert _sequencia_r02(moodle, monkeypatch.setattr) == _R02_ESPERADO
