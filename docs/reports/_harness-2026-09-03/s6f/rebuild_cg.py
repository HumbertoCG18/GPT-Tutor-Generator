"""S6f: rebuild LIMPO do CG pela API numa COPIA (.ablacao/CG-rebuild/Computacao-Grafica-Tutor) — o MESMO caminho da UI
(scan_stash_cards -> build_stash_entries -> RepoBuilder.build), com o perfil REAL do CG lido do subjects.json (sem grava-lo),
zero curadoria. Conta chamadas Datalab/Gemini (nunca imprime chaves). `--dry-run` = so o plano; `--fresh` = apaga a copia antes.
Cache de imagens das paginas semeado do gate do S6b (24 Curvas, com pt) para nao pagar de novo."""
import collections
import json
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder import engine as engine_module  # noqa: E402
from src.builder.runtime import datalab_client, gemini_client  # noqa: E402
from src.builder.core.stash_import import build_stash_entries, scan_stash_cards  # noqa: E402
from src.builder.engine import RepoBuilder  # noqa: E402
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
from src.ui.app import _build_options_from_config  # noqa: E402
from src.ui.theme import AppConfig  # noqa: E402
from src.utils.helpers import ensure_builtin_profiles  # noqa: E402

STASH = Path.home() / "Desktop/Moodle/computacao-grafica/stash"
REPO = GEN / ".ablacao" / "CG-rebuild" / "Computacao-Grafica-Tutor"
SEED_CACHE = GEN / ".ablacao" / "CG-gate-html" / "course" / ".image_transcriptions.json"
DRY = "--dry-run" in sys.argv
FRESH = "--fresh" in sys.argv

calls = {"datalab": 0, "datalab_pages": 0, "gemini_text": 0, "gemini_bundle": 0}
_real_convert = datalab_client.convert_document_to_markdown


def _convert_counted(path, **kw):
    r = _real_convert(path, **kw)
    calls["datalab"] += 1
    calls["datalab_pages"] += int(getattr(r, "page_count", 0) or 0)
    print(f"    [datalab #{calls['datalab']}] {Path(path).name[:55]} pages={getattr(r, 'page_count', None)} "
          f"cost={getattr(r, 'cost_breakdown', None)}", flush=True)
    return r


datalab_client.convert_document_to_markdown = _convert_counted
engine_module.convert_document_to_markdown = _convert_counted
_real_text = gemini_client.GeminiClient.generate_text
_real_bundle = gemini_client.GeminiClient.summarize_bundle


def _text_counted(self, *a, **k):
    calls["gemini_text"] += 1
    return _real_text(self, *a, **k)


def _bundle_counted(self, *a, **k):
    calls["gemini_bundle"] += 1
    return _real_bundle(self, *a, **k)


gemini_client.GeminiClient.generate_text = _text_counted
gemini_client.GeminiClient.summarize_bundle = _bundle_counted

store = SubjectStore()
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "computacao-grafica")
frases = []
for titulo, topicos in (_parse_units_from_teaching_plan(sp.teaching_plan) or []):
    frases.append(str(titulo or "").lower())
    frases.extend(str(t[0] if isinstance(t, (tuple, list)) else t).lower() for t in topicos or [])
scan = scan_stash_cards(STASH, frases_do_plano=[f for f in frases if len(f) >= 6])
entries = build_stash_entries(scan, existing_source_paths=set(), defaults={
    "processing_mode": sp.default_mode, "ocr_language": sp.default_ocr_lang, "preferred_backend": sp.default_backend,
    "datalab_mode": sp.default_datalab_mode, "document_profile": ""})
print(f"[stash] {len(entries)} entries | tipos {dict(collections.Counter(e.file_type for e in entries))} | "
      f"categorias {dict(collections.Counter(e.category for e in entries))} | ignorados {[Path(s).name for s in scan.skipped]}")
config = AppConfig()
ensure_builtin_profiles(config)
options = _build_options_from_config(sp.default_mode, sp.default_ocr_lang, config, subject=sp)
meta = {"course_name": sp.name, "course_slug": sp.slug, "semester": sp.semester, "professor": sp.professor,
        "institution": getattr(sp, "institution", "") or "PUCRS"}
print("[options]", {k: options.get(k) for k in ("default_processing_mode", "image_description_source", "skip_base_backends",
                                                 "use_anchor_engine", "use_llm_voter", "compile_vocabulary", "profile_backends")})
print("[meta]", meta)
if DRY:
    print("[dry-run] build NAO executado.")
    sys.exit(0)
if FRESH and REPO.exists():
    shutil.rmtree(REPO)
REPO.mkdir(parents=True, exist_ok=True)
if SEED_CACHE.is_file() and not (REPO / "course" / ".image_transcriptions.json").exists():
    (REPO / "course").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SEED_CACHE, REPO / "course" / ".image_transcriptions.json")
    print("[cache] semeado do gate S6b:", len(json.loads(SEED_CACHE.read_text(encoding="utf-8"))), "imagens")
t0 = time.time()
b = RepoBuilder(root_dir=REPO, course_meta=meta, entries=entries, options=options, subject_profile=sp,
                progress_callback=lambda i, n, t: print(f"  ({i + 1}/{n}) {t[:70]}  [{time.time() - t0:.0f}s]", flush=True))
b.build()
print(f"[build] {time.time() - t0:.0f}s | falhas {len(b.failed_entries)} | chamadas {calls}")
for f in b.failed_entries[:10]:
    print("   !!", str(f)[:160])
m = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
es = m["entries"]
print("entries no manifest:", len(es), "| tipos:", dict(collections.Counter(e.get("file_type") for e in es)),
      "| base_backend:", dict(collections.Counter(str(e.get("base_backend")) for e in es)))
tot = collections.Counter()
for e in es:
    for k, v in (e.get("html_images") or {}).items():
        tot[k] += v
print("html_images total:", dict(tot))
print("revisar:", dict(collections.Counter(e.get("revisar") for e in es)),
      "| metodos:", dict(collections.Counter(str(e.get("temporal_block_method")) for e in es)))
print("[fim]", flush=True)
