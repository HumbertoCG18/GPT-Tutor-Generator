"""Regressao do read timeout de 60s no submit do Datalab.

O submit (upload do PDF) tinha o mesmo request_timeout=60 dos polls; PDFs
grandes / servidor lento estouravam 'Read timed out (read timeout=60)'. Fix:
submit_timeout generoso e configuravel por env, retry em timeout transiente,
e poll tolerante a timeouts transientes ate o deadline.
"""
import requests

import src.builder.runtime.datalab_client as dc


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _set_key(monkeypatch):
    monkeypatch.setenv("DATALAB_API_KEY", "test-key")


def test_submit_retries_on_read_timeout(tmp_path, monkeypatch):
    _set_key(monkeypatch)
    src = tmp_path / "f.pdf"
    src.write_bytes(b"%PDF-1.4 fake")
    calls = {"post": 0}

    def fake_post(url, **kw):
        calls["post"] += 1
        if calls["post"] == 1:
            raise requests.exceptions.ReadTimeout("boom")
        return _Resp({"request_id": "r1", "request_check_url": "http://check"})

    def fake_get(url, **kw):
        return _Resp({"status": "complete", "markdown": "# ok"})

    monkeypatch.setattr(dc.requests, "post", fake_post)
    monkeypatch.setattr(dc.requests, "get", fake_get)
    monkeypatch.setattr(dc.time, "sleep", lambda *_: None)

    res = dc.convert_document_to_markdown(src, max_retries=2)
    assert res.markdown == "# ok"
    assert calls["post"] == 2  # 1 falha + 1 sucesso


def test_submit_timeout_from_env(tmp_path, monkeypatch):
    _set_key(monkeypatch)
    monkeypatch.setenv("DATALAB_SUBMIT_TIMEOUT", "200")
    src = tmp_path / "f.pdf"
    src.write_bytes(b"x")
    captured = {}

    def fake_post(url, **kw):
        captured["timeout"] = kw.get("timeout")
        return _Resp({"request_id": "r1", "request_check_url": "http://check"})

    def fake_get(url, **kw):
        return _Resp({"status": "complete", "markdown": "ok"})

    monkeypatch.setattr(dc.requests, "post", fake_post)
    monkeypatch.setattr(dc.requests, "get", fake_get)

    dc.convert_document_to_markdown(src)
    to = captured["timeout"]
    read = to[1] if isinstance(to, tuple) else to
    assert read == 200  # submit usa o timeout do env, nao o poll de 60


def test_poll_continues_on_transient_timeout(tmp_path, monkeypatch):
    _set_key(monkeypatch)
    src = tmp_path / "f.pdf"
    src.write_bytes(b"x")

    def fake_post(url, **kw):
        return _Resp({"request_id": "r1", "request_check_url": "http://check"})

    state = {"get": 0}

    def fake_get(url, **kw):
        state["get"] += 1
        if state["get"] == 1:
            raise requests.exceptions.ReadTimeout("transient")
        return _Resp({"status": "complete", "markdown": "ok"})

    monkeypatch.setattr(dc.requests, "post", fake_post)
    monkeypatch.setattr(dc.requests, "get", fake_get)
    monkeypatch.setattr(dc.time, "sleep", lambda *_: None)

    res = dc.convert_document_to_markdown(src, max_retries=2)
    assert res.markdown == "ok"
    assert state["get"] == 2  # 1 timeout transiente + 1 sucesso, sem abortar
