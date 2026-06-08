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
