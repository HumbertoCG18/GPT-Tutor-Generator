from src.builder.sources.m365 import (
    parse_onedrive_path, subfolder_for, select_for_subject,
)

_BASE = "https://brpucrs-my.sharepoint.com/personal/10070245_pucrs_br/Documents/Documentos"

def test_parse_onedrive_path_segments():
    segs = parse_onedrive_path(f"{_BASE}/metodosformais/dafny/hoare.zip")
    assert segs[-3:] == ["metodosformais", "dafny", "hoare.zip"]

def test_subfolder_for_uses_immediate_subfolder():
    assert subfolder_for(f"{_BASE}/metodosformais/dafny/hoare.zip", "metodosformais") == "dafny"
    assert subfolder_for(f"{_BASE}/metodosformais/logica_programas/Hoare.pdf", "metodosformais") == "logica_programas"

def test_subfolder_for_root_file_is_default():
    assert subfolder_for(f"{_BASE}/metodosformais/plano.pdf", "metodosformais") == "_geral"

def test_select_for_subject_filters_by_substring():
    items = [
        {"web_url": f"{_BASE}/metodosformais/dafny/a.pdf"},
        {"web_url": f"{_BASE}/engenhariadesoftware2/b.pdf"},
        {"web_url": "https://outlook.office.com/owa/?x=AttachmentId"},
    ]
    out = select_for_subject(items, "metodosformais")
    assert len(out) == 1 and "dafny" in out[0]["web_url"]

def test_select_for_subject_empty_filter_returns_nothing():
    assert select_for_subject([{"web_url": "x"}], "") == []

from src.builder.sources.m365 import match_card

_SECTIONS = ["Introdução a Métodos Formais", "Provas por Indução",
             "Verificação de Programas", "Plano de Ensino"]

def test_match_card_matches_by_normalized_tokens():
    assert match_card("introducao", _SECTIONS) == ("Introdução a Métodos Formais", True)
    assert match_card("correcao_provasinducao", _SECTIONS)[1] is True
    assert match_card("logica_programas", _SECTIONS) == ("Verificação de Programas", True)

def test_match_card_falls_back_to_new_card_when_no_match():
    card, matched = match_card("dafny", _SECTIONS)
    assert matched is False and card == "dafny"

from src.builder.sources import m365 as m365mod

class _Resp:
    def __init__(self, status=200, payload=None, content=b""):
        self.status_code = status; self._p = payload or {}; self.content = content; self.text = str(payload)
    def json(self): return self._p
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(f"http {self.status_code}")

