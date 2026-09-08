"""CIRCULARIDADE: 4 dos 6 cursos com gold tem `course/.glossary_curation.json` marcado "Proposto-claude a partir de
subunit_gt_<curso>" (SO, IA, ES2, TCC; 25/08 e 26/08). Esses sinonimos viram ALIAS da taxonomia e sao o sinal de maior
peso da subunidade — e o motor e medido contra o MESMO gold que os originou. SO, IA e TCC estao em 100%.

Este experimento tira a curadoria e reprocessa pela rota real (tripwire, 0 chamadas), para separar o que o motor acerta
sozinho do que ele acerta porque a resposta foi plantada no vocabulario.
Uso: ablate_curadoria_gold.py
"""
import csv as _csv
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/curadoria"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (ablate_curadoria_gold)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

# so os cursos cuja curadoria e derivada do gold
REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")


def golds(sig):
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {}
    for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


def mede(root: Path, sig: str) -> Counter:
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]
        ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    c = Counter()
    for e in man:
        eid, erros = e["id"], []
        if eid in gb:
            c["n_bloco"] += 1
            ok = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
            c["ok_bloco"] += ok
            erros += [] if ok else ["bloco"]
        if eid in gu:
            c["n_unidade"] += 1
            ok = str(e.get("computed_unit_slug") or "") == gu[eid]
            c["ok_unidade"] += ok
            erros += [] if ok else ["unidade"]
        if eid in gs:
            c["n_sub"] += 1
            ok = str(e.get("computed_subunit_slug") or "") in gs[eid]
            c["ok_sub"] += ok
            erros += [] if ok else ["sub"]
        r = revisar_de(e)
        c["fila"] += r in ("duvida", "mudou")
        if erros:
            c["confiante_errado"] += r not in ("duvida", "mudou")
        if eid in gb or eid in gu or eid in gs:
            c["com_gold"] += 1
            c["tudo_certo"] += not erros
    return c


def linha(tag, sig, c):
    return (f"{tag:8} {sig:4} 100% {c['tudo_certo']:3}/{c['com_gold']:3} | bloco {c['ok_bloco']:3}/{c['n_bloco']:3} | "
            f"unidade {c['ok_unidade']:3}/{c['n_unidade']:3} | sub {c['ok_sub']:3}/{c['n_sub']:3} | fila {c['fila']:3} | conf-err {c['confiante_errado']:2}")


DST.mkdir(parents=True, exist_ok=True)
ANTES, DEPOIS = Counter(), Counter()
t0 = time.time()
for sig, repo in REPO.items():
    dst = DST / repo
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(GH / repo, dst, ignore=IGN)
    cur = dst / "course/.glossary_curation.json"
    n = 0
    if cur.exists():
        d = json.loads(cur.read_text(encoding="utf-8"))
        n = len([k for k in d if not k.startswith("_")])
        cur.unlink()
    a = mede(GH / repo, sig)
    ANTES.update(a)
    print(linha("ANTES", sig, a), flush=True)
    ra.reprocess(dst, [])
    d = mede(dst, sig)
    DEPOIS.update(d)
    print(linha(f"SEM-CUR", sig, d) + f"   (removidos {n} termos curados)", flush=True)
    shutil.rmtree(dst, ignore_errors=True)
print()
print(linha("ANTES", "TOT", ANTES))
print(linha("SEM-CUR", "TOT", DEPOIS))
print(f"[fim] {time.time() - t0:.0f}s")
