"""Efeito do FILTRO da descricao de imagem no scorer (o markdown fica intacto), pela rota real: copia os 6 cursos com gold,
reprocessa com o gerador atual e mede subunidade/unidade/bloco contra os golds + fila e erros confiantes. Compara com o
produto em disco (que ainda nao tem o filtro). Tripwire: Gemini bloqueado. Uso: mede_filtro_descricao.py"""
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/filtro"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (filtro)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
sys.path.insert(0, str(GEN / "docs/reports/_harness-2026-09-04/c1-3"))
from simula_aprovacao import mede, linha, REPO, IGN  # noqa: E402

DST.mkdir(parents=True, exist_ok=True)
ANTES, DEPOIS = Counter(), Counter()
t0 = time.time()
for sig, repo in REPO.items():
    dst = DST / repo
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(GH / repo, dst, ignore=IGN)
    a = mede(GH / repo, sig)
    ANTES.update(a)
    print(linha("ANTES", sig, a), flush=True)
    ra.reprocess(dst, [])
    d = mede(dst, sig)
    DEPOIS.update(d)
    print(linha("DEPOIS", sig, d), flush=True)
    shutil.rmtree(dst, ignore_errors=True)
print()
print(linha("ANTES", "TOT", ANTES))
print(linha("DEPOIS", "TOT", DEPOIS))
print(f"[fim] {time.time() - t0:.0f}s")
