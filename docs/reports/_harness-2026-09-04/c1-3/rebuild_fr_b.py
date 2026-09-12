"""RUN B do FR (06/09, Gemini LIBERADO pelo user so para o FR): tutor do ZERO em `.ablacao/FR-rebuild-B/`, mesmo caminho da UI, zero
curadoria, zero gold, com as camadas de LLM que o produto usa sozinho: resumos de codigo (Gemini), voter (Gemini) e vocab compilado
(Gemini, compilado no reprocess que segue o build, porque o build do zero ainda nao tem unidades). Datalab segue bloqueado (pymupdf4llm).
Conta cada chamada; nunca imprime chaves. Config da UI NAO e gravada (override em memoria de `gemini_auto_summarize`).
Uso: rebuild_fr_b.py [--fresh]"""
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
os.environ.pop("TUTOR_NO_VOCAB_COMPILE", None)
os.environ["TUTOR_REPOS_ORIG"] = str(Path(r"C:\Users\Humberto\Documents\GitHub"))   # perfil/plano do FR pelo nome da pasta (reprocess)
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
import reprocess_assignments as ra  # noqa: E402

STASH = Path.home() / "Desktop/Moodle/fundamentos-de-redes-de-computadores/stash"
REPO = GEN / ".ablacao" / "FR-rebuild-B" / "Fundamentos-de-Redes-Tutor"
PROD = GH / "Fundamentos-de-Redes-Tutor"
FRESH = "--fresh" in sys.argv
NOBUILD = "--no-build" in sys.argv   # reaproveita o build (resumos ja pagos); so reprocess + comparacao
calls = collections.Counter()


def _datalab_bloqueado(path, **kw):
    calls["datalab_bloqueado"] += 1
    raise RuntimeError("Datalab bloqueado (run B usa pymupdf4llm)")


datalab_client.convert_document_to_markdown = _datalab_bloqueado
engine_module.convert_document_to_markdown = _datalab_bloqueado
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
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "fundamentos-de-redes-de-computadores")
frases = []
for titulo, topicos in (_parse_units_from_teaching_plan(sp.teaching_plan) or []):
    frases.append(str(titulo or "").lower())
    frases.extend(str(t[0] if isinstance(t, (tuple, list)) else t).lower() for t in topicos or [])
scan = scan_stash_cards(STASH, frases_do_plano=[f for f in frases if len(f) >= 6])
entries = build_stash_entries(scan, existing_source_paths=set(), defaults={
    "processing_mode": sp.default_mode, "ocr_language": sp.default_ocr_lang, "preferred_backend": "pymupdf4llm",
    "datalab_mode": sp.default_datalab_mode, "document_profile": ""})
config = AppConfig()
ensure_builtin_profiles(config)
_get = config.get
config.get = lambda k, d=None: True if k == "gemini_auto_summarize" else _get(k, d)   # em memoria; nada gravado
options = _build_options_from_config(sp.default_mode, sp.default_ocr_lang, config, subject=sp)
options["compile_vocabulary"] = True
meta = {"course_name": sp.name, "course_slug": sp.slug, "semester": sp.semester, "professor": sp.professor,
        "institution": getattr(sp, "institution", "") or "PUCRS"}
print(f"[stash] {len(entries)} entries | gemini_auto_summarize={config.get('gemini_auto_summarize')} | client={'ok' if gemini_client.get_gemini_client(config) else 'NONE'}")
if FRESH and REPO.exists():
    shutil.rmtree(REPO)
REPO.mkdir(parents=True, exist_ok=True)
t0 = time.time()
if NOBUILD and (REPO / "manifest.json").exists():
    print("[build] pulado (--no-build): reaproveita o build anterior", flush=True)
else:
    b = RepoBuilder(root_dir=REPO, course_meta=meta, entries=entries, options=options, subject_profile=sp,
                    progress_callback=lambda i, n, t: None)
    b.build()
    print(f"[build] {time.time() - t0:.0f}s | falhas {len(b.failed_entries)} | chamadas {dict(calls)}", flush=True)
for passo in (1, 2):
    c0 = dict(calls)
    ra.reprocess(REPO, [])
    print(f"[reprocess {passo}] chamadas acumuladas {dict(calls)} (neste passo: { {k: calls[k] - c0.get(k, 0) for k in calls} })", flush=True)
m = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
es = m["entries"]
print("revisar:", dict(collections.Counter(e.get("revisar") for e in es)),
      "| metodos:", dict(collections.Counter(str(e.get("temporal_block_method")) for e in es)))
for name in ("course/.glossary_curation.llm.json", "material_curation.json", "code_curation.json"):
    p = REPO / name
    print(f"   {name}: {'existe (' + str(p.stat().st_size) + ' bytes)' if p.exists() else 'ausente'}")
prod = {e["id"]: e for e in json.loads((PROD / "manifest.json").read_text(encoding="utf-8"))["entries"]}
ti = {b_["block_uuid"]: b_["id"] for b_ in json.loads((REPO / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]}
ti_p = {b_["block_uuid"]: b_["id"] for b_ in json.loads((PROD / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]}
agree = collections.Counter()
print(f"\n{'entry':34} {'bloco B':9} {'bloco prod':10} {'unidade B':22} {'unidade prod':22} {'sub B':22} {'sub prod':22} {'revisar B':9}")
for e in es:
    p = prod.get(e["id"])
    if not p:
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
print(f"\nconcordancia com o produto: bloco {agree['bloco']}/{n} · unidade {agree['unidade']}/{n} · subunidade {agree['sub']}/{n}")
print(f"[fim] chamadas Gemini: {dict(calls)}", flush=True)
