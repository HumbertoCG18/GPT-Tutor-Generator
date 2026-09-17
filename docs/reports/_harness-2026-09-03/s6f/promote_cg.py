"""S6f (f): promove o rebuild do CG (.ablacao/CG-rebuild) a original (Computacao-Grafica-Tutor), em 5 passos.
1. backup: tudo do original (menos .git) -> .ablacao/CG-export-backup/   2. copia o rebuild para o original
3. course/SYNC_REPORT.md (primeira sync = rebuild: todos novos + formulas transcritas)   4. commit no tutor
5. perfil: stash_folder -> Desktop/Moodle/computacao-grafica/stash
Idempotente por passo; nunca imprime chaves. Rode: python promote_cg.py"""
import json
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG = GEN.parent / "Computacao-Grafica-Tutor"
BACKUP = GEN / ".ablacao" / "CG-export-backup"
REB = GEN / ".ablacao" / "CG-rebuild" / "Computacao-Grafica-Tutor"
PULL_ROOT = Path.home() / "Desktop/Moodle/computacao-grafica"
GERADOR = subprocess.run(["git", "-C", str(GEN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

assert (ORIG / ".git").is_dir(), "original sem .git"
assert (REB / "manifest.json").is_file(), "rebuild ausente"
st = subprocess.run(["git", "-C", str(ORIG), "status", "--short"], capture_output=True, text=True).stdout.strip()
assert not st or BACKUP.exists(), f"original com mudancas nao commitadas:\n{st}"

# 1. backup (so se ainda nao foi feito)
if not BACKUP.exists():
    BACKUP.mkdir(parents=True)
    t0 = time.time()
    n = 0
    for p in list(ORIG.iterdir()):
        if p.name != ".git":
            shutil.move(str(p), str(BACKUP / p.name)); n += 1
    print(f"[1] backup: {n} itens -> {BACKUP} ({time.time() - t0:.0f}s)")
else:
    print(f"[1] backup ja existe em {BACKUP}; pulando")

# 2. copia do rebuild
if not (ORIG / "manifest.json").exists():
    t0 = time.time()
    for p in REB.iterdir():
        dst = ORIG / p.name
        shutil.copytree(p, dst) if p.is_dir() else shutil.copy2(p, dst)
    print(f"[2] rebuild copiado para {ORIG} ({time.time() - t0:.0f}s)")
else:
    print("[2] original ja tem manifest.json (copia feita); pulando")

# 3. SYNC_REPORT (primeira sync = rebuild)
from src.builder.sources.moodle_sync import formula_index, render_sync_report, sync_diff  # noqa: E402

contents = json.loads((PULL_ROOT / "raw/moodle/contents.json").read_text(encoding="utf-8"))
man = json.loads((ORIG / "manifest.json").read_text(encoding="utf-8"))
diff = sync_diff([], contents)
dd = {"moved": [], "added": [e["id"] for e in man["entries"]], "removed": []}
report = render_sync_report(diff, dd, when=date.today().isoformat(), curso="Computação Gráfica",
                            ignorados=["ProjecaoPerspectiva.xlsx", "ImpressaoMonocromatica.xlsx"], review=[],
                            plan_counts=f"rebuild limpo pela API: {len(man['entries'])} entries (gerador {GERADOR})",
                            formulas=formula_index(man["entries"], ORIG))
(ORIG / "course" / "SYNC_REPORT.md").write_text(report, encoding="utf-8")
print(f"[3] course/SYNC_REPORT.md: {len(report)} chars, formulas de {sum(1 for e in man['entries'] if e.get('html_images'))} paginas")

# 4. commit no tutor
subprocess.run(["git", "-C", str(ORIG), "add", "-A"], check=True)
msg = (f"rebuild: CG limpo pela API do Moodle (gerador {GERADOR}, campanha SYNC S6f) — {len(man['entries'])} entries "
       "(28 html, 21 pdf, 14 zip, 3 code); paginas do professor e do Moodle como material html, formulas transcritas em "
       "manual-review/formulas; stash novo em Desktop/Moodle/computacao-grafica/stash; holdout puro 30/35, curado 33/35 (aceito com causa)")
r = subprocess.run(["git", "-C", str(ORIG), "commit", "-q", "-m", msg], capture_output=True, text=True)
print("[4] commit:", (r.stdout + r.stderr).strip()[:200] or "ok")
print("    HEAD:", subprocess.run(["git", "-C", str(ORIG), "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip()[:120])

# 5. perfil
from src.models.core import SubjectStore  # noqa: E402

store = SubjectStore()
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "computacao-grafica")
sp.stash_folder = str(PULL_ROOT / "stash")
store.add(sp)
print(f"[5] perfil '{sp.name}': stash_folder -> {sp.stash_folder} | repo_root {sp.repo_root}")
print("[fim]")
