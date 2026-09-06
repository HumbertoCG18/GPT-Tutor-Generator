"""Regua AUTOMATICA (05/09 tarde, pedido do user: gold so mede; nada de curadoria por curso): motor + voter com CACHE de votos, SEM pinos, SEM
glossario manual, COM vocab compilado por LLM. Copias .ablacao; tripwire (client nulo: cache miss = voto pulado, contado; construtor explode).
Uso: motor_auto.py {puro5|holdout}"""
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
import reprocess_assignments as ra  # noqa: E402
_merge_orig = ra._merge_profile_flags
_reprocess_orig = ra.reprocess


def _reprocess_com_voter(repo, flags, store=None):
    ra._merge_profile_flags = _merge_orig      # desfaz o 'sem voter' do motor_puro/holdout: voter ON (cache)
    return _reprocess_orig(repo, flags, store)


if TARGET == "puro5":
    import motor_puro
    ra.reprocess = _reprocess_com_voter
    sys.exit(motor_puro.main(["--com-vocab"]))
else:
    ra.reprocess = _reprocess_com_voter
    sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
    runpy.run_path(sys.argv[0], run_name="__main__")
