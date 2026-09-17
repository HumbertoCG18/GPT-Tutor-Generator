"""Roda `_harness-2026-09-02/determinismo.py` (8 tutores, 2 reprocess cada) com o tripwire Gemini de produto: voter so com cache
(`get_gemini_client` -> None), construtor do client explode. Uso: python determinismo_tripwire.py"""
import runpy
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado no determinismo (tripwire)")


_gc.GeminiClient.__init__ = _bloqueado
sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/determinismo.py")]
runpy.run_path(sys.argv[0], run_name="__main__")
