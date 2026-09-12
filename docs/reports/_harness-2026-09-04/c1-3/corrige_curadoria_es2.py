"""CORRECAO da curadoria do ES2, justificada pelo PROFESSOR (nao pelo gold), medida pela rota real (0 chamadas).

Defeito: `.glossary_curation.json` poe `service discovery`, `name server`, `service registry`, `API gateway`, `gateway`
sob 2.7 "Estudo de Caso: integração e IMPLANTAÇÃO de microsserviços" (unidade 02). Duas evidencias do professor, ambas
independentes do gold:
  1. O ROTULO do proprio professor: 1.5 e "arquitetura orientada a microsserviços", 2.7 e "integração e implantação".
     Service discovery, name server/registry e API gateway sao padroes de ARQUITETURA de microsservicos.
  2. O CRONOGRAMA: 27/03 "microsserviços no Spring introdução" · 10/04 "discovery" · 17/04 "api gateway" · [P1 08/05] ·
     15/05 "circuit breaker" · 22/05 "conteineres" · 05/06 "comunicação assíncrona" · 12/06 "autenticação". Os 5 termos
     sao das aulas ANTES da P1; o resto de 2.7 e depois.
Efeito hoje: o alias faz o bloco-04 casar 2.7 com score 7,656 (todos os outros 0,2) e confianca 1,0 -> o bloco recebe a
unidade 02 -> 6 materiais herdam ("herdada_do_bloco") -> 6 erros de subunidade.

Tambem tira `microsserviço de câmbio` de 2.7: o termo esta em 1.5 E em 2.7 (alias que serve a dois topicos nao discrimina).
Uso: corrige_curadoria_es2.py
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
DST = GEN / ".ablacao/es2cur"
SIG, REPO = "ES2", "Engenharia-Software-2-Tutor"
MOVER = ["service discovery", "name server", "service registry", "API gateway", "gateway"]
TIRAR = ["microsserviço de câmbio"]
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (corrige_curadoria_es2)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")
K27 = "2.7 Estudo de Caso: integração e implantação de microsserviços"
K15 = "1.5 Estudo de caso: arquitetura orientada a microsserviços"


def golds():
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{SIG}.csv")
    gu = _load_truth(SIG)
    gs = {}
    for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{SIG}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


GB, GU, GS = golds()


def mede(root: Path, tag: str) -> Counter:
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]
        ti[b["id"]] = b["id"]
    c = Counter()
    det = []
    for e in man:
        eid, erros = e["id"], []
        if eid in GB:
            c["n_bloco"] += 1
            ok = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == GB[eid]
            c["ok_bloco"] += ok
            erros += [] if ok else ["bloco"]
        if eid in GU:
            c["n_unidade"] += 1
            ok = str(e.get("computed_unit_slug") or "") == GU[eid]
            c["ok_unidade"] += ok
            erros += [] if ok else ["unidade"]
        if eid in GS:
            c["n_sub"] += 1
            ok = str(e.get("computed_subunit_slug") or "") in GS[eid]
            c["ok_sub"] += ok
            erros += [] if ok else ["sub"]
            det.append((eid, str(e.get("computed_unit_slug") or "")[8:20], str(e.get("computed_subunit_slug") or ""), ok))
        r = revisar_de(e)
        c["fila"] += r in ("duvida", "mudou")
        if erros:
            c["confiante_errado"] += r not in ("duvida", "mudou")
        if eid in GB or eid in GU or eid in GS:
            c["com_gold"] += 1
            c["tudo_certo"] += not erros
    c["_det"] = 0
    globals()[f"DET_{tag}"] = {d[0]: d for d in det}
    return c


def linha(tag, c):
    return (f"{tag:9} 100% {c['tudo_certo']:3}/{c['com_gold']:3} | bloco {c['ok_bloco']:3}/{c['n_bloco']:3} | "
            f"unidade {c['ok_unidade']:3}/{c['n_unidade']:3} | sub {c['ok_sub']:3}/{c['n_sub']:3} | fila {c['fila']:3} | conf-err {c['confiante_errado']:2}")


DST.mkdir(parents=True, exist_ok=True)
dst = DST / REPO
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(GH / REPO, dst, ignore=IGN)
cur = dst / "course/.glossary_curation.json"
d = json.loads(cur.read_text(encoding="utf-8"))
d[K27]["synonyms"] = [s for s in d[K27]["synonyms"] if s not in MOVER and s not in TIRAR]
d[K15]["synonyms"] = sorted(set(d[K15]["synonyms"]) | set(MOVER))
d["_nota"] = str(d.get("_nota", "")) + " | 07/09: service discovery/name server/service registry/API gateway/gateway movidos de 2.7 para 1.5 (rotulo do professor: 1.5 e ARQUITETURA, 2.7 e integracao/implantacao; cronograma poe discovery 10/04 e gateway 17/04 antes da P1 de 08/05). 'microsservico de cambio' tirado de 2.7 por estar tambem em 1.5."
cur.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# 2) o PINO do bloco-04 (`.timeline_curation.json`, commit b06b264 de 10/08 "4 pinos gold-backed") forca a unidade 02
# num bloco cujos materiais sao, pelos DOIS golds do user (unidade e subunidade), da unidade 01. Sem tirar o pino, a
# correcao dos sinonimos nao tem efeito: o pino sobrepoe o DP posicional (medido: sub 21/28 -> 21/28).
BLOCO4 = "8a2e86f0-fb4a-4487-86ec-07e74c73d88a"
tc = dst / "course/.timeline_curation.json"
if tc.exists():
    c = json.loads(tc.read_text(encoding="utf-8"))
    if (c.get("blocks") or {}).get(BLOCO4, {}).pop("manual_unit_slug", None):
        if not c["blocks"][BLOCO4]:
            c["blocks"].pop(BLOCO4)
        tc.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
        print("pino do bloco-04 removido")

t0 = time.time()
a = mede(GH / REPO, "ANTES")
print(linha("ANTES", a), flush=True)
ra.reprocess(dst, [])
b = mede(dst, "DEPOIS")
print(linha("CORRIGIDO", b), flush=True)
print("\nmateriais que mudaram de subunidade:")
for eid, d1 in sorted(globals()["DET_ANTES"].items()):
    d2 = globals()["DET_DEPOIS"].get(eid)
    if d2 and d2[2] != d1[2]:
        s = "+" if (d2[3] and not d1[3]) else "-" if (d1[3] and not d2[3]) else "~"
        print(f"  {s} {eid[:34]:34} u {d1[1]:12}->{d2[1]:12}  {d1[2][:34]:34} -> {d2[2][:34]:34} gold={sorted(GS[eid])[0][:34]}")
tl = json.loads((dst / "course/.timeline_index.json").read_text(encoding="utf-8"))
b4 = next((x for x in tl["blocks"] if x["id"] == "bloco-04"), {})
print(f"\nbloco-04 depois: unit={str(b4.get('unit_slug'))[8:30]} conf={b4.get('unit_confidence')} "
      f"topico={str(b4.get('primary_topic_slug'))[:44]} ({b4.get('primary_topic_confidence')})")
print(f"[fim] {time.time() - t0:.0f}s  (copia mantida em {dst})")
