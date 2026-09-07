"""Grade do PISO DE FORCA da 1a passada, pela rota REAL do motor: copia os 6 cursos com gold, reprocessa com cada piso
(env TUTOR_SUBUNIT_FORCE_FLOOR) e mede a subunidade contra os golds. Tripwire: Gemini bloqueado. Uso: mede_piso_grade.py"""
import csv
import json
import os
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/piso"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (grade do piso)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")
PISOS = ["0", "0.5", "1.0", "1.5", "3.0"]


def golds(sig):
    g = {}
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            g[r["entry_id"]] = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
    return g


def mede(root, sig):
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    g = golds(sig)
    ok = sum(1 for k, aceitos in g.items() if k in man and str(man[k].get("computed_subunit_slug") or "") in aceitos)
    return ok, len(g)


t0 = time.time()
DST.mkdir(parents=True, exist_ok=True)
for piso in PISOS:
    os.environ["TUTOR_SUBUNIT_FORCE_FLOOR"] = piso
    tot_ok = tot_n = 0
    partes = []
    for sig, repo in REPO.items():
        dst = DST / repo
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(GH / repo, dst, ignore=IGN)
        ra.reprocess(dst, [])
        ok, n = mede(dst, sig)
        partes.append(f"{sig} {ok}/{n}")
        tot_ok += ok; tot_n += n
        shutil.rmtree(dst, ignore_errors=True)
    print(f"piso {piso:>4}: subunidade {tot_ok}/{tot_n} · " + " · ".join(partes), flush=True)
print(f"[fim] {time.time() - t0:.0f}s")
