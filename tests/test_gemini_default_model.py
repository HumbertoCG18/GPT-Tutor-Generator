"""Guard do pré-flight FASE 4 (item 0): modelo default vivo e zero refs ao morto."""
from pathlib import Path


def test_default_model_is_pinned_live():
    from src.builder.runtime.gemini_client import DEFAULT_MODEL
    assert DEFAULT_MODEL == "gemini-3.5-flash"


def test_no_dead_gemini_25_reference_in_src():
    root = Path(__file__).resolve().parents[1] / "src"
    hits = sorted(
        str(p) for p in root.rglob("*.py")
        if "gemini-2.5" in p.read_text(encoding="utf-8")
    )
    assert hits == []
