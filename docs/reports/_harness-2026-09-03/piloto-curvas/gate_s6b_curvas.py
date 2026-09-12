"""Gate S6b: Curvas.htm de ponta a ponta numa COPIA do CG (.ablacao/CG-gate-html), stash no layout REAL do mirror
(Curvas.htm + Curvas.fld/ + irmas), cache Datalab semeado do gold do piloto (0 chamadas Datalab), Gemini REAL
para as 12 legendas/vazias. Depois: unprocess + re-add = 0 chamadas (cache) e markdown byte-identico.
READ-ONLY nos originais. Nunca imprime chaves."""
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.utils.helpers  # noqa: F401,E402  (.env)
import reprocess_assignments as ra  # noqa: E402
from src.builder import engine as engine_module  # noqa: E402
from src.builder.engine import RepoBuilder  # noqa: E402
from src.builder.runtime.gemini_client import GeminiClient  # noqa: E402
from src.models.core import FileEntry, SubjectStore  # noqa: E402

ORIG = GEN.parent / "Computacao-Grafica-Tutor"
GATE = GEN / ".ablacao" / "CG-gate-html"
MIRROR = Path.home() / "Desktop/Moodle/computacao-grafica-raw/raw/site/www.inf.pucrs.br/pinho/CG/Aulas/Curvas"
GOLD = json.loads((GEN / "docs/reports/_harness-2026-09-03/piloto-curvas/datalab_cache.json").read_text(encoding="utf-8"))

# contadores nos clientes reais (Datalab nao pode ser chamado: cache semeado)
calls = {"datalab": 0, "gemini": 0}


def _datalab_guard(path):
    calls["datalab"] += 1
    raise RuntimeError(f"Datalab chamado no gate para {path.name} (cache deveria cobrir)")


_real_generate = GeminiClient.generate_text


def _gemini_counted(self, prompt, image_path=None):
    calls["gemini"] += 1
    return _real_generate(self, prompt, image_path)


engine_module._core_html_material_datalab_image_markdown = _datalab_guard
GeminiClient.generate_text = _gemini_counted

# 1. copia do CG (sem .git/build/raw pesado)
t0 = time.time()
old_cache = {}
if (GATE / "course" / ".image_transcriptions.json").is_file():
    old_cache = json.loads((GATE / "course" / ".image_transcriptions.json").read_text(encoding="utf-8"))
if GATE.exists():
    shutil.rmtree(GATE)
shutil.copytree(ORIG, GATE, ignore=shutil.ignore_patterns(".git", "build", "pdfs", "zip", "repos", "*.bak"))
print(f"copia: {time.time() - t0:.0f}s")

# 2. stash no layout real do mirror
card = GATE / "stash-gate" / "7 - Curvas Paramétricas"
shutil.copytree(MIRROR, card, ignore=shutil.ignore_patterns("*.orig"))
html = card / "Curvas.htm"

# 3. cache semeado do gold, chaveado por md5 do arquivo real
cache = {}
for p in card.rglob("*"):
    if p.is_file() and p.name in GOLD and "markdown" in GOLD[p.name]:
        key = hashlib.md5(p.read_bytes()).hexdigest()
        cache[key] = {"markdown": GOLD[p.name]["markdown"]}
        if old_cache.get(key, {}).get("pt"):
            cache[key]["pt"] = old_cache[key]["pt"]
cache_path = GATE / "course" / ".image_transcriptions.json"
cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print("cache semeado:", len(cache))

# 4. incremental build (mesmo caminho do sync_moodle.apply_sync)
store = SubjectStore()
prof = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "computacao-grafica")
m = json.loads((GATE / "manifest.json").read_text(encoding="utf-8"))
options = m.get("options", {}) or {}
ra._merge_profile_flags(options, prof)
course_meta = m.get("course", {}) or {}


def build_once(label):
    entry = FileEntry(source_path=str(html), file_type="html", category="outros", title="Curvas",
                      source_section="7 - Curvas Paramétricas")
    t = time.time()
    b = RepoBuilder(root_dir=GATE, course_meta=course_meta, entries=[entry], options=options, subject_profile=prof,
                    progress_callback=lambda i, n, t_: print(f"  ({i + 1}/{n}) {t_[:60]}", flush=True))
    b.incremental_build()
    print(f"[{label}] build {time.time() - t:.0f}s | falhas: {b.failed_entries} | chamadas: {calls}")
    m2 = json.loads((GATE / "manifest.json").read_text(encoding="utf-8"))
    e = next(x for x in m2["entries"] if x["id"] == "curvas")
    md = (GATE / e["base_markdown"]).read_text(encoding="utf-8")
    return b, e, md


b, e, md = build_once("1a rodada")
print("entry:", {k: e.get(k) for k in ("file_type", "category", "base_markdown", "raw_target", "html_images",
                                        "temporal_block_id", "temporal_block_method", "temporal_block_flag",
                                        "computed_unit_slug", "revisar")})
print("fontes:", md.count("<sub>fonte: ["), "| figuras:", md.count("![Figura: "), "| nao capturadas:",
      md.count("não capturada"), "| vml:", md.count("[if gte vml"), "| chars:", len(md))
print("content/images curvas-*:", len(list((GATE / "content/images").glob("curvas-*"))),
      "| manual-review/formulas:", len(list((GATE / "manual-review/formulas").glob("*.md"))))
cache2 = json.loads(cache_path.read_text(encoding="utf-8"))
print("cache:", len(cache2), "| com pt:", sum(1 for v in cache2.values() if v.get("pt")))
for line in md.splitlines():
    if line.startswith("![Figura: "):
        print("  ", line[:150])
fm = (GATE / "course/FILE_MAP.md").read_text(encoding="utf-8")
print("FILE_MAP cita curvas.md:", "html/curvas.md" in fm)
out = Path(__file__).parent / "curvas_gate.md"
out.write_text(md, encoding="utf-8")

# 5. idempotencia: unprocess + re-add -> 0 chamadas e md identico
calls["datalab"] = calls["gemini"] = 0
b.unprocess("curvas")
print("apos unprocess: curvas-* em content/images:", len(list((GATE / "content/images").glob("curvas-*"))))
b2, e2, md2 = build_once("2a rodada")
print("idempotente:", md2 == md, "| html_images:", e2.get("html_images"), "| chamadas na 2a:", calls)
print("bloco 1a x 2a:", e.get("temporal_block_id"), e2.get("temporal_block_id"))
