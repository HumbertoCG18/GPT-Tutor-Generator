"""Experimento (read-only nos originais): copia o repo do IA para uma pasta temporaria, reprocessa com o clamp
do FILE_MAP DESLIGADO (monkeypatch), e roda a regua de travessia contra a copia. Mede se a perda de precisao
e o corte de 12 KB, nao o LLM."""
import os, shutil, subprocess, sys
from pathlib import Path

GEN = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
TMP = Path("C:/Users/Humberto/.claude/jobs/ea3da64b/tmp/semclamp")
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
os.environ["TUTOR_REPOS_ORIG"] = str(GEN.parent)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"

SIG, NOME = sys.argv[1], {"IA": "Inteligencia-Artifical-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}[sys.argv[1]]
src, dst = GEN.parent / NOME, TMP / NOME
if dst.exists():
    shutil.rmtree(dst)
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak"))

from src.builder.artifacts import navigation  # noqa: E402
import src.builder.engine as engine  # noqa: E402

_orig = navigation.clamp_navigation_artifact if hasattr(navigation, "clamp_navigation_artifact") else None


def no_clamp(text, max_chars=0, label=""):
    return text


# o clamp e injetado por partial no engine; patch nos dois lugares que o carregam
for mod in (navigation, engine):
    for name in dir(mod):
        if "clamp_navigation_artifact" in name:
            setattr(mod, name, no_clamp)
import functools  # noqa: E402
# engine._navigation_budgeted_file_map_md e um partial com clamp_navigation_artifact=...; refaz o partial
if hasattr(engine, "_navigation_budgeted_file_map_md"):
    p = engine._navigation_budgeted_file_map_md
    if isinstance(p, functools.partial):
        kw = dict(p.keywords); kw["clamp_navigation_artifact"] = no_clamp
        engine._navigation_budgeted_file_map_md = functools.partial(p.func, *p.args, **kw)

import reprocess_assignments as ra  # noqa: E402
ra.reprocess(dst, [])
fm = (dst / "course/FILE_MAP.md").read_text(encoding="utf-8", errors="replace")
import re  # noqa: E402
n_rows = len(re.findall(r"^[|][ ]*[0-9]+[ ]*[|]", fm, re.M))
print(f"FILE_MAP sem clamp: {len(fm)} chars, linhas={n_rows}")
env = {**os.environ, "TUTOR_REPOS_DIR": str(TMP), "PYTHONIOENCODING": "utf-8"}
for mode in (["--sem-llm"], ["--cap", "20"]):
    out = subprocess.run([sys.executable, str(GEN / "scripts/eval_travessia.py"), SIG, *mode], cwd=str(GEN), env=env,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(l for l in out.stdout.splitlines() if l.startswith(SIG) or "por estilo" in l or "ERR" in l or "LLM disse" in l))
