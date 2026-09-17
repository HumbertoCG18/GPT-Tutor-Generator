"""FR sem gold, regime intermediario (12/09): a run A (motor puro, 0 chamadas) + o vocabulario LLM do FR que ja esta em cache no
produto (`course/.glossary_curation.llm.json`, compilado em 11/09), reprocessado SEM voter e sem compilar nada (0 chamadas ao vivo).
Isola quanto da subunidade do FR vem do vocab: run A 7/18 x produto 18/18. Copia o sandbox da run A para FR-rebuild-A-vocab.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/fr_puro_com_vocab.py"""
import collections
import os
import shutil
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder.runtime import gemini_client  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

SRC = GEN / ".ablacao" / "FR-rebuild" / "Fundamentos-de-Redes-Tutor"
DST = GEN / ".ablacao" / "FR-rebuild-A-vocab" / "Fundamentos-de-Redes-Tutor"
PROD = GH / "Fundamentos-de-Redes-Tutor"
calls = collections.Counter()


def _bloqueado(*a, **k):
    calls["gemini_bloqueado"] += 1
    raise RuntimeError("Gemini bloqueado (tripwire)")


gemini_client.get_gemini_client = lambda config=None: None
gemini_client.GeminiClient.__init__ = _bloqueado
_orig_merge = ra._merge_profile_flags


def _sem_voter(options, profile):
    _orig_merge(options, profile)
    options["use_llm_voter"] = False


ra._merge_profile_flags = _sem_voter

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
shutil.copy(PROD / "course" / ".glossary_curation.llm.json", DST / "course" / ".glossary_curation.llm.json")
print(f"[copia] {SRC.name} -> {DST.parent.name}; vocab LLM do produto copiado ({(DST / 'course' / '.glossary_curation.llm.json').stat().st_size} bytes)")
# O sandbox nao esta no subjects.json: sem perfil, o plano parseia 0 unidades e o guard 'unidade nunca encolhe' aborta.
# Forca o perfil real do FR para qualquer raiz (mesmo truque do rebuild_fr.py, que passa subject_profile=sp ao builder).
from src.models.core import SubjectStore  # noqa: E402
store = SubjectStore()
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "fundamentos-de-redes-de-computadores")
store.find_by_repo_root = lambda root: sp
t0 = time.time()
ra.reprocess(DST, [], store=store)
print(f"[reprocess] {time.time() - t0:.0f}s · chamadas Gemini bloqueadas: {dict(calls) or 0}")
