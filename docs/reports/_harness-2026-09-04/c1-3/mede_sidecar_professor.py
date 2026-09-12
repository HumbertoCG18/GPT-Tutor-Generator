"""Mede pela ROTA REAL o sidecar gerado so de fontes do professor (`gera_sidecar_professor.py`), contra as duas bases:
  ATUAL   o produto em disco, com o sidecar "proposto-claude a partir de subunit_gt" (contaminado)
  LIMPO   sem sidecar nenhum
  PROF    com o sidecar gerado de SARC + secao do Moodle + headings dos materiais da secao
Tripwire: Gemini bloqueado. 6 cursos com gold. Uso: mede_sidecar_professor.py
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
DST = GEN / ".ablacao/sidecar"
REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.path.insert(0, str(GEN / "docs/reports/_harness-2026-09-04/c1-3"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (mede_sidecar_professor)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from gera_sidecar_professor import gera  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")


def golds(sig):
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {r["entry_id"]: ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
          for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"}
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
        eid, err = e["id"], []
        if eid in gb:
            c["nb"] += 1
            ok = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
            c["ob"] += ok
            err += [] if ok else ["b"]
        if eid in gu:
            c["nu"] += 1
            ok = str(e.get("computed_unit_slug") or "") == gu[eid]
            c["ou"] += ok
            err += [] if ok else ["u"]
        if eid in gs:
            c["ns"] += 1
            ok = str(e.get("computed_subunit_slug") or "") in gs[eid]
            c["os"] += ok
            err += [] if ok else ["s"]
        r = revisar_de(e)
        c["fila"] += r in ("duvida", "mudou")
        if err:
            c["cerr"] += r not in ("duvida", "mudou")
        if eid in gb or eid in gu or eid in gs:
            c["cg"] += 1
            c["tc"] += not err
    return c


def linha(tag, sig, c):
    return (f"{tag:7} {sig:4} 100% {c['tc']:3}/{c['cg']:3} | bloco {c['ob']:3}/{c['nb']:3} | unidade {c['ou']:3}/{c['nu']:3} | "
            f"sub {c['os']:3}/{c['ns']:3} | fila {c['fila']:3} | conf-err {c['cerr']:2}")


DST.mkdir(parents=True, exist_ok=True)
TOT = {"ATUAL": Counter(), "LIMPO": Counter(), "PROF": Counter()}
t0 = time.time()
for sig, repo in REPO.items():
    a = mede(GH / repo, sig)
    TOT["ATUAL"].update(a)
    print(linha("ATUAL", sig, a), flush=True)
    for modo in ("LIMPO", "PROF"):
        dst = DST / modo / repo   # o nome do diretorio TEM de ser o do repo: o perfil da materia resolve por ele
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(GH / repo, dst, ignore=IGN)
        p = dst / "course/.glossary_curation.json"
        if modo == "LIMPO":
            p.unlink(missing_ok=True)
        else:
            out, _ = gera(dst)
            p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        ra.reprocess(dst, [])
        c = mede(dst, sig)
        TOT[modo].update(c)
        print(linha(modo, sig, c), flush=True)
        shutil.rmtree(dst, ignore_errors=True)
    print()
print("=" * 108)
for modo in ("ATUAL", "LIMPO", "PROF"):
    print(linha(modo, "TOT", TOT[modo]))
print(f"[fim] {time.time() - t0:.0f}s")
