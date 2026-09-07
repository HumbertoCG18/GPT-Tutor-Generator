"""EXPERIMENTO (07/09): quanto o POS-PROCESSAMENTO DA APROVACAO muda os numeros do motor. Copia os tutores para `.ablacao/aprovado/`,
aplica nos textos que o motor le o mesmo que o Curator Studio faz ao aprovar UM arquivo (`_clean_extraction_noise` + `_inject_executive_summary`
de artifacts/navigation) onde ainda nao ha sumario, reprocessa com tripwire (0 chamadas) e mede contra os golds: bloco, unidade, subunidade,
fila e erros confiantes — antes x depois, na MESMA base. Nao toca nos tutores originais. Uso: simula_aprovacao.py [--so-medir]"""
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
DST = GEN / ".ablacao/aprovado"
SO_MEDIR = "--so-medir" in sys.argv
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (simula_aprovacao)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from src.builder.artifacts.navigation import _clean_extraction_noise, _inject_executive_summary  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
ORDEM = ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]
IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")


def golds(sig):
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {}
    import csv as _csv
    for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


def mede(root: Path, sig: str) -> Counter:
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]; ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    c = Counter()
    for e in man:
        eid = e["id"]
        erros = []
        if eid in gb:
            c["n_bloco"] += 1
            ok = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
            c["ok_bloco"] += ok
            if not ok:
                erros.append("bloco")
        if eid in gu:
            c["n_unidade"] += 1
            ok = str(e.get("computed_unit_slug") or "") == gu[eid]
            c["ok_unidade"] += ok
            if not ok:
                erros.append("unidade")
        if eid in gs:
            c["n_sub"] += 1
            ok = str(e.get("computed_subunit_slug") or "") in gs[eid]
            c["ok_sub"] += ok
            if not ok:
                erros.append("sub")
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
    if not SO_MEDIR:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(GH / repo, dst, ignore=IGN)
    a = mede(GH / repo, sig)
    ANTES.update(a)
    print(linha("ANTES", sig, a), flush=True)
    if not SO_MEDIR:
        man = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))["entries"]
        n = 0
        for e in man:
            rel = next((e.get(k) for k in ORDEM if e.get(k)), None)
            p = dst / rel if rel else None
            if not p or not p.exists():
                continue
            t = p.read_text(encoding="utf-8", errors="replace")
            if "EXEC_SUMMARY_START" in t:
                continue
            limpo = _clean_extraction_noise(t)
            if limpo != t:
                p.write_text(limpo, encoding="utf-8")
            if _inject_executive_summary(p):
                n += 1
        print(f"         {sig}: pos-processamento aplicado em {n} textos", flush=True)
        ra.reprocess(dst, [])
    d = mede(dst, sig)
    DEPOIS.update(d)
    print(linha("DEPOIS", sig, d), flush=True)
print()
print(linha("ANTES", "TOT", ANTES))
print(linha("DEPOIS", "TOT", DEPOIS))
print(f"[fim] {time.time() - t0:.0f}s · copias em {DST}")
