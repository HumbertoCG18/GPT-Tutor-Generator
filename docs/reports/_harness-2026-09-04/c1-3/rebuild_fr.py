"""RUN A do FR (06/09): tutor do ZERO numa COPIA (.ablacao/FR-rebuild/Fundamentos-de-Redes-Tutor), o MESMO caminho da UI
(scan_stash_cards -> build_stash_entries -> RepoBuilder.build), perfil real do FR (sem grava-lo), zero curadoria, zero gold,
ZERO chamada externa: Gemini bloqueado (tripwire), Datalab bloqueado (tripwire; o FR atual ja era pymupdf4llm), vocab NAO compilado.
Cenario: o aluno so fez login. Depois: comparacao entry a entry com o FR atual (produto, que tem vocab LLM + 13 votos + 4 resumos).
Uso: rebuild_fr.py [--dry-run] [--fresh]"""
import collections
import json
import os
import shutil
import sys
import time
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
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

STASH = Path.home() / "Desktop/Moodle/fundamentos-de-redes-de-computadores/stash"
REPO = GEN / ".ablacao" / "FR-rebuild" / "Fundamentos-de-Redes-Tutor"
PROD = GH / "Fundamentos-de-Redes-Tutor"
DRY = "--dry-run" in sys.argv
FRESH = "--fresh" in sys.argv
calls = collections.Counter()

# --- tripwires: nenhuma chamada externa paga -------------------------------------------------------------------
gemini_client.get_gemini_client = lambda config=None: None


def _gemini_bloqueado(*a, **k):
    calls["gemini_bloqueado"] += 1
    raise RuntimeError("Gemini bloqueado (tripwire da run A)")


gemini_client.GeminiClient.__init__ = _gemini_bloqueado


def _datalab_bloqueado(path, **kw):
    calls["datalab_bloqueado"] += 1
    raise RuntimeError("Datalab bloqueado (tripwire da run A): use pymupdf4llm")


datalab_client.convert_document_to_markdown = _datalab_bloqueado
engine_module.convert_document_to_markdown = _datalab_bloqueado

store = SubjectStore()
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "fundamentos-de-redes-de-computadores")
frases = []
for titulo, topicos in (_parse_units_from_teaching_plan(sp.teaching_plan) or []):
    frases.append(str(titulo or "").lower())
    frases.extend(str(t[0] if isinstance(t, (tuple, list)) else t).lower() for t in topicos or [])
scan = scan_stash_cards(STASH, frases_do_plano=[f for f in frases if len(f) >= 6])
entries = build_stash_entries(scan, existing_source_paths=set(), defaults={
    "processing_mode": sp.default_mode, "ocr_language": sp.default_ocr_lang, "preferred_backend": "pymupdf4llm",
    "datalab_mode": sp.default_datalab_mode, "document_profile": ""})
print(f"[stash] {len(entries)} entries | tipos {dict(collections.Counter(e.file_type for e in entries))} | "
      f"categorias {dict(collections.Counter(e.category for e in entries))} | ignorados {[Path(s).name for s in scan.skipped]}")
config = AppConfig()
ensure_builtin_profiles(config)
options = _build_options_from_config(sp.default_mode, sp.default_ocr_lang, config, subject=sp)
meta = {"course_name": sp.name, "course_slug": sp.slug, "semester": sp.semester, "professor": sp.professor,
        "institution": getattr(sp, "institution", "") or "PUCRS"}
print("[options]", {k: options.get(k) for k in ("default_processing_mode", "image_description_source", "skip_base_backends", "profile_backends")})
print("[meta]", meta, "| gemini_auto_summarize:", config.get("gemini_auto_summarize", None))
if DRY:
    print("[dry-run] build NAO executado.")
    sys.exit(0)
if FRESH and REPO.exists():
    shutil.rmtree(REPO)
REPO.mkdir(parents=True, exist_ok=True)
t0 = time.time()
b = RepoBuilder(root_dir=REPO, course_meta=meta, entries=entries, options=options, subject_profile=sp,
                progress_callback=lambda i, n, t: print(f"  ({i + 1}/{n}) {t[:70]}  [{time.time() - t0:.0f}s]", flush=True))
b.build()
print(f"[build] {time.time() - t0:.0f}s | falhas {len(b.failed_entries)} | chamadas bloqueadas {dict(calls)}")
for f in b.failed_entries[:10]:
    print("   !!", str(f)[:160])
m = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
es = m["entries"]
print("entries no manifest:", len(es), "| tipos:", dict(collections.Counter(e.get("file_type") for e in es)),
      "| base_backend:", dict(collections.Counter(str(e.get("base_backend")) for e in es)))
print("revisar:", dict(collections.Counter(e.get("revisar") for e in es)),
      "| metodos:", dict(collections.Counter(str(e.get("temporal_block_method")) for e in es)))
for name in ("course/.glossary_curation.llm.json", "course/.glossary_curation.json", "material_curation.json", "code_curation.json", "course/.timeline_curation.json"):
    p = REPO / name
    print(f"   {name}: {'existe (' + str(p.stat().st_size) + ' bytes)' if p.exists() else 'ausente'}")

# --- comparacao com o FR atual (produto) ---------------------------------------------------------------------------
prod = {e["id"]: e for e in json.loads((PROD / "manifest.json").read_text(encoding="utf-8"))["entries"]}
ti = {b_["block_uuid"]: b_["id"] for b_ in json.loads((REPO / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]}
ti_p = {b_["block_uuid"]: b_["id"] for b_ in json.loads((PROD / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]}
agree = collections.Counter()
print("\n=== rebuild (run A, 0 chamadas) x produto (vocab LLM + voter + resumos) ===")
print(f"{'entry':34} {'bloco A':9} {'bloco prod':10} {'unidade A':22} {'unidade prod':22} {'sub A':22} {'sub prod':22} {'revisar A':9}")
for e in es:
    p = prod.get(e["id"])
    if not p:
        agree["so_no_rebuild"] += 1
        continue
    ba = ti.get(e.get("temporal_block_id") or "", e.get("temporal_block_id") or "-")
    bp = ti_p.get(p.get("manual_timeline_block_id") or p.get("temporal_block_id") or "", p.get("temporal_block_id") or "-")
    ua, up = str(e.get("computed_unit_slug") or "-"), str(p.get("computed_unit_slug") or "-")
    sa, sp_ = str(e.get("computed_subunit_slug") or "-"), str(p.get("computed_subunit_slug") or "-")
    agree["n"] += 1
    agree["bloco"] += ba == bp
    agree["unidade"] += ua == up
    agree["sub"] += sa == sp_
    print(f"{e['id'][:34]:34} {str(ba)[-9:]:9} {str(bp)[-10:]:10} {ua[-22:]:22} {up[-22:]:22} {sa[-22:]:22} {sp_[-22:]:22} {str(e.get('revisar') or 'ok'):9}")
n = max(1, agree["n"])
print(f"\nconcordancia com o produto: bloco {agree['bloco']}/{n} · unidade {agree['unidade']}/{n} · subunidade {agree['sub']}/{n} · so no rebuild {agree['so_no_rebuild']}")
print("[fim]", flush=True)
