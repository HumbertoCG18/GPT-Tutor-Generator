"""Guard do pré-flight FASE 4 (item 0): modelo default vivo e zero refs ao morto."""
from pathlib import Path


def test_default_model_is_pinned_live():
    from src.builder.runtime.gemini_client import DEFAULT_MODEL
    assert DEFAULT_MODEL == "gemini-3.5-flash"


def test_no_dead_gemini_25_reference_in_src():
    root = Path(__file__).resolve().parents[1] / "src"
    # gemini_client.py pode referenciar gemini-2.5 no RETIRED_MODELS guard
    hits = sorted(
        str(p) for p in root.rglob("*.py")
        if p.name != "gemini_client.py" and "gemini-2.5" in p.read_text(encoding="utf-8")
    )
    assert hits == []


def test_retired_model_in_config_resolves_to_default(monkeypatch):
    """Config persistido antigo com modelo aposentado não pode vazar pro client."""
    import src.builder.runtime.gemini_client as gc

    captured = {}

    class _FakeClient:
        def __init__(self, api_key, model):
            captured["model"] = model

    monkeypatch.setattr(gc, "GeminiClient", _FakeClient)
    gc.get_gemini_client({"gemini_api_key": "k", "gemini_model": "gemini-2.5-flash"})
    assert captured["model"] == gc.DEFAULT_MODEL


def test_retired_model_remap_logs_info(monkeypatch, caplog):
    """review F4 T1a: remap silencioso de modelo aposentado -> logger.info p/ auditoria."""
    import src.builder.runtime.gemini_client as gc

    class _FakeClient:
        def __init__(self, api_key, model):
            pass

    monkeypatch.setattr(gc, "GeminiClient", _FakeClient)
    with caplog.at_level("INFO", logger="src.builder.runtime.gemini_client"):
        gc.get_gemini_client({"gemini_api_key": "k", "gemini_model": "gemini-2.5-flash"})
    assert any(
        "gemini-2.5-flash" in r.message and gc.DEFAULT_MODEL in r.message
        for r in caplog.records
    )
