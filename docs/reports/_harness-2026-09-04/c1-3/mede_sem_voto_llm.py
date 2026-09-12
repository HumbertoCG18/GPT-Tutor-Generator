"""Pergunta do user (08/09): "e se fizermos sem esse cache, qual seria o numero?"

96 dos 348 materiais tiveram o BLOCO decidido por voto de LLM (`temporal_block_provider=llm`), e o reprocess com
tripwire reusa o voto em cache em vez de rechamar. Este experimento desliga o voter de verdade (`use_llm_voter=False`,
o mesmo mecanismo de `scripts/motor_puro.py`) para que o cache nunca seja consultado, e mede o que sobra.

Tres regimes, todos com Gemini bloqueado (0 chamadas), nos 6 cursos com gold:
  PRODUTO    como esta em disco hoje (voto em cache + vocabulario + curadoria)
  SEM-VOTO   voter OFF: o bloco tem de sair das camadas deterministicas. Vocabulario e curadoria ficam.
  ZERO-LLM   voter OFF + sem `.glossary_curation*.json` (nem o compilado por LLM, nem o do professor): o numero
             sem nenhuma camada de LLM, nem gasta agora nem gasta no passado.
Uso: mede_sem_voto_llm.py
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
DST = GEN / ".ablacao/semvoto"
REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (mede_sem_voto_llm)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

_orig_merge = ra._merge_profile_flags


def _sem_voter(options, profile):
    """Mesmo mecanismo do scripts/motor_puro.py: o voter nunca e construido, entao o cache nunca e lido."""
    _orig_merge(options, profile)
    options["use_llm_voter"] = False


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
        if str(e.get("temporal_block_provider") or "") in ("llm", "llm-funil"):
            c["prov_llm"] += 1
        if not str(e.get("temporal_block_id") or ""):
            c["sem_bloco"] += 1
        r = revisar_de(e)
        c["fila"] += r in ("duvida", "mudou")
        if err:
            c["cerr"] += r not in ("duvida", "mudou")
        if eid in gb or eid in gu or eid in gs:
            c["cg"] += 1
            c["tc"] += not err
    return c


def linha(tag, sig, c):
    return (f"{tag:9} {sig:4} 100% {c['tc']:3}/{c['cg']:3} | bloco {c['ob']:3}/{c['nb']:3} | unidade {c['ou']:3}/{c['nu']:3} | "
            f"sub {c['os']:3}/{c['ns']:3} | fila {c['fila']:3} | conf-err {c['cerr']:2} | prov-llm {c['prov_llm']:3} | sem-bloco {c['sem_bloco']:2}")


DST.mkdir(parents=True, exist_ok=True)
TOT = {"PRODUTO": Counter(), "SEM-VOTO": Counter(), "ZERO-LLM": Counter()}
t0 = time.time()
for sig, repo in REPO.items():
    a = mede(GH / repo, sig)
    TOT["PRODUTO"].update(a)
    print(linha("PRODUTO", sig, a), flush=True)
    for modo in ("SEM-VOTO", "ZERO-LLM"):
        dst = DST / modo / repo    # o nome do diretorio TEM de ser o do repo (o perfil resolve por ele)
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(GH / repo, dst, ignore=IGN)
        if modo == "ZERO-LLM":
            for nome in (".glossary_curation.json", ".glossary_curation.llm.json"):
                (dst / "course" / nome).unlink(missing_ok=True)
        ra._merge_profile_flags = _sem_voter
        try:
            ra.reprocess(dst, [])
        finally:
            ra._merge_profile_flags = _orig_merge
        c = mede(dst, sig)
        TOT[modo].update(c)
        print(linha(modo, sig, c), flush=True)
        shutil.rmtree(dst, ignore_errors=True)
    print()
print("=" * 128)
for modo in ("PRODUTO", "SEM-VOTO", "ZERO-LLM"):
    print(linha(modo, "TOT", TOT[modo]))
print(f"[fim] {time.time() - t0:.0f}s")
