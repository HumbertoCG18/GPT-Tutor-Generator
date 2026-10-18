"""S6f complemento: leva ao repo do CG o que o rebuild pelo build nao ingeriu — (1) as 4 folhas da subarvore (bundles novos no
stash, mesmo modulo do hub: sync_diff nao as ve porque o modulo url ja tem entry) e (2) os 23 links de referencia do links.json
(7 videos + 16 indices de video), como `apply_sync` faz. Uma so incremental_build (Datalab so nas imagens das folhas; Gemini nos
resumos das referencias e no voter cacheado) + course/SYNC_REPORT.md. Uso: sync_complete_cg.py <repo> [--dry-run]. Nunca imprime chaves."""
import json
import sys
import time
from datetime import date
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.utils.helpers  # noqa: F401,E402
import reprocess_assignments as ra  # noqa: E402
from src.builder.core.stash_import import build_stash_entries, scan_stash_cards  # noqa: E402
from src.builder.engine import RepoBuilder  # noqa: E402
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan  # noqa: E402
from src.builder.sources.moodle_sync import (decision_diff, formula_index, mark_sync_changes, plan_import,  # noqa: E402
                                             render_sync_report, snapshot_decisions, sync_diff)
from src.models.core import SubjectStore  # noqa: E402
from src.utils.helpers import write_json_manifest  # noqa: E402

REPO = Path(sys.argv[1]).resolve()
DRY = "--dry-run" in sys.argv
ROOT = Path.home() / "Desktop/Moodle/computacao-grafica"
STASH = ROOT / "stash"
assert (REPO / "manifest.json").is_file(), f"sem manifest em {REPO}"

store = SubjectStore()
prof = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "computacao-grafica")
manifest = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
entries = manifest.get("entries", [])
contents = json.loads((ROOT / "raw/moodle/contents.json").read_text(encoding="utf-8"))
links = json.loads((ROOT / "links.json").read_text(encoding="utf-8"))
nomes = json.loads((STASH / ".moodle_nomes.json").read_text(encoding="utf-8"))
# (0) backfill do moodle_label a partir do sidecar: o rebuild pelo caminho de build nao o gravou (66/66 sem label; fix no
# build_stash_entries vale para os proximos). Sem o label, 19 materiais de modulo url/page nao casam (sync os veria "sumidos").
n_label = 0
for e in entries:
    if not (e.get("moodle_label") or ""):
        nome = nomes.get(f"{e.get('source_section')}/{Path(str(e.get('source_path') or '')).name}")
        if nome:
            e["moodle_label"] = nome; n_label += 1
print(f"[label] moodle_label preenchido em {n_label} entries a partir do sidecar")
if n_label and not DRY:
    write_json_manifest(REPO / "manifest.json", manifest)
frases = []
for titulo, topicos in (_parse_units_from_teaching_plan(prof.teaching_plan) or []):
    frases.append(str(titulo or "").lower())
    frases.extend(str(t[0] if isinstance(t, (tuple, list)) else t).lower() for t in topicos or [])
scan = scan_stash_cards(STASH, frases_do_plano=[f for f in frases if len(f) >= 6])
defaults = {"processing_mode": prof.default_mode, "ocr_language": prof.default_ocr_lang,
            "preferred_backend": prof.default_backend, "datalab_mode": prof.default_datalab_mode, "document_profile": ""}
existing = {str(e.get("source_path") or "") for e in entries}
novas = build_stash_entries(scan, existing, defaults)          # so o que o stash tem e o manifest nao (as folhas)
for fe in novas:
    fe.moodle_label = str(nomes.get(f"{fe.source_section}/{Path(fe.source_path).name}") or "")
diff = sync_diff(entries, contents)
plan = plan_import(diff, contents, scan, links, entries, nomes=nomes, defaults=defaults, prune_removed=False)
print(f"[stash] novas no stash e fora do manifest: {[(Path(e.source_path).name, e.source_section[:28], e.moodle_label[:40]) for e in novas]}")
print(f"[links] referencias a entrar: {len(plan.links)} | review: {len(plan.review)} | diff: novos {len(diff['novos'])} alterados {len(diff['alterados'])} sumidos {len(diff['sumidos'])}")
if DRY:
    print("[dry-run] nada gravado."); sys.exit(0)

(REPO / "raw" / "moodle").mkdir(parents=True, exist_ok=True)
for f in ("contents.json", "sections.json", "labels.json"):
    src = ROOT / "raw" / "moodle" / f
    if src.is_file():
        (REPO / "raw" / "moodle" / f).write_bytes(src.read_bytes())
options = manifest.get("options", {}) or {}
ra._merge_profile_flags(options, prof)
course_meta = manifest.get("course", {}) or {}
before = snapshot_decisions(entries)
new_entries = novas + plan.links
t0 = time.time()
b = RepoBuilder(root_dir=REPO, course_meta=course_meta, entries=new_entries, options=options, subject_profile=prof,
                progress_callback=lambda i, n, t: print(f"  ({i + 1}/{n}) {t[:70]}", flush=True))
b.incremental_build()
print(f"[build] {time.time() - t0:.0f}s | falhas {len(b.failed_entries)}")
for f in b.failed_entries[:10]:
    print("   !!", str(f)[:160])
when = date.today().isoformat()
m = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
dd = decision_diff(before, m.get("entries", []))
n_mark = mark_sync_changes(m.get("entries", []), dd["moved"], when=when)
write_json_manifest(REPO / "manifest.json", m)
report = render_sync_report(diff, dd, when=when, curso=prof.name, ignorados=plan.ignorados, review=plan.review,
                            plan_counts=f"complemento do rebuild: folhas {len(novas)} links {len(plan.links)}",
                            formulas=formula_index(m.get("entries", []), REPO))
(REPO / "course" / "SYNC_REPORT.md").write_text(report, encoding="utf-8")
print(f"[sync] {REPO.name}: entries {len(entries)} -> {len(m['entries'])} | url: {sum(1 for e in m['entries'] if e.get('file_type') == 'url')} | "
      f"decisoes movidas {len(dd['moved'])} (marcadas {n_mark}) | course/SYNC_REPORT.md")
if "--commit" in sys.argv and (REPO / ".git").is_dir():
    import subprocess
    ger = subprocess.run(["git", "-C", str(GEN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "-C", str(REPO), "add", "-A"], check=True)
    msg = (f"sync: complemento do rebuild pela API (gerador {ger}, SYNC S6f) — {len(novas)} folhas da subarvore como material html, "
           f"{len(plan.links)} referencias (videos e indices de video), moodle_label do sidecar nos {len(entries)} entries, SYNC_REPORT")
    r = subprocess.run(["git", "-C", str(REPO), "commit", "-q", "-m", msg], capture_output=True, text=True)
    print("[commit]", (r.stdout + r.stderr).strip()[:160] or "ok",
          "| HEAD:", subprocess.run(["git", "-C", str(REPO), "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip()[:100])
print("[fim]")
