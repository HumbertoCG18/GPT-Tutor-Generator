"""Roda a regua do motor puro (5 cursos, --com-vocab) ou o holdout CG puro com o TRIPWIRE de Gemini (get_gemini_client -> None;
construtor do client explode). Mesma conta dos scripts oficiais, so a protecao a mais. Uso: regua_tripwire.py {puro|holdout}"""
import runpy
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TARGET = sys.argv[1]
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (tripwire)")


_gc.GeminiClient.__init__ = _bloqueado

if TARGET == "puro":
    import motor_puro
    sys.exit(motor_puro.main(["--com-vocab"]))
else:
    sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
    runpy.run_path(sys.argv[0], run_name="__main__")
