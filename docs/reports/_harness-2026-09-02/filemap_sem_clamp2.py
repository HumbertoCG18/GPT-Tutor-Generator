"""Gera o FILE_MAP SEM clamp chamando o renderizador low-token direto (mesmos inputs da regeneracao),
grava na copia temporaria (ja reprocessada) e roda a regua de travessia contra ela."""
import functools, json, os, re, subprocess, sys
from pathlib import Path

GEN = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
TMP = Path("C:/Users/Humberto/.claude/jobs/ea3da64b/tmp/semclamp")
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
SIG = sys.argv[1]
NOME = {"IA": "Inteligencia-Artifical-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}[SIG]
repo = TMP / NOME
assert repo.exists(), "rode filemap_sem_clamp.py antes (cria a copia)"

import src.builder.engine as engine  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402

al = engine._navigation_template_aliases
def no_clamp(text, max_chars=0, label=""):
    return text
low_p = al["_low_token_file_map_md"]; lk = dict(low_p.keywords); lk["clamp_navigation_artifact"] = no_clamp
low = functools.partial(low_p.func, *low_p.args, **lk)
bud_p = al["_budgeted_file_map_md"]; bk = dict(bud_p.keywords); bk["clamp_navigation_artifact"] = no_clamp; bk["low_token_file_map_md_fn"] = low
bud = functools.partial(bud_p.func, *bud_p.args, **bk)
man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
sp = SubjectStore().find_by_repo_root(GEN.parent / NOME)
course_meta = {**(man.get("course") or {}), "_repo_root": repo, "_content_taxonomy": load_internal_content_taxonomy(repo)}
text = bud(course_meta, man.get("entries", []), sp)
n_rows = len(re.findall(r"^[|][ ]*[0-9]+[ ]*[|]", text, re.M))
print(f"FILE_MAP sem clamp: {len(text)} chars, linhas={n_rows} (clampado: 12000 chars)")
(repo / "course" / "FILE_MAP.md").write_text(text, encoding="utf-8")
env = {**os.environ, "TUTOR_REPOS_DIR": str(TMP), "PYTHONIOENCODING": "utf-8"}
for mode in (["--sem-llm"], ["--cap", "20"]):
    out = subprocess.run([sys.executable, str(GEN / "scripts/eval_travessia.py"), SIG, *mode], cwd=str(GEN), env=env,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(l for l in out.stdout.splitlines() if l.startswith(SIG) or "por estilo" in l or "ERR" in l or "ok3" in l or "LLM disse" in l))
    if out.returncode:
        print(out.stderr[-800:])
