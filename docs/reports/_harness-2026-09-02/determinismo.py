"""Item 5: determinismo dos renderizadores. Copia cada tutor para temp, reprocessa 2x (voter cacheado,
vocab compilado cacheado), e faz diff de TODOS os artefatos derivados (.md/.json/.yaml, exceto .bak e updated_at).
Saida: por curso, arquivos que mudaram entre a 1a e a 2a rodada."""
import filecmp, json, os, shutil, sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[3]
TMP = GEN / ".determinismo"   # copia temporaria (gitignored? nao: apague depois)
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GEN.parent)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import reprocess_assignments as ra  # noqa: E402

REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor",
         "TCC-Tutor", "Computacao-Grafica-Tutor", "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor"]
IGN = shutil.ignore_patterns(".git", "build", "__pycache__", "*.bak", "staging")


def snapshot(repo: Path) -> dict:
    out = {}
    for p in repo.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".json", ".yaml", ".yml") and ".bak" not in p.name and "raw" not in p.parts[len(repo.parts):][:1]:
            t = p.read_text(encoding="utf-8", errors="replace")
            if p.name == "manifest.json":
                try:
                    d = json.loads(t); d.pop("updated_at", None); t = json.dumps(d, ensure_ascii=False, sort_keys=True)
                except Exception:
                    pass
            out[str(p.relative_to(repo))] = t
    return out


total = 0
for nome in REPOS:
    dst = TMP / nome
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(GEN.parent / nome, dst, ignore=IGN)
    ra.reprocess(dst, [])
    s1 = snapshot(dst)
    ra.reprocess(dst, [])
    s2 = snapshot(dst)
    mud = sorted(k for k in set(s1) | set(s2) if s1.get(k) != s2.get(k))
    total += len(mud)
    print(f"== {nome}: {len(mud)} arquivo(s) diferem entre rodada 1 e 2: {mud[:8]}", flush=True)
    for k in mud[:3]:
        a, b = s1.get(k, "").splitlines(), s2.get(k, "").splitlines()
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print(f"     {k}:{i + 1}\n       1: {x[:140]}\n       2: {y[:140]}"); break
print(f"TOTAL arquivos nao deterministicos: {total}")
