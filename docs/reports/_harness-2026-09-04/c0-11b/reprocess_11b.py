"""C0 11b — reprocess REGISTRADO dos 8 originais com o gerador commitado (regra `exclusivo` exige 2+ tokens).
Por tutor: manifest.json.bak (feito pelo reprocess) -> reprocess (voter cacheado; flags novas podem votar) -> diff
flag/bloco/metodo -> commit no tutor "reprocess: ... (gerador <hash>, C0 11a)". Nunca imprime chaves.
Uso: python reprocess_11a.py [--dry-run]   (dry-run: so lista o estado, nao reprocessa nem commita)"""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import reprocess_assignments as ra  # noqa: E402

DRY = "--dry-run" in sys.argv
TUTORES = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor",
           "TCC-Tutor", "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor", "Computacao-Grafica-Tutor"]
GER = subprocess.run(["git", "-C", str(GEN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(GEN), "status", "--short", "--", "src", "tests"], capture_output=True, text=True).stdout.strip()
assert not dirty, f"gerador com src/tests nao commitados:\n{dirty}"


def snap(repo: Path) -> dict:
    es = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    return {e["id"]: (bool(e.get("temporal_block_flag")), str(e.get("temporal_block_ref") or e.get("temporal_block_id") or ""),
                      str(e.get("temporal_block_method") or "")) for e in es}


tot = Counter()
for name in TUTORES:
    repo = GH / name
    st = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout.strip()
    before = snap(repo)
    print(f"== {name}: {len(before)} entries | flagadas {sum(1 for v in before.values() if v[0])} | git sujo: {st.count(chr(10)) + 1 if st else 0}")
    if DRY:
        continue
    ra.reprocess(repo, [])
    after = snap(repo)
    fl_b = sum(1 for v in before.values() if v[0]); fl_a = sum(1 for v in after.values() if v[0])
    moved = [k for k in before if k in after and before[k][1] != after[k][1]]
    meth = Counter(f"{before[k][2]}->{after[k][2]}" for k in before if k in after and before[k][2] != after[k][2])
    print(f"   flagadas {fl_b} -> {fl_a} ({fl_a - fl_b:+d}) | bloco mudou {len(moved)} {moved[:6]} | metodo mudou {dict(meth)}")
    tot["fl_b"] += fl_b; tot["fl_a"] += fl_a; tot["moved"] += len(moved)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    msg = (f"reprocess: CRONOGRAMA_HEALTH conta votos de LLM e flagados por 100 (gerador {GER}, C0 11b) — "
           f"flagadas {fl_b} -> {fl_a}, bloco mudou em {len(moved)}")
    r = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print("   commit:", "nada a commitar" if "nothing to commit" in out else (out[:100] or "ok"),
          "| HEAD", subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip())
if not DRY:
    print(f"TOTAL 8 tutores: flagadas {tot['fl_b']} -> {tot['fl_a']} ({tot['fl_a'] - tot['fl_b']:+d}) | blocos mudados {tot['moved']}")
print("[fim]")
