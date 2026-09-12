"""Reparo REGISTRADO das 16 paginas do Moodle do CG capturadas como tela de login (06/09). Raiz: a sync criou entries url para
`moodle.pucrs.br/mod/page/view.php?id=N` e o conversor de URL as buscou sem sessao. O pull ja tinha salvo o HTML real (com token)
em `<pull>/raw/moodle/pages/<N>-<slug>.html`. Aqui: para cada entry url dessas, copia o HTML para `stash/<card>/<id>.html`,
remove a entry url (unprocess) e cria a entry html com o MESMO id (id_override) — golds e curadoria intactos —, roda o build
incremental (conversao local de html; tripwire: Gemini e Datalab bloqueados) e o reprocess. Uso: repara_paginas_cg.py [--dry-run]"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
REPO = GH / "Computacao-Grafica-Tutor"
PULL = Path.home() / "Desktop/Moodle/computacao-grafica"
DRY = "--dry-run" in sys.argv
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("bloqueado (tripwire de produto)")


_gc.GeminiClient.__init__ = _bloqueado
from src.builder.runtime import datalab_client  # noqa: E402
from src.builder import engine as engine_module  # noqa: E402
datalab_client.convert_document_to_markdown = _bloqueado
engine_module.convert_document_to_markdown = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from src.builder.engine import RepoBuilder  # noqa: E402
from src.models.core import FileEntry, SubjectStore  # noqa: E402

man = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
alvo = [e for e in man["entries"] if e.get("file_type") == "url" and "moodle.pucrs.br/mod/page/view.php" in str(e.get("source_path") or "")]
print(f"entries url de mod/page no CG: {len(alvo)}")
pages = {re.match(r"(\d+)-", p.name).group(1): p for p in (PULL / "raw/moodle/pages").glob("*.html")}
novas, faltam = [], []
for e in alvo:
    mid = re.search(r"id=(\d+)", str(e.get("source_path"))).group(1)
    src = pages.get(mid)
    if not src:
        faltam.append(e["id"]); continue
    card = str(e.get("source_section") or "")
    dest = PULL / "stash" / card / f"{e['id']}.html"
    html = src.read_text(encoding="utf-8", errors="replace")
    palavras = len(re.sub(r"<[^>]+>", " ", html).split())
    print(f"  {e['id'][:50]:50} <- {src.name[:60]} ({palavras} palavras) -> stash/{card[:28]}/{e['id'][:30]}.html")
    novas.append((e, dest, html))
print(f"com HTML salvo: {len(novas)} · sem: {faltam}")
if DRY or not novas:
    sys.exit(0)
store = SubjectStore()
profile = ra._find_subject_profile(REPO, store)
options = man.get("options", {}) or {}
ra._merge_profile_flags(options, profile)
builder = RepoBuilder(root_dir=REPO, course_meta=man.get("course", {}) or {}, entries=[], options=options, subject_profile=profile)
entries_novas = []
for e, dest, html in novas:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    builder.unprocess(e["id"])
    entries_novas.append(FileEntry(source_path=str(dest), file_type="html", category="references", title=str(e.get("title") or ""),
                                   source_section=str(e.get("source_section") or ""), id_override=e["id"],
                                   processing_mode=str(e.get("processing_mode") or "fast"), ocr_language=str(e.get("ocr_language") or "por")))
b2 = RepoBuilder(root_dir=REPO, course_meta=man.get("course", {}) or {}, entries=entries_novas, options=options, subject_profile=profile,
                 progress_callback=lambda i, n, t: print(f"  ({i + 1}/{n}) {t[:60]}", flush=True))
b2.incremental_build()
print("falhas:", [str(f)[:120] for f in (getattr(b2, "failed_entries", []) or [])])
ra.reprocess(REPO, [])
m2 = {e["id"]: e for e in json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))["entries"]}
for e, dest, html in novas:
    n = m2.get(e["id"])
    if not n:
        print("  !! sumiu:", e["id"]); continue
    md = n.get("base_markdown"); txt = (REPO / md).read_text(encoding="utf-8", errors="replace") if md and (REPO / md).exists() else ""
    print(f"  {e['id'][:46]:46} type={n.get('file_type'):5} chars={len(txt):6} login={'SIM' if 'login' in txt.lower() and len(txt) < 3000 else 'nao'} sub={str(n.get('computed_subunit_slug') or '-')[-30:]} unit={str(n.get('computed_unit_slug') or '-')[-20:]}")
r = subprocess.run(["git", "-C", str(REPO), "status", "--short"], capture_output=True, text=True)
print("git status (linhas):", r.stdout.count("\n"))
print("[fim]")
