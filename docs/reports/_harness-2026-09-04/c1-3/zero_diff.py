"""GATE ZERO-DIFF do refactor (07/09). Copia os 8 tutores (COM `staging/`, onde vive o base_markdown de LR/CG/FR/MF — o determinismo.py
antigo ignorava `staging` e reprocessava sem texto), reprocessa UMA vez (tripwire: Gemini bloqueado, voter so com cache, vocab nao recompila)
e tira um snapshot dos artefatos derivados (.md/.json/.yaml fora de build/, raw/, .git; sem BUILD_REPORT.md e STUDENT_STATE.md, que dependem
de build/ e da data; manifest sem updated_at; .block_identity.json sem last_seen).
  --base  : grava o snapshot de referencia em .zerodiff/base/<repo>.json (rodar com o gerador ANTES do refactor)
  --check : reprocessa de novo e compara com a referencia; 0 arquivos = comportamento preservado
Uso: zero_diff.py --base | --check"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
TMP = GEN / ".zerodiff"
MODE = "base" if "--base" in sys.argv else "check"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GEN.parent)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (zero-diff)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402

REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor",
         "TCC-Tutor", "Computacao-Grafica-Tutor", "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor"]
IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak")
VOLATEIS = {"BUILD_REPORT.md", "STUDENT_STATE.md"}
_LAST_SEEN = re.compile(r'"last_seen":\s*"[^"]*"')


def snapshot(repo: Path) -> dict:
    out = {}
    for p in repo.rglob("*"):
        rel = p.relative_to(repo)
        if not p.is_file() or p.suffix not in (".md", ".json", ".yaml", ".yml") or ".bak" in p.name:
            continue
        if rel.parts[0] in ("raw", ".git", "build", "staging") or p.name in VOLATEIS:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if p.name == "manifest.json":
            try:
                d = json.loads(t); d.pop("updated_at", None); t = json.dumps(d, ensure_ascii=False, sort_keys=True)
            except Exception:
                pass
        elif p.name == ".block_identity.json":
            t = _LAST_SEEN.sub('"last_seen": ""', t)
        out[str(rel).replace("\\", "/")] = t
    return out


total = 0
t0 = time.time()
(TMP / "base").mkdir(parents=True, exist_ok=True)
for nome in REPOS:
    dst = TMP / nome
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(GEN.parent / nome, dst, ignore=IGN)
    ra.reprocess(dst, [])
    snap = snapshot(dst)
    ref_p = TMP / "base" / f"{nome}.json"
    if MODE == "base":
        ref_p.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        print(f"== {nome}: referencia gravada ({len(snap)} arquivos)", flush=True)
    else:
        ref = json.loads(ref_p.read_text(encoding="utf-8"))
        mud = sorted(k for k in set(ref) | set(snap) if ref.get(k) != snap.get(k))
        total += len(mud)
        print(f"== {nome}: {len(mud)} arquivo(s) diferem da referencia: {mud[:8]}", flush=True)
        for k in mud:
            if k.endswith("manifest.json"):
                try:
                    da = {e["id"]: e for e in json.loads(ref[k])["entries"]}; db = {e["id"]: e for e in json.loads(snap[k])["entries"]}
                    for eid in da:
                        if eid in db and da[eid] != db[eid]:
                            campos = sorted(c for c in set(da[eid]) | set(db[eid]) if da[eid].get(c) != db[eid].get(c))
                            print(f"     {eid[:36]}: {campos[:8]}")
                except Exception:
                    pass
    shutil.rmtree(dst, ignore_errors=True)
print(f"[{MODE}] TOTAL arquivos diferentes: {total} · {time.time() - t0:.0f}s")
