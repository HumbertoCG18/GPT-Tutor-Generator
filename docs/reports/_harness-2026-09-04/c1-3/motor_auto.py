"""Regua AUTOMATICA (05/09 tarde, pedido do user: gold so mede; nada de curadoria por curso): motor + voter com CACHE de votos DO PRODUTO,
SEM pinos, SEM glossario manual, COM vocab compilado por LLM (tambem no holdout CG, que por definicao do puro roda sem vocab). Copias
.ablacao; tripwire (client nulo: cache miss = voto pulado, contado; construtor explode). O cache de votos do produto e copiado para a copia
antes do reprocess (a copia acumulava votos antigos: CG 2/42 diferentes). Uso: motor_auto.py {puro5|holdout}"""
import runpy
import shutil
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TARGET = sys.argv[1]
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (tripwire)")


_gc.GeminiClient.__init__ = _bloqueado
import ablacao_rapida as ab  # noqa: E402
import reprocess_assignments as ra  # noqa: E402
_merge_orig = ra._merge_profile_flags
_reprocess_orig = ra.reprocess
_ablate_orig = ab.ablate


def _ablate_com_vocab(repo, keep_llm_vocab=False):
    n = _ablate_orig(repo, keep_llm_vocab=True)            # vocab compilado FICA (faz parte do automatico)
    src = GH / Path(repo).name / "material_curation.json"   # cache de votos = o do PRODUTO
    if src.exists():
        shutil.copy2(src, Path(repo) / "material_curation.json")
    return n


def _reprocess_com_voter(repo, flags, store=None):
    ra._merge_profile_flags = _merge_orig      # desfaz o 'sem voter' do motor_puro/holdout: voter ON (cache)
    return _reprocess_orig(repo, flags, store)


ab.ablate = _ablate_com_vocab
ra.reprocess = _reprocess_com_voter
if TARGET == "puro5":
    import motor_puro
    sys.exit(motor_puro.main(["--com-vocab"]))
else:
    sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
    runpy.run_path(sys.argv[0], run_name="__main__")
