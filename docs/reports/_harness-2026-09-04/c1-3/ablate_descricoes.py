"""EXPERIMENTO (07/09): quanto o motor depende das DESCRICOES DE IMAGEM do Datalab, que hoje sao injetadas no markdown que ele le.
Copia os tutores para `.ablacao/sem-descricao/`, REMOVE os blocos `<!-- IMAGE_DESCRIPTION ... -->` do texto lido, reprocessa com tripwire
(0 chamadas) e mede contra os golds — antes x depois, na mesma base. Numero honesto para um produto que nao pode depender de API paga.
Nao toca nos tutores originais. Uso: ablate_descricoes.py"""
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/sem-descricao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (ablate_descricoes)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from src.builder.extraction.image_markdown import _IMAGE_DESC_BLOCK_RE, _IMAGE_DESC_ORPHANS_RE  # noqa: E402
sys.path.insert(0, str(GEN / "docs/reports/_harness-2026-09-04/c1-3"))
from simula_aprovacao import mede, linha, REPO, ORDEM, IGN  # noqa: E402

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
    man = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))["entries"]
    n = chars = 0
    for e in man:
        rel = next((e.get(k) for k in ORDEM if e.get(k)), None)
        p = dst / rel if rel else None
        if not p or not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        novo = _IMAGE_DESC_ORPHANS_RE.sub("\n", _IMAGE_DESC_BLOCK_RE.sub("", t))
        if novo != t:
            p.write_text(novo, encoding="utf-8"); n += 1; chars += len(t) - len(novo)
    print(f"         {sig}: descricoes removidas de {n} textos ({chars} chars)", flush=True)
    ra.reprocess(dst, [])
    d = mede(dst, sig)
    DEPOIS.update(d)
    print(linha("DEPOIS", sig, d), flush=True)
print()
print(linha("ANTES", "TOT", ANTES))
print(linha("DEPOIS", "TOT", DEPOIS))
print(f"[fim] {time.time() - t0:.0f}s · copias em {DST}")