def test_list_shared_follows_pagination(monkeypatch):
    pages = {
        "https://graph.microsoft.com/v1.0/me/insights/shared?$top=200": _Resp(payload={
            "value": [{"id": "1", "resourceVisualization": {"title": "a.pdf", "type": "Pdf"},
                       "resourceReference": {"webUrl": "u/a"}}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/insights/shared?$skip=1"}),
        "https://graph.microsoft.com/v1.0/me/insights/shared?$skip=1": _Resp(payload={
            "value": [{"id": "2", "resourceVisualization": {"title": "b.pdf", "type": "Pdf"},
                       "resourceReference": {"webUrl": "u/b"}}]}),
    }
    monkeypatch.setattr(m365mod.requests, "get", lambda url, headers=None, timeout=0: pages[url])
    c = m365mod.M365Client("tok")
    items = c.list_shared(top=200)
    assert [it["id"] for it in items] == ["1", "2"]
    assert items[0]["title"] == "a.pdf" and items[0]["web_url"] == "u/a"

def test_resolve_and_download_via_downloadurl(monkeypatch):
    calls = {}
    def fake_get(url, headers=None, timeout=0):
        if "/resource" in url:
            return _Resp(payload={"name": "x.pdf", "id": "I", "file": {},
                                  "@microsoft.graph.downloadUrl": "https://dl/x"})
        if url == "https://dl/x":
            calls["dl"] = True
            return _Resp(content=b"%PDF-1.7 ok")
        raise AssertionError(url)
    monkeypatch.setattr(m365mod.requests, "get", fake_get)
    c = m365mod.M365Client("tok")
    res = c.resolve("INS")
    data = c.download(res)
    assert res["name"] == "x.pdf" and data[:4] == b"%PDF" and calls["dl"]

def test_device_login_polls_until_token(monkeypatch, tmp_path):
    monkeypatch.setattr(m365mod, "_token_path", lambda: tmp_path / ".m365_token.json")
    monkeypatch.setattr(m365mod.time, "sleep", lambda s: None)
    seq = [
        _Resp(payload={"verification_uri": "https://aka.ms/dev", "user_code": "ABC",
                       "device_code": "DC", "interval": 1, "expires_in": 900}),
    ]
    posts = [
        _Resp(payload={"error": "authorization_pending"}),
        _Resp(payload={"access_token": "AT", "refresh_token": "RT"}),
    ]
    monkeypatch.setattr(m365mod.requests, "post",
                        lambda url, data=None, timeout=0: seq.pop(0) if "devicecode" in url else posts.pop(0))
    shown = {}
    tok = m365mod.device_login(prompt_callback=lambda m: shown.update(m))
    assert tok == "AT"
    assert shown["user_code"] == "ABC"
    saved = (tmp_path / ".m365_token.json").read_text(encoding="utf-8")
    assert "RT" in saved

def test_load_cached_token_refreshes(monkeypatch, tmp_path):
    p = tmp_path / ".m365_token.json"
    p.write_text('{"refresh_token": "RT"}', encoding="utf-8")
    monkeypatch.setattr(m365mod, "_token_path", lambda: p)
    monkeypatch.setattr(m365mod.requests, "post",
                        lambda url, data=None, timeout=0: _Resp(payload={"access_token": "NEW", "refresh_token": "RT2"}))
    assert m365mod.load_cached_token() == "NEW"
    assert "RT2" in p.read_text(encoding="utf-8")

import json as _json

def test_apply_source_section_writes_manifest(tmp_path):
    from src.builder.sources.m365 import apply_source_section
    repo = tmp_path / "repo"; repo.mkdir()
    (repo / "manifest.json").write_text(_json.dumps({"entries": [
        {"id": "1", "source_path": "C:/x/Hoare.pdf"},
        {"id": "2", "source_path": "C:/x/outro.pdf"},
    ]}), encoding="utf-8")
    n = apply_source_section(str(repo), {"hoare.pdf": "Verificação de Programas"})
    assert n == 1
    m = _json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in m["entries"]}
    assert by_id["1"]["source_section"] == "Verificação de Programas"
    assert "source_section" not in by_id["2"]
    assert (repo / "manifest.json.apibak").is_file()

def test_apply_source_section_noop_without_manifest(tmp_path):
    from src.builder.sources.m365 import apply_source_section
    assert apply_source_section(str(tmp_path / "nada"), {"a.pdf": "X"}) == 0

def test_download_subject_m365_merges_cards_and_validates(tmp_path):
    from src.builder.sources.m365 import download_subject_m365
    base = "https://brpucrs-my.sharepoint.com/personal/p/Documents/Documentos/metodosformais"

    class FakeClient:
        def list_shared(self, top=200):
            return [
                {"id": "1", "title": "Hoare.pdf", "type": "Pdf", "web_url": f"{base}/logica_programas/Hoare.pdf"},
                {"id": "2", "title": "hoare.zip", "type": "Archive", "web_url": f"{base}/dafny/hoare.zip"},
                {"id": "3", "title": "ruim.pdf", "type": "Pdf", "web_url": f"{base}/dafny/ruim.pdf"},
                {"id": "9", "title": "outro.pdf", "type": "Pdf", "web_url": "https://x/engsoft/outro.pdf"},
            ]
        def resolve(self, iid):
            return {"name": {"1": "Hoare.pdf", "2": "hoare.zip", "3": "ruim.pdf"}[iid],
                    "id": iid, "parentReference": {"driveId": "D"}}
        def download(self, item):
            return {"Hoare.pdf": b"%PDF-1.7 ok", "hoare.zip": b"PK\x03\x04zip",
                    "ruim.pdf": b'{"error":"x"}'}[item["name"]]

    sections = ["Verificação de Programas", "Provas por Indução"]
    rep = download_subject_m365(FakeClient(), "metodosformais", sections, tmp_path)

    assert rep["downloaded"] == 2
    assert "ruim.pdf" in rep["failed"]                          # magic byte errado
    # logica_programas casa com "Verificação de Programas" (token 'programas')
    assert (tmp_path / "Verificação de Programas" / "Hoare.pdf").exists()
    # dafny não casa -> card novo
    assert (tmp_path / "dafny" / "hoare.zip").exists()
    # item de outro curso ignorado pelo filtro
    assert not any("outro" in str(p) for p in tmp_path.rglob("*"))
    assert rep["name_to_section"]["hoare.pdf"] == "Verificação de Programas"

def test_download_subject_m365_no_collision_loss(tmp_path):
    from src.builder.sources.m365 import download_subject_m365
    base = "https://x/Documents/Documentos/metodosformais/dafny"

    class FakeClient:
        def list_shared(self, top=200):
            return [{"id": "1", "title": "main.pdf", "type": "Pdf", "web_url": f"{base}/main.pdf"},
                    {"id": "2", "title": "main.pdf", "type": "Pdf", "web_url": f"{base}/sub/main.pdf"}]
        def resolve(self, iid):
            return {"name": "main.pdf", "id": iid, "parentReference": {"driveId": "D"}}
        def download(self, item):
            return b"%PDF-1.7 x"
    rep = download_subject_m365(FakeClient(), "metodosformais", [], tmp_path)
    assert rep["downloaded"] == 2                              # nenhum perdido
    assert (tmp_path / "dafny" / "main.pdf").exists()
    assert (tmp_path / "dafny" / "main (2).pdf").exists()
    # FIX 3: both the original and renamed file must be tracked in name_to_section
    assert "main.pdf" in rep["name_to_section"]
    assert "main (2).pdf" in rep["name_to_section"]
    assert rep["name_to_section"]["main.pdf"] == rep["name_to_section"]["main (2).pdf"]


def test_download_via_downloadurl_raises_on_http_error(monkeypatch):
    """FIX 1: download() must call raise_for_status() on the direct-download branch."""
    def fake_get(url, headers=None, timeout=0):
        if url == "https://dl/bad":
            return _Resp(status=403, content=b"")
        raise AssertionError(url)
    monkeypatch.setattr(m365mod.requests, "get", fake_get)
    c = m365mod.M365Client("tok")
    item = {"@microsoft.graph.downloadUrl": "https://dl/bad"}
    try:
        c.download(item)
        assert False, "should have raised"
    except RuntimeError:
        pass


def test_load_cached_token_returns_none_on_corrupt_file(monkeypatch, tmp_path):
    """FIX 2: corrupt token file must return None instead of crashing."""
    p = tmp_path / ".m365_token.json"
    p.write_text("not json{", encoding="utf-8")
    monkeypatch.setattr(m365mod, "_token_path", lambda: p)
    assert m365mod.load_cached_token() is None


def test_download_subject_m365_sanitizes_invalid_card_and_filename(tmp_path):
    """Regressão WinError 123: card (seção Moodle casada) ou nome de arquivo com
    chars inválidos no Windows não podem quebrar o mkdir/write."""
    from src.builder.sources.m365 import download_subject_m365
    base = "https://x/Documents/Documentos/metodosformais/logica_programas"

    class FakeClient:
        def list_shared(self, top=200):
            return [{"id": "1", "title": "Hoare", "type": "Pdf",
                     "web_url": f"{base}/Hoare.pdf"}]
        def resolve(self, iid):
            # nome com char inválido (':') que precisa ser sanitizado
            return {"name": "Logica: Hoare.pdf", "id": iid, "parentReference": {"driveId": "D"}}
        def download(self, item):
            return b"%PDF-1.7 ok"

    # seção Moodle com chars inválidos de path ('/', ':') que casa com logica_programas
    sections = ["Lógica: Programas/Hoare"]
    rep = download_subject_m365(FakeClient(), "metodosformais", sections, tmp_path)
    assert rep["downloaded"] == 1
    # pasta sanitizada existe e o arquivo foi gravado (sem WinError)
    written = list(tmp_path.rglob("*.pdf"))
    assert len(written) == 1
    rel = written[0].relative_to(tmp_path)
    assert ":" not in str(rel)                 # nenhum char inválido no caminho relativo
    assert all(part not in ("", ".", "..") for part in rel.parts)
