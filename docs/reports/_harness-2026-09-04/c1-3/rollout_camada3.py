"""Rollout do corte da camada 3 nos 8 tutores REAIS (11/09): re-importa os zips com o process_zip corrigido (membro leva
o id do zip) e reprocessa pela rota do produto, que agora sintetiza code_curation.json (determ v3) e le o vocabulario
LLM novo. Deve custar 0 chamadas: vocab em cache/sidecar, votos em cache por md5 do arquivo (zip nao mudou), resumo
deterministico. Detector: qualquer metodo publico do GeminiClient que for chamado LEVANTA e conta — se aparecer 1,
o rollout parou de ser gratis e a saida diz onde.
Uso: python rollout_camada3.py [SIGLA ...]   (sem args = os 8)"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"

import src.builder.runtime.gemini_client as _gc  # noqa: E402

TENTATIVAS = []


def _detector(nome):
    def f(self, *a, **k):
        TENTATIVAS.append(nome)
        raise RuntimeError(f"Gemini bloqueado no rollout: {nome}")
    return f


for _n, _v in list(vars(_gc.GeminiClient).items()):
    if callable(_v) and not _n.startswith("_"):
        setattr(_gc.GeminiClient, _n, _detector(_n))

import reprocess_assignments as ra  # noqa: E402
from src.builder.core import source_importers as si  # noqa: E402
from src.models.core import FileEntry  # noqa: E402

TUTORES = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "FR": "Fundamentos-de-Redes-Tutor",
           "IA": "Inteligencia-Artifical-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "MF": "Metodos-Formais-Tutor",
           "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}


def reimporta_zips(repo: Path) -> tuple:
    from types import SimpleNamespace
    mp = repo / "manifest.json"
    man = json.loads(mp.read_text(encoding="utf-8"))
    b = SimpleNamespace(root_dir=repo, logs=[])
    n = m = 0
    for e in man["entries"]:
        raw = repo / str(e.get("raw_target") or "")
        if e.get("file_type") != "zip" or not e.get("raw_target") or not raw.is_file():
            continue
        fe = FileEntry(source_path=str(raw), file_type="zip", category=e.get("category") or "codigo-professor",
                       title=e.get("title") or e["id"], id_override=e["id"])
        item = si.process_zip(b, fe, raw)
        if item.get("extraction_error"):
            print(f"  [zip] {repo.name}/{e['id']}: {item['extraction_error']}", flush=True)
            continue
        e["extracted_files"] = item["extracted_files"]
        e["file_count"] = item["file_count"]
        n += 1
        m += item["file_count"]
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    mds = [f.get("base_markdown") for e in man["entries"] if e.get("file_type") == "zip" for f in (e.get("extracted_files") or [])]
    return n, m, len(set(mds))


def limpa_orfaos(repo: Path) -> int:
    """Apaga .md e raw de codigo que nenhuma entrada do manifest referencia: membros das rodadas anteriores (id por nome-base,
    depois por caminho sem extensao). So em code/{professor,student} e raw/code/{professor,student}."""
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ref = set()
    for e in man:
        for k in ("base_markdown", "raw_target"):
            if e.get(k):
                ref.add(str(e[k]).replace("\\", "/"))
        for f in e.get("extracted_files") or []:
            bm = f.get("base_markdown")
            if not bm:
                continue
            ref.add(str(bm).replace("\\", "/"))
            sub = Path(bm).parent.name
            ref.add(f"raw/code/{sub}/{Path(bm).stem}{Path(str(f.get('title') or '')).suffix.lower()}")
    n = 0
    for pasta in ("code/professor", "code/student", "raw/code/professor", "raw/code/student"):
        d = repo / pasta
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.is_file() and f.relative_to(repo).as_posix() not in ref:
                f.unlink()
                n += 1
    return n


def git_sujo(repo: Path) -> int:
    out = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout
    return len([l for l in out.splitlines() if l.strip()])


sigs = sys.argv[1:] or list(TUTORES)
t0 = time.time()
for sig in sigs:
    repo = GH / TUTORES[sig]
    antes = git_sujo(repo)
    n, m, d = reimporta_zips(repo)
    orf = limpa_orfaos(repo)
    t1 = time.time()
    ra.reprocess(repo, [])
    cc = json.loads((repo / "code_curation.json").read_text(encoding="utf-8")) if (repo / "code_curation.json").exists() else {}
    modelos = {}
    for v in (cc.get("entries") or {}).values():
        modelos[v.get("model", "?")] = modelos.get(v.get("model", "?"), 0) + 1
    print(f"[{sig}] zips {n}, membros {m}, md distintos {d} ({'ok' if d == m else 'COLISAO'}) · reprocess {time.time() - t1:.0f}s · "
          f"orfaos apagados {orf} · code_curation {modelos} · git sujo {antes} -> {git_sujo(repo)} · tentativas Gemini {len(TENTATIVAS)}", flush=True)
print(f"total {time.time() - t0:.0f}s · tentativas de chamada Gemini: {TENTATIVAS or 0}")
