"""snapshot.py <nome>: copia manifest.json + course/.timeline_index.json das 6 copias .ablacao para scratchpad/c1-3/<nome>/<repo>/."""
import sys, shutil
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"); SP = Path(__file__).resolve().parent
REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor", "TCC-Tutor", "Computacao-Grafica-Tutor"]
only = sys.argv[2:] or REPOS
for r in only:
    src = GEN / ".ablacao" / r; dst = SP / sys.argv[1] / r
    (dst / "course").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "manifest.json", dst / "manifest.json")
    shutil.copy2(src / "course" / ".timeline_index.json", dst / "course" / ".timeline_index.json")
    if (src / "course" / ".block_identity.json").exists(): shutil.copy2(src / "course" / ".block_identity.json", dst / "course" / ".block_identity.json")
    print("snap", sys.argv[1], r)
