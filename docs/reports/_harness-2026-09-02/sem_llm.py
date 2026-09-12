"""Experimento READ-ONLY nos originais: reprocessa as COPIAS (.ablacao) com
use_llm_voter=False e mede quanto o motor sozinho acerta onde hoje o LLM decide.

    python sem_llm.py            # reprocessa MF,SO,IA,ES2,TCC nas copias + eval

Copias em GEN/.ablacao (sincronizadas pelo ablacao_rapida; gate curado == original).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
ORIG = GEN.parent
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
os.environ["TUTOR_REPOS_ORIG"] = str(ORIG)

import reprocess_assignments as ra  # noqa: E402

REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor",
         "Engenharia-Software-2-Tutor", "TCC-Tutor"]

# monkeypatch: depois do merge de flags do perfil, desliga o voter
_orig_merge = ra._merge_profile_flags


def _merge_sem_voter(options, profile):
    _orig_merge(options, profile)
    options["use_llm_voter"] = False


ra._merge_profile_flags = _merge_sem_voter

for nome in REPOS:
    repo = COPY / nome
    if not (repo / "manifest.json").exists():
        print(f"[skip] copia ausente: {repo}")
        continue
    ra.reprocess(repo, [])

env = {**os.environ, "TUTOR_REPOS_DIR": str(COPY), "PYTHONIOENCODING": "utf-8"}
out = subprocess.run([sys.executable, str(GEN / "scripts/eval_eixos.py")], cwd=str(GEN), env=env,
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
print("\n=== EVAL nas copias SEM voter ===")
print(out.stdout[-1500:])

# diff bloco a bloco vs original, nos entries que hoje sao 'llm'/'llm-funil'
print("\n=== onde o motor sozinho diverge do LLM (original) ===")
for nome in REPOS:
    mo = json.loads((ORIG / nome / "manifest.json").read_text(encoding="utf-8"))
    mc = json.loads((COPY / nome / "manifest.json").read_text(encoding="utf-8"))
    co = {str(e.get("id")): e for e in mc["entries"]}
    n_llm = n_same = n_diff = n_vazio = 0
    for e in mo["entries"]:
        if str(e.get("temporal_block_method") or "") not in ("llm", "llm-funil"):
            continue
        n_llm += 1
        c = co.get(str(e.get("id")), {})
        bo, bc = str(e.get("temporal_block_id") or ""), str(c.get("temporal_block_id") or "")
        if not bc:
            n_vazio += 1
        elif bo == bc:
            n_same += 1
        else:
            n_diff += 1
    print(f"  {nome[:28]:30} llm-hoje={n_llm:>3}  motor-igual={n_same:>3}  motor-diverge={n_diff:>3}  motor-vazio={n_vazio:>3}")
