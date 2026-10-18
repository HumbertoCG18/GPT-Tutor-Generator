"""Gemini API key resolution: config (UI) takes precedence, .env/env is fallback.

Mirrors the DATALAB principle (key via env var in .env) but keeps the existing
UI config field working. `.env` is loaded into os.environ at import by
helpers._load_project_env_file, so here we drive os.environ directly.
"""

from src.builder.runtime import gemini_client as gc


class _Cfg:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)


def test_has_key_true_from_config(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gc.has_gemini_api_key(_Cfg({"gemini_api_key": "cfg-key"})) is True


def test_has_key_true_from_env_when_config_empty(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    assert gc.has_gemini_api_key(_Cfg({"gemini_api_key": ""})) is True


def test_has_key_false_when_both_empty(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gc.has_gemini_api_key(_Cfg({"gemini_api_key": ""})) is False


def test_client_prefers_config_over_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    client = gc.get_gemini_client(_Cfg({"gemini_api_key": "cfg-key"}))
    assert client is not None and client.api_key == "cfg-key"


def test_client_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    client = gc.get_gemini_client(_Cfg({"gemini_api_key": ""}))
    assert client is not None and client.api_key == "env-key"


def test_client_none_when_both_empty(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gc.get_gemini_client(_Cfg({"gemini_api_key": ""})) is None
